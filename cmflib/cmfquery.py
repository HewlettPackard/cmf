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


class CmfQuery(object):
    def __init__(self, filepath: str = "mlmd"):
        config = mlpb.ConnectionConfig()
        config.sqlite.filename_uri = filepath
        self.store = metadata_store.MetadataStore(config)

    def _transform_to_dataframe(self, node):
        d = {"id": node.id}
        for k, v in node.properties.items():
            d[k] = v.string_value if v.HasField('string_value') else v.int_value
        for k, v in node.custom_properties.items():
            d[k] = v.string_value if v.HasField('string_value') else v.int_value
        df = pd.DataFrame(d, index=[0, ])
        return df

    def get_pipeline_id(self, pipeline_name: str) -> int:
        contexts = self.store.get_contexts_by_type("Parent_Context")
        for ctx in contexts:
            if ctx.name == pipeline_name:
                return ctx.id

        return -1

    def get_pipeline_stages(self, pipeline_name: str) -> []:
        stages = []
        contexts = self.store.get_contexts_by_type("Parent_Context")
        for ctx in contexts:
            if ctx.name == pipeline_name:
                child_contexts = self.store.get_children_contexts_by_context(ctx.id)
                for cc in child_contexts:
                    stages.append(cc.name)
        return stages

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
            d[k] = v.string_value if v.HasField('string_value') else v.double_value
        for k, v in node.custom_properties.items():
            d[k] = v.string_value if v.HasField('string_value') else v.double_value
        df = pd.DataFrame(d, index=[0, ])
        return df

    def get_artifact(self, name: str):
        artifact = None
        artifacts = self.store.get_artifacts()
        for art in artifacts:
            if art.name == name:
                artifact = art
                break
        return self.get_artifact_df(artifact)

    def get_all_artifacts_for_execution(self, execution_id: int) -> pd.DataFrame:
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
            df = df.append(d1, sort=True, ignore_index=True)
        for art in output_artifacts:
            d1 = self.get_artifact_df(art)
            d1["event"] = "OUTPUT"
            df = df.append(d1, sort=True, ignore_index=True)
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
            df = df.append(d1, sort=True, ignore_index=True)

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
            df = df.append(d1, sort=True, ignore_index=True)
        return df

    def get_all_child_artifacts(self, artifact_name: str) -> pd.DataFrame:
        df = pd.DataFrame()
        d1 = self.get_one_hop_child_artifacts(artifact_name)
        df = df.append(d1, sort=True, ignore_index=True)
        for row in d1.itertuples():
            d1 = self.get_all_child_artifacts(row.name)
            df = df.append(d1, sort=True, ignore_index=True)
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
            df = df.append(d1, sort=True, ignore_index=True)
        return df

    def get_all_parent_artifacts(self, artifact_name: str) -> pd.DataFrame:
        df = pd.DataFrame()
        d1 = self.get_one_hop_parent_artifacts(artifact_name)
        df = df.append(d1, sort=True, ignore_index=True)
        for row in d1.itertuples():
            d1 = self.get_all_parent_artifacts(row.name)
            df = df.append(d1, sort=True, ignore_index=True)
        df = df.drop_duplicates(subset=None, keep='first', inplace=False)
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
