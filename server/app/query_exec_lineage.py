from cmflib import cmfquery
import pandas as pd
import itertools
from ml_metadata.proto.metadata_store_pb2 import Value

def query_exec_lineage(mlmd_path, pipeline_name,dict_of_exe_ids,exec_type,uuid_server):
    query = cmfquery.CmfQuery(mlmd_path)
    pipeline_id=query.get_pipeline_id(pipeline_name)
    node_id_name_list=[]
    link_src_trgt_list=[]
    for id,context_type,uuid in zip(dict_of_exe_ids[pipeline_name]["id"],dict_of_exe_ids[pipeline_name]["Context_Type"],dict_of_exe_ids[pipeline_name]["Execution_uuid"]):
        truncated_uuid=uuid.split("_")[0][:4]
        if (context_type+"_"+truncated_uuid) == (pipeline_name+"/"+exec_type+"_"+uuid_server):
            host_id=id
            node_id_name_list.append({"id":host_id,"name":(context_type+"_"+uuid.split("-")[0][:4]),"color":"#16B8E9"})
#    exec=query.get_one_hop_parent_executions([host_id],pipeline_id)
    exec_new=query.get_all_parent_executions_by_id([host_id],pipeline_id)
    for i in exec_new[0]:
        id=i[0]
        name=i[1]
        exec_uuid=i[2]
        node_id_name_list.append({"id":i[0],"name":(name+"_"+exec_uuid.split("-")[0][:4]),"color":"#FA6318"})
    link_src_trgt_list.append(exec_new[1])
    node_id_name_list_unique=[dict(t) for t in {tuple(d.items()) for d in node_id_name_list}]
    new_list = pd.DataFrame(
    link_src_trgt_list[0]
    ).drop_duplicates().to_dict('records')
    data = {
        "nodes" : node_id_name_list_unique,
        "links" : new_list
    }
    return data

#query_exec_lineage("/home/chobey/cmf-server/data/mlmd", "Test-env",data,"Evaluate")
    
