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

def _exec_sort_key(e):
    """Sort key for executions: prefer create_time_since_epoch, fall back to numeric id."""
    ts = e.get("create_time_since_epoch")
    if ts is not None:
        try:
            return (0, int(ts))
        except (TypeError, ValueError):
            pass
    try:
        return (1, int(e.get("id")))
    except (TypeError, ValueError):
        return (2, 0)

def convert_to_stage_json(input_json: dict, pipeline_name: str) -> dict:
    """
    Converts MLMD JSON for a clean hierarchy map.
    - Combines Execution Type name and a 4-digit truncated UUID.
    - Includes rich metadata fields for frontend hover/tooltip parsing.
    JSON structure is always: { "Pipeline": [ { "stages": [...] } ] }
    """

    try:
        stages_candidate = input_json["Pipeline"][0]["stages"]
        if not isinstance(stages_candidate, list):
            stages_candidate = []
    except (KeyError, IndexError, TypeError):
        stages_candidate = []

    # MLMD returns stages in reverse pipeline order (last-run stage first).
    # Reverse so columns render left-to-right: Prepare -> Featurize -> Train -> Evaluate.
    stages_candidate = list(reversed(stages_candidate))

    out = {
        "environment": pipeline_name,
        "metadata": { "version": "4.0.0", "description": "Executions Lineage Map" },
        "stages": []
    }

    stage_idx = 1
    exec_idx = 1

    for s_item in stages_candidate:
        stage_name = s_item["name"]

        stage_obj = {
            "stage_id": f"stage_{stage_idx:02d}",
            "stage_name": stage_name,
            "status": "completed",
            "executions": []
        }
        stage_idx += 1

        # Sort executions by actual creation time; fall back to numeric id.
        executions = sorted(s_item.get("executions", []), key=_exec_sort_key)

        for e in executions:
            full_uuid = str(e["properties"]["Execution_uuid"])
            exec_obj = {
                "execution_id": f"exec_{exec_idx:03d}",
                "execution_type": f"{stage_name}:{full_uuid[:4]}",
                "children": [],
                "tooltip": full_uuid,
                "title": full_uuid,
                "description": f"Full UUID: {full_uuid}",
                "full_uuid": full_uuid
            }
            exec_idx += 1
            stage_obj["executions"].append(exec_obj)

        out["stages"].append(stage_obj)

    return out