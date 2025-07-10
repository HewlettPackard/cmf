"""This module contains all the public API for CMF"""
###
# Copyright (2022) Hewlett Packard Enterprise Development LP
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

import time
import uuid
import re
import os
import sys
import yaml
import pandas as pd
import typing as t
import json
from cmflib import cmfquery, cmf_merger

# This import is needed for jupyterlab environment
from ml_metadata.proto import metadata_store_pb2 as mlpb
from cmflib.dvc_wrapper import (
    dvc_get_url,
    dvc_get_hash,
    git_get_commit,
    commit_output,
    git_get_repo,
    commit_dvc_lock_file,
    git_checkout_new_branch,
    check_git_repo,
    check_default_remote,
    check_git_remote,
    git_commit,
)
from cmflib import graph_wrapper
from cmflib.store.sqllite_store import SqlliteStore
from cmflib.store.postgres import PostgresStore 
from cmflib.metadata_helper import (
    get_or_create_parent_context,
    get_or_create_run_context,
    get_or_create_context_with_type,
    update_context_custom_properties,
    associate_child_to_parent_context,
    create_new_execution_in_existing_run_context,
    link_execution_to_artifact,
    create_new_artifact_event_and_attribution,
    get_artifacts_by_id,
    put_artifact,
    link_execution_to_input_artifact,
)
from cmflib.utils.cmf_config import CmfConfig
from cmflib.utils.helper_functions import get_python_env, change_dir, get_md5_hash, get_postgres_config, calculate_md5
from cmflib.cmf_server import (
    merge_created_context, 
    merge_created_execution, 
    log_python_env_from_client, 
    log_dataset_with_version,
    log_model_with_version, 
    log_execution_metrics_from_client, 
    log_step_metrics_from_client,
    log_dataslice_from_client,
    log_label_with_version,
)

from cmflib.cmf_commands_wrapper import (
    _metadata_push,
    _metadata_pull,
    _metadata_export,
    _artifact_pull,
    _artifact_push,
    _artifact_pull_single,
    _cmf_cmd_init,
    _init_local,
    _init_minioS3,
    _init_amazonS3,
    _init_sshremote,
    _init_osdfremote,
    _artifact_list,
    _pipeline_list,
    _execution_list,
    _repo_push,
    _repo_pull,
    _dvc_ingest,
)

