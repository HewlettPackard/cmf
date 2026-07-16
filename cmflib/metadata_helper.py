# Copyright 2022 The Kubeflow Authors Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###


import os
import sys
import typing as t
from time import sleep
from ml_metadata.proto import metadata_store_pb2
from ml_metadata.metadata_store import metadata_store
from ipaddress import ip_address, IPv4Address
from typing import List
import functools

def value_to_mlmd_value(value) -> metadata_store_pb2.Value: # type: ignore  # Value not recognized by mypy, using ignore to bypass
    if value is None:
        return metadata_store_pb2.Value()   # type: ignore  # Value not recognized by mypy, using ignore to bypass
    if isinstance(value, int):
        return metadata_store_pb2.Value(int_value=value)    # type: ignore  # Value not recognized by mypy, using ignore to bypass
    if isinstance(value, float):
        return metadata_store_pb2.Value(double_value=value) # type: ignore  # Value not recognized by mypy, using ignore to bypass
    return metadata_store_pb2.Value(string_value=str(value))    # type: ignore  # Value not recognized by mypy, using ignore to bypass


def connect_to_mlmd() -> metadata_store.MetadataStore:
    metadata_service_host = os.environ.get(
        'METADATA_GRPC_SERVICE_SERVICE_HOST', 'metadata-grpc-service')
    metadata_service_port = int(os.environ.get(
        'METADATA_GRPC_SERVICE_SERVICE_PORT', 8080))

    mlmd_connection_config = metadata_store_pb2.MetadataStoreClientConfig(  # type: ignore  # MetadataStoreClientConfig not recognized by mypy, using ignore to bypass
        host="[{}]".format(metadata_service_host) if isIPv6(metadata_service_host) else metadata_service_host,
        port=metadata_service_port,
    )

    # Checking the connection to the Metadata store.
    for _ in range(100):
        try:
            mlmd_store = metadata_store.MetadataStore(mlmd_connection_config)
            # All get requests fail when the DB is empty, so we have to use a put request.
            # TODO: Replace with _ = mlmd_store.get_context_types()
            # when https://github.com/google/ml-metadata/issues/28 is fixed
            _ = mlmd_store.put_execution_type(
                metadata_store_pb2.ExecutionType(   # type: ignore  # Execution type not recognized by mypy, using ignore to bypass
                    name="DummyExecutionType",
                )
            )
            return mlmd_store
        except Exception as e:
            print('Failed to access the Metadata store. Exception: "{}"'.format(str(e)), file=sys.stderr)
            sys.stderr.flush()
            sleep(1)

    raise RuntimeError('Could not connect to the Metadata store.')


def get_artifacts_by_id(store, artifact_id: List[int]) -> List[metadata_store_pb2.Artifact]:    # type: ignore  # Artifact type not recognized by mypy, using ignore to bypass
    try:
        artifacts = store.get_artifacts_by_id(artifact_id)
        return artifacts
    except Exception as e:
        print('Failed to get artifact. Exception: "{}"'.format(str(e)), file=sys.stderr)


def put_artifact(store, artifact: metadata_store_pb2.Artifact):  # type: ignore  # Artifact type not recognized by mypy, using ignore to bypass
    try:
        store.put_artifacts([artifact])
    except Exception as e:
        print('Failed to put artifact . Exception: "{}"'.format(str(e)), file=sys.stderr)


def get_or_create_artifact_type(store, type_name, properties: t.Optional[dict] = None) -> metadata_store_pb2.ArtifactType:   # type: ignore  # Artifact type not recognized by mypy, using ignore to bypass
    try:
        artifact_type = store.get_artifact_type(type_name=type_name)
        return artifact_type
    except BaseException:
        artifact_type = metadata_store_pb2.ArtifactType(    # type: ignore  # Artifact type not recognized by mypy, using ignore to bypass
            name=type_name,
            properties=properties,
        )
        artifact_type.id = store.put_artifact_type(artifact_type)  # Returns ID
        return artifact_type


