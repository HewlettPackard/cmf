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
    """Represents a single search condition"""
    def __init__(self, column: str, operator: ComparisonOperator, value: Union[str, int, float]):
        self.column = column.strip()
        self.operator = operator
        self.value = value
        
    def __repr__(self):
        return f"SearchCondition({self.column} {self.operator.value} {self.value})"

class AdvancedSearchParser:
    """Parser for advanced search queries with comparison operators"""
    
    # Regex pattern to match search conditions
    # Supports: column>value, column<=value, column="quoted value", etc.
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
        
        # Find all structured conditions
        matches = cls.CONDITION_PATTERN.findall(query)
        matched_positions = []
        
        for match in cls.CONDITION_PATTERN.finditer(query):
            matched_positions.append((match.start(), match.end()))
            
        for match in matches:
            column, operator_str, _, quoted_value1, quoted_value2, unquoted_value = match
            
            # Get the actual value (quoted or unquoted)
            value = quoted_value1 or quoted_value2 or unquoted_value
            
            try:
                # Parse operator
                operator = ComparisonOperator(operator_str)
                
                # Convert value to appropriate type
                parsed_value = cls._parse_value(value, operator)
                
                conditions.append(SearchCondition(column, operator, parsed_value))
                
            except ValueError as e:
                errors.append(f"Invalid condition '{column}{operator_str}{value}': {str(e)}")
                
        # Extract remaining text as plain search terms
        remaining_text = query
        for start, end in reversed(matched_positions):
            remaining_text = remaining_text[:start] + remaining_text[end:]
            
        plain_terms = [term.strip() for term in remaining_text.split() if term.strip()]
        
        return conditions, plain_terms, errors
    
    @classmethod
    def _parse_value(cls, value: str, operator: ComparisonOperator) -> Union[str, int, float]:
        """Parse value string to appropriate type based on operator"""
        if operator in [ComparisonOperator.CONTAINS, ComparisonOperator.NOT_CONTAINS]:
            return value  # Keep as string for text operations
            
        if operator in [ComparisonOperator.EQUAL, ComparisonOperator.NOT_EQUAL]:
            # Try to parse as number, fall back to string
            try:
                if '.' in value:
                    return float(value)
                else:
                    return int(value)
            except ValueError:
                return value
                
        # For numeric comparisons, try to parse as number
        if operator in [ComparisonOperator.GREATER_THAN, ComparisonOperator.LESS_THAN,
                       ComparisonOperator.GREATER_EQUAL, ComparisonOperator.LESS_EQUAL]:
            try:
                if '.' in value:
                    return float(value)
                else:
                    return int(value)
            except ValueError:
                raise ValueError(f"Numeric value expected for operator {operator.value}, got '{value}'")
                
        return value


