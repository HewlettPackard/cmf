"""
Label Search Utility Functions

This module contains all label-related functionality including:
- CSV label file indexing
- Label search statistics
- Auto-reindexing capabilities
- Content hash-based change detection
"""

# Standard library imports
import csv
import io
import json
import time
import os
import hashlib
import re
import logging
from pathlib import Path
from typing import Dict, Any

# Third-party imports
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Set up logger
logger = logging.getLogger(__name__)

# Labels directory constant
LABELS_DIR = "/cmf-server/data/labels"


async def index_csv_labels(database_url: str, labels_directory: str = "/cmf-server/data/labels") -> Dict[str, Any]:
    """
    Index CSV label files into PostgreSQL for full-text search
    """
    try:

        labels_dir = Path(labels_directory)
        if not labels_dir.exists():
            return {"status": "error", "message": f"Labels directory not found: {labels_directory}"}

        # Look for both .csv files and files without extension (assuming they're CSV)
        csv_files = list(labels_dir.glob("*.csv"))

        # Also include files without extension that might be CSV files
        for file_path in labels_dir.iterdir():
            if file_path.is_file() and not file_path.suffix and file_path.name not in [f.stem for f in csv_files]:
                # Try to detect if it's a CSV file by reading first few lines
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        first_line = f.readline().strip()
                        # Simple heuristic: if it contains commas or common CSV patterns, treat as CSV
                        if ',' in first_line or any(keyword in first_line.lower() for keyword in ['file', 'name', 'id', 'type', 'size']):
                            csv_files.append(file_path)
                            logger.info(f"Detected CSV-like file without extension: {file_path.name}")
                except:
                    pass  # Skip files that can't be read

        if not csv_files:
            return {"status": "warning", "message": "No CSV files found", "indexed_files": [], "total_files": 0}

        engine = create_async_engine(database_url, echo=False)
        indexed_files = []
        total_records = 0

        async with engine.begin() as conn:
            for csv_file in csv_files:
                try:
                    # Clear existing data for this file
                    await conn.execute(
                        text("DELETE FROM label_index WHERE file_name = :file_name"),
                        {"file_name": csv_file.name}
                    )

                    # Process CSV file
                    records = []
                    with open(csv_file, 'r', encoding='utf-8') as csvfile:
                        # Detect CSV format with fallback
                        sample = csvfile.read(1024)
                        csvfile.seek(0)

                        # Try to detect delimiter, with fallbacks
                        delimiter = ','  # Default fallback
                        try:
                            sniffer = csv.Sniffer()
                            detected_delimiter = sniffer.sniff(sample).delimiter
                            delimiter = detected_delimiter
                        except:
                            # Fallback: try common delimiters
                            for test_delimiter in [',', '\t', ';', '|']:
                                if test_delimiter in sample:
                                    delimiter = test_delimiter
                                    break

                        reader = csv.DictReader(csvfile, delimiter=delimiter)

                        for row_index, row in enumerate(reader):
                            # Create searchable content
                            content_parts = []
                            metadata = {}

                            for key, value in row.items():
                                if value and value.strip():
                                    content_parts.append(f"{key}: {value.strip()}")
                                    metadata[key] = value.strip()

                            content = " | ".join(content_parts)

                            if content.strip():
                                records.append({
                                    'file_name': csv_file.name,
                                    'file_path': str(csv_file),
                                    'row_index': row_index,
                                    'content': content,
                                    'metadata': json.dumps(metadata),
                                    'created_at': int(time.time() * 1000),
                                    'updated_at': int(time.time() * 1000)
                                })

                    # Insert records
                    if records:
                        insert_query = text("""
                            INSERT INTO label_index (file_name, file_path, row_index, content, metadata, created_at, updated_at)
                            VALUES (:file_name, :file_path, :row_index, :content, :metadata, :created_at, :updated_at)
                        """)
                        await conn.execute(insert_query, records)

                        indexed_files.append({
                            'file_name': csv_file.name,
                            'records_indexed': len(records),
                            'status': 'success'
                        })
                        total_records += len(records)
                        logger.info(f"Indexed {len(records)} records from {csv_file.name}")
                    else:
                        indexed_files.append({
                            'file_name': csv_file.name,
                            'records_indexed': 0,
                            'status': 'empty'
                        })

                except Exception as e:
                    logger.error(f"Error indexing {csv_file.name}: {e}")
                    indexed_files.append({
                        'file_name': csv_file.name,
                        'records_indexed': 0,
                        'status': 'error',
                        'error': str(e)
                    })

        await engine.dispose()

        success_count = sum(1 for f in indexed_files if f['status'] == 'success')
        return {
            'status': 'success',
            'message': f'Indexed {success_count}/{len(csv_files)} files successfully',
            'indexed_files': indexed_files,
            'total_files': len(csv_files),
            'total_records': total_records
        }

    except Exception as e:
        logger.error(f"Label indexing failed: {e}")
        return {"status": "error", "message": str(e)}


