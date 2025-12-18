import socket
from urllib.parse import urlparse
import csv
import os
from typing import Tuple


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
            # name = rsplit_by_colon[0].split("/")[-1] + ":" +  split_by_colon[-1][:4]
            # Handle cases where user provides an artifact path like "artifacts/features/" in dvc.yaml.
            # If the path ends with a slash ("/"), get the second last part as the artifact name.
            # Combine the artifact name with a shortened lineage ID (e.g., ":2323") to form the final name.
            artifact_name = rsplit_by_colon[0].split("/")[-1] if rsplit_by_colon[0].split("/")[-1] != "" else rsplit_by_colon[0].split("/")[-2]
            name = artifact_name + ":" + split_by_colon[-1][:4]

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
 

def extract_hostname(server_url):
    try:
        parsed = urlparse(server_url)
        # If netloc is empty, try parsing as just a hostname
        if parsed.netloc:
            host = parsed.hostname
        else:
            # If user entered just 'localhost' or similar
            host = parsed.path.split(':')[0]
        return host
    except Exception:
        return server_url

def get_fqdn(name: str) -> str:
    try:
        fqdn = socket.getfqdn(name)
        if fqdn == name or "." not in fqdn:
            try:
                return socket.gethostbyaddr(name)[0]
            except Exception:
                return socket.gethostbyname(name)
        return fqdn
    except Exception:
        return "127.0.0.1"


def extract_csv_text_content(file_path: str, max_size_mb: int = 500) -> Tuple[str, bool]:
    """
    Extract searchable text content from a CSV file.
    
    Stores original CSV content without pre-tokenization. Tokenization for full-text
    search is handled by PostgreSQL's to_tsvector() on the content_tsvector column.
    This approach:
    - Keeps full_text_content readable and true to original data
    - Allows ILIKE substring matching on original text (e.g., "data.xml.gz", "4KB")
    - Enables future tsvector full-text search with PostgreSQL's built-in tokenization
    
    Args:
        file_path (str): Full path to the CSV file
        max_size_mb (int): Maximum file size in MB to process (default: 500 MB)
    
    Returns:
        Tuple[str, bool]: (extracted_text, is_truncated)
            - extracted_text: All CSV cell values concatenated with spaces, 
                              with special chars replaced for better tokenization
            - is_truncated: True if file was too large and content was truncated
    
    Raises:
        FileNotFoundError: If file doesn't exist
        Exception: For other CSV parsing errors
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    
    # Check file size
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    is_truncated = False
    
    if file_size_mb > max_size_mb:
        is_truncated = True
        print(f"Warning: CSV file {file_path} is {file_size_mb:.2f} MB (exceeds {max_size_mb} MB limit)")
    
    text_parts = []
    
    try:
        import re
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as csvfile:
            csv_reader = csv.reader(csvfile)
            
            rows_processed = 0
            max_rows = 100000 if file_size_mb > max_size_mb else None  # Limit rows for large files
            
            for row in csv_reader:
                # Convert all cells in the row to strings and join with spaces
                row_text = ' '.join(str(cell).strip() for cell in row if cell)
                if row_text:
                    # Store original text without manipulation
                    # PostgreSQL's to_tsvector() will handle tokenization for content_tsvector column
                    # This keeps full_text_content readable and allows ILIKE substring matching
                    text_parts.append(row_text)
                
                rows_processed += 1
                
                # Stop if we've hit the row limit for large files
                if max_rows and rows_processed >= max_rows:
                    is_truncated = True
                    print(f"Truncated after {max_rows} rows for large file: {file_path}")
                    break
        
        # Join all rows with newlines to preserve some structure
        full_text = '\n'.join(text_parts)
        
        # Additional safety: truncate if resulting text is too large (> 100 MB of text)
        max_text_size = 100 * 1024 * 1024  # 100 MB
        if len(full_text) > max_text_size:
            full_text = full_text[:max_text_size]
            is_truncated = True
            print(f"Truncated text content to {max_text_size} bytes for: {file_path}")
        
        return full_text, is_truncated
    
    except Exception as e:
        raise Exception(f"Error parsing CSV file {file_path}: {str(e)}")

