"""This module contains all the APIs for CMF server"""
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
import typing as t

# This import is needed for jupyterlab environment
from ml_metadata.proto import metadata_store_pb2 as mlpb
from cmflib.metadata_helper import (
    get_or_create_run_context,
    associate_child_to_parent_context,
    create_new_execution_in_existing_run_context,
    link_execution_to_artifact,
    create_new_artifact_event_and_attribution,
    link_execution_to_input_artifact,
)

def merge_created_context(
    self, pipeline_stage: str, custom_properties: t.Optional[t.Dict] = None
) -> mlpb.Context:  # type: ignore  # Context type not recognized by mypy, using ignore to bypass
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
        cmf = Cmf(filepath="mlmd", pipeline_name="test_pipeline")
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


def merge_created_execution(
    self,
    execution_type: str,
    execution_cmd: str,
    properties: t.Optional[t.Dict] = None,
    custom_properties: t.Optional[t.Dict] = None,
    orig_execution_name:str = "",
    create_new_execution:bool = True
) -> mlpb.Execution:    # type: ignore  # Execution type not recognized by mypy, using ignore to bypass
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
        cmf = Cmf(filepath="mlmd", pipeline_name="test_pipeline")
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
        # In case of a reusable execution, the execution UUID is repeated each time while pushing MLMD inside the server.  
        # To resolve this, taking the union of  properties["Execution_uuid"] and uuids.
        set_of_uuids = set(uuids.split(",") + properties["Execution_uuid"].split(","))
        self.execution.properties["Execution_uuid"].string_value = ",".join(set_of_uuids)
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

    # link the artifact to execution if it exists and creates artifact if it doesn't
    return self.execution


