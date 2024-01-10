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
def query_visualization_execution(mlmd_path, pipeline_name):
    file_path="/cmf-server/data/static/data.json"
    query = cmfquery.CmfQuery(mlmd_path)
    stages = query.get_pipeline_stages(pipeline_name)
    list_all_artifacts = []
    temp = []
    temp1 = []
    new_list_artifacts=[]
    node_id_name_list=[]
    link_src_trgt_list=[]
    for i in range(len(stages)):
        node_id_name={}
        link_src_trgt={}
        executions = query.get_all_executions_in_stage(stages[i])
        node_id_name["id"]=int(i)
        node_id_name["name"]=stages[i]
        if i+1 < len(stages):
            link_src_trgt["source"]=i
            link_src_trgt["target"]=i+1
            link_src_trgt_list.append(link_src_trgt)
        node_id_name_list.append(node_id_name)
 
    data = {
        "nodes" : node_id_name_list,
        "links" : link_src_trgt_list
    }
    with open(file_path, 'w') as json_file:
        json.dump(data, json_file)
    return file_path

#print(query_visualization_execution("/home/chobey/cmf-server/data/mlmd","image"))