class Cmf:
    """This class provides methods to log metadata for distributed AI pipelines.
    The class instance creates an ML metadata store to store the metadata.
    It creates a driver to store nodes and its relationships to neo4j.
    The user has to provide the name of the pipeline, that needs to be recorded with CMF.
    ```python
    cmflib.cmf.Cmf(
        filepath="mlmd",
        pipeline_name="test_pipeline",
        custom_properties={"owner": "user_a"},
        graph=False
    )
    ```
    Args:
        filepath: Path  to the sqlite file to store the metadata
        pipeline_name: Name to uniquely identify the pipeline.
        Note that name is the unique identifier for a pipeline.
        If a pipeline already exist with the same name, the existing pipeline object is reused.
        custom_properties: Additional properties of the pipeline that needs to be stored.
        graph: If set to true, the libray also stores the relationships in the provided graph database.
        The following
        variables should be set: `neo4j_uri` (graph server URI), `neo4j_user` (user name) and
        `neo4j_password` (user password), e.g.:
        ```
        cmf init local --path /home/user/local-storage --git-remote-url https://github.com/XXX/exprepo.git --neo4j-user neo4j --neo4j-password neo4j
                              --neo4j-uri bolt://localhost:7687
        ```
    """

    # pylint: disable=too-many-instance-attributes
    cmf_config = os.environ.get("CONFIG_FILE", ".cmfconfig")
    ARTIFACTS_PATH = "cmf_artifacts"
    DATASLICE_PATH = "dataslice"
    METRICS_PATH = "metrics"
    # Fix for MyPy error: Ensure attributes are defined properly
    if os.path.exists(cmf_config):
        attr_dict = CmfConfig.read_config(cmf_config)
        __neo4j_uri = attr_dict.get("neo4j-uri", "")
        __neo4j_password = attr_dict.get("neo4j-password", "")
        __neo4j_user = attr_dict.get("neo4j-user", "")

    def __init__(
        self,
        filepath: str = "mlmd",
        pipeline_name: str = "",
        custom_properties: t.Optional[t.Dict] = None,
        graph: bool = False,
        is_server: bool = False,
    ):
        #path to directory
        self.cmf_init_path = filepath.rsplit("/",1)[0] \
				 if len(filepath.rsplit("/",1)) > 1 \
					else  os.getcwd()

        logging_dir = change_dir(self.cmf_init_path)
        temp_store: t.Optional[t.Union[SqlliteStore, PostgresStore]] = None
        if is_server is False:
            Cmf.__prechecks()
            temp_store = SqlliteStore({"filename": filepath})
        else:
            config_dict = get_postgres_config()
            temp_store = PostgresStore(config_dict)
        if custom_properties is None:
            custom_properties = {}
        # If pipeline_name is not provided, derive it from the current folder name 
        # self.pipeline_name to ensure that it is accessible as an instance variable for use in other methods
        if not pipeline_name:
            # assign folder name as pipeline name 
            cur_folder = os.path.basename(os.getcwd())
            pipeline_name = cur_folder
        self.pipeline_name = pipeline_name
        self.store = temp_store.connect()
        self.filepath = filepath
        self.child_context = None
        self.execution = None
        self.execution_name = ""
        self.execution_command = ""
        self.metrics: dict[str, dict[int, dict[str, t.Any]]] = {}
        self.input_artifacts: list[str] = []
        self.execution_label_props: dict[str, str] = {}
        self.graph = graph
        #last token in filepath
        self.branch_name = filepath.rsplit("/", 1)[-1]

        if is_server is False:
            git_checkout_new_branch(self.branch_name)
        self.parent_context = get_or_create_parent_context(
            store=self.store,
            pipeline=self.pipeline_name,
            custom_properties=custom_properties,
        )
        if is_server:
            Cmf.__get_neo4j_server_config()
        if graph is True:
            Cmf.__load_neo4j_params()
            self.driver = graph_wrapper.GraphDriver(
                Cmf.__neo4j_uri, Cmf.__neo4j_user, Cmf.__neo4j_password
            )
            self.driver.create_pipeline_node(
                self.pipeline_name, self.parent_context.id, custom_properties
            )
        os.chdir(logging_dir)

    # Declare methods as class-level callables
    merge_created_context: t.Callable[..., t.Any]
    merge_created_execution: t.Callable[..., t.Any]
    log_python_env_from_client: t.Callable[..., t.Any]
    log_dataset_with_version: t.Callable[..., t.Any]
    log_model_with_version: t.Callable[..., t.Any]
    log_execution_metrics_from_client: t.Callable[..., t.Any]
    log_step_metrics_from_client: t.Callable[..., t.Any]
    log_label_with_version: t.Callable[..., t.Any]

    # function used to load neo4j params for cmf client
    @staticmethod
    def __load_neo4j_params():
         cmf_config = os.environ.get("CONFIG_FILE", ".cmfconfig")
         if os.path.exists(cmf_config):
             attr_dict = CmfConfig.read_config(cmf_config)
             Cmf.__neo4j_uri = attr_dict.get("neo4j-uri", "")
             Cmf.__neo4j_password = attr_dict.get("neo4j-password", "")
             Cmf.__neo4j_user = attr_dict.get("neo4j-user", "")

    # function used to load neo4j params for cmf-server
    @staticmethod
    def __get_neo4j_server_config():
        Cmf.__neo4j_uri = os.getenv('NEO4J_URI', "")
        Cmf.__neo4j_user = os.getenv('NEO4J_USER_NAME', "")
        Cmf.__neo4j_password = os.getenv('NEO4J_PASSWD', "")


    @staticmethod
    def __prechecks():
        """Pre checks for cmf
        1. Needs to be a git repository and
           git remote should be set
        2. Needs to be a dvc repository and
           default dvc remote should be set
        """
        Cmf.__check_git_init()
        Cmf.__check_default_remote()
        Cmf.__check_git_remote()

    @staticmethod
    def __check_git_remote():
        """Executes precheck for git remote"""
        if not check_git_remote():
            print(
                "*** Error git remote not set ***\n"
                "*** Run cmf init ***"
            )
            sys.exit(1)

    @staticmethod
    def __check_default_remote():
        """Executes precheck for default dvc remote"""
        if not check_default_remote():
            print(
                "*** DVC not configured correctly ***\n"
                "*** Run command cmf init ***" 
            )
            sys.exit(1)

    @staticmethod
    def __check_git_init():
        """Verifies that the directory is a git repo"""
        if not check_git_repo():
            print(
                "*** Not a git repo, Please do the following ***\n"
                "*** Run Command cmf init ***"
            )
            sys.exit(1)

    def finalize(self):
        git_commit(self.execution_name)
        if self.graph:
            self.driver.close()

    def create_context(
        self, pipeline_stage: str, custom_properties: t.Optional[t.Dict] = None
    ) -> mlpb.Context:  # type: ignore  # Context type not recognized by mypy, using ignore to bypass
        """Create's a  context(stage).
        Every call creates a unique pipeline stage.
        Updates Pipeline_stage name.
        Example:
            ```python
            #Create context
            # Import CMF
            from cmflib.cmf import Cmf
            from ml_metadata.proto import metadata_store_pb2 as mlpb
            # Create CMF logger
            cmf = Cmf(filepath="mlmd", pipeline_name="test_pipeline")
            # Create context
            context: mlmd.proto.Context = cmf.create_context(
                pipeline_stage="prepare",
                custom_properties ={"user-metadata1": "metadata_value"}
            )

            ```
            Args:
                Pipeline_stage: Name of the Stage.
                custom_properties: Developers can provide key value pairs with additional properties of the execution that
                    need to be stored.
            Returns:
                Context object from ML Metadata library associated with the new context for this stage.
        """
        custom_props = {} if custom_properties is None else custom_properties
        pipeline_stage = self.parent_context.name + "/" + pipeline_stage
        ctx = get_or_create_run_context(
            self.store, pipeline_stage, custom_props)
        self.child_context = ctx
        associate_child_to_parent_context(
            store=self.store, parent_context=self.parent_context, child_context=ctx
        )
        if self.graph:
            self.driver.create_stage_node(
                pipeline_stage, self.parent_context, ctx.id, custom_props
            )
        return ctx

    def update_context(
        self,
        type_name: str,
        context_name: str,
        context_id: int,
        properties: t.Optional[t.Dict] = None,
        custom_properties: t.Optional[t.Dict] = None
    ) -> mlpb.Context:  # type: ignore # Context type not recognized by mypy, using ignore to bypass
        self.context = get_or_create_context_with_type(
                           self.store, 
                           context_name, 
                           type_name, 
                           properties, 
                           type_properties = None,
                           custom_properties = custom_properties
                       )
        if self.context is None:
            print("Error - no context id")
            return

        if custom_properties:
            for key, value in custom_properties.items():
                if isinstance(value, int):
                    self.context.custom_properties[key].int_value = value
                else:
                    self.context.custom_properties[key].string_value = str(
                        value)
        updated_context = update_context_custom_properties(
            self.store,
            context_id,
            context_name,
            self.context.properties,
            self.context.custom_properties,
        )        
        return updated_context

    def create_execution(
        self,
        execution_type: str,
        custom_properties: t.Optional[t.Dict] = None,
        cmd: t.Optional[str] = None,
        create_new_execution: bool = True,
    ) -> mlpb.Execution:    # type: ignore  # Execution type not recognized by mypy, using ignore to bypass
        """Create execution.
        Every call creates a unique execution. Execution can only be created within a context, so
        [create_context][cmflib.cmf.Cmf.create_context] must be called first.
        Example:
            ```python
            # Import CMF
            from cmflib.cmf import Cmf
            from ml_metadata.proto import metadata_store_pb2 as mlpb
            # Create CMF logger
            cmf = Cmf(filepath="mlmd", pipeline_name="test_pipeline")
            # Create or reuse context for this stage
            context: mlmd.proto.Context = cmf.create_context(
                pipeline_stage="prepare",
                custom_properties ={"user-metadata1": "metadata_value"}
            )
            # Create a new execution for this stage run
            execution: mlmd.proto.Execution = cmf.create_execution(
                execution_type="Prepare",
                custom_properties = {"split": split, "seed": seed}
            )
            ```
        Args:
            execution_type: Type of the execution.(when create_new_execution is False, this is the name of execution)
            custom_properties: Developers can provide key value pairs with additional properties of the execution that
                need to be stored.

            cmd: command used to run this execution.

            create_new_execution:bool = True, This can be used by advanced users to re-use executions
                This is applicable, when working with framework code like mmdet, pytorch lightning etc, where the
                custom call-backs are used to log metrics.
                if create_new_execution is True(Default), execution_type parameter will be used as the name of the execution type.
                if create_new_execution is False, if existing execution exist with the same name as execution_type.
                it will be reused.
                Only executions created with  create_new_execution as False will have "name" as a property.


        Returns:
            Execution object from ML Metadata library associated with the new execution for this stage.
        """
        logging_dir = change_dir(self.cmf_init_path)
        # Assigning current file name as stage and execution name
        current_script = sys.argv[0]
        file_name = os.path.basename(current_script)
        assigned_stage_name = os.path.splitext(file_name)[0]
        # create context if not already created
        if not self.child_context:
            self.create_context(pipeline_stage=assigned_stage_name)
            assert self.child_context is not None, f"Failed to create context for {self.pipeline_name}!!"

        # Initializing the execution related fields

        self.metrics = {}
        self.input_artifacts = []
        self.execution_label_props = {}
        custom_props = {} if custom_properties is None else custom_properties
        git_repo = git_get_repo()
        git_start_commit = git_get_commit()
        cmd = str(sys.argv) if cmd is None else cmd

        self.execution = create_new_execution_in_existing_run_context(
            store=self.store,
            # Type field when re-using executions
            execution_type_name=self.child_context.name,
            execution_name=execution_type, 
            #Name field if we are re-using executions
            #Type field , if creating new executions always 
            context_id=self.child_context.id,
            execution=cmd,
            pipeline_id=self.parent_context.id,
            pipeline_type=self.parent_context.name,
            git_repo=git_repo,
            git_start_commit=git_start_commit,
            custom_properties=custom_props,
            create_new_execution=create_new_execution,
        )
        uuids = self.execution.properties["Execution_uuid"].string_value
        if uuids:
            self.execution.properties["Execution_uuid"].string_value = uuids+","+str(uuid.uuid1())
        else:
            self.execution.properties["Execution_uuid"].string_value = str(uuid.uuid1())          
        self.store.put_executions([self.execution])
        self.execution_name = str(self.execution.id) + "," + execution_type
        self.execution_command = cmd
        for k, v in custom_props.items():
            k = re.sub("-", "_", k)
            self.execution_label_props[k] = v
        self.execution_label_props["Execution_Name"] = (
            execution_type + ":" + str(self.execution.id)
        )

        self.execution_label_props["execution_command"] = cmd

        # The following lines create an artifact of type 'Environment'.  
        # This artifact captures detailed information about all installed packages in the environment.  
        # (Additional Information: The package details are retrieved using `pip freeze` or `conda list`.  
        # Note: `pip freeze` lists only Python packages, whereas `conda list` may also include non-Python dependencies.)  

        directory_path = self.ARTIFACTS_PATH
        os.makedirs(directory_path, exist_ok=True)
        packages = get_python_env(env_name=self.branch_name)
        if isinstance(packages, list):
            output = f"{packages}\n"
            md5_hash = get_md5_hash(output)
            python_env_file_path = os.path.join(directory_path, f"python_env_{md5_hash}.txt")
            # create file if it doesn't exists
            if not os.path.exists(python_env_file_path):
                #print(f"{python_env_file_path} doesn't exists!!")
                with open(python_env_file_path, 'w') as file:
                    for package in packages:
                        file.write(f"{package}\n")

        else:
            # in case output is dict
            env_output = yaml.dump(packages, sort_keys=False)
            md5_hash = get_md5_hash(env_output)
            python_env_file_path = os.path.join(directory_path, f"python_env_{md5_hash}.yaml")
            # create file if it doesn't exists
            if not os.path.exists(python_env_file_path):
                #print(f"{python_env_file_path} doesn't exists!!")
                with open(python_env_file_path, 'w') as file:
                    file.write(env_output)

        if self.graph:
            self.driver.create_execution_node(
            self.execution_name,
            self.child_context.id,
            self.parent_context,
            cmd,
            self.execution.id,
            custom_props,
        )
            
        custom_props["Python_Env"] = python_env_file_path
        self.update_execution(self.execution.id, custom_props)
        # link the artifact to execution if it exists and creates artifact if it doesn't
        self.log_python_env(python_env_file_path)
        os.chdir(logging_dir)
        return self.execution

    def update_execution(
        self, execution_id: int, custom_properties: t.Optional[t.Dict] = None
    ):
        """Updates an existing execution.
        The custom properties can be updated after creation of the execution.
        The new custom properties is merged with earlier custom properties.
        Example
            ```python
            # Import CMF
            from cmflib.cmf import Cmf
            from ml_metadata.proto import metadata_store_pb2 as mlpb
            # Create CMF logger
            cmf = Cmf(filepath="mlmd", pipeline_name="test_pipeline")
            # Update a execution
            execution: mlmd.proto.Execution = cmf.update_execution(
                execution_id=8,
                custom_properties = {"split": split, "seed": seed}
            )
            ```
            Args:
                execution_id: id of the execution.
                custom_properties: Developers can provide key value pairs with additional properties of the execution that
                need to be updated.
            Returns:
                Execution object from ML Metadata library associated with the updated execution for this stage.
        """
        self.execution = self.store.get_executions_by_id([execution_id])[0]
        if self.execution is None:
            print("Error - no execution id")
            return
        execution_type = self.store.get_execution_types_by_id([self.execution.type_id])[0]

        if custom_properties:
            for key, value in custom_properties.items():
                if isinstance(value, int):
                    self.execution.custom_properties[key].int_value = value
                else:
                    self.execution.custom_properties[key].string_value = str(value)
        self.store.put_executions([self.execution])
        c_props = {}
        for k, v in self.execution.custom_properties.items():
            key = re.sub("-", "_", k)
            val_type = str(v).split(":", maxsplit=1)[0]
            if val_type == "string_value":
                val = self.execution.custom_properties[k].string_value
            else:
                val = str(v).split(":")[1].strip()
            # The properties value are stored in the format type:value hence,
            # taking only value
            self.execution_label_props[key] = val
            c_props[key] = val
        self.execution_name = str(self.execution.id) + \
            "," + execution_type.name
        self.execution_command = self.execution.properties["Execution"]
        self.execution_label_props["Execution_Name"] = (
            execution_type.name + ":" + str(self.execution.id)
        )
        self.execution_label_props["execution_command"] = self.execution.properties[
            "Execution"
        ].string_value
        if self.graph:
            self.driver.create_execution_node(
                self.execution_name,
                self.child_context.id,
                self.parent_context,
                self.execution.properties["Execution"].string_value,
                self.execution.id,
                c_props,
            )
        return self.execution

    def log_python_env(
            self,
            url: str,
        ) -> mlpb.Artifact: # type: ignore  # Artifact type not recognized by mypy, using ignore to bypass
            """
            Logs the Python environment used in the current execution by creating an 'Environment' artifact.

            This function retrieves information about the Python environment, including package details,
            and associates it with the current execution. It ensures that the environment's state is 
            tracked using a DVC hash and links it with the execution in a metadata store.

            Args:
                url (str): The path to the artifact.

            Returns:
                    Artifact object from ML Metadata library associated with the new dataset artifact.
            """
            git_repo = git_get_repo()
            name = re.split("/", url)[-1]
            existing_artifact: list[mlpb.Artifact] = [] # type: ignore  # Artifact type not recognized by mypy, using ignore to bypass

            if self.execution is None:
                raise ValueError("Execution is not initialized. Please create an execution before calling this method.")
            
            commit_output(url, self.execution.id)
            c_hash = dvc_get_hash(url)

            if c_hash == "":
                print("Error in getting the dvc hash,return without logging")
                return

            commit = c_hash
            dvc_url = dvc_get_url(url)
            dvc_url_with_pipeline = f"{self.parent_context.name}:{dvc_url}"
            url = url + ":" + c_hash
            if c_hash and c_hash.strip():
                existing_artifact.extend(self.store.get_artifacts_by_uri(c_hash))

            if existing_artifact and len(existing_artifact) != 0:
                existing_artifact = existing_artifact[0]
                uri = c_hash
                artifact = link_execution_to_artifact(
                    store=self.store,
                    execution_id=self.execution.id,
                    uri=uri,
                    input_name=url,
                    event_type=mlpb.Event.Type.INPUT,
                )
            else:
                uri = c_hash if c_hash and c_hash.strip() else str(uuid.uuid1())
                artifact = create_new_artifact_event_and_attribution(
                    store=self.store,
                    execution_id=self.execution.id,
                    context_id=self.child_context.id,
                    uri=uri,
                    name=url,
                    type_name="Environment",
                    event_type=mlpb.Event.Type.INPUT,
                    properties={
                        "git_repo": str(git_repo),
                        # passing c_hash value to commit
                        "Commit": str(commit),
                        "url": str(dvc_url_with_pipeline),
                    },
                    artifact_type_properties={
                        "git_repo": mlpb.STRING,
                        "Commit": mlpb.STRING,
                        "url": mlpb.STRING,
                    },
                    milliseconds_since_epoch=int(time.time() * 1000),
                )
            custom_props = {}
            custom_props["git_repo"] = git_repo
            custom_props["Commit"] = commit
            self.execution_label_props["git_repo"] = git_repo
            self.execution_label_props["Commit"] = commit

            if self.graph:
                self.driver.create_env_node(
                    name,
                    url,
                    uri,
                    "input",
                    self.execution.id,
                    self.parent_context,
                    custom_props,
                )
                self.input_artifacts.append(
                    {
                        "Name": name,
                        "Path": url,
                        "URI": uri,
                        "Event": "input",
                        "Execution_Name": self.execution_name,
                        "Type": "Environment",
                        "Execution_Command": self.execution_command,
                        "Pipeline_Id": self.parent_context.id,
                        "Pipeline_Name": self.parent_context.name,
                    }
                )
                # commented this because input links from 'Env' node to executions 
                # are getting created without running this piece of code
                #self.driver.create_execution_links(uri, name, "Environment")
            return artifact


    def log_dvc_lock(self, file_path: str):
        """Used to update the dvc lock file created with dvc run command."""
        print("Entered dvc lock file commit")
        if self.execution is None:
            raise ValueError("Execution is not initialized. Please create an execution before calling this method.")
        return commit_dvc_lock_file(file_path, self.execution.id)


    def log_dataset(
        self,
        url: str,
        event: str,
        custom_properties: t.Optional[t.Dict] = None,
        label: t.Optional[str] = None,
        label_properties: t.Optional[t.Dict] = None,
        external: bool = False,
    ) -> mlpb.Artifact: # type: ignore  # Artifact type not recognized by mypy, using ignore to bypass
        """Logs a dataset as artifact.
        This call adds the dataset to dvc. The dvc metadata file created (.dvc) will be added to git and committed. The
        version of the  dataset is automatically obtained from the versioning software(DVC) and tracked as a metadata.
        Example:
            ```python
            artifact: mlmd.proto.Artifact = cmf.log_dataset(
                url="/repo/data.xml",
                event="input",
                custom_properties={"source":"kaggle"},
                label=artifacts/labels.csv,
                label_properties={"user":"Ron"}
            )
            ```
        Args:
             url: The path to the dataset.
             event: Takes arguments `INPUT` OR `OUTPUT`.
             custom_properties: Dataset properties (key/value pairs).
             labels: Labels are usually .csv files containing information regarding the dataset.
             label_properties: Custom properties for a label.
        Returns:
            Artifact object from ML Metadata library associated with the new dataset artifact.
        """
        logging_dir = change_dir(self.cmf_init_path)
        # Assigning current file name as stage and execution name
        current_script = sys.argv[0]
        file_name = os.path.basename(current_script)
        assigned_name = os.path.splitext(file_name)[0]
        # create context if not already created
        if not self.child_context:
            self.create_context(pipeline_stage=assigned_name)
            assert self.child_context is not None, f"Failed to create context for {self.pipeline_name}!!"

        # create execution if not already created
        if not self.execution:
            self.create_execution(execution_type=assigned_name)
            assert self.execution is not None, f"Failed to create execution for {self.pipeline_name}!!"

        ### To Do : Technical Debt. 
        # If the dataset already exist , then we just link the existing dataset to the execution
        # We do not update the dataset properties . 
        # We need to append the new properties to the existing dataset properties
        custom_props = {} if custom_properties is None else custom_properties

        git_repo = git_get_repo()
        name = re.split("/", url)[-1]
        event_type = mlpb.Event.Type.OUTPUT
        existing_artifact = []
        if event.lower() == "input":
            event_type = mlpb.Event.Type.INPUT

        commit_output(url, self.execution.id)
        c_hash = dvc_get_hash(url)

        if c_hash == "":
            print("Error in getting the dvc hash,return without logging")
            return

        dataset_commit = c_hash
        dvc_url = dvc_get_url(url)
        dvc_url_with_pipeline = f"{self.parent_context.name}:{dvc_url}"
        url = url + ":" + c_hash
        if c_hash and c_hash.strip:
            existing_artifact.extend(self.store.get_artifacts_by_uri(c_hash))

        uri = c_hash
        label_hash = 0
        if label:
            if not os.path.isfile(label):
                print(f"Error: File '{label}' not found.")
            else:
                label_hash = calculate_md5(label)
                label_custom_props = {} if label_properties is None else label_properties
                self.log_label(label, label_hash, uri, label_custom_props)
                # update custom_props
                label_with_hash = label + ":" + label_hash
                custom_props["labels"] = label
                custom_props["labels_uri"] = label_with_hash

        # To Do - What happens when uri is the same but names are different
        if existing_artifact and len(existing_artifact) != 0:
            existing_artifact = existing_artifact[0]

            # Quick fix- Updating only the name
            if custom_props is not None:
                self.update_existing_artifact(
                    existing_artifact, custom_props)

            uri = c_hash
            # update url for existing artifact
            self.update_dataset_url(existing_artifact, dvc_url_with_pipeline)
            artifact = link_execution_to_artifact(
                store=self.store,
                execution_id=self.execution.id,
                uri=uri,
                input_name=url,
                event_type=event_type,
            )
        else:
            # if((existing_artifact and len(existing_artifact )!= 0) and c_hash != ""):
            #   url = url + ":" + str(self.execution.id)
            uri = c_hash if c_hash and c_hash.strip() else str(uuid.uuid1())
            artifact = create_new_artifact_event_and_attribution(
                store=self.store,
                execution_id=self.execution.id,
                context_id=self.child_context.id,
                uri=uri,
                name=url,
                type_name="Dataset",
                event_type=event_type,
                properties={
                    "git_repo": str(git_repo),
                    # passing c_hash value to commit
                    "Commit": str(dataset_commit),
                    "url": str(dvc_url_with_pipeline),
                },
                artifact_type_properties={
                    "git_repo": mlpb.STRING,
                    "Commit": mlpb.STRING,
                    "url": mlpb.STRING,
                },
                custom_properties=custom_props,

                milliseconds_since_epoch=int(time.time() * 1000),
            )
        custom_props["git_repo"] = git_repo
        custom_props["Commit"] = dataset_commit
        self.execution_label_props["git_repo"] = git_repo
        self.execution_label_props["Commit"] = dataset_commit

        if self.graph:
            self.driver.create_dataset_node(
                name,
                url,
                uri,
                event,
                self.execution.id,
                self.parent_context,
                custom_props,
            )
            if event.lower() == "input":
                self.input_artifacts.append(
                    {
                        "Name": name,
                        "Path": url,
                        "URI": uri,
                        "Event": event.lower(),
                        "Execution_Name": self.execution_name,
                        "Type": "Dataset",
                        "Execution_Command": self.execution_command,
                        "Pipeline_Id": self.parent_context.id,
                        "Pipeline_Name": self.parent_context.name,
                    }
                )
                self.driver.create_execution_links(uri, name, "Dataset")
            else:
                child_artifact = {
                    "Name": name,
                    "Path": url,
                    "URI": uri,
                    "Event": event.lower(),
                    "Execution_Name": self.execution_name,
                    "Type": "Dataset",
                    "Execution_Command": self.execution_command,
                    "Pipeline_Id": self.parent_context.id,
                    "Pipeline_Name": self.parent_context.name,
                }
                self.driver.create_artifact_relationships(
                    self.input_artifacts, child_artifact, self.execution_label_props
                )
        os.chdir(logging_dir)
        return artifact

    def update_dataset_url(self, artifact: mlpb.Artifact, updated_url: str):    # type: ignore  # Artifact type not recognized by mypy, using ignore to bypass
        """Update dataset url
           Updates url of given artifact.
           Example
               ```python
               artifact: mlmd.proto.Artifact = cmf.update_dataset_url(
                artifact="data.xml.gz"
                updated_url="/repo/data.xml",
               )
               ```
               Args:
                  artifact: Artifact for which url is to be updated
                  updated_url: The updated url path of the dataset.
               Returns:
                  Updates artifact in mlmd, does not returns anything.
        """
        for key, value in artifact.properties.items():
            if key == "url":
                old_url = value.string_value
                # If the old URL is empty or only contains spaces, assign the new URL directly.
                if not old_url.strip():
                    new_url = updated_url

                # If the updated URL is not already present, append it with a comma separator.
                elif updated_url not in old_url:
                    new_url = f"{old_url},{updated_url}"

                # If the updated URL is already present, keep the old URL unchanged.
                else:
                    new_url = old_url
                artifact.properties[key].string_value = new_url
        put_artifact(self.store, artifact)

    def update_model_url(self, dup_artifact: list, updated_url: str):
        """Updates the URL property of model artifacts.
           Example: 
               ```python
               dup_artifact = [...] # List of artifacts
               updated_url = "/new/url"
               updated_artifacts = cmf.update_model_url(dup_artifact, updated_url)
               ```
               Args:
                  dup_artifact: List of artifacts to update.
                  updated_url: New URL to add to the existing URLs.
               Returns:
                  List of updated artifacts.
        """
        for art in dup_artifact:
            dup_art = art
            for key, value in dup_art.properties.items():
                if key == "url":
                    old_url = value.string_value
                    # If the old URL is empty or only contains spaces, assign the new URL directly.
                    if not old_url.strip():
                        new_url = updated_url

                    # If the updated URL is not already present, append it with a comma separator.
                    elif updated_url not in old_url:
                        new_url = f"{old_url},{updated_url}"

                    # If the updated URL is already present, keep the old URL unchanged.
                    else:
                        new_url = old_url
                    dup_art.properties[key].string_value = new_url
            put_artifact(self.store, dup_art)
        return dup_artifact


    # Add the model to dvc do a git commit and store the commit id in MLMD
    def log_model(
        self,
        path: str,
        event: str,
        model_framework: str = "Default",
        model_type: str = "Default",
        model_name: str = "Default",
        custom_properties: t.Optional[t.Dict] = None,
    ) -> mlpb.Artifact: # type: ignore  # Artifact type not recognized by mypy, using ignore to bypass
        """Logs a model.
        The model is added to dvc and the metadata file (.dvc) gets committed to git.
        Example:
            ```python
            artifact: mlmd.proto.Artifact= cmf.log_model(
                path="path/to/model.pkl",
                event="output",
                model_framework="SKlearn",
                model_type="RandomForestClassifier",
                model_name="RandomForestClassifier:default"
            )
            ```
        Args:
            path: Path to the model file.
            event: Takes arguments `INPUT` OR `OUTPUT`.
            model_framework: Framework used to create the model.
            model_type: Type of model algorithm used.
            model_name: Name of the algorithm used.
            custom_properties: The model properties.
        Returns:
            Artifact object from ML Metadata library associated with the new model artifact.
        """

        logging_dir = change_dir(self.cmf_init_path)
        # Assigning current file name as stage and execution name
        current_script = sys.argv[0]
        file_name = os.path.basename(current_script)
        assigned_name = os.path.splitext(file_name)[0]
        # create context if not already created
        if not self.child_context:
            self.create_context(pipeline_stage=assigned_name)
            assert self.child_context is not None, f"Failed to create context for {self.pipeline_name}!!"

        # create execution if not already created
        if not self.execution:
            self.create_execution(execution_type=assigned_name)
            assert self.execution is not None, f"Failed to create execution for {self.pipeline_name}!!"


        # To Do : Technical Debt. 
        # If the model already exist , then we just link the existing model to the execution
        # We do not update the model properties . 
        # We need to append the new properties to the existing model properties
        if custom_properties is None:
            custom_properties = {}
        custom_props = {} if custom_properties is None else custom_properties
        # name = re.split('/', path)[-1]
        event_type = mlpb.Event.Type.OUTPUT
        existing_artifact = []
        if event.lower() == "input":
            event_type = mlpb.Event.Type.INPUT

        commit_output(path, self.execution.id)
        c_hash = dvc_get_hash(path)

        if c_hash == "":
            print("Error in getting the dvc hash,return without logging")
            return

        model_commit = c_hash

        # If connecting to an existing artifact - The name of the artifact is
        # used as path/steps/key
        model_uri = path + ":" + c_hash
        dvc_url = dvc_get_url(path, False)
        url = dvc_url
        url_with_pipeline = f"{self.parent_context.name}:{url}"
        uri = ""
        if c_hash and c_hash.strip():
            uri = c_hash.strip()
            existing_artifact.extend(self.store.get_artifacts_by_uri(uri))
        else:
            raise RuntimeError("Model commit failed, Model uri empty")

        if (existing_artifact and len(existing_artifact) != 0):
            # update url for existing artifact
            existing_artifact = self.update_model_url(
                existing_artifact, url_with_pipeline
            )
            artifact = link_execution_to_artifact(
                store=self.store,
                execution_id=self.execution.id,
                uri=c_hash,
                input_name=model_uri,
                event_type=event_type,
            )
            model_uri =  model_uri + ":" + str(self.execution.id)
        else:
            uri = c_hash if c_hash and c_hash.strip() else str(uuid.uuid1())
            model_uri = model_uri + ":" + str(self.execution.id)
            artifact = create_new_artifact_event_and_attribution(
                store=self.store,
                execution_id=self.execution.id,
                context_id=self.child_context.id,
                uri=uri,
                name=model_uri,
                type_name="Model",
                event_type=event_type,
                properties={
                    "model_framework": str(model_framework),
                    "model_type": str(model_type),
                    "model_name": str(model_name),
                    # passing c_hash value to commit
                    "Commit": str(model_commit),
                    "url": str(url_with_pipeline),
                },
                artifact_type_properties={
                    "model_framework": mlpb.STRING,
                    "model_type": mlpb.STRING,
                    "model_name": mlpb.STRING,
                    "Commit": mlpb.STRING,
                    "url": mlpb.STRING,
                },
                custom_properties=custom_props,
                milliseconds_since_epoch=int(time.time() * 1000),
            )
        custom_props["Commit"] = model_commit
        self.execution_label_props["Commit"] = model_commit
        #To DO model nodes should be similar to dataset nodes when we create neo4j
        if self.graph:
            self.driver.create_model_node(
                model_uri,
                uri,
                event,
                self.execution.id,
                self.parent_context,
                custom_props,
            )
            if event.lower() == "input":
                self.input_artifacts.append(
                    {
                        "Name": model_uri,
                        "URI": uri,
                        "Event": event.lower(),
                        "Execution_Name": self.execution_name,
                        "Type": "Model",
                        "Execution_Command": self.execution_command,
                        "Pipeline_Id": self.parent_context.id,
                        "Pipeline_Name": self.parent_context.name,
                    }
                )
                self.driver.create_execution_links(uri, model_uri, "Model")
            else:
                child_artifact = {
                    "Name": model_uri,
                    "URI": uri,
                    "Event": event.lower(),
                    "Execution_Name": self.execution_name,
                    "Type": "Model",
                    "Execution_Command": self.execution_command,
                    "Pipeline_Id": self.parent_context.id,
                    "Pipeline_Name": self.parent_context.name,
                }

                self.driver.create_artifact_relationships(
                    self.input_artifacts, child_artifact, self.execution_label_props
                )
        os.chdir(logging_dir)
        return artifact


    def log_execution_metrics(
        self, metrics_name: str, custom_properties: t.Optional[t.Dict] = None
    ) -> mlpb.Artifact: # type: ignore  # Artifact type not recognized by mypy, using ignore to bypass
        """Log the metadata associated with the execution (coarse-grained tracking).
        It is stored as a metrics artifact. This does not have a backing physical file, unlike other artifacts that we
        have.
        Example:
            ```python
            exec_metrics: mlpb.Artifact = cmf.log_execution_metrics(
                metrics_name="Training_Metrics",
                {"auc": auc, "loss": loss}
            )
            ```
        Args:
            metrics_name: Name to identify the metrics.
            custom_properties: Dictionary with metric values.
        Returns:
              Artifact object from ML Metadata library associated with the new coarse-grained metrics artifact.
        """
        logging_dir = change_dir(self.cmf_init_path)
        # Assigning current file name as stage and execution name
        current_script = sys.argv[0]
        file_name = os.path.basename(current_script)
        assigned_name = os.path.splitext(file_name)[0]
        # create context if not already created
        if not self.child_context:
            self.create_context(pipeline_stage=assigned_name)
            assert self.child_context is not None, f"Failed to create context for {self.pipeline_name}!!"

        # create execution if not already created
        if not self.execution:
            self.create_execution(execution_type=assigned_name)
            assert self.execution is not None, f"Failed to create execution for {self.pipeline_name}!!"

        custom_props = {} if custom_properties is None else custom_properties
        uri = str(uuid.uuid1())
        metrics_name = metrics_name + ":" + uri + ":" + str(self.execution.id)
        metrics = create_new_artifact_event_and_attribution(
            store=self.store,
            execution_id=self.execution.id,
            context_id=self.child_context.id,
            uri=uri,
            name=metrics_name,
            type_name="Metrics",
            event_type=mlpb.Event.Type.OUTPUT,
            properties={"metrics_name": metrics_name},
            artifact_type_properties={"metrics_name": mlpb.STRING},
            custom_properties=custom_props,
            milliseconds_since_epoch=int(time.time() * 1000),
        )
        if self.graph:
            # To do create execution_links
            self.driver.create_metrics_node(
                metrics_name,
                uri,
                "output",
                self.execution.id,
                self.parent_context,
                custom_props,
            )
            child_artifact = {
                "Name": metrics_name,
                "URI": uri,
                "Event": "output",
                "Execution_Name": self.execution_name,
                "Type": "Metrics",
                "Execution_Command": self.execution_command,
                "Pipeline_Id": self.parent_context.id,
                "Pipeline_Name": self.parent_context.name,
            }
            self.driver.create_artifact_relationships(
                self.input_artifacts, child_artifact, self.execution_label_props
            )
        os.chdir(logging_dir)
        return metrics

    def log_metric(
        self, metrics_name: str, custom_properties: t.Optional[t.Dict] = None
    ) -> None:
        """Stores the fine-grained (per step or per epoch) metrics to memory.
        The metrics provided are stored in a parquet file. The `commit_metrics` call add the parquet file in the version
        control framework. The metrics written in the parquet file can be retrieved using the `read_metrics` call.
        Example:
            ```python
            # Can be called at every epoch or every step in the training. This is logged to a parquet file and committed
            # at the commit stage.
            # Inside training loop
            while True:
                 cmf.log_metric("training_metrics", {"train_loss": train_loss})
            cmf.commit_metrics("training_metrics")
            ```
        Args:
            metrics_name: Name to identify the metrics.
            custom_properties: Dictionary with metrics.
        """
        custom_props = {} if custom_properties is None else custom_properties
        if metrics_name in self.metrics:
            key = max((self.metrics[metrics_name]).keys()) + 1
            self.metrics[metrics_name][key] = custom_props
        else:
            self.metrics[metrics_name] = {}
            self.metrics[metrics_name][1] = custom_props

    def commit_metrics(self, metrics_name: str):
        """ Writes the in-memory metrics to a Parquet file, commits the metrics file associated with the metrics id to DVC and Git,
        and stores the artifact in MLMD.

        Example:
        ```python
        artifact: mlpb.Artifact = cmf.commit_metrics("example_metrics")
        ```

        Args:
           metrics_name: Name of the metrics.

        Returns:
           Artifact object from the ML Protocol Buffers library associated with the new metrics artifact.
        """

        logging_dir = change_dir(self.cmf_init_path)
        # code for nano cmf
        # Assigning current file name as stage and execution name
        current_script = sys.argv[0]
        file_name = os.path.basename(current_script)
        assigned_name = os.path.splitext(file_name)[0]
        # create context if not already created
        if not self.child_context:
            self.create_context(pipeline_stage=assigned_name)
            assert self.child_context is not None, f"Failed to create context for {self.pipeline_name}!!"

        # create execution if not already created
        if not self.execution:
            self.create_execution(execution_type=assigned_name)
            assert self.execution is not None, f"Failed to create execution for {self.pipeline_name}!!"

        
        directory_path = os.path.join(self.ARTIFACTS_PATH, self.execution.properties["Execution_uuid"].string_value.split(',')[0], self.METRICS_PATH)
        os.makedirs(directory_path, exist_ok=True)
        metrics_df = pd.DataFrame.from_dict(
            self.metrics[metrics_name], orient="index")
        metrics_df.index.names = ["SequenceNumber"]
        metrics_path = os.path.join(directory_path,metrics_name)
        metrics_df.to_parquet(metrics_path)
        commit_output(metrics_path, self.execution.id)
        uri = dvc_get_hash(metrics_path)

        if uri == "":
            print("Error in getting the dvc hash,return without logging")
            return
        metrics_commit = uri
        dvc_url = dvc_get_url(metrics_path)
        dvc_url_with_pipeline = f"{self.parent_context.name}:{dvc_url}"
        name = (
            metrics_path
            + ":"
            + uri
            + ":"
            + str(self.execution.id)
            + ":"
            + str(uuid.uuid1())
        )
        # not needed as property 'name' is part of artifact 
        # to maintain uniformity - Commit goes propeties of the artifact
        # custom_props = {"Name": metrics_name, "Commit": metrics_commit}
        custom_props = {}
        metrics = create_new_artifact_event_and_attribution(
            store=self.store,
            execution_id=self.execution.id,
            context_id=self.child_context.id,
            uri=uri,
            name=name,
            type_name="Step_Metrics",
            event_type=mlpb.Event.Type.OUTPUT,
            properties={
                # passing uri value to commit
                "Commit": metrics_commit,
                "url": str(dvc_url_with_pipeline),
            },
            artifact_type_properties={
                "Commit": mlpb.STRING,
                "url": mlpb.STRING,
            },
            custom_properties=custom_props,
            milliseconds_since_epoch=int(time.time() * 1000),
        )

        custom_props["Commit"] = metrics_commit
        self.execution_label_props["Commit"] = metrics_commit

        if self.graph:
            self.driver.create_step_metrics_node(
                name,
                uri,
                "output",
                self.execution.id,
                self.parent_context,
                custom_props,
            )
            child_artifact = {
                "Name": name,
                "URI": uri,
                "Event": "output",
                "Execution_Name": self.execution_name,
                "Type": "Step_Metrics",
                "Execution_Command": self.execution_command,
                "Pipeline_Id": self.parent_context.id,
            }
            self.driver.create_artifact_relationships(
                self.input_artifacts, child_artifact, self.execution_label_props
            )

        os.chdir(logging_dir)
        return metrics


    def log_validation_output(
        self, version: str, custom_properties: t.Optional[t.Dict] = None
    ) -> object: 
        uri = str(uuid.uuid1())
        if self.execution is None:
            raise ValueError("Execution is not initialized. Please create an execution before calling this method.")
        return create_new_artifact_event_and_attribution(
            store=self.store,
            execution_id=self.execution.id,
            context_id=self.child_context.id,
            uri=uri,
            name=uri,
            type_name="Validation_output",
            event_type=mlpb.Event.Type.INTERNAL_OUTPUT,
            properties={"version": version},
            artifact_type_properties={"version": mlpb.STRING},
            custom_properties=custom_properties,
            milliseconds_since_epoch=int(time.time() * 1000),
        )


    def update_existing_artifact(
        self, artifact: mlpb.Artifact, custom_properties: t.Dict    # type: ignore  # Artifact type not recognized by mypy, using ignore to bypass
    ):
        """ Updates an existing artifact with the provided custom properties and stores it back to MLMD. 
          Example: 
          ```python
                update_artifact=cmf.update_existing_artifact(existing_artifact, {"key1": "updated_value"}) 
          ``` 
          Args: 
             artifact: Existing artifact to be updated. 
             custom_properties: Dictionary containing custom properties to update. 
          Returns: 
             None 
       """
        for key, value in custom_properties.items():
            if isinstance(value, int):
                artifact.custom_properties[key].int_value = value
            else:
                 if key == "labels" or key == "labels_uri":
                     existing_value = artifact.custom_properties[key].string_value
                     if existing_value:
                         temp = existing_value + "," + str(value)
                         new_temp = set(temp.split(","))
                         # join the temp 
                         new_new_temp = ",".join(list(new_temp))
                         artifact.custom_properties[key].string_value = str(new_new_temp)
                     else: 
                        artifact.custom_properties[key].string_value = str(value)
                 else:
                     artifact.custom_properties[key].string_value = str(value)
        put_artifact(self.store, artifact)


    def get_artifact(self, artifact_id: int) -> mlpb.Artifact:  # type: ignore  # Artifact type not recognized by mypy, using ignore to bypass
        """Gets the artifact object from mlmd"""
        return get_artifacts_by_id(self.store, [artifact_id])[0]

    # To Do - The interface should be simplified.
    # To Do - Links should be created in mlmd also.
    # Todo - assumes source as Dataset and target as slice - should be generic and accomodate any types
    def link_artifacts(
        self, artifact_source: mlpb.Artifact, artifact_target: mlpb.Artifact    # type: ignore  # Artifact type not recognized by mypy, using ignore to bypass
    ):
        self.driver.create_links(artifact_source.name,
                                 artifact_target.name, "derived")

    def update_model_output(self, artifact: mlpb.Artifact): # type: ignore  # Artifact type not recognized by mypy, using ignore to bypass
        """updates an artifact"""
        put_artifact(self.store, artifact)

    def create_dataslice(self, name: str) -> "Cmf.DataSlice":
        """Creates a dataslice object.
        Once created, users can add data instances to this data slice with [add_data][cmflib.cmf.Cmf.DataSlice.add_data]
        method. Users are also responsible for committing data slices by calling the
        [commit][cmflib.cmf.Cmf.DataSlice.commit] method.
        Example:
            ```python
            dataslice = cmf.create_dataslice("slice-a")
            ```
        Args:
            name: Name to identify the dataslice.

        Returns:
            Instance of a newly created [DataSlice][cmflib.cmf.Cmf.DataSlice].
        """
        return Cmf.DataSlice(name, self)

    def read_dataslice(self, name: str) -> pd.DataFrame:
        """Reads the dataslice"""
        # To do checkout if not there
        if self.execution is None:
            raise ValueError("Execution is not initialized. Please create an execution before calling this method.")
        directory_path = os.path.join(self.ARTIFACTS_PATH, self.execution.properties["Execution_uuid"].string_value.split(',')[0], self.DATASLICE_PATH)
        name = os.path.join(directory_path, name)
        df = pd.read_parquet(name)
        return df

    # To do - Once update the hash and the new version should be updated in
    # the mlmd
    def update_dataslice(self, name: str, record: str, custom_properties: t.Dict):
        """Updates a dataslice record in a Parquet file with the provided custom properties.
        Example:
        ```python
           dataslice=cmf.update_dataslice("dataslice_file.parquet", "record_id", 
           {"key1": "updated_value"})
        ```
        Args:
           name: Name of the Parquet file.
           record: Identifier of the dataslice record to be updated.
           custom_properties: Dictionary containing custom properties to update.

        Returns:
           None
        """
        if self.execution is None:
            raise ValueError("Execution is not initialized. Please create an execution before calling this method.")
        directory_path = os.path.join(self.ARTIFACTS_PATH, self.execution.properties["Execution_uuid"].string_value.split(',')[0], self.DATASLICE_PATH)
        name = os.path.join(directory_path, name)
        df = pd.read_parquet(name)
        temp_dict = df.to_dict("index")
        temp_dict[record].update(custom_properties)
        dataslice_df = pd.DataFrame.from_dict(temp_dict, orient="index")
        dataslice_df.index.names = ["Path"]
        dataslice_df.to_parquet(name)

    def log_label(self, url: str, label_hash:str, dataset_uri: str, custom_properties: t.Optional[t.Dict] = None) -> mlpb.Artifact:
        """
        Logs a label artifact associated with a dataset.

        This function checks whether a label artifact (identified by `label_hash`) already exists in the metadata store.
        - If the artifact exists, it links it to the current execution and optionally updates its properties and URL.
        - If the artifact does not exist, it creates a new artifact with the provided properties and links it to the execution context.

        Args:
            url (str): The base URL representing the label (e.g., path or storage location).
            label_hash (str): A unique mdh5 hash calculated on the label content.
            dataset_uri (str): The URI of the associated dataset.
            custom_properties (Optional[Dict], optional): Additional metadata to associate with the artifact. Defaults to None.

        Returns:
            mlpb.Artifact: The logged or linked label artifact.
        """
        
        ### To Do : Technical Debt. 
        # If the dataset already exist , then we just link the existing dataset to the execution
        # We do not update the dataset properties . 
        # We need to append the new properties to the existing dataset properties
        custom_props = {} if custom_properties is None else custom_properties
        git_repo = git_get_repo()

        existing_artifact = []
        if label_hash and label_hash.strip:
            existing_artifact.extend(self.store.get_artifacts_by_uri(label_hash))
        
        url = url + ":" + label_hash

        # To Do - What happens when uri is the same but names are different
        if existing_artifact and len(existing_artifact) != 0:
            existing_artifact = existing_artifact[0]

            # Quick fix- Updating only the name
            if custom_props is not None:
                self.update_existing_artifact(
                    existing_artifact, custom_props)
            uri = label_hash
            # update url for existing artifact
            self.update_dataset_url(existing_artifact, url)
            artifact = link_execution_to_artifact(
                store=self.store,
                execution_id=self.execution.id,
                uri=uri,
                input_name=url,
                event_type=mlpb.Event.Type.INPUT,
            )
        else:
            uri = label_hash if label_hash and label_hash.strip() else str(uuid.uuid1())
            artifact = create_new_artifact_event_and_attribution(
                store=self.store,
                execution_id=self.execution.id,
                context_id=self.child_context.id,
                uri=uri,
                name=url,
                type_name="Label",
                event_type=mlpb.Event.Type.INPUT,
                properties={
                    "git_repo": str(git_repo),
                    # passing hash_value value to commit
                    "Commit": str(label_hash),
                    "url": str(url),
                    "dataset_uri": str(dataset_uri),
                },
                artifact_type_properties={
                    "git_repo": mlpb.STRING,
                    "Commit": mlpb.STRING,
                    "url": mlpb.STRING,
                    "dataset_uri": mlpb.STRING,
                },
                custom_properties=custom_props,
                milliseconds_since_epoch=int(time.time() * 1000),
            )
        custom_props["git_repo"] = git_repo
        custom_props["Commit"] = label_hash
        custom_props["dataset_uri"] = dataset_uri
        return artifact

    class DataSlice:
        """A data slice represents a named subset of data.
        It can be used to track performance of an ML model on different slices of the training or testing dataset
        splits. This can be useful from different perspectives, for instance, to mitigate model bias.
        > Instances of data slices are not meant to be created manually by users. Instead, use
        [Cmf.create_dataslice][cmflib.cmf.Cmf.create_dataslice] method.
        """

        def __init__(self, name: str, writer):
            self.props:dict[str, dict[str, str]] = {}
            self.name = name
            self.writer = writer

        # Declare methods as class-level callables
        log_dataslice_from_client: t.Callable[..., t.Any]

        # def add_files(self, list_of_files:np.array ):
        #    for i in list_of_files:

        def add_data(
            self, path: str, custom_properties: t.Optional[t.Dict] = None
        ) -> None:
            """Add data to create the dataslice.
            Currently supported only for file abstractions. Pre-condition - the parent folder, containing the file
                should already be versioned.
            Example:
                ```python
                #dataslice.add_data(f"data/raw_data/{j}.xml)
                ```
            Args:
                path: Name to identify the file to be added to the dataslice.
                custom_properties: Properties associated with this datum.
            """

            self.props[path] = {}
            self.props[path]['hash'] = dvc_get_hash(path)
            parent_path = path.rsplit("/", 1)[0]
            self.data_parent = parent_path.rsplit("/", 1)[1]
            if custom_properties:
                for k, v in custom_properties.items():
                    self.props[path][k] = v

        #        """
        #        Place holder for updating back to mlmd

        #        def update_data(self, path, custom_props:{}):
        #            for k ,v in custom_props.items():
        #                self.props[path][k] = v
        #        """

        def commit(self, custom_properties: t.Optional[t.Dict] = None) -> None:
            """Commit the dataslice.
            The created dataslice is versioned and added to underneath data versioning software.
            Example:

                dataslice.commit()
                ```
            Args:
                custom_properties: Dictionary to store key value pairs associated with Dataslice
                Example{"mean":2.5, "median":2.6}
            """

            logging_dir = change_dir(self.writer.cmf_init_path)
            # code for nano cmf
            # Assigning current file name as stage and execution name
            current_script = sys.argv[0]
            file_name = os.path.basename(current_script)
            assigned_name = os.path.splitext(file_name)[0]
            # create context if not already created
            if not self.writer.child_context:
                self.writer.create_context(pipeline_stage=assigned_name)
                assert self.writer.child_context is not None, f"Failed to create context for {self.writer.pipeline_name}!!"

            # create execution if not already created
            if not self.writer.execution:
                self.writer.create_execution(execution_type=assigned_name)
                assert self.writer.execution is not None, f"Failed to create execution for {self.writer.pipeline_name}!!"

            directory_path = os.path.join(self.writer.ARTIFACTS_PATH, self.writer.execution.properties["Execution_uuid"].string_value.split(',')[0], self.writer.DATASLICE_PATH)
            os.makedirs(directory_path, exist_ok=True)
            custom_props = {} if custom_properties is None else custom_properties
            git_repo = git_get_repo()
            dataslice_df = pd.DataFrame.from_dict(self.props, orient="index")
            dataslice_df.index.names = ["Path"]
            dataslice_path = os.path.join(directory_path,self.name)
            dataslice_df.to_parquet(dataslice_path)
            existing_artifact = []

            commit_output(dataslice_path, self.writer.execution.id)
            c_hash = dvc_get_hash(dataslice_path)
            if c_hash == "":
                print("Error in getting the dvc hash,return without logging")
                return

            dataslice_commit = c_hash
            url = dvc_get_url(dataslice_path)
            dvc_url_with_pipeline = f"{self.writer.parent_context.name}:{url}"
            if c_hash and c_hash.strip():
                existing_artifact.extend(
                    self.writer.store.get_artifacts_by_uri(c_hash))
            if existing_artifact and len(existing_artifact) != 0:
                print("Adding to existing data slice")
                # Haven't added event type in this if cond, is it not needed??
                slice = link_execution_to_input_artifact(
                    store=self.writer.store,
                    execution_id=self.writer.execution.id,
                    uri=c_hash,
                    input_name=dataslice_path + ":" + c_hash,
                )
            else:
                slice = create_new_artifact_event_and_attribution(
                    store=self.writer.store,
                    execution_id=self.writer.execution.id,
                    context_id=self.writer.child_context.id,
                    uri=c_hash,
                    name=dataslice_path + ":" + c_hash,
                    type_name="Dataslice",
                    event_type=mlpb.Event.Type.OUTPUT,  # type: ignore  # Event type not recognized by mypy, using ignore to bypass
                    properties={
                        "git_repo": str(git_repo),
                        # passing c_hash value to commit
                        "Commit": str(dataslice_commit),
                        "url": str(dvc_url_with_pipeline),
                    },
                    artifact_type_properties={
                        "git_repo": mlpb.STRING,    # type: ignore  # String type not recognized by mypy, using ignore to bypass
                        "Commit": mlpb.STRING,  # type: ignore  # String type not recognized by mypy, using ignore to bypass
                        "url": mlpb.STRING, # type: ignore  # String type not recognized by mypy, using ignore to bypass
                    },
                    custom_properties=custom_props,
                    milliseconds_since_epoch=int(time.time() * 1000),
                )

            custom_props["git_repo"] = git_repo
            custom_props["Commit"] = dataslice_commit
            self.writer.execution_label_props["git_repo"] = git_repo
            self.writer.execution_label_props["Commit"] = dataslice_commit
            if self.writer.graph:
                self.writer.driver.create_dataslice_node(
                    self.name, dataslice_path + ":" + c_hash, c_hash, self.data_parent, custom_props
                )
            os.chdir(logging_dir)
            return slice