def get_or_create_execution_type(store, type_name, properties: t.Optional[dict] = None) -> metadata_store_pb2.ExecutionType:    # type: ignore  # Execution type not recognized by mypy, using ignore to bypass
    try:
        execution_type = store.get_execution_type(type_name=type_name)
        return execution_type
    except BaseException:
        execution_type = metadata_store_pb2.ExecutionType(  # type: ignore  # Execution type not recognized by mypy, using ignore to bypass
            name=type_name,
            properties=properties,
        )
        execution_type.id = store.put_execution_type(
            execution_type)  # Returns ID
        return execution_type


def get_or_create_context_type(store, type_name, properties: t.Optional[dict] = None) -> metadata_store_pb2.ContextType:    # type: ignore  # Context type not recognized by mypy, using ignore to bypass
    try:
        context_type = store.get_context_type(type_name=type_name)
        return context_type
    except BaseException:
        context_type = metadata_store_pb2.ContextType(  # type: ignore  # Context type not recognized by mypy, using ignore to bypass
            name=type_name,
            properties=properties,
        )
        context_type.id = store.put_context_type(context_type)  # Returns ID
        return context_type


def update_context_custom_properties(store, context_id, context_name: str, properties: dict, custom_properties: dict) -> metadata_store_pb2.Context:    # type: ignore  # Context type not recognized by mypy, using ignore to bypass
        context = metadata_store_pb2.Context(   # type: ignore  # Context type not recognized by mypy, using ignore to bypass
            id = context_id,
            name=context_name,
            properties=properties,
            custom_properties=custom_properties,
        )
        store.put_contexts([context])
        return context

def create_artifact_with_type(
        store,
        uri: str,
        name: str,
        type_name: str,
        properties: t.Optional[dict] = None,
        type_properties: t.Optional[dict] = None,
        custom_properties: t.Optional[dict] = None,
) -> metadata_store_pb2.Artifact:   # type: ignore  # Artifact type not recognized by mypy, using ignore to bypass
    artifact_type = get_or_create_artifact_type(
        store=store,
        type_name=type_name,
        properties=type_properties,
    )
    artifact = metadata_store_pb2.Artifact( # type: ignore  # Artifact type not recognized by mypy, using ignore to bypass
        uri=uri,
        name=name,
        type_id=artifact_type.id,
        properties=properties,
        custom_properties=custom_properties,
    )
    artifact.id = store.put_artifacts([artifact])[0]
    return artifact


def create_execution_with_type(
        store,
        type_name: str,
        name: str,
        properties: t.Optional[t.Dict] = None,
        type_properties: t.Optional[t.Dict] = None,
        custom_properties: t.Optional[t.Dict] = None,
        create_new_execution: bool = True
) -> metadata_store_pb2.Execution:  # type: ignore  # Execution type not recognized by mypy, using ignore to bypass
    if create_new_execution:
        execution_type = get_or_create_execution_type(
        store = store,
        type_name = name,
        properties = type_properties,
        )
        execution = metadata_store_pb2.Execution(   # type: ignore  # Execution type not recognized by mypy, using ignore to bypass
            type_id=execution_type.id,
            properties=properties,
            custom_properties=custom_properties,
        )
        execution.id = store.put_executions([execution])[0]
    else:
        execution_type = get_or_create_execution_type(
        store=store,
        type_name=type_name,
        properties=type_properties,
        )
        execution = store.get_execution_by_type_and_name(type_name, name)
        if not execution:

            execution = metadata_store_pb2.Execution(   # type: ignore  # Execution type not recognized by mypy, using ignore to bypass
                type_id=execution_type.id,
                name=name,
                properties=properties,
                custom_properties=custom_properties,
             )
            execution.id = store.put_executions([execution])[0]
    return execution


def create_context_with_type(
        store,
        context_name: str,
        type_name: str,
        properties: t.Optional[dict] = None,
        type_properties: t.Optional[dict] = None,
        custom_properties: t.Optional[dict] = None,
) -> metadata_store_pb2.Context:    # type: ignore  # Context type not recognized by mypy, using ignore to bypass
    # ! Context_name must be unique
    context_type = get_or_create_context_type(
        store=store,
        type_name=type_name,
        properties=type_properties,
    )
    context = metadata_store_pb2.Context(   # type: ignore  # Context type not recognized by mypy, using ignore to bypass
        name=context_name,
        type_id=context_type.id,
        properties=properties,
        custom_properties=custom_properties,
    )
    context.id = store.put_contexts([context])[0]
    return context


