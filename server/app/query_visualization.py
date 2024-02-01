import itertools
import re
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout
import pandas as pd
from cmflib import cmfquery
import dvc
import json
import random
import warnings

warnings.filterwarnings("ignore")

def truncate_artifact_name(my_str):
    if "/" in my_str:
        my_str = my_str.split("/")[-1]
    temp = my_str.split(":")
    temp[1] = temp[1][:4]
    temp=":".join(temp)
    return temp

def query_visualization(mlmd_path, pipeline_name):
    query = cmfquery.CmfQuery(mlmd_path)
    stages = query.get_pipeline_stages(pipeline_name)
    list_all_artifacts = []
    temp = []
    temp1 = []
    new_list_artifacts=[]
    pipeline_id=query.get_pipeline_id(pipeline_name)
    for stage in stages:
        executions = query.get_all_executions_in_stage(stage)
        for i in executions.id.to_list():
            artifacts = query.get_all_artifacts_for_execution(i)
            artifact_name_list = [i for i in artifacts.name.to_list()]
            new_list_artifacts.extend(artifact_name_list)
         
        for name in artifacts["name"]:
            list_all_artifacts.append(name)
    temp={}    #dictionary for linking id and node {"name":"id"} example {"data.xml.gz":"27"}    
    node_id_name={}  #dictionary for nodes in data.json file {"id":"1","name":"artifact_name"}
    node_id_name_list=[]
    link_src_trgt_list=[]
    for artifact in list(set(new_list_artifacts)):
        node_id_name={}
        node_id_name['id']=int(query.get_artifact(artifact).id[0])
        node_id_name['name']=truncate_artifact_name(artifact)
        datatype=query.get_artifact(artifact).type[0]
        result="#48D1CC" if datatype == "Dataset" else "#2E8B57" if datatype =="Model" else "#FF8C00"
        node_id_name['color']=result 
        node_id_name_list.append(node_id_name)

    for artifact_name in list(set(new_list_artifacts)):
        immediate_child_artifacts = query.get_one_hop_child_artifacts(artifact_name,pipeline_id)
        if immediate_child_artifacts.empty == True:
            pass
        else:
            for i in list(set(immediate_child_artifacts["name"])):
                link_src_trgt={}
                source_artifact_id=query.get_artifact(artifact_name)
                target_artifact_id=query.get_artifact(i).id[0]
                link_src_trgt["source"]=int(source_artifact_id.id[0])
                link_src_trgt["target"]=int(target_artifact_id)
                link_src_trgt_list.append(link_src_trgt)
    new_list = pd.DataFrame(
    link_src_trgt_list
    ).drop_duplicates().to_dict('records')
    data = {
        "nodes" : node_id_name_list,
        "links" : new_list
    }

    return data

#print(query_visualization("/home/chobey/cmf-server/data/mlmd","Test-env"))
