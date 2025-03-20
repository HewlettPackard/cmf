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
from neo4j import GraphDatabase
import typing as t
import re
from ml_metadata.proto import metadata_store_pb2 as mlpb


class GraphDriver:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, 
                                        auth=(user, password),
                                        #notifications_min_severity="OFF" # Suppress warnings on driver level
                                        )
        self.pipeline_id = None
        self.stage_id = None
        self.execution_id = None

    def close(self):
        self.driver.close()

    def create_pipeline_node(self, name: str, uri: int, props=None):
        if props is None:
            props = {}
        pipeline_syntax = self._create_pipeline_syntax(name, props, uri)
        with self.driver.session() as session:
            node = session.write_transaction(
                self._run_transaction, pipeline_syntax)
            self.pipeline_id = node[0]["node_id"]

    def create_stage_node(self, name: str, parent_context: mlpb.Context, stage_id: int, props=None):    # type: ignore  # Context type not recognized by mypy, using ignore to bypass
        if props is None:
            props = {}
        parent_id = parent_context.id
        parent_name = parent_context.name
        stage_syntax = self._create_stage_syntax(
            name, props, stage_id, parent_id, parent_name)
        with self.driver.session() as session:
            node = session.write_transaction(
                self._run_transaction, stage_syntax)
            self.stage_id = node[0]["node_id"]
            pc_syntax = self._create_parent_child_syntax(
                "Pipeline", "Stage", self.pipeline_id, self.stage_id, "contains")
            _ = session.write_transaction(self._run_transaction, pc_syntax)

    def create_execution_node(self, name: str, parent_id: int, pipeline_context: mlpb.Context, command: str,    # type: ignore  # Context type not recognized by mypy, using ignore to bypass
                              execution_id: int,
                              props=None):
        if props is None:
            props = {}
        pipeline_id = pipeline_context.id
        pipeline_name = pipeline_context.name
        execution_syntax = self._create_execution_syntax(
            name, command, props, execution_id, pipeline_id, pipeline_name)
        with self.driver.session() as session:
            node = session.write_transaction(
                self._run_transaction, execution_syntax)
            self.execution_id = node[0]["node_id"]
            pc_syntax = self._create_parent_child_syntax(
                "Stage", "Execution", self.stage_id, self.execution_id, "runs")
            _ = session.write_transaction(self._run_transaction, pc_syntax)

    def create_dataset_node(self, name: str, path: str, uri: str, event: str, execution_id: int,
                            pipeline_context: mlpb.Context, # type: ignore  # Context type not recognized by mypy, using ignore to bypass
                            custom_properties=None):
        if custom_properties is None:
            custom_properties = {}
        pipeline_id = pipeline_context.id
        pipeline_name = pipeline_context.name
        dataset_syntax = self._create_dataset_syntax(
            name, path, uri, pipeline_id, pipeline_name, custom_properties)
        with self.driver.session() as session:
            node = session.write_transaction(
                self._run_transaction, dataset_syntax)
            node_id = node[0]["node_id"]
            pc_syntax = self._create_execution_artifacts_link_syntax(
                "Execution", "Dataset", self.execution_id, node_id, event)
            _ = session.write_transaction(self._run_transaction, pc_syntax)

    def create_env_node(self, name: str, path: str, uri: str, event: str, execution_id: int,
                            pipeline_context: mlpb.Context, custom_properties=None):    # type: ignore  # Context type not recognized by mypy, using ignore to bypass
        if custom_properties is None:
            custom_properties = {}
        pipeline_id = pipeline_context.id
        pipeline_name = pipeline_context.name
        dataset_syntax = self._create_env_syntax(
            name, path, uri, pipeline_id, pipeline_name, custom_properties)
        with self.driver.session() as session:
            node = session.write_transaction(
                self._run_transaction, dataset_syntax)
            node_id = node[0]["node_id"]
            pc_syntax = self._create_execution_artifacts_link_syntax(
                "Execution", "Environment", self.execution_id, node_id, event)
            _ = session.write_transaction(self._run_transaction, pc_syntax)

    def create_dataslice_node(self, name: str, path: str, uri: str, parent_name:str,
                            custom_properties=None):
        if custom_properties is None:
            custom_properties = {}
        dataslice_syntax = self._create_dataslice_syntax(
            name, path, uri, custom_properties)
        with self.driver.session() as session:
            node = session.write_transaction(
                self._run_transaction, dataslice_syntax)
            node_id = node[0]["node_id"]
        p_nid = self._get_node("Dataset", parent_name )
        with self.driver.session() as session:
            pc_syntax = self._create_parent_child_syntax(
                "Dataset", "Dataslice", p_nid, node_id, "contains")
            _ = session.write_transaction(self._run_transaction, pc_syntax)

    def create_links(self, source_path:str, target_path:str, relation:str ):
        source_node_id = self._get_node_with_path("Dataset", source_path)
        target_node_id = self._get_node_with_path("Dataslice", target_path)
        with self.driver.session() as session:
            pc_syntax = self._create_parent_child_syntax("Dataset", "Dataslice", source_node_id, target_node_id, relation)
            _ = session.write_transaction(self._run_transaction, pc_syntax)


    def create_model_node(self, name: str, uri: str, event: str, execution_id: str, pipeline_context: mlpb.Context, # type: ignore  # Context type not recognized by mypy, using ignore to bypass
                          custom_properties=None):
        if custom_properties is None:
            custom_properties = {}
        pipeline_id = pipeline_context.id
        pipeline_name = pipeline_context.name
        model_syntax = self._create_model_syntax(
            name, uri, pipeline_id, pipeline_name, custom_properties)
        with self.driver.session() as session:
            node = session.write_transaction(
                self._run_transaction, model_syntax)
            node_id = node[0]["node_id"]
            pc_syntax = self._create_execution_artifacts_link_syntax(
                "Execution", "Model", self.execution_id, node_id, event)
            _ = session.write_transaction(self._run_transaction, pc_syntax)

    def create_metrics_node(self, name: str, uri: str, event: str, execution_id: int, pipeline_context: mlpb.Context,   # type: ignore  # Context type not recognized by mypy, using ignore to bypass
                            custom_properties=None):
        if custom_properties is None:
            custom_properties = {}
        pipeline_id = pipeline_context.id
        pipeline_name = pipeline_context.name
        metrics_syntax = self._create_metrics_syntax(
            name, uri, event, execution_id, pipeline_id, pipeline_name, custom_properties)
        with self.driver.session() as session:
            node = session.write_transaction(
                self._run_transaction, metrics_syntax)
            node_id = node[0]["node_id"]
            pc_syntax = self._create_execution_artifacts_link_syntax(
                "Execution", "Metrics", self.execution_id, node_id, event)
            _ = session.write_transaction(self._run_transaction, pc_syntax)

    def create_step_metrics_node(self, name: str, uri: str, event: str, execution_id: int, pipeline_context: mlpb.Context,  # type: ignore  # Context type not recognized by mypy, using ignore to bypass
                            custom_properties=None):
        if custom_properties is None:
            custom_properties = {}
        pipeline_id = pipeline_context.id
        pipeline_name = pipeline_context.name
        metrics_syntax = self._create_step_metrics_syntax(
            name, uri, event, execution_id, pipeline_id, pipeline_name, custom_properties)
        with self.driver.session() as session:
            node = session.write_transaction(
                self._run_transaction, metrics_syntax)
            node_id = node[0]["node_id"]
            pc_syntax = self._create_execution_artifacts_link_syntax(
                "Execution", "Step_Metrics", self.execution_id, node_id, event)
            _ = session.write_transaction(self._run_transaction, pc_syntax)

    def create_artifact_relationships(
            self,
            parent_artifacts,
            child_artifact,
            relation_properties):
        #      f = lambda d: d['Event']
        #      res = {k:list(v) for k,v in groupby(sorted(artifacts, key=f), f)}

        #     for v in res["output"]:

        child_artifact_type = child_artifact["Type"]
        child_artifact_uri = child_artifact["URI"]
        child_name = child_artifact["Name"]
        pipeline_id = child_artifact["Pipeline_Id"]
        for k in parent_artifacts:
            parent_artifact_type = k["Type"]
            parent_artifact_uri = k["URI"]
            parent_name = k["Name"]
            relation = re.sub(
                '\W+', '', re.split(",", k["Execution_Name"])[-1])
            pc_syntax = self._create_parent_child_artifacts_syntax(
                parent_artifact_type,
                child_artifact_type,
                parent_artifact_uri,
                child_artifact_uri,
                parent_name,
                child_name,
                pipeline_id,
                relation,
                relation_properties)
            with self.driver.session() as session:
                _ = session.write_transaction(self._run_transaction, pc_syntax)

    def create_execution_links(
            self,
            parent_artifact_uri,
            parent_artifact_name,
            parent_artifact_type):

        parent_execution_query = "MATCH (n:{}".format(
            parent_artifact_type) + "{uri: '" + parent_artifact_uri + "'}) " \
            "<-[:output]-(f:Execution) Return ELEMENTID(f) as id, f.uri as uri"

        already_linked_execution_query = "MATCH (f)-[r:linked]->(e2:Execution) " \
            "WHERE r.uri = '{}' RETURN ELEMENTID(f) as id, f.uri as uri".format(parent_artifact_uri)

        with self.driver.session(notifications_min_severity="OFF") as session: # Supress Warnings on Session level
            execution_parent = session.read_transaction(
                self._run_transaction, parent_execution_query)
            executions = {}

            for record in execution_parent:
                p_id = record["id"]
                executions[str(p_id)] = str(record["uri"])

            linked_executions = session.read_transaction(
                self._run_transaction, already_linked_execution_query)
            linked = {}
            for record in linked_executions:
                linked_id = record["id"]
                linked[str(linked_id)] = str(record["uri"])
            unlinked_executions = [
                i for i in executions.keys() if i not in linked.keys()]
            if not unlinked_executions:
                return
            execution_id_to_link = unlinked_executions[0]
            execution_uri = executions[execution_id_to_link]
            pc_syntax = self._create_execution_link_syntax(
                "Execution", "Execution", execution_uri, execution_id_to_link, self.execution_id, "linked", {
                    "Artifact_Name": parent_artifact_name, "uri": parent_artifact_uri})
            _ = session.write_transaction(self._run_transaction, pc_syntax)

    def _get_node(self, node_label: str, node_name: str)->int:
        #Match(n:Metrics) where n.Name contains 'metrics_1' return n
        search_syntax = "MATCH (n:{}) where '{}' in n.Name  \
                              return ELEMENTID(n) as node_id".format(node_label, node_name)
        node_id = None
        with self.driver.session() as session:
            nodes = session.read_transaction(
                self._run_transaction, search_syntax)

            node_id = nodes[0]["node_id"]
        return node_id

    def _get_node_with_path(self, node_label: str, node_path: str)->int:
        #Match(n:Metrics) where n.Path contains 'metrics_1' return n
        search_syntax = "MATCH (n:{}) where '{}' in n.Path  \
                              return ELEMENTID(n) as node_id".format(node_label, node_path)
        node_id = None
        with self.driver.session() as session:
            nodes = session.read_transaction(
                self._run_transaction, search_syntax)

            node_id = nodes[0]["node_id"]
        return node_id

    @staticmethod
    def _run_transaction(tx, message):
        result = tx.run(message)
        values = []
        for record in result:
            values.append(record)
        return values

    @staticmethod
    def _create_pipeline_syntax(name: str, props: t.Dict, uri: int) -> str:
        props["Name"] = name
        props["uri"] = str(uri)
        props["pipeline_id"] = str(uri)
        props["pipeline_name"] = name
        syntax_str = "MERGE (a:Pipeline {"  # + str(props) + ")"
        for k, v in props.items():
            k = re.sub('\W+', '', k)
            syntax_str = syntax_str + k + ":" + "\"" + v + "\"" + ","
        syntax_str = syntax_str.rstrip(syntax_str[-1])
        syntax_str = syntax_str + "}) RETURN ELEMENTID(a) as node_id"
        return syntax_str

    # Todo - Verify what is considered as unique node . is it a combination of
    # all properties

    @staticmethod
    def _create_dataset_syntax(name: str, path: str, uri: str, pipeline_id: int, pipeline_name: str,
                               custom_properties):
        custom_properties["Name"] = name
        custom_properties["Path"] = path
        custom_properties["pipeline_id"] = str(pipeline_id)
        custom_properties["pipeline_name"] = pipeline_name
        syntax_str = "MERGE (a:Dataset {uri:\"" + uri + "\"}) SET "
        # props_str = ""
        for k, v in custom_properties.items():
            k = re.sub('\W+', '', k)
            props_str = "a." + k + \
                " = coalesce([x in a." + k + " where x <>\"" + str(v) + "\"], []) + \"" + str(v) + "\","
            syntax_str = syntax_str + props_str
        syntax_str = syntax_str.rstrip(",")
        syntax_str = syntax_str + " RETURN ELEMENTID(a) as node_id"
        return syntax_str

    @staticmethod
    def _create_env_syntax(name: str, path: str, uri: str, pipeline_id: int, pipeline_name: str, 
                            custom_properties):
        custom_properties["Name"] = name
        custom_properties["Path"] = path
        custom_properties["pipeline_id"] = str(pipeline_id)
        custom_properties["pipeline_name"] = pipeline_name
        syntax_str = "MERGE (a:Environment {uri:\"" + uri + "\"}) SET "
        # props_str = ""
        for k, v in custom_properties.items():
            k = re.sub('\W+', '', k)
            props_str = "a." + k + \
                " = coalesce([x in a." + k + " where x <>\"" + str(v) + "\"], []) + \"" + str(v) + "\","
            syntax_str = syntax_str + props_str
        syntax_str = syntax_str.rstrip(",")
        syntax_str = syntax_str + " RETURN ELEMENTID(a) as node_id"
        return syntax_str

    @staticmethod
    def _create_dataslice_syntax(name: str, path: str, uri: str,
                               custom_properties):
        custom_properties["Name"] = name
        custom_properties["Path"] = path
        syntax_str = "MERGE (a:Dataslice {uri:\"" + uri + "\"}) SET "
        # props_str = ""
        for k, v in custom_properties.items():
            k = re.sub('\W+', '', k)
            props_str = "a." + k + \
                " = coalesce([x in a." + k + " where x <>\"" + str(v) + "\"], []) + \"" + str(v) + "\","
            syntax_str = syntax_str + props_str
        syntax_str = syntax_str.rstrip(",")
        syntax_str = syntax_str + " RETURN ELEMENTID(a) as node_id"
        return syntax_str

    @staticmethod
    def _create_model_syntax(name: str, uri: str, pipeline_id: int, pipeline_name: str, custom_properties):
        custom_properties["Name"] = name
        custom_properties["pipeline_id"] = str(pipeline_id)
        custom_properties["pipeline_name"] = pipeline_name
        syntax_str = "MERGE (a:Model {uri:\"" + uri + "\"}) SET "
        for k, v in custom_properties.items():
            k = re.sub('\W+', '', k)
            props_str = "a." + k + \
                " = coalesce([x in a." + k + " where x <>\"" + str(v) + "\"], []) + \"" + str(v) + "\","
            #syntax_str = syntax_str + k + ":" + "\"" + str(v) + "\"" + ","
            syntax_str = syntax_str + props_str
        syntax_str = syntax_str.rstrip(",")
        syntax_str = syntax_str + " RETURN ELEMENTID(a) as node_id"
        return syntax_str

    @staticmethod
    def _create_metrics_syntax(name: str, uri: str, event: str, execution_id: int, pipeline_id: int,
                               pipeline_name: str, custom_properties):
        custom_properties["Name"] = name
        custom_properties["uri"] = uri
        # custom_properties["execution_id"] = str(execution_id)
        custom_properties["pipeline_id"] = str(pipeline_id)
        custom_properties["pipeline_name"] = pipeline_name
        syntax_str = "MERGE (a:Metrics {"  # + str(props) + ")"
        for k, v in custom_properties.items():
            k = re.sub('\W+', '', k)
            syntax_str = syntax_str + k + ":" + "\"" + str(v) + "\"" + ","
        syntax_str = syntax_str.rstrip(syntax_str[-1])
        syntax_str = syntax_str + "})"
        syntax_str = syntax_str + " RETURN ELEMENTID(a) as node_id"
        return syntax_str
    
    @staticmethod
    def _create_step_metrics_syntax(name: str, uri: str, event: str, execution_id: int, pipeline_id: int,
                               pipeline_name: str, custom_properties):
        custom_properties["Name"] = name
        custom_properties["uri"] = uri
        # custom_properties["execution_id"] = str(execution_id)
        custom_properties["pipeline_id"] = str(pipeline_id)
        custom_properties["pipeline_name"] = pipeline_name
        syntax_str = "MERGE (a:Step_Metrics {"  # + str(props) + ")"
        for k, v in custom_properties.items():
            k = re.sub('\W+', '', k)
            syntax_str = syntax_str + k + ":" + "\"" + str(v) + "\"" + ","
        syntax_str = syntax_str.rstrip(syntax_str[-1])
        syntax_str = syntax_str + "})"
        syntax_str = syntax_str + " RETURN ELEMENTID(a) as node_id"
        return syntax_str

    @staticmethod
    def _create_stage_syntax(name: str, props: t.Dict, uri: int, pipeline_id: int, pipeline_name: str) -> str:
        props["Name"] = name
        props["uri"] = str(uri)
        props["pipeline_id"] = str(pipeline_id)
        props["pipeline_name"] = pipeline_name
        syntax_str = "MERGE (a:Stage {"  # + str(props) + ")"
        for k, v in props.items():
            k = re.sub('\W+', '', k)
            syntax_str = syntax_str + k + ":" + "\"" + str(v) + "\"" + ","

        syntax_str = syntax_str.rstrip(syntax_str[-1])
        syntax_str = syntax_str + "}) RETURN ELEMENTID(a) as node_id"
        return syntax_str


    @staticmethod
    def _create_parent_child_syntax(parent_label: str, child_label: str, parent_id: int, child_id: int, relation: str):
        parent_child_syntax = "MATCH (a:{}), (b:{}) where ELEMENTID(a) = '{}' AND ELEMENTID(b) = '{}' MERGE (a)-[r:{}]->(b) \
                              return type(r)".format(parent_label, child_label, parent_id, child_id, relation)
        return parent_child_syntax

    @staticmethod
    def _create_execution_artifacts_link_syntax(parent_label: str, child_label: str, parent_id: int, child_id: int,
                                                relation: str):
        if relation.lower() == "input":
            parent_child_syntax = "MATCH (a:{}), (b:{}) where ELEMENTID(a) = '{}' AND ELEMENTID(b) = '{}' MERGE (a)<-[r:{}]-(b) \
                              return type(r)".format(parent_label, child_label, parent_id, child_id, relation)
        else:
            parent_child_syntax = "MATCH (a:{}), (b:{}) where ELEMENTID(a) = '{}' AND ELEMENTID(b) = '{}' MERGE (a)-[r:{}]->(b) \
                              return type(r)".format(parent_label, child_label, parent_id, child_id, relation)

        return parent_child_syntax

    @staticmethod
    def _create_execution_link_syntax(parent_label: str, child_label: str, parent_uri: str, parent_id: str,
                                      child_id: int,
                                      relation: str, relation_properties: t.Dict):
        """
        MATCH
        (a:Person),
        (b:Person)
        WHERE a.name = 'A' AND b.name = 'B'
        CREATE (a)-[r:RELTYPE]->(b)
        RETURN type(r)
        """
        parent_child_syntax_1 = "MATCH (a:{}), (b:{}) WHERE a.uri = '{}' AND ELEMENTID(a) = '{}' AND  ELEMENTID(b) = '{}' ".format(
            parent_label, child_label, parent_uri, parent_id, child_id)
        parent_child_syntax_2 = "MERGE (a)-[r:{}".format(relation)
        parent_child_syntax_3 = "{"
        for k, v in relation_properties.items():
            parent_child_syntax_3 = parent_child_syntax_3 + k + ":" + "\"" + v + "\"" + ","
        parent_child_syntax_3 = parent_child_syntax_3.rstrip(
            parent_child_syntax_3[-1])
        parent_child_syntax_4 = "}]->(b) RETURN type(r)"
        parent_child_syntax = parent_child_syntax_1 + parent_child_syntax_2 \
            + parent_child_syntax_3 + parent_child_syntax_4
        return parent_child_syntax

    @staticmethod
    def _create_parent_child_artifacts_syntax(parent_label: str, child_label: str, parent_uri: str, child_uri: str,
                                              parent_name: str, child_name: str, pipeline_id: int, relation: str,
                                              relation_properties: t.Dict):
        """
        MATCH
        (a:Person),
        (b:Person)
        WHERE a.name = 'A' AND b.name = 'B'
        CREATE (a)-[r:RELTYPE]->(b)
        RETURN type(r)
        """
        parent_child_syntax_1 = "MATCH (a:{}), (b:{}) WHERE a.uri = '{}' AND b.uri = '{}' ".format(
            parent_label, child_label, parent_uri, child_uri)
        parent_child_syntax_2 = "MERGE (a)-[r:{}".format(relation)
        parent_child_syntax_3 = "{"
        for k, v in relation_properties.items():
            parent_child_syntax_3 = parent_child_syntax_3 + \
                k + ":" + "\"" + str(v) + "\"" + ","
        parent_child_syntax_3 = parent_child_syntax_3.rstrip(
            parent_child_syntax_3[-1])
        parent_child_syntax_4 = "}]->(b) RETURN type(r)"
        parent_child_syntax = parent_child_syntax_1 + parent_child_syntax_2 + \
            parent_child_syntax_3 + parent_child_syntax_4
        return parent_child_syntax

    @staticmethod
    def _create_execution_syntax(name: str, command: str, props: t.Dict, uri: int, pipeline_id: int,
                                 pipeline_name: str) -> str:
        props["Name"] = name
        props["Command"] = command
        props["uri"] = str(uri)
        props["pipeline_id"] = str(pipeline_id)
        props["pipeline_name"] = pipeline_name
        syntax_str = "MERGE (a:Execution {"  # + str(props) + ")"
        for k, v in props.items():
            k = re.sub('\W+', '', k)
            v = str(v)
            syntax_str = syntax_str + k + ":" + "\"" + v + "\"" + ","

        syntax_str = syntax_str.rstrip(syntax_str[-1])
        syntax_str = syntax_str + "}) RETURN ELEMENTID(a) as node_id"
        return syntax_str
