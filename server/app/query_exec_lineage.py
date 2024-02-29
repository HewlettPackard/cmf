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
    exec=query.get_one_hop_parent_executions([host_id],pipeline_id)
    query.get_all_parent_executions_by_id([host_id],pipeline_id)    
    for i in exec:
        for j in i:
            name=j.properties["Execution_type_name"].string_value
            exec_uuid=j.properties["Execution_uuid"].string_value
            link_src_trgt_list.append({"source":j.id,"target":host_id})
            node_id_name_list.append({"id":j.id,"name":(name+"_"+exec_uuid.split("-")[0][:4]),"color":"#FA6318"})

    new_list = pd.DataFrame(
    link_src_trgt_list
    ).drop_duplicates().to_dict('records')
    data = {
        "nodes" : node_id_name_list,
        "links" : new_list
    }
    return data

#query_exec_lineage("/home/chobey/cmf-server/data/mlmd", "Test-env",data,"Evaluate")
    
