from cmflib import merger

def merge_mlmd(json_payload):
    cmd='push'
    merger.parse_json_to_mlmd(json_payload,'data/mlmd',cmd)