#        """Temporary code"""
#
#        def materialize(self, name):
#            slicedir = name + "-" + "dir"
#            os.mkdir(slicedir)
#            df = pd.read_parquet(name)
#            for index, row in df.iterrows():
#                print(index)
#                first, middle, last = str(index).split("/")
#                print(last)
#                os.symlink(str(index), slicedir + "/ " + last)

# Binding cmf_server.py methods to Cmf class
Cmf.merge_created_context = merge_created_context
Cmf.merge_created_execution = merge_created_execution
Cmf.log_python_env_from_client = log_python_env_from_client
Cmf.log_dataset_with_version = log_dataset_with_version
Cmf.log_model_with_version = log_model_with_version
Cmf.log_execution_metrics_from_client =  log_execution_metrics_from_client
Cmf.log_step_metrics_from_client = log_step_metrics_from_client
Cmf.DataSlice.log_dataslice_from_client = log_dataslice_from_client
Cmf.log_label_with_version = log_label_with_version

def metadata_push(pipeline_name: str, file_name = "./mlmd", tensorboard_path: str = "", execution_uuid: str = ""):
    """ Pushes metadata file to CMF-server.
    Example:
    ```python
         result = metadata_push("example_pipeline", "mlmd_file", "eg_execution_uuid", "tensorboard_log")
    ```
    Args:
        pipeline_name: Name of the pipeline.
        file_name: Specify input metadata file name.
        execution_uuid: Optional execution UUID.
        tensorboard_path: Path to tensorboard logs.

    Returns:
        Response output from the _metadata_push function.
    """
    # Required arguments: pipeline_name
    # Optional arguments: execution_UUID, file_name, tensorboard_path
    output = _metadata_push(pipeline_name, file_name, execution_uuid, tensorboard_path)
    return output


