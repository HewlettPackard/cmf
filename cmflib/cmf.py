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
import pandas as pd
import uuid
import re
import os
import sys
from ml_metadata.proto import metadata_store_pb2 as mlpb, metadata_store_pb2
from ml_metadata.metadata_store import metadata_store
from cmflib.dvc_wrapper import dvc_get_url, dvc_get_hash, git_get_commit, \
    commit_output, git_get_repo, commit_dvc_lock_file
import cmflib.graph_wrapper as graph_wrapper
from cmflib.metadata_helper import get_or_create_parent_context, get_or_create_run_context, \
    associate_child_to_parent_context, create_new_execution_in_existing_run_context, link_execution_to_artifact, \
    create_new_artifact_event_and_attribution, get_artifacts_by_id, put_artifact, link_execution_to_input_artifact


class Cmf(object):
    __neo4j_uri = os.getenv('NEO4J_URI', "")
    __neo4j_user = os.getenv('NEO4J_USER_NAME', "")
    __neo4j_password = os.getenv('NEO4J_PASSWD', "")

    def __init__(self, filename: str = "mlmd",
                 pipeline_name="", custom_properties=None, graph: bool = False):
        if custom_properties is None:
            custom_properties = {}
        config = metadata_store_pb2.ConnectionConfig()
        config.sqlite.filename_uri = filename
        self.store = metadata_store.MetadataStore(config)
        self.child_context = None
        self.execution = None
        self.execution_name = ""
        self.execution_command = ""
        self.metrics = {}
        self.input_artifacts = []
        self.execution_label_props = {}
        self.graph = graph
        self.parent_context = get_or_create_parent_context(store=self.store, pipeline=pipeline_name,
                                                           custom_properties=custom_properties)
        if graph:
            self.driver = graph_wrapper.GraphDriver(Cmf.__neo4j_uri, Cmf.__neo4j_user, Cmf.__neo4j_password)
            self.driver.create_pipeline_node(pipeline_name, self.parent_context.id, custom_properties)

    def __del__(self):
        if self.graph:
            self.driver.close()

    def create_context(self, pipeline_stage: str, custom_properties: {} = None) -> mlpb.Context:
        custom_props = {} if custom_properties is None else custom_properties
        pipeline_stage = pipeline_stage
        ctx = get_or_create_run_context(self.store, pipeline_stage, custom_props)
        self.child_context = ctx
        associate_child_to_parent_context(store=self.store, parent_context=self.parent_context,
                                          child_context=ctx)
        if self.graph:
            self.driver.create_stage_node(pipeline_stage, self.parent_context, ctx.id, custom_props)
        return ctx

    def create_execution(self, execution_type: str,
                         custom_properties: {} = None) -> mlpb.Execution:
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
        self.execution_label_props["Execution_Name"] = execution_type + ":" + str(self.execution.id)
        self.execution_label_props["execution_command"] = str(sys.argv)
        if self.graph:
            self.driver.create_execution_node(self.execution_name, self.child_context.id, self.parent_context,
                                              str(sys.argv), self.execution.id, custom_props)
        return self.execution

    def update_execution(self, execution_id: int):
        self.execution = self.store.get_executions_by_id([execution_id])[0]
        if self.execution is None:
            print("Error - no execution id")
            exit()
        execution_type = self.store.get_execution_types_by_id([self.execution.type_id])[0]

        self.execution_name = str(self.execution.id) + "," + execution_type.name
        self.execution_command = self.execution.properties["Execution"]
        self.execution_label_props["Execution_Name"] = execution_type.name + ":" + str(self.execution.id)
        self.execution_label_props["execution_command"] = self.execution.properties["Execution"].string_value
        if self.graph:
            self.driver.create_execution_node(self.execution_name, self.child_context.id, self.parent_context,
                                              self.execution.properties["Execution"].string_value,
                                              self.execution.id, {})
        return self.execution

    def merge_created_execution(self, execution_type: str, execution_cmd: str,
                         custom_properties: {} = None) -> mlpb.Execution:
        #Initializing the execution related fields
        self.metrics = {}
        self.input_artifacts = []
        self.execution_label_props = {}
        custom_props = {} if custom_properties is None else custom_properties
        git_repo = git_get_repo()
        git_start_commit = git_get_commit()
        self.execution = create_new_execution_in_existing_run_context \
            (store=self.store,
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
        self.execution_label_props["Execution_Name"] = execution_type + ":" + str(self.execution.id)
        self.execution_label_props["execution_command"] = execution_cmd
        if self.graph:
            self.driver.create_execution_node(self.execution_name, self.child_context.id, self.parent_context,
                                              str(sys.argv), self.execution.id, custom_props)
        return self.execution
    
    def log_dvc_lock(self, file_path: str):
        return commit_dvc_lock_file(file_path, self.execution.id)

    def log_dataset(self, url: str, event: str, custom_properties: {} = None) -> mlpb.Artifact:
        custom_props = {} if custom_properties is None else custom_properties
        git_repo = git_get_repo()
        name = re.split('/', url)[-1]
        event_type = metadata_store_pb2.Event.Type.OUTPUT
        existing_artifact = []
        if event.lower() == "input":
            event_type = metadata_store_pb2.Event.Type.INPUT

        dataset_commit = commit_output(url, self.execution.id)
        c_hash = dvc_get_hash(url)

        unique_name = url + ":" + c_hash
        dvc_url =  dvc_get_url(url)
        print(dvc_url)

        if c_hash and c_hash.strip:
            existing_artifact.extend(self.store.get_artifacts_by_uri(c_hash))

        # To Do - What happens when uri is the same but names are different
        if existing_artifact and len(existing_artifact) != 0:
            existing_artifact = existing_artifact[0]

            # Quick fix- Updating only the name
            if custom_properties is not None:
                self.update_existing_artifact(existing_artifact, custom_properties)
            uri = c_hash
            artifact = link_execution_to_artifact(store=self.store,
                                                  execution_id=self.execution.id,
                                                  uri=uri,
                                                  input_name=url,
                                                  event_type=event_type)
        else:
            # if((existing_artifact and len(existing_artifact )!= 0) and c_hash != ""):
            #   url = url + ":" + str(self.execution.id)
            uri = c_hash if c_hash and c_hash.strip() else str(uuid.uuid1())
            artifact = create_new_artifact_event_and_attribution \
                (store=self.store,
                 execution_id=self.execution.id,
                 context_id=self.child_context.id,
                 uri=uri,
                 name=unique_name,
                 type_name="Dataset",
                 event_type=event_type,
                 properties={"git_repo": str(git_repo), "Commit": str(dataset_commit), "url":str(dvc_url)},
                 artifact_type_properties={"git_repo": metadata_store_pb2.STRING,
                                           "Commit": metadata_store_pb2.STRING,
                                           "url":metadata_store_pb2.STRING
                                           },
                 custom_properties=custom_props,
                 milliseconds_since_epoch=int(time.time() * 1000),
                 )
        custom_props["git_repo"] = git_repo
        custom_props["Commit"] = dataset_commit
        custom_props["url"] = dvc_url
        self.execution_label_props["git_repo"] = git_repo
        self.execution_label_props["Commit"] = dataset_commit

        if self.graph:
            self.driver.create_dataset_node(name, url, uri, event, self.execution.id, self.parent_context, custom_props)
            if event.lower() == "input":
                self.input_artifacts.append({"Name": name, "Path": url, "URI": uri, "Event": event.lower(),
                                             "Execution_Name": self.execution_name,
                                             "Type": "Dataset", "Execution_Command": self.execution_command,
                                             "Pipeline_Id": self.parent_context.id,
                                             "Pipeline_Name": self.parent_context.name})
                self.driver.create_execution_links(uri, name, "Dataset")
            else:
                child_artifact = {"Name": name, "Path": url, "URI": uri, "Event": event.lower(),
                                  "Execution_Name": self.execution_name,
                                  "Type": "Dataset", "Execution_Command": self.execution_command,
                                  "Pipeline_Id": self.parent_context.id, "Pipeline_Name": self.parent_context.name}
                self.driver.create_artifact_relationships(self.input_artifacts, child_artifact,
                                                          self.execution_label_props)
        return artifact

    def log_dataset_with_version(self, url: str, version: str,  event: str,
                                 custom_properties: {} = None) -> mlpb.Artifact:
        custom_props = {} if custom_properties is None else custom_properties
        git_repo = git_get_repo()
        name = re.split('/', url)[-1]
        event_type = metadata_store_pb2.Event.Type.OUTPUT
        existing_artifact = []
        c_hash = version
        if event.lower() == "input":
            event_type = metadata_store_pb2.Event.Type.INPUT

        # dataset_commit = commit_output(url, self.execution.id)

        dataset_commit = version
        url = url + ":" + c_hash
        #To do - dvc_url(s3_url)
        if c_hash and c_hash.strip:
            existing_artifact.extend(self.store.get_artifacts_by_uri(c_hash))

        # To Do - What happens when uri is the same but names are different
        if existing_artifact and len(existing_artifact) != 0:
            existing_artifact = existing_artifact[0]

            # Quick fix- Updating only the name
            if custom_properties is not None:
                self.update_existing_artifact(existing_artifact, custom_properties)
            uri = c_hash
            artifact = link_execution_to_artifact(store=self.store,
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
             properties={"git_repo": str(git_repo), "Commit": str(dataset_commit)},
             artifact_type_properties={"git_repo": metadata_store_pb2.STRING,
                                       "Commit": metadata_store_pb2.STRING
                                       },
             custom_properties=custom_props,
             milliseconds_since_epoch=int(time.time() * 1000),
             )
        custom_props["git_repo"] = git_repo
        custom_props["Commit"] = dataset_commit
        self.execution_label_props["git_repo"] = git_repo
        self.execution_label_props["Commit"] = dataset_commit

        if self.graph:
            self.driver.create_dataset_node(name, url, uri, event, self.execution.id, self.parent_context, custom_props)
            if event.lower() == "input":
                self.input_artifacts.append({"Name": name, "Path": url, "URI": uri, "Event": event.lower(),
                                             "Execution_Name": self.execution_name,
                                             "Type": "Dataset", "Execution_Command": self.execution_command,
                                             "Pipeline_Id": self.parent_context.id,
                                             "Pipeline_Name": self.parent_context.name})
                self.driver.create_execution_links(uri, name, "Dataset")
            else:
                child_artifact = {"Name": name, "Path": url, "URI": uri, "Event": event.lower(),
                                  "Execution_Name": self.execution_name,
                                  "Type": "Dataset", "Execution_Command": self.execution_command,
                                  "Pipeline_Id": self.parent_context.id, "Pipeline_Name": self.parent_context.name}
                self.driver.create_artifact_relationships(self.input_artifacts, child_artifact,
                                                          self.execution_label_props)
        return artifact

    # Add the model to dvc do a git commit and store the commit id in MLMD
    def log_model_with_version(self, path: str, event: str, props=None,
                  custom_properties=None) -> object:

        if custom_properties is None:
            custom_properties = {}
        custom_props = {} if custom_properties is None else custom_properties
        name = re.split('/', path)[-1]
        event_type = metadata_store_pb2.Event.Type.OUTPUT
        existing_artifact = []
        if event.lower() == "input":
            event_type = metadata_store_pb2.Event.Type.INPUT

        props["commit"] = "" # To do get from incoming data 
        c_hash = props["uri"]
        print(c_hash)
        # If connecting to an existing artifact - The name of the artifact is used as path/steps/key
        model_uri = path + ":" + c_hash
        #dvc_url = dvc_get_url(path, False)
        url = props["url"]
        #uri = ""
        if c_hash and c_hash.strip():
            uri = c_hash.strip()
            existing_artifact.extend(self.store.get_artifacts_by_uri(uri))
        else:
            raise RuntimeError("Model commit failed, Model uri empty")

        if existing_artifact and len(existing_artifact) != 0 and event_type == metadata_store_pb2.Event.Type.INPUT:
            artifact = link_execution_to_artifact(store=self.store,
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
                properties={"model_framework": str("Default"),
                            "model_type": str("Default"),
                            "model_name": str("Default"),
                            "Commit": str("Default"),
                            "url": str(url)},
                artifact_type_properties={"model_framework": metadata_store_pb2.STRING,
                                          "model_type": metadata_store_pb2.STRING,
                                          "model_name": metadata_store_pb2.STRING,
                                          "Commit": metadata_store_pb2.STRING,
                                          "url":metadata_store_pb2.STRING,
                                          },
                custom_properties=custom_props,
                milliseconds_since_epoch=int(time.time() * 1000),
            )
        # custom_properties["Commit"] = model_commit
        custom_props["url"] = url
        self.execution_label_props["Commit"] = props["commit"]
        if self.graph:
            self.driver.create_model_node(model_uri, uri, event, self.execution.id, self.parent_context, custom_props)
            if event.lower() == "input":

                self.input_artifacts.append(
                    {"Name": model_uri, "URI": uri, "Event": event.lower(), "Execution_Name": self.execution_name,
                     "Type": "Model", "Execution_Command": self.execution_command,
                     "Pipeline_Id": self.parent_context.id, "Pipeline_Name": self.parent_context.name})
                self.driver.create_execution_links(uri, model_uri, "Model")
            else:

                child_artifact = {"Name": model_uri, "URI": uri, "Event": event.lower(),
                                  "Execution_Name": self.execution_name,
                                  "Type": "Model", "Execution_Command": self.execution_command,
                                  "Pipeline_Id": self.parent_context.id, "Pipeline_Name": self.parent_context.name}
                self.driver.create_artifact_relationships(self.input_artifacts, child_artifact,
                                                          self.execution_label_props)

        return artifact

    # Add the model to dvc do a git commit and store the commit id in MLMD
    def log_model(self, path: str, event: str, model_framework: str, model_type: str, model_name: str,
                  custom_properties=None) -> object:

        if custom_properties is None:
            custom_properties = {}
        custom_props = {} if custom_properties is None else custom_properties
        # name = re.split('/', path)[-1]
        event_type = metadata_store_pb2.Event.Type.OUTPUT
        existing_artifact = []
        if event.lower() == "input":
            event_type = metadata_store_pb2.Event.Type.INPUT

        model_commit = commit_output(path, self.execution.id)
        c_hash = dvc_get_hash(path)

        # If connecting to an existing artifact - The name of the artifact is used as path/steps/key
        model_uri = path + ":" + c_hash
        dvc_url = dvc_get_url(path, False)
        url = dvc_url
        uri = ""
        if c_hash and c_hash.strip():
            uri = c_hash.strip()
            existing_artifact.extend(self.store.get_artifacts_by_uri(uri))
        else:
            raise RuntimeError("Model commit failed, Model uri empty")

        if existing_artifact and len(existing_artifact) != 0 and event_type == metadata_store_pb2.Event.Type.INPUT:
            artifact = link_execution_to_artifact(store=self.store,
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
                properties={"model_framework": str(model_framework),
                            "model_type": str(model_type),
                            "model_name": str(model_name),
                            "Commit": str(model_commit),
                            "url": str(url)},
                artifact_type_properties={"model_framework": metadata_store_pb2.STRING,
                                          "model_type": metadata_store_pb2.STRING,
                                          "model_name": metadata_store_pb2.STRING,
                                          "Commit": metadata_store_pb2.STRING,
                                          "url":metadata_store_pb2.STRING,
                                          },
                custom_properties=custom_props,
                milliseconds_since_epoch=int(time.time() * 1000),
            )
        # custom_properties["Commit"] = model_commit
        custom_props["url"] = url
        self.execution_label_props["Commit"] = model_commit
        if self.graph:
            self.driver.create_model_node(model_uri, uri, event, self.execution.id, self.parent_context, custom_props)
            if event.lower() == "input":

                self.input_artifacts.append(
                    {"Name": model_uri, "URI": uri, "Event": event.lower(), "Execution_Name": self.execution_name,
                     "Type": "Model", "Execution_Command": self.execution_command,
                     "Pipeline_Id": self.parent_context.id, "Pipeline_Name": self.parent_context.name})
                self.driver.create_execution_links(uri, model_uri, "Model")
            else:

                child_artifact = {"Name": model_uri, "URI": uri, "Event": event.lower(),
                                  "Execution_Name": self.execution_name,
                                  "Type": "Model", "Execution_Command": self.execution_command,
                                  "Pipeline_Id": self.parent_context.id, "Pipeline_Name": self.parent_context.name}
                self.driver.create_artifact_relationships(self.input_artifacts, child_artifact,
                                                          self.execution_label_props)

        return artifact

    def log_execution_metrics(self, metrics_name: str, custom_properties: {} = None) -> object:

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
            event_type=metadata_store_pb2.Event.Type.OUTPUT,
            properties={"metrics_name": metrics_name},
            artifact_type_properties={"metrics_name": metadata_store_pb2.STRING},
            custom_properties=custom_props,
            milliseconds_since_epoch=int(time.time() * 1000),
        )
        if self.graph:
            # To do create execution_links
            self.driver.create_metrics_node(metrics_name, uri, "output", self.execution.id, self.parent_context,
                                            custom_props)
            child_artifact = {"Name": metrics_name, "URI": uri, "Event": "output",
                              "Execution_Name": self.execution_name,
                              "Type": "Metrics", "Execution_Command": self.execution_command,
                              "Pipeline_Id": self.parent_context.id, "Pipeline_Name": self.parent_context.name}
            self.driver.create_artifact_relationships(self.input_artifacts, child_artifact, self.execution_label_props)
        return metrics

    # Log to parquet file
    def log_metric(self, metrics_name: str, custom_properties: {} = None):
        if metrics_name in self.metrics.keys():
            key = max((self.metrics[metrics_name]).keys()) + 1
            self.metrics[metrics_name][key] = custom_properties
        else:
            self.metrics[metrics_name] = {}
            self.metrics[metrics_name][1] = custom_properties

    # Commit the metrics file associated with the metrics id to dvc and git and
    # store the artifact in mlmd
    def commit_metrics(self, metrics_name: str):
        metrics_df = pd.DataFrame.from_dict(self.metrics[metrics_name], orient='index')
        metrics_df.index.names = ['SequenceNumber']
        metrics_df.to_parquet(metrics_name)
        metrics_commit = commit_output(metrics_name, self.execution.id)
        uri = dvc_get_hash(metrics_name)
        url = dvc_get_url(metrics_name, False)
        name = metrics_name + ":" + uri + ":" + str(self.execution.id)
        custom_props = {"Name": metrics_name, "Commit": metrics_commit, "url":url}
        metrics = create_new_artifact_event_and_attribution(
            store=self.store,
            execution_id=self.execution.id,
            context_id=self.child_context.id,
            uri=uri,
            name=name,
            type_name="Step_Metrics",
            event_type=metadata_store_pb2.Event.Type.OUTPUT,
            custom_properties=custom_props,
            milliseconds_since_epoch=int(time.time() * 1000),
        )
        if self.graph:
            self.driver.create_metrics_node(name, uri, "output", self.execution.id, self.parent_context,
                                            custom_props)
            child_artifact = {"Name": name, "URI": uri, "Event": "output", "Execution_Name": self.execution_name,
                              "Type": "Metrics", "Execution_Command": self.execution_command,
                              "Pipeline_Id": self.parent_context.id}
            self.driver.create_artifact_relationships(self.input_artifacts, child_artifact, self.execution_label_props)
        return metrics

    def log_validation_output(self, version: str, custom_properties: {} = None) -> object:
        uri = str(uuid.uuid1())
        return create_new_artifact_event_and_attribution(
            store=self.store,
            execution_id=self.execution.id,
            context_id=self.child_context.id,
            uri=uri,
            name=uri,
            type_name="Validation_output",
            event_type=metadata_store_pb2.Event.Type.INTERNAL_OUTPUT,
            properties={"version": version},

            artifact_type_properties={"version": metadata_store_pb2.STRING},
            custom_properties=custom_properties,
            milliseconds_since_epoch=int(time.time() * 1000),
        )

    def update_existing_artifact(self, artifact: mlpb.Artifact, custom_props: {}):
        for key, value in custom_props.items():
            if isinstance(value, int):
                artifact.custom_properties[key].int_value = value
            else:
                artifact.custom_properties[key].string_value = str(value)
        put_artifact(self.store, artifact)

    def get_artifact(self, artifact_id: int) -> metadata_store_pb2.Artifact:
        return get_artifacts_by_id(self.store, [artifact_id])[0]

    def update_model_output(self, artifact: metadata_store_pb2.Artifact):
        put_artifact(self.store, artifact)

    def create_dataslice(self, name: str) -> object:
        return Cmf.dataslice(name, self)

    def read_dataslice(self, name: str) -> pd.DataFrame:
        # To do checkout if not there
        df = pd.read_parquet(name)
        return df

    # To do - Once update the hash and the new version should be updated in the mlmd
    def update_dataslice(self, name: str, record: str, custom_props: {}):
        df = pd.read_parquet(name)
        temp_dict = df.to_dict('index')
        temp_dict[record].update(custom_props)
        dataslice_df = pd.DataFrame.from_dict(temp_dict, orient='index')
        dataslice_df.index.names = ['Path']
        dataslice_df.to_parquet(name)

    class dataslice(object):
        def __init__(self, name: str, writer, props: {} = None):
            self.props = {} if props is None else props
            self.name = name
            self.writer = writer

        def add_data(self, path, custom_props: {} = None):
            self.props[path] = {}
            self.props[path]['hash'] = dvc_get_hash(path)
            if custom_props:
                for k, v in custom_props.items():
                    self.props[path][k] = v

        """
        Place holder for updating back to mlmd

        def update_data(self, path, custom_props:{}):
            for k ,v in custom_props.items():
                self.props[path][k] = v
        """

        def commit(self, custom_props: {} = None):
            git_repo = git_get_repo()
            dataslice_df = pd.DataFrame.from_dict(self.props, orient='index')
            dataslice_df.index.names = ['Path']
            dataslice_df.to_parquet(self.name)
            existing_artifact = []

            dataslice_commit = commit_output(self.name, self.writer.execution.id)
            c_hash = dvc_get_hash(self.name)
            remote = dvc_get_url(self.name)
            if c_hash and c_hash.strip():
                existing_artifact.extend(self.writer.store.get_artifacts_by_uri(c_hash))
            if existing_artifact and len(existing_artifact) != 0:
                print("Adding to existing data slice")
                _ = link_execution_to_input_artifact(store=self.writer.store,
                                                     execution_id=self.writer.execution.id,
                                                     uri=c_hash,
                                                     input_name=self.name + ":" + c_hash)
            else:
                props = {"Commit": dataslice_commit, "git_repo": git_repo, "Remote": remote}
                custom_properties = props.update(custom_props) if custom_props else props
                create_new_artifact_event_and_attribution(
                    store=self.writer.store,
                    execution_id=self.writer.execution.id,
                    context_id=self.writer.child_context.id,
                    uri=c_hash,
                    name=self.name + ":" + c_hash,
                    type_name="Dataslice",
                    event_type=metadata_store_pb2.Event.Type.OUTPUT,
                    custom_properties=custom_properties,
                    milliseconds_since_epoch=int(time.time() * 1000),
                )
            return None

        """Temporary code"""

        def materialize(self, name):
            slicedir = name + "-" + "dir"
            os.mkdir(slicedir)
            df = pd.read_parquet(name)
            for index, row in df.iterrows():
                print(index)
                first, middle, last = str(index).split("/")
                print(last)
                os.symlink(str(index), slicedir + "/ " + last)
