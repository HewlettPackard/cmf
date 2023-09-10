###
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
import logging
import typing as t

import pandas as pd
from ml_metadata.metadata_store import metadata_store
from ml_metadata.proto import metadata_store_pb2 as mlpb

from cmflib.mlmd_objects import CONTEXT_LIST

__all__ = ["CmfQuery"]

logger = logging.getLogger(__name__)


class CmfQuery(object):
    """CMF Query communicates with the MLMD database and implements basic search and retrieval functionality.

    Args:
        filepath: Path to the MLMD database file.
    """

    def __init__(self, filepath: str = "mlmd") -> None:
        config = mlpb.ConnectionConfig()
        config.sqlite.filename_uri = filepath
        self.store = metadata_store.MetadataStore(config)

    @staticmethod
    def _copy(source: t.Mapping, target: t.Optional[t.Dict] = None, key_mapper: t.Optional[t.Dict] = None) -> t.Dict:
        """Create copy of `source` and return it, reuse `target` if not None.

        Args:
            source: Input dict-like object to create copy.
            target: If not None, this will be reused and returned. If None, new dict will be created.
            key_mapper: Dictionary containing how to map keys in `source`, e.g., {"key_in": "key_out"} means the
            key in `source` named "key_in" should be renamed to "key_out" in output dictionary object.
        Returns:
            If `target` is not None, it is returned containing data from `source`. Else, new object is returned.
        """
        if target is None:
            target = {}
        if key_mapper is None:
            key_mapper = {}

        for key, value in source.items():
            if value.HasField("string_value"):
                value = value.string_value
            elif value.HasField("int_value"):
                value = value.int_value
            else:
                value = value.double_value

            target[key_mapper.get(key, key)] = value

        return target

    @staticmethod
    def _transform_to_dataframe(
        node: t.Union[mlpb.Execution, mlpb.Artifact], d: t.Optional[t.Dict] = None
    ) -> pd.DataFrame:
        """Transform MLMD entity `node` to pandas data frame.

        Args:
            node: MLMD entity to transform.
            d: Pre-populated dictionary of KV-pairs to associate  with `node` (will become columns in output table).
        Returns:
            Pandas data frame with one row containing data from `node`.

        TODO: (sergey) Overwriting `d` with key/values from `properties` and `custom_properties` is not safe, some
              tests fail (`test_get_all_parent_executions`) - it happens to be the case that `id` gets overwritten. For
              instance, this happens when artifact is of type Dataset, and custom_properties contain id equal to
              `multi_nli`. Later, this `id` can be used to invoke other MLMD APIs and that fails.

        TODO: (sergey) Maybe add prefix for properties and custom_properties keys?
        """
        if d is None:
            d = {}

        keys_to_be_updated = set(d.keys()).intersection(node.properties.keys())
        if keys_to_be_updated:
            logger.warning(
                "Unsafe OP detected for node (type=%s, id=%i): existing node keys (%s) will be updated from "
                "node's `properties`.",
                type(node),
                node.id,
                keys_to_be_updated,
            )
        if "id" in node.properties:
            logger.warning(
                "Unsafe OP detected for node (type=%s, id=%i): will update `id` from properties (value=%s)",
                type(node),
                node.id,
                node.properties["id"],
            )
        d = CmfQuery._copy(node.properties, d)

        keys_to_be_updated = set(d.keys()).intersection(node.properties.keys())
        if keys_to_be_updated:
            logger.warning(
                "Unsafe OP detected for node (type=%s, id=%i): existing node keys (%s) will be updated from "
                "node's `custom_properties`.",
                type(node),
                node.id,
                keys_to_be_updated,
            )
        if "id" in node.custom_properties:
            logger.warning(
                "Unsafe OP detected for node (type=%s, id=%i): will update `id` from custom_properties (value=%s)",
                type(node),
                node.id,
                node.properties["id"],
            )
        d = CmfQuery._copy(node.custom_properties, d)

        return pd.DataFrame(
            d,
            index=[
                0,
            ],
        )

    @staticmethod
    def _as_pandas_df(elements: t.Iterable, transform_fn: t.Callable[[t.Any], pd.DataFrame]) -> pd.DataFrame:
        """Convert elements in `elements` to rows in pandas data frame using `transform_fn` function.

        Args:
            elements: Collection with items to be converted to tabular representation, each item becomes one row.
            transform_fn: A callable object that takes one element in `elements` and returns its tabular representation
                (pandas data frame with one row).
        Returns:
            Pandas data frame containing representation of elements in `elements` with one row being one element.

        TODO: maybe easier to initially transform elements to list of dicts?
        """
        df = pd.DataFrame()
        for element in elements:
            df = pd.concat([df, transform_fn(element)], sort=True, ignore_index=True)
        return df

    def _get_pipelines(self, name: t.Optional[str] = None) -> t.List[mlpb.Context]:
        """Return list of pipelines with the given name.

        Args:
            name: Piepline name or None to return all pipelines.
        Returns:
            List of objects associated with pipelines.

        TODO (sergey): Is `Parent_Context` value always used for pipelines?
        TODO (sergey): Why `name` parameter when there's another method `_get_pipeline`?
        TODO (sergey): Use `self.store.get_context_by_type_and_name` when name presents?
        """
        pipelines: t.List[mlpb.Context] = self.store.get_contexts_by_type("Parent_Context")
        if name is not None:
            pipelines = [pipeline for pipeline in pipelines if pipeline.name == name]
        return pipelines

    def _get_pipeline(self, name: str) -> t.Optional[mlpb.Context]:
        """Return a pipeline with the given name or None if one does not exist.
        Args:
            name: Pipeline name.
        Returns:
            A pipeline object if found, else None.

        TODO (sergey): Use `self.store.get_context_by_type_and_name` instead calling self._get_pipelines?
        """
        pipelines: t.List = self._get_pipelines(name)
        if pipelines:
            if len(pipelines) >= 2:
                logger.debug("Found %d pipelines with '%s' name.", len(pipelines), name)
            return pipelines[0]
        return None

    def _get_stages(self, pipeline_id: int) -> t.List[mlpb.Context]:
        """Return stages for the given pipeline.

        Args:
            pipeline_id: Pipeline ID.
        Returns:
            List of associated pipeline stages.
        """
        return self.store.get_children_contexts_by_context(pipeline_id)

    def _get_executions(self, stage_id: int, execution_id: t.Optional[int] = None) -> t.List[mlpb.Execution]:
        """Return executions of the given stage.

        Args:
            stage_id: Stage identifier.
            execution_id: If not None, return only execution with this ID.
        Returns:
            List of executions matching input parameters.
        """
        executions: t.List[mlpb.Execution] = self.store.get_executions_by_context(stage_id)
        if execution_id is not None:
            executions = [execution for execution in executions if execution.id == execution_id]
        return executions

    def _get_executions_by_input_artifact_id(self, artifact_id: int) -> t.List[int]:
        """Return stage executions that consumed given input artifact.

        Args:
            artifact_id: Identifier of the input artifact.
        Returns:
            List of stage executions that consumed the given artifact.
        """
        execution_ids = set(
            event.execution_id
            for event in self.store.get_events_by_artifact_ids([artifact_id])
            if event.type == mlpb.Event.INPUT
        )
        return list(execution_ids)

    def _get_executions_by_output_artifact_id(self, artifact_id: int) -> t.List[int]:
        """Return stage execution that produced given output artifact.

        Args:
            artifact_id: Identifier of the output artifact.
        Return:
            List of stage executions, should probably be size of 1 or zero.
        """
        execution_ids: t.List[int] = [
            event.execution_id
            for event in self.store.get_events_by_artifact_ids([artifact_id])
            if event.type == mlpb.Event.OUTPUT
        ]
        if len(execution_ids) >= 2:
            logger.warning("%d executions claim artifact (id=%d) as output.", len(execution_ids), artifact_id)

        return list(set(execution_ids))

    def _get_artifact(self, name: str) -> t.Optional[mlpb.Artifact]:
        """Return artifact with the given name or None.

        TODO: Different artifact types can have the same name (see `get_artifacts_by_type`,
              `get_artifact_by_type_and_name`).
        TODO: (sergey) Use `self.store.get_artifacts` with list_options (filter_query)?
        Args:
            name: Artifact name.
        Returns:
            Artifact or None (if not found).
        """
        name = name.strip()
        for artifact in self.store.get_artifacts():
            if artifact.name == name:
                return artifact
        return None

    def _get_output_artifacts(self, execution_ids: t.List[int]) -> t.List[int]:
        """Return output artifacts for the given executions.

        Args:
            execution_ids: List of execution identifiers to return output artifacts for.
        Returns:
            List of output artifact identifiers.

        TODO: (sergey) The `test_get_one_hop_child_artifacts` prints the warning in this method (Multiple executions
              claim the same output artifacts)
        """
        artifact_ids: t.List[int] = [
            event.artifact_id
            for event in self.store.get_events_by_execution_ids(set(execution_ids))
            if event.type == mlpb.Event.OUTPUT
        ]
        unique_artifact_ids = set(artifact_ids)
        if len(unique_artifact_ids) != len(artifact_ids):
            logger.warning("Multiple executions claim the same output artifacts")

        return list(unique_artifact_ids)

    def _get_input_artifacts(self, execution_ids: t.List[int]) -> t.List[int]:
        """Return input artifacts for the given executions.

        Args:
            execution_ids: List of execution identifiers to return input artifacts for.
        Returns:
            List of input artifact identifiers.
        """
        artifact_ids = set(
            event.artifact_id
            for event in self.store.get_events_by_execution_ids(set(execution_ids))
            if event.type == mlpb.Event.INPUT
        )
        return list(artifact_ids)

    def get_pipeline_names(self) -> t.List[str]:
        """Return names of all pipelines.

        Returns:
            List of all pipeline names.
        """
        return [ctx.name for ctx in self._get_pipelines()]

    def get_pipeline_id(self, pipeline_name: str) -> int:
        """Return pipeline identifier for the pipeline names `pipeline_name`.
        Args:
            pipeline_name: Name of the pipeline.
        Returns:
            Pipeline identifier or -1 if one does not exist.
        """
        pipeline: t.Optional[mlpb.Context] = self._get_pipeline(pipeline_name)
        return -1 if not pipeline else pipeline.id

    def get_pipeline_stages(self, pipeline_name: str) -> t.List[str]:
        """Return list of pipeline stages for the pipeline with the given name.

        Args:
            pipeline_name: Name of the pipeline for which stages need to be returned.
        Returns:
            List of stage names associated with the given pipeline.

        TODO: Can there be multiple pipelines with the same name?
        TODO: (sergey) not clear from method name that this method returns stage names
        """
        stages = []
        for pipeline in self._get_pipelines(pipeline_name):
            stages.extend(stage.name for stage in self._get_stages(pipeline.id))
        return stages

    def get_all_exe_in_stage(self, stage_name: str) -> t.List[mlpb.Execution]:
        """Return list of all executions for the stage with the given name.

        Args:
            stage_name: Name of the stage.
        Returns:
            List of executions for the given stage.

        TODO: Can stages from different pipelines have the same name?. Currently, the first matching stage is used to
              identify its executions. Also see "get_all_executions_in_stage".
        """
        for pipeline in self._get_pipelines():
            for stage in self._get_stages(pipeline.id):
                if stage.name == stage_name:
                    return self.store.get_executions_by_context(stage.id)
        return []

    def get_all_executions_in_stage(self, stage_name: str) -> pd.DataFrame:
        """Return executions of the given stage as pandas data frame.

        Args:
            stage_name: Stage name.
        Returns:
            Data frame with all executions associated with the given stage.

        TODO: Multiple stages with the same name? This method collects executions from all such stages. Also, see
              "get_all_exe_in_stage"
        """
        df = pd.DataFrame()
        for pipeline in self._get_pipelines():
            for stage in self._get_stages(pipeline.id):
                if stage.name == stage_name:
                    for execution in self._get_executions(stage.id):
                        ex_as_df: pd.DataFrame = self._transform_to_dataframe(
                            execution, {"id": execution.id, "name": execution.name}
                        )
                        df = pd.concat([df, ex_as_df], sort=True, ignore_index=True)
        return df

    def get_artifact_df(self, artifact: mlpb.Artifact, d: t.Optional[t.Dict] = None) -> pd.DataFrame:
        """Return artifact's data frame representation.

        Args:
            artifact: MLMD entity representing artifact.
            d: Optional initial content for data frame.
        Returns:
            A data frame with the single row containing attributes of this artifact.

        TODO: (sergey) there are no "public" methods that return `mlpb.Artifact`.
        TODO: (sergey) what's the  difference between this method and `get_artifact`?
        """
        if d is None:
            d = {}
        d.update(
            {
                "id": artifact.id,
                "type": self.store.get_artifact_types_by_id([artifact.type_id])[0].name,
                "uri": artifact.uri,
                "name": artifact.name,
                "create_time_since_epoch": artifact.create_time_since_epoch,
                "last_update_time_since_epoch": artifact.last_update_time_since_epoch,
            }
        )
        return self._transform_to_dataframe(artifact, d)

    def get_all_artifacts(self) -> t.List[str]:
        """Return names of all artifacts.

        Returns:
            List of all artifact names.

        TODO: (sergey) Can multiple artifacts have the same name?
        TODO: (sergey) Maybe rename to get_artifact_names (to be consistent with `get_pipeline_names`)?
        """
        return [artifact.name for artifact in self.store.get_artifacts()]

    get_artifact_names = get_all_artifacts

    def get_artifact(self, name: str) -> t.Optional[pd.DataFrame]:
        """Return artifact's data frame representation using artifact name.

        Args:
            name: Artifact name.
        Returns:
            Pandas data frame with one row containing attributes of this artifact.

        TODO: (sergey) what's the  difference between this method and `get_artifact_df`?
        """
        artifact: t.Optional[mlpb.Artifact] = self._get_artifact(name)
        if artifact:
            return self.get_artifact_df(artifact)
        return None

    def get_all_artifacts_for_execution(self, execution_id: int) -> pd.DataFrame:
        """Return input and output artifacts for the given execution.

        Args:
            execution_id: Execution identifier.
        Return:
            Data frame containing input and output artifacts for the given execution, one artifact per row.

        TODO: (sergey) briefly describe in what cases an execution may not have any artifacts.
        """
        df = pd.DataFrame()
        for event in self.store.get_events_by_execution_ids([execution_id]):
            event_type = "INPUT" if event.type == mlpb.Event.Type.INPUT else "OUTPUT"
            for artifact in self.store.get_artifacts_by_id([event.artifact_id]):
                df = pd.concat(
                    [df, self.get_artifact_df(artifact, {"event": event_type})], sort=True, ignore_index=True
                )
        return df

    def get_all_executions_for_artifact(self, artifact_name: str) -> pd.DataFrame:
        """Return executions that consumed and produced given artifact.

        Args:
            artifact_name: Artifact name.
        Returns:
            Pandas data frame containing stage executions, one execution per row.

        TODO: (sergey) build list of dicts and then convert to data frame - will be quicker.
        TODO: (sergey) can multiple contexts (pipeline and stage) be associated with one execution?
        """
        df = pd.DataFrame()

        artifact: t.Optional = self._get_artifact(artifact_name)
        if not artifact:
            return df

        for event in self.store.get_events_by_artifact_ids([artifact.id]):
            # TODO: (sergey) seems to be the same as stage below. What's this context for (stage or pipeline)?
            ctx = self.store.get_contexts_by_execution(event.execution_id)[0]
            linked_execution = {
                "Type": "INPUT" if event.type == mlpb.Event.Type.INPUT else "OUTPUT",
                "execution_id": event.execution_id,
                "execution_name": self.store.get_executions_by_id([event.execution_id])[0].name,
                "stage": self.store.get_contexts_by_execution(event.execution_id)[0].name,
                "pipeline": self.store.get_parent_contexts_by_context(ctx.id)[0].name,
            }
            d1 = pd.DataFrame(
                linked_execution,
                index=[
                    0,
                ],
            )
            df = pd.concat([df, d1], sort=True, ignore_index=True)
        return df

    def get_one_hop_child_artifacts(self, artifact_name: str) -> pd.DataFrame:
        """Get artifacts produced by executions that consume given artifact.

        Args:
            artifact name: Name of an artifact.
        Return:
            Output artifacts of all executions that consumed given artifact.
        """
        artifact: t.Optional = self._get_artifact(artifact_name)
        if not artifact:
            return pd.DataFrame()

        # Get output artifacts of executions consumed the above artifact.
        artifacts_ids = self._get_output_artifacts(self._get_executions_by_input_artifact_id(artifact.id))

        return self._as_pandas_df(
            self.store.get_artifacts_by_id(artifacts_ids), lambda _artifact: self.get_artifact_df(_artifact)
        )

    def get_all_child_artifacts(self, artifact_name: str) -> pd.DataFrame:
        """Return all downstream artifacts starting from the given artifact.

        Args:
            artifact_name: Artifact name.
        Returns:
            Data frame containing all child artifacts.

        TODO: Only output artifacts or all?
        """
        df = pd.DataFrame()
        d1 = self.get_one_hop_child_artifacts(artifact_name)
        # df = df.append(d1, sort=True, ignore_index=True)
        df = pd.concat([df, d1], sort=True, ignore_index=True)
        for row in d1.itertuples():
            d1 = self.get_all_child_artifacts(row.name)
            # df = df.append(d1, sort=True, ignore_index=True)
            df = pd.concat([df, d1], sort=True, ignore_index=True)
        df = df.drop_duplicates(subset=None, keep="first", inplace=False)
        return df

    def get_one_hop_parent_artifacts(self, artifact_name: str) -> pd.DataFrame:
        """Return input artifacts for the execution that produced the given artifact.

        Args:
            artifact_name
        """
        artifact: t.Optional = self._get_artifact(artifact_name)
        if not artifact:
            return pd.DataFrame()

        artifact_ids: t.List[int] = self._get_input_artifacts(self._get_executions_by_output_artifact_id(artifact.id))

        return self._as_pandas_df(
            self.store.get_artifacts_by_id(artifact_ids), lambda _artifact: self.get_artifact_df(_artifact)
        )

    def get_all_parent_artifacts(self, artifact_name: str) -> pd.DataFrame:
        """Return all upstream artifacts.

        TODO: All input and output artifacts?
        """
        df = pd.DataFrame()
        d1 = self.get_one_hop_parent_artifacts(artifact_name)
        # df = df.append(d1, sort=True, ignore_index=True)
        df = pd.concat([df, d1], sort=True, ignore_index=True)
        for row in d1.itertuples():
            d1 = self.get_all_parent_artifacts(row.name)
            # df = df.append(d1, sort=True, ignore_index=True)
            df = pd.concat([df, d1], sort=True, ignore_index=True)
        df = df.drop_duplicates(subset=None, keep="first", inplace=False)
        return df

    def get_all_parent_executions(self, artifact_name: str) -> pd.DataFrame:
        """Return all executions that produced upstream artifacts for the given artifact."""
        parent_artifacts: pd.DataFrame = self.get_all_parent_artifacts(artifact_name)

        execution_ids = set(
            event.execution_id
            for event in self.store.get_events_by_artifact_ids(parent_artifacts.id.values.tolist())
            if event.type == mlpb.Event.OUTPUT
        )

        return self._as_pandas_df(
            self.store.get_executions_by_id(execution_ids),
            lambda _exec: self._transform_to_dataframe(_exec, {"id": _exec.id, "name": _exec.name}),
        )

    def find_producer_execution(self, artifact_name: str) -> t.Optional[mlpb.Execution]:
        """Return execution that produced the given artifact.

        TODO: how come one artifact can have multiple producer executions?
        """
        artifact: t.Optional[mlpb.Artifact] = self._get_artifact(artifact_name)
        if not artifact:
            logger.debug("Artifact does not exist (name=%s).", artifact_name)
            return None

        executions_ids = set(
            event.execution_id
            for event in self.store.get_events_by_artifact_ids([artifact.id])
            if event.type == mlpb.Event.OUTPUT
        )
        if not executions_ids:
            logger.debug("No producer execution exists for artifact (name=%s, id=%s).", artifact.name, artifact.id)
            return None

        executions: t.List[mlpb.Execution] = self.store.get_executions_by_id(executions_ids)
        if not executions:
            logger.debug("No executions exist for given IDs (ids=%s)", str(executions_ids))
            return None

        if len(executions) >= 2:
            logger.debug(
                "Multiple executions (ids=%s) claim artifact (name=%s) as output.",
                [e.id for e in executions],
                artifact.name,
            )

        return executions[0]

    get_producer_execution = find_producer_execution

    def get_metrics(self, metrics_name: str) -> t.Optional[pd.DataFrame]:
        """Return metric data frame.

        TODO: need better description.
        """
        for metric in self.store.get_artifacts_by_type("Step_Metrics"):
            if metric.name == metrics_name:
                name: t.Optional[str] = metric.custom_properties.get("Name", None)
                if name:
                    return pd.read_parquet(name)
                break
        return None

    @staticmethod
    def read_dataslice(name: str) -> pd.DataFrame:
        """Reads the data slice.

        TODO: Why is it here?
        """
        # To do checkout if not there
        df = pd.read_parquet(name)
        return df

    def dumptojson(self, pipeline_name: str, exec_id: t.Optional[int] = None) -> t.Optional[str]:
        """Return JSON-parsable string containing details about the given pipeline.

        TODO: Think if this method should return dict.
        """
        if exec_id is not None:
            exec_id = int(exec_id)

        def _get_node_attributes(_node: t.Union[mlpb.Context, mlpb.Execution, mlpb.Event], _attrs: t.Dict) -> t.Dict:
            for attr in CONTEXT_LIST:
                if getattr(_node, attr, None) is not None:
                    _attrs[attr] = getattr(_node, attr)

            if "properties" in _attrs:
                _attrs["properties"] = CmfQuery._copy(_attrs["properties"])
            if "custom_properties" in _attrs:
                _attrs["custom_properties"] = CmfQuery._copy(
                    _attrs["custom_properties"], key_mapper={"type": "user_type"}
                )
            return _attrs

        pipelines: t.List[t.Dict] = []
        for pipeline in self._get_pipelines(pipeline_name):
            pipeline_attrs = _get_node_attributes(pipeline, {"stages": []})
            for stage in self._get_stages(pipeline.id):
                stage_attrs = _get_node_attributes(stage, {"executions": []})
                for execution in self._get_executions(stage.id, execution_id=exec_id):
                    # name will be an empty string for executions that are created with
                    # create new execution as true(default)
                    # In other words name property will there only for execution
                    # that are created with create new execution flag set to false(special case)
                    exec_attrs = _get_node_attributes(
                        execution,
                        {
                            "type": self.store.get_execution_types_by_id([execution.type_id])[0].name,
                            "name": execution.name if execution.name != "" else "",
                            "events": [],
                        },
                    )
                    for event in self.store.get_events_by_execution_ids([execution.id]):
                        event_attrs = _get_node_attributes(event, {"artifacts": []})
                        for artifact in self.store.get_artifacts_by_id([event.artifact_id]):
                            artifact_attrs = _get_node_attributes(
                                artifact, {"type": self.store.get_artifact_types_by_id([artifact.type_id])[0].name}
                            )
                            event_attrs["artifacts"].append(artifact_attrs)
                        exec_attrs["events"].append(event_attrs)
                    stage_attrs["executions"].append(exec_attrs)
                pipeline_attrs["stages"].append(stage_attrs)
            pipelines.append(pipeline_attrs)

        return json.dumps({"Pipeline": pipelines})

    """def materialize(self, artifact_name:str):
       artifacts = self.store.get_artifacts()
       for art in artifacts:
           if art.name == artifact_name:
               selected_artifact = art
               break
       for k, v in selected_artifact.custom_properties.items():
           if (k == "Path"):
               path = v
           elif (k == "git_repo"):
               git_repo = v
           elif (k == "Revision"):
               rev = v
           elif (remote == "Remote"):
               remote = v
       
       Cmf.materialize(path, git_repo, rev, remote)"""
