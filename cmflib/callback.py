import abc
import typing as t
from enum import Enum

from ml_metadata.proto import metadata_store_pb2 as mlpb


class ArtifactEvent(Enum):
    """A helper class to work with Cmf's and MLMD's event types (input / output)"""

    CONSUMED = 1
    """Event type: 'input'"""
    PRODUCED = 2
    """Event type: 'output'"""

    @classmethod
    def from_string(cls, event: str) -> 'ArtifactEvent':
        """Convert MLMD's event string to this enum."""
        event = event.lower()
        if event == 'input':
            return ArtifactEvent.CONSUMED
        if event == 'output':
            return ArtifactEvent.PRODUCED
        raise ValueError(f"Invalid artifact event: {event}. Valid values are (input, output).")

    def to_mlmd_string(self) -> str:
        """Convert this enum to MLMD's string."""
        if self == ArtifactEvent.CONSUMED:
            return 'input'
        return 'output'


class Artifact:
    """Base class for all artifacts that Cmf uses to communicate with its subscribers (via callback mechanism).

    TODO: Needs a little refactoring (remove `event` parameter, maybe replace execution_id with execution)
    """
    type: str = 'artifact'
    """String identifier of this artifact."""

    def __init__(self, uri: str, event: str, execution_id, parent_context: mlpb.Context, custom_props: t.Dict,
                 execution_label_props: t.Dict) -> None:
        self.uri: str = uri
        self.event: str = event.lower()
        self.execution_id = execution_id
        self.parent_context: mlpb.Context = parent_context
        self.custom_props: t.Dict = custom_props
        self.execution_label_props: t.Dict = execution_label_props


class Dataset(Artifact):
    """Machine learning dataset."""
    type: str = 'dataset'

    def __init__(self, name: str, url: str, uri: str, event: str, execution_id, parent_context: mlpb.Context,
                 custom_props: t.Dict, execution_label_props: t.Dict) -> None:
        super().__init__(uri, event, execution_id, parent_context, custom_props, execution_label_props)
        self.url: str = url
        self.name: str = name


class Model(Artifact):
    """Machine learning model."""
    type: str = 'model'

    def __init__(self, model_uri: str, uri: str, event: str, execution_id, parent_context: mlpb.Context,
                 custom_props: t.Dict, execution_label_props: t.Dict) -> None:
        super().__init__(uri, event, execution_id, parent_context, custom_props, execution_label_props)
        self.model_uri: str = model_uri


class ExecutionMetrics(Artifact):
    """Stage-level performance metrics (those that are reported at the end of a stage, e.g., test accuracy)."""
    type: str = 'execution_metrics'

    def __init__(self, metrics_name: str, uri: str, event: str, execution_id, parent_context: mlpb.Context,
                 custom_props: t.Dict, execution_label_props: t.Dict) -> None:
        super().__init__(uri, event, execution_id, parent_context, custom_props, execution_label_props)
        self.metrics_name: str = metrics_name


class Callback:
    """Base class for Cmf callbacks.

    TODO: (sergey) no support for real-time metric logging. All metrics are logged at the end in `on_artifact_event`.
    """

    @abc.abstractmethod
    def on_pipeline_context(self, name: str, id_, properties: t.Optional[t.Dict]) -> None:
        """Is called when a new or existing pipeline becomes available."""
        ...

    @abc.abstractmethod
    def on_stage_context(self, name: str, id_, properties: t.Optional[t.Dict],
                         pipeline_context: mlpb.Context) -> None:
        """Is called when a new or existing stage context becomes available."""
        ...

    @abc.abstractmethod
    def on_stage_execution(self, name: str, id_, properties: t.Optional[t.Dict],
                           stage_context: mlpb.Context, pipeline_context: mlpb.Context,
                           is_new: bool) -> None:
        """Is called when a new stage execution is created, or when properties of the existing one to be updated."""
        ...

    @abc.abstractmethod
    def on_artifact_event(self, event: ArtifactEvent, artifact: Artifact) -> None:
        """Is called when a new artifact is consumed or produced by a stage."""
        ...


class LifeCycleStageGuard(Callback):
    """A helper callback to identify bugs related to improper use of the Cmf API.

    TODO: work in progress.
    """

    NOT_INITIALIZED = 0
    PIPELINE_CREATED = 1
    CONTEXT_CREATED = 2
    EXECUTION_CREATED = 3

    def __init__(self) -> None:
        self.stage = self.NOT_INITIALIZED

    def on_pipeline_context(self, name: str, id_, properties: t.Optional[t.Dict]) -> None:
        if self.stage != self.NOT_INITIALIZED:
            print("[WARNING] transition to `PIPELINE_CREATED` is only allowed from `NOT_INITIALIZED` state.")
        self.stage = self.PIPELINE_CREATED

    def on_stage_context(self, name: str, id_, properties: t.Optional[t.Dict], pipeline_context: mlpb.Context) -> None:
        if self.stage != self.PIPELINE_CREATED:
            print("[WARNING] transition to `CONTEXT_CREATED` is only allowed from `PIPELINE_CREATED` state.")
        self.stage = self.CONTEXT_CREATED

    def on_stage_execution(self, name: str, id_, properties: t.Optional[t.Dict],
                           stage_context: mlpb.Context, pipeline_context: mlpb.Context,
                           is_new: bool) -> None:
        if is_new:
            if self.stage not in (self.CONTEXT_CREATED, self.EXECUTION_CREATED):
                print("[WARNING] transition to `EXECUTION_CREATED` is only allowed from `CONTEXT_CREATED` or "
                      "`EXECUTION_CREATED` states.")
        else:
            if self.stage != self.EXECUTION_CREATED:
                print(
                    f"[WARNING] execution update is allowed in `EXECUTION_CREATED` stage. Current stage = {self.stage}"
                )
        self.stage = self.EXECUTION_CREATED

    def on_artifact_event(self, event: ArtifactEvent, artifact: Artifact) -> None:
        if self.stage != self.EXECUTION_CREATED:
            print(
                f"[WARNING] artifact event is only allowed in `EXECUTION_CREATED` stage. Current stage is {self.stage}"
            )