class JsonbQueryBuilder:
    """Build PostgreSQL JSONB queries from SearchCondition objects"""

    @classmethod
    def _get_case_insensitive_column_value(cls, column_key: str) -> str:
        """
        Generate SQL to get column value with case-insensitive matching and whitespace handling.
        This handles cases where user searches for 'lines' but CSV has 'Lines', ' Lines', etc.
        """
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
        if not conditions:
            return "", {}

        where_parts = []
        params = {}

        for i, condition in enumerate(conditions):
            clause, condition_params = cls._build_condition_clause(condition, i)
            if clause:
                where_parts.append(clause)
                params.update(condition_params)

        if not where_parts:
            return "", {}

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
        column_key = f"col_{index}"
        value_key = f"val_{index}"

        # Use case-insensitive column value extraction
        column_value_sql = cls._get_case_insensitive_column_value(column_key)

        if condition.operator == ComparisonOperator.CONTAINS:
            # For contains, use ILIKE on the text value
            clause = f"({column_value_sql}) ILIKE :{value_key}"
            params = {
                column_key: condition.column,
                value_key: f"%{condition.value}%"
            }

        elif condition.operator == ComparisonOperator.NOT_CONTAINS:
            # For not contains, use NOT ILIKE on the text value
            clause = f"({column_value_sql}) NOT ILIKE :{value_key}"
            params = {
                column_key: condition.column,
                value_key: f"%{condition.value}%"
            }

        elif condition.operator == ComparisonOperator.EQUAL:
            if isinstance(condition.value, (int, float)):
                # Numeric comparison - cast to numeric
                clause = f"({column_value_sql})::numeric = :{value_key}"
            else:
                # Text comparison - case insensitive
                clause = f"LOWER({column_value_sql}) = LOWER(:{value_key})"
            params = {
                column_key: condition.column,
                value_key: condition.value
            }

        elif condition.operator == ComparisonOperator.NOT_EQUAL:
            if isinstance(condition.value, (int, float)):
                # Numeric comparison - cast to numeric
                clause = f"({column_value_sql})::numeric != :{value_key}"
            else:
                # Text comparison - case insensitive
                clause = f"LOWER({column_value_sql}) != LOWER(:{value_key})"
            params = {
                column_key: condition.column,
                value_key: condition.value
            }

        elif condition.operator == ComparisonOperator.GREATER_THAN:
            # Numeric comparison - cast to numeric
            clause = f"({column_value_sql})::numeric > :{value_key}"
            params = {
                column_key: condition.column,
                value_key: condition.value
            }

        elif condition.operator == ComparisonOperator.LESS_THAN:
            # Numeric comparison - cast to numeric
            clause = f"({column_value_sql})::numeric < :{value_key}"
            params = {
                column_key: condition.column,
                value_key: condition.value
            }

        elif condition.operator == ComparisonOperator.GREATER_EQUAL:
            # Numeric comparison - cast to numeric
            clause = f"({column_value_sql})::numeric >= :{value_key}"
            params = {
                column_key: condition.column,
                value_key: condition.value
            }

        elif condition.operator == ComparisonOperator.LESS_EQUAL:
            # Numeric comparison - cast to numeric
            clause = f"({column_value_sql})::numeric <= :{value_key}"
            params = {
                column_key: condition.column,
                value_key: condition.value
            }

        else:
            return "", {}

        return clause, params


# CSV PARSING AND VALUE CONVERSION
def parse_csv_value(value: str):
    """
    Parse a CSV value and convert it to the appropriate Python type for JSONB storage.

    Args:
        value: String value from CSV

    Returns:
        Parsed value (int, float, bool, or string)
    """
    if not value or not value.strip():
        return None

    value = value.strip()

    # Try boolean first (case-insensitive)
    if value.lower() in ('true', 'false', 'yes', 'no', '1', '0'):
        if value.lower() in ('true', 'yes', '1'):
            return True
        elif value.lower() in ('false', 'no', '0'):
            return False

    # Try integer
    try:
        # Check if it looks like an integer (no decimal point)
        if '.' not in value and 'e' not in value.lower():
            return int(value)
    except ValueError:
        pass

    # Try float
    try:
        return float(value)
    except ValueError:
        pass

    # Return as string
    return value


