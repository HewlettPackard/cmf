import os
from cmflib import cmfquery
from collections import deque, defaultdict
import pandas as pd

async def query_tangled_lineage(mlmd_path,pipeline_name, dict_of_exe_id,uuid):
    query = cmfquery.CmfQuery(mlmd_path)
    pipeline_id = query.get_pipeline_id(pipeline_name)
    df=dict_of_exe_id[pipeline_name]
    result = df[df['Execution_uuid'].str[:4] == uuid.split('_')[1]]
    execution_id=result["id"].tolist()

    parents_set = set()
    queue = deque()  
    pd.set_option("display.max_columns", None)

    df = pd.DataFrame()

    parents = query.get_one_hop_parent_executions_with_df(execution_id,pipeline_id)
    dict_parents = {}
    dict_parents[execution_id[0]] = list(set(parents))
    parents_set.add(execution_id[0])
    for i in set(parents):
        queue.append(i)
        parents_set.add(i)
    while len(queue) > 0:
        exe_id = queue.popleft()
        parents = query.get_one_hop_parent_executions_with_df([exe_id],pipeline_id)
        dict_parents[exe_id] = list(set(parents))
        for i in set(parents):
            queue.append(i)
            parents_set.add(i)

    df = query.get_executions_with_execution_ids(list(parents_set))

    df['name_uuid'] = df['Execution_type_name'] + '_' + df['Execution_uuid']
    result_dict = df.set_index('id')['name_uuid'].to_dict()
 
    data_organized = topological_sort(dict_parents,result_dict)
    return data_organized

def topological_sort(input_data,execution_id_dict):
    # Initialize in-degree of all nodes to 0
    in_degree = {node: 0 for node in input_data}
    # Initialize adjacency list
    adj_list = defaultdict(list)

    # Fill the adjacency list and in-degree dictionary
    for node, dependencies in input_data.items():
        for dep in dependencies:
            adj_list[dep].append(node)
            in_degree[node] += 1

    # Queue for nodes with in-degree 0
    zero_in_degree_queue = deque([node for node, degree in in_degree.items() if degree == 0])
    topo_sorted_nodes = []

    while zero_in_degree_queue:
        current_node = zero_in_degree_queue.popleft()
        topo_sorted_nodes.append(current_node)
        for neighbor in adj_list[current_node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                zero_in_degree_queue.append(neighbor)
    # Transform sorted nodes into the required output format
    parent_dict = defaultdict(list)
    for id_val in topo_sorted_nodes:
        if id_val in input_data:
            parents = tuple(sorted(input_data[id_val]))
            parent_dict[parents].append({'id': modify_exec_name(execution_id_dict[id_val]),'parents': [modify_exec_name(execution_id_dict[parent]) for parent in input_data[id_val]]})
    output_data= list(parent_dict.values())
    return output_data

def modify_exec_name(exec_name_uuid):
    name=exec_name_uuid.split('_')[0].split('/')[-1]
    uuid=exec_name_uuid.split('_')[-1].split('-')[0][:4]
    return (name +"_"+uuid)
