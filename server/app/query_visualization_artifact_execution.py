from cmflib.cmfquery import CmfQuery
from collections import deque, defaultdict
import warnings

warnings.filterwarnings("ignore")

async def query_visualization_artifact_execution(query: CmfQuery, pipeline_name: str, dict_art_id: dict, dict_exe_id: dict) -> list:
    arti_exe_dict = {} # Used to map artifact and execution ids with artifact and execution names
    dict_output: dict[str, list[str]] = {}   # Used to establish parent-child relationship between artifacts and executions
    exclusion_list: list[int] = []

    df = dict_exe_id[pipeline_name]
    
    # Mapping execution id with execution name
    # Here appending execution id with "execution_name_" which will helpful in gui side to differentiate artifact and execution names
    for _, df_row in df.iterrows():
        arti_exe_dict["e_"+str(df_row['id'])] = "execution_name_"+df_row['Context_Type']+":"+df_row['Execution_uuid'][:4]  
    
    for type_, df in dict_art_id[pipeline_name].items():
        if type_ == "Environment" or type_ == "Label":
            exclusion_list = list(df["id"])
        for _, df_row in df.iterrows():
            if df_row['id'] in exclusion_list:
                continue
            # Fetching executions based on artifact id 
            # When the same artifact is shared between two pipelines (e.g., Test-env1 and Test-env2),
            # get_all_executions_for_artifact_id returns executions from both pipelines, not just the current one.
            data = query.get_all_executions_for_artifact_id(df_row['id'])
            
            # Mapping artifact id with artifact name
            # Here appending artifact id with "artifact_name_" which will helpful in gui side to differentiate artifact and execution names
            arti_exe_dict["a_"+str(df_row['id'])] = "artifact_name_"+modify_artifact_name(df_row['name'], type_)  
            
            # To check whether any artifact is given as output to any executions or not
            # This is helpful to define starting point of tree
            output_flag =  False

            if not data.empty:
                for _, data_row in data.iterrows():
                    '''create pattern like this:
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
                    # Taken executions based on pipeline name
                    if data_row['pipeline'] == pipeline_name:
                        if data_row['Type'] == "INPUT":
                            # if same key present then append respective values of that key otherwise create new key value pair
                            if 'e_'+str(data_row['execution_id']) in dict_output.keys():
                                dict_output['e_'+str(data_row['execution_id'])].append("a_"+str(df_row['id']))
                            else:
                                dict_output['e_'+str(data_row['execution_id'])] =  ["a_"+str(df_row['id'])]
                        else:
                            if 'a_'+str(df_row['id']) in dict_output.keys():
                                dict_output['a_'+str(df_row['id'])].append("e_"+str(data_row['execution_id']))
                            else:
                                dict_output['a_'+str(df_row['id'])]=["e_"+str(data_row['execution_id'])]
                            output_flag = True
            else:
                dict_output["a_"+str(df_row['id'])] = []
            
            # If artifact is not taken as output by any executions then make parents of that given artifact to empty
            if(not output_flag):
                dict_output["a_"+str(df_row['id'])] = []

    data_organized = topological_sort(dict_output, arti_exe_dict)
    return data_organized

def topological_sort(input_data: dict, arti_exe_dict: dict) -> list:
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
            parent_dict[parents].append({'id':arti_exe_dict[id_val],'parents': [arti_exe_dict[parent] for parent in input_data[id_val]]})
    output_data= list(parent_dict.values()) 
    return output_data


def modify_artifact_name(artifact_name: str, type: str) -> str:
    # artifact_name optimization based on artifact type.["Dataset","Model","Metrics"]
    try:
        name = ""
        if type == "Metrics" :   # Example metrics:4ebdc980-1e7c-11ef-b54c-25834a9c665c:388 -> metrics:4ebd:388
            name = f"{artifact_name.split(':')[0]}:{artifact_name.split(':')[1][:4]}:{artifact_name.split(':')[2]}"
        elif type == "Model":
            #first split on ':' then on '/' to get name. Example 'Test-env/prepare:uuid:32' -> prepare_uuid
            name = artifact_name.split(':')[-3].split("/")[-1] + ":" + artifact_name.split(':')[-2][:4]
        elif type == "Dataset":
            if "raw_data" in artifact_name:
                # Example artifacts/raw_data:ee7a79a76326c4a307297880943.. -> raw_data:ee7a
                name = artifact_name.split(':')[0].split("/")[-1]+ ":" + artifact_name.split(':')[-1][:4] 
            else:
                # Example artifacts/data.xml.gz:236d9502e0283d91f689d7038b8508a2 -> data.xml.gz:236d 
                name = artifact_name.rsplit(':')[0].split("/")[-1] + ":" +  artifact_name.split(':')[-1][:4]
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