# DATABASE OPERATIONS FOR LABEL INDEXING
async def index_csv_labels(db: AsyncSession, labels_directory: str = "/cmf-server/data/labels") -> Dict[str, Any]:
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

        indexed_files = []
        total_records = 0

        for csv_file in csv_files:
            try:
                # Clear existing data for this file
                await db.execute(
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
                    await db.execute(insert_query, records)

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
    Get statistics about indexed labels
    """
    try:
        # Get total records and files
        result = await db.execute(text("""
            SELECT
                COUNT(*) as total_records,
                COUNT(DISTINCT file_name) as total_files
            FROM label_index
        """))
        stats = result.fetchone()

        # Get recent files
        result = await db.execute(text("""
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


async def auto_reindex_if_needed(db: AsyncSession, labels_directory: str = "/cmf-server/data/labels") -> Dict[str, Any]:
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
        needs_reindex = False
        files_to_reindex = []

        for csv_file in csv_files:
            # Calculate content hash for change detection
            try:
                with open(csv_file, 'rb') as f:
                    content_hash = hashlib.md5(f.read()).hexdigest()
            except:
                continue

            # Check if file exists in index and get its content hash
            result = await db.execute(text("""
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
            result = await db.execute(text("""
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

        if needs_reindex:
            logger.info(f"Auto-reindexing {len(files_to_reindex)} files...")
            result = await index_csv_labels_with_hash(db, labels_directory)
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


async def index_csv_labels_with_hash(db: AsyncSession, labels_directory: str = "/cmf-server/data/labels") -> Dict[str, Any]:
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

        indexed_files = []
        total_records = 0

        for csv_file in csv_files:
            try:
                # Calculate content hash
                with open(csv_file, 'rb') as f:
                    content_hash = hashlib.md5(f.read()).hexdigest()

                # Clear existing data for this file
                await db.execute(
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
                        # Create searchable content and parsed data
                        content_parts = []
                        metadata = {'content_hash': content_hash}
                        parsed_data = {}

                        for key, value in row.items():
                            if value and value.strip():
                                content_parts.append(f"{key}: {value.strip()}")
                                metadata[key] = value.strip()
                                # Parse value for JSONB storage
                                parsed_data[key] = parse_csv_value(value.strip())

                        content = " | ".join(content_parts)

                        if content.strip():
                            records.append({
                                'file_name': csv_file.name,
                                'file_path': str(csv_file),
                                'row_index': row_index,
                                'content': content,
                                'metadata': json.dumps(metadata),
                                'parsed_data': json.dumps(parsed_data),
                                'created_at': int(time.time() * 1000),
                                'updated_at': int(time.time() * 1000)
                            })

                # Insert records
                if records:
                    insert_query = text("""
                        INSERT INTO label_index (file_name, file_path, row_index, content, metadata, parsed_data, created_at, updated_at)
                        VALUES (:file_name, :file_path, :row_index, :content, :metadata, :parsed_data, :created_at, :updated_at)
                    """)
                    await db.execute(insert_query, records)

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


# LABEL SEARCH INITIALIZATION AND FILE LOADING
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
            from server.app.db.dbconfig import async_session
            async with async_session() as db:
                stats = await get_label_stats(db)
                if stats['total_records'] == 0:
                    logger.info("Indexing label files...")
                    result = await index_csv_labels(db)
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


async def load_label_csv_content(artifact: dict) -> str:
    """
    Load CSV content for a label artifact.

    Args:
        artifact: Dictionary containing artifact information with 'name' and 'uri' keys

    Returns:
        CSV content as string, or None if not found
    """
    try:
        # Extract file information
        artifact_name = artifact.get('name', '')
        artifact_uri = artifact.get('uri', '')

        # Try different strategies to locate the file
        potential_paths = []

        # Strategy 1: Direct path from URI
        if artifact_uri:
            potential_paths.append(Path(artifact_uri))

        # Strategy 2: Look in labels directory using name
        if artifact_name:
            labels_dir = Path(LABELS_DIR)
            potential_paths.extend([
                labels_dir / artifact_name,
                labels_dir / f"{artifact_name}.csv"
            ])

        # Strategy 3: Look in labels directory using URI basename
        if artifact_uri:
            uri_basename = Path(artifact_uri).name
            labels_dir = Path(LABELS_DIR)
            potential_paths.extend([
                labels_dir / uri_basename,
                labels_dir / f"{uri_basename}.csv"
            ])

        # Try each potential path
        for path in potential_paths:
            if path.exists() and path.is_file():
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if content.strip():  # Only return non-empty content
                            logger.info(f"Successfully loaded label content from: {path}")
                            return content
                except Exception as e:
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

        logger.warning(f"Could not find label file: {file_name}")
        return None

    except Exception as e:
        logger.error(f"Error loading label CSV by filename: {e}")
        return None
