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

from ml_metadata.proto import metadata_store_pb2 as mlpb
from ml_metadata.metadata_store import metadata_store
from cmflib.dvc_wrapper import dvc_get_url, dvc_get_hash, git_get_commit, \
    commit_output, git_get_repo, commit_dvc_lock_file,  \
    git_checkout_new_branch, \
    check_git_repo, check_default_remote, check_git_remote
from cmflib import graph_wrapper
from cmflib.metadata_helper import get_or_create_parent_context,   \
    get_or_create_run_context, associate_child_to_parent_context,  \
    create_new_execution_in_existing_run_context, link_execution_to_artifact, \
    create_new_artifact_event_and_attribution, get_artifacts_by_id,  \
    put_artifact, link_execution_to_input_artifact


class Cmf:
    """This class provides methods to log metadata for distributed AI pipelines.

    The class instance creates an ML metadata store to store the metadata. It creates a driver to store nodes and its
    relationships to neo4j. The user has to provide the name of the pipeline, that needs to be recorded with it.

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
        pipeline_name: Name to uniquely identify the pipeline. Note that name is the unique identification for a
            pipeline.  If a pipeline already exist with the same name, the existing pipeline object is reused.
        custom_properties: Additional properties of the pipeline that needs to be stored.
        graph: If set to true, the libray also stores the relationships in the provided graph database. The following
            environment variables should be set: `NEO4J_URI` (graph server URI), `NEO4J_USER_NAME` (user name) and
            `NEO4J_PASSWD` (user password), e.g.:
            ```bash
            export NEO4J_URI="bolt://ip:port"
            export NEO4J_USER_NAME=neo4j
            export NEO4J_PASSWD=neo4j
            ```
    """

    # pylint: disable=too-many-instance-attributes

    __neo4j_uri = os.getenv('NEO4J_URI', "")
    __neo4j_user = os.getenv('NEO4J_USER_NAME', "")
    __neo4j_password = os.getenv('NEO4J_PASSWD', "")

    def __init__(self, filename: str = "mlmd",
                 pipeline_name: str = "", custom_properties: t.Optional[t.Dict] = None,
                 graph: bool = False):
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
        self.branch_name = filename.rsplit('/',1)[-1]

        git_checkout_new_branch(self.branch_name)
        self.parent_context = get_or_create_parent_context(
            store=self.store, pipeline=pipeline_name, custom_properties=custom_properties)
        if graph is True:
            self.driver = graph_wrapper.GraphDriver(
                Cmf.__neo4j_uri, Cmf.__neo4j_user, Cmf.__neo4j_password)
            self.driver.create_pipeline_node(
                pipeline_name, self.parent_context.id, custom_properties)

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
            print("*** Error git remote not set ***\n"
                  "*** Run the command "
                  "`git remote add origin <GIT_REMOTE_URL>` ***\n"
                  " or \n"
                  " After Updating the sample_env file,"
                  " run `source sample_env`\n"
                  " Then run 'sh initialize.sh'")
            sys.exit(1)

    @staticmethod
    def __check_default_remote():
        """Executes precheck for default dvc remote"""
        if not check_default_remote():
            print("*** DVC not configured correctly***\n"
                  "Initialize dvc and add a default dvc remote\n"
                  "Run commands\n"
                  "dvc init\n"
                  "dvc remote add -d <remotename> <remotelocation>\n")
            sys.exit(1)

    @staticmethod
    def __check_git_init():
        """Verifies that the directory is a git repo"""
        if not check_git_repo():
            print("*** Not a git repo, Please do the following ***\n"
                  " Initialize git\n"
                  " Initialize dvc and add a default dvc remote\n"
                  " or \n"
                  " After Updating the sample_env file,"
                  " run `source sample_env`\n"
                  " Then run 'sh initialize.sh'")
            sys.exit(1)

    def __del__(self):
        """Destructor - Cleans up the connection to neo4j"""
        # if self.execution is not None:
        #    commit_output(self.filename, self.execution.id)
        if hasattr(self, 'driver'):
            self.driver.close()

    def create_context(self, pipeline_stage: str,
                       custom_properties: t.Optional[t.Dict] = None) -> mlpb.Context:
        """Creates a stage in the pipeline.

        If it already exists, it is reused and not created again.

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
            ```

        Args:
            pipeline_stage: Name of the pipeline stage.
            custom_properties: Developers can provide key value pairs with additional properties of the stage that
                need to be stored.
        Returns:
            Context object from ML Metadata library associated with the new stage.
        """
        custom_props = {} if custom_properties is None else custom_properties
        ctx = get_or_create_run_context(
            self.store, pipeline_stage, custom_props)
        self.child_context = ctx
        associate_child_to_parent_context(
            store=self.store,
            parent_context=self.parent_context,
            child_context=ctx)
        if self.graph:
            self.driver.create_stage_node(
                pipeline_stage, self.parent_context, ctx.id, custom_props)
        return ctx

    def create_execution(self, execution_type: str,
                         custom_properties: t.Optional[t.Dict] = None) -> mlpb.Execution:
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
            execution_type: Name of the execution.
            custom_properties: Developers can provide key value pairs with additional properties of the execution that
                need to be stored.

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
        self.execution = create_new_execution_in_existing_run_context(
            store=self.store,
            execution_type_name=execution_type,
            context_id=self.child_context.id,
            execution=str(sys.argv),
            pipeline_id=self.parent_context.id,
            pipeline_type=self.parent_context.name,
            git_repo=git_repo,
            git_start_commit=git_start_commit,
            custom_properties=custom_props
        )
        self.execution_name = str(self.execution.id) + "," + execution_type
        self.execution_command = str(sys.argv)
        for k, v in custom_props.items():
            k = re.sub('-', '_', k)
            self.execution_label_props[k] = v
        self.execution_label_props["Execution_Name"] = execution_type + \
            ":" + str(self.execution.id)
        self.execution_label_props["execution_command"] = str(sys.argv)
        if self.graph:
            self.driver.create_execution_node(
                self.execution_name, self.child_context.id, self.parent_context, str(
                    sys.argv), self.execution.id, custom_props)
        return self.execution

    def update_execution(self, execution_id: int, custom_properties: t.Optional[t.Dict] = None):
        """Updates an existing execution.

        The custom properties can be updated after creation of the execution.
        The new custom properties is merged with earlier custom properties.
        """
        self.execution = self.store.get_executions_by_id([execution_id])[0]
        if self.execution is None:
            print("Error - no execution id")
            sys.exit(1)
        execution_type = self.store.get_execution_types_by_id(
            [self.execution.type_id])[0]

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
            key = re.sub('-', '_', k)
            val_type = str(v).split(':', maxsplit=1)[0]
            if val_type == "string_value":
                val = self.execution.custom_properties[k].string_value
            else:
                val = str(v).split(':')[1]
            # The properties value are stored in the format type:value hence,
            # taking only value
            self.execution_label_props[key] = val
            c_props[key] = val
        self.execution_name = str(
            self.execution.id) + "," + execution_type.name
        self.execution_command = self.execution.properties["Execution"]
        self.execution_label_props["Execution_Name"] = execution_type.name + \
            ":" + str(self.execution.id)
        self.execution_label_props["execution_command"] = self.execution.properties["Execution"].string_value
        if self.graph:
            self.driver.create_execution_node(
                self.execution_name,
                self.child_context.id,
                self.parent_context,
                self.execution.properties["Execution"].string_value,
                self.execution.id,
                c_props)
        return self.execution

    def log_dvc_lock(self, file_path: str):
        """Used to update the dvc lock file created with dvc run command."""
        return commit_dvc_lock_file(file_path, self.execution.id)

    def log_dataset(self, url: str, event: str, custom_properties: t.Optional[t.Dict] = None) -> mlpb.Artifact:
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
        custom_props = {} if custom_properties is None else custom_properties
        git_repo = git_get_repo()
        name = re.split('/', url)[-1]
        event_type = mlpb.Event.Type.OUTPUT
        existing_artifact = []
        if event.lower() == "input":
            event_type = mlpb.Event.Type.INPUT

        dataset_commit = commit_output(url, self.execution.id)
        c_hash = dvc_get_hash(url)

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
            artifact = link_execution_to_artifact(
                store=self.store,
                execution_id=self.execution.id,
                uri=uri,
                input_name=url,
                event_type=event_type)
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
                    "Commit": str(dataset_commit)},
                artifact_type_properties={
                    "git_repo": mlpb.STRING,
                    "Commit": mlpb.STRING},
                custom_properties=custom_props,
                milliseconds_since_epoch=int(
                    time.time() * 1000),
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
                custom_props)
            if event.lower() == "input":
                self.input_artifacts.append({"Name": name,
                                             "Path": url,
                                             "URI": uri,
                                             "Event": event.lower(),
                                             "Execution_Name": self.execution_name,
                                             "Type": "Dataset",
                                             "Execution_Command": self.execution_command,
                                             "Pipeline_Id": self.parent_context.id,
                                             "Pipeline_Name": self.parent_context.name})
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
                    "Pipeline_Name": self.parent_context.name}
                self.driver.create_artifact_relationships(
                    self.input_artifacts, child_artifact, self.execution_label_props)
        return artifact


    def log_dataset_with_version(self, url: str, version: str, event: str,
                                 custom_properties: t.Optional[t.Dict] = None) -> mlpb.Artifact:
        """Logs a dataset when the version(hash) is known"""

        custom_props = {} if custom_properties is None else custom_properties
        git_repo = git_get_repo()
        name = re.split('/', url)[-1]
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
            artifact = link_execution_to_artifact(
                store=self.store,
                execution_id=self.execution.id,
                uri=uri,
                input_name=url,
                event_type=event_type)
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
                    "Commit": str(dataset_commit)},
                artifact_type_properties={
                    "git_repo": mlpb.STRING,
                    "Commit": mlpb.STRING},
                custom_properties=custom_props,
                milliseconds_since_epoch=int(
                    time.time() * 1000),
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
                custom_props)
            if event.lower() == "input":
                self.input_artifacts.append({"Name": name,
                                             "Path": url,
                                             "URI": uri,
                                             "Event": event.lower(),
                                             "Execution_Name": self.execution_name,
                                             "Type": "Dataset",
                                             "Execution_Command": self.execution_command,
                                             "Pipeline_Id": self.parent_context.id,
                                             "Pipeline_Name": self.parent_context.name})
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
                    "Pipeline_Name": self.parent_context.name}
                self.driver.create_artifact_relationships(
                    self.input_artifacts, child_artifact,
                    self.execution_label_props)
        return artifact

    # Add the model to dvc do a git commit and store the commit id in MLMD
    def log_model(self, path: str, event: str, model_framework: str = "Default",
                  model_type: str = "Default", model_name: str = "Default",
                  custom_properties: t.Optional[t.Dict] = None) -> mlpb.Artifact:
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

        if custom_properties is None:
            custom_properties = {}
        custom_props = {} if custom_properties is None else custom_properties
        # name = re.split('/', path)[-1]
        event_type = mlpb.Event.Type.OUTPUT
        existing_artifact = []
        if event.lower() == "input":
            event_type = mlpb.Event.Type.INPUT

        model_commit = commit_output(path, self.execution.id)
        c_hash = dvc_get_hash(path)

        # If connecting to an existing artifact - The name of the artifact is
        # used as path/steps/key
        model_uri = path + ":" + c_hash
        # uri = ""
        if c_hash and c_hash.strip():
            uri = c_hash.strip()
            existing_artifact.extend(self.store.get_artifacts_by_uri(uri))
        else:
            raise RuntimeError("Model commit failed, Model uri empty")

        if existing_artifact and len(
                existing_artifact) != 0 and event_type == mlpb.Event.Type.INPUT:
            artifact = link_execution_to_artifact(
                store=self.store,
                execution_id=self.execution.id,
                uri=c_hash,
                input_name=model_uri,
                event_type=event_type)
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
                    "Commit": str(model_commit)},
                artifact_type_properties={
                    "model_framework": mlpb.STRING,
                    "model_type": mlpb.STRING,
                    "model_name": mlpb.STRING,
                    "Commit": mlpb.STRING,
                },
                custom_properties=custom_props,
                milliseconds_since_epoch=int(
                    time.time() * 1000),
            )
        # custom_properties["Commit"] = model_commit
        self.execution_label_props["Commit"] = model_commit
        if self.graph:
            self.driver.create_model_node(
                model_uri,
                uri,
                event,
                self.execution.id,
                self.parent_context,
                custom_props)
            if event.lower() == "input":

                self.input_artifacts.append(
                    {"Name": model_uri, "URI": uri, "Event": event.lower(),
                        "Execution_Name": self.execution_name,
                     "Type": "Model", "Execution_Command": self.execution_command,
                     "Pipeline_Id": self.parent_context.id,
                     "Pipeline_Name": self.parent_context.name})
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
                    "Pipeline_Name": self.parent_context.name}
                self.driver.create_artifact_relationships(
                    self.input_artifacts, child_artifact, self.execution_label_props)

        return artifact

    def log_execution_metrics(self, metrics_name: str, custom_properties: t.Optional[t.Dict] = None) -> mlpb.Artifact:
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
            properties={
                "metrics_name": metrics_name},
            artifact_type_properties={
                "metrics_name": mlpb.STRING},
            custom_properties=custom_props,
            milliseconds_since_epoch=int(
                time.time() * 1000),
        )
        if self.graph:
            # To do create execution_links
            self.driver.create_metrics_node(
                metrics_name,
                uri,
                "output",
                self.execution.id,
                self.parent_context,
                custom_props)
            child_artifact = {
                "Name": metrics_name,
                "URI": uri,
                "Event": "output",
                "Execution_Name": self.execution_name,
                "Type": "Metrics",
                "Execution_Command": self.execution_command,
                "Pipeline_Id": self.parent_context.id,
                "Pipeline_Name": self.parent_context.name}
            self.driver.create_artifact_relationships(
                self.input_artifacts, child_artifact, self.execution_label_props)
        return metrics

    def log_metric(self, metrics_name: str, custom_properties: t.Optional[t.Dict] = None) -> None:
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
        """Writes the inmemory metrics to parquet file

        Commit the metrics file associated with the metrics id to dvc and git and
        store the artifact in mlmd
        """
        metrics_df = pd.DataFrame.from_dict(
            self.metrics[metrics_name], orient='index')
        metrics_df.index.names = ['SequenceNumber']
        metrics_df.to_parquet(metrics_name)
        metrics_commit = commit_output(metrics_name, self.execution.id)
        uri = dvc_get_hash(metrics_name)
        name = metrics_name + ":" + uri + ":" + \
            str(self.execution.id) + ":" + str(uuid.uuid1())
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
                custom_props)
            child_artifact = {
                "Name": name,
                "URI": uri,
                "Event": "output",
                "Execution_Name": self.execution_name,
                "Type": "Metrics",
                "Execution_Command": self.execution_command,
                "Pipeline_Id": self.parent_context.id}
            self.driver.create_artifact_relationships(
                self.input_artifacts, child_artifact, self.execution_label_props)
        return metrics


    def log_validation_output(self, version: str, custom_properties: t.Optional[t.Dict] = None) -> object:
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


    def update_existing_artifact(self, artifact: mlpb.Artifact, custom_props: t.Dict):
        """Updates an existing artifact and stores it back to mlmd"""
        for key, value in custom_props.items():
            if isinstance(value, int):
                artifact.custom_properties[key].int_value = value
            else:
                artifact.custom_properties[key].string_value = str(value)
        put_artifact(self.store, artifact)


    def get_artifact(self, artifact_id: int) -> mlpb.Artifact:
        """Gets the artifact object from mlmd"""
        return get_artifacts_by_id(self.store, [artifact_id])[0]


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
    def update_dataslice(self, name: str, record: str, custom_props: t.Dict):
        df = pd.read_parquet(name)
        temp_dict = df.to_dict('index')
        temp_dict[record].update(custom_props)
        dataslice_df = pd.DataFrame.from_dict(temp_dict, orient='index')
        dataslice_df.index.names = ['Path']
        dataslice_df.to_parquet(name)

    class DataSlice:
        """A data slice represents a named subset of data.

        It can be used to track performance of an ML model on different slices of the training or testing dataset
        splits. This can be useful from different perspectives, for instance, to mitigate model bias.

        > Instances of data slices are not meant to be created manually by users. Instead, use
        [Cmf.create_dataslice][cmflib.cmf.Cmf.create_dataslice] method.

        """
        def __init__(self, name: str, writer, props: t.Optional[t.Dict] = None):
            self.props = {} if props is None else props
            self.name = name
            self.writer = writer

        def add_data(self, path: str, custom_props: t.Optional[t.Dict] = None) -> None:
            """Add data to create the dataslice.

            Currently supported only for file abstractions. Pre-condition - the parent folder, containing the file
                should already be versioned.

            Example:
                ```python
                dataslice.add_data(f"data/raw_data/{j}.xml)
                ```
            Args:
                path: Name to identify the file to be added to the dataslice.
                custom_props: Properties associated with this datum.
            """

            self.props[path] = {}
            self.props[path]['hash'] = dvc_get_hash(path)
            if custom_props:
                for k, v in custom_props.items():
                    self.props[path][k] = v