async def get_label_stats(database_url: str) -> Dict[str, Any]:
    """
    Get statistics about indexed labels
    """
    try:

        engine = create_async_engine(database_url, echo=False)

        async with engine.begin() as conn:
            # Get total records and files
            result = await conn.execute(text("""
                SELECT
                    COUNT(*) as total_records,
                    COUNT(DISTINCT file_name) as total_files
                FROM label_index
            """))
            stats = result.fetchone()

            # Get recent files
            result = await conn.execute(text("""
                SELECT file_name, COUNT(*) as record_count, MAX(updated_at) as last_updated
                FROM label_index
                GROUP BY file_name
                ORDER BY last_updated DESC
                LIMIT 10
            """))
            recent_files = [
                {
                    'file_name': row[0],
                    'record_count': row[1],
                    'last_updated': row[2]
                }
                for row in result.fetchall()
            ]

        await engine.dispose()

        return {
            'total_records': stats[0] if stats else 0,
            'total_files': stats[1] if stats else 0,
            'recent_files': recent_files,
            'status': 'success'
        }

    except Exception as e:
        logger.error(f"Error getting label stats: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'total_records': 0,
            'total_files': 0,
            'recent_files': []
        }


async def auto_reindex_if_needed(database_url: str, labels_directory: str = "/cmf-server/data/labels") -> Dict[str, Any]:
    """
    Automatically reindex labels if files have been modified or content has changed.
    Handles MD5 hash filenames and detects content changes.
    """
    try:

        labels_dir = Path(labels_directory)
        if not labels_dir.exists():
            return {"status": "no_directory", "message": "Labels directory does not exist"}

        # Get all potential CSV files (with and without .csv extension)
        csv_files = list(labels_dir.glob("*.csv"))

        # Also check files without extension (including MD5 hash names)
        for file_path in labels_dir.iterdir():
            if file_path.is_file() and not file_path.suffix:
                # Check if it's an MD5 hash (32 hex characters)
                is_md5_hash = bool(re.match(r'^[a-f0-9]{32}$', file_path.name))

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        first_line = f.readline().strip()
                        # For MD5 hash files, be more lenient in detection
                        if is_md5_hash or ',' in first_line or any(keyword in first_line.lower() for keyword in ['file', 'name', 'id', 'type', 'size']):
                            csv_files.append(file_path)
                            if is_md5_hash:
                                logger.info(f"Detected MD5 hash file: {file_path.name}")
                except:
                    pass

        if not csv_files:
            return {"status": "no_files", "message": "No CSV files found"}

        # Check if we need to reindex based on content changes
        engine = create_async_engine(database_url, echo=False)
        needs_reindex = False
        files_to_reindex = []

        async with engine.begin() as conn:
            for csv_file in csv_files:
                # Calculate content hash for change detection
                try:
                    with open(csv_file, 'rb') as f:
                        content_hash = hashlib.md5(f.read()).hexdigest()
                except:
                    continue

                # Check if file exists in index and get its content hash
                result = await conn.execute(text("""
                    SELECT
                        MAX(updated_at) as last_indexed,
                        COUNT(*) as record_count
                    FROM label_index
                    WHERE file_name = :file_name
                """), {"file_name": csv_file.name})

                row = result.fetchone()
                last_indexed = row[0] if row else None
                record_count = row[1] if row else 0

                # Get stored content hash from metadata if available
                result = await conn.execute(text("""
                    SELECT metadata->>'content_hash' as stored_hash
                    FROM label_index
                    WHERE file_name = :file_name
                    LIMIT 1
                """), {"file_name": csv_file.name})

                stored_hash_row = result.fetchone()
                stored_hash = stored_hash_row[0] if stored_hash_row else None

                # Check if reindexing is needed
                file_mtime = int(os.path.getmtime(csv_file) * 1000)

                if (not last_indexed or
                    record_count == 0 or
                    stored_hash != content_hash or
                    file_mtime > (last_indexed + 60000)):  # 1 minute grace period

                    needs_reindex = True
                    files_to_reindex.append({
                        'file': csv_file,
                        'reason': 'new' if not last_indexed else 'content_changed' if stored_hash != content_hash else 'modified'
                    })
                    logger.info(f"File {csv_file.name} needs reindexing - {files_to_reindex[-1]['reason']}")

        await engine.dispose()

        if needs_reindex:
            logger.info(f"Auto-reindexing {len(files_to_reindex)} files...")
            result = await index_csv_labels_with_hash(database_url, labels_directory)
            return {
                "status": "reindexed",
                "message": f"Auto-reindexed {result.get('total_files', 0)} files",
                "files_reindexed": [f['file'].name for f in files_to_reindex],
                "details": result
            }
        else:
            return {
                "status": "up_to_date",
                "message": "All label files are up to date"
            }

    except Exception as e:
        logger.error(f"Auto-reindex failed: {e}")
        return {"status": "error", "message": str(e)}