def log_python_env_from_client(
        self,
        url: str,
        uri: str,
        props: t.Optional[t.Dict] = None,
    ) -> mlpb.Artifact: # type: ignore  # Artifact type not recognized by mypy, using ignore to bypass
        "Used to log the python packages involved in the current execution"
        props = {} if props is None else props
        git_repo = props.get("git_repo", "")
        name = url
        existing_artifact = []
        c_hash = uri
        commit = props.get("Commit", "")
        url = url + ":" + c_hash
        if c_hash and c_hash.strip():
            existing_artifact.extend(self.store.get_artifacts_by_uri(c_hash))

        if existing_artifact and len(existing_artifact) != 0:
            existing_artifact = existing_artifact[0]
            artifact = link_execution_to_artifact(
                store=self.store,
                execution_id=self.execution.id,
                uri=uri,
                input_name=url,
                event_type=mlpb.Event.Type.INPUT,   # type: ignore  # Event type not recognized by mypy, using ignore to bypass
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
                event_type=mlpb.Event.Type.INPUT,   # type: ignore  # Event type not recognized by mypy, using ignore to bypass
                properties={
                    "git_repo": str(git_repo),
                    # passing c_hash value to commit
                    "Commit": str(commit),
                    "url": props.get("url", ""),
                },
                artifact_type_properties={
                    "git_repo": mlpb.STRING,    # type: ignore  # String type not recognized by mypy, using ignore to bypass
                    "Commit": mlpb.STRING,      # type: ignore  # String type not recognized by mypy, using ignore to bypass
                    "url": mlpb.STRING,         # type: ignore  # String type not recognized by mypy, using ignore to bypass
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
            self.driver.create_execution_links(uri, name, "Environment")
        return artifact


def log_dataset_with_version(
    self,
    url: str,
    version: str,
    event: str,
    props: t.Optional[t.Dict] = None,
    custom_properties: t.Optional[t.Dict] = None,
) -> mlpb.Artifact: # type: ignore  # Artifact type not recognized by mypy, using ignore to bypass
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
    event_type = mlpb.Event.Type.OUTPUT # type: ignore  # Event type not recognized by mypy, using ignore to bypass
    existing_artifact = []
    c_hash = version
    if event.lower() == "input":
        event_type = mlpb.Event.Type.INPUT  # type: ignore  # Event type not recognized by mypy, using ignore to bypass

    # dataset_commit = commit_output(url, self.execution.id)

    dataset_commit = version
    url = url + ":" + c_hash
    if c_hash and c_hash.strip():
        existing_artifact.extend(self.store.get_artifacts_by_uri(c_hash))

    # To Do - What happens when uri is the same but names are different
    if existing_artifact and len(existing_artifact) != 0:
        existing_artifact = existing_artifact[0]

        # Quick fix- Updating only the name
        if custom_props is not None:
            self.update_existing_artifact(
                existing_artifact, custom_props)
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
                "git_repo": mlpb.STRING,    # type: ignore  # String type not recognized by mypy, using ignore to bypass
                "Commit": mlpb.STRING,      # type: ignore  # String type not recognized by mypy, using ignore to bypass
                "url": mlpb.STRING,         # type: ignore  # String type not recognized by mypy, using ignore to bypass
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


def log_label_with_version(self, url: str, version:str, props: t.Optional[t.Dict] = None, 
                           custom_properties: t.Optional[t.Dict] = None
) -> mlpb.Artifact: # type: ignore  # Artifact type not recognized by mypy, using ignore to bypass
    """
        needs to be added 
    """
    props = {} if props is None else props
    custom_props = {} if custom_properties is None else custom_properties
    git_repo = props.get("git_repo", "")
    existing_artifact = []
    c_hash = version

    label_commit = version
    url = url + ":" + c_hash
    if c_hash and c_hash.strip():
        existing_artifact.extend(self.store.get_artifacts_by_uri(c_hash))

    # To Do - What happens when uri is the same but names are different
    if existing_artifact and len(existing_artifact) != 0:
        existing_artifact = existing_artifact[0]

        # Quick fix- Updating only the name
        if custom_props is not None:
            self.update_existing_artifact(
                existing_artifact, custom_props)
        uri = c_hash
        # update url for existing artifact
        self.update_dataset_url(existing_artifact, props.get("url", ""))
        artifact = link_execution_to_artifact(
            store=self.store,
            execution_id=self.execution.id,
            uri=uri,
            input_name=url,
            event_type=mlpb.Event.Type.INPUT,
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
            type_name="Label",
            event_type=mlpb.Event.Type.INPUT,
            properties={
                "git_repo": str(git_repo),
                "Commit": str(label_commit),
                "url": props.get("url", " "),
                "dataset_uri": props.get("dataset_uri", " ")
            },
            artifact_type_properties={
                "git_repo": mlpb.STRING,    # type: ignore  # String type not recognized by mypy, using ignore to bypass
                "Commit": mlpb.STRING,      # type: ignore  # String type not recognized by mypy, using ignore to bypass
                "url": mlpb.STRING,         # type: ignore  # String type not recognized by mypy, using ignore to bypass
                "dataset_uri": mlpb.STRING, # type: ignore  # String type not recognized by mypy, using ignore to bypass
            },
            custom_properties=custom_props,
            milliseconds_since_epoch=int(time.time() * 1000),
        )
    custom_props["git_repo"] = git_repo
    custom_props["Commit"] = label_commit
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
    event_type = mlpb.Event.Type.OUTPUT # type: ignore  # Event type not recognized by mypy, using ignore to bypass
    existing_artifact = []
    if event.lower() == "input":
        event_type = mlpb.Event.Type.INPUT  # type: ignore  # Event type not recognized by mypy, using ignore to bypass

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
                "model_framework": mlpb.STRING,     # type: ignore  # String type not recognized by mypy, using ignore to bypass
                "model_type": mlpb.STRING,          # type: ignore  # String type not recognized by mypy, using ignore to bypass
                "model_name": mlpb.STRING,          # type: ignore  # String type not recognized by mypy, using ignore to bypass
                "Commit": mlpb.STRING,              # type: ignore  # String type not recognized by mypy, using ignore to bypass
                "url": mlpb.STRING,                 # type: ignore  # String type not recognized by mypy, using ignore to bypass
            },
            custom_properties=custom_props,
            milliseconds_since_epoch=int(time.time() * 1000),
        )
    custom_properties["Commit"] = props.get("Commit", "")
    custom_props["url"] = url
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
                                        custom_properties: t.Optional[t.Dict] = None) -> mlpb.Artifact: # type: ignore  # Artifact type not recognized by mypy, using ignore to bypass
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
    existing_artifact: t.Optional[mlpb.Artifact] = None # type: ignore  # Artifact type not recognized by mypy, using ignore to bypass
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
        (existing_artifact.name == new_metrics_name)): #we need to add the artifact otherwise its already there
        metrics = create_new_artifact_event_and_attribution(
        store=self.store,
        execution_id=self.execution.id,
        context_id=self.child_context.id,
        uri=uri,
        name=new_metrics_name,
        type_name="Metrics",
        event_type=mlpb.Event.Type.OUTPUT,  # type: ignore  # Event type not recognized by mypy, using ignore to bypass
        properties={"metrics_name": metrics_name},
        artifact_type_properties={"metrics_name": mlpb.STRING}, # type: ignore  # String type not recognized by mypy, using ignore to bypass
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



def log_step_metrics_from_client(self, metrics_name: str, uri: str, props: t.Optional[t.Dict] = None, custom_properties: t.Optional[t.Dict] = None):
    """
    Commits existing metrics associated with the given URI to MLMD.
    Example:
    ```python
        artifact: mlpb.Artifact = cmf.log_metrics_from_client("existing_metrics", "abc123",
        {"custom_key": "custom_value"})
    ```
    Args:
        metrics_name: Name of the metrics.
        uri: Unique identifier associated with the metrics.
        custom_properties: Optional custom properties for the metrics.
    Returns:
        Artifact object from the ML Protocol Buffers library associated with the existing metrics artifact.
    """
    # Ensure `props` is initialized as an empty dictionary if None to avoid attribute errors.
    props = {} if props is None else props
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
            event_type=mlpb.Event.Type.OUTPUT,  # type: ignore  # Event type not recognized by mypy, using ignore to bypass
        )
    else:
        metrics = create_new_artifact_event_and_attribution(
            store=self.store,
            execution_id=self.execution.id,
            context_id=self.child_context.id,
            uri=uri,
            name=metrics_name,
            type_name="Step_Metrics",
            event_type=mlpb.Event.Type.OUTPUT,  # type: ignore  # Event type not recognized by mypy, using ignore to bypass
            properties={
                # passing uri value to commit
                "Commit": props.get("Commit", ""),
                "url": props.get("url", ""),
            },
            artifact_type_properties={
                "Commit": mlpb.STRING,  # type: ignore  # String type not recognized by mypy, using ignore to bypass
                "url": mlpb.STRING,     # type: ignore  # String type not recognized by mypy, using ignore to bypass
            },
            custom_properties=custom_props,
            milliseconds_since_epoch=int(time.time() * 1000),
        )
    metrics_commit = props.get("Commit", "")
    custom_props["Commit"] = metrics_commit
    self.execution_label_props["Commit"] = metrics_commit

    if self.graph:
        self.driver.create_step_metrics_node(
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
            "Type": "Step_Metrics",
            "Execution_Command": self.execution_command,
            "Pipeline_Id": self.parent_context.id,
        }
        self.driver.create_artifact_relationships(
            self.input_artifacts, child_artifact, self.execution_label_props
        )
    return metrics

