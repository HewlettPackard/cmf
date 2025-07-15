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
import traceback

from cmflib import cmf
from ml_metadata.errors import AlreadyExistsError
from ml_metadata.metadata_store import metadata_store
from ml_metadata.proto import metadata_store_pb2 as mlpb
from typing import Union

def handle_context(cmf_class, stage):
    """
    Handles the creation or updating of context metadata in MLMD.
    
    Args:
        cmf_class: CMF object for interacting with MLMD.
        stage: Stage dictionary containing context data.
    """
    try:
        # Try to create context
        _ = cmf_class.merge_created_context(
            pipeline_stage=stage['name'],
            custom_properties=stage["custom_properties"],
        )
    except AlreadyExistsError:
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
        print(f"Error in merge_created_context: {e}")

def handle_execution(cmf_class, execution):
    """
    Handles the creation or updating of execution metadata in MLMD.
    
    Args:
        cmf_class: CMF object for interacting with MLMD.
        execution: Execution dictionary containing execution data.
    """
    try:
        # Try to create execution
        _ = cmf_class.merge_created_execution(
            execution["properties"]["Context_Type"],
            execution["properties"]["Execution"],
            execution["properties"],
            execution["custom_properties"],
            execution["name"]
        )
    except AlreadyExistsError:
        # Update execution if it already exists
        _ = cmf_class.update_execution(
            execution["id"],
            execution["custom_properties"]
        )
    except Exception as e:
        print(f"Error in merge_created_execution: {e}")

def handle_event(cmf_class, store, event):
    """
    Handles the creation or updating of event metadata in MLMD.
    The function handles various artifact types (Dataset, Model, Metrics, Dataslice, Step_Metrics, Environment) and logs them accordingly.
    Args:
        cmf_class: CMF object for interacting with MLMD.
        store: Metadata store object for interacting with MLMD.
        event: Event dictionary containing event data.
    """
    # Constants for event types
    INPUT = 3
    OUTPUT = 4
    artifact_type = event["artifact"]["type"]
    event_type = event["type"]
    artifact_name = (event["artifact"]["name"].split(":"))[0]
    custom_props = event["artifact"]["custom_properties"]
    props = event["artifact"]["properties"]
    uri = event["artifact"]["uri"]

    try:
        if artifact_type == "Dataset":
            event_io = "input" if event_type == INPUT else "output"
            cmf_class.log_dataset_with_version(
                artifact_name, uri, event_io, props, custom_properties=custom_props
            )
        elif artifact_type == "Model":
            event_io = "input" if event_type == INPUT else "output"
            props["uri"] = uri
            cmf_class.log_model_with_version(
                path=artifact_name, event=event_io, props=props, custom_properties=custom_props
            )
        elif artifact_type == "Metrics":
            cmf_class.log_execution_metrics_from_client(event["artifact"]["name"], custom_props)
        elif artifact_type == "Dataslice":
            dataslice = cmf_class.create_dataslice(event["artifact"]["name"])
            dataslice.log_dataslice_from_client(uri, props, custom_props)
        elif artifact_type == "Step_Metrics":
            cmf_class.log_step_metrics_from_client(
                event["artifact"]["name"], uri, props, custom_props
            )
        elif artifact_type == "Environment":
            cmf_class.log_python_env_from_client(artifact_name, uri, props)
        elif artifact_type == "Label":
            cmf_class.log_label_with_version(artifact_name, uri, props, custom_props)
        else:
            # Skip unsupported artifact types without raising an error
            pass
    except AlreadyExistsError:
        # if same pipeline is pushed twice at same time, update custom_properties using 2nd pipeline                      
        artifact = store.get_artifacts_by_uri(uri)
        cmf_class.update_existing_artifact(artifact[0], custom_properties=custom_props)
    except Exception as e:
        print(f"Error in log_{artifact_type}_with_version: {e}")

def process_execution(cmf_class, store, stage, execution):
    """
    Processes a single execution including its context, execution details, and events.
    
    Args:
        cmf_class: CMF object for interacting with MLMD.
        store: Metadata store object for interacting with MLMD.
        stage: Stage dictionary containing context and execution data.
        execution: Execution dictionary containing execution and event data.
    """
    # Handle context and execution
    handle_context(cmf_class, stage)
    handle_execution(cmf_class, execution)

    # Process events sequentially within each execution
    for event in execution["events"]:
        try:
            handle_event(cmf_class, store, event)
        except Exception as e:
            print(f"Error in event processing: {e}")

