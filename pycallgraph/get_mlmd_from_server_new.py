from cmflib import cmf, cmfquery, cmf_merger
from pycallgraph2 import PyCallGraph
from pycallgraph2 import Config
from pycallgraph2.output import GraphvizOutput
from pycallgraph2 import GlobbingFilter
import pandas as pd
import typing as t
import json, glob
import os


def get_mlmd_from_server(server_store_path: str, pipeline_name: str, exec_id: str):
    query = cmfquery.CmfQuery(server_store_path)
    execution_flag = 0
    json_payload = None
    df = pd.DataFrame()
    if(query.get_pipeline_id(pipeline_name)!=-1):  # checks if pipeline name is available in mlmd
        if exec_id != None:
            exec_id = int(exec_id)
            df = query.get_all_executions_by_ids_list([exec_id])
            if df.empty:
                json_payload = "no_exec_id"
                return json_payload
        json_payload = query.dumptojson(pipeline_name, exec_id)
    return json_payload


def get_mlmd() -> None:
    config = Config(max_depth=9)
    config.trace_filter = GlobbingFilter(exclude=["pycallgraph2.*", "selectors.*", "collections.*", "<module>", "email.*", "fsspec.*", "funcy.*", 
                                                   "logging.*", "absl.*", "typing.*", "threading.*", "sre_compile.*", "sre_parse.*", "codecs.*",
                                                   "warnings.*", "os.*", "subprocess.*", "<lambda>", "encodings.*", "gzip.*", "genericpath.*",
                                                   "_process_posts", "enum.*", "uuid.*", "xml.*", "pandas.*", "numpy.*"])
    graphviz = GraphvizOutput(output_file='mlmd_from_server_new.png')
    with PyCallGraph(output=graphviz, config=config):
        mlmdfilePath="/home/ayesha/cmf-server/data/mlmd"
        pipeline_name="Test-env"
        jsonInfo = get_mlmd_from_server(mlmdfilePath, pipeline_name, None)
        print(jsonInfo)

if __name__ == '__main__':
    get_mlmd()



