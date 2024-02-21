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
import pandas as pd
import typing as t

# This import is needed for jupyterlab environment
import dvc
from ml_metadata.proto import metadata_store_pb2 as mlpb
from ml_metadata.metadata_store import metadata_store
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
from cmflib.metadata_helper import (
    get_or_create_parent_context,
    get_or_create_run_context,
    associate_child_to_parent_context,
    create_new_execution_in_existing_run_context,
    link_execution_to_artifact,
    create_new_artifact_event_and_attribution,
    get_artifacts_by_id,
    put_artifact,
    link_execution_to_input_artifact,
)
from cmflib.utils.cmf_config import CmfConfig
from cmflib.cmf_commands_wrapper import (
    _metadata_push,
    _metadata_pull,
    _artifact_pull,
    _artifact_push,
    _artifact_pull_single,
    _cmf_cmd_init,
    _init_local,
    _init_minioS3,
    _init_amazonS3,
    _init_sshremote

)

class Cmf:
    """This class provides methods to log metadata for distributed AI pipelines.
    The class instance creates an ML metadata store to store the metadata.
    It creates a driver to store nodes and its relationships to neo4j.
    The user has to provide the name of the pipeline, that needs to be recorded with CMF.
    ```python
    cmflib.cmf.Cmf(
        filename="mlmd",
        pipeline_name="test_pipeline",
        custom_properties={"owner": "user_a"},
        graph=False
    )
    ```
    Args:
        filename: Path  to the sqlite file to store the metadata
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
    # Reading CONFIG_FILE variable
    cmf_config = os.environ.get("CONFIG_FILE", ".cmfconfig")
    if os.path.exists(cmf_config):
        attr_dict = CmfConfig.read_config(cmf_config)
        __neo4j_uri = attr_dict.get("neo4j-uri", "")
        __neo4j_password = attr_dict.get("neo4j-password", "")
        __neo4j_user = attr_dict.get("neo4j-user", "")

    def __init__(
        self,
        filename: str = "mlmd",
        pipeline_name: str = "",
        custom_properties: t.Optional[t.Dict] = None,
        graph: bool = False,
        is_server: bool = False,
    ):
        if is_server is False:
            Cmf.__prechecks()
        if custom_properties is None:
            custom_properties = {}
        config = mlpb.ConnectionConfig()
        config.sqlite.filename_uri = filename
        self.store = metadata_store.MetadataStore(config)
        self.filename = filename
        self.child_context = None
        self.execution = None
        self.execution_name = ""
        self.execution_command = ""
        self.metrics = {}
        self.input_artifacts = []
        self.execution_label_props = {}
        self.graph = graph
        self.branch_name = filename.rsplit("/", 1)[-1]

        if is_server is False:
            git_checkout_new_branch(self.branch_name)
        self.parent_context = get_or_create_parent_context(
            store=self.store,
            pipeline=pipeline_name,
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
                pipeline_name, self.parent_context.id, custom_properties
            )

    @staticmethod
    def __load_neo4j_params():
         cmf_config = os.environ.get("CONFIG_FILE", ".cmfconfig")
         if os.path.exists(cmf_config):
             attr_dict = CmfConfig.read_config(cmf_config)
             Cmf.__neo4j_uri = attr_dict.get("neo4j-uri", "")
             Cmf.__neo4j_password = attr_dict.get("neo4j-password", "")
             Cmf.__neo4j_user = attr_dict.get("neo4j-user", "")


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
    ) -> mlpb.Context:
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
            cmf = Cmf(filename="mlmd", pipeline_name="test_pipeline")
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

    def merge_created_context(
        self, pipeline_stage: str, custom_properties: t.Optional[t.Dict] = None
    ) -> mlpb.Context:
        """Merge created context.
        Every call creates a unique pipeline stage.
        Created for metadata push purpose.
        Example:

            ```python
            #Create context
            # Import CMF
            from cmflib.cmf import Cmf
            from ml_metadata.proto import metadata_store_pb2 as mlpb
            # Create CMF logger
            cmf = Cmf(filename="mlmd", pipeline_name="test_pipeline")
            # Create context
            context: mlmd.proto.Context = cmf.merge_created_context(
                pipeline_stage="Test-env/prepare",
                custom_properties ={"user-metadata1": "metadata_value"}
            ```
            Args:
                Pipeline_stage: Pipeline_Name/Stage_name.
                custom_properties: Developers can provide key value pairs with additional properties of the execution that
                    need to be stored.
            Returns:
                Context object from ML Metadata library associated with the new context for this stage.
        """

        custom_props = {} if custom_properties is None else custom_properties
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

    def create_execution(
        self,
        execution_type: str,
        custom_properties: t.Optional[t.Dict] = None,
        cmd: str = None,
        create_new_execution: bool = True,
    ) -> mlpb.Execution:
        """Create execution.
        Every call creates a unique execution. Execution can only be created within a context, so
        [create_context][cmflib.cmf.Cmf.create_context] must be called first.
        Example:
            ```python
            # Import CMF
            from cmflib.cmf import Cmf
            from ml_metadata.proto import metadata_store_pb2 as mlpb
            # Create CMF logger
            cmf = Cmf(filename="mlmd", pipeline_name="test_pipeline")
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
        self.execution_label_props["execution_command"] = str(sys.argv)
        if self.graph:
            self.driver.create_execution_node(
                self.execution_name,
                self.child_context.id,
                self.parent_context,
                str(sys.argv),
                self.execution.id,
                custom_props,
            )
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
            cmf = Cmf(filename="mlmd", pipeline_name="test_pipeline")
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
        execution_type = self.store.get_execution_types_by_id([self.execution.type_id])[
            0
        ]

        if custom_properties:
            for key, value in custom_properties.items():
                if isinstance(value, int):
                    self.execution.custom_properties[key].int_value = value
                else:
                    self.execution.custom_properties[key].string_value = str(
                        value)
        self.store.put_executions([self.execution])
        c_props = {}
        for k, v in self.execution.custom_properties.items():
            key = re.sub("-", "_", k)
            val_type = str(v).split(":", maxsplit=1)[0]
            if val_type == "string_value":
                val = self.execution.custom_properties[k].string_value
            else:
                val = str(v).split(":")[1]
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

    def merge_created_execution(
        self,
        execution_type: str,
        execution_cmd: str,
        properties: t.Optional[t.Dict] = None,
        custom_properties: t.Optional[t.Dict] = None,
        orig_execution_name:str = "",
        create_new_execution:bool = True
    ) -> mlpb.Execution:
        """Merge Created execution.
        Every call creates a unique execution. Execution can only be created within a context, so
        [create_context][cmflib.cmf.Cmf.create_context] must be called first.
        Every call occurs when metadata push or pull is processed. Data from pre-existing executions is used
        to create new executions with additional data(Required on cmf-server).
        Example:
            ```python
            # Import CMF
            from cmflib.cmf import Cmf
            from ml_metadata.proto import metadata_store_pb2 as mlpb
            # Create CMF logger
            cmf = Cmf(filename="mlmd", pipeline_name="test_pipeline")
            # Create or reuse context for this stage
            context: mlmd.proto.Context = cmf.merge_created_context(
                pipeline_stage="prepare",
                custom_properties ={"user-metadata1": "metadata_value"}
            )
            # Create a new execution for this stage run
            execution: mlmd.proto.Execution = cmf.merge_created_execution(
                execution_type="Prepare",
                properties={"Context_Type":""},
                custom_properties = {"split": split, "seed": seed},
                orig_execution_name=execution_name
            )
            ```
        Args:
            execution_type: Type of the execution.(when create_new_execution is False, this is the name of execution)
            properties: Properties of Execution.
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
            Execution object from ML Metadata library associated with the execution for this stage.
        """
        # Initializing the execution related fields
        properties = {} if properties is None else properties
        self.metrics = {}
        self.input_artifacts = []
        self.execution_label_props = {}
        custom_props = {} if custom_properties is None else custom_properties
        # print(custom_props)
        git_repo = properties.get("Git_Repo", "")
        git_start_commit = properties.get("Git_Start_Commit", "")
        #name = properties.get("Name", "")
        create_new_execution = True
        execution_name = execution_type
        #exe.name property is passed as the orig_execution_name.
        #if name is not an empty string then we are re-using executions
        if orig_execution_name != "":
            create_new_execution = False
            execution_name = orig_execution_name

        self.execution = create_new_execution_in_existing_run_context(
            store=self.store,
            execution_type_name=execution_type, # Type field when re-using executions
            execution_name=execution_name, #Name field if we are re-using executionsname
                                           #Type field , if creating new executions always
            context_id=self.child_context.id,
            execution=execution_cmd,
            pipeline_id=self.parent_context.id,
            pipeline_type=self.parent_context.name,
            git_repo=git_repo,
            git_start_commit=git_start_commit,
            custom_properties=custom_props,
            create_new_execution=create_new_execution
        )

        uuids = ""

        uuids = self.execution.properties["Execution_uuid"].string_value
        if uuids:
            self.execution.properties["Execution_uuid"].string_value = uuids +\
                ","+properties["Execution_uuid"]
        else:
            self.execution.properties["Execution_uuid"].string_value =\
                properties["Execution_uuid"]

        
        self.store.put_executions([self.execution])
        self.execution_name = str(self.execution.id) + "," + execution_type
        self.execution_command = execution_cmd
        for k, v in custom_props.items():
            k = re.sub("-", "_", k)
            self.execution_label_props[k] = v
        self.execution_label_props["Execution_Name"] = (
            execution_type + ":" + str(self.execution.id)
        )
        self.execution_label_props["execution_command"] = execution_cmd
        if self.graph:
            self.driver.create_execution_node(
                self.execution_name,
                self.child_context.id,
                self.parent_context,
                execution_cmd,
                self.execution.id,
                custom_props,
            )
        return self.execution

    def log_dvc_lock(self, file_path: str):
        """Used to update the dvc lock file created with dvc run command."""
        print("Entered dvc lock file commit")
        return commit_dvc_lock_file(file_path, self.execution.id)

    def log_dataset(
        self,
        url: str,
        event: str,
        custom_properties: t.Optional[t.Dict] = None,
        external: bool = False,
    ) -> mlpb.Artifact:
        """Logs a dataset as artifact.
        This call adds the dataset to dvc. The dvc metadata file created (.dvc) will be added to git and committed. The
        version of the  dataset is automatically obtained from the versioning software(DVC) and tracked as a metadata.
        Example:
            ```python
            artifact: mlmd.proto.Artifact = cmf.log_dataset(
                url="/repo/data.xml",
                event="input",
                custom_properties={"source":"kaggle"}
            )
            ```
        Args:
             url: The path to the dataset.
             event: Takes arguments `INPUT` OR `OUTPUT`.
             custom_properties: Dataset properties (key/value pairs).
        Returns:
            Artifact object from ML Metadata library associated with the new dataset artifact.
        """
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
        dataset_commit = c_hash
        dvc_url = dvc_get_url(url)
        dvc_url_with_pipeline = f"{self.parent_context.name}:{dvc_url}"
        url = url + ":" + c_hash
        if c_hash and c_hash.strip:
            existing_artifact.extend(self.store.get_artifacts_by_uri(c_hash))

        # To Do - What happens when uri is the same but names are different
        if existing_artifact and len(existing_artifact) != 0:
            existing_artifact = existing_artifact[0]

            # Quick fix- Updating only the name
            if custom_properties is not None:
                self.update_existing_artifact(
                    existing_artifact, custom_properties)
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
        return artifact

    def update_dataset_url(self, artifact: mlpb.Artifact, updated_url: str):
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
                if updated_url not in old_url:
                    new_url = f"{old_url},{updated_url}"
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
                    if updated_url not in old_url:
                        new_url = f"{old_url},{updated_url}"
                        dup_art.properties[key].string_value = new_url
            put_artifact(self.store, dup_art)
        return dup_artifact

    def log_dataset_with_version(
        self,
        url: str,
        version: str,
        event: str,
        props: t.Optional[t.Dict] = None,
        custom_properties: t.Optional[t.Dict] = None,
    ) -> mlpb.Artifact:
        """Logs a dataset when the version (hash) is known.
           Example: 
             ```python 
             artifact: mlpb.Artifact = cmf.log_dataset_with_version( 
                 url="path/to/dataset", 
                 version="abcdef",
                 event="output",
                 props={ "git_repo": "https://github.com/example/repo",
                         "url": "/path/in/repo", },
                 custom_properties={ "custom_key": "custom_value", }, 
                 ) 
             ```
             Args: 
                url: Path to the dataset. 
                version: Hash or version identifier for the dataset. 
                event: Takes arguments `INPUT` or `OUTPUT`. 
                props: Optional properties for the dataset (e.g., git_repo, url). 
                custom_properties: Optional custom properties for the dataset.
             Returns:
                Artifact object from the ML Protocol Buffers library associated with the new dataset artifact. 
        """

        props = {} if props is None else props
        custom_props = {} if custom_properties is None else custom_properties
        git_repo = props.get("git_repo", "")
        name = url
        event_type = mlpb.Event.Type.OUTPUT
        existing_artifact = []
        c_hash = version
        if event.lower() == "input":
            event_type = mlpb.Event.Type.INPUT

        # dataset_commit = commit_output(url, self.execution.id)

        dataset_commit = version
        url = url + ":" + c_hash
        if c_hash and c_hash.strip:
            existing_artifact.extend(self.store.get_artifacts_by_uri(c_hash))

        # To Do - What happens when uri is the same but names are different
        if existing_artifact and len(existing_artifact) != 0:
            existing_artifact = existing_artifact[0]

            # Quick fix- Updating only the name
            if custom_properties is not None:
                self.update_existing_artifact(
                    existing_artifact, custom_properties)
            uri = c_hash
            # update url for existing artifact
            self.update_dataset_url(existing_artifact, props.get("url", ""))
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
                    "Commit": str(dataset_commit),
                    "url": props.get("url", " "),
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
        return artifact

    # Add the model to dvc do a git commit and store the commit id in MLMD
    def log_model(
        self,
        path: str,
        event: str,
        model_framework: str = "Default",
        model_type: str = "Default",
        model_name: str = "Default",
        custom_properties: t.Optional[t.Dict] = None,
    ) -> mlpb.Artifact:
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

        if (
            existing_artifact
            and len(existing_artifact) != 0
        ):
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
            model_uri = artifact.name
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
        # custom_properties["Commit"] = model_commit
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

        return artifact

    # Add the model to dvc do a git commit and store the commit id in MLMD
    def log_model_with_version(
        self,
        path: str,
        event: str,
        props=None,
        custom_properties: t.Optional[t.Dict] = None,
    ) -> object:
        """Logs a model when the version(hash) is known
         The model is added to dvc and the metadata file (.dvc) gets committed to git.
        Example:
            ```python
            artifact: mlmd.proto.Artifact= cmf.log_model_with_version(
                path="path/to/model.pkl",
                event="output",
                props={
                        "url": "/home/user/local-storage/bf/629ccd5cd008066b72c04f9a918737",
                        "model_type": "RandomForestClassifier",
                        "model_name": "RandomForestClassifier:default",
                        "Commit": "commit 1146dad8b74cae205db6a3132ea403db1e4032e5",
                        "model_framework": "SKlearn",
                       },
                custom_properties={
                        "uri": "bf629ccd5cd008066b72c04f9a918737",
                },

            )
            ```
        Args:
            path: Path to the model file.
            event: Takes arguments `INPUT` OR `OUTPUT`.
            props: Model artifact properties.
            custom_properties: The model properties.
        Returns:
            Artifact object from ML Metadata library associated with the new model artifact.
        """

        if custom_properties is None:
            custom_properties = {}
        custom_props = {} if custom_properties is None else custom_properties
        name = re.split("/", path)[-1]
        event_type = mlpb.Event.Type.OUTPUT
        existing_artifact = []
        if event.lower() == "input":
            event_type = mlpb.Event.Type.INPUT

        # props["commit"] = "" # To do get from incoming data
        c_hash = props.get("uri", " ")
        # If connecting to an existing artifact - The name of the artifact is used as path/steps/key
        model_uri = path + ":" + c_hash
        # dvc_url = dvc_get_url(path, False)
        url = props.get("url", "")
        # uri = ""
        if c_hash and c_hash.strip():
            uri = c_hash.strip()
            existing_artifact.extend(self.store.get_artifacts_by_uri(uri))
        else:
            raise RuntimeError("Model commit failed, Model uri empty")

        if (
            existing_artifact
            and len(existing_artifact) != 0
        ):
            # update url for existing artifact
            existing_artifact = self.update_model_url(existing_artifact, url)
            artifact = link_execution_to_artifact(
                store=self.store,
                execution_id=self.execution.id,
                uri=c_hash,
                input_name=model_uri,
                event_type=event_type,
            )
            model_uri = artifact.name
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
                    "model_framework": props.get("model_framework", ""),
                    "model_type": props.get("model_type", ""),
                    "model_name": props.get("model_name", ""),
                    "Commit": props.get("Commit", ""),
                    "url": str(url),
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
        # custom_properties["Commit"] = model_commit
        # custom_props["url"] = url
        self.execution_label_props["Commit"] = props.get("Commit", "")
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

        return artifact

    def log_execution_metrics_from_client(self, metrics_name: str,
                                         custom_properties: t.Optional[t.Dict] = None) -> mlpb.Artifact:
        """ Logs execution metrics from a client.
            Data from pre-existing metrics from client side is used to create identical metrics on server side. 
            Example: 
              ```python 
              artifact: mlpb.Artifact = cmf.log_execution_metrics_from_client( 
                      metrics_name="example_metrics:uri:123", 
                      custom_properties={"custom_key": "custom_value"}, 
                      )
              ``` 
              Args: 
                 metrics_name: Name of the metrics in the format "name:uri:execution_id". 
                 custom_properties: Optional custom properties for the metrics. 
              Returns: 
                 Artifact object from the ML Protocol Buffers library associated with the metrics artifact.
        """
        metrics = None
        custom_props = {} if custom_properties is None else custom_properties
        existing_artifact = []
        name_tokens = metrics_name.split(":")
        if name_tokens and len(name_tokens) > 2:
            name = name_tokens[0]
            uri = name_tokens[1]
            execution_id = name_tokens[2]
        else:
            print(f"Error : metrics name {metrics_name} is not in the correct format")
            return 

        #we need to add the execution id to the metrics name
        new_metrics_name = f"{name}:{uri}:{str(self.execution.id)}"
        existing_artifacts = self.store.get_artifacts_by_uri(uri)

        existing_artifact = existing_artifacts[0] if existing_artifacts else None
        if not existing_artifact or \
           ((existing_artifact) and not
            (existing_artifact.name == new_metrics_name)):  #we need to add the artifact otherwise its already there 
            metrics = create_new_artifact_event_and_attribution(
            store=self.store,
            execution_id=self.execution.id,
            context_id=self.child_context.id,
            uri=uri,
            name=new_metrics_name,
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
        return metrics


    def log_execution_metrics(
        self, metrics_name: str, custom_properties: t.Optional[t.Dict] = None
    ) -> mlpb.Artifact:
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
        if metrics_name in self.metrics:
            key = max((self.metrics[metrics_name]).keys()) + 1
            self.metrics[metrics_name][key] = custom_properties
        else:
            self.metrics[metrics_name] = {}
            self.metrics[metrics_name][1] = custom_properties

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
        metrics_df = pd.DataFrame.from_dict(
            self.metrics[metrics_name], orient="index")
        metrics_df.index.names = ["SequenceNumber"]
        metrics_df.to_parquet(metrics_name)
        commit_output(metrics_name, self.execution.id)
        uri = dvc_get_hash(metrics_name)
        metrics_commit = uri
        name = (
            metrics_name
            + ":"
            + uri
            + ":"
            + str(self.execution.id)
            + ":"
            + str(uuid.uuid1())
        )
        # passing uri value to commit
        custom_props = {"Name": metrics_name, "Commit": metrics_commit}
        metrics = create_new_artifact_event_and_attribution(
            store=self.store,
            execution_id=self.execution.id,
            context_id=self.child_context.id,
            uri=uri,
            name=name,
            type_name="Step_Metrics",
            event_type=mlpb.Event.Type.OUTPUT,
            custom_properties=custom_props,
            milliseconds_since_epoch=int(time.time() * 1000),
        )
        if self.graph:
            self.driver.create_metrics_node(
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
                "Type": "Metrics",
                "Execution_Command": self.execution_command,
                "Pipeline_Id": self.parent_context.id,
            }
            self.driver.create_artifact_relationships(
                self.input_artifacts, child_artifact, self.execution_label_props
            )
        return metrics

    def commit_existing_metrics(self, metrics_name: str, uri: str, custom_properties: t.Optional[t.Dict] = None):
        """ 
        Commits existing metrics associated with the given URI to MLMD. 
        Example: 
        ```python 
           artifact: mlpb.Artifact = cmf.commit_existing_metrics("existing_metrics", "abc123", 
           {"custom_key": "custom_value"}) 
        ``` 
        Args: 
           metrics_name: Name of the metrics. 
           uri: Unique identifier associated with the metrics. 
           custom_properties: Optional custom properties for the metrics. 
        Returns:
           Artifact object from the ML Protocol Buffers library associated with the existing metrics artifact. 
        """

        custom_props =  {} if custom_properties is None else custom_properties
        c_hash = uri.strip()
        existing_artifact = []
        existing_artifact.extend(self.store.get_artifacts_by_uri(c_hash))
        if (existing_artifact
            and len(existing_artifact) != 0 ):
            metrics = link_execution_to_artifact(
                store=self.store,
                execution_id=self.execution.id,
                uri=c_hash,
                input_name=metrics_name,
                event_type=mlpb.Event.Type.OUTPUT,
            )
        else:
            metrics = create_new_artifact_event_and_attribution(
                store=self.store,
                execution_id=self.execution.id,
                context_id=self.child_context.id,
                uri=uri,
                name=metrics_name,
                type_name="Step_Metrics",
                event_type=mlpb.Event.Type.OUTPUT,
                custom_properties=custom_props,
                milliseconds_since_epoch=int(time.time() * 1000),
            )
        if self.graph:
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
            }
            self.driver.create_artifact_relationships(
                self.input_artifacts, child_artifact, self.execution_label_props
            )
        return metrics


    def log_validation_output(
        self, version: str, custom_properties: t.Optional[t.Dict] = None
    ) -> object:
        uri = str(uuid.uuid1())
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
        self, artifact: mlpb.Artifact, custom_properties: t.Dict
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
                artifact.custom_properties[key].string_value = str(value)
        put_artifact(self.store, artifact)

    def get_artifact(self, artifact_id: int) -> mlpb.Artifact:
        """Gets the artifact object from mlmd"""
        return get_artifacts_by_id(self.store, [artifact_id])[0]

    # To Do - The interface should be simplified.
    # To Do - Links should be created in mlmd also.
    # Todo - assumes source as Dataset and target as slice - should be generic and accomodate any types
    def link_artifacts(
        self, artifact_source: mlpb.Artifact, artifact_target: mlpb.Artifact
    ):
        self.driver.create_links(artifact_source.name,
                                 artifact_target.name, "derived")

    def update_model_output(self, artifact: mlpb.Artifact):
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
        df = pd.read_parquet(name)
        temp_dict = df.to_dict("index")
        temp_dict[record].update(custom_properties)
        dataslice_df = pd.DataFrame.from_dict(temp_dict, orient="index")
        dataslice_df.index.names = ["Path"]
        dataslice_df.to_parquet(name)

    class DataSlice:
        """A data slice represents a named subset of data.
        It can be used to track performance of an ML model on different slices of the training or testing dataset
        splits. This can be useful from different perspectives, for instance, to mitigate model bias.
        > Instances of data slices are not meant to be created manually by users. Instead, use
        [Cmf.create_dataslice][cmflib.cmf.Cmf.create_dataslice] method.
        """

        def __init__(self, name: str, writer):
            self.props = {}
            self.name = name
            self.writer = writer

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
                dataslice.add_data(f"data/raw_data/{j}.xml)
                ```
            Args:
                path: Name to identify the file to be added to the dataslice.
                custom_properties: Properties associated with this datum.
            """

            self.props[path] = {}
            # self.props[path]['hash'] = dvc_get_hash(path)
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
            custom_props = {} if custom_properties is None else custom_properties
            git_repo = git_get_repo()
            dataslice_df = pd.DataFrame.from_dict(self.props, orient="index")
            dataslice_df.index.names = ["Path"]
            dataslice_df.to_parquet(self.name)
            existing_artifact = []

            commit_output(self.name, self.writer.execution.id)
            c_hash = dvc_get_hash(self.name)
            dataslice_commit = c_hash
            remote = dvc_get_url(self.name)
            if c_hash and c_hash.strip():
                existing_artifact.extend(
                    self.writer.store.get_artifacts_by_uri(c_hash))
            if existing_artifact and len(existing_artifact) != 0:
                print("Adding to existing data slice")
                slice = link_execution_to_input_artifact(
                    store=self.writer.store,
                    execution_id=self.writer.execution.id,
                    uri=c_hash,
                    input_name=self.name + ":" + c_hash,
                )
            else:
                props = {
                    "Commit": dataslice_commit,  # passing c_hash value to commit
                    "git_repo": git_repo,
                    "Remote": remote,
                }
                props.update(custom_props)
                slice = create_new_artifact_event_and_attribution(
                    store=self.writer.store,
                    execution_id=self.writer.execution.id,
                    context_id=self.writer.child_context.id,
                    uri=c_hash,
                    name=self.name + ":" + c_hash,
                    type_name="Dataslice",
                    event_type=mlpb.Event.Type.OUTPUT,
                    custom_properties=props,
                    milliseconds_since_epoch=int(time.time() * 1000),
                )
            if self.writer.graph:
                self.writer.driver.create_dataslice_node(
                    self.name, self.name + ":" + c_hash, c_hash, self.data_parent, props
                )
            return slice

        def commit_existing(self, uri: str, custom_properties: t.Optional[t.Dict] = None) -> None:
            custom_props = {} if custom_properties is None else custom_properties
            c_hash = uri
            dataslice_commit = c_hash
            existing_artifact = []
            if c_hash and c_hash.strip():
                existing_artifact.extend(
                    self.writer.store.get_artifacts_by_uri(c_hash))
            if existing_artifact and len(existing_artifact) != 0:
                print("Adding to existing data slice")
                slice = link_execution_to_input_artifact(
                    store=self.writer.store,
                    execution_id=self.writer.execution.id,
                    uri=c_hash,
                    input_name=self.name
                )
            else:
                slice = create_new_artifact_event_and_attribution(
                    store=self.writer.store,
                    execution_id=self.writer.execution.id,
                    context_id=self.writer.child_context.id,
                    uri=c_hash,
                    name=self.name,
                    type_name="Dataslice",
                    event_type=mlpb.Event.Type.OUTPUT,
                    custom_properties=custom_properties,
                    milliseconds_since_epoch=int(time.time() * 1000),
                )
            if self.writer.graph:
                self.writer.driver.create_dataslice_node(
                    self.name, self.name, c_hash, self.data_parent, custom_properties
                )
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

def metadata_push(pipeline_name,filename,execution_id: str = ""):
    """ Pushes MLMD file to CMF-server.
    Example:
    ```python
         result = metadata_push("example_pipeline", "mlmd_file", "3")
    ```
    Args:
        pipeline_name: Name of the pipeline.
        filename: Path to the MLMD file.
        execution_id: Optional execution ID.

    Returns:
        Response output from the _metadata_push function.
    """
    # Required arguments:  pipeline_name, filename (mlmd file path) 
    #Optional arguments: Execution_ID
    output = _metadata_push(pipeline_name,filename, execution_id)
    return output

def metadata_pull(pipeline_name,filename ="./mlmd", execution_id: str = ""):
    """ Pulls MLMD file from CMF-server. 
     Example: 
     ```python 
          result = metadata_pull("example_pipeline", "./mlmd_directory", "execution_123") 
     ``` 
     Args: 
        pipeline_name: Name of the pipeline. 
        filename: File path to store the MLMD file. 
        execution_id: Optional execution ID. 
     Returns: 
        Message from the _metadata_pull function. 
     """
    # Required arguments:  pipeline_name, filename(file path to store mlmd file) 
    #Optional arguments: Execution_ID
    output = _metadata_pull(pipeline_name,filename, execution_id)
    return output

def artifact_pull(pipeline_name,filename="./mlmd"):
    """ Pulls artifacts from the initialized repository.

    Example:
    ```python
         result = artifact_pull("example_pipeline", "./mlmd_directory")
    ```

    Args:
        pipeline_name: Name of the pipeline.
        filename: Path to store artifacts.

    Returns:
        Output from the _artifact_pull function.
    """

    # Required arguments: Pipeline_name
    # Optional arguments: filename( path to store artifacts)
    output = _artifact_pull(pipeline_name,filename)
    return output

def artifact_pull_single(pipeline_name,filename,artifact_name):
    """ Pulls a single artifact from the initialized repository. 
    Example: 
    ```python 
        result = artifact_pull_single("example_pipeline", "./mlmd_directory", "example_artifact") 
    ```
    Args: 
       pipeline_name: Name of the pipeline. 
       filename: Path to store the artifact. 
       artifact_name: Name of the artifact. 
    Returns:
       Output from the _artifact_pull_single function. 
    """

    # Required arguments: Pipeline_name
    # Optional arguments: filename( path to store artifacts)
    output = _artifact_pull_single(pipeline_name,filename,artifact_name)
    return output

def artifact_push():
    """ Pushes artifacts to the initialized repository.

    Example:
    ```python
         result = artifact_push()
    ```

    Returns:
        Output from the _artifact_push function.
    """
    output = _artifact_push()
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

def cmf_init(type: str="",
        path: str="",
        git_remote_url: str="",
        cmf_server_url: str = "",
        neo4j_user: str = "",
        neo4j_password: str = "",
        neo4j_uri: str = "",
        url: str="",
        endpoint_url: str="",
        access_key_id: str="",
        secret_key: str="",
        user: str="",
        password: str="",
        port: int=0
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
       type: Type of repository ("local", "minioS3", "amazonS3", "sshremote")
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
       user: SSH remote username.
       password: SSH remote password. 
       port: SSH remote port
    Returns:
       Output based on the initialized repository type.
    """

    if type=="":
        return print("Error: Type is not provided")
    if type not in ["local","minioS3","amazonS3","sshremote"]:
        return print("Error: Type value is undefined"+ " "+type+".Expected: "+",".join(["local","minioS3","amazonS3","sshremote"]))

    if neo4j_user!="" and  neo4j_password != "" and neo4j_uri != "":
        pass
    elif neo4j_user == "" and  neo4j_password == "" and neo4j_uri == "":
        pass
    else:
        return print("Error: Enter all neo4j parameters.") 

    args={'path':path,
        'git_remote_url':git_remote_url,
       'url':url,
        'endpoint_url':endpoint_url,
        'access_key_id':access_key_id,
        'secret_key':secret_key,
        'user':user,
        'password':password,
        }

    status_args=non_related_args(type,args)

    if type=="local" and path!= "" and  git_remote_url!= "" :
        """Initialize local repository"""
        output = _init_local(
            path, git_remote_url, cmf_server_url, neo4j_user, neo4j_password, neo4j_uri
        )
        if status_args != []:
            print("There are non-related arguments: "+",".join(status_args)+".Please remove them.")
        return output
         
    elif type=="minioS3" and url!= "" and endpoint_url!= "" and access_key_id!= "" and secret_key!= "" and git_remote_url!= "":
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

    elif type=="amazonS3" and url!= "" and access_key_id!= "" and secret_key!= "" and git_remote_url!= "":
        """Initialize amazonS3 repository"""
        output = _init_amazonS3(
            url,
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

    elif type=="sshremote" and path !="" and user!="" and port!=0 and password!="" and git_remote_url!="":
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

    else:
        print("Error: Enter all arguments")


def non_related_args(type:str,args:dict):
    available_args=[i for i,j in args.items() if j!=""]
    local=["path","git_remote_url"]
    minioS3=["url","endpoint_url","access_key_id","secret_key","git_remote_url"]
    amazonS3=["url","access_key_id","secret_key","git_remote_url"]
    sshremote=["path","user","port","password","git_remote_url"]

    dict_repository_args={"local":local,"minioS3":minioS3,"amazonS3":amazonS3,"sshremote":sshremote}
    
    for repo,arg in dict_repository_args.items():
        if repo ==type:
            non_related_args=list(set(available_args)-set(dict_repository_args[repo]))
    return non_related_args
 
    
