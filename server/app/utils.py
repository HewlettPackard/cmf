# Standard library imports
import asyncio
import csv
import json
import time
import os
import hashlib
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Third-party imports
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Set up logger
logger = logging.getLogger(__name__)


def modify_arti_name(arti_name, type):
    # artifact_name optimization based on artifact type.["Dataset","Model","Metrics"]
    try:
        name = ""

        if type == "Metrics" or type == "Model" or type == "Dataset":
            # Metrics   metrics:7bea36fc-8b99-11ef-abea-ddaa7ef0aa99:13  -----------> ['metrics', '7bea36fc-8b99-11ef-abea-ddaa7ef0aa99', '13']
            # Dataset   artifacts/data.xml.gz:236d9502e0283d91f689d7038b8508a2  -----------> ['artifacts/data.xml.gz', '236d9502e0283d91f689d7038b8508a2']
            # Model   artifacts/model/model.pkl:4c48f23acd14d20ebba0352f4b5f55e8:9  ------> ['artifacts/model/model.pkl', '4c48f23acd14d20ebba0352f4b5f55e8', '9']
            split_by_colon = arti_name.split(':')

        if type == "Dataslice" or type == "Step_Metrics":
            # Step_Metrics   cmf_artifacts/5a2f6686-8b99-11ef-abea-ddaa7ef0aa99/metrics/training_metrics:46fd4d02f72dee5fc88b0cf9aa908ed5:15:744ad0be-8b99-11ef-abea-ddaa7ef0aa99 
            # ---> 5a2f6686-8b99-11ef-abea-ddaa7ef0aa99/metrics/training_metrics:46fd4d02f72dee5fc88b0cf9aa908ed5:15:744ad0be-8b99-11ef-abea-ddaa7ef0aa99
            # Dataslice   cmf_artifacts/c1e542fc-8ba1-11ef-abea-ddaa7ef0aa99/dataslice/slice-1:059136b3b35fc4b58cf13f73e4564b9b
            # ----> "c1e542fc-8ba1-11ef-abea-ddaa7ef0aa99/dataslice/slice-1:059136b3b35fc4b58cf13f73e4564b9b"
            split_by_slash = arti_name.split('/', 1)[1] #remove cmf_artifacts/

        if type ==  "Dataset" or type == "Step_Metrics":
            # Dataset   artifacts/data.xml.gz:236d9502e0283d91f689d7038b8508a2  -----------> ["artifacts/data.xml.gz","236d9502e0283d91f689d7038b8508a2"]
            # Step_Metrics   cmf_artifacts/5a2f6686-8b99-11ef-abea-ddaa7ef0aa99/metrics/training_metrics:46fd4d02f72dee5fc88b0cf9aa908ed5:15:744ad0be-8b99-11ef-abea-ddaa7ef0aa99 
            # ----> ["cmf_artifacts/5a2f6686-8b99-11ef-abea-ddaa7ef0aa99/metrics/training_metrics", "46fd4d02f72dee5fc88b0cf9aa908ed5", "15" "744ad0be-8b99-11ef-abea-ddaa7ef0aa99"]
            rsplit_by_colon = arti_name.rsplit(':')
       
        if type == "Metrics" :   
            # split_by_colon = ["metrics","7bea36fc-8b99-11ef-abea-ddaa7ef0aa99","13"] ----> "metrics:7bea:13"
            # name = "metrics:7bea:13"
            name = f"{split_by_colon[0]}:{split_by_colon[1][:4]}:{split_by_colon[2]}"

        elif type == "Model":
            # split_by_colon = ["artifacts/model/model.pkl", "4c48f23acd14d20ebba0352f4b5f55e8", "9"]
            # split_by_colon[-3].split("/")[-1] --> "model.pkl"
            # split_by_colon[-2][:4] --> "4c48"
            # name = "model.pkl:4c48"
            name = split_by_colon[-3].split("/")[-1] + ":" + split_by_colon[-2][:4]

        elif type == "Dataset":
            # Example artifacts/data.xml.gz:236d9502e0283d91f689d7038b8508a2 -> "data.xml.gz:236d"
            # rsplit_by_colon --> ["artifacts/data.xml.gz","236d9502e0283d91f689d7038b8508a2"] 
            # rsplit_by_colon[0].split("/")[-1] ---> artifacts/data.xml.gz ---> "data.xml.gz"
            # split_by_colon[-1][:4] ---> ["artifacts/data.xml.gz","236d9502e0283d91f689d7038b8508a2"]  ---> "236d"
            # name = "data.xml.gz:236d"
            name = rsplit_by_colon[0].split("/")[-1] + ":" +  split_by_colon[-1][:4]

        elif type == "Dataslice":
            # split_by_slash = "c1e542fc-8ba1-11ef-abea-ddaa7ef0aa99/dataslice/slice-1:059136b3b35fc4b58cf13f73e4564b9b"
            # data = ["c1e542fc-8ba1-11ef-abea-ddaa7ef0aa99/dataslice/slice-1", "059136b3b35fc4b58cf13f73e4564b9b"]
            # name = "c1e542fc-8ba1-11ef-abea-ddaa7ef0aa99/dataslice/slice-1:0591"
            data = split_by_slash.rsplit(":",-1)
            name = data[0] + ":" + data[-1][:4]

        elif type == "Step_Metrics":
            # split_by_slash = 5a2f6686-8b99-11ef-abea-ddaa7ef0aa99/metrics/training_metrics:46fd4d02f72dee5fc88b0cf9aa908ed5:15:744ad0be-8b99-11ef-abea-ddaa7ef0aa99 
            # split_by_slash.rsplit(":",-3)[0] = "5a2f6686-8b99-11ef-abea-ddaa7ef0aa99/metrics/training_metrics"
            # rsplit_by_colon = ["cmf_artifacts/5a2f6686-8b99-11ef-abea-ddaa7ef0aa99/metrics/training_metrics", "46fd4d02f72dee5fc88b0cf9aa908ed5", "15", "744ad0be-8b99-11ef-abea-ddaa7ef0aa99"]
            # rsplit_by_colon[-3][:4] = "46fd"
            # rsplit_by_colon[-2] = "15"
            # rsplit_by_colon[-1][:4] = "744a"
            # name = "5a2f6686-8b99-11ef-abea-ddaa7ef0aa99/metrics/training_metrics:46fd:15:744a"
            name = split_by_slash.rsplit(":",-3)[0] + ":" + rsplit_by_colon[-3][:4] + ":" + rsplit_by_colon[-2] + ":" + rsplit_by_colon[-1][:4]
        else:
            name = arti_name  
    except Exception as e:
        print(f"Error parsing artifact name: {e}")
        name = arti_name  # Fallback to the original arti_name in case of error
    return name


# Label Search Utility Functions

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

async def search_labels(database_url: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search indexed labels using PostgreSQL full-text search
    """
    try:

        engine = create_async_engine(database_url, echo=False)

        async with engine.begin() as conn:
            result = await conn.execute(text("""
                SELECT file_name, row_index, content, metadata,
                       ts_rank(search_vector, plainto_tsquery('english', :query)) as relevance_score
                FROM label_index
                WHERE search_vector @@ plainto_tsquery('english', :query)
                ORDER BY relevance_score DESC
                LIMIT :limit
            """), {"query": query, "limit": limit})

            results = [
                {
                    "file_name": row[0],
                    "row_index": row[1],
                    "content": row[2],
                    "metadata": json.loads(row[3]) if row[3] else {},
                    "relevance_score": float(row[4])
                }
                for row in result.fetchall()
            ]

        await engine.dispose()
        return results

    except Exception as e:
        logger.error(f"Label search failed: {e}")
        return []

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
 