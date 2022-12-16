from cmflib import merger

def merge_mlmd(json_payload,exec_id):
    cmd='push'

    if exec_id == None:                                                 #if execution id not available
        merger.parse_json_to_mlmd(json_payload,'data/mlmd',cmd)         #parsing mlmd Json data to mlmd file
    else:
        merger.push_execution_to_mlmd(json_payload,'data/mlmd',cmd,exec_id) #parsing mlmd Json data for given execution id to mlmd file

