from cmflib import cmf, cmfquery, cmf_merger
from pycallgraph2 import PyCallGraph
from pycallgraph2 import Config
from pycallgraph2.output import GraphvizOutput
from pycallgraph2 import GlobbingFilter
import pandas as pd
import typing as t
import json, glob
import os


def get_mlmd_from_server(server_store_path, pipeline_name, exec_id):
        query = cmfquery.CmfQuery(server_store_path)
        execution_flag = 0
    # checks if given execution_id present in mlmd
        if (
            pipeline_name in query.get_pipeline_names()
        ):  # checks if pipeline name is available in mlmd
            json_payload = query.dumptojson(pipeline_name, None)
            mlmd_data = json.loads(json_payload)["Pipeline"]
            if exec_id == None:
                json_payload = query.dumptojson(pipeline_name, exec_id)
            else:
                for stage in mlmd_data[0]["stages"]:
                    for execution in stage["executions"]:
                        if execution["id"] == int(exec_id):
                            execution_flag = 1
                            break
                if execution_flag == 1:
                    json_payload = query.dumptojson(pipeline_name, exec_id)
                else:
                    json_payload = "no_exec_id"
                    return json_payload
        else:
            json_payload = "NULL"
        return json_payload


def get_mlmd() -> None:
    config = Config(max_depth=9)
    config.trace_filter = GlobbingFilter(exclude=["pycallgraph2.*", "selectors.*", "collections.*", "<module>", "email.*", "fsspec.*", "funcy.*", 
                                                   "logging.*", "absl.*", "typing.*", "threading.*", "sre_compile.*", "sre_parse.*", "codecs.*",
                                                   "warnings.*", "os.*", "subprocess.*", "<lambda>", "encodings.*", "gzip.*", "genericpath.*",
                                                   "_process_posts", "enum.*", "uuid.*", "xml.*", "pandas.*", "numpy.*"])
    graphviz = GraphvizOutput(output_file='mlmd_from_server.png')
    with PyCallGraph(output=graphviz, config=config):
        mlmdfilePath="/home/ayesha/cmf-server/data/mlmd"
        pipeline_name="Test-env"
        jsonInfo = get_mlmd_from_server(mlmdfilePath, pipeline_name, None)
        print(jsonInfo)

if __name__ == '__main__':
    get_mlmd()


