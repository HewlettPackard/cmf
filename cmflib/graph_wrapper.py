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
import re
from itertools import groupby


class GraphDriver:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_pipeline_node(self, name: str, uri: int, props=None):
        if props is None:
            props = {}
        pipeline_syntax = self._create_pipeline_syntax(name, props, uri)
        with self.driver.session() as session:
            _ = session.write_transaction(self._run_transaction, pipeline_syntax)

    def create_stage_node(self, name: str, parent_id: int, stage_id: int, props=None):
        if props is None:
            props = {}
        stage_syntax = self._create_stage_syntax(name, props, stage_id, parent_id)
        pc_syntax = self._create_parent_child_syntax("Pipeline", "Stage", str(parent_id), str(stage_id), parent_id,
                                                     "contains")
        with self.driver.session() as session:
            _ = session.write_transaction(self._run_transaction, stage_syntax)
            _ = session.write_transaction(self._run_transaction, pc_syntax)

    def create_execution_node(self, name: str, parent_id: int, pipeline_id: int, command: str, execution_id: int,
                              props=None):

        if props is None:
            props = {}
        execution_syntax = self._create_execution_syntax(name, command, props, execution_id, pipeline_id)
        pc_syntax = self._create_parent_child_syntax("Stage", "Execution", str(parent_id),
                                                     str(execution_id), pipeline_id, "runs")
        with self.driver.session() as session:
            _ = session.write_transaction(self._run_transaction, execution_syntax)
            _ = session.write_transaction(self._run_transaction, pc_syntax)

    def create_dataset_node(self, name: str, path: str, uri: str, event: str, execution_id: int, pipeline_id: int,
                            custom_properties=None):

        if custom_properties is None:
            custom_properties = {}
        dataset_syntax = self._create_dataset_syntax(name, path, uri, pipeline_id, custom_properties)
        pc_syntax = self._create_execution_artifacts_link_syntax("Execution", "Dataset", str(execution_id), uri, name,
                                                                 pipeline_id, event)
        with self.driver.session() as session:
            _ = session.write_transaction(self._run_transaction, dataset_syntax)
            _ = session.write_transaction(self._run_transaction, pc_syntax)

    def create_model_node(self, name: str, uri: str, event: str, execution_id: int, pipeline_id: int,
                          custom_properties=None):

        if custom_properties is None:
            custom_properties = {}
        model_syntax = self._create_model_syntax(name, uri, pipeline_id, custom_properties)
        pc_syntax = self._create_execution_artifacts_link_syntax("Execution", "Model", str(execution_id), uri, name,
                                                                 pipeline_id, event)
        with self.driver.session() as session:
            _ = session.write_transaction(self._run_transaction, model_syntax)
            _ = session.write_transaction(self._run_transaction, pc_syntax)

    """
    def create_model_node(self, name:str, path:str, uri:str, event:str, execution_id:str,
                                        pipeline_id:int,custom_properties={}):
        model_syntax = self._create_model_syntax(name, path, uri, event, execution_id, pipeline_id, custom_properties)
        pc_syntax = self._create_parent_child_syntax("Execution", "Model", execution_id, uri, event)
        with self.driver.session() as session:
            execution = session.write_transaction(self._run_transaction, model_syntax)
            relation = session.write_transaction(self._run_transaction, pc_syntax)
    """

    def create_metrics_node(self, name: str, uri: str, event: str, execution_id: int, pipeline_id: int,
                            custom_properties=None):

        if custom_properties is None:
            custom_properties = {}
        metrics_syntax = self._create_metrics_syntax(name, uri, event, execution_id, pipeline_id, custom_properties)
        pc_syntax = self._create_execution_artifacts_link_syntax("Execution", "Metrics", str(execution_id), uri, name,
                                                                 pipeline_id, event)
        with self.driver.session() as session:
            _ = session.write_transaction(self._run_transaction, metrics_syntax)
            _ = session.write_transaction(self._run_transaction, pc_syntax)

    def create_artifact_relationships(self, parent_artifacts, child_artifact, relation_properties):
        #      f = lambda d: d['Event']
        #      res = {k:list(v) for k,v in groupby(sorted(artifacts, key=f), f)}

        #     for v in res["output"]:

        child_artifact_type = child_artifact["Type"]
        child_artifact_uri = child_artifact["URI"]
        child_name = child_artifact["Name"]
        pipline_id = child_artifact["Pipeline_Id"]
        for k in parent_artifacts:
            parent_artifact_type = k["Type"]
            parent_artifact_uri = k["URI"]
            parent_name = k["Name"]
            relation = re.sub('\W+', '', re.split("_", k["Execution_Name"])[-1])
            pc_syntax = self._create_parent_child_artifacts_syntax(parent_artifact_type, child_artifact_type,
                                                                   parent_artifact_uri, child_artifact_uri, parent_name,
                                                                   child_name, pipline_id, relation,
                                                                   relation_properties)
            with self.driver.session() as session:
                _ = session.write_transaction(self._run_transaction, pc_syntax)

    def create_execution_links(self, parent_artifact_uri, parent_artifact_name, parent_artifact_type, execution_id,
                               pipeline_id):

        parent_execution_query = "MATCH (n:{}".format(
            parent_artifact_type) + "{uri: '" + parent_artifact_uri + "', pipeline_id:'" + str(
            pipeline_id) + "'}) <-[:output]-(execution) return execution.uri as uri"

        with self.driver.session() as session:
            execution_parent = session.read_transaction(self._run_transaction, parent_execution_query)
            line = execution_parent
            parent_value = None if line is None else line["uri"]
            # parent_value = None if  execution_parent_record is None else execution_parent_record.value()
            if parent_value:
                pc_syntax = self._create_execution_link_syntax("Execution", "Execution", parent_value, execution_id,
                                                               "linked", {"Artifact_Name": parent_artifact_name,
                                                                          "uri": parent_artifact_uri})
                _ = session.write_transaction(self._run_transaction, pc_syntax)

    @staticmethod
    def _run_transaction(tx, message):
        result = tx.run(message)
        return result.single()

    @staticmethod
    def _create_pipeline_syntax(name: str, props: {}, uri: int) -> str:
        props["Name"] = name
        props["uri"] = str(uri)
        props["pipeline_id"] = str(uri)
        syntax_str = "MERGE (a:Pipeline {"  # + str(props) + ")"
        for k, v in props.items():
            k = re.sub('\W+', '', k)
            syntax_str = syntax_str + k + ":" + "\"" + v + "\"" + ","
        syntax_str = syntax_str.rstrip(syntax_str[-1])
        syntax_str = syntax_str + "})"
        return syntax_str

    # Todo - Verify what is considered as unique node . is it a combination of all properties
    @staticmethod
    def _create_dataset_syntax(name: str, path: str, uri: str, pipeline_id: int,
                               custom_properties):
        custom_properties["Name"] = name
        custom_properties["Path"] = path
        custom_properties["uri"] = uri
        custom_properties["pipeline_id"] = str(pipeline_id)
        syntax_str = "MERGE (a:Dataset {"  # + str(props) + ")"
        for k, v in custom_properties.items():
            k = re.sub('\W+', '', k)
            syntax_str = syntax_str + k + ":" + "\"" + str(v) + "\"" + ","
        syntax_str = syntax_str.rstrip(syntax_str[-1])
        syntax_str = syntax_str + "})"
        return syntax_str

    @staticmethod
    def _create_model_syntax(name: str, uri: str, pipeline_id: int, custom_properties):
        custom_properties["Name"] = name
        custom_properties["uri"] = uri
        custom_properties["pipeline_id"] = str(pipeline_id)
        syntax_str = "MERGE (a:Model {"  # + str(props) + ")"
        for k, v in custom_properties.items():
            k = re.sub('\W+', '', k)
            syntax_str = syntax_str + k + ":" + "\"" + str(v) + "\"" + ","
        syntax_str = syntax_str.rstrip(syntax_str[-1])
        syntax_str = syntax_str + "})"
        return syntax_str

    @staticmethod
    def _create_metrics_syntax(name: str, uri: str, event: str, execution_id: int, pipeline_id: int, custom_properties):
        custom_properties["Name"] = name
        custom_properties["uri"] = uri
        # custom_properties["execution_id"] = str(execution_id)
        custom_properties["pipeline_id"] = str(pipeline_id)
        syntax_str = "MERGE (a:Metrics {"  # + str(props) + ")"
        for k, v in custom_properties.items():
            k = re.sub('\W+', '', k)
            syntax_str = syntax_str + k + ":" + "\"" + str(v) + "\"" + ","
        syntax_str = syntax_str.rstrip(syntax_str[-1])
        syntax_str = syntax_str + "})"
        return syntax_str

    @staticmethod
    def _create_stage_syntax(name: str, props: {}, uri: int, pipeline_id: int) -> str:
        props["Name"] = name
        props["uri"] = str(uri)
        props["pipeline_id"] = str(pipeline_id)
        syntax_str = "MERGE (a:Stage {"  # + str(props) + ")"
        for k, v in props.items():
            k = re.sub('\W+', '', k)
            syntax_str = syntax_str + k + ":" + "\"" + str(v) + "\"" + ","

        syntax_str = syntax_str.rstrip(syntax_str[-1])
        syntax_str = syntax_str + "})"
        return syntax_str

    @staticmethod
    def _create_parent_child_syntax(parent_label: str, child_label: str, parent_name: str, child_name: str,
                                    pipeline_id: int, relation: str):
        """
        MATCH
        (a:Person),
        (b:Person)
        WHERE a.name = 'A' AND b.name = 'B'
        CREATE (a)-[r:RELTYPE]->(b)
        RETURN type(r)
        """
        if relation.lower() == "input":

            parent_child_syntax = "MATCH (a:{}), (b:{}) WHERE a.uri = '{}' AND b.uri = '{}' AND a.pipeline_id = '{}' " \
                                  "AND b.pipeline_id = '{}'\
                               MERGE (a)<-[r:{}]-(b) \
                               RETURN type(r)".format(parent_label, child_label, parent_name, child_name,
                                                      str(pipeline_id), str(pipeline_id), relation)
        else:
            parent_child_syntax = "MATCH (a:{}), (b:{}) WHERE a.uri = '{}' AND b.uri = '{}' AND a.pipeline_id = '{}' " \
                                  "AND b.pipeline_id = '{}' \
                               MERGE (a)-[r:{}]->(b) \
                               RETURN type(r)".format(parent_label, child_label, parent_name, child_name, pipeline_id,
                                                      pipeline_id, relation)
        return parent_child_syntax

    @staticmethod
    def _create_execution_artifacts_link_syntax(parent_label: str, child_label: str, parent_uri: str, child_uri: str,
                                                child_name: str, pipeline_id: int, relation: str):
        """
        MATCH
        (a:Person),
        (b:Person)
        WHERE a.name = 'A' AND b.name = 'B'
        CREATE (a)-[r:RELTYPE]->(b)
        RETURN type(r)
        """
        if relation.lower() == "input":

            parent_child_syntax = "MATCH (a:{}), (b:{}) WHERE a.uri = '{}' AND b.uri = '{}' AND b.Name = '{}' " \
                                  "AND a.pipeline_id = '{}' AND b.pipeline_id = '{}'\
                               MERGE (a)<-[r:{}]-(b) \
                               RETURN type(r)".format(parent_label, child_label, parent_uri, child_uri, child_name,
                                                      str(pipeline_id), str(pipeline_id),
                                                      relation)
        else:
            parent_child_syntax = "MATCH (a:{}), (b:{}) WHERE a.uri = '{}' AND b.uri = '{}' AND b.Name = '{}' AND " \
                                  "a.pipeline_id = '{}' AND b.pipeline_id = '{}'\
                               MERGE (a)-[r:{}]->(b) \
                               RETURN type(r)".format(parent_label, child_label, parent_uri, child_uri, child_name,
                                                      str(pipeline_id), str(pipeline_id),
                                                      relation)
        return parent_child_syntax

    @staticmethod
    def _create_execution_link_syntax(parent_label: str, child_label: str, parent_uri: str, child_uri: str,
                                      relation: str, relation_properties: {}):
        """
        MATCH
        (a:Person),
        (b:Person)
        WHERE a.name = 'A' AND b.name = 'B'
        CREATE (a)-[r:RELTYPE]->(b)
        RETURN type(r)
        """

        #  parent_child_syntax_1 = "MATCH (a:{}), (b:{}) WHERE a.Name = '{}' AND
        #  b.Name = '{}' ".format(parent_label, child_label, parent_name, child_name)
        #  parent_child_syntax_2 = "MERGE (a)-[r:{}\{]->(b)
        #                         RETURN type(r)".format(parent_label, child_label, parent_name, child_name, relation)

        parent_child_syntax_1 = "MATCH (a:{}), (b:{}) WHERE a.uri = '{}' AND  b.uri = '{}' ".format(parent_label,
                                                                                                    child_label,
                                                                                                    parent_uri,
                                                                                                    child_uri)
        parent_child_syntax_2 = "MERGE (a)-[r:{}".format(relation)
        parent_child_syntax_3 = "{"
        for k, v in relation_properties.items():
            parent_child_syntax_3 = parent_child_syntax_3 + k + ":" + "\"" + v + "\"" + ","
        parent_child_syntax_3 = parent_child_syntax_3.rstrip(parent_child_syntax_3[-1])
        parent_child_syntax_4 = "}]->(b) RETURN type(r)"
        parent_child_syntax = parent_child_syntax_1 + parent_child_syntax_2 \
                              + parent_child_syntax_3 + parent_child_syntax_4

        return parent_child_syntax

    @staticmethod
    def _create_parent_child_artifacts_syntax(parent_label: str, child_label: str, parent_uri: str, child_uri: str,
                                              parent_name: str, child_name: str, pipeline_id: int, relation: str,
                                              relation_properties: {}):
        """
        MATCH
        (a:Person),
        (b:Person)
        WHERE a.name = 'A' AND b.name = 'B'
        CREATE (a)-[r:RELTYPE]->(b)
        RETURN type(r)
        """

        #  parent_child_syntax_1 = "MATCH (a:{}), (b:{}) WHERE a.Name = '{}' AND
        #  b.Name = '{}' ".format(parent_label, child_label, parent_name, child_name)
        #  parent_child_syntax_2 = "MERGE (a)-[r:{}\{]->(b)
        #                         RETURN type(r)".format(parent_label, child_label, parent_name, child_name, relation)

        parent_child_syntax_1 = "MATCH (a:{}), (b:{}) WHERE a.uri = '{}' AND a.Name = '{}'" \
                                " AND a.pipeline_id = '{}' AND b.pipeline_id = '{}' " \
                                "AND b.Name = '{}' AND b.uri = '{}' ".format(
                                parent_label, child_label, parent_uri, parent_name, str(pipeline_id),
                                str(pipeline_id), child_name,
                                child_uri)
        parent_child_syntax_2 = "MERGE (a)-[r:{}".format(relation)
        parent_child_syntax_3 = "{"
        for k, v in relation_properties.items():
            parent_child_syntax_3 = parent_child_syntax_3 + k + ":" + "\"" + str(v) + "\"" + ","
        parent_child_syntax_3 = parent_child_syntax_3.rstrip(parent_child_syntax_3[-1])
        parent_child_syntax_4 = "}]->(b) RETURN type(r)"
        parent_child_syntax = parent_child_syntax_1 + parent_child_syntax_2 + parent_child_syntax_3 + \
                              parent_child_syntax_4

        return parent_child_syntax

    @staticmethod
    def _create_execution_syntax(name: str, command: str, props: {}, uri: int, pipeline_id: int) -> str:
        props["Name"] = name
        props["Command"] = command
        props["uri"] = str(uri)
        props["pipeline_id"] = str(pipeline_id)
        syntax_str = "MERGE (a:Execution {"  # + str(props) + ")"
        for k, v in props.items():
            k = re.sub('\W+', '', k)
            v = str(v)
            syntax_str = syntax_str + k + ":" + "\"" + v + "\"" + ","

        syntax_str = syntax_str.rstrip(syntax_str[-1])
        syntax_str = syntax_str + "})"
        return syntax_str
