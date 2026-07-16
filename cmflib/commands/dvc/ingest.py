###
# Copyright (2025) Hewlett Packard Enterprise Development LP
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

from cmflib.cmfquery import CmfQuery
from cmflib.cmf import Cmf
from cmflib.cli.command import CmdBase
from cmflib.dvc_wrapper import git_get_repo
from ml_metadata.metadata_store import metadata_store
from ml_metadata.proto import metadata_store_pb2 as mlpb
from cmflib.utils.helper_functions import fetch_cmf_config_path
from cmflib.cmf_exception_handling import (
    MsgSuccess, 
    FileNotFound, 
    DuplicateArgumentNotAllowed, 
    MissingArgument
)

class CmdDVCIngest(CmdBase):
    
    def find_location(self, search_element: str, list_of_elements: t.List[str]) -> t.Optional[int]:
        for index, element in enumerate(list_of_elements):
            if search_element == element:
                return index
        return None

    def ingest_metadata(self, *args) -> t.Dict[str, bool]:
        """
        Ingest the metadata into cmf
        
        args:
            A tuple of arguments in the following order:
            
            1. execution (str): The execution identifier or filename. 
            - Example: "3" (if already exists in CMF) or "demo_train.py" (if creating new execution).
            2. context_name (str): Context in which this execution is run. 
            - Example: "eval", "active_learning"
            3. pipeline_name (str): Name of the pipeline associated with the execution.
            - Example: "active_learning"
            4. metadata (dict): Parsed metadata dictionary from `dvc.lock` file.
            - Contains "deps" and "outs" describing inputs and outputs with MD5s.
            5. metawriter (object): CMF metadata writer object used to log executions, datasets, etc.
            6. tracked (dict): Dictionary tracking existing datasets that are already logged.
            - Key: dataset path
            - Value: True
            7. command (str): The command that was run for this execution.

        Returns:
            tracked (dict): Updated tracked dictionary after logging input/output datasets.
        """
        execution, context_name, pipeline_name, metadata, metawriter, tracked, command = args

        _ = metawriter.create_execution(
            str(context_name) + '_' + str(execution), 
            {}, 
            cmd = str(command),
            create_new_execution = False
            )
            
        output, config_file_path = fetch_cmf_config_path()
        artifact_repo = list(output.values())[0]

        for options, data in metadata.items():
            props = {}
            props["git_repo"] = git_get_repo()            
            if options == "deps":
                for dep in data:
                    # A dependency path (dep["path"]) can be a full file path like "artifacts/parsed/train.tsv"
                    # or just a directory like "artifacts/parsed".
                    if dep["path"] not in tracked:
                        metawriter.log_dataset(dep["path"], 'input')
                    else:
                        md5_value = dep["md5"] 
                        url = pipeline_name + ":" + artifact_repo + "/files/md5/" + md5_value[:2] + "/" + md5_value[2:]
                        props["url"] = url
                        metawriter.log_dataset_with_version(dep["path"], md5_value, "input", props)
            if options == "outs":
                for out in data:
                    md5_value = out["md5"] 
                    url = pipeline_name + ":" + artifact_repo + "/files/md5/" + md5_value[:2] + "/" + md5_value[2:]
                    props["url"] = url
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
        cmd_args = {
            "file_name": self.args.file_name,
        }
        for arg_name, arg_value in cmd_args.items():
            if arg_value:
                if arg_value[0] == "":
                    raise MissingArgument(arg_name)
                elif len(arg_value) > 1:
                    raise DuplicateArgumentNotAllowed(arg_name,("-"+arg_name[0]))
                
        current_directory = os.getcwd()
        if not self.args.file_name:         # If self.args.file_name is None or an empty list ([]). 
            mlmd_file_name = "./mlmd"       # Default path for mlmd file name.
        else:
            mlmd_file_name = self.args.file_name[0].strip()
            if mlmd_file_name == "mlmd":
                mlmd_file_name = "./mlmd"
         
        current_directory = os.path.dirname(mlmd_file_name)
        # In our case, "mlmd" is the default file name. Whether the file exists or not, we need to continue with the same name.
        if not os.path.exists(mlmd_file_name) and mlmd_file_name != "./mlmd":  
            raise FileNotFound(mlmd_file_name, current_directory)

        uuid_ = str(uuid.uuid4())
        pipeline_name = ""
        cmd_exe: t.Dict[str, str] = {}
        query = cmfquery.CmfQuery(mlmd_file_name)
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

        for stage in valuesYaml['stages']:
            pipeline_dict[stage] = {}
            commands=[]
            deps = []
            outs = []
            k_dict = {}
            i = 0
            
            for options in valuesYaml['stages'][stage]:
                if options == 'cmd':
                    cmd_list = valuesYaml['stages'][stage][options].split()
                    commands.append(cmd_list)
                    k_dict['cmd'] = cmd_list
                    i = i + 1
                if options == 'deps':
                    deps = valuesYaml['stages'][stage][options]
                    k_dict['deps'] = deps
                if options == 'outs':
                    outs = valuesYaml['stages'][stage][options]
                    k_dict['outs'] = outs

            pipeline_dict[stage][str(i)] = k_dict

        # Create a unique Pipeline name if there is no mlmd file
        pipeline_name = "Pipeline" + "-" + str(uuid_) if not pipeline_name else pipeline_name
        metawriter = Cmf(filepath = mlmd_file_name, pipeline_name = pipeline_name, graph = True)

        # Parse the dvc.lock dictionary and get the command section
        tracked = {} #Used to keep a record of files tracked by outs and therefore not needed to be tracked in deps
        for stage, stage_data in pipeline_dict.items():
            for index, dict_data in stage_data.items():
                for options, option_details in dict_data.items():
                    if options == 'cmd':
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
                        option_details.pop(0)
                        # This check is specific to the active learning scenario where '--execution_name' is expected.
                        pos = self.find_location('--execution_name', option_details)
                        if pos:
                            execution_name = option_details[pos+1]
                        else:
                            execution_name = uuid_
                            
                        context_name = stage
                        # Cast option_details to a list of strings to ensure join works correctly.
                        # join the list to single string
                        cmd_str = ' '.join(t.cast(t.List[str], option_details))
                        cmd = cmd_exe.get(cmd_str, None)
                        _ = metawriter.create_context(pipeline_stage=context_name)
                        tracked = self.ingest_metadata(execution_name, context_name, pipeline_name, dict_data, metawriter, tracked, cmd_str)
        metawriter.log_dvc_lock("dvc.lock")
        return MsgSuccess(msg_str="Done.")


def add_parser(subparsers, parent_parser):
    HELP = "Ingests metadata from the dvc.lock file into the CMF."

    parser = subparsers.add_parser(
        "ingest",
        parents=[parent_parser],
        description="Ingests metadata from the dvc.lock file into the CMF. If an existing metadata file is provided, it merges and updates execution metadata based on matching commands; otherwise, it creates new executions.",
        help=HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-f", 
        "--file_name", 
        action="append",
        help="Specify input mlmd file name. (default: mlmd)",
        metavar="<file_name>"
    )

    parser.set_defaults(func=CmdDVCIngest)
