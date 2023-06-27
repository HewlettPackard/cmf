import typing as t

import determined as det
import determined.experimental.unmanaged
import yaml
from ml_metadata.proto import metadata_store_pb2 as mlpb

from cmflib.callback import Artifact, ArtifactEvent, Callback, ExecutionMetrics

__all__ = ['DeterminedCallback']


class DeterminedCallback(Callback):
    """
    pip install determined
    det deploy local cluster-up [--no-gpu]
    """
    def __init__(self) -> None:
        self.client = det.experimental.Determined()
        self.cluster: t.Optional[det.ClusterInfo] = None
        self.context: t.Optional[det.experimental.unmanaged.Context] = None

    def on_pipeline_context(self, name: str, id_, properties: t.Optional[t.Dict]) -> None:
        # Properties are supposed to be providing pipeline metadata at pipeline definition level (e.g., all executions
        # of this pipeline share the same metadata fields).

        # This callback is ignored here - it will be available and will be processed in `on_stage_execution`.
        pass

    def on_stage_context(self, name: str, id_, properties: t.Optional[t.Dict], pipeline_context: mlpb.Context) -> None:
        # Properties are supposed to be providing stage metadata that:
        #   - Is shared across all executions of this stage.
        #   - Provide default values for metadata fields should some of these fields not be provided at execution time.
        # Stage name has the following format: `{pipeline_name}/{stage_name}`.

        # This callback is ignored here - it will be available and will be processed in `on_stage_execution`.
        pass

    def on_stage_execution(
            self, name: str, id_, properties: t.Optional[t.Dict], stage_context: mlpb.Context,
            pipeline_context: mlpb.Context, is_new: bool
    ) -> None:
        # Stage name has the following format: `{pipeline_name}/{stage_name}`:
        stage_names = stage_context.name.split("/", maxsplit=1)
        # Execution name has the following format: `{execution_id},{execution_name}`.
        exec_names = name.split(",", maxsplit=1)

        config = {
            # Let's assume the name is `PIPELINE.STAGE.EXEC_ID`
            "name": f"{pipeline_context.name}.{stage_names[1]}.{id_}",
            # We'll add many labels later.
            "labels": ["cmf"],
            # Another assumption - execution properties are hyperparameters.
            "hyperparameters": properties or {},
            # This seems to be required by Determined.
            "checkpoint_storage": {
                "host_path": "/tmp",
                "storage_path": "determined-cp",
                "type": "shared_fs"
            },
            # This seems to be required by Determined.
            "searcher": {
                "name": "single",
                "metric": "loss",
                "smaller_is_better": True,
                "max_length": {
                    "batches": 1
                }
            }
        }

        self._add_labels(config["labels"], "pipeline", pipeline_context)
        self._add_labels(config["labels"], "stage", stage_context)

        config["labels"].append(f"execution.name:{exec_names[1]}")
        config["labels"].append(f"execution.id:{id_}")
        for k, v in (properties or {}).items():
            config["labels"].append(f"execution.property.{k}:{v}")

        config["description"] = "PoC implementation of how CMF can send metadata to Determined."

        self.cluster = det.experimental.unmanaged.create_unmanaged_cluster_info(
            self.client, config_text=yaml.dump(config)
        )
        self.context = det.experimental.unmanaged.init(
            unmanaged_info=self.cluster, client=self.client
        )

    def on_artifact_event(self, event: ArtifactEvent, artifact: Artifact) -> None:
        print(f"[on_artifact_event] event={event}, artifact={artifact}.")
        if event == ArtifactEvent.CONSUMED:
            return
        if isinstance(artifact, ExecutionMetrics):
            # The `artifact.metrics_name` has the following format: ${metrics_name}:${file_hash}:{execution_id}:{guid}
            # The `metrics_name` component is the name of the metrics file containing pandas dataframe.
            # PS - Determined seems to require that all epoch metrics to be logged in one transaction (e.g., I can't
            #      log history of train metrics, and then history of validation metrics)
            import pandas as pd
            # Hopefully, epochs are properly sorted in increasing order.
            history: t.List[t.Dict] = pd.read_parquet(artifact.metrics_name.split(":")[0]).to_dict("records")
            for idx, epoch_metrics in enumerate(history):
                epoch: int = epoch_metrics.pop("epoch", idx+1)
                self.context.train.report_training_metrics(epoch, epoch_metrics)
        # TODO: (sergey) other artifacts such as datasets and models?

    @staticmethod
    def _add_labels(labels: t.List[str], root_ns: str, context: mlpb.Context) -> None:
        """Add labels for Determined run to the list of labels using.

        Args:
            labels: List of labels to add to.
            root_ns: Root namespace that all labels must share (e.g., ${root_ns}.label:value).
            context: Source of labels. The following fields will be used: `name`, `id` and `properties`.
        """
        labels.append(f"{root_ns}.name:{context.name}")
        labels.append(f"{root_ns}.id:{context.id}")
        for name, value in context.properties.items():
            # https://github.com/google/ml-metadata/blob/master/ml_metadata/proto/metadata_store.proto#L34
            field_name: str = value.WhichOneof("value")
            assert field_name in ("int_value", "double_value", "string_value", "bool_value"), f"Fix me ({field_name})."
            labels.append(f"{root_ns}.property.{name}:{getattr(value, field_name)}")