@functools.lru_cache(maxsize=128)
def get_context_by_name(
        store,
        context_name: str,
) -> metadata_store_pb2.Context:    # type: ignore  # Context type not recognized by mypy, using ignore to bypass
    matching_contexts = [
        context for context in store.get_contexts() if context.name == context_name]
    assert len(matching_contexts) <= 1
    if len(matching_contexts) == 0:
        raise ValueError(
            'Context with name "{}" was not found'.format(context_name))
    return matching_contexts[0]


def get_or_create_context_with_type(
        store,
        context_name: str,
        type_name: str,
        properties: t.Optional[dict] = None,
        type_properties: t.Optional[dict] = None,
        custom_properties: t.Optional[dict] = None,
) -> metadata_store_pb2.Context:    # type: ignore  # Context type not recognized by mypy, using ignore to bypass
    try:
        context = get_context_by_name(store, context_name)
    except BaseException:
        context = create_context_with_type(
            store=store,
            context_name=context_name,
            type_name=type_name,
            properties=properties,
            type_properties=type_properties,
            custom_properties=custom_properties,
        )
        return context  # Return newly created context

    # Verifying that the context has the expected type name
    context_types = store.get_context_types_by_id([context.type_id])
    assert len(context_types) == 1
    if context_types[0].name != type_name:
        raise RuntimeError(
            'Context "{}" was found, but it has type "{}" instead of "{}"'.format(
                context_name, context_types[0].name, type_name))
    return context  # Return existing context


def create_new_execution_in_existing_context(
        store,
        execution_type_name: str,
        execution_name: str,
        context_id: int,
        properties: t.Optional[dict] = None,
        execution_type_properties: t.Optional[dict] = None,
        custom_properties: t.Optional[dict] = None,
        create_new_execution: bool = True
) -> metadata_store_pb2.Execution:  # type: ignore  # Execution type not recognized by mypy, using ignore to bypass
    execution = create_execution_with_type(
        store=store,
        properties=properties,
        custom_properties=custom_properties,
        type_name=execution_type_name,
        name=execution_name,
        type_properties=execution_type_properties,
        create_new_execution=create_new_execution
    )
    association = metadata_store_pb2.Association(   # type: ignore  # Association type not recognized by mypy, using ignore to bypass
        execution_id=execution.id,
        context_id=context_id,
    )

    store.put_attributions_and_associations([], [association])
    return execution


# Parent context type name
PARENT_CONTEXT_TYPE_NAME = "Parent_Context"
# Project name - eg - climatenet, smartsim etc
PARENT_CONTEXT_NAME = "Pipeline"
# where is it executed - NERSC, HPE CLUSTER, VM etc
ENVIRONMENT = "Environment"
# Type of project - Active learning, Mini Epoch etc
PROJECT_TYPE = "Project_type"

# child context type name
RUN_CONTEXT_TYPE_NAME = "Child_Context"

# Pipeline stage - eg - Training, Inference, Active Labeling
PIPELINE_STAGE = "Pipeline_Stage"

# Pipeline stage - eg - Training, Inference, Active Labeling
EXECUTION_CONTEXT_NAME_PROPERTY_NAME = "Context_Type"
EXECUTION_CONTEXT_ID = "Context_ID"
EXECUTION_EXECUTION = "Execution"
EXECUTION_EXECUTION_TYPE_NAME="Execution_type_name"
EXECUTION_REPO = "Git_Repo"
EXECUTION_START_COMMIT = "Git_Start_Commit"
EXECUTION_END_COMMIT = "Git_End_Commit"
EXECUTION_PIPELINE_TYPE = "Pipeline_Type"

EXECUTION_PIPELINE_ID = "Pipeline_id"
EXECUTION_UNIQUE_ID = "Execution_uuid"