def metadata_pull(pipeline_name: str, file_name = "./mlmd", execution_uuid: str = ""):
    """ Pulls metadata file from CMF-server. 
     Example: 
     ```python 
          result = metadata_pull("example_pipeline", "./mlmd_directory", "eg_execution_uuid") 
     ``` 
     Args: 
        pipeline_name: Name of the pipeline. 
        file_name: Specify output metadata file name.
        execution_uuid: Optional execution UUID. 
     Returns: 
        Message from the _metadata_pull function. 
     """
    # Required arguments: pipeline_name 
    # Optional arguments: execution_UUID, file_name 
    output = _metadata_pull(pipeline_name, file_name, execution_uuid)
    return output


def metadata_export(pipeline_name: str, json_file_name: str = "", file_name = "./mlmd"):
    """ Export local mlmd's metadata in json format to a json file. 
     Example: 
     ```python 
          result = metadata_pull("example_pipeline", "./jsonfile", "./mlmd_directory") 
     ``` 
     Args: 
        pipeline_name: Name of the pipeline. 
        json_file_name: File path of json file. 
        file_name: Specify input metadata file name. 
     Returns: 
        Message from the _metadata_export function. 
     """
    # Required arguments: pipeline_name 
    # Optional arguments: json_file_name, file_name
    output = _metadata_export(pipeline_name, json_file_name, file_name)
    return output


