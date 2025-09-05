"""
Label Management Module

This module provides comprehensive label management functionality including:
- CSV label file indexing and database operations
- Advanced search query parsing and filtering
- Label search initialization and statistics
- Content hash-based change detection
- JSONB query building for PostgreSQL

Combines functionality from the former label_utils.py and search_utils.py
"""

# Standard library imports
import csv
import json
import time
import os
import hashlib
import re
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Union
from enum import Enum

# Third-party imports
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

# Set up logger
logger = logging.getLogger(__name__)

# Labels directory constant
LABELS_DIR = "/cmf-server/data/labels"


# SEARCH QUERY PARSING AND FILTERING
class ComparisonOperator(Enum):
    """Supported comparison operators"""
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    EQUAL = "="
    NOT_EQUAL = "!="
    CONTAINS = "~"  # For text contains (case-insensitive)
    NOT_CONTAINS = "!~"  # For text does not contain

class SearchCondition:
    """
    Represents a single search condition for advanced label search queries.

    This class encapsulates a structured search condition that can be converted
    into PostgreSQL JSONB queries for efficient database searching.

    Examples:
        SearchCondition("lines", ComparisonOperator.GREATER_THAN, 240)
        SearchCondition("score", ComparisonOperator.LESS_EQUAL, 0.5)
        SearchCondition("status", ComparisonOperator.EQUAL, "active")
        SearchCondition("name", ComparisonOperator.CONTAINS, "test")

    Attributes:
        column: The CSV column name to search in
        operator: The comparison operator to apply
        value: The value to compare against (auto-typed)
    """
    def __init__(self, column: str, operator: ComparisonOperator, value: Union[str, int, float]):
        self.column = column.strip()
        self.operator = operator
        self.value = value

    def __repr__(self):
        return f"SearchCondition({self.column} {self.operator.value} {self.value})"

class AdvancedSearchParser:
    """
    Parser for advanced search queries with comparison operators.

    This class enables users to perform sophisticated searches on CSV label content
    using structured query syntax. It parses queries like:
    - "lines>240 score<=0.5 status=active"
    - "name~test AND size>=1000"
    - 'description="error message" OR type!=warning'

    Supported Features:
    - Numeric comparisons: >, <, >=, <=, =, !=
    - Text operations: ~ (contains), !~ (not contains)
    - Quoted values: "value with spaces", 'single quotes'
    - Mixed queries: Combines structured conditions with plain text search

    The parser separates structured conditions from plain text terms,
    enabling hybrid search that uses both JSONB queries and full-text search.
    """

    # Regex pattern to match search conditions
    # Captures: column_name operator "quoted_value" or unquoted_value
    # Supports all comparison operators with flexible whitespace handling
    CONDITION_PATTERN = re.compile(
        r'(\w+)\s*(>=|<=|!=|!~|>|<|=|~)\s*("([^"]*)"|\'([^\']*)\'|([^\s,]+))',
        re.IGNORECASE
    )
    
    @classmethod
    def parse_search_query(cls, query: str) -> Tuple[List[SearchCondition], List[str], List[str]]:
        """
        Parse a search query into structured conditions and plain text terms.

        Args:
            query: Search query string (e.g., "lines>240 score<=0.5 test")

        Returns:
            Tuple of (conditions, plain_text_terms, errors)
        """
        conditions = []
        errors = []

        # Step 1: Find all structured conditions using regex
        # This captures patterns like "column>value", "name='quoted value'", etc.
        matches = cls.CONDITION_PATTERN.findall(query)
        matched_positions = []

        # Track positions of matched conditions so we can remove them later
        # This allows us to extract remaining text as plain search terms
        for match in cls.CONDITION_PATTERN.finditer(query):
            matched_positions.append((match.start(), match.end()))

        # Step 2: Process each structured condition
        for match in matches:
            # Regex groups: (column, operator, full_value, quoted1, quoted2, unquoted)
            column, operator_str, _, quoted_value1, quoted_value2, unquoted_value = match

            # Extract the actual value - prioritize quoted values over unquoted
            # This handles cases like: name="test value" vs name=test
            value = quoted_value1 or quoted_value2 or unquoted_value

            try:
                # Convert operator string to enum (validates supported operators)
                operator = ComparisonOperator(operator_str)

                # Convert value to appropriate type based on operator context
                # This enables proper numeric comparisons and text operations
                parsed_value = cls._parse_value(value, operator)

                # Create structured condition object for database query building
                conditions.append(SearchCondition(column, operator, parsed_value))

            except ValueError as e:
                # Collect parsing errors without stopping the entire parse
                # This allows partial success - valid conditions work, invalid ones are reported
                errors.append(f"Invalid condition '{column}{operator_str}{value}': {str(e)}")

        # Step 3: Extract remaining text as plain search terms
        # Remove all structured conditions from the original query
        remaining_text = query
        # Process in reverse order to maintain correct string positions
        for start, end in reversed(matched_positions):
            remaining_text = remaining_text[:start] + remaining_text[end:]

        # Split remaining text into individual terms, filtering out empty strings
        # These terms will be used for full-text search
        plain_terms = [term.strip() for term in remaining_text.split() if term.strip()]

        return conditions, plain_terms, errors
    
    @classmethod
    def _parse_value(cls, value: str, operator: ComparisonOperator) -> Union[str, int, float]:
        """Parse value string to appropriate type based on operator"""

        # Text operations: Keep values as strings for ILIKE operations
        if operator in [ComparisonOperator.CONTAINS, ComparisonOperator.NOT_CONTAINS]:
            return value  # No conversion needed for text matching

        # Equality operations: Try numeric conversion but allow strings
        if operator in [ComparisonOperator.EQUAL, ComparisonOperator.NOT_EQUAL]:
            # Attempt intelligent type detection for flexible comparisons
            try:
                # Check for decimal point to distinguish int vs float
                if '.' in value:
                    return float(value)  # Decimal numbers become floats
                else:
                    return int(value)    # Whole numbers become integers
            except ValueError:
                # If numeric conversion fails, keep as string
                # This allows comparisons like: status="active"
                return value

        # Numeric comparisons: Require valid numbers
        if operator in [ComparisonOperator.GREATER_THAN, ComparisonOperator.LESS_THAN,
                       ComparisonOperator.GREATER_EQUAL, ComparisonOperator.LESS_EQUAL]:
            try:
                # Parse as appropriate numeric type
                if '.' in value:
                    return float(value)  # Handle decimal comparisons: score<=0.85
                else:
                    return int(value)    # Handle integer comparisons: lines>240
            except ValueError:
                # Numeric operators require valid numbers - this is a user error
                raise ValueError(f"Numeric value expected for operator {operator.value}, got '{value}'")

        # Fallback for any unhandled operators
        return value


