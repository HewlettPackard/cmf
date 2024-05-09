from cmflib import cmfquery
import pandas as pd
import itertools
from ml_metadata.proto.metadata_store_pb2 import Value

def query_Tree_lineage(mlmd_path, pipeline_name, dict_of_exe_ids, exec_type, uuid_server):
    data = {}
    query = cmfquery.CmfQuery(mlmd_path)
    pipeline_id = query.get_pipeline_id(pipeline_name)
    node_id_name_list = []
    link_src_trgt_list = []
    host_id = None
    for id, context_type, uuid in zip(dict_of_exe_ids[pipeline_name]["id"], dict_of_exe_ids[pipeline_name]["Context_Type"], dict_of_exe_ids[pipeline_name]["Execution_uuid"]):
        truncated_uuid = uuid.split("_")[0][:4]
        # this condition is failing that's why we are unable to assign id to host_id
        if (context_type + "_" + truncated_uuid) == (pipeline_name + "/" + exec_type + "_" + uuid_server):
#            print(id,"id")
            host_id = id
            host_name = context_type + "_" + uuid.split("-")[0][:4]
            node_id_name_list.append({"id":host_id, "name":(context_type + "_" + uuid.split("-")[0][:4]), "color":"#16B8E9"})
    #exec=query.get_one_hop_parent_executions([host_id],pipeline_id)
    exec_new = None
    if host_id is None:
        return data
    exec_new = query.get_all_parent_executions_by_id([host_id], pipeline_id)
    tree_data = query.get_all_tree_data_by_id([host_id],host_name, pipeline_id)
#    print(exec_new)
    print(tree_data,"tree_data")

    return tree_data
'''
data = {
    'Test-env': {
        'id': [1, 2, 3, 4],
        'Context_Type': ['Test-env/Prepare', 'Test-env/Featurize', 'Test-env/Train', 'Test-env/Evaluate'],
        'Execution_uuid': ['415c9486-0227-11ef-944f-4bf54f5aca7f', '4a035d2c-0227-11ef-944f-4bf54f5aca7f', '61f71e96-0227-11ef-944f-4bf54f5aca7f', '6ae25868-0227-11ef-944f-4bf54f5aca7f'],
        'Context_ID': [2, 3, 4, 5]
    }
}

query_exec_lineage("/home/chobey/cmf-server/data/mlmd", "Test-env",data,"Evaluate","6ae2")
'''
