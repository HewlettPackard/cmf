import argparse
import yaml
import pandas as pd
import typing as t
import uuid
from ml_metadata.metadata_store import metadata_store
from ml_metadata.proto import metadata_store_pb2 as mlpb
from cmflib import cmfquery
from cmflib import cmf

pipeline_name = ""

parser = argparse.ArgumentParser()
parser.add_argument('--cmf_filename', type=str, default="mlmd", help="cmf filename")
args = parser.parse_args()

def get_cmf_hierarchy(execution_lineage:str):
    cmf_levels = execution_lineage.split(',')
    return cmf_levels[-1], cmf_levels[1], cmf_levels[0]

def ingest_metadata(execution_lineage:str, metadata:dict, execution_exist:bool, metawriter:cmf.Cmf) :
    pipeline_name, context_name, execution = get_cmf_hierarchy(execution_lineage)
    _ = metawriter.create_context(pipeline_stage=context_name)

    if execution_exist:
        _ = metawriter.update_execution(int(execution))
    else :
        _ = metawriter.create_execution(execution)

    for k, v in metadata.items():
        if k == "deps":
            for dep in v:
                metawriter.log_dataset_with_version(dep["path"], dep["md5"], "input")
        if k == "outs":
            for out in v:
                metawriter.log_dataset_with_version(out["path"], out["md5"], "output")

#Query mlmd to get all the executions and its commands
cmd_exe = {}
cmf_query = cmfquery.CmfQuery(args.cmf_filename)
pipelines: t.List[str] = cmf_query.get_pipeline_names()
for pipeline in pipelines:
    pipeline_name = pipeline
    stages: t.List[str] = cmf_query.get_pipeline_stages(pipeline)
    for stage in stages:
        exe_df: pd.DataFrame = cmf_query.get_all_executions_in_stage(stage)

        if not exe_df.empty:
            exe_step = exe_df['Execution'].values[0]
            cmd_exe[exe_step] = str(exe_df['id'].values[0]) + "," + stage + "," + pipeline

#Parse dvc.lock file
pipeline_dict = {}
with open("dvc.lock", 'r') as f:
    valuesYaml = yaml.load(f, Loader=yaml.FullLoader)

for k in valuesYaml['stages']:
    pipeline_dict[k] = {}
    commands=[]
    deps = []
    outs = []
    k_dict = {}
    i = 0

    for kk in valuesYaml['stages'][k]:
        if kk == 'cmd':
            cmd_list = valuesYaml['stages'][k][kk].split()
            commands.append(cmd_list)
            k_dict['cmd'] = cmd_list
            i = i + 1
        if kk == 'deps':
            deps = valuesYaml['stages'][k][kk]
            k_dict['deps'] = deps
        if kk == 'outs':
            outs = valuesYaml['stages'][k][kk]
            k_dict['outs'] = outs

    pipeline_dict[k][str(i)] = k_dict

#Pipeline name if there is no mlmd file
pipeline_name = "Pipeline"+"-"+str(uuid.uuid4()) if not pipeline_name else pipeline_name


metawriter = cmf.Cmf(filename="mlmd", pipeline_name=pipeline_name, graph=True)
for k, v in pipeline_dict.items():
    for kk, vv in v.items():
        for kkk, vvv in vv.items():
            if kkk == 'cmd':
                vvv.pop(0)
                cmd = cmd_exe.get(str(vvv), None)
                if cmd is not None:
                    ingest_metadata(cmd, vv, True)
                else:
                    context_name = k
                    execution_name = vvv[0]
                    lineage = execution_name+","+context_name+","+ pipeline_name
                    ingest_metadata(lineage, vv, False, metawriter)

metawriter.log_dvc_lock("dvc.lock")
