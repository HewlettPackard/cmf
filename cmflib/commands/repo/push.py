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

#!/usr/bin/env python3
import argparse
import os
import re

from cmflib import cmfquery
from cmflib.cli.utils import check_minio_server, find_root
from cmflib.utils.helper_functions import generate_osdf_token, branch_exists
from cmflib.utils.dvc_config import DvcConfig
from cmflib.dvc_wrapper import dvc_add_attribute
from cmflib.utils.cmf_config import CmfConfig
from cmflib.cli.command import CmdBase
from cmflib.dvc_wrapper import git_get_repo, git_get_pull, git_get_push, git_get_branch, dvc_push
from cmflib.commands.artifact.push import CmdArtifactPush
from cmflib.commands.metadata.push import CmdMetadataPush
from cmflib.cmf_exception_handling import (
    MsgSuccess, 
    MsgFailure, 
    ArtifactPushSuccess, 
    Minios3ServerInactive, 
    CmfNotConfigured, 
    FileNotFound,
    ExecutionUUIDNotFound,
    MissingArgument,
    DuplicateArgumentNotAllowed,
)


class CmdRepoPush(CmdBase):   
    def git_push(self):
        # Getting GitHub URL from cmf init command
        url = git_get_repo()
        # Example url = https://github.com/ABC/my-repo
        # Check if the URL is a GitHub URL
        if "github.com" not in url:
            raise MsgFailure(msg_str="The repository URL is not a GitHub URL.")
        
        # Extracting the repository owner and name from the URL
        # repo_owner = ABC, repo_name = my-repo
        url_parts = url.split("/")
        repo_owner = url_parts[-2]
        repo_name = url_parts[-1]
        
        # Getting the current branch name
        branch_name = git_get_branch()[0]
        
        # Check whether the branch exists in the GitHub repository
        if branch_exists(repo_owner, repo_name, branch_name):
            # Pull the latest changes from the branch
            stdout, stderr, returncode = git_get_pull(branch_name)
            if returncode != 0:
                raise MsgFailure(msg_str=f"Git pull failed: {stderr}")
            print(stdout)
        
        # Push the changes to the branch
        stdout, stderr, returncode = git_get_push(branch_name)
        if returncode != 0:
            raise MsgFailure(msg_str=f"Git push failed: {stderr}")
        
        return MsgSuccess(msg_str="cmf repo push command executed successfully.")
    
    def artifact_push(self, live):
        """
        Pushes artifacts to the remote storage.

        Raises:
            MissingArgument: If a required argument is missing.
            DuplicateArgumentNotAllowed: If a duplicate argument is provided.
            CmfNotConfigured: If the .cmfconfig file is not configured.
            Minios3ServerInactive: If the Minio server is inactive.
            FileNotFound: If the mlmd file does not exist.
            ExecutionUUIDNotFound: If the execution UUID is not found in the pipeline.

        Returns:
            ArtifactPushSuccess: If the artifacts are successfully pushed to the remote storage.
        """
        cmd_args = {
            "file_name": self.args.file_name,
            "pipeline_name": self.args.pipeline_name,
            "execution_uuid": self.args.execution_uuid,
            "tensorboad": self.args.tensorboard,
            "jobs": self.args.jobs
        }
        # Validates the command arguments.
        for arg_name, arg_value in cmd_args.items():
            if arg_value:
                if arg_value[0] == "":
                    raise MissingArgument(arg_name)
                # Check if the argument is a list and has more than one value
                elif len(arg_value) > 1:
                    raise DuplicateArgumentNotAllowed(arg_name,("-"+arg_name[0]))
                
        result = ""

        # Checks the DVC configuration and the presence of the .cmfconfig file.
        dvc_config_op = DvcConfig.get_dvc_config()
        cmf_config_file = os.environ.get("CONFIG_FILE", ".cmfconfig")

        # find root_dir of .cmfconfig
        output = find_root(cmf_config_file)

        # in case, there is no .cmfconfig file
        if output.find("'cmf' is not configured.") != -1:
            raise CmfNotConfigured(output)

        # Verifies the Minio server status if the remote is Minio.
        out_msg = check_minio_server(dvc_config_op)
        if dvc_config_op["core.remote"] == "minio" and out_msg != "SUCCESS":
            raise Minios3ServerInactive()
        
        # If user has not specified the number of jobs or jobs is not a digit, set it to 4 * cpu_count()
        num_jobs = int(self.args.jobs[0]) if self.args.jobs and self.args.jobs[0].isdigit() else 4 * os.cpu_count()
        
        # If the remote is OSDF, generate a dynamic password and update the DVC configuration.
        if dvc_config_op["core.remote"] == "osdf":
            config_file_path = os.path.join(output, cmf_config_file)
            cmf_config={}
            cmf_config=CmfConfig.read_config(config_file_path)
            #print("key_id="+cmf_config["osdf-key_id"])
            dynamic_password = generate_osdf_token(cmf_config["osdf-key_id"],cmf_config["osdf-key_path"],cmf_config["osdf-key_issuer"])
            #print("Dynamic Password"+dynamic_password)
            dvc_add_attribute(dvc_config_op["core.remote"],"password",dynamic_password)
            #The Push URL will be something like: https://<Path>/files/md5/[First Two of MD5 Hash]
            result = dvc_push(num_jobs)
            return result

        # Determines the mlmd file name and checks its existence.
        current_directory = os.getcwd()
        if not self.args.file_name:         # If self.args.file_name is None or an empty list ([]). 
            mlmd_file_name = "./mlmd"       # Default path for mlmd file name.
        else:
            mlmd_file_name = self.args.file_name[0]
            if mlmd_file_name == "mlmd":
                mlmd_file_name = "./mlmd"
            current_directory = os.path.dirname(mlmd_file_name)
        if not os.path.exists(mlmd_file_name):   #checking if MLMD files exists
            raise FileNotFound(mlmd_file_name, current_directory)
        
        # Creates a CmfQuery object and retrieves all executions in the specified pipeline.
        query = cmfquery.CmfQuery(mlmd_file_name)
        names = []
        isExecUuid = False
        df = query.get_all_executions_in_pipeline(self.args.pipeline_name[0])

        # checking if execution_uuid exists in the df
        for index, row in df.iterrows():
            if row['Execution_uuid'] == self.args.execution_uuid[0] or self.args.execution_uuid[0] in row['Execution_uuid']:
                isExecUuid = True
                break
        
        if not isExecUuid:
            raise ExecutionUUIDNotFound(self.args.execution_uuid[0])
        
        # fetching execution id from df based on execution_uuid 
        exec_id_df = df[df['Execution_uuid'].apply(lambda x: self.args.execution_uuid[0] in x.split(","))]['id'] 
        exec_id = int(exec_id_df.iloc[0])
        
        artifacts = query.get_all_artifacts_for_execution(exec_id)  # getting all artifacts based on execution id
        # dropping artifact with type 'metrics' as metrics doesn't have physical file
        if not artifacts.empty:
            artifacts = artifacts[artifacts['type'] != 'Metrics']
            # adding .dvc at the end of every file as it is needed for pull
            artifacts['name'] = artifacts['name'].apply(lambda name: f"{name.split(':')[0]}.dvc")
            names.extend(artifacts['name'].tolist())

        final_list = []
        for file in set(names):
            # checking if the .dvc exists
            if os.path.exists(file):
                final_list.append(file)
            # checking if the .dvc exists in user's project working directory
            elif os.path.isabs(file):
                    file = re.split("/",file)[-1]
                    file = os.path.join(os.getcwd(), file)
                    if os.path.exists(file):
                        final_list.append(file)
            else:
                # not adding the .dvc to the final list in case .dvc doesn't exists in both the places
                pass
        result = dvc_push(num_jobs, list(final_list))
        return ArtifactPushSuccess(result)
        

    def run(self, live):
        print("Executing cmf artifact push command..")
        if(self.args.execution_uuid):
            # If an execution uuid exists, push the artifacts associated with that execution. 
            artifact_push_result = self.artifact_push(live)
        else:
            # Pushing all artifacts. 
            artifact_push_instance = CmdArtifactPush(self.args)
            artifact_push_result = artifact_push_instance.run(live)

        if artifact_push_result.status == "success":
            print("Executing cmf metadata push command..")
            metadata_push_instance = CmdMetadataPush(self.args)
            metadata_push_result = metadata_push_instance.run(live)
            if metadata_push_result.status == "success":
                print(metadata_push_result.handle())  # Print the message returned by the handle() method of the metadata_push_result object.
                print("Executing git push command..")
                live.stop()
                return self.git_push()
    