class JsonbQueryBuilder:
    """
    Build PostgreSQL JSONB queries from SearchCondition objects for high-performance search.

    This class converts structured search conditions into optimized PostgreSQL JSONB queries
    that can efficiently search through parsed CSV data stored in the database.

    Key Features:
    - Case-insensitive column name matching (handles "Lines" vs "lines")
    - Automatic type casting for numeric comparisons
    - Support for text operations (ILIKE for contains/not contains)
    - Parameterized queries to prevent SQL injection
    - Flexible column name handling with whitespace tolerance

    Query Generation Process:
    1. Takes SearchCondition objects from AdvancedSearchParser
    2. Builds PostgreSQL WHERE clauses using JSONB operators
    3. Handles type conversion and case sensitivity
    4. Returns parameterized query components for safe execution

    Performance Benefits:
    - Uses PostgreSQL's native JSONB indexing capabilities
    - Enables complex queries without full table scans
    - Supports efficient numeric range queries
    - Leverages database-level type casting and comparison
    """

    @classmethod
    def _get_case_insensitive_column_value(cls, column_key: str) -> str:
        """
        Generate SQL to get column value with case-insensitive matching and whitespace handling.
        This handles cases where user searches for 'lines' but CSV has 'Lines', ' Lines', etc.
        """
        # Two-tier approach for robust column matching:
        # 1. First try exact key match (fastest path)
        # 2. Fall back to case-insensitive search with whitespace trimming
        return f"""COALESCE(
            parsed_data->>:{column_key},
            (SELECT value FROM jsonb_each_text(parsed_data) WHERE lower(trim(key)) = lower(:{column_key}) LIMIT 1)
        )"""

    @classmethod
    def build_where_clause(cls, conditions: List[SearchCondition]) -> Tuple[str, Dict[str, Any]]:
        """
        Build a PostgreSQL WHERE clause for JSONB queries from search conditions.

        Args:
            conditions: List of SearchCondition objects

        Returns:
            Tuple of (where_clause, parameters)
        """
        # Early return for empty conditions to avoid unnecessary processing
        if not conditions:
            return "", {}

        where_parts = []
        params = {}

        # Process each condition into a SQL clause with unique parameter names
        for i, condition in enumerate(conditions):
            # Use index-based parameter naming to avoid conflicts
            clause, condition_params = cls._build_condition_clause(condition, i)
            if clause:  # Only include valid clauses
                where_parts.append(clause)
                params.update(condition_params)

        # Safety check - ensure we have valid clauses to combine
        if not where_parts:
            return "", {}

        # Combine all conditions with AND logic
        # Note: Future enhancement could support OR logic with parentheses
        where_clause = " AND ".join(where_parts)
        return where_clause, params

    @classmethod
    def _build_condition_clause(cls, condition: SearchCondition, index: int) -> Tuple[str, Dict[str, Any]]:
        """
        Build a single condition clause for JSONB query.

        Args:
            condition: SearchCondition object
            index: Index for parameter naming

        Returns:
            Tuple of (clause, parameters)
        """
        # Generate unique parameter names to avoid conflicts in complex queries
        column_key = f"col_{index}"
        value_key = f"val_{index}"

        # Get SQL for extracting column value with case-insensitive matching
        column_value_sql = cls._get_case_insensitive_column_value(column_key)

        # Text containment operations: Use PostgreSQL ILIKE for case-insensitive matching
        if condition.operator == ComparisonOperator.CONTAINS:
            # ILIKE with wildcards for substring matching: "name~test" → name ILIKE '%test%'
            clause = f"({column_value_sql}) ILIKE :{value_key}"
            params = {
                column_key: condition.column,
                value_key: f"%{condition.value}%"  # Add wildcards for partial matching
            }

        elif condition.operator == ComparisonOperator.NOT_CONTAINS:
            # NOT ILIKE for exclusion: "name!~error" → name NOT ILIKE '%error%'
            clause = f"({column_value_sql}) NOT ILIKE :{value_key}"
            params = {
                column_key: condition.column,
                value_key: f"%{condition.value}%"  # Add wildcards for partial matching
            }

        # Equality operations: Handle both numeric and text comparisons
        elif condition.operator == ComparisonOperator.EQUAL:
            if isinstance(condition.value, (int, float)):
                # Numeric equality: Cast JSONB value to numeric for proper comparison
                clause = f"({column_value_sql})::numeric = :{value_key}"
            else:
                # Text equality: Case-insensitive comparison using LOWER()
                clause = f"LOWER({column_value_sql}) = LOWER(:{value_key})"
            params = {
                column_key: condition.column,
                value_key: condition.value
            }

        elif condition.operator == ComparisonOperator.NOT_EQUAL:
            if isinstance(condition.value, (int, float)):
                # Numeric inequality: Cast for proper numeric comparison
                clause = f"({column_value_sql})::numeric != :{value_key}"
            else:
                # Text inequality: Case-insensitive comparison
                clause = f"LOWER({column_value_sql}) != LOWER(:{value_key})"
            params = {
                column_key: condition.column,
                value_key: condition.value
            }

        # Numeric comparison operations: All require casting to numeric type
        elif condition.operator == ComparisonOperator.GREATER_THAN:
            # Greater than: "lines>240" → (parsed_data->>'lines')::numeric > 240
            clause = f"({column_value_sql})::numeric > :{value_key}"
            params = {
                column_key: condition.column,
                value_key: condition.value
            }

        elif condition.operator == ComparisonOperator.LESS_THAN:
            # Less than: "score<0.5" → (parsed_data->>'score')::numeric < 0.5
            clause = f"({column_value_sql})::numeric < :{value_key}"
            params = {
                column_key: condition.column,
                value_key: condition.value
            }

        elif condition.operator == ComparisonOperator.GREATER_EQUAL:
            # Greater than or equal: "size>=1000" → (parsed_data->>'size')::numeric >= 1000
            clause = f"({column_value_sql})::numeric >= :{value_key}"
            params = {
                column_key: condition.column,
                value_key: condition.value
            }

        elif condition.operator == ComparisonOperator.LESS_EQUAL:
            # Less than or equal: "confidence<=0.95" → (parsed_data->>'confidence')::numeric <= 0.95
            clause = f"({column_value_sql})::numeric <= :{value_key}"
            params = {
                column_key: condition.column,
                value_key: condition.value
            }

        else:
            # Unsupported operator - return empty clause (will be filtered out)
            return "", {}

        return clause, params


