import os
import functools
import sys
import typing as t
from time import sleep
from ml_metadata.proto import metadata_store_pb2 as mlpb
from ml_metadata.metadata_store.metadata_store import MetadataStore
from .store import MetadataStore
from ipaddress import ip_address, IPv4Address

__all__ = ['MlmdStore']


class MlmdStore(MetadataStore):
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

    def __init__(self, backend='sqlite', config: t.Optional[t.Dict] = None) -> None:
        config = config or {}
        connection_config = mlpb.ConnectionConfig()

        if backend == 'sqlite':
            connection_config.sqlite.filename_uri = config.get('filename', 'mlmd')
        else:
            raise ValueError(f"Unsupported MLMD backend: '{backend}'.")

        self.store = MetadataStore(connection_config)

    def get_or_create_parent_context(self, pipeline: str, custom_properties: t.Optional[t.Dict] = None) -> mlpb.Context:
        mlmd_custom_properties = {}
        for property_name, property_value in (custom_properties or {}).items():
            mlmd_custom_properties[property_name] = self._value_to_mlmd_value(property_value)

        context = self._get_or_create_context_with_type(
            context_name=pipeline,
            type_name=self.PARENT_CONTEXT_TYPE_NAME,
            type_properties={
                self.PARENT_CONTEXT_NAME: mlpb.STRING,
            },
            properties={
                self.PARENT_CONTEXT_NAME: mlpb.Value(string_value=pipeline)
            },
            custom_properties=mlmd_custom_properties)
        return context

    def get_or_create_run_context(self, pipeline_stage: str,
                                  custom_properties: t.Optional[t.Dict] = None) -> mlpb.Context:
        mlmd_custom_properties = {}
        for property_name, property_value in (custom_properties or {}).items():
            mlmd_custom_properties[property_name] = self._value_to_mlmd_value(property_value)

        context = self._get_or_create_context_with_type(
            context_name=pipeline_stage,
            type_name=self.PIPELINE_STAGE,
            type_properties={
                self.PIPELINE_STAGE: mlpb.STRING,
            },
            properties={
                self.PIPELINE_STAGE: mlpb.Value(string_value=pipeline_stage)
            },
            custom_properties=mlmd_custom_properties
        )
        return context

    def associate_child_to_parent_context(self, parent_context: mlpb.Context, child_context: mlpb.Context) -> None:
        try:
            associate = mlpb.ParentContext(child_id=child_context.id, parent_id=parent_context.id)
            self.store.put_parent_contexts([associate])
        except Exception as e:
            # print(e)
            # print('Warning: Exception:{}'.format(str(e)), file=sys.stderr)
            sys.stderr.flush()

    def link_execution_to_artifact(
            self,
            execution_id: int,
            uri: str,
            input_name: str,
            event_type: mlpb.Event
    ) -> mlpb.Artifact:
        artifacts = self.store.get_artifacts_by_uri(uri)
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
        events = self.store.get_events_by_artifact_ids([artifact.id])
        for evt in events:
            if evt.execution_id == execution_id:
                return artifact

        event = mlpb.Event(
            execution_id=execution_id,
            artifact_id=artifact.id,
            type=event_type,
            path=mlpb.Event.Path(
                steps=[
                    mlpb.Event.Path.Step(
                        key=input_name,
                    ),

                ]
            ),
        )
        self.store.put_events([event])

        return artifact

    def link_execution_to_input_artifact(
            self,
            execution_id: int,
            uri: str,
            input_name: str,
    ) -> mlpb.Artifact:
        artifacts = self.store.get_artifacts_by_uri(uri)
        if len(artifacts) == 0:
            print('Error: Not found upstream artifact with URI={}.'.format(uri), file=sys.stderr)
            return None
        if len(artifacts) > 1:
            print('Error: Found multiple artifacts with the same URI. {} Using the last one..'.format(artifacts),
                  file=sys.stderr)

        artifact = artifacts[-1]

        event = mlpb.Event(
            execution_id=execution_id,
            artifact_id=artifact.id,
            type=mlpb.Event.INPUT,
            path=mlpb.Event.Path(
                steps=[
                    mlpb.Event.Path.Step(
                        key=input_name,
                    ),
                ]
            ),
        )
        self.store.put_events([event])

        return artifact

    def create_new_execution_in_existing_run_context(
            self,
            execution_type_name: str = None,  # TRAINING EXECUTION
            context_id: int = 0,  # TRAINING CONTEXT ASSOCIATED WITH THIS EXECUTION
            execution: str = None,
            pipeline_id: int = 0,  # THE PARENT CONTEXT
            pipeline_type: str = None,
            git_repo: str = None,
            git_start_commit: str = None,
            git_end_commit: str = "",
            custom_properties: t.Optional[t.Dict] = None,
    ) -> mlpb.Execution:
        mlmd_custom_properties = {}
        for property_name, property_value in (custom_properties or {}).items():
            mlmd_custom_properties[property_name] = self._value_to_mlmd_value(property_value)

        return self._create_new_execution_in_existing_context(
            execution_type_name=execution_type_name,
            context_id=context_id,
            execution_type_properties={
                self.EXECUTION_CONTEXT_NAME_PROPERTY_NAME: mlpb.STRING,
                self.EXECUTION_CONTEXT_ID: mlpb.INT,
                self.EXECUTION_EXECUTION: mlpb.STRING,
                self.EXECUTION_PIPELINE_TYPE: mlpb.STRING,
                self.EXECUTION_PIPELINE_ID: mlpb.INT,
                self.EXECUTION_REPO: mlpb.STRING,
                self.EXECUTION_START_COMMIT: mlpb.STRING,
                self.EXECUTION_END_COMMIT: mlpb.STRING,
            },
            properties={
                self.EXECUTION_CONTEXT_NAME_PROPERTY_NAME: mlpb.Value(string_value=execution_type_name),
                # Mistakenly used for grouping in the UX
                self.EXECUTION_CONTEXT_ID: mlpb.Value(int_value=context_id),
                self.EXECUTION_EXECUTION: mlpb.Value(string_value=execution),
                self.EXECUTION_PIPELINE_TYPE: mlpb.Value(string_value=pipeline_type),
                self.EXECUTION_PIPELINE_ID: mlpb.Value(int_value=pipeline_id),
                self.EXECUTION_REPO: mlpb.Value(string_value=git_repo),
                self.EXECUTION_START_COMMIT: mlpb.Value(string_value=git_start_commit),
                self.EXECUTION_END_COMMIT: mlpb.Value(string_value=git_end_commit)
                # should set to task ID, not component ID
            },
            custom_properties=mlmd_custom_properties,
        )

    def create_new_artifact_event_and_attribution(
            self,
            execution_id: int,
            context_id: int,
            uri: str,
            name: str,
            type_name: str,
            event_type: mlpb.Event.Type,
            properties: dict = None,
            artifact_type_properties: dict = None,
            custom_properties: dict = None,
            artifact_name_path: mlpb.Event.Path = None,
            milliseconds_since_epoch: int = None,
    ) -> mlpb.Artifact:
        mlmd_properties = {}
        for property_name, property_value in (properties or {}).items():
            mlmd_properties[property_name] = self._value_to_mlmd_value(property_value)

        mlmd_custom_properties = {}
        for property_name, property_value in (custom_properties or {}).items():
            mlmd_custom_properties[property_name] = self._value_to_mlmd_value(
                property_value)

        artifact = self._create_artifact_with_type(
            uri=uri,
            name=name,
            type_name=type_name,
            type_properties=artifact_type_properties,
            properties=mlmd_properties,
            custom_properties=mlmd_custom_properties,
        )
        event = mlpb.Event(
            execution_id=execution_id,
            artifact_id=artifact.id,
            type=event_type,
            path=artifact_name_path,
            milliseconds_since_epoch=milliseconds_since_epoch,
        )
        self.store.put_events([event])
        attribution = mlpb.Attribution(
            context_id=context_id,
            artifact_id=artifact.id,
        )
        self.store.put_attributions_and_associations([attribution], [])

        return artifact

    def get_artifacts_by_id(self, artifact_id: [int]) -> t.List[mlpb.Artifact]:
        try:
            artifacts = self.store.get_artifacts_by_id(artifact_id)
            return artifacts

        except Exception as e:
            print('Failed to get artifact. Exception: "{}"'.format(str(e)), file=sys.stderr)

    def get_artifacts_by_uri(self, uri: str) -> t.List[mlpb.Artifact]:
        return self.store.get_artifacts_by_uri(uri)

    def get_executions_by_id(self, execution_id) -> t.List[mlpb.Execution]:
        return self.store.get_executions_by_id([execution_id])

    def get_execution_types_by_id(self, type_id) -> t.List[mlpb.ExecutionType]:
        return self.store.get_execution_types_by_id([type_id])

    def put_artifact(self, artifact: mlpb.Artifact) -> None:
        try:
            self.store.put_artifacts([artifact])
        except Exception as e:
            print('Failed to put artifact . Exception: "{}"'.format(str(e)), file=sys.stderr)

    def put_execution(self, execution: mlpb.Execution) -> None:
        self.store.put_executions([execution])

    @staticmethod
    def _value_to_mlmd_value(value) -> mlpb.Value:
        if value is None:
            return mlpb.Value()
        if isinstance(value, int):
            return mlpb.Value(int_value=value)
        if isinstance(value, float):
            return mlpb.Value(double_value=value)
        return mlpb.Value(string_value=str(value))

    def _get_or_create_context_with_type(
            self,
            context_name: str,
            type_name: str,
            properties: dict = None,
            type_properties: dict = None,
            custom_properties: dict = None,
    ) -> mlpb.Context:
        try:
            context = self._get_context_by_name(context_name)
        except BaseException:
            context = self._create_context_with_type(
                context_name=context_name,
                type_name=type_name,
                properties=properties,
                type_properties=type_properties,
                custom_properties=custom_properties,
            )
            return context

        # Verifying that the context has the expected type name
        context_types = self.store.get_context_types_by_id([context.type_id])
        assert len(context_types) == 1
        if context_types[0].name != type_name:
            raise RuntimeError(
                'Context "{}" was found, but it has type "{}" instead of "{}"'.format(
                    context_name, context_types[0].name, type_name))
        return context

    @functools.lru_cache(maxsize=128)
    def _get_context_by_name(
            self,
            context_name: str,
    ) -> mlpb.Context:
        matching_contexts = [
            context for context in self.store.get_contexts() if context.name == context_name]
        assert len(matching_contexts) <= 1
        if len(matching_contexts) == 0:
            raise ValueError(
                'Context with name "{}" was not found'.format(context_name))
        return matching_contexts[0]

    def _create_context_with_type(
            self,
            context_name: str,
            type_name: str,
            properties: dict = None,
            type_properties: dict = None,
            custom_properties: dict = None,
    ) -> mlpb.Context:
        # ! Context_name must be unique
        context_type = self._get_or_create_context_type(
            type_name=type_name,
            properties=type_properties,
        )
        context = mlpb.Context(
            name=context_name,
            type_id=context_type.id,
            properties=properties,
            custom_properties=custom_properties,
        )
        context.id = self.store.put_contexts([context])[0]
        return context

    def _get_or_create_context_type(self, type_name, properties: dict = None) -> mlpb.ContextType:
        try:
            context_type = self.store.get_context_type(type_name=type_name)
            return context_type
        except BaseException:
            context_type = mlpb.ContextType(
                name=type_name,
                properties=properties,
            )
            context_type.id = self.store.put_context_type(context_type)  # Returns ID
            return context_type

    def _create_new_execution_in_existing_context(
            self,
            execution_type_name: str,
            context_id: int,
            properties: dict = None,
            execution_type_properties: dict = None,
            custom_properties: dict = None,
    ) -> mlpb.Execution:
        execution = self._create_execution_with_type(
            properties=properties,
            custom_properties=custom_properties,
            type_name=execution_type_name,
            type_properties=execution_type_properties,
        )
        association = mlpb.Association(
            execution_id=execution.id,
            context_id=context_id,
        )

        self.store.put_attributions_and_associations([], [association])
        return execution

    def _create_execution_with_type(
            self,
            type_name: str,
            properties: dict = None,
            type_properties: dict = None,
            custom_properties: dict = None,
    ) -> mlpb.Execution:
        execution_type = self._get_or_create_execution_type(
            type_name=type_name,
            properties=type_properties,
        )
        execution = mlpb.Execution(
            type_id=execution_type.id,
            properties=properties,
            custom_properties=custom_properties,
        )
        execution.id = self.store.put_executions([execution])[0]
        return execution

    def _get_or_create_execution_type(self, type_name, properties: dict = None) -> mlpb.ExecutionType:
        try:
            execution_type = self.store.get_execution_type(type_name=type_name)
            return execution_type
        except BaseException:
            execution_type = mlpb.ExecutionType(
                name=type_name,
                properties=properties,
            )
            execution_type.id = self.store.put_execution_type(execution_type)  # Returns ID
            return execution_type

    def _create_artifact_with_type(
            self,
            uri: str,
            name: str,
            type_name: str,
            properties: dict = None,
            type_properties: dict = None,
            custom_properties: dict = None,
    ) -> mlpb.Artifact:
        artifact_type = self._get_or_create_artifact_type(
            type_name=type_name,
            properties=type_properties,
        )
        artifact = mlpb.Artifact(
            uri=uri,
            name=name,
            type_id=artifact_type.id,
            properties=properties,
            custom_properties=custom_properties,
        )
        artifact.id = self.store.put_artifacts([artifact])[0]
        return artifact

    def _get_or_create_artifact_type(self, type_name, properties: dict = None) -> mlpb.ArtifactType:
        try:
            artifact_type = self.store.get_artifact_type(type_name=type_name)
            return artifact_type
        except BaseException:
            artifact_type = mlpb.ArtifactType(
                name=type_name,
                properties=properties,
            )
            artifact_type.id = self.store.put_artifact_type(artifact_type)  # Returns ID
            return artifact_type