def get_or_create_parent_context(
        store,
        pipeline: str,
        custom_properties: t.Optional[t.Dict] = None
) -> metadata_store_pb2.Context:    # type: ignore  # Context type not recognized by mypy, using ignore to bypass
    mlmd_custom_properties = {}
    for property_name, property_value in (custom_properties or {}).items():
        mlmd_custom_properties[property_name] = value_to_mlmd_value(
            property_value)

    context = get_or_create_context_with_type(
        store=store,
        context_name=pipeline,
        type_name=PARENT_CONTEXT_TYPE_NAME,
        type_properties={
            PARENT_CONTEXT_NAME: metadata_store_pb2.STRING, # type: ignore  # String type not recognized by mypy, using ignore to bypass
        },
        properties={
            PARENT_CONTEXT_NAME: metadata_store_pb2.Value(  # type: ignore  # Value type not recognized by mypy, using ignore to bypass
                string_value=pipeline)},
        custom_properties=mlmd_custom_properties)
    return context


def get_or_create_run_context(
        store,
        pipeline_stage: str,
        custom_properties: t.Optional[t.Dict] = None,
) -> metadata_store_pb2.Context:    # type: ignore  # Context type not recognized by mypy, using ignore to bypass
    mlmd_custom_properties = {}
    for property_name, property_value in (custom_properties or {}).items():
        mlmd_custom_properties[property_name] = value_to_mlmd_value(
            property_value)

    context = get_or_create_context_with_type(
        store=store,
        context_name=pipeline_stage,
        type_name=PIPELINE_STAGE,
        type_properties={
            PIPELINE_STAGE: metadata_store_pb2.STRING,  # type: ignore  # String type not recognized by mypy, using ignore to bypass
        },
        properties={
            PIPELINE_STAGE: metadata_store_pb2.Value(   # type: ignore  # Value type not recognized by mypy, using ignore to bypass
                string_value=pipeline_stage)},
        custom_properties=mlmd_custom_properties)
    return context


def associate_child_to_parent_context(store, parent_context: metadata_store_pb2.Context,    # type: ignore  # Context type not recognized by mypy, using ignore to bypass
                                      child_context: metadata_store_pb2.Context):   # type: ignore  # Context type not recognized by mypy, using ignore to bypass
    try:
        associate = metadata_store_pb2.ParentContext(   # type: ignore  # ParentContext type not recognized by mypy, using ignore to bypass
            child_id=child_context.id, parent_id=parent_context.id)
        store.put_parent_contexts([associate])
    except Exception as e:
        # print(e)
        # print('Warning: Exception:{}'.format(str(e)), file=sys.stderr)
        sys.stderr.flush()