# CSV PARSING AND VALUE CONVERSION
def parse_csv_value(value: str):
    """
    Parse a CSV value and convert it to the appropriate Python type for JSONB storage.

    This function enables advanced search capabilities by converting CSV string values
    into their appropriate types, allowing for:
    - Numeric comparisons (e.g., "lines>240", "score<=0.5")
    - Boolean filtering (e.g., "active=true")
    - Proper sorting and range queries in PostgreSQL JSONB

    Type Detection Logic:
    1. Empty/whitespace values → None
    2. Boolean values (true/false/yes/no/1/0) → bool
    3. Integer values (no decimal point) → int
    4. Floating point values → float
    5. Everything else → string (preserved as-is)

    Args:
        value: String value from CSV cell

    Returns:
        Parsed value (int, float, bool, None, or string) suitable for JSONB storage

    Examples:
        parse_csv_value("240") → 240 (int)
        parse_csv_value("0.85") → 0.85 (float)
        parse_csv_value("true") → True (bool)
        parse_csv_value("active") → "active" (str)
        parse_csv_value("  ") → None
    """
    # Handle empty or whitespace-only values
    if not value or not value.strip():
        return None

    value = value.strip()

    # Boolean detection: Check common boolean representations
    # This enables searches like "active=true" or "enabled=yes"
    if value.lower() in ('true', 'false', 'yes', 'no', '1', '0'):
        if value.lower() in ('true', 'yes', '1'):
            return True
        elif value.lower() in ('false', 'no', '0'):
            return False

    # Integer detection: Avoid scientific notation and decimals
    try:
        # Exclude scientific notation (1e5) and decimals to ensure clean integers
        if '.' not in value and 'e' not in value.lower():
            return int(value)  # Clean integer values like "240", "1000"
    except ValueError:
        pass  # Not an integer, continue to next type

    # Float detection: Handle decimal numbers and scientific notation
    try:
        return float(value)  # Handles "0.85", "1.5", "1e-3", etc.
    except ValueError:
        pass  # Not a float, treat as string

    # Default: Return as string for text values
    # This preserves original formatting for text searches
    return value


