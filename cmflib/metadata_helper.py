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

# TODO [sergey]: maybe it's better to catch `StatusError` instead of Exception of BaseException. The StatusError seems
#      to be the base class for all mlmd errors (`ml_metadata.errors`).

# TODO [sergey]: can this module be considered as a module implementing the API for working with metadata backends?


"""
### Artifact Methods:
METHOD                                     VISIBILITY  DESCRIPTION
link_execution_to_input_artifact           public      is called in DataSlice.commit
link_execution_to_artifact                 public      is called in ~ log_dataset for existing artifacts
create_new_artifact_event_and_attribution  public      create new artifact (called from ~ log_dataset). calls:
                                                             `create_artifact_with_type`
create_artifact_with_type                  private     create new artifact instance. calls:
                                                             `get_or_create_artifact_type`
get_or_create_artifact_type                private     create (if not exist) artifact type by name
put_artifact                               public      put new artifact into a database  
get_artifacts_by_id                        public      return artifacts with specified IDs.
"""


def value_to_mlmd_value(value: t.Any) -> metadata_store_pb2.Value:
    if value is None:
        return metadata_store_pb2.Value()
    if isinstance(value, int):
        return metadata_store_pb2.Value(int_value=value)
    if isinstance(value, float):
        return metadata_store_pb2.Value(double_value=value)
    return metadata_store_pb2.Value(string_value=str(value))


def connect_to_mlmd() -> metadata_store.MetadataStore:
    metadata_service_host = os.environ.get(
        'METADATA_GRPC_SERVICE_SERVICE_HOST', 'metadata-grpc-service')
    metadata_service_port = int(os.environ.get(
        'METADATA_GRPC_SERVICE_SERVICE_PORT', 8080))

    mlmd_connection_config = metadata_store_pb2.MetadataStoreClientConfig(
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
                metadata_store_pb2.ExecutionType(
                    name="DummyExecutionType",
                )
            )
            return mlmd_store
        except Exception as e:
            print('Failed to access the Metadata store. Exception: "{}"'.format(str(e)), file=sys.stderr)
            sys.stderr.flush()
            sleep(1)

    raise RuntimeError('Could not connect to the Metadata store.')


def get_artifacts_by_id(store: metadata_store.MetadataStore,
                        artifact_ids: t.List[int]) -> List[metadata_store_pb2.Artifact]:
    # TODO: [sergey] Does the `store.get_artifacts_by_id` method raise any exceptions? Seems like it just returns
    #       empty list when no artifacts found.
    # TODO: [sergey] If an error is raised on the other hand, what it the right way to handle it?
    # TODO: [sergey] In some parts of the code methods of store  are directly used instead, e.g.,
    #       `store.get_artifacts_by_uri` (see cmf.py)
    try:
        return store.get_artifacts_by_id(artifact_ids)
    except Exception as e:
        print('Failed to get artifact. Exception: "{}"'.format(str(e)), file=sys.stderr)


def put_artifact(store: metadata_store.MetadataStore, artifact: metadata_store_pb2.Artifact) -> None:
    # TODO: [sergey] this method raises `AlreadyExistsError` error. How does Cmf handle it (silently ignore)?
    try:
        store.put_artifacts([artifact])
    except Exception as e:
        print('Failed to put artifact . Exception: "{}"'.format(str(e)), file=sys.stderr)


def get_or_create_artifact_type(store: metadata_store.MetadataStore,
                                type_name: str,
                                properties: t.Optional[t.Dict] = None) -> metadata_store_pb2.ArtifactType:
    # TODO: [sergey] docs say the method raises two errors - NotFoundError and InternalError
    try:
        return store.get_artifact_type(type_name=type_name)
    except BaseException:
        artifact_type = metadata_store_pb2.ArtifactType(
            name=type_name,
            properties=properties,
        )
        artifact_type.id = store.put_artifact_type(artifact_type)  # Returns ID
        return artifact_type