async def index_csv_labels_with_hash(database_url: str, labels_directory: str = "/cmf-server/data/labels") -> Dict[str, Any]:
    """
    Enhanced version of index_csv_labels that stores content hashes for change detection
    """
    try:

        labels_dir = Path(labels_directory)
        if not labels_dir.exists():
            return {"status": "error", "message": f"Labels directory not found: {labels_directory}"}

        # Get all potential CSV files (including MD5 hash files)
        csv_files = list(labels_dir.glob("*.csv"))

        # Also include files without extension
        for file_path in labels_dir.iterdir():
            if file_path.is_file() and not file_path.suffix:
                is_md5_hash = bool(re.match(r'^[a-f0-9]{32}$', file_path.name))
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        first_line = f.readline().strip()
                        if is_md5_hash or ',' in first_line or any(keyword in first_line.lower() for keyword in ['file', 'name', 'id', 'type', 'size']):
                            csv_files.append(file_path)
                except:
                    pass

        if not csv_files:
            return {"status": "warning", "message": "No CSV files found", "indexed_files": [], "total_files": 0}

        engine = create_async_engine(database_url, echo=False)
        indexed_files = []
        total_records = 0

        async with engine.begin() as conn:
            for csv_file in csv_files:
                try:
                    # Calculate content hash
                    with open(csv_file, 'rb') as f:
                        content_hash = hashlib.md5(f.read()).hexdigest()

                    # Clear existing data for this file
                    await conn.execute(
                        text("DELETE FROM label_index WHERE file_name = :file_name"),
                        {"file_name": csv_file.name}
                    )

                    # Process CSV file
                    records = []
                    with open(csv_file, 'r', encoding='utf-8') as csvfile:
                        # Detect CSV format with fallback
                        sample = csvfile.read(1024)
                        csvfile.seek(0)

                        # Try to detect delimiter, with fallbacks
                        delimiter = ','  # Default fallback
                        try:
                            sniffer = csv.Sniffer()
                            detected_delimiter = sniffer.sniff(sample).delimiter
                            delimiter = detected_delimiter
                        except:
                            # Fallback: try common delimiters
                            for test_delimiter in [',', '\t', ';', '|']:
                                if test_delimiter in sample:
                                    delimiter = test_delimiter
                                    break

                        reader = csv.DictReader(csvfile, delimiter=delimiter)

                        for row_index, row in enumerate(reader):
                            # Create searchable content
                            content_parts = []
                            metadata = {"content_hash": content_hash}  # Store content hash

                            for key, value in row.items():
                                if value and value.strip():
                                    content_parts.append(f"{key}: {value.strip()}")
                                    metadata[key] = value.strip()

                            content = " | ".join(content_parts)

                            if content.strip():
                                records.append({
                                    'file_name': csv_file.name,
                                    'file_path': str(csv_file),
                                    'row_index': row_index,
                                    'content': content,
                                    'metadata': json.dumps(metadata),
                                    'created_at': int(time.time() * 1000),
                                    'updated_at': int(time.time() * 1000)
                                })

                    # Insert records
                    if records:
                        insert_query = text("""
                            INSERT INTO label_index (file_name, file_path, row_index, content, metadata, created_at, updated_at)
                            VALUES (:file_name, :file_path, :row_index, :content, :metadata, :created_at, :updated_at)
                        """)
                        await conn.execute(insert_query, records)

                        indexed_files.append({
                            'file_name': csv_file.name,
                            'records_indexed': len(records),
                            'content_hash': content_hash,
                            'status': 'success'
                        })
                        total_records += len(records)
                        logger.info(f"Indexed {len(records)} records from {csv_file.name} (hash: {content_hash[:8]}...)")
                    else:
                        indexed_files.append({
                            'file_name': csv_file.name,
                            'records_indexed': 0,
                            'status': 'empty'
                        })

                except Exception as e:
                    logger.error(f"Error indexing {csv_file.name}: {e}")
                    indexed_files.append({
                        'file_name': csv_file.name,
                        'records_indexed': 0,
                        'status': 'error',
                        'error': str(e)
                    })

        await engine.dispose()

        success_count = sum(1 for f in indexed_files if f['status'] == 'success')
        return {
            'status': 'success',
            'message': f'Indexed {success_count}/{len(csv_files)} files successfully',
            'indexed_files': indexed_files,
            'total_files': len(csv_files),
            'total_records': total_records
        }

    except Exception as e:
        logger.error(f"Label indexing failed: {e}")
        return {"status": "error", "message": str(e)}