# Is this function unused?
def connect_to_mlmd() -> MetadataStore:
    metadata_service_host = os.environ.get(
        'METADATA_GRPC_SERVICE_SERVICE_HOST', 'metadata-grpc-service')
    metadata_service_port = int(os.environ.get(
        'METADATA_GRPC_SERVICE_SERVICE_PORT', 8080))

    mlmd_connection_config = mlpb.MetadataStoreClientConfig(
        host="[{}]".format(metadata_service_host) if isIPv6(metadata_service_host) else metadata_service_host,
        port=metadata_service_port,
    )

    # Checking the connection to the Metadata store.
    for _ in range(100):
        try:
            mlmd_store = MetadataStore(mlmd_connection_config)
            # All get requests fail when the DB is empty, so we have to use a put request.
            # TODO: Replace with _ = mlmd_store.get_context_types()
            # when https://github.com/google/ml-metadata/issues/28 is fixed
            _ = mlmd_store.put_execution_type(
                mlpb.ExecutionType(
                    name="DummyExecutionType",
                )
            )
            return mlmd_store
        except Exception as e:
            print('Failed to access the Metadata store. Exception: "{}"'.format(str(e)), file=sys.stderr)
            sys.stderr.flush()
            sleep(1)

    raise RuntimeError('Could not connect to the Metadata store.')


def isIPv6(ip: str) -> bool:
    try:
        return False if type(ip_address(ip)) is IPv4Address else True
    except Exception as e:
        print('Error: Exception:{}'.format(str(e)), file=sys.stderr)
        sys.stderr.flush()
