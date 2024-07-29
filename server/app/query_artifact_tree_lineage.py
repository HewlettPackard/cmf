import os
from cmflib import cmfquery
from collections import deque, defaultdict
import pandas as pd
import json
from typing import List, Dict, Any

async def query_artifact_tree_lineage(mlmd_path: str,pipeline_name: str, dict_of_art_ids: Dict) -> List[List[Dict[str, Any]]]:
    query = cmfquery.CmfQuery(mlmd_path)
    pipeline_id = query.get_pipeline_id(pipeline_name)
    id_name = {}
    child_parent_artifact_id = {}
    for type_, df in dict_of_art_ids[pipeline_name].items():
        for index, row in df.iterrows():
            #creating a dictionary of id and artifact name {id:artifact name}          
            id_name[row["id"]] = modify_arti_name(row["name"])   
            one_hop_parent_artifacts = query.get_one_hop_parent_artifacts(row["name"])  # get immediate artifacts     
            child_parent_artifact_id[row["id"]] = []      # empty dict for artifact with no parent artifact
            if not one_hop_parent_artifacts.empty:        # if artifact have parent artifacts             
                child_parent_artifact_id[row["id"]] = list(one_hop_parent_artifacts["id"])
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
    if "metrics" in arti_name:   # for metrics metrics:4ebdc980-1e7c-11ef-b54c-25834a9c665c:388 -> metrics:4ebd:388
        name = f"{arti_name.split(':')[0]}:{arti_name.split(':')[1][:4]}:{arti_name.split(':')[2]}"
    elif arti_name.startswith("artifacts")  :
        name = arti_name.split("artifacts/")[1].rsplit(":", 1)[0] + ":" + arti_name.rsplit(":", 1)[1][:4]  # artifacts/parsed/train.tsv:32b715ef0d71ff4c9e61f55b09c15e75 -> parsed/train.tsv
    else:
        name = arti_name
    return name