def get_or_create_execution_type(store, type_name, properties: dict = None) -> metadata_store_pb2.ExecutionType:
    try:
        execution_type = store.get_execution_type(type_name=type_name)
        return execution_type
    except BaseException:
        execution_type = metadata_store_pb2.ExecutionType(
            name=type_name,
            properties=properties,
        )
        execution_type.id = store.put_execution_type(
            execution_type)  # Returns ID
        return execution_type


def get_or_create_context_type(store, type_name, properties: dict = None) -> metadata_store_pb2.ContextType:
    try:
        context_type = store.get_context_type(type_name=type_name)
        return context_type
    except BaseException:
        context_type = metadata_store_pb2.ContextType(
            name=type_name,
            properties=properties,
        )
        context_type.id = store.put_context_type(context_type)  # Returns ID
        return context_type


def create_artifact_with_type(
        store: metadata_store.MetadataStore,
        uri: str,
        name: str,
        type_name: str,
        properties: t.Optional[t.Dict] = None,
        type_properties: t.Optional[t.Dict] = None,
        custom_properties: t.Optional[t.Dict] = None,
) -> metadata_store_pb2.Artifact:
    # TODO [sergey]: what's the difference between properties and custom_properties?
    artifact_type = get_or_create_artifact_type(
        store=store,
        type_name=type_name,
        properties=type_properties,
    )
    artifact = metadata_store_pb2.Artifact(
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
        properties: dict = None,
        type_properties: dict = None,
        custom_properties: dict = None,
) -> metadata_store_pb2.Execution:
    execution_type = get_or_create_execution_type(
        store=store,
        type_name=type_name,
        properties=type_properties,
    )
    execution = metadata_store_pb2.Execution(
        type_id=execution_type.id,
        properties=properties,
        custom_properties=custom_properties,
    )
    execution.id = store.put_executions([execution])[0]
    return execution


def create_context_with_type(
        store,
        context_name: str,
        type_name: str,
        properties: dict = None,
        type_properties: dict = None,
        custom_properties: dict = None,
) -> metadata_store_pb2.Context:
    # ! Context_name must be unique
    context_type = get_or_create_context_type(
        store=store,
        type_name=type_name,
        properties=type_properties,
    )
    context = metadata_store_pb2.Context(
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
) -> metadata_store_pb2.Context:
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
        properties: dict = None,
        type_properties: dict = None,
        custom_properties: dict = None,
) -> metadata_store_pb2.Context:
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
        return context

    # Verifying that the context has the expected type name
    context_types = store.get_context_types_by_id([context.type_id])
    assert len(context_types) == 1
    if context_types[0].name != type_name:
        raise RuntimeError(
            'Context "{}" was found, but it has type "{}" instead of "{}"'.format(
                context_name, context_types[0].name, type_name))
    return context


