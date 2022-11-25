from cmflib import merger

def merge_mlmd(json_payload,exec_id):
    cmd='push'

    if exec_id == None:
        merger.parse_json_to_mlmd(json_payload,'data/mlmd',cmd)
    else:
        merger.push_execution_to_mlmd(json_payload,'data/mlmd',cmd,exec_id)

