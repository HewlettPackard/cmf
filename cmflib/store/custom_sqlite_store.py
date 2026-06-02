import json
import os
import sqlite3
import typing as t


class CustomSqliteStore:
    """Store execution-level artifact metadata in SQLite."""

    def __init__(self, db_path: str):
        # Function Name: __init__
        # Input: db_path (str)
        # Output: None
        # Description: Resolve DB path and initialize execution_log table.
        # Step 1: Normalize incoming DB path.
        # Step 2: Create DB/table if missing.
        self.db_path = self._resolve_db_path(db_path)
        self._init_db()

    @staticmethod
    def _resolve_db_path(path_hint: str) -> str:
        # Function Name: _resolve_db_path
        # Input: path_hint (str)
        # Output: str (resolved DB path)
        # Description: Determine final DB path based on input hint or defaults.
        # Step 1: Trim whitespace from input path hint.
        raw_path = (path_hint or "").strip()

        # Step 2: If no path provided, default to current working directory.
        if not raw_path:
            raw_path = os.getcwd()

        # Step 3: Normalize path to remove redundant separators and up-level references.
        normalized_path = os.path.normpath(raw_path)

        # Step 4: If the path ends with "mlmd", treat it as the final DB path.
        if os.path.basename(normalized_path) == "mlmd":
            return normalized_path

        # Step 5: Otherwise, treat input as a directory path and place DB at <dir>/mlmd.
        return os.path.join(normalized_path, "mlmd")

    def _connect(self) -> sqlite3.Connection:
        # Function Name: _connect
        # Input: None
        # Output: sqlite3.Connection
        # Description: Create a resilient SQLite connection for shared-file usage.
        # Step 1: Open connection with a longer timeout.
        # Step 2: Configure journaling and sync pragmas for safer writes.
        # Step 3: Return configured connection.
        # Use a longer timeout to avoid lock-contention failures when MLMD writes to the same DB.
        conn = sqlite3.connect(self.db_path, timeout=15)
        # Keep classic journaling when sharing one DB file with MLMD.

        # What each line does:

        # 1. `PRAGMA journal_mode=DELETE;`
        # - Uses classic rollback journal mode.
        # - Reason for change: your previous mode was WAL, and WAL can be fragile with mixed tooling/writers (MLMD writes, custom sqlite writes, VS Code viewer reads).
        # - In shared single-file usage, `DELETE` is simpler and usually less likely to produce weird sidecar-file issues (`mlmd-wal`, `mlmd-shm`) that lead to malformed/open errors in tools.

        # 2. `PRAGMA busy_timeout=15000;`
        # - Wait up to 15 seconds if DB is locked instead of failing immediately.
        # - Reason: MLMD and custom writes can briefly overlap. Without timeout, you get fast lock errors and possibly incomplete operation sequences.
        # - This improves stability under lock contention.

        # 3. `PRAGMA synchronous=FULL;`
        # - Forces SQLite to fully flush writes to disk before commit is considered done.
        # - Reason: strongest durability, reduces risk of corruption if process/system crashes during writes.
        # - Tradeoff: slightly slower writes, but safer.

        # Why this set specifically:
        # - You asked to keep a single DB (no separate custom DB).
        # - Single-DB multi-writer scenarios need safety over speed.
        # - These settings prioritize consistency/durability and reduce corruption probability.

        conn.execute("PRAGMA journal_mode=DELETE;")
        conn.execute("PRAGMA busy_timeout=15000;")
        conn.execute("PRAGMA synchronous=FULL;")
        return conn

    def _init_db(self) -> None:
        # Function Name: _init_db
        # Input: None
        # Output: None
        # Description: Ensure ExecutionLogs table exists with expected key shape.
        # Step 1: Create parent directory when path contains one.
        # Step 2: Create ExecutionLogs table if missing.
        # Step 3: Commit schema setup.
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ExecutionLogs (
                    execution_uuid TEXT NOT NULL,
                    artifact_uri TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    PRIMARY KEY (execution_uuid, artifact_uri)
                )
                """
            )
            conn.commit()

    def insert_execution_log(
        self,
        execution_uuid: str,
        artifact_uri: str,
        metadata: t.Optional[t.Dict[str, t.Any]] = None,
    ) -> None:
        # Function Name: insert_execution_log
        # Input: execution_uuid (str), artifact_uri (str), metadata (dict | None)
        # Output: None
        # Description: Upsert one row per (execution_uuid, artifact_uri) with JSON metadata.
        # Step 1: Validate required keys.
        # Step 2: Serialize metadata to JSON string.
        # Step 3: Insert new row or update existing row for same composite key.
        # Step 4: Commit transaction.
        if not execution_uuid or not artifact_uri:
            return
        payload = json.dumps(metadata or {}, default=str, sort_keys=True)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO ExecutionLogs (
                    execution_uuid,
                    artifact_uri,
                    metadata_json
                ) VALUES (?, ?, ?)
                ON CONFLICT(execution_uuid, artifact_uri)
                DO UPDATE SET metadata_json = excluded.metadata_json
                """,
                (
                    execution_uuid,
                    artifact_uri,
                    payload,
                ),
            )
            conn.commit()

    def get_execution_log(self, execution_uuid: str, artifact_uri: str) -> t.Optional[t.Dict[str, t.Any]]:
        # Function Name: get_execution_log
        # Input: execution_uuid (str), artifact_uri (str)
        # Output: Dict or None
        # Description: Retrieve metadata from ExecutionLogs for (execution_uuid, artifact_uri) pair.
        # Step 1: Validate input parameters are not empty.
        # Step 2: Query ExecutionLogs table using composite key.
        # Step 3: If row found, parse metadata_json and return as dict.
        # Step 4: If row not found or error occurs, return None.
        # Step 5: Log errors if JSON parsing fails.
        
        # Step 1: Skip retrieval if input is invalid.
        if not execution_uuid or not artifact_uri:
            return None
        
        try:
            # Step 2: Open connection and query ExecutionLogs by composite key (execution_uuid, artifact_uri).
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    SELECT metadata_json FROM ExecutionLogs
                    WHERE execution_uuid = ? AND artifact_uri = ?
                    """,
                    (execution_uuid, artifact_uri),
                )
                row = cursor.fetchone()
            
            # Step 3: If row found, deserialize metadata_json from JSON string to dict.
            if row:
                return json.loads(row[0])
            
            # Step 4: Row not found; return None to indicate no custom metadata for this pair.
            return None
        except json.JSONDecodeError as e:
            # Step 5a: Log error if JSON parsing fails (data corruption scenario).
            print(f"Error parsing JSON for ({execution_uuid}, {artifact_uri}): {e}")
            return None
        except Exception as e:
            # Step 5b: Catch other exceptions (DB errors) and return None; caller will use original artifact data.
            print(f"Error querying ExecutionLogs for ({execution_uuid}, {artifact_uri}): {e}")
            return None