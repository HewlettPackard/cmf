from cmflib.cmfquery import CmfQuery
from collections import deque, defaultdict
from typing import List, Dict, Any
from server.app.utils import modify_arti_name
import pandas as pd

def query_artifact_lineage_d3tree(query: CmfQuery, pipeline_name: str, dict_of_art_ids: Dict) -> List[List[Dict[str, Any]]]:
    id_name = {}
    child_parent_artifact_id: Dict[int, List[int]] = {}
    skip_ids = set() # Skip environment and label artifacts

    # Get all artifact IDs that belong to the current pipeline
    current_pipeline_artifact_ids = set(pd.concat(dict_of_art_ids[pipeline_name].values())["id"])

    for type_, df in dict_of_art_ids[pipeline_name].items():
        # Collect environment and label artifact IDs for skipping
        if type_ == "Environment" or type_ == "Label":
            skip_ids.update(df["id"])
            continue  # No need to process them further

        for index, row in df.iterrows():
            #creating a dictionary of id and artifact name {id:artifact name}
            artifact_id = row['id']  # This will be an integer
            id_name[artifact_id] = modify_arti_name(row["name"], type_)
            one_hop_parent_artifacts = query.get_one_hop_parent_artifacts_with_id(artifact_id)  # get immediate artifacts     
            child_parent_artifact_id[artifact_id] = []      # assign empty dict for artifact with no parent artifact
            if not one_hop_parent_artifacts.empty:        # if artifact have parent artifacts    
                parents_list =  list(one_hop_parent_artifacts["id"])
                # Filter parent artifacts to only include those from the current pipeline
                pipeline_filtered_parents = [pid for pid in parents_list if pid in current_pipeline_artifact_ids]
                final_parents_list = list(set(pipeline_filtered_parents) - skip_ids)
                child_parent_artifact_id[artifact_id] = final_parents_list

    data_organized: List[List[Dict[str, Any]]] = topological_sort(child_parent_artifact_id, id_name)
    return data_organized

def topological_sort(input_data, artifact_name_id_dict) -> List[List[Dict[str, Any]]]:
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