def create_new_execution_in_existing_run_context(
        store,
        execution_type_name: str = "",  # TRAINING EXECUTION
        execution_name: str = "",
        context_id: int = 0,  # TRAINING CONTEXT ASSOCIATED WITH THIS EXECUTION
        execution: t.Optional[str] = None,
        pipeline_id: int = 0,  # THE PARENT CONTEXT
        pipeline_type: t.Optional[str] = None,
        git_repo: t.Optional[str] = None,
        git_start_commit: t.Optional[str] = None,
        git_end_commit: str = "",
        custom_properties: t.Optional[dict] = None,
        create_new_execution: bool = True
) -> metadata_store_pb2.Execution:  # type: ignore  # Execution type not recognized by mypy, using ignore to bypass
    mlmd_custom_properties = {}
    for property_name, property_value in (custom_properties or {}).items():
        mlmd_custom_properties[property_name] = value_to_mlmd_value(
            property_value)

    return create_new_execution_in_existing_context(
        store=store,
        execution_type_name=execution_type_name,
        execution_name=execution_name,
        context_id=context_id,
        execution_type_properties={
            EXECUTION_UNIQUE_ID: metadata_store_pb2.STRING, # type: ignore  # String type not recognized by mypy, using ignore to bypass
            EXECUTION_CONTEXT_NAME_PROPERTY_NAME: metadata_store_pb2.STRING,    # type: ignore  # String type not recognized by mypy, using ignore to bypass
            EXECUTION_CONTEXT_ID: metadata_store_pb2.INT,   # type: ignore  # Int type not recognized by mypy, using ignore to bypass
            EXECUTION_EXECUTION: metadata_store_pb2.STRING, # type: ignore  # String type not recognized by mypy, using ignore to bypass
            EXECUTION_EXECUTION_TYPE_NAME: metadata_store_pb2.STRING,   # type: ignore  # String type not recognized by mypy, using ignore to bypass
            EXECUTION_PIPELINE_TYPE: metadata_store_pb2.STRING, # type: ignore  # String type not recognized by mypy, using ignore to bypass
            EXECUTION_PIPELINE_ID: metadata_store_pb2.INT,  # type: ignore  # Int type not recognized by mypy, using ignore to bypass
            EXECUTION_REPO: metadata_store_pb2.STRING,  # type: ignore  # String type not recognized by mypy, using ignore to bypass
            EXECUTION_START_COMMIT: metadata_store_pb2.STRING,  # type: ignore  # String type not recognized by mypy, using ignore to bypass
            EXECUTION_END_COMMIT: metadata_store_pb2.STRING,    # type: ignore  # String type not recognized by mypy, using ignore to bypass
        },

        properties={

            EXECUTION_CONTEXT_NAME_PROPERTY_NAME: metadata_store_pb2.Value(string_value=execution_type_name),   # type: ignore  # Value type not recognized by mypy, using ignore to bypass
            # Mistakenly used for grouping in the UX
            EXECUTION_CONTEXT_ID: metadata_store_pb2.Value(int_value=context_id),   # type: ignore  # Value type not recognized by mypy, using ignore to bypass
            EXECUTION_EXECUTION: metadata_store_pb2.Value(string_value=execution),  # type: ignore  # Value type not recognized by mypy, using ignore to bypass
            EXECUTION_EXECUTION_TYPE_NAME: metadata_store_pb2.Value(string_value=execution_type_name),  # type: ignore  # Value type not recognized by mypy, using ignore to bypass
            EXECUTION_PIPELINE_TYPE: metadata_store_pb2.Value(string_value=pipeline_type),  # type: ignore  # Value type not recognized by mypy, using ignore to bypass
            EXECUTION_PIPELINE_ID: metadata_store_pb2.Value(int_value=pipeline_id), # type: ignore  # Value type not recognized by mypy, using ignore to bypass
            EXECUTION_REPO: metadata_store_pb2.Value(string_value=git_repo),    # type: ignore  # Value type not recognized by mypy, using ignore to bypass
            EXECUTION_START_COMMIT: metadata_store_pb2.Value(string_value=git_start_commit),    # type: ignore  # Value type not recognized by mypy, using ignore to bypass
            EXECUTION_END_COMMIT: metadata_store_pb2.Value(string_value=git_end_commit),    # type: ignore  # Value type not recognized by mypy, using ignore to bypass
            # should set to task ID, not component ID
        },
        custom_properties=mlmd_custom_properties,
        create_new_execution=create_new_execution
    )


def create_new_artifact_event_and_attribution(
        store,
        execution_id: int,
        context_id: int,
        uri: str,
        name: str,
        type_name: str,
        event_type: metadata_store_pb2.Event.Type,  # type: ignore  # Event type not recognized by mypy, using ignore to bypass
        properties: t.Optional[dict] = None,
        artifact_type_properties: t.Optional[dict] = None,
        custom_properties: t.Optional[dict] = None,
        artifact_name_path: t.Optional[metadata_store_pb2.Event.Path] = None,   # type: ignore  # Event type not recognized by mypy, using ignore to bypass
        milliseconds_since_epoch: t.Optional[int] = None,
) -> metadata_store_pb2.Artifact:   # type: ignore  # Artifact type not recognized by mypy, using ignore to bypass
    mlmd_properties = {}
    for property_name, property_value in (properties or {}).items():
        mlmd_properties[property_name] = value_to_mlmd_value(property_value)

    mlmd_custom_properties = {}
    for property_name, property_value in (custom_properties or {}).items():
        mlmd_custom_properties[property_name] = value_to_mlmd_value(
            property_value)

    artifact = create_artifact_with_type(
        store=store,
        uri=uri,
        name=name,
        type_name=type_name,
        type_properties=artifact_type_properties,
        properties=mlmd_properties,
        custom_properties=mlmd_custom_properties,
    )
    event = metadata_store_pb2.Event(   # type: ignore  # Event type not recognized by mypy, using ignore to bypass
        execution_id=execution_id,
        artifact_id=artifact.id,
        type=event_type,
        path=artifact_name_path,
        milliseconds_since_epoch=milliseconds_since_epoch,
    )
    store.put_events([event])
    attribution = metadata_store_pb2.Attribution(   # type: ignore  # Attribution type not recognized by mypy, using ignore to bypass
        context_id=context_id,
        artifact_id=artifact.id,
    )
    store.put_attributions_and_associations([attribution], [])

    return artifact