# commit existing dataslice to server
def log_dataslice_from_client(self, uri: str, props: t.Optional[t.Dict] = None, custom_properties: t.Optional[t.Dict] = None) -> None:
    custom_props = {} if custom_properties is None else custom_properties
    props = {} if props is None else props
    c_hash = uri.strip()
    dataslice_commit = c_hash
    existing_artifact = []
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
            input_name=self.name,
        )
    else:
        slice = create_new_artifact_event_and_attribution(
            store=self.writer.store,
            execution_id=self.writer.execution.id,
            context_id=self.writer.child_context.id,
            uri=c_hash,
            name=self.name,
            type_name="Dataslice",
            event_type=mlpb.Event.Type.OUTPUT,  # type: ignore  # Event type not recognized by mypy, using ignore to bypass
            properties={
                "git_repo": props.get("git_repo", ""),
                "Commit": props.get("Commit", ""),
                "url": props.get("url", " "),
            },
            artifact_type_properties={
                "git_repo": mlpb.STRING,    # type: ignore  # String type not recognized by mypy, using ignore to bypass
                "Commit": mlpb.STRING,      # type: ignore  # String type not recognized by mypy, using ignore to bypass
                "url": mlpb.STRING,         # type: ignore  # String type not recognized by mypy, using ignore to bypass
            },
            custom_properties=custom_props,
            milliseconds_since_epoch=int(time.time() * 1000),
        )
    custom_props["git_repo"] = props.get("git_repo", "")
    custom_props["Commit"] = props.get("Commit", "")
    if self.writer.graph:
        self.writer.driver.create_dataslice_node(
            self.name, self.name, c_hash, self.data_parent, custom_props
        )
    return slice