def process_stage(cmf_class, stage, exec_uuid):
    """
    Processes a single stage including its executions and events.
    
    Args:
        stage: Stage dictionary containing execution and event data.
        path_to_store: Path to the MLMD store.
        pipeline_name: Name of the pipeline.
        graph: Boolean indicating if graph is enabled.
        exec_uuid: Optional execution UUID to filter executions.
        cmd (str): The command to execute. If "push", the original_time_since_epoch is added to the custom_properties.
    """

    # Filter executions based on execution UUID (if provided)
    if exec_uuid is None:   #if exec_uuid is None we pass all the executions.
        list_executions = stage["executions"]
    elif exec_uuid is not None:  # elif exec_uuid is not None, we pass executions for that specific uuid.
        list_executions = [
            execution for execution in stage["executions"]
            if exec_uuid in execution['properties'].get("Execution_uuid", "").split(",")
        ]
    else:
        return "Invalid execution uuid given."

    # Process each execution sequentially within the stage
    for execution in list_executions:
        try:
            process_execution(cmf_class, cmf_class.store, stage, execution)
        except Exception as e:
            print(f"Error in execution processing: {e}")

def parse_json_to_mlmd(mlmd_json, path_to_store: str, cmd: str, exec_uuid: Union[str, str]) -> Union[str, None]:
    """
    Parses a JSON string representing ML Metadata (MLMD) and stores it in a specified path.
    Args:
        mlmd_json (str): A JSON string containing the MLMD data.
        path_to_store (str): The file path where the MLMD data should be stored.
        cmd (str): The command to execute. If "push", the original_time_since_epoch is added to the custom_properties.
        exec_uuid (Union[str, str]): The execution UUID. If None, all executions are processed. If a specific UUID is provided, only executions with that UUID are processed.
    Returns:
        Union[str, None]: Returns a string message if an invalid execution UUID is given, "success" if parsing is successful, otherwise an error message.
    Raises:
        Exception: If any error occurs during the parsing or storing process, an exception is raised and the error message is printed.
    Notes:
        - If the environment variable 'NEO4J_URI' is set, the graph is enabled.
        - The function iterates over all stages in the MLMD data.
    """
    try:
        # from now we are going to make it like this 
        # we will online pass the data of only one pipeline
        # print("Parsing JSON to MLMD...")
        #mlmd_data = json.loads(mlmd_json)
        pipeline_data = json.loads(mlmd_json)
        # this line won't be needed
        # pipelines = mlmd_data["Pipeline"]
        # print("pipelines = ", pipelines)
        # pipeline = pipelines[0]
        pipeline_name = pipeline_data["name"]
        stage = {}

        # When the command is "push", add the original_time_since_epoch to the custom_properties in the metadata while pulling mlmd no need
        if cmd == "push":   
            data = create_original_time_since_epoch(pipeline_data)
        else:
            data = pipeline_data
        # if cmf is configured with 'neo4j' make graph True.
        graph = bool(os.getenv('NEO4J_URI', ""))

        # Initialize the cmf class with pipeline_name and graph_status
        if cmd == "pull":
            cmf_class = cmf.Cmf(filepath=path_to_store, pipeline_name=pipeline_name,  #intializing cmf
                                graph=graph)
        else:
            # in else, we are assuming cmd="push"
            cmf_class = cmf.Cmf(filepath=path_to_store, pipeline_name=pipeline_name,  #intializing cmf
                                graph=graph, is_server=True)

        # Process each stage sequentially
        for stage in data["stages"]:
            try:
                process_stage(cmf_class, stage, exec_uuid)
            except Exception as e:
                print(f"Error in stage processing: {e}")

        return "success"

    except Exception as e:
        print(f"An error occurred in parse_json_to_mlmd: {e}")
        traceback.print_exc()
        return "An error occurred in parse_json_to_mlmd"

# create_time_since_epoch is appended to mlmd pushed to cmf-server as original_create_time_since_epoch
def create_original_time_since_epoch(mlmd_data):
    stages = []
    executions = []
    artifact = []
    original_stages = []
    original_executions = []
    original_artifacts = []
    mlmd_data["original_create_time_since_epoch"] = mlmd_data["create_time_since_epoch"]
    for stage in mlmd_data["stages"]:
        stage["custom_properties"]["original_create_time_since_epoch"] = str(stage[
            "create_time_since_epoch"
        ])
        original_stages.append(
            stage["custom_properties"]["original_create_time_since_epoch"]
        )
        stages.append(stage["create_time_since_epoch"])
        
        for execution in stage["executions"]:
            execution["custom_properties"]["original_create_time_since_epoch"] = str(execution[
                "create_time_since_epoch"
            ])
            original_executions.append(
                execution["custom_properties"]["original_create_time_since_epoch"]
            )
            executions.append(execution["create_time_since_epoch"])
            
            for event in execution["events"]:
                event["artifact"]["custom_properties"][
                    "original_create_time_since_epoch"
                ] = str(event["artifact"]["create_time_since_epoch"])
                original_artifacts.append(
                    event["artifact"]["custom_properties"][
                        "original_create_time_since_epoch"
                    ]
                )
                artifact.append(event["artifact"]["create_time_since_epoch"])
        
    return mlmd_data