def create_new_execution_in_existing_context(
        store,
        execution_type_name: str,
        context_id: int,
        properties: dict = None,
        execution_type_properties: dict = None,
        custom_properties: dict = None,
) -> metadata_store_pb2.Execution:
    execution = create_execution_with_type(
        store=store,
        properties=properties,
        custom_properties=custom_properties,
        type_name=execution_type_name,
        type_properties=execution_type_properties,
    )
    association = metadata_store_pb2.Association(
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

EXECUTION_REPO = "Git_Repo"
EXECUTION_START_COMMIT = "Git_Start_Commit"
EXECUTION_END_COMMIT = "Git_End_Commit"
EXECUTION_PIPELINE_TYPE = "Pipeline_Type"

EXECUTION_PIPELINE_ID = "Pipeline_id"


def get_or_create_parent_context(
        store,
        pipeline: str,
        custom_properties: t.Optional[t.Dict] = None
) -> metadata_store_pb2.Context:
    mlmd_custom_properties = {}
    for property_name, property_value in (custom_properties or {}).items():
        mlmd_custom_properties[property_name] = value_to_mlmd_value(
            property_value)

    context = get_or_create_context_with_type(
        store=store,
        context_name=pipeline,
        type_name=PARENT_CONTEXT_TYPE_NAME,
        type_properties={
            PARENT_CONTEXT_NAME: metadata_store_pb2.STRING,
        },
        properties={
            PARENT_CONTEXT_NAME: metadata_store_pb2.Value(
                string_value=pipeline)},
        custom_properties=mlmd_custom_properties)
    return context


def get_or_create_run_context(
        store,
        pipeline_stage: str,
        custom_properties: t.Optional[t.Dict] = None,
) -> metadata_store_pb2.Context:
    mlmd_custom_properties = {}
    for property_name, property_value in (custom_properties or {}).items():
        mlmd_custom_properties[property_name] = value_to_mlmd_value(
            property_value)

    context = get_or_create_context_with_type(
        store=store,
        context_name=pipeline_stage,
        type_name=PIPELINE_STAGE,
        type_properties={
            PIPELINE_STAGE: metadata_store_pb2.STRING,
        },
        properties={
            PIPELINE_STAGE: metadata_store_pb2.Value(
                string_value=pipeline_stage)},
        custom_properties=mlmd_custom_properties)
    return context


def associate_child_to_parent_context(store, parent_context: metadata_store_pb2.Context,
                                      child_context: metadata_store_pb2.Context):
    try:
        associate = metadata_store_pb2.ParentContext(
            child_id=child_context.id, parent_id=parent_context.id)
        store.put_parent_contexts([associate])
    except Exception as e:
        # print(e)
        # print('Warning: Exception:{}'.format(str(e)), file=sys.stderr)
        sys.stderr.flush()


def create_new_execution_in_existing_run_context(
        store,
        execution_type_name: str = None,  # TRAINING EXECUTION
        context_id: int = 0,  # TRAINING CONTEXT ASSOCIATED WITH THIS EXECUTION
        execution: str = None,
        pipeline_id: int = 0,  # THE PARENT CONTEXT
        pipeline_type: str = None,
        git_repo: str = None,
        git_start_commit: str = None,
        git_end_commit: str = "",
        custom_properties: t.Optional[t.Dict] = None,
) -> metadata_store_pb2.Execution:
    mlmd_custom_properties = {}
    for property_name, property_value in (custom_properties or {}).items():
        mlmd_custom_properties[property_name] = value_to_mlmd_value(
            property_value)

    return create_new_execution_in_existing_context(
        store=store,
        execution_type_name=execution_type_name,
        context_id=context_id,
        execution_type_properties={
            EXECUTION_CONTEXT_NAME_PROPERTY_NAME: metadata_store_pb2.STRING,
            EXECUTION_CONTEXT_ID: metadata_store_pb2.INT,
            EXECUTION_EXECUTION: metadata_store_pb2.STRING,
            EXECUTION_PIPELINE_TYPE: metadata_store_pb2.STRING,
            EXECUTION_PIPELINE_ID: metadata_store_pb2.INT,
            EXECUTION_REPO: metadata_store_pb2.STRING,
            EXECUTION_START_COMMIT: metadata_store_pb2.STRING,
            EXECUTION_END_COMMIT: metadata_store_pb2.STRING,
        },

        properties={
            EXECUTION_CONTEXT_NAME_PROPERTY_NAME: metadata_store_pb2.Value(string_value=execution_type_name),
            # Mistakenly used for grouping in the UX
            EXECUTION_CONTEXT_ID: metadata_store_pb2.Value(int_value=context_id),
            EXECUTION_EXECUTION: metadata_store_pb2.Value(string_value=execution),
            EXECUTION_PIPELINE_TYPE: metadata_store_pb2.Value(string_value=pipeline_type),
            EXECUTION_PIPELINE_ID: metadata_store_pb2.Value(int_value=pipeline_id),
            EXECUTION_REPO: metadata_store_pb2.Value(string_value=git_repo),
            EXECUTION_START_COMMIT: metadata_store_pb2.Value(string_value=git_start_commit),
            EXECUTION_END_COMMIT: metadata_store_pb2.Value(string_value=git_end_commit)
            # should set to task ID, not component ID
        },
        custom_properties=mlmd_custom_properties,
    )


def create_new_artifact_event_and_attribution(
        store: metadata_store.MetadataStore,
        execution_id: int,  # Stage execution ID
        context_id: int,  # Stage context ID
        uri: str,
        name: str,
        type_name: str,  # This seems to be the key: artifact type name (e.g., Dataset)
        event_type: metadata_store_pb2.Event.Type,  # INPUT or OUTPUT
        properties: t.Optional[t.Dict] = None,
        artifact_type_properties: t.Optional[t.Dict] = None,
        custom_properties: t.Optional[t.Dict] = None,
        artifact_name_path: t.Optional[metadata_store_pb2.Event.Path] = None,
        milliseconds_since_epoch: t.Optional[int] = None,
) -> metadata_store_pb2.Artifact:
    """ Create new artifact.

    This method is called from methods such as log_dataset. This method:
        - Creates a new artifact instance.
        - Creates a new event instance (input / output) associating this artifact with this stage execution
        - Creates a new attribution associating artifact with this stage context.

    TODO: [sergey] what's `artifact_name_path`?
    """
    mlmd_properties = {}
    for property_name, property_value in (properties or {}).items():
        mlmd_properties[property_name] = value_to_mlmd_value(property_value)

    mlmd_custom_properties = {}
    for property_name, property_value in (custom_properties or {}).items():
        mlmd_custom_properties[property_name] = value_to_mlmd_value(property_value)

    artifact = create_artifact_with_type(
        store=store,
        uri=uri,
        name=name,
        type_name=type_name,
        type_properties=artifact_type_properties,
        properties=mlmd_properties,
        custom_properties=mlmd_custom_properties,
    )
    event = metadata_store_pb2.Event(
        execution_id=execution_id,
        artifact_id=artifact.id,
        type=event_type,
        path=artifact_name_path,
        milliseconds_since_epoch=milliseconds_since_epoch,
    )
    store.put_events([event])
    attribution = metadata_store_pb2.Attribution(
        context_id=context_id,
        artifact_id=artifact.id,
    )
    store.put_attributions_and_associations([attribution], [])

    return artifact


def link_execution_to_input_artifact(
        store: metadata_store.MetadataStore,
        execution_id: int,
        uri: str,
        input_name: str,
) -> t.Optional[metadata_store_pb2.Artifact]:
    artifacts = store.get_artifacts_by_uri(uri)
    if len(artifacts) == 0:
        print('Error: Not found upstream artifact with URI={}.'.format(uri), file=sys.stderr)
        return None
    if len(artifacts) > 1:
        print('Error: Found multiple artifacts with the same URI. {} Using the last one..'.format(artifacts),
              file=sys.stderr)

    artifact = artifacts[-1]

    event = metadata_store_pb2.Event(
        execution_id=execution_id,
        artifact_id=artifact.id,
        type=metadata_store_pb2.Event.INPUT,
        path=metadata_store_pb2.Event.Path(
            steps=[
                metadata_store_pb2.Event.Path.Step(
                    key=input_name,
                ),
            ]
        ),
    )
    store.put_events([event])

    return artifact


def link_execution_to_artifact(
        store: metadata_store.MetadataStore,
        execution_id: int,
        uri: str,
        input_name: str,
        event_type: metadata_store_pb2.Event
) -> metadata_store_pb2.Artifact:
    # TODO: [sergey] the caller does not expect this function returns None.
    # TODO: [sergey] what's input_name?
    artifacts: t.List[metadata_store_pb2.Artifact] = store.get_artifacts_by_uri(uri)
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

    event = metadata_store_pb2.Event(
        execution_id=execution_id,
        artifact_id=artifact.id,
        type=event_type,
        path=metadata_store_pb2.Event.Path(
            steps=[
                metadata_store_pb2.Event.Path.Step(
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
