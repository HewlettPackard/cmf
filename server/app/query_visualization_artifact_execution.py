from cmflib import cmfquery
from collections import deque, defaultdict
import warnings

warnings.filterwarnings("ignore")

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
    

async def query_visualization_artifact_execution(mlmd_path, pipeline_name, dict_art_id, dict_exe_id):
    dict_result = {}
    dict_output = {}
    
    query = cmfquery.CmfQuery(mlmd_path)
    df = dict_exe_id[pipeline_name]
    
    # Mapping execution id with name[Context_Type+:+uuid] for eg: Test-env/Train:bb79
    for i,row in df.iterrows():
        dict_result["e_"+str(row['id'])] = "execution_name_"+row['Context_Type']+":"+row['Execution_uuid'][:4]  #Mapping execution id with execution name
    
    for type_, df in dict_art_id[pipeline_name].items():
        for index, row in df.iterrows():
            # Featching executions based on artifact name which is in dict
            data = query.get_all_executions_for_artifact(row['name'])
            
            dict_result["a_"+str(row['id'])] = "artifact_name_"+modify_artifact_name(row['name'], type_)  #Mapping artifact id with artifact name
            
            # To check whether any artifact is given as output to any executions or not
            output_flag =  False
            if not data.empty:
                for index, row1 in data.iterrows():
                    '''Trying to create pattern like that:
                    data=  [ 
                        [{'id': 'data.xml.gz', 'parents': []} ],
                        [{'id': 'prepare', 'parents': ['data.xml.gz']} ],    artifact is passed as a input to executions
                        [
                        {'id': 'train.tsv', 'parents': ['prepare']},       based on executions new artifact is generated
                        {'id': 'test.tsv', 'parents': ['prepare']}
                        ],
                        [{'id': 'featurize', 'parents': ['train.tsv','test.tsv']}],
                        [
                        {'id': 'train.pkl', 'parents': ['featurize']},
                        {'id': 'test.pkl', 'parents': ['featurize']}
                        ],
                    ]  
                    Here the logic is if type is input then we need to specify executions as a id and artifacts as parents
                    otherwise we need to specify artifacts as id and executions as parents'''

                    if row1['Type'] == "INPUT":
                        # if same key present then append respective values to that key
                        if 'e_'+str(row1['execution_id']) in dict_output.keys():
                            dict_output['e_'+str(row1['execution_id'])].append("a_"+str(row['id']))
                        else:
                            dict_output['e_'+str(row1['execution_id'])] =  ["a_"+str(row['id'])]
                    else:
                        if 'a_'+str(row['id']) in dict_output.keys():
                            dict_output['a_'+str(row['id'])].append("e_"+str(row1['execution_id']))
                        else:
                            dict_output['a_'+str(row['id'])]=["e_"+str(row1['execution_id'])]
                        output_flag = True
            else:
                dict_output["a_"+str(row['id'])] = []
            
            # If artifact is not taken as output by any executions then make parents of artifact to []
            if(not output_flag):
                dict_output["a_"+str(row['id'])] = []
            

    data_organized = topological_sort(dict_output, dict_result)
    return data_organized

def topological_sort(input_data, execution_id_dict):
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
            parent_dict[parents].append({'id':execution_id_dict[id_val],'parents': [execution_id_dict[parent] for parent in input_data[id_val]]})
    output_data= list(parent_dict.values()) 
    return output_data


def modify_artifact_name(artifact_name: str, type: str):
    # artifact_name optimization based on artifact type.["Dataset","Model","Metrics"]
    try:
        name = ""
        if type == "Metrics" :   # Example metrics:4ebdc980-1e7c-11ef-b54c-25834a9c665c:388 -> metrics:4ebd:388
            name = f"{artifact_name.split(':')[0]}:{artifact_name.split(':')[1][:4]}:{artifact_name.split(':')[2]}"
        elif type == "Model":
            #first split on ':' then on '/' to get name. Example 'Test-env/prepare:uuid:32' -> prepare_uuid
            name = artifact_name.split(':')[-3].split("/")[-1] + ":" + artifact_name.split(':')[-2][:4]
        elif type == "Dataset":
            # Example artifacts/data.xml.gz:236d9502e0283d91f689d7038b8508a2 -> data.xml.gz 
            name = artifact_name.split(':')[-2] .split("/")[-1]  
        elif type == "Dataslice":
            # cmf_artifacts/dataslices/ecd6dcde-4f3b-11ef-b8cd-f71a4cc9ba38/slice-1:e77e3466872898fcf2fa22a3752bc1ca
            dataslice_part1 = artifact_name.split("/",1)[1] #remove cmf_artifacts/
            # dataslices/ecd6dcde-4f3b-11ef-b8cd-f71a4cc9ba38/slice-1 + : + e77e
            name = dataslice_part1.rsplit(":",-1)[0] + ":" + dataslice_part1.rsplit(":",-1)[-1][:4]
        elif type == "Step_Metrics":
            #cmf_artifacts/metrics/1a86b01c-4da9-11ef-b8cd-f71a4cc9ba38/training_metrics:d7c32a3f4fce4888c905de07ba253b6e:3:2029c720-4da9-11ef-b8cd-f71a4cc9ba38
            step_new = artifact_name.split("/",1)[1]     #remove cmf_artifacts/
            step_metrics_part2 = artifact_name.rsplit(":")
            # metrics/1a86b01c-4da9-11ef-b8cd-f71a4cc9ba38/training_metrics: + d7c3 + : +3 + : + 2029
            name = step_new.rsplit(":",-3)[0] + ":" + step_metrics_part2[-3][:4] + ":" + step_metrics_part2[-2] + ":" + step_metrics_part2[-1][:4]
        else:
            name = artifact_name  
    except Exception as e:
        print(f"Error parsing artifact name: {e}")
        name = artifact_name  # Fallback to the original artifact_name in case of error
    return name
