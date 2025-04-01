#
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

import json
import os
from cmflib import cmf
import traceback
from ml_metadata.errors import AlreadyExistsError
from ml_metadata.metadata_store import metadata_store
from ml_metadata.proto import metadata_store_pb2 as mlpb
from typing import Union

def parse_json_to_mlmd(mlmd_json, path_to_store: str, cmd: str, exec_uuid: Union[str, str]) -> Union[str, None]:
    """
    Parses a JSON string representing ML Metadata (MLMD) and stores it in a specified path.
    Args:
        mlmd_json (str): A JSON string containing the MLMD data.
        path_to_store (str): The file path where the MLMD data should be stored.
        cmd (str): The command to execute. If "push", the original_time_since_epoch is added to the custom_properties.
        exec_uuid (Union[str, str]): The execution UUID. If None, all executions are processed. If a specific UUID is provided, only executions with that UUID are processed.
    Returns:
        Union[str, None]: Returns a string message if an invalid execution UUID is given, otherwise returns None.
    Raises:
        Exception: If any error occurs during the parsing or storing process, an exception is raised and the error message is printed.
    Notes:
        - If the environment variable 'NEO4J_URI' is set, the graph is enabled.
        - The function initializes a connection configuration and metadata store.
        - The function iterates over all stages and executions in the MLMD data.
        - If a context or execution already exists, it updates the custom properties.
        - The function handles various artifact types (Dataset, Model, Metrics, Dataslice, Step_Metrics, Environment) and logs them accordingly.
    """

    # CONSTANTS
    INPUT = 3
    OUTPUT = 4

    try:
        mlmd_data = json.loads(mlmd_json)
        pipelines = mlmd_data["Pipeline"]
        pipeline = pipelines[0]
        pipeline_name = pipeline["name"]
        stage = {}
        
        # When the command is "push", add the original_time_since_epoch to the custom_properties in the metadata while pulling mlmd no need
        if cmd == "push":   
            data = create_original_time_since_epoch(mlmd_data)
        else:
            data = mlmd_data

        graph = False
        # if cmf is configured with 'neo4j' make graph True.
        if os.getenv('NEO4J_URI', "") != "":   
            graph = True

        # Initialize the connection configuration and metadata store
        config = mlpb.ConnectionConfig()
        config.sqlite.filename_uri = path_to_store
        store = metadata_store.MetadataStore(config)

        # Initialize the cmf class with pipeline_name and graph_status
        cmf_class = cmf.Cmf(filepath=path_to_store, pipeline_name=pipeline_name,  #intializing cmf
                            graph=graph, is_server=True)
        
        for stage in data["Pipeline"][0]["stages"]:  # Iterates over all the stages
            if exec_uuid is None:  #if exec_uuid is None we pass all the executions.
                list_executions = [execution for execution in stage["executions"]]
            elif exec_uuid is not None:  # elif exec_uuid is not None, we pass executions for that specific uuid.
                list_executions = [
                    execution
                    for execution in stage["executions"]
                    if exec_uuid in execution['properties']["Execution_uuid"].split(",") 
                ]
            else:
                return "Invalid execution uuid given."
            for execution in list_executions:  # Iterates over all the executions
                try:
                    _ = cmf_class.merge_created_context(
                        pipeline_stage=stage['name'],
                        custom_properties=stage["custom_properties"],
                    )
                except AlreadyExistsError as e:
                    # Handle the case where the context already exists, possibly due to concurrent pushes.
                    # As both pipelines will be unable to fetch data from server 
                    # updating custom properties if context already exists
                    _ = cmf_class.update_context(
                        str(stage["type"]),
                        str(stage["name"]),
                        stage["id"],
                        stage["properties"],
                        custom_properties=stage["custom_properties"]
                    )
                except Exception as e:
                    print(f"Error in merge_created_context")
                try:
                    _ = cmf_class.merge_created_execution(
                        execution["properties"]["Context_Type"],
                        execution["properties"]["Execution"],
                        execution["properties"],
                        execution["custom_properties"],
                        execution["name"]
                    )
                except AlreadyExistsError as e:
                    _ = cmf_class.update_execution(
                        execution["id"],
                        execution["custom_properties"] 
                    )
                except Exception as e:
                    print(f"Error in merge_created_execution {e}")

                for event in execution["events"]:  # Iterates over all the events
                    artifact_type = event["artifact"]["type"]
                    event_type = event["type"]
                    artifact_name = (event["artifact"]["name"].split(":"))[0]
                    custom_props = event["artifact"]["custom_properties"]
                    props = event["artifact"]["properties"]
                    uri = event["artifact"]["uri"]

                    try:
                        if artifact_type == "Dataset" :
                            if event_type == INPUT :
                                event_io = "input" 
                            else:
                                event_io = "output"    
                            cmf_class.log_dataset_with_version(
                                artifact_name,
                                uri,
                                event_io,
                                props,
                                custom_properties=custom_props,
                            )
                        elif artifact_type == "Model":
                            if event_type == INPUT :
                                event_io = "input" 
                            else:
                                event_io = "output"
                            props["uri"] = uri
                            cmf_class.log_model_with_version(
                                path=artifact_name,
                                event= event_io,
                                props=props,
                                custom_properties=custom_props,
                            )
                        elif artifact_type == "Metrics":
                            cmf_class.log_execution_metrics_from_client(event["artifact"]["name"], custom_props)
                        elif artifact_type == "Dataslice":            
                            dataslice = cmf_class.create_dataslice(event["artifact"]["name"])
                            dataslice.log_dataslice_from_client(uri, props, custom_props)                    
                        elif artifact_type == "Step_Metrics":                          
                            cmf_class.log_step_metrics_from_client(event["artifact"]["name"], uri, props, 
                                                                   custom_props)
                        elif artifact_type == "Environment":
                            cmf_class.log_python_env_from_client(artifact_name, uri, props)
                        else:
                            pass
                    except AlreadyExistsError as e:
                            # if same pipeline is pushed twice at same time, update custom_properties using 2nd pipeline
                            artifact = store.get_artifacts_by_uri(uri)
                            cmf_class.update_existing_artifact(
                                artifact[0],
                                custom_properties=custom_props,
                            ) 
                    except Exception as e:
                            print(f"Error in log_{artifact_type}_with_version" , e)
    except Exception as e:
        print(f"An error occurred in parse_json_to_mlmd: {e}")
        traceback.print_exc()