def artifact_pull(pipeline_name: str, file_name = "./mlmd"):
    """ Pulls artifacts from the initialized repository.
    Example:
    ```python
         result = artifact_pull("example_pipeline", "./mlmd_directory")
    ```
    Args:
        pipeline_name: Name of the pipeline.
        file_name: Specify input metadata file name.
    Returns:
        Output from the _artifact_pull function.
    """
    # Required arguments: pipeline_name
    # Optional arguments: file_name
    output = _artifact_pull(pipeline_name, file_name)
    return output


def artifact_pull_single(pipeline_name: str, file_name: str, artifact_name: str):
    """ Pulls a single artifact from the initialized repository. 
    Example: 
    ```python 
        result = artifact_pull_single("example_pipeline", "./mlmd_directory", "example_artifact") 
    ```
    Args: 
       pipeline_name: Name of the pipeline. 
       file_name: Specify input metadata file name.
       artifact_name: Name of the artifact. 
    Returns:
       Output from the _artifact_pull_single function. 
    """
    # Required arguments: pipeline_name
    # Optional arguments: file_name, artifact_name
    output = _artifact_pull_single(pipeline_name, file_name, artifact_name)
    return output

# Prevent multiplying int with NoneType; added default value to jobs.
def artifact_push(pipeline_name: str, filepath = "./mlmd", jobs: int = 32):
    """ Pushes artifacts to the initialized repository.
    Example:
    ```python
         result = artifact_push("example_pipeline", "./mlmd_directory", 32)
    ```
    Args: 
       pipeline_name: Name of the pipeline. 
       filepath: Path to store the artifact. 
       jobs: Number of jobs to use for pushing artifacts.
    Returns:
        Output from the _artifact_push function.
    """
    output = _artifact_push(pipeline_name, filepath, jobs)
    return output


