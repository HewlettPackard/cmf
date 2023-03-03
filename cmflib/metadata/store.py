import abc
import typing as t
from ml_metadata.proto import metadata_store_pb2 as mlpb

__all__ = ['MetadataStore']


class MetadataStore:
    @abc.abstractmethod
    def get_or_create_parent_context(self, pipeline: str, custom_properties: t.Optional[t.Dict] = None) -> mlpb.Context:
        ...

    @abc.abstractmethod
    def get_or_create_run_context(self, pipeline_stage: str,
                                  custom_properties: t.Optional[t.Dict] = None) -> mlpb.Context:
        ...

    @abc.abstractmethod
    def associate_child_to_parent_context(self, parent_context: mlpb.Context, child_context: mlpb.Context) -> None:
        ...

    @abc.abstractmethod
    def link_execution_to_artifact(
            self,
            execution_id: int,
            uri: str,
            input_name: str,
            event_type: mlpb.Event
    ) -> mlpb.Artifact:
        ...

    @abc.abstractmethod
    def link_execution_to_input_artifact(
            self,
            execution_id: int,
            uri: str,
            input_name: str,
    ) -> mlpb.Artifact:
        ...

    @abc.abstractmethod
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
        ...

    @abc.abstractmethod
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
        ...

    @abc.abstractmethod
    def get_artifacts_by_id(self, artifact_id: [int]) -> t.List[mlpb.Artifact]:
        ...

    @abc.abstractmethod
    def get_artifacts_by_uri(self, uri: str) -> t.List[mlpb.Artifact]:
        ...

    @abc.abstractmethod
    def get_executions_by_id(self, execution_id) -> t.List[mlpb.Execution]:
        ...

    @abc.abstractmethod
    def get_execution_types_by_id(self, type_id) -> t.List[mlpb.ExecutionType]:
        ...

    @abc.abstractmethod
    def put_artifact(self, artifact: mlpb.Artifact) -> None:
        ...

    @abc.abstractmethod
    def put_execution(self, execution: mlpb.Execution) -> None:
        ...
