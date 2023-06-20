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

import pandas as pd
from ml_metadata.metadata_store import metadata_store
from ml_metadata.proto import metadata_store_pb2 as mlpb
from cmflib.mlmd_objects import CONTEXT_LIST
import json
import typing as t



class CmfQuery(object):
    def __init__(self, filepath: str = "mlmd"):
        config = mlpb.ConnectionConfig()
        config.sqlite.filename_uri = filepath
        self.store = metadata_store.MetadataStore(config)

    def _transform_to_dataframe(self, node):
        d = {"id": node.id}
        for k, v in node.properties.items():
            if v.HasField('string_value'):
                d[k] = v.string_value
            elif v.HasField('int_value'):
                d[k] = v.int_value
            else:
                d[k] = v.double_value

        for k, v in node.custom_properties.items():
            if v.HasField('string_value'):
                d[k] = v.string_value
            elif v.HasField('int_value'):
                d[k] = v.int_value
            else:
                d[k] = v.double_value

        df = pd.DataFrame(d, index=[0, ])
        return df

    def get_pipeline_id(self, pipeline_name: str) -> int:
        contexts = self.store.get_contexts_by_type("Parent_Context")
        for ctx in contexts:
            if ctx.name == pipeline_name:
                return ctx.id
        return -1


    def get_pipeline_names(self) -> t.List:
        names = []
        contexts = self.store.get_contexts_by_type("Parent_Context")
        for ctx in contexts:
            names.append(ctx.name)
        return names

    def get_pipeline_stages(self, pipeline_name: str) -> []:
        stages = []
        contexts = self.store.get_contexts_by_type("Parent_Context")
        for ctx in contexts:
            if ctx.name == pipeline_name:
                child_contexts = self.store.get_children_contexts_by_context(ctx.id)
                for cc in child_contexts:
                    stages.append(cc.name)
        return stages

    def get_all_exe_in_stage(self, stage_name: str) -> []:
        df = pd.DataFrame()
        contexts = self.store.get_contexts_by_type("Parent_Context")
        executions = None
        for ctx in contexts:
            child_contexts = self.store.get_children_contexts_by_context(ctx.id)
            for cc in child_contexts:
                if cc.name == stage_name:
                    executions = self.store.get_executions_by_context(cc.id)
        return executions


    def get_all_executions_in_stage(self, stage_name: str) -> pd.DataFrame:
        df = pd.DataFrame()
        contexts = self.store.get_contexts_by_type("Parent_Context")
        for ctx in contexts:
            child_contexts = self.store.get_children_contexts_by_context(ctx.id)
            for cc in child_contexts:
                if cc.name == stage_name:
                    executions = self.store.get_executions_by_context(cc.id)
                    for exe in executions:
                        d1 = self._transform_to_dataframe(exe)
                        # df = df.append(d1, sort=True, ignore_index=True)
                        df = pd.concat([df, d1], sort=True, ignore_index=True)

        return df

    def get_artifact_df(self, node):
        d = {"id": node.id, "type": self.store.get_artifact_types_by_id([node.type_id])[0].name, "uri": node.uri,
             "name": node.name, "create_time_since_epoch": node.create_time_since_epoch,
             "last_update_time_since_epoch": node.last_update_time_since_epoch}
        for k, v in node.properties.items():
            if v.HasField('string_value'):
                d[k] = v.string_value
            elif v.HasField('int_value'):
                d[k] = v.int_value
            else:
                d[k] = v.double_value
        for k, v in node.custom_properties.items():
            if v.HasField('string_value'):
                d[k] = v.string_value
            elif v.HasField('int_value'):
                d[k] = v.int_value
            else:
                d[k] = v.double_value
        df = pd.DataFrame(d, index=[0, ])
        return df

    def get_all_artifacts(self) -> t.List:
        artifact_list = []
        artifacts = self.store.get_artifacts()
        for art in artifacts:
            name = art.name
            artifact_list.append(name)
        return artifact_list

    def get_artifact(self, name: str):
        artifact = None
        artifacts = self.store.get_artifacts()
        for art in artifacts:
            if art.name == name:
                artifact = art
                break
        return self.get_artifact_df(artifact)

    def get_all_artifacts_for_execution(self, execution_id: int) -> pd.DataFrame: # change here
        df = pd.DataFrame()
        input_artifacts = []
        output_artifacts = []
        events = self.store.get_events_by_execution_ids([execution_id])
        for event in events:
            if event.type == mlpb.Event.Type.INPUT:  # 3 - INPUT #4 - Output
                input_artifacts.extend(self.store.get_artifacts_by_id([event.artifact_id]))
            else:
                output_artifacts.extend(self.store.get_artifacts_by_id([event.artifact_id]))
        for art in input_artifacts:
            d1 = self.get_artifact_df(art)
            d1["event"] = "INPUT"
            #df = df.append(d1, sort=True, ignore_index=True)
            df = pd.concat([df, d1], sort=True, ignore_index=True)
        for art in output_artifacts:
            d1 = self.get_artifact_df(art)
            d1["event"] = "OUTPUT"
            #df = df.append(d1, sort=True, ignore_index=True)
            df = pd.concat([df, d1], sort=True, ignore_index=True)
        return df

    def get_all_executions_for_artifact(self, artifact_name: str) -> pd.DataFrame:
        selected_artifact = None
        linked_execution = {}
        events = []
        df = pd.DataFrame()
        artifacts = self.store.get_artifacts()
        for art in artifacts:
            if art.name == artifact_name:
                selected_artifact = art
                break
        if selected_artifact is not None:
            events = self.store.get_events_by_artifact_ids([selected_artifact.id])

        for evt in events:
            linked_execution["Type"] = "INPUT" if evt.type == mlpb.Event.Type.INPUT else "OUTPUT"
            linked_execution["execution_id"] = evt.execution_id
            linked_execution["execution_name"] = self.store.get_executions_by_id([evt.execution_id])[0].name
            ctx = self.store.get_contexts_by_execution(evt.execution_id)[0]
            linked_execution["stage"] = self.store.get_contexts_by_execution(evt.execution_id)[0].name

            linked_execution["pipeline"] = self.store.get_parent_contexts_by_context(ctx.id)[0].name
            d1 = pd.DataFrame(linked_execution, index=[0, ])
            #df = df.append(d1, sort=True, ignore_index=True)
            df = pd.concat([df, d1], sort=True, ignore_index=True)

        return df

    def get_one_hop_child_artifacts(self, artifact_name: str) -> pd.DataFrame:
        df = pd.DataFrame()

        artifact = None
        artifacts = self.store.get_artifacts()
        for art in artifacts:
            if artifact_name.strip() == art.name:
                artifact = art
                break
        # Get a list of artifacts within a 1-hop of the artifacts of interest
        artifact_ids = [artifact.id]
        executions_ids = set(
            event.execution_id
            for event in self.store.get_events_by_artifact_ids(artifact_ids)
            if event.type == mlpb.Event.INPUT)
        artifacts_ids = set(
            event.artifact_id
            for event in self.store.get_events_by_execution_ids(executions_ids)
            if event.type == mlpb.Event.OUTPUT)
        artifacts = self.store.get_artifacts_by_id(artifacts_ids)
        for art in artifacts:
            d1 = self.get_artifact_df(art)
            #df = df.append(d1, sort=True, ignore_index=True)
            df = pd.concat([df, d1], sort=True, ignore_index=True)
        return df

    def get_all_child_artifacts(self, artifact_name: str) -> pd.DataFrame:
        df = pd.DataFrame()
        d1 = self.get_one_hop_child_artifacts(artifact_name)
        #df = df.append(d1, sort=True, ignore_index=True)
        df = pd.concat([df, d1], sort=True, ignore_index=True)
        for row in d1.itertuples():
            d1 = self.get_all_child_artifacts(row.name)
            #df = df.append(d1, sort=True, ignore_index=True)
            df = pd.concat([df, d1], sort=True, ignore_index=True)
        df = df.drop_duplicates(subset=None, keep='first', inplace=False)
        return df

    def get_one_hop_parent_artifacts(self, artifact_name: str) -> pd.DataFrame:
        df = pd.DataFrame()

        artifact = None
        artifacts = self.store.get_artifacts()
        for art in artifacts:
            if artifact_name in art.name:
                artifact = art
                break
        # Get a list of artifacts within a 1-hop of the artifacts of interest
        artifact_ids = [artifact.id]
        executions_ids = set(
            event.execution_id
            for event in self.store.get_events_by_artifact_ids(artifact_ids)
            if event.type == mlpb.Event.OUTPUT)
        artifacts_ids = set(
            event.artifact_id
            for event in self.store.get_events_by_execution_ids(executions_ids)
            if event.type == mlpb.Event.INPUT)
        artifacts = self.store.get_artifacts_by_id(artifacts_ids)
        for art in artifacts:
            d1 = self.get_artifact_df(art)
            #df = df.append(d1, sort=True, ignore_index=True)
            df = pd.concat([df, d1], sort=True, ignore_index=True)
        return df

    def get_all_parent_artifacts(self, artifact_name: str) -> pd.DataFrame:
        df = pd.DataFrame()
        d1 = self.get_one_hop_parent_artifacts(artifact_name)
        #df = df.append(d1, sort=True, ignore_index=True)
        df = pd.concat([df, d1], sort=True, ignore_index=True)
        for row in d1.itertuples():
            d1 = self.get_all_parent_artifacts(row.name)
            #df = df.append(d1, sort=True, ignore_index=True)
            df = pd.concat([df, d1], sort=True, ignore_index=True)
        df = df.drop_duplicates(subset=None, keep='first', inplace=False)
        return df

    def get_all_parent_executions(self, artifact_name:str)-> pd.DataFrame:
        df = self.get_all_parent_artifacts(artifact_name)
        artifact_ids = df.id.values.tolist()

        executions_ids = set(
            event.execution_id
            for event in self.store.get_events_by_artifact_ids(artifact_ids)
            if event.type == mlpb.Event.OUTPUT)
        executions = self.store.get_executions_by_id(executions_ids)

        df = pd.DataFrame()
        for exe in executions:
            d1 = self._transform_to_dataframe(exe)
            # df = df.append(d1, sort=True, ignore_index=True)
            df = pd.concat([df, d1], sort=True, ignore_index=True)
        return df

    def find_producer_execution(self, artifact_name: str) -> object:
        artifact = None
        artifacts = self.store.get_artifacts()
        for art in artifacts:
            if art.name == artifact_name:
                artifact = art
                break

        executions_ids = set(
            event.execution_id
            for event in self.store.get_events_by_artifact_ids([artifact.id])
            if event.type == mlpb.Event.OUTPUT)
        return self.store.get_executions_by_id(executions_ids)[0]
    
    def get_metrics(self, metrics_name:str) ->pd.DataFrame:
        metric = None
        metrics = self.store.get_artifacts_by_type("Step_Metrics")
        for m in metrics:
            if m.name == metrics_name:
                metric = m
                break
        if metric is None:
            print("Error : The given metrics does not exist")
            return None
        name = ""
        for k, v in metric.custom_properties.items():
            if k == "Name":
                name = v
                break
        df = pd.read_parquet(name)
        return df
    
    def read_dataslice(self, name: str) -> pd.DataFrame:
        """Reads the dataslice"""
        # To do checkout if not there
        df = pd.read_parquet(name)
        return df
        



    @staticmethod
    def __get_node_properties(node) -> dict:
        # print(node)
        node_dict = {}
        for attr in dir(node):
            if attr in CONTEXT_LIST:
                if attr == "properties":
                    node_dict["properties"] = CmfQuery.__get_properties(node)
                elif attr == "custom_properties":
                    node_dict["custom_properties"] = CmfQuery.__get_customproperties(
                        node
                    )
                else:
                    node_dict[attr] = node.__getattribute__(attr)

        # print(node_dict)
        return node_dict

    @staticmethod
    def __get_properties(node) -> dict:
        prop_dict = {}
        for k, v in node.properties.items():
            if v.HasField("string_value"):
                prop_dict[k] = v.string_value
            elif v.HasField("int_value"):
                prop_dict[k] = v.int_value
            else:
                prop_dict[k] = v.double_value
        return prop_dict

    @staticmethod
    def __get_customproperties(node) -> dict:
        prop_dict = {}
        for k, v in node.custom_properties.items():
            if k == "type":
                k = "user_type"
            if v.HasField("string_value"):
                prop_dict[k] = v.string_value
            elif v.HasField("int_value"):
                prop_dict[k] = v.int_value
            else:
                prop_dict[k] = v.double_value
        return prop_dict

    def dumptojson(self, pipeline_name: str, exec_id):
        mlmd_json = {}
        mlmd_json["Pipeline"] = []
        contexts = self.store.get_contexts_by_type("Parent_Context")
        for ctx in contexts:
            if ctx.name == pipeline_name:
                ctx_dict = CmfQuery.__get_node_properties(ctx)
                ctx_dict["stages"] = []
                stages = self.store.get_children_contexts_by_context(ctx.id)
                for stage in stages:
                    stage_dict = CmfQuery.__get_node_properties(stage)
                    # ctx["stages"].append(stage_dict)
                    stage_dict["executions"] = []
                    executions = self.store.get_executions_by_context(stage.id)
                    if exec_id is None:
                        list_executions = [exe for exe in executions]
                    elif exec_id is not None:
                        list_executions = [
                            exe for exe in executions if exe.id == int(exec_id)
                        ]
                    else:
                        return "Invalid execution id given."
                    for exe in list_executions:
                        exe_dict = CmfQuery.__get_node_properties(exe)
                        exe_type = self.store.get_execution_types_by_id([exe.type_id])
                        exe_dict["type"] = exe_type[0].name
                        exe_dict["events"] = []
                        # name will be an empty string for executions that are created with 
                        # create new execution as true(default)
                        # In other words name property will there only for execution 
                        # that are created with create new execution flag set to false(special case)
                        exe_dict["name"] = exe.name if exe.name != "" else ""
                        events = self.store.get_events_by_execution_ids([exe.id])
                        for evt in events:
                            evt_dict = CmfQuery.__get_node_properties(evt)
                            artifact = self.store.get_artifacts_by_id([evt.artifact_id])
                            if artifact is not None:
                                artifact_type = self.store.get_artifact_types_by_id(
                                    [artifact[0].type_id]
                                )
                                artifact_dict = CmfQuery.__get_node_properties(
                                    artifact[0]
                                )
                                artifact_dict["type"] = artifact_type[0].name
                                evt_dict["artifact"] = artifact_dict
                            exe_dict["events"].append(evt_dict)
                        stage_dict["executions"].append(exe_dict)
                    ctx_dict["stages"].append(stage_dict)
                mlmd_json["Pipeline"].append(ctx_dict)
                json_str = json.dumps(mlmd_json)
                # json_str = jsonpickle.encode(ctx_dict)
                return json_str

    '''def materialize(self, artifact_name:str):
       artifacts = self.store.get_artifacts()
       for art in artifacts:
           if art.name == artifact_name:
               selected_artifact = art
               break
       for k, v in selected_artifact.custom_properties.items():
           if (k == "Path"):
               path = v
           elif (k == "git_repo"):
               git_repo = v
           elif (k == "Revision"):
               rev = v
           elif (remote == "Remote"):
               remote = v
       
       Cmf.materialize(path, git_repo, rev, remote)'''
    