# create_time_since_epoch is appended to mlmd pushed to cmf-server as original_create_time_since_epoch
def create_original_time_since_epoch(mlmd_data):
    stages = []
    execution = []
    artifact = []
    original_stages = []
    original_execution = []
    original_artifact = []
    mlmd_data["Pipeline"][0]["original_create_time_since_epoch"] = mlmd_data[
        "Pipeline"
    ][0]["create_time_since_epoch"]
    for i in mlmd_data["Pipeline"][0]["stages"]:
        i["custom_properties"]["original_create_time_since_epoch"] = i[
            "create_time_since_epoch"
        ]
        original_stages.append(
            i["custom_properties"]["original_create_time_since_epoch"]
        )
        stages.append(i["create_time_since_epoch"])
        # print(i['custom_properties']['original_create_time_since_epoch'])
        for j in i["executions"]:
            j["custom_properties"]["original_create_time_since_epoch"] = j[
                "create_time_since_epoch"
            ]
            original_execution.append(
                j["custom_properties"]["original_create_time_since_epoch"]
            )
            execution.append(j["create_time_since_epoch"])
            # print(j['custom_properties']['original_create_time_since_epoch'])
            for k in j["events"]:
                k["artifact"]["custom_properties"][
                    "original_create_time_since_epoch"
                ] = k["artifact"]["create_time_since_epoch"]
                original_artifact.append(
                    k["artifact"]["custom_properties"][
                        "original_create_time_since_epoch"
                    ]
                )
                artifact.append(k["artifact"]["create_time_since_epoch"])
                # print(k['artifact']['custom_properties']['original_create_time_since_epoch'])

    return mlmd_data