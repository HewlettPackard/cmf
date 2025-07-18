from cmflib.cmfquery import CmfQuery
import pandas as pd
from typing import Dict

def query_execution_lineage_d3force(query: CmfQuery, pipeline_name, dict_of_exe_ids, uuid_server) -> Dict:
    """
    Creates data of executions for forced_directed_graph.
    Parameters:
        pipeline_name: Name of pipeline.
        dict_of_exe_ids: Dict of execution data, [id,Context_Type,Execution_uuid, Context_ID].
        uuid_server: first four characters of uuid, example: fb0e.
    Returns:
        Returns dictionary of nodes and links.
        {
        "nodes" : node_id_name_list,
        "links" : [{1:2},{2:3}]
         }
    """
    data: Dict[str, list] = {}
    df=dict_of_exe_ids[pipeline_name]
    #finding Context_Type by comparing Execution_uuid (d09fdb26-0e9d-11ef-944f-4bf54f5aca7f) and uuid_server ('u3tr')  
    result = df[df['Execution_uuid'].str[:4] == uuid_server]  ##result = df[id: "1","Execution_type_name", "Execution_uuid"]
    exec_type = result["Context_Type"] 

    pipeline_id = query.get_pipeline_id(pipeline_name)
    node_id_name_list = []
    link_src_trgt_list = []
    host_id = None
    for id, context_type, uuid in zip(dict_of_exe_ids[pipeline_name]["id"], dict_of_exe_ids[pipeline_name]["Context_Type"], dict_of_exe_ids[pipeline_name]["Execution_uuid"]):
        truncated_uuid = uuid.split("_")[0][:4]    # first 4 characters of uuid example fb0e
        # comparing exec_type fetched from server with the one in dict_of_exe_ids and getting host_id of exec_type
        if (context_type + "_" + truncated_uuid) == (exec_type.to_list()[0] + "_" + uuid_server):
            host_id = id
            node_id_name_list.append({"id":host_id, "name":(context_type.split("/")[-1] + "_" + uuid.split("-")[0][:4]), "color":"#16B8E9"})
    #exec=query.get_one_hop_parent_executions([host_id],pipeline_id)
    exec_new = None
    if host_id is None:  #if host_id is None then return {}
        return data
    exec_new = query.get_all_parent_executions_by_id([host_id], pipeline_id) 
    if exec_new is None:  # if execution has no parent executions return {}
        return data
    for i in exec_new[0]: # appending id, name, exec_uuid to node_id_name_list
        id = i[0]
        name = i[1]
        exec_uuid = i[2]
        node_id_name_list.append({"id":i[0], "name":(name.split("/")[-1] + "_" + exec_uuid.split("-")[0][:4]), "color":"#FA6318"})
    link_src_trgt_list.append(exec_new[1])
    if not node_id_name_list and not link_src_trgt_list:
        return data
    node_id_name_list_unique = [dict(t) for t in {tuple(d.items()) for d in node_id_name_list}]
    new_list = pd.DataFrame(
      link_src_trgt_list[0]
    ).drop_duplicates().to_dict('records')
    data = {
        "nodes" : node_id_name_list_unique,
        "links" : new_list
    }
    return data

#query_exec_lineage("/home/chobey/cmf-server/data/mlmd", "Test-env",data,"Evaluate")
