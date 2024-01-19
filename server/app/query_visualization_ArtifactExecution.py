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
def query_visualization_ArtifactExecution(mlmd_path, pipeline_name):
    file_path="/cmf-server/data/static/data.json"
    query = cmfquery.CmfQuery(mlmd_path)
    stages = query.get_pipeline_stages(pipeline_name)
    node_id_name_list=[]
    link_src_trgt_list=[]
    seen_ids_and_names = set()
    for stage in stages:
        executions = query.get_all_executions_in_stage(stage)
        for i in executions.id.to_list():
            artifacts = query.get_all_artifacts_for_execution(i)
#            print(artifacts['name'],type(artifacts))
            print("___________________")
            for i in range(len(artifacts)):
                node_id_name={}
                link_src_trgt_={}
                node_id_name["id"]=artifacts.loc[i, "id"]
                node_id_name["name"]=artifacts.loc[i, "name"]
                id_and_name = (node_id_name['id'], node_id_name['name'])
                if id_and_name not in seen_ids_and_names:
                    seen_ids_and_names.add(id_and_name)
                    node_id_name_list.append(node_id_name)
                if artifacts.loc[i, "event"] == "INPUT":
                    link_src_trgt["source"]=stage
                    link_src_trgt["target"]=artifacts.loc[i,"id"]
    for stage in stages:
        id_list=[100:200]
        node_id_name["id"]
#            for i in artifacts:
#                print(i['name'])
        print(stage)
        
query_visualization_ArtifactExecution("/home/chobey/cmf-server/data/mlmd","image")
