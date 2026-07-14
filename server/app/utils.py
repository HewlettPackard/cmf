import socket
from urllib.parse import urlparse


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

import json

def convert_to_stage_json(input_json: dict, pipeline_name: str) -> dict:
    """
    Converts MLMD JSON for a clean hierarchy map.
    - Removes trailing child nodes underneath executions.
    - Combines Execution Type name and a 6-digit truncated UUID.
    - Includes rich metadata fields for frontend hover/tooltip parsing.
    """
    
    def extract_stages_recursively(data):
        """Recursively parses and drills down to locate the raw stages list."""
        if isinstance(data, str):
            cleaned = data.strip()
            try:
                return extract_stages_recursively(json.loads(cleaned))
            except Exception:
                if "stages" in cleaned or "Pipeline" in cleaned:
                    try:
                        if not (cleaned.startswith('{') and cleaned.endswith('}')):
                            return extract_stages_recursively(json.loads("{" + cleaned + "}"))
                    except Exception:
                        pass
                return None

        if isinstance(data, dict):
            for key in ("stages", "stage_list", "stageList"):
                if key in data and isinstance(data[key], list):
                    return data[key]
            for key in ("Pipeline", "pipelines", "name"):
                if key in data:
                    res = extract_stages_recursively(data[key])
                    if res: return res
            for v in data.values():
                if isinstance(v, (dict, list, str)):
                    res = extract_stages_recursively(v)
                    if res: return res

        if isinstance(data, list):
            for item in data:
                res = extract_stages_recursively(item)
                if res: return res
                
        return None

    stages_candidate = extract_stages_recursively(input_json)
    if not stages_candidate:
        stages_candidate = []

    out = {
        "environment": pipeline_name,
        "metadata": { "version": "4.0.0", "description": "Executions Lineage Map" },
        "stages": []
    }

    stage_idx = 1
    exec_idx = 1

    for s_item in stages_candidate:
        if not isinstance(s_item, dict):
            continue

        raw_executions = s_item.get("executions") or []
        if isinstance(raw_executions, str):
            try: raw_executions = json.loads(raw_executions)
            except Exception: raw_executions = []

        if not raw_executions:
            continue

        # Extract context attributes from the execution definition
        first_exec = raw_executions[0] if isinstance(raw_executions, list) and len(raw_executions) > 0 else {}
        props = first_exec.get("properties") or {} if isinstance(first_exec, dict) else {}
        
        context_type = props.get("Context_Type") or props.get("Execution_type_name") or first_exec.get("type") or ""
        if "/" in context_type:
            stage_name = context_type.split("/", 1)[1]
        elif context_type:
            stage_name = context_type
        else:
            stage_name = f"stage_{stage_idx}"

        stage_obj = {
            "stage_id": f"stage_{stage_idx:02d}",
            "stage_name": stage_name,
            "status": "completed",
            "executions": []
        }
        stage_idx += 1

        for e in raw_executions:
            if not isinstance(e, dict):
                continue

            e_props = e.get("properties") or {}
            
            # 1. Fetch execution base name (e.g., "Prepare")
            exec_base_name = e.get("type") or "Execution"
            
            # 2. Use Execution_uuid first — same field the tangled-tree lineage keys off of,
            #    so the same execution shows the same short UUID in both views.
            full_uuid = str(e_props.get("Execution_uuid") or e_props.get("Git_End_Commit") or e_props.get("Git_Start_Commit") or e.get("id") or "")
            truncated_uuid = full_uuid[:4] if full_uuid else f"ex_{exec_idx}"

            # 3. Create the multi-line UI text block
            # Note: '\n' handles line breaks in graph frameworks configured with CSS white-space: pre-wrap
            display_text = f"{exec_base_name}\n{truncated_uuid}"

            exec_obj = {
                "execution_id": f"exec_{exec_idx:03d}",
                "execution_type": display_text, 
                "children": [],  # Empty array ensures no leaf artifact nodes render underneath
                
                # Broad compatibility fields for the UI graphing framework's hover tooltip engine
                "tooltip": full_uuid,
                "title": full_uuid,
                "description": f"Full UUID: {full_uuid}",
                "full_uuid": full_uuid
            }
            exec_idx += 1

            stage_obj["executions"].append(exec_obj)
        
        out["stages"].append(stage_obj)

    return out
