import json
import typing as t
from cmflib.callback import (Callback, ArtifactEvent, Artifact)
import mlflow
import mlflow.entities
from ml_metadata.proto import metadata_store_pb2 as mlpb


__all__ = ['MLflowCallback']


class MLflowCallback(Callback):
    """Callback to report Cmf data to MLflow.

    TODO: work in progress.
    """
    def __init__(self) -> None:
        self.pipeline_run: t.Optional[mlflow.entities.Run] = None
        self.stage_run: t.Optional[mlflow.entities.Run] = None

    def on_pipeline_context(self, name: str, id_, properties: t.Optional[t.Dict]) -> None:
        # End all active runs
        while mlflow.active_run() is not None:
            mlflow.end_run()

        # Find or create and then start or resume a run for this pipeline.
        runs: t.List[mlflow.entities.Run] = mlflow.search_runs(
            filter_string=f"tags.cmf_id = {id_}", output_format='list'
        )
        pipeline_run_id: t.Optional[str] = runs[0].info.run_id if runs else None
        self.pipeline_run = mlflow.start_run(
            run_id=pipeline_run_id,
            tags={'cmf_id': id_, 'cmf_name': name, 'cmf_type': 'pipeline'}
        )
        # Log pipeline properties as MLflow run parameters.
        # TODO: are properties parameters or tags?
        self._log_properties(self.pipeline_run.info.run_id, properties)

    def on_stage_context(self, name: str, id_, properties: t.Optional[t.Dict], pipeline_context: mlpb.Context) -> None:
        # Check that pipeline run is active now.
        self._check_active_run(self.pipeline_run)

        # Add new parameter to pipeline run with information for this stage.
        client = mlflow.tracking.MlflowClient()
        client.log_param(
            run_id=self.pipeline_run.info.run_id,
            key=f'cmf_stage_{name}',
            value=json.dumps({'name': name, 'id': id_, 'properties': properties or {}})
        )

    def on_stage_execution(self, name: str, id_, properties: t.Optional[t.Dict],
                           stage_context: mlpb.Context, pipeline_context: mlpb.Context,
                           is_new: bool) -> None:
        if is_new:
            if self.stage_run is not None:
                self._check_active_run(self.stage_run)
                mlflow.end_run()
                self.stage_run = None
            self._check_active_run(self.pipeline_run)
            self.stage_run = mlflow.start_run(
                tags={'cmf_id': id_, 'cmf_name': name, 'cmf_type': 'stage', 'cmf_stage_context_id': stage_context.id,
                      'cmf_pipeline_context_id': pipeline_context.id},
                nested=True
            )
        self._check_active_run(self.stage_run)
        self._log_properties(self.stage_run.info.run_id, properties)

    def on_artifact_event(self, event: ArtifactEvent, artifact: Artifact) -> None:
        # Check that active run is the expected stage run
        self._check_active_run(self.stage_run)
        # The `mlmd_event` variable is either `input` or `output`
        mlmd_event = event.to_mlmd_string()
        events: t.List[t.Dict] = json.loads(self.stage_run.data.tags.get(mlmd_event, '[]'))
        # Update run's tag
        if event == ArtifactEvent.CONSUMED:
            event_info = {'uri': artifact.uri}
        else:
            event_info = {
                'type': artifact.type, 'uri': artifact.uri, 'properties': artifact.custom_props or {}
            }

        events.append(event_info)
        mlflow.tracking.MlflowClient().set_tag(self.stage_run.info.run_id, mlmd_event, json.dumps(events))
        self.stage_run = mlflow.get_run(self.stage_run.info.run_id)

    @staticmethod
    def _log_properties(run_id: str, properties: t.Optional[t.Dict]) -> None:
        """Log properties for the given MLflow run."""
        if properties:
            client = mlflow.tracking.MlflowClient()
            for name, value in properties.items():
                client.log_param(run_id, name, value)

    @staticmethod
    def _check_active_run(expected_run: t.Optional[mlflow.entities.Run]) -> None:
        """Check that expected and active runs exist and are the same."""
        active_run: t.Optional[mlflow.ActiveRun] = mlflow.active_run()
        assert active_run is not None, "MLflow active run must be active now."
        assert expected_run is not None, "Expected run must be known."
        assert expected_run.info.run_id == active_run.info.run_id, "Expected and active runs do not match."
