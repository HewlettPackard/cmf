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
def query_visualization_execution(mlmd_path, pipeline_name, dict_of_art_ids, dict_of_exe_ids):
    list_of_exec = []
    list_of_exec_uuid = []
    list_of_exec = dict_of_exe_ids[pipeline_name]["Context_Type"].tolist()
    list_of_uuid = dict_of_exe_ids[pipeline_name]["Execution_uuid"].tolist()
    for exec_type, uuid in zip(list_of_exec, list_of_uuid):
        list_of_exec_uuid.append(exec_type + "_" + uuid.split("-")[0][:4])
    return list_of_exec_uuid

#print(query_visualization_execution("/home/chobey/cmf-server/data/mlmd","image"))