# DATABASE OPERATIONS FOR LABEL INDEXING
async def index_csv_labels(db: AsyncSession, labels_directory: str = "/cmf-server/data/labels") -> Dict[str, Any]:
    """
    Index CSV label files into PostgreSQL for full-text search.

    This function scans the labels directory for CSV files and indexes their content
    into the label_index table for efficient searching. It handles:
    - CSV files with .csv extension
    - Files without extension that appear to be CSV format
    - Automatic delimiter detection
    - Content parsing and metadata extraction
    - Full-text search vector creation

    Args:
        db: Database session for executing queries
        labels_directory: Path to directory containing CSV label files

    Returns:
        Dictionary containing indexing results:
        - status: 'success', 'warning', or 'error'
        - message: Human-readable status message
        - indexed_files: List of file indexing results
        - total_files: Number of files processed
        - total_records: Total records indexed across all files

    Note:
        This function clears existing data for each file before reindexing.
        For change detection and incremental updates, use index_csv_labels_with_hash().
    """
    try:

        labels_dir = Path(labels_directory)
        if not labels_dir.exists():
            return {"status": "error", "message": f"Labels directory not found: {labels_directory}"}

        # Step 1: Find all potential CSV files using multiple strategies
        # Start with obvious .csv files
        csv_files = list(labels_dir.glob("*.csv"))

        # Step 2: Auto-detect CSV files without extensions (including hash-based names)
        # This handles cases where files are uploaded without proper extensions
        for file_path in labels_dir.iterdir():
            if file_path.is_file() and not file_path.suffix and file_path.name not in [f.stem for f in csv_files]:
                # Content-based CSV detection using heuristics
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        first_line = f.readline().strip()
                        # Heuristic: Look for CSV indicators in the first line
                        # - Comma separators (most common)
                        # - Common CSV header keywords
                        if ',' in first_line or any(keyword in first_line.lower() for keyword in ['file', 'name', 'id', 'type', 'size']):
                            csv_files.append(file_path)
                            logger.info(f"Detected CSV-like file without extension: {file_path.name}")
                except:
                    # Silently skip files that can't be read (permissions, binary files, etc.)
                    pass

        if not csv_files:
            return {"status": "warning", "message": "No CSV files found", "indexed_files": [], "total_files": 0}

        indexed_files = []
        total_records = 0

        # Step 3: Process each CSV file for indexing
        for csv_file in csv_files:
            try:
                # Clean slate: Remove any existing data for this file
                # This ensures fresh indexing without duplicate records
                await db.execute(
                    text("DELETE FROM label_index WHERE file_name = :file_name"),
                    {"file_name": csv_file.name}
                )

                # Step 4: Parse CSV file with robust format detection
                records = []
                with open(csv_file, 'r', encoding='utf-8') as csvfile:
                    # Read sample for delimiter detection
                    sample = csvfile.read(1024)
                    csvfile.seek(0)  # Reset file pointer

                    # Intelligent delimiter detection with fallbacks
                    delimiter = ','  # Safe default
                    try:
                        # Use Python's CSV sniffer for automatic detection
                        sniffer = csv.Sniffer()
                        detected_delimiter = sniffer.sniff(sample).delimiter
                        delimiter = detected_delimiter
                    except:
                        # Fallback strategy: Test common delimiters by frequency in sample
                        for test_delimiter in [',', '\t', ';', '|']:
                            if test_delimiter in sample:
                                delimiter = test_delimiter
                                break
                        # Note: Comma remains default if no delimiters found

                    # Create CSV reader with detected format
                    reader = csv.DictReader(csvfile, delimiter=delimiter)

                    # Step 5: Process each row for full-text search indexing
                    for row_index, row in enumerate(reader):
                        # Build searchable content from all non-empty fields
                        content_parts = []
                        metadata = {}

                        # Extract and clean all field values
                        for key, value in row.items():
                            if value and value.strip():  # Skip empty/whitespace values
                                # Format for full-text search: "column: value"
                                content_parts.append(f"{key}: {value.strip()}")
                                # Store clean value in metadata
                                metadata[key] = value.strip()

                        # Combine all fields into searchable text
                        # Format: "col1: val1 | col2: val2 | col3: val3"
                        content = " | ".join(content_parts)

                        # Only index rows with actual content
                        if content.strip():
                            records.append({
                                'file_name': csv_file.name,
                                'file_path': str(csv_file),
                                'row_index': row_index,
                                'content': content,  # For full-text search
                                'metadata': json.dumps(metadata),  # For display/filtering
                                'created_at': int(time.time() * 1000),  # Timestamp in milliseconds
                                'updated_at': int(time.time() * 1000)
                            })

                # Step 6: Bulk insert records into database
                if records:
                    # Use parameterized query for security and performance
                    insert_query = text("""
                        INSERT INTO label_index (file_name, file_path, row_index, content, metadata, created_at, updated_at)
                        VALUES (:file_name, :file_path, :row_index, :content, :metadata, :created_at, :updated_at)
                    """)
                    # Bulk insert all records for this file in one operation
                    await db.execute(insert_query, records)

                    # Track successful indexing
                    indexed_files.append({
                        'file_name': csv_file.name,
                        'records_indexed': len(records),
                        'status': 'success'
                    })
                    total_records += len(records)
                    logger.info(f"Indexed {len(records)} records from {csv_file.name}")
                else:
                    # Handle empty files (no content rows)
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

        await db.commit()

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