def cmf_init_show():
    """ Initializes and shows details of the CMF command. 
    Example: 
    ```python 
         result = cmf_init_show() 
    ``` 
    Returns: 
       Output from the _cmf_cmd_init function. 
    """
    output=_cmf_cmd_init()
    return output


def cmf_init(type: str = "",
        path: str = "",
        git_remote_url: str = "",
        cmf_server_url: str = "",
        neo4j_user: str = "",
        neo4j_password: str = "",
        neo4j_uri: str = "",
        url: str = "",
        endpoint_url: str = "",
        access_key_id: str = "",
        secret_key: str = "",
        session_token: str = "",
        user: str = "",
        password: str = "",
        port: int = 0,
        osdf_path: str = "",
        osdf_cache: str = "",
        key_id: str = "",
        key_path: str = "",
        key_issuer: str = "",
         ):

    """ Initializes the CMF configuration based on the provided parameters. 
    Example:
    ```python
       cmf_init( type="local", 
                 path="/path/to/re",
                 git_remote_url="git@github.com:user/repo.git",
                 cmf_server_url="http://cmf-server"
                 neo4j_user", 
                 neo4j_password="password",
                 neo4j_uri="bolt://localhost:76"
               )
    ```
    Args: 
       type: Type of repository ("local", "minioS3", "amazonS3", "sshremote", "osdfremote")
       path: Path for the local repository. 
       git_remote_url: Git remote URL for version control.
       cmf_server_url: CMF server URL.
       neo4j_user: Neo4j database username.
       neo4j_password: Neo4j database password.
       neo4j_uri: Neo4j database URI.
       url: URL for MinioS3 or AmazonS3.
       endpoint_url: Endpoint URL for MinioS3.
       access_key_id: Access key ID for MinioS3 or AmazonS3.
       secret_key: Secret key for MinioS3 or AmazonS3. 
       session_token: Session token for AmazonS3.
       user: SSH remote username.
       password: SSH remote password. 
       port: SSH remote port.
       osdf_path: OSDF Origin Path.
       osdf_cache: OSDF Cache Path (Optional).
       key_id: OSDF Key ID.
       key_path: OSDF Private Key Path.
       key_issuer: OSDF Key Issuer URL.
    Returns:
       Output based on the initialized repository type.
    """

    if type == "":
        return print("Error: Type is not provided")
    if type not in ["local","minioS3","amazonS3","sshremote","osdfremote"]:
        return print("Error: Type value is undefined"+ " "+type+".Expected: "+",".join(["local","minioS3","amazonS3","sshremote","osdfremote"]))

    if neo4j_user != "" and  neo4j_password != "" and neo4j_uri != "":
        pass
    elif neo4j_user == "" and  neo4j_password == "" and neo4j_uri == "":
        pass
    else:
        return print("Error: Enter all neo4j parameters.") 

    args={'path': path,
        'git_remote_url': git_remote_url,
        'url': url,
        'endpoint_url': endpoint_url,
        'access_key_id': access_key_id,
        'secret_key': secret_key,
        'session_token': session_token,
        'user': user,
        'password': password,
        'osdf_path': osdf_path,
        'osdf_cache': osdf_cache,
        'key_id': key_id,
        'key_path': key_path, 
        'key-issuer': key_issuer,
        }

    status_args=non_related_args(type, args)

    if type == "local" and path != "" and  git_remote_url != "" :
        """Initialize local repository"""
        output = _init_local(
            path, 
            git_remote_url, 
            cmf_server_url, 
            neo4j_user, 
            neo4j_password, 
            neo4j_uri
        )
        if status_args != []:
            print("There are non-related arguments: "+",".join(status_args)+".Please remove them.")
        return output
         
    elif type == "minioS3" and url != "" and endpoint_url != "" and access_key_id != "" and secret_key != "" and git_remote_url != "":
        """Initialize minioS3 repository"""
        output = _init_minioS3(
            url,
            endpoint_url,
            access_key_id,
            secret_key,
            git_remote_url,
            cmf_server_url,
            neo4j_user,
            neo4j_password,
            neo4j_uri,
        )
        if status_args != []:
            print("There are non-related arguments: "+",".join(status_args)+".Please remove them.")
        return output

    elif type == "amazonS3" and url != "" and access_key_id != "" and secret_key != "" and git_remote_url != "":
        """Initialize amazonS3 repository"""
        output = _init_amazonS3(
            url,
            access_key_id,
            secret_key,
            session_token,
            git_remote_url,
            cmf_server_url,
            neo4j_user,
            neo4j_password,
            neo4j_uri,
        )
        if status_args != []:
            print("There are non-related arguments: "+",".join(status_args)+".Please remove them.")

        return output

    elif type == "sshremote" and path != "" and user != "" and port != 0 and password != "" and git_remote_url != "":
        """Initialize sshremote repository"""
        output = _init_sshremote(
            path,
            user,
            port,
            password,
            git_remote_url,
            cmf_server_url,
            neo4j_user,
            neo4j_password,
            neo4j_uri,
        )
        if status_args != []:
            print("There are non-related arguments: "+",".join(status_args)+".Please remove them.")

        return output

    elif type == "osdfremote" and osdf_path != "" and key_id != "" and key_path != "" and key_issuer != "" and git_remote_url != "":
        """Initialize osdfremote repository"""
        output = _init_osdfremote(
            osdf_path,
            osdf_cache,
            key_id,
            key_path,
            key_issuer,
            git_remote_url,
            cmf_server_url,
            neo4j_user,
            neo4j_password,
            neo4j_uri,
        )
        if status_args != []:
            print("There are non-related arguments: "+",".join(status_args)+".Please remove them.")

        return output

    else:
        print("Error: Enter all arguments")