# Label File Loading Functions
async def initialize_label_search():
    """Initialize label search functionality on startup"""
    try:
        logger.info("Initializing label search functionality...")

        # Check primary directory for CSV files
        primary_dir = Path(LABELS_DIR)
        csv_files = []

        if primary_dir.exists():
            csv_files = list(primary_dir.glob("*.csv"))

        if csv_files:
            logger.info(f"Found {len(csv_files)} CSV label files in primary directory: {primary_dir}")

            # Check if we need to index (if no records exist)
            from server.app.db.dbconfig import DATABASE_URL
            stats = await get_label_stats(DATABASE_URL)
            if stats['total_records'] == 0:
                logger.info("Indexing label files...")
                result = await index_csv_labels(DATABASE_URL)
                logger.info(f"Indexed {result.get('total_records', 0)} records from {result.get('total_files', 0)} files")
            else:
                logger.info(f"Label search ready: {stats['total_records']} records indexed")
        else:
            logger.info(f"No CSV label files found in primary directory: {primary_dir}")

        # Log the labels directory being used
        logger.info(f"Labels directory: {LABELS_DIR}")

    except Exception as e:
        logger.warning(f"Label search initialization failed: {e}")
        logger.info("Label search will be available once configured properly")


async def filter_labels_by_csv_content(label_artifacts: list, conditions: list) -> list:
    """
    Filter label artifacts by checking if their CSV content matches the advanced search conditions.

    Args:
        label_artifacts: List of label artifact dictionaries
        conditions: List of SearchCondition objects

    Returns:
        List of artifacts that contain CSV rows matching the conditions
    """
    matching_artifacts = []

    for artifact in label_artifacts:
        try:
            # Try to load the CSV content for this label
            csv_content = await load_label_csv_content(artifact)
            if not csv_content:
                continue

            # Parse CSV content
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            csv_rows = list(csv_reader)

            if not csv_rows:
                continue

            # Apply advanced search conditions to CSV rows
            from server.app.search_utils import LabelSearchFilter
            matching_rows = LabelSearchFilter.apply_conditions(csv_rows, conditions)

            # If any rows match, include this artifact
            if matching_rows:
                matching_artifacts.append(artifact)

        except Exception:
            continue

    return matching_artifacts


