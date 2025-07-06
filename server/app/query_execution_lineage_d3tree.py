from cmflib.cmfquery import CmfQuery
from collections import deque, defaultdict
import pandas as pd

class UniqueQueue:
    def __init__(self):
        self.queue = deque()
        self.seen = set()
    
    def enqueue(self, value):
        if value not in self.seen:
            self.queue.append(value)
            self.seen.add(value)
    
    def dequeue(self):
        if self.queue:
            value = self.queue.popleft()
            self.seen.remove(value)
            return value
        raise IndexError("dequeue from an empty queue")
    
    def __len__(self):
        return len(self.queue)
    
    def __contains__(self, value):
        return value in self.seen


def query_execution_lineage_d3tree(query: CmfQuery, pipeline_name: str, dict_of_exe_id: dict, uuid: str):
    pipeline_id = query.get_pipeline_id(pipeline_name)
    df=dict_of_exe_id[pipeline_name]
    
    #finding execution_id by comparing Execution_uuid (d09fdb26-0e9d-11ef-944f-4bf54f5aca7f) and uuid ('Prepare_u3tr')  
    result = df[df['Execution_uuid'].str[:4] == uuid]   #result = df[id: "1","Execution_type_name", "Execution_uuid"]
    execution_id=result["id"].tolist() 
    # Return error if no execution ID is found for the given uuid
    if not execution_id:  
        return {"error": f"uuid '{uuid}' does not match any execution in pipeline '{pipeline_name}'"}
    parents_set = set()
    queue = UniqueQueue()
    df = pd.DataFrame()
    parents = query.get_one_hop_parent_executions_ids(execution_id, pipeline_id) #list of parent execution ids
    dict_parents = {}
    if parents == None:
        parents = []
    dict_parents[execution_id[0]] = list(set(parents))  # [2] = [1,2,3,4] list of parent id
    parents_set.add(execution_id[0])     #created so that we can directly find execuions using execution ids
    for i in set(parents):
        queue.enqueue(i)
        parents_set.add(i)

    while len(queue) > 0:
        exe_id = queue.dequeue()
        parents = query.get_one_hop_parent_executions_ids([exe_id], pipeline_id)
        if parents == None:
            parents = [] 
        dict_parents[exe_id] = list(set(parents))
        for i in set(parents):
            queue.enqueue(i)
            parents_set.add(i)
    
    df = query.get_executions_with_execution_ids(list(parents_set))  # for execution_id get executions(complete df with all data of executions)
    df['name_uuid'] = df['Execution_type_name'] + '_' + df['Execution_uuid'] 
    result_dict = df.set_index('id')['name_uuid'].to_dict()   # {"id" : "name_uuid"} for example {"2":"Prepare_d09fdb26-0e9d-11ef-944f-4bf54f5aca7f"}

    data_organized = topological_sort(dict_parents,result_dict) # it will use topological sort to create data from parents to child pattern
    """
    data_organized format
    [[{'id': 'Prepare_d09f', 'parents': []}],  
    [{'id': 'Featurize_fae6', 'parents': ['Prepare_d09f']}], 
    [{'id': 'Train_7fe7', 'parents': ['Featurize_fae6']}]]
    """
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
    # creating list of list which contains dictionary of {"id":1,parents:"execution_name"}
    for id_val in topo_sorted_nodes:   # topo_sorted_nodes = ['1','2','3','4']
        if id_val in input_data:       # input_data = {"child_id":[parents_id]}, for example {"4":['3','7','9']}
            parents = tuple(sorted(input_data[id_val]))
            # {tuple(parents): {'id':execution_name,'parents':["exec_1","exec_2","exec_3"]}
            # append id,parents to key with same parents to get all child in same list
            parent_dict[parents].append({'id': modify_exec_name(execution_id_dict[id_val]),'parents': [modify_exec_name(execution_id_dict[parent]) for parent in input_data[id_val]]})
    output_data= list(parent_dict.values()) 
    return output_data

def modify_exec_name(exec_name_uuid):
    # First split by '/' once, and then split by '_' to get the parts.
    # 'Test-env/Prepare_d09fdb26-0e9d-11ef-944f-4bf54f5aca7f' ------->  'Prepare_d09fdb26-0e9d-11ef-944f-4bf54f5aca7f'
    # "huggingface_leaderboard/Evaluation_2_01-ai/Yi-34B_1eb053ac-c143-11ee-8b31-996711f273d5" ---------> 'Evaluation_2_01-ai/Yi-34B_1eb053ac-c143-11ee-8b31-996711f273d5'
    after_first_slash = exec_name_uuid.split('/', 1)[1]

    # Use rsplit only once to get the name and uuid parts.
    # 'Prepare_d09fdb26-0e9d-11ef-944f-4bf54f5aca7f' --------> ['Prepare','d09fdb26-0e9d-11ef-944f-4bf54f5aca7f']
    # 'Evaluation_2_01-ai/Yi-34B_1eb053ac-c143-11ee-8b31-996711f273d5' ----> ['Evaluation_2_01-ai/Yi-34B', '1eb053ac-c143-11ee-8b31-996711f273d5']
    name_and_uuid = after_first_slash.rsplit('_', 1)
    
    # Name comes from the first part (before the last '_')
    #  ['Prepare','d09fdb26-0e9d-11ef-944f-4bf54f5aca7f'] ----> ['Prepare]
    # ['Evaluation_2_01-ai/Yi-34B', '1eb053ac-c143-11ee-8b31-996711f273d5'] -----> ['Evaluation_2_01-ai/Yi-34B']
    name = name_and_uuid[0]

    # UUID is taken from the last part of the rsplit (after the last '_')
    # 'd09fdb26-0e9d-11ef-944f-4bf54f5aca7f' ----->  d09f
    # '1eb053ac-c143-11ee-8b31-996711f273d5' -----> 1eb0
    uuid = name_and_uuid[1].split('-')[0][:4]

    # Combine the name and shortened UUID
    result = name + "_" + uuid
    return result