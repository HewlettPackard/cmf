###
# Copyright (2024) Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###

import argparse
import yaml
import pandas as pd
import typing as t
import uuid
from ml_metadata.metadata_store import metadata_store
from ml_metadata.proto import metadata_store_pb2 as mlpb
from cmflib import cmfquery
from cmflib import cmf


"""
Ingest the metadata in dvc.lock file into CMF.
If cmf mlmd file exist with metadata from metrics logging or logging for other
metadata not captured in dvc.lock file, pass that mlmd file as the input file.
This code queries the file for existing pipelines, stages and executions and stores 
as a dictionary. If the execution cmd in the stored dict, matches the execution command
in the dvc.lock file, that execution is updated with additional metadata.
If there is no prior execution captured, a new execution is created
"""
uuid_ = str(uuid.uuid4())

pipeline_name = ""

parser = argparse.ArgumentParser()
"""
File name of the cmf metadata file . Pass the file name if the pipeline has been recorded
with CMF explicit log statements , to record metadata not part of dvc.lock file
"""
parser.add_argument('--cmf_filename', type=str, default="mlmd", help="cmf filename")
args = parser.parse_args()

"""
Parses the string and returns, pipeline name, context name and execution name
"""
def get_cmf_hierarchy(execution_lineage:str):
    cmf_levels = execution_lineage.split(',')
    return cmf_levels[-1], cmf_levels[1], cmf_levels[0]

"""
Ingest the metadata into cmf
args
    execution_lineage: format- execution id(if present)/execution file name/context/pipeline
      eg - demo_train.py,active_learning_training@2,active_learning -- without existing execution
         - 3,eval,active_learning -- with existing execution in cmf metadata file
    metadata: The parsed dictionary from dvc.lock file
    execution_exist : True if it exeist, False otherwise
    metawrite: cmf object 
"""
def ingest_metadata(execution_lineage:str, metadata:dict, metawriter:cmf.Cmf, command:str = "") :
    pipeline_name, context_name, execution = get_cmf_hierarchy(execution_lineage)

    _ = metawriter.create_execution(
        str(context_name) + '_' + str(execution), 
        {}, 
        cmd = str(command),
        create_new_execution=False
        )
        
    for k, v in metadata.items():
        if k == "deps":
            for dep in v:
                metawriter.log_dataset_with_version(dep["path"], dep["md5"], "input")
        if k == "outs":
            for out in v:
                metawriter.log_dataset_with_version(out["path"], out["md5"], "output")

def find_location(string, elements):
    for index, element in enumerate(elements):
        if string == element:
            return index
    return None

#Query mlmd to get all the executions and its commands
cmd_exe = {}
cmf_query = cmfquery.CmfQuery(args.cmf_filename)
pipelines: t.List[str] = cmf_query.get_pipeline_names()
for pipeline in pipelines:
    pipeline_name = pipeline
    stages: t.List[str] = cmf_query.get_pipeline_stages(pipeline)
    for stage in stages:
        exe_df: pd.DataFrame = cmf_query.get_all_executions_in_stage(stage)
        """
        Parse all the executions in a stage
        eg- exe_step = ['demo_eval.py', '--trained_model', 'data/model-1', '--enable_df', 'True', '--round', '1']
        """
        for index, row in exe_df.iterrows():
            exe_step = row['Execution']
            '''
            if already same execution command has been captured previously use the latest
            execution id to associate the new metadata
            '''
            if None is cmd_exe.get(exe_step, None):
                cmd_exe[exe_step] = str(row['id']) + "," + stage + "," + pipeline
            else:
                if row['id'] > int(cmd_exe.get(exe_step, None).split(',')[0]):
                    cmd_exe[exe_step] = str(row['id']) + "," + stage + "," + pipeline

"""
Parse the dvc.lock file.
"""
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

"""
Create a unique Pipeline name if there is no mlmd file
"""


pipeline_name = "Pipeline"+"-"+str(uuid_) if not pipeline_name else pipeline_name
metawriter = cmf.Cmf(filename="mlmd", pipeline_name=pipeline_name, graph=True)

"""
Parse the dvc.lock dictionary and get the command section
"""
for k, v in pipeline_dict.items():
    for kk, vv in v.items():
        for kkk, vvv in vv.items():
            if kkk == 'cmd':
                """
                Key eg - cmd
                Value eg - ['python3', 'demo.py', '--enable_df', 'True']
                cmd_exe eg - {"['demo_eval.py', '--trained_model', 'data/model-3', '--enable_df', 'True', '--round', '3']":
                '3,eval,active_learning', 
                "['demo_eval.py', '--trained_model', 'data/model-2', '--enable_df', 'True', '--round', '2']": '2,eval,active_learning',
                "['demo_eval.py', '--trained_model', 'data/model-1', '--enable_df', 'True', '--round', '1']": '1,eval,active_learning'}
                In the next line pop out the python
                if the pipeline_dict command is already there in the cmd_exe dict got from parsing the mlmd pop that cmd out 
                and use the stored lineage from the mlmd
                """
                vvv.pop(0)
                pos = find_location('--execution_name', vvv)
                if pos:
                    execution_name = vvv[pos+1]
                else:
                    execution_name = uuid_
                    
                context_name = k
                lineage = execution_name+","+context_name+","+ pipeline_name

                cmd = cmd_exe.get(str(' '.join(vvv)), None)
                _ = metawriter.create_context(pipeline_stage=context_name)

                ingest_metadata(lineage, vv, metawriter, str(' '.join(vvv)))


metawriter.log_dvc_lock("dvc.lock")
