import os
from cmflib import cmfquery
from collections import deque, defaultdict
import pandas as pd
import json

async def query_artifact_lineage_d3tree(mlmd_path,pipeline_name, dict_of_art_ids,lineagetype):
    query = cmfquery.CmfQuery(mlmd_path)
    pipeline_id = query.get_pipeline_id(pipeline_name)
    id_name = {}
    child_parent_artifact_id = {}
    for type_, df in dict_of_art_ids[pipeline_name].items():
        for index, row in df.iterrows():
            id_name[row["id"]] = modify_arti_name(row["name"])
            parent_artifacts = query.get_all_parent_artifacts(row["name"])
            child_parent_artifact_id[row["id"]] = []
            if not parent_artifacts.empty:
                child_parent_artifact_id[row["id"]] = list(parent_artifacts["id"])
    data_organized = topological_sort(child_parent_artifact_id, id_name)
    return data_organized

def topological_sort(input_data,artifact_name_id_dict):
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
    for id_val in topo_sorted_nodes:   # topo_sorted_nodes = ['1','2','3','4']
        if id_val in input_data:       # input_data = {"child_id":[parents_id]}, for example {"4":['3','7','9']}
            parents = tuple(sorted(input_data[id_val]))
            parent_dict[parents].append({'id': artifact_name_id_dict[id_val],'parents': [artifact_name_id_dict[parent] for parent in input_data[id_val]]})
    output_data= list(parent_dict.values()) 
    return output_data

def modify_arti_name(arti_name):
    if "metrics" in arti_name:
        name = f"{arti_name.split(':')[0]}:{arti_name.split(':')[1][:4]}:{arti_name.split(':')[2]}"
    else:
        name = arti_name.split("artifacts/")[1].rsplit(":", 1)[0] + ":" + arti_name.rsplit(":", 1)[1][:4]
    return name

#query_artifact_tree_lineage("/home/chobey/cmf-server/data/mlmd","Test-env",data,'Artifact_Tree')
