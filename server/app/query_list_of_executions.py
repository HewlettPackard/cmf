import warnings

warnings.filterwarnings("ignore")
def query_list_of_executions(pipeline_name, dict_of_exe_ids):
    list_of_exec = []
    list_of_exec_uuid = []
    list_of_exec = dict_of_exe_ids[pipeline_name]["Context_Type"].tolist()
    list_of_uuid = dict_of_exe_ids[pipeline_name]["Execution_uuid"].tolist()
    for exec_type, uuid in zip(list_of_exec, list_of_uuid):
        list_of_exec_uuid.append(exec_type.split("/",1)[1] + "_" + uuid.split("-")[0][:4])
    return list_of_exec_uuid