def link_execution_to_input_artifact(
        store,
        execution_id: int,
        uri: str,
        input_name: str,
) -> metadata_store_pb2.Artifact:   # type: ignore  # Artifact type not recognized by mypy, using ignore to bypass
    artifacts = store.get_artifacts_by_uri(uri)
    if len(artifacts) == 0:
        print('Error: Not found upstream artifact with URI={}.'.format(uri), file=sys.stderr)
        return None
    if len(artifacts) > 1:
        print('Error: Found multiple artifacts with the same URI. {} Using the last one..'.format(artifacts),
              file=sys.stderr)

    artifact = artifacts[-1]

    event = metadata_store_pb2.Event(   # type: ignore  # Event type not recognized by mypy, using ignore to bypass
        execution_id=execution_id,
        artifact_id=artifact.id,
        type=metadata_store_pb2.Event.INPUT,    # type: ignore  # Event type not recognized by mypy, using ignore to bypass
        path=metadata_store_pb2.Event.Path( # type: ignore  # Event type not recognized by mypy, using ignore to bypass
            steps=[
                metadata_store_pb2.Event.Path.Step( # type: ignore  # Event type not recognized by mypy, using ignore to bypass
                    key=input_name,
                ),
            ]
        ),
    )
    store.put_events([event])

    return artifact


def link_execution_to_artifact(
        store,
        execution_id: int,
        uri: str,
        input_name: str,
        event_type: metadata_store_pb2.Event    # type: ignore  # Event type not recognized by mypy, using ignore to bypass
) -> metadata_store_pb2.Artifact:   # type: ignore  # Artifact type not recognized by mypy, using ignore to bypass
    artifacts = store.get_artifacts_by_uri(uri)
    if len(artifacts) == 0:
        print('Error: Not found upstream artifact with URI={}.'.format(uri), file=sys.stderr)
        return None
    if len(artifacts) > 1:
        # print('Warning: Found multiple artifacts with the same URI. {} Using the last one..'.format(artifacts),
        #      file=sys.stderr)

        print('Warning: Found multiple artifacts with the same URI.Using the last one..',
              file=sys.stderr)

    artifact = artifacts[-1]

    # Check if event already exist
    events = store.get_events_by_artifact_ids([artifact.id])
    for evt in events:
        if evt.execution_id == execution_id:
            return artifact

    event = metadata_store_pb2.Event(   # type: ignore  # Event type not recognized by mypy, using ignore to bypass
        execution_id=execution_id,
        artifact_id=artifact.id,
        type=event_type,
        path=metadata_store_pb2.Event.Path( # type: ignore  # Event type not recognized by mypy, using ignore to bypass
            steps=[
                metadata_store_pb2.Event.Path.Step( # type: ignore  # Event type not recognized by mypy, using ignore to bypass
                    key=input_name,
                ),

            ]
        ),
    )
    store.put_events([event])

    return artifact


def isIPv6(ip: str) -> bool:
    try:
        return False if type(ip_address(ip)) is IPv4Address else True
    except Exception as e:
        print('Error: Exception:{}'.format(str(e)), file=sys.stderr)
        sys.stderr.flush()
        return False    # Ensure function always returns a boolean
