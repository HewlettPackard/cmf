import os
import typing as t
from cmflib.callback import Callback, ArtifactEvent, Artifact, Dataset, Model, ExecutionMetrics
from ml_metadata.proto import metadata_store_pb2 as mlpb
from ._driver import GraphDriver

__all__ = ['Neo4JCallback']


class Neo4JCallback(Callback):
    """Callback to report Cmf data to Neo4J framework."""

    def __init__(self, uri: t.Optional[str], user: t.Optional[str], password: t.Optional[str]) -> None:
        # TODO: Does this need to be closed? This is from cmf.py:
        # if self.graph:
        #    self.driver.close()
        self.driver = GraphDriver(
            uri or os.getenv('NEO4J_URI', ''),
            user or os.getenv('NEO4J_USER_NAME', ''),
            password or os.getenv('NEO4J_PASSWD', '')
        )
        self.input_artifacts: t.List[t.Dict] = []
        self.execution_name: t.Optional[str] = None
        self.execution_command: t.Optional[str] = None

    def on_pipeline_context(self, name: str, id_, properties: t.Optional[t.Dict]) -> None:
        self.driver.create_pipeline_node(name, id_, properties)

    def on_stage_context(self, name: str, id_, properties: t.Optional[t.Dict],
                         pipeline_context: mlpb.Context) -> None:
        self.driver.create_stage_node(name, pipeline_context, id_, properties)

    def on_stage_execution(self, name: str, id_, properties: t.Optional[t.Dict],
                           stage_context: mlpb.Context, pipeline_context: mlpb.Context,
                           is_new: bool) -> None:
        if is_new:
            self.input_artifacts.clear()
            self.execution_name = name
            self.execution_command = stage_context.properties["Execution"].string_value
        else:
            # This is an update for current execution
            ...

        self.driver.create_execution_node(
            name, stage_context.id, pipeline_context, self.execution_command, id_, properties
        )

    def on_artifact_event(self, event: ArtifactEvent, artifact: Artifact) -> None:
        if isinstance(artifact, Dataset):
            self._on_dataset(event, artifact)
        elif isinstance(artifact, Model):
            self._on_model(event, artifact)
        elif isinstance(artifact, ExecutionMetrics):
            self._on_execution_metrics(event, artifact)
        else:
            raise ValueError(f"Unsupported artifact: {artifact}")

    def _on_dataset(self, event: ArtifactEvent, dataset: Dataset) -> None:
        self.driver.create_dataset_node(
            dataset.name, dataset.url, dataset.uri, dataset.event,
            dataset.execution_id, dataset.parent_context, dataset.custom_props
        )
        artifact_info = {
            "Name": dataset.name,
            "Path": dataset.url,
            "URI": dataset.uri,
            "Event": dataset.event,
            "Execution_Name": self.execution_name,
            "Type": "Dataset",
            "Execution_Command": self.execution_command,
            "Pipeline_Id": dataset.parent_context.id,
            "Pipeline_Name": dataset.parent_context.name
        }
        if event == ArtifactEvent.CONSUMED:
            self.input_artifacts.append(artifact_info)
            self.driver.create_execution_links(dataset.uri, dataset.name, "Dataset")
        else:
            self.driver.create_artifact_relationships(
                self.input_artifacts, artifact_info, dataset.execution_label_props
            )

    def _on_model(self, event: ArtifactEvent, model: Model) -> None:
        self.driver.create_model_node(
            model.model_uri, model.uri, model.event,
            model.execution_id, model.parent_context, model.custom_props
        )
        artifact_info = {
            "Name": model.model_uri,
            "URI": model.uri,
            "Event": model.event,
            "Execution_Name": self.execution_name,
            "Type": "Model",
            "Execution_Command": self.execution_command,
            "Pipeline_Id": model.parent_context.id,
            "Pipeline_Name": model.parent_context.name
        }
        if event == ArtifactEvent.CONSUMED:
            self.input_artifacts.append(artifact_info)
            self.driver.create_execution_links(model.uri, model.model_uri, "Model")
        else:
            self.driver.create_artifact_relationships(
                self.input_artifacts, artifact_info, model.execution_label_props
            )

    def _on_execution_metrics(self, event: ArtifactEvent, metrics: ExecutionMetrics) -> None:
        assert event == ArtifactEvent.PRODUCED, "Should this assert be here?"
        self.driver.create_metrics_node(
            metrics.metrics_name, metrics.uri, metrics.event,
            metrics.execution_id, metrics.parent_context, metrics.custom_props
        )
        artifact_info = {
            "Name": metrics.metrics_name,
            "URI": metrics.uri,
            "Event": metrics.event,
            "Execution_Name": self.execution_name,
            "Type": "Metrics",
            "Execution_Command": self.execution_command,
            "Pipeline_Id": metrics.parent_context.id,
            "Pipeline_Name": metrics.parent_context.name
        }
        self.driver.create_artifact_relationships(
            self.input_artifacts, artifact_info, metrics.execution_label_props
        )