def non_related_args(type : str, args : dict):
    available_args=[i for i, j in args.items() if j != ""]
    local=["path", "git_remote_url"]
    minioS3=["url", "endpoint_url", "access_key_id", "secret_key", "git_remote_url"]
    amazonS3=["url", "access_key_id", "secret_key", "session_token", "git_remote_url"]
    sshremote=["path", "user", "port", "password", "git_remote_url"]
    osdfremote=["osdf_path", "osdf_cache", "key_id", "key_path", "key-issuer", "git_remote_url"]


    dict_repository_args={"local" : local, "minioS3" : minioS3, "amazonS3" : amazonS3, "sshremote" : sshremote, "osdfremote": osdfremote}
    
    for repo,arg in dict_repository_args.items():
        if repo ==type:
            non_related_args=list(set(available_args)-set(dict_repository_args[repo]))
    return non_related_args


def pipeline_list(file_name = "./mlmd"):
    """ Display a list of pipeline name(s) from the available input metadata file.

    Example:
    ```python
         result = _pipeline_list("./mlmd_directory")
    ```
    Args:
        file_name: Specify input metadata file name.
    Returns:
        Output from the _pipeline_list function.
    """
    # Optional arguments: file_name( path to store the MLMD file)
    output = _pipeline_list(file_name)
    return output