async def get_label_stats(db: AsyncSession) -> Dict[str, Any]:
    """
    Get comprehensive statistics about indexed label files and records.

    This function provides insights into the current state of the label search system:
    - Total number of indexed records across all files
    - Total number of unique label files indexed
    - Recent file activity with record counts and timestamps

    Args:
        db: Database session for executing queries

    Returns:
        Dictionary containing label statistics:
        - total_records: Total number of indexed records
        - total_files: Total number of unique label files
        - recent_files: List of recent files with metadata
        - status: 'success' or 'error'
        - error: Error message if status is 'error'

    Use Cases:
        - System health monitoring and dashboards
        - Debugging label search issues
        - Administrative oversight of indexed content
        - Capacity planning for label storage
    """
    try:
        # Query 1: Get overall statistics (total records and unique files)
        result = await db.execute(text("""
            SELECT
                COUNT(*) as total_records,
                COUNT(DISTINCT file_name) as total_files
            FROM label_index
        """))
        stats = result.fetchone()

        # Query 2: Get recent file activity for monitoring/debugging
        result = await db.execute(text("""
            SELECT file_name, COUNT(*) as record_count, MAX(updated_at) as last_updated
            FROM label_index
            GROUP BY file_name
            ORDER BY last_updated DESC
            LIMIT 10
        """))
        # Convert query results to structured format
        recent_files = [
            {
                'file_name': row[0],
                'record_count': row[1],
                'last_updated': row[2]  # Timestamp in milliseconds
            }
            for row in result.fetchall()
        ]

        # Return comprehensive statistics
        return {
            'total_records': stats[0] if stats else 0,  # Handle empty database
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


async def auto_reindex_if_needed(db: AsyncSession, labels_directory: str = "/cmf-server/data/labels") -> Dict[str, Any]:
    """
    Automatically reindex labels if files have been modified or content has changed.

    This intelligent reindexing function performs change detection to avoid unnecessary
    reprocessing of unchanged files. It handles:
    - MD5 hash-based filenames (32 hex character names)
    - Content hash comparison for change detection
    - File modification time checking
    - Graceful handling of new, modified, and deleted files

    Change Detection Strategy:
    1. Calculates MD5 hash of current file content
    2. Compares with stored content hash in database
    3. Checks file modification time vs last index time
    4. Only reindexes files that have actually changed

    Args:
        db: Database session for executing queries
        labels_directory: Path to directory containing CSV label files

    Returns:
        Dictionary containing reindex results:
        - status: 'reindexed', 'up_to_date', 'no_directory', 'no_files', or 'error'
        - message: Human-readable status message
        - files_reindexed: List of filenames that were reindexed (if applicable)
        - details: Full indexing results (if reindexing occurred)

    Performance Benefits:
        - Avoids reprocessing unchanged files
        - Reduces database load and indexing time
        - Maintains data freshness without unnecessary overhead
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
        needs_reindex = False
        files_to_reindex = []

        for csv_file in csv_files:
            # Calculate current file content hash for comparison
            try:
                with open(csv_file, 'rb') as f:
                    content_hash = hashlib.md5(f.read()).hexdigest()
            except:
                continue  # Skip files that can't be read

            # Query database for existing index information
            result = await db.execute(text("""
                SELECT
                    MAX(updated_at) as last_indexed,
                    COUNT(*) as record_count
                FROM label_index
                WHERE file_name = :file_name
            """), {"file_name": csv_file.name})

            row = result.fetchone()
            last_indexed = row[0] if row else None  # When was this file last indexed?
            record_count = row[1] if row else 0     # How many records exist?

            # Retrieve stored content hash from previous indexing
            result = await db.execute(text("""
                SELECT metadata->>'content_hash' as stored_hash
                FROM label_index
                WHERE file_name = :file_name
                LIMIT 1
            """), {"file_name": csv_file.name})

            stored_hash_row = result.fetchone()
            stored_hash = stored_hash_row[0] if stored_hash_row else None

            # Multi-criteria reindexing decision
            file_mtime = int(os.path.getmtime(csv_file) * 1000)  # File modification time

            # Reindex if ANY of these conditions are true:
            if (not last_indexed or                              # Never indexed before
                record_count == 0 or                            # No records in database
                stored_hash != content_hash or                   # Content has changed
                file_mtime > (last_indexed + 60000)):           # File modified recently (1 min grace)

                needs_reindex = True
                # Determine the specific reason for logging/debugging
                reason = ('new' if not last_indexed else
                         'content_changed' if stored_hash != content_hash else
                         'modified')

                files_to_reindex.append({
                    'file': csv_file,
                    'reason': reason
                })
                logger.info(f"File {csv_file.name} needs reindexing - {reason}")

        # Step 5: Execute reindexing decision
        if needs_reindex:
            # Perform reindexing using enhanced function with hash storage
            logger.info(f"Auto-reindexing {len(files_to_reindex)} files...")
            result = await index_csv_labels_with_hash(db, labels_directory)
            return {
                "status": "reindexed",
                "message": f"Auto-reindexed {result.get('total_files', 0)} files",
                "files_reindexed": [f['file'].name for f in files_to_reindex],  # List of affected files
                "details": result  # Full indexing results
            }
        else:
            # No changes detected - system is up to date
            return {
                "status": "up_to_date",
                "message": "All label files are up to date"
            }

    except Exception as e:
        logger.error(f"Auto-reindex failed: {e}")
        return {"status": "error", "message": str(e)}


async def index_csv_labels_with_hash(db: AsyncSession, labels_directory: str = "/cmf-server/data/labels") -> Dict[str, Any]:
    """
    Enhanced version of index_csv_labels that stores content hashes for change detection.

    This is the preferred indexing function for production use as it enables:
    - Content hash storage for efficient change detection
    - Support for MD5 hash-based filenames
    - Enhanced JSONB data parsing for advanced search
    - Automatic type conversion (strings, numbers, booleans)
    - Comprehensive metadata storage

    Key Improvements over basic index_csv_labels:
    1. Stores MD5 content hash in metadata for change detection
    2. Parses CSV values into appropriate types for JSONB storage
    3. Better support for files without .csv extension
    4. Enhanced delimiter detection and CSV format handling

    Args:
        db: Database session for executing queries
        labels_directory: Path to directory containing CSV label files

    Returns:
        Dictionary containing indexing results:
        - status: 'success', 'warning', or 'error'
        - message: Human-readable status message
        - indexed_files: List of file indexing results with content hashes
        - total_files: Number of files processed
        - total_records: Total records indexed across all files

    Note:
        This function is used by auto_reindex_if_needed() for intelligent reindexing.
        The content hashes enable efficient change detection in future operations.
    """
    try:

        labels_dir = Path(labels_directory)
        if not labels_dir.exists():
            return {"status": "error", "message": f"Labels directory not found: {labels_directory}"}

        # Step 1: Comprehensive file discovery including hash-based names
        csv_files = list(labels_dir.glob("*.csv"))

        # Step 2: Auto-detect CSV files without extensions (including MD5 hash names)
        for file_path in labels_dir.iterdir():
            if file_path.is_file() and not file_path.suffix:
                # Check if filename is an MD5 hash (32 hex characters)
                is_md5_hash = bool(re.match(r'^[a-f0-9]{32}$', file_path.name))
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        first_line = f.readline().strip()
                        # Include if: MD5 hash OR contains CSV indicators
                        if is_md5_hash or ',' in first_line or any(keyword in first_line.lower() for keyword in ['file', 'name', 'id', 'type', 'size']):
                            csv_files.append(file_path)
                except:
                    # Skip files that can't be read (permissions, binary, etc.)
                    pass

        if not csv_files:
            return {"status": "warning", "message": "No CSV files found", "indexed_files": [], "total_files": 0}

        indexed_files = []
        total_records = 0

        # Step 3: Process each file with enhanced change detection
        for csv_file in csv_files:
            try:
                # Calculate MD5 hash for change detection (binary mode for accuracy)
                with open(csv_file, 'rb') as f:
                    content_hash = hashlib.md5(f.read()).hexdigest()

                # Clean slate: Remove existing records for this file
                await db.execute(
                    text("DELETE FROM label_index WHERE file_name = :file_name"),
                    {"file_name": csv_file.name}
                )

                # Step 4: Parse CSV with robust format detection
                records = []
                with open(csv_file, 'r', encoding='utf-8') as csvfile:
                    # Sample-based delimiter detection
                    sample = csvfile.read(1024)
                    csvfile.seek(0)  # Reset file pointer

                    # Intelligent delimiter detection with fallbacks
                    delimiter = ','  # Safe default
                    try:
                        # Use Python's built-in CSV sniffer
                        sniffer = csv.Sniffer()
                        detected_delimiter = sniffer.sniff(sample).delimiter
                        delimiter = detected_delimiter
                    except:
                        # Manual fallback: Test common delimiters by presence
                        for test_delimiter in [',', '\t', ';', '|']:
                            if test_delimiter in sample:
                                delimiter = test_delimiter
                                break

                    # Create reader with detected format
                    reader = csv.DictReader(csvfile, delimiter=delimiter)

                    # Step 5: Enhanced row processing with type conversion
                    for row_index, row in enumerate(reader):
                        # Initialize data structures for this row
                        content_parts = []
                        metadata = {'content_hash': content_hash}  # Store hash for change detection
                        parsed_data = {}  # Type-converted data for advanced search

                        # Process each column in the row
                        for key, value in row.items():
                            if value and value.strip():  # Skip empty values
                                # Build searchable text content
                                content_parts.append(f"{key}: {value.strip()}")
                                # Store raw string value in metadata
                                metadata[key] = value.strip()
                                # Convert to appropriate type for JSONB advanced search
                                parsed_data[key] = parse_csv_value(value.strip())

                        # Combine all fields into searchable text
                        content = " | ".join(content_parts)

                        # Only index rows with actual content
                        if content.strip():
                            records.append({
                                'file_name': csv_file.name,
                                'file_path': str(csv_file),
                                'row_index': row_index,
                                'content': content,                          # For full-text search
                                'metadata': json.dumps(metadata),           # Raw values + hash
                                'parsed_data': json.dumps(parsed_data),     # Type-converted for advanced search
                                'created_at': int(time.time() * 1000),      # Timestamp in milliseconds
                                'updated_at': int(time.time() * 1000)
                            })

                # Step 6: Bulk database insertion with enhanced schema
                if records:
                    # Use parameterized query for security and performance
                    insert_query = text("""
                        INSERT INTO label_index (file_name, file_path, row_index, content, metadata, parsed_data, created_at, updated_at)
                        VALUES (:file_name, :file_path, :row_index, :content, :metadata, :parsed_data, :created_at, :updated_at)
                    """)
                    # Bulk insert all records for this file
                    await db.execute(insert_query, records)

                    # Track successful indexing with content hash
                    indexed_files.append({
                        'file_name': csv_file.name,
                        'records_indexed': len(records),
                        'content_hash': content_hash,  # Store for change detection
                        'status': 'success'
                    })
                    total_records += len(records)
                    # Log with truncated hash for debugging
                    logger.info(f"Indexed {len(records)} records from {csv_file.name} (hash: {content_hash[:8]}...)")
                else:
                    # Handle empty files
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

        # Step 7: Commit all changes to database
        await db.commit()

        # Calculate success metrics for reporting
        success_count = sum(1 for f in indexed_files if f['status'] == 'success')
        return {
            'status': 'success',
            'message': f'Indexed {success_count}/{len(csv_files)} files successfully',
            'indexed_files': indexed_files,  # Detailed per-file results
            'total_files': len(csv_files),
            'total_records': total_records
        }

    except Exception as e:
        # Top-level error handling for database or system failures
        logger.error(f"Label indexing failed: {e}")
        return {"status": "error", "message": str(e)}


# LABEL SEARCH INITIALIZATION AND FILE LOADING
async def initialize_label_search():
    """
    Initialize label search functionality on server startup.

    This function sets up the label search system by:
    1. Checking for existing CSV files in the labels directory
    2. Verifying if label records are already indexed in the database
    3. Performing initial indexing if no records exist
    4. Logging system status and configuration

    Startup Behavior:
    - If CSV files exist but no database records: Performs full indexing
    - If database records exist: Assumes system is ready (no reindexing)
    - If no CSV files found: Logs warning but continues (files can be added later)

    This function is called during server startup via the lifespan context manager
    to ensure label search is ready when the API becomes available.

    Note:
        This function does not perform reindexing of existing data.
        For ongoing change detection, use auto_reindex_if_needed().
    """
    try:
        logger.info("Initializing label search functionality...")

        # Step 1: Scan for existing CSV files in the configured directory
        primary_dir = Path(LABELS_DIR)
        csv_files = []

        if primary_dir.exists():
            # Look for .csv files (most common case)
            csv_files = list(primary_dir.glob("*.csv"))

        if csv_files:
            logger.info(f"Found {len(csv_files)} CSV label files in primary directory: {primary_dir}")

            # Step 2: Check if database indexing is needed
            # Import here to avoid circular dependencies during startup
            from server.app.db.dbconfig import async_session
            async with async_session() as db:
                # Query current index status
                stats = await get_label_stats(db)

                if stats['total_records'] == 0:
                    # No existing index - perform initial indexing
                    logger.info("No existing index found. Performing initial indexing...")
                    result = await index_csv_labels(db)
                    logger.info(f"Initial indexing complete: {result.get('total_records', 0)} records from {result.get('total_files', 0)} files")
                else:
                    # Index exists - system is ready
                    logger.info(f"Label search ready: {stats['total_records']} records already indexed")
        else:
            # No CSV files found - log but don't error (files can be added later)
            logger.info(f"No CSV label files found in primary directory: {primary_dir}")
            logger.info("Label search will be available once CSV files are uploaded")

        # Step 3: Log configuration for debugging/monitoring
        logger.info(f"Labels directory configured: {LABELS_DIR}")
        logger.info("Label search initialization complete")

    except Exception as e:
        logger.warning(f"Label search initialization failed: {e}")
        logger.info("Label search will be available once configured properly")


async def load_label_csv_content(artifact: dict) -> str:
    """
    Load CSV content for a label artifact using multiple fallback strategies.

    This function implements a robust file location strategy to handle various
    artifact naming conventions and storage patterns:

    Search Strategies (in order):
    1. Direct path from artifact URI
    2. Filename from artifact name in labels directory
    3. Filename with .csv extension added
    4. URI basename in labels directory
    5. URI basename with .csv extension

    This multi-strategy approach handles cases where:
    - Artifacts reference absolute paths vs relative names
    - Files may or may not have .csv extensions
    - Artifact names may include path prefixes or suffixes
    - Files may be stored with hash-based names

    Args:
        artifact: Dictionary containing artifact information with 'name' and 'uri' keys
                 Expected format: {'name': 'filename', 'uri': '/path/to/file'}

    Returns:
        CSV content as string if file found and readable, None otherwise

    Note:
        This function is used by the label content display API to show
        actual CSV data when users click on label artifacts.
    """
    try:
        # Extract file information
        artifact_name = artifact.get('name', '')
        artifact_uri = artifact.get('uri', '')

        # Multi-strategy file location approach to handle various naming conventions
        potential_paths = []

        # Strategy 1: Direct path from URI (absolute or relative paths)
        # Handles cases where URI contains full file path
        if artifact_uri:
            potential_paths.append(Path(artifact_uri))

        # Strategy 2: Search in labels directory using artifact name
        # Handles cases where name is just the filename
        if artifact_name:
            labels_dir = Path(LABELS_DIR)
            potential_paths.extend([
                labels_dir / artifact_name,           # Exact name match
                labels_dir / f"{artifact_name}.csv"   # Add .csv extension
            ])

        # Strategy 3: Extract basename from URI and search in labels directory
        # Handles cases where URI has path but file is in labels directory
        if artifact_uri:
            uri_basename = Path(artifact_uri).name
            labels_dir = Path(LABELS_DIR)
            potential_paths.extend([
                labels_dir / uri_basename,            # URI basename as-is
                labels_dir / f"{uri_basename}.csv"    # URI basename with .csv
            ])

        # Try each potential path until we find a readable file
        for path in potential_paths:
            if path.exists() and path.is_file():
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if content.strip():  # Ensure file has actual content
                            logger.info(f"Successfully loaded label content from: {path}")
                            return content
                except Exception as e:
                    # Log but continue trying other paths
                    logger.warning(f"Failed to read file {path}: {e}")
                    continue

        # If no file found, log the attempt
        logger.warning(f"Could not find label file for artifact: name='{artifact_name}', uri='{artifact_uri}'")
        return None

    except Exception as e:
        logger.error(f"Error loading label CSV content: {e}")
        return None


async def load_label_csv_by_filename(file_name: str, pipeline_name: str = None) -> str:
    """
    Load CSV content by filename, with special handling for hash-based and regular filenames.

    This function provides flexible file loading that handles various filename formats:
    - Regular filenames (e.g., "labels.csv", "data.csv")
    - Hash-based filenames (e.g., "a1b2c3d4e5f6...") - 32 character MD5 hashes
    - Filenames with or without .csv extensions

    Loading Strategy:
    1. First attempts to use existing load_label_csv_content() logic
    2. Falls back to direct file system searches in labels directory
    3. Tries both with and without .csv extension
    4. Handles edge cases for hash-based artifact storage

    This function is particularly useful for:
    - API endpoints that receive filename parameters
    - Loading content for search result display
    - Handling artifacts stored with hash-based names
    - Supporting both legacy and modern filename conventions

    Args:
        file_name: The filename to load (hash, regular name, with/without extension)
        pipeline_name: Optional pipeline name (reserved for future pipeline-specific logic)

    Returns:
        CSV content as string if file found and readable, None otherwise

    Note:
        The pipeline_name parameter is currently unused but reserved for future
        enhancements that may require pipeline-specific file location logic.
    """
    try:
        # Note: pipeline_name parameter is reserved for future pipeline-specific logic
        # Currently unused but maintained for API compatibility and future enhancements

        # Strategy 1: Leverage existing multi-path loading logic
        # Create a mock artifact to reuse the robust path resolution
        mock_artifact = {
            'name': file_name,
            'uri': file_name
        }

        # Try the comprehensive loading logic first
        content = await load_label_csv_content(mock_artifact)
        if content:
            return content

        # Strategy 2: Direct file system fallback for edge cases
        # This handles scenarios not covered by the main loading logic
        labels_dir = LABELS_DIR
        if os.path.exists(labels_dir):
            # Direct filename match (handles hash-based names)
            direct_path = os.path.join(labels_dir, file_name)
            if os.path.exists(direct_path):
                try:
                    with open(direct_path, 'r', encoding='utf-8') as f:
                        return f.read()
                except Exception as e:
                    logger.warning(f"Failed to read direct path {direct_path}: {e}")

            # Try with .csv extension (handles missing extensions)
            csv_path = os.path.join(labels_dir, f"{file_name}.csv")
            if os.path.exists(csv_path):
                try:
                    with open(csv_path, 'r', encoding='utf-8') as f:
                        return f.read()
                except Exception as e:
                    logger.warning(f"Failed to read CSV path {csv_path}: {e}")

        logger.warning(f"Could not find label file: {file_name}")
        return None

    except Exception as e:
        logger.error(f"Error loading label CSV by filename: {e}")
        return None
