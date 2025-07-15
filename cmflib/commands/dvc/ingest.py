###
# Copyright (2023) Hewlett Packard Enterprise Development LP
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

import os
import yaml
import uuid
import argparse
import typing as t
import pandas as pd

from cmflib import cmfquery, cmf
from cmflib.cli.command import CmdBase
from ml_metadata.metadata_store import metadata_store
from ml_metadata.proto import metadata_store_pb2 as mlpb
from cmflib.utils.helper_functions import fetch_cmf_config_path
from cmflib.cmf_exception_handling import MsgSuccess, FileNotFound

class CmdDVCIngest(CmdBase):
    
    def find_location(self, string, elements):
        for index, element in enumerate(elements):
            if string == element:
                return index
        return None
    
    def get_cmf_hierarchy(self, execution_lineage: str):
        """
            Parses the string and returns, pipeline name, context name and execution name
        """
        cmf_levels = execution_lineage.split(',')
        return cmf_levels[-1], cmf_levels[1], cmf_levels[0]

    def ingest_metadata(self, execution_lineage: str, metadata: dict, metawriter: cmf.Cmf, tracked: dict, command: str = "" ) :
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
        pipeline_name, context_name, execution = self.get_cmf_hierarchy(execution_lineage)

        _ = metawriter.create_execution(
            str(context_name) + '_' + str(execution), 
            {}, 
            cmd = str(command),
            create_new_execution=False
            )
            
        output, config_file_path = fetch_cmf_config_path()
        artifact_repo = list(output.values())[0]

        for k, v in metadata.items():
            props={}
            if k == "deps":
                for dep in v:
                    if dep["path"] not in tracked:
                        metawriter.log_dataset(dep["path"], 'input')
                    else:
                        md5_value = dep["md5"] 
                        url = pipeline_name + ":" + artifact_repo + "/files/md5/" + md5_value[:2] + "/" + md5_value[2:]
                        props["url"] =  url
                        metawriter.log_dataset_with_version(dep["path"], md5_value, "input", props)
            if k == "outs":
                for out in v:
                    md5_value = out["md5"] 
                    url = pipeline_name + ":" + artifact_repo + "/files/md5/" + md5_value[:2] + "/" + md5_value[2:]
                    props["url"] =  url
                    metawriter.log_dataset_with_version(out["path"], md5_value, "output", props)
                    tracked[out["path"]] = True
        return tracked

    def run(self, live):
        """
            Ingest the metadata in dvc.lock file into CMF.
            If mlmd file exist with metadata from metrics logging or logging for other
            metadata not captured in dvc.lock file, pass that mlmd file as the input file.
            This code queries the file for existing pipelines, stages and executions and stores 
            as a dictionary. If the execution cmd in the stored dict, matches the execution command
            in the dvc.lock file, that execution is updated with additional metadata.
            If there is no prior execution captured, a new execution is created
        """
        uuid_ = str(uuid.uuid4())
        pipeline_name = ""
        cmd_exe: t.Dict[str, str] = {}
        query = cmfquery.CmfQuery(self.args.file_name)
        pipelines: t.List[str] = query.get_pipeline_names()

        # Query mlmd to get all the executions and its commands
        for pipeline in pipelines:
            pipeline_name = pipeline
            stages: t.List[str] = query.get_pipeline_stages(pipeline)
            for stage in stages:
                exe_df: pd.DataFrame = query.get_all_executions_in_stage(stage)
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
                    existing = cmd_exe.get(exe_step)
                    if existing is None:
                        cmd_exe[exe_step] = f"{row['id']},{stage},{pipeline}"
                    else:
                        if row['id'] > int(existing.split(',')[0]):
                            cmd_exe[exe_step] = f"{row['id']},{stage},{pipeline}"

        # Parse the dvc.lock file.
        # pipeline_dict stores pipeline stages with the following hierarchy:
        # {
        #     "<stage_name>": {
        #         "<index>": {
        #             "cmd": List[str],        # List of command parts as strings
        #             "deps": List[Dict[str, Any]],  # List of dependency dictionaries
        #             "outs": List[Dict[str, Any]]   # List of output dictionaries
        #         }
        #     }
        # }
        pipeline_dict: t.Dict[str, t.Dict[str, t.Dict[str, t.Union[t.List[str], t.List[t.Dict[str, t.Any]]]]]] = {}
        
        # check whether dvc.lock file present in cwd
        if not os.path.exists("dvc.lock"):
            raise FileNotFound("dvc.lock", os.getcwd())

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

        # Create a unique Pipeline name if there is no mlmd file
        pipeline_name = "Pipeline"+"-"+str(uuid_) if not pipeline_name else pipeline_name
        metawriter = cmf.Cmf(filepath = "mlmd", pipeline_name=pipeline_name, graph=True)

        # Parse the dvc.lock dictionary and get the command section
        tracked = {} #Used to keep a record of files tracked by outs and therefore not needed to be tracked in deps
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
                        pos = self.find_location('--execution_name', vvv)
                        if pos:
                            execution_name = vvv[pos+1]
                        else:
                            execution_name = uuid_
                            
                        context_name = k
                        lineage = execution_name+","+context_name+","+ pipeline_name
                        # Cast vvv to a list of strings to ensure join works correctly.
                        # join the list to single string
                        cmd_str = ' '.join(t.cast(t.List[str], vvv))
                        cmd = cmd_exe.get(cmd_str, None)
                        _ = metawriter.create_context(pipeline_stage=context_name)
                        tracked = self.ingest_metadata(lineage, vv, metawriter, tracked, cmd_str)
        metawriter.log_dvc_lock("dvc.lock")
        return MsgSuccess(msg_str="Command has completed running..")


def add_parser(subparsers, parent_parser):
    HELP = "Ingests metadata from the dvc.lock file into the CMF."

    parser = subparsers.add_parser(
        "ingest",
        parents=[parent_parser],
        description="Ingests metadata from the dvc.lock file into the CMF. If an existing MLMD file is provided, it merges and updates execution metadata based on matching commands, or creates new executions if none exist.",
        help=HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-f", 
        "--file_name", 
        type=str,
        default="mlmd",
        help="Specify input mlmd file name. (default: mlmd)",
        metavar="<file_name>"
    )

    parser.set_defaults(func=CmdDVCIngest)