#        """
#        Place holder for updating back to mlmd

#        def update_data(self, path, custom_props:{}):
#            for k ,v in custom_props.items():
#                self.props[path][k] = v
#        """

        def commit(self, custom_props: t.Optional[t.Dict] = None) -> None:
            """Commit the dataslice.

            The created dataslice is versioned and added to underneath data versioning software.

            Example:
                ```python
                dataslice.commit()
                ```

            Args:
                custom_props: Properties associated with this data slice.
            """
            git_repo = git_get_repo()
            dataslice_df = pd.DataFrame.from_dict(self.props, orient='index')
            dataslice_df.index.names = ['Path']
            dataslice_df.to_parquet(self.name)
            existing_artifact = []

            dataslice_commit = commit_output(
                self.name, self.writer.execution.id)
            c_hash = dvc_get_hash(self.name)
            remote = dvc_get_url(self.name)
            if c_hash and c_hash.strip():
                existing_artifact.extend(
                    self.writer.store.get_artifacts_by_uri(c_hash))
            if existing_artifact and len(existing_artifact) != 0:
                print("Adding to existing data slice")
                _ = link_execution_to_input_artifact(
                    store=self.writer.store,
                    execution_id=self.writer.execution.id,
                    uri=c_hash,
                    input_name=self.name + ":" + c_hash)
            else:
                props = {
                    "Commit": dataslice_commit,
                    "git_repo": git_repo,
                    "Remote": remote}
                custom_properties = props.update(
                    custom_props) if custom_props else props
                create_new_artifact_event_and_attribution(
                    store=self.writer.store,
                    execution_id=self.writer.execution.id,
                    context_id=self.writer.child_context.id,
                    uri=c_hash,
                    name=self.name + ":" + c_hash,
                    type_name="Dataslice",
                    event_type=mlpb.Event.Type.OUTPUT,
                    custom_properties=custom_properties,
                    milliseconds_since_epoch=int(time.time() * 1000),
                )


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
