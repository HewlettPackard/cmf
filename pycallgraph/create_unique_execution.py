from cmflib import cmf, cmfquery, cmf_merger
from pycallgraph2 import PyCallGraph
from pycallgraph2 import Config
from pycallgraph2.output import GraphvizOutput
from pycallgraph2 import GlobbingFilter
import pandas as pd
import typing as t
import json, glob
import os



def create_unique_executions(server_store_path, req_info):
        mlmd_data = req_info
        pipelines = mlmd_data["Pipeline"]
        pipeline = pipelines[0]
        pipeline_name = pipeline["name"]
        executions_server = []
        list_executions_exists = []
        if os.path.exists(server_store_path):
            query = cmfquery.CmfQuery(server_store_path)
            stages = query.get_pipeline_stages(pipeline_name)
            for stage in stages:
                executions = []
                executions = query.get_all_executions_in_stage(stage)
                for i in executions.index:
                    for uuid in executions['Execution_uuid'][i].split(","):
                        executions_server.append(uuid)
            executions_client = []
            for i in mlmd_data['Pipeline'][0]["stages"]:  # checks if given execution_id present in mlmd
                for j in i["executions"]:
                    if j['name'] != "": #If executions have name , they are reusable executions
                        continue       #which needs to be merged in irrespective of whether already
                                   #present or not so that new artifacts associated with it gets in.
                    if 'Execution_uuid' in j['properties']:
                        for uuid in j['properties']['Execution_uuid'].split(","):
                            executions_client.append(uuid)
                    else:
                    # mlmd push is failed here
                        status="version_update"
                        return status
            if executions_server != []:
                list_executions_exists = list(set(executions_client).intersection(set(executions_server)))
            for i in mlmd_data["Pipeline"]:
                for stage in i['stages']:
                    for cmf_exec in stage['executions'][:]:
                        uuids = cmf_exec["properties"]["Execution_uuid"].split(",")
                        for uuid in uuids:
                            if uuid in list_executions_exists:
                                stage['executions'].remove(cmf_exec)

            for i in mlmd_data["Pipeline"]:
                i['stages']=[stage for stage in i['stages'] if stage['executions']!=[]]
        for i in mlmd_data["Pipeline"]:
            if len(i['stages']) == 0 :
                status="exists"
            else:
                cmf_merger.parse_json_to_mlmd(
                    json.dumps(mlmd_data), "/cmf-server/data/mlmd", "push", None
                )
                status='success'
        return status



def create_unique_exe() -> None:
    config = Config(max_depth=9)
    config.trace_filter = GlobbingFilter(exclude=["pycallgraph2.*", "selectors.*", "collections.*", "<module>", "email.*", "fsspec.*", "funcy.*",
                                                   "logging.*", "absl.*", "typing.*", "threading.*", "sre_compile.*", "sre_parse.*", "codecs.*",
                                                   "warnings.*", "os.*", "subprocess.*", "<lambda>", "encodings.*", "gzip.*", "genericpath.*", 
                                                   "_process_posts", "enum.*", "uuid.*", "xml.*", "pandas.*", "numpy.*"])
    graphviz = GraphvizOutput(output_file='create_unique_exe.png')
    with PyCallGraph(output=graphviz, config=config):
        mlmdfilePath="/home/ayesha/cmf-server/data/mlmd"
        pipeline_name="Test-env"
        query = cmfquery.CmfQuery(mlmdfilePath)
        req_info = query.dumptojson(pipeline_name)
        info = json.loads(req_info)
        create_unique_executions(mlmdfilePath, info)

if __name__ == '__main__':
    create_unique_exe()