def execution_list(pipeline_name: str, file_name = "./mlmd", execution_uuid: str = ""):
    """Displays executions from the input metadata file with a few properties in a 7-column table, limited to 20 records per page.
    Example: 
    ```python 
        result = _execution_list("example_pipeline", "./mlmd_directory", "example_execution_uuid") 
    ```
    Args: 
       pipeline_name: Name of the pipeline. 
       file_name: Specify input metadata file name.
       execution_uuid: Specify the execution uuid to retrieve execution.
    Returns:
       Output from the _execution_list function. 
    """
    # Required arguments: pipeline_name
    # Optional arguments: file_name, execution_uuid
    output = _execution_list(pipeline_name, file_name, execution_uuid)
    return output


def artifact_list(pipeline_name: str, file_name = "./mlmd", artifact_name: str = ""):
    """ Displays artifacts from the input metadata file with a few properties in a 7-column table, limited to 20 records per page.
    Example: 
    ```python 
        result = _artifact_list("example_pipeline", "./mlmd_directory", "example_artifact_name") 
    ```
    Args: 
       pipeline_name: Name of the pipeline. 
       file_name: Specify input metadata file name. 
       artifact_name: Artifacts for particular artifact name.
    Returns:
       Output from the _artifact_list function. 
    """
    # Required arguments: pipeline_name
    # Optional arguments: file_name, artifact_name
    output = _artifact_list(pipeline_name, file_name, artifact_name)
    return output

# Prevent multiplying int with NoneType; added default value to jobs.
def repo_push(pipeline_name: str, filepath = "./mlmd", tensorboard_path: str = "", execution_uuid: str = "", jobs: int = 32):
    """ Push artifacts, metadata files, and source code to the user's artifact repository, cmf-server, and git respectively.
    Example: 
    ```python 
        result = _repo_push("example_pipeline", "./mlmd_directory", "example_execution_uuid", "./tensorboard_path", 32) 
    ```
    Args: 
       pipeline_name: Name of the pipeline. 
       file_name: Specify input metadata file name.
       execution_uuid: Specify execution uuid.
       tensorboard_path: Path to tensorboard logs.
       jobs: Number of jobs to use for pushing artifacts.
    Returns:
       Output from the _repo_push function. 
    """
    # Required arguments: pipeline_name
    # Optional arguments: filepath, execution_uuid, tensorboard_path, jobs
    output = _repo_push(pipeline_name, filepath, tensorboard_path, execution_uuid, jobs)
    return output


def repo_pull(pipeline_name: str, file_name = "./mlmd", execution_uuid: str = ""):
    """ Pull artifacts, metadata files, and source code from the user's artifact repository, cmf-server, and git respectively.
    Example: 
    ```python 
        result = _repo_pull("example_pipeline", "./mlmd_directory", "example_execution_uuid") 
    ```
    Args: 
       pipeline_name: Name of the pipeline. 
       file_name: Specify output metadata file name.
       execution_uuid: Specify execution uuid.
    Returns:
       Output from the _repo_pull function. 
    """
    # Required arguments: pipeline_name
    # Optional arguments: file_name, execution_uuid
    output = _repo_pull(pipeline_name, file_name, execution_uuid)
    return output


def dvc_ingest(file_name = "./mlmd"):
    """ Ingests metadata from the dvc.lock file into the CMF. 
        If an existing MLMD file is provided, it merges and updates execution metadata 
        based on matching commands, or creates new executions if none exist.
    Example: 
    ```python 
        result = _dvc_ingest("./mlmd_directory") 
    ```
    Args: 
       file_name: Specify input metadata file name.
    Returns:
       Output from the _dvc_ingest function. 
    """
    # Optional argument: file_name
    output = _dvc_ingest(file_name)
    return output