def add_parser(subparsers, parent_parser):
    PUSH_HELP = "Push artifacts, metadata files, and source code to the user's artifact repository, cmf-server, and git respectively."

    parser = subparsers.add_parser(
        "push",
        parents=[parent_parser],
        description="Push artifacts, metadata files, and source code to the user's artifact repository, cmf-server, and git respectively.",
        help=PUSH_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    required_arguments = parser.add_argument_group("required arguments")

    required_arguments.add_argument(
        "-p",
        "--pipeline_name",
        required=True,
        action="append",
        help="Specify Pipeline name.",
        metavar="<pipeline_name>",
    )

    parser.add_argument(
        "-f", 
        "--file_name", 
        action="append",
        help="Specify input metadata file name.", 
        metavar="<file_name>"
    )

    parser.add_argument(
        "-e",
        "--execution_uuid",
        action="append",
        help="Specify Execution uuid.",
        default=None,
        metavar="<exec_uuid>",
    )

    parser.add_argument(
        "-t",
        "--tensorboard_path",
        action="append",
        help="Specify path to tensorboard logs for the pipeline.",
        metavar="<tensorboard_path>"
    )

    parser.add_argument(
        "-j",
        "--jobs",
        action="append",
        help="Number of parallel jobs for uploading artifacts to remote storage. Default is 4 * cpu_count(). Increasing jobs may speed up uploads but will use more resources.",
        metavar="<jobs>"
    )

    parser.set_defaults(func=CmdRepoPush)