async def load_label_csv_content(artifact: dict) -> str:
    """
    Load CSV content for a label artifact.

    Args:
        artifact: Label artifact dictionary

    Returns:
        CSV content as string, or None if not found
    """
    try:
        # Try different ways to get the file path
        file_paths_to_try = []

        # Method 1: Use URI if available
        if artifact.get('uri'):
            uri = artifact['uri']
            if ':' in uri:
                file_name = uri.split(':', 1)[1]
                file_paths_to_try.append(file_name)
            file_paths_to_try.append(uri)

        # Method 2: Use artifact name
        if artifact.get('name'):
            name = artifact['name']
            # Extract the base filename from the artifact name
            # e.g., "artifacts/labels_m.csv:93951bf..." -> "labels_m.csv"
            if 'artifacts/' in name and ':' in name:
                # Extract the part between "artifacts/" and ":"
                parts = name.split('artifacts/', 1)
                if len(parts) > 1:
                    file_part = parts[1].split(':', 1)[0]
                    file_paths_to_try.append(file_part)

            # Clean the name - remove prefixes
            if ':' in name:
                clean_name = name.split(':', 1)[1]
                file_paths_to_try.append(clean_name)
            file_paths_to_try.append(name)
            file_paths_to_try.append(f"{name}.csv")

        # Try to load the file from the labels directory
        labels_dir = LABELS_DIR
        if os.path.exists(labels_dir):
            # First try exact matches
            for file_path in file_paths_to_try:
                try:
                    full_path = os.path.join(labels_dir, os.path.basename(file_path))
                    if os.path.exists(full_path):
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            return content
                except Exception:
                    continue

            # Then try partial matches for CSV files
            try:
                csv_files = list(Path(labels_dir).glob("*.csv"))
                for file_path_to_try in file_paths_to_try:
                    base_name = os.path.basename(file_path_to_try).lower()
                    # Remove common extensions and hash suffixes for matching
                    clean_name = base_name.split('.')[0].split(':')[0]

                    for csv_file in csv_files:
                        csv_name = csv_file.name.lower()
                        # Check if the clean name is contained in the CSV filename
                        if clean_name in csv_name or csv_name.split('.')[0] in clean_name:
                            try:
                                with open(csv_file, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                    return content
                            except Exception:
                                continue
            except Exception:
                pass

            # Also try all CSV files in the directory as fallback
            # Return the most recently modified CSV file if multiple exist
            try:
                csv_files = list(Path(labels_dir).glob("*.csv"))
                if csv_files:
                    # Sort by modification time, most recent first
                    csv_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                    for file_path in csv_files:
                        if file_path.is_file():
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                    return content
                            except Exception:
                                continue
            except Exception:
                pass

        return None

    except Exception:
        return None


async def load_label_csv_by_filename(file_name: str, pipeline_name: str = None) -> str:
    """
    Load CSV content by filename, handling both hash names and actual filenames.

    Args:
        file_name: The filename (could be hash or actual filename)
        pipeline_name: Optional pipeline name to help locate artifacts

    Returns:
        CSV content as string, or None if not found
    """
    try:
        # Try to load using the same logic as load_label_csv_content
        # Create a mock artifact to use the existing loading logic
        mock_artifact = {
            'name': file_name,
            'uri': file_name
        }

        # Try the existing loading logic first
        content = await load_label_csv_content(mock_artifact)
        if content:
            return content

        # If that fails, try additional strategies for hash-based filenames
        # Try to find CSV files that might correspond to this hash
        labels_dir = LABELS_DIR
        if os.path.exists(labels_dir):
            # Try direct filename match first
            direct_path = os.path.join(labels_dir, file_name)
            if os.path.exists(direct_path):
                with open(direct_path, 'r', encoding='utf-8') as f:
                    return f.read()

            # Try with .csv extension
            csv_path = os.path.join(labels_dir, f"{file_name}.csv")
            if os.path.exists(csv_path):
                with open(csv_path, 'r', encoding='utf-8') as f:
                    return f.read()

            # If filename looks like a hash, try all CSV files in the directory
            # Return the most recently modified CSV file
            if len(file_name) > 20 and all(c in '0123456789abcdef' for c in file_name.lower()):
                try:
                    csv_files = list(Path(labels_dir).glob("*.csv"))
                    if csv_files:
                        # Sort by modification time, most recent first
                        csv_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                        for file_path in csv_files:
                            if file_path.is_file():
                                try:
                                    with open(file_path, 'r', encoding='utf-8') as f:
                                        return f.read()
                                except Exception:
                                    continue
                except Exception:
                    pass

        return None

    except Exception:
        return None
