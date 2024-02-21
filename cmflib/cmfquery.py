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
import abc
import json
import logging
import typing as t
from enum import Enum

import pandas as pd
from ml_metadata.metadata_store import metadata_store
from ml_metadata.proto import metadata_store_pb2 as mlpb

from cmflib.mlmd_objects import CONTEXT_LIST

__all__ = ["CmfQuery"]

logger = logging.getLogger(__name__)


class _KeyMapper(abc.ABC):
    """Map one key (string) to another key (string) using a predefined strategy.
    Args:
        on_collision: What to do if the mapped key already exists in the target dictionary.
    """

    class OnCollision(Enum):
        """What to do when a mapped key exists in the target dictionary."""

        DO_NOTHING = 0
        """Ignore the collision and overwrite the value associated with this key."""
        RESOLVE = 1
        """Resolve it by appending `_INDEX` where INDEX as the smallest positive integer that avoids this collision."""
        RAISE_ERROR = 2
        """Raise an exception."""

    def __init__(self, on_collision: OnCollision = OnCollision.DO_NOTHING) -> None:
        self.on_collision = on_collision

    def get(self, d: t.Mapping, key: t.Any) -> t.Any:
        """Return new (mapped) key.
        Args:
            d: Dictionary to update with the mapped key.
            key: Source key name.
         Returns:
            A mapped (target) key to be used with the `d` dictionary.
        """
        new_key = self._get(key)
        if new_key in d:
            if self.on_collision == _KeyMapper.OnCollision.RAISE_ERROR:
                raise ValueError(f"Mapped key ({key} -> {new_key}) already exists.")
            elif self.on_collision == _KeyMapper.OnCollision.RESOLVE:
                _base_key, index = new_key, 0
                while new_key in d:
                    index += 1
                    new_key = f"{_base_key}_{index}"
        return new_key

    @abc.abstractmethod
    def _get(self, key: t.Any) -> t.Any:
        """Mapp a source key to a target key.
        Args:
            key: Source key.
        Returns:
            Target key.
        """
        raise NotImplementedError()


class _DictMapper(_KeyMapper):
    """Use dictionaries to specify key mappings (source -> target)."""

    def __init__(self, mappings: t.Mapping, **kwargs) -> None:
        super().__init__(**kwargs)
        self.mappings = mappings

    def _get(self, key: t.Any) -> t.Any:
        return self.mappings.get(key, key)


class _PrefixMapper(_KeyMapper):
    """Prepend a constant prefix to produce a mapped key."""

    def __init__(self, prefix: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.prefix = prefix

    def _get(self, key: t.Any) -> t.Any:
        return self.prefix + key


class CmfQuery(object):
    """CMF Query communicates with the MLMD database and implements basic search and retrieval functionality.

    This class has been designed to work with the CMF framework. CMF alters names of pipelines, stages and artifacts
    in various ways. This means that actual names in the MLMD database will be different from those originally provided
    by users via CMF API. When methods in this class accept `name` parameters, it is expected that values of these
    parameters are fully-qualified names of respective entities.


    Args:
        filepath: Path to the MLMD database file.
    """

    def __init__(self, filepath: str = "mlmd") -> None:
        config = mlpb.ConnectionConfig()
        config.sqlite.filename_uri = filepath
        self.store = metadata_store.MetadataStore(config)

    @staticmethod
    def _copy(
        source: t.Mapping, target: t.Optional[t.Dict] = None, key_mapper: t.Optional[t.Union[t.Dict, _KeyMapper]] = None
    ) -> t.Dict:
        """Create copy of `source` and return it, reuse `target` if not None.

        Args:
            source: Input dict-like object to create copy.
            target: If not None, this will be reused and returned. If None, new dict will be created.
            key_mapper: Dictionary containing how to map keys in `source`, e.g., {"key_in": "key_out"} means the
                        key in `source` named "key_in" should be renamed to "key_out" in output dictionary object, or
                        instance of _KeyMapper.
        Returns:
            If `target` is not None, it is returned containing data from `source`. Else, new object is returned.
        """
        if target is None:
            target = {}
        if key_mapper is None:
            key_mapper = _DictMapper({})
        elif isinstance(key_mapper, dict):
            key_mapper = _DictMapper(key_mapper)
        assert isinstance(key_mapper, _KeyMapper), f"Invalid key_mapper type (type={type(key_mapper)})."

        for key, value in source.items():
            if value.HasField("string_value"):
                value = value.string_value
            elif value.HasField("int_value"):
                value = value.int_value
            else:
                value = value.double_value

            target[key_mapper.get(target, key)] = value

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
        """
        if d is None:
            d = {}

        d = CmfQuery._copy(
            source=node.properties,
            target=d#, # renaming properties with prefix properties has impact in server GUI 
            #key_mapper=_PrefixMapper("properties_", on_collision=_KeyMapper.OnCollision.RESOLVE),
        )
        d = CmfQuery._copy(
            source=node.custom_properties,
            target=d, # renaming custom_properties with prefix custom_properties has impact in server GUI 
            key_mapper=_PrefixMapper("custom_properties_", on_collision=_KeyMapper.OnCollision.RESOLVE),
        )

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
        """
        df = pd.DataFrame()
        for element in elements:
            df = pd.concat([df, transform_fn(element)], sort=True, ignore_index=True)
        return df

    def _get_pipelines(self, name: t.Optional[str] = None) -> t.List[mlpb.Context]:
        pipelines: t.List[mlpb.Context] = self.store.get_contexts_by_type("Parent_Context")
        """Return list of pipelines with the given name.

        Args:
            name: Piepline name or None to return all pipelines.
        Returns:
            List of objects associated with pipelines.
        """
        if name is not None:
            pipelines = [pipeline for pipeline in pipelines if pipeline.name == name]
        return pipelines

    def _get_pipeline(self, name: str) -> t.Optional[mlpb.Context]:
        """Return a pipeline with the given name or None if one does not exist.
        Args:
            name: Pipeline name.
        Returns:
            A pipeline object if found, else None.
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

    def _get_executions_by_input_artifact_id(self, artifact_id: int,pipeline_id: str = None) -> t.List[int]:
        """Return stage executions that consumed given input artifact.

        Args:
            artifact_id: Identifier of the input artifact.
        Returns:
            List of stage executions that consumed the given artifact.
        """
        execution_ids = list(set(
            event.execution_id
            for event in self.store.get_events_by_artifact_ids([artifact_id])
            if event.type == mlpb.Event.INPUT
        ))
        
        if pipeline_id != None:
            list_exec=self.store.get_executions_by_id(execution_ids)
            execution_ids=[]
            for exe in list_exec:
                if (self._transform_to_dataframe(exe).Pipeline_id.to_string(index=False)) == str(pipeline_id):
                    execution_ids.append(exe.id)
        return execution_ids

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
        # According to CMF, it's OK to have multiple executions that produce the same exact artifact.
        # if len(execution_ids) >= 2:
        #     logger.warning("%d executions claim artifact (id=%d) as output.", len(execution_ids), artifact_id)

        return list(set(execution_ids))

    def _get_artifact(self, name: str) -> t.Optional[mlpb.Artifact]:
        """Return artifact with the given name or None.
        Args:
            name: Fully-qualified name (e.g., artifact hash is added to the name), so name collisions across different
                  artifact types are not issues here.
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

        Artifacts are uniquely identified by their hashes in CMF, and so, when executions produce the same exact file,
        they will claim this artifact as an output artifact, and so same artifact can have multiple producer
        executions.

        Args:
            execution_ids: List of execution identifiers to return output artifacts for.
        Returns:
            List of output artifact identifiers.
        """
        artifact_ids: t.List[int] = [
            event.artifact_id
            for event in self.store.get_events_by_execution_ids(set(execution_ids))
            if event.type == mlpb.Event.OUTPUT
        ]
        unique_artifact_ids = set(artifact_ids)
        if len(unique_artifact_ids) != len(artifact_ids):
            logger.warning("Multiple executions claim the same output artifacts")
#        artifacts=self.get_all_artifacts_by_ids_list(list(unique_artifact_ids))
#        for key,val in artifacts.iterrows():
#                print(val["name"])
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
            pipeline_name: Name of the pipeline for which stages need to be returned. In CMF, there are no different
                pipelines with the same name.
        Returns:
            List of stage names associated with the given pipeline.
        """
        stages = []
        for pipeline in self._get_pipelines(pipeline_name):
            stages.extend(stage.name for stage in self._get_stages(pipeline.id))
        return stages

    def get_all_exe_in_stage(self, stage_name: str) -> t.List[mlpb.Execution]:
        """Return list of all executions for the stage with the given name.

        Args:
            stage_name: Name of the stage. Before stages are recorded in MLMD, they are modified (e.g., pipeline name
                        will become part of the stage name). So stage names from different pipelines will not collide.
        Returns:
            List of executions for the given stage.
        """
        for pipeline in self._get_pipelines():
            for stage in self._get_stages(pipeline.id):
                if stage.name == stage_name:
                    return self.store.get_executions_by_context(stage.id)
        return []

    def get_all_executions_by_ids_list(self, exe_ids: t.List[int]) -> pd.DataFrame:
        """Return executions for given execution ids list as a pandas data frame.

        Args:
            exe_ids: List of execution identifiers.

        Returns:
            Data frame with all executions for the list of given execution identifiers.
        """

        df = pd.DataFrame()
        executions = self.store.get_executions_by_id(exe_ids)
        for exe in executions:
            d1 = self._transform_to_dataframe(exe)
            df = pd.concat([df, d1], sort=True, ignore_index=True)
        return df

    def get_all_artifacts_by_context(self, pipeline_name: str) -> pd.DataFrame:
        """Return artifacts for given pipeline name as a pandas data frame.

        Args:
            pipeline_name: Name of the pipeline.

        Returns:
            Data frame with all artifacts associated with given pipeline name.
        """
        df = pd.DataFrame()
        contexts = self.store.get_contexts_by_type("Parent_Context")
        context_id = self.get_pipeline_id(pipeline_name)
        for ctx in contexts:
            if ctx.id == context_id:
                child_contexts = self.store.get_children_contexts_by_context(ctx.id)
                for cc in child_contexts:
                    artifacts = self.store.get_artifacts_by_context(cc.id)
                    for art in artifacts:
                        d1 = self.get_artifact_df(art)
                        df = pd.concat([df, d1], sort=True, ignore_index=True)
        return df

    def get_all_artifacts_by_ids_list(self, artifact_ids: t.List[int]) -> pd.DataFrame:
        """Return all artifacts for the given artifact ids list.

        Args:
            artifact_ids: List of artifact identifiers

        Returns:
            Data frame with all artifacts for the given artifact ids list.
        """
        df = pd.DataFrame()
        artifacts = self.store.get_artifacts_by_id(artifact_ids)
        for art in artifacts:
            d1 = self.get_artifact_df(art)
            df = pd.concat([df, d1], sort=True, ignore_index=True)
        return df

    def get_all_executions_in_stage(self, stage_name: str) -> pd.DataFrame:
        """Return executions of the given stage as pandas data frame.
        Args:
            stage_name: Stage name. See doc strings for the prev method.
        Returns:
            Data frame with all executions associated with the given stage.
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
        """
        return [artifact.name for artifact in self.store.get_artifacts()]

    get_artifact_names = get_all_artifacts

    def get_artifact(self, name: str) -> t.Optional[pd.DataFrame]:
        """Return artifact's data frame representation using artifact name.

        Args:
            name: Artifact name.
        Returns:
            Pandas data frame with one row containing attributes of this artifact.
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
        """
        df = pd.DataFrame()
        for event in self.store.get_events_by_execution_ids([execution_id]):
            event_type = "INPUT" if event.type == mlpb.Event.Type.INPUT else "OUTPUT"
            for artifact in self.store.get_artifacts_by_id([event.artifact_id]):
                df = pd.concat(
                    [df, self.get_artifact_df(artifact, {"event": event_type})], sort=True, ignore_index=True
                )
        return df

    def get_all_artifact_types(self) -> t.List[str]:
        """Return names of all artifact types.

        Returns:
            List of all artifact types.
        """
        artifact_list = self.store.get_artifact_types()
        types=[i.name for i in artifact_list]
        return types

    def get_all_executions_for_artifact(self, artifact_name: str) -> pd.DataFrame:
        """Return executions that consumed and produced given artifact.

        Args:
            artifact_name: Artifact name.
        Returns:
            Pandas data frame containing stage executions, one execution per row.
        """
        df = pd.DataFrame()

        artifact: t.Optional = self._get_artifact(artifact_name)
        if not artifact:
            return df

        for event in self.store.get_events_by_artifact_ids([artifact.id]):
            stage_ctx = self.store.get_contexts_by_execution(event.execution_id)[0]
            linked_execution = {
                "Type": "INPUT" if event.type == mlpb.Event.Type.INPUT else "OUTPUT",
                "execution_id": event.execution_id,
                "execution_name": self.store.get_executions_by_id([event.execution_id])[0].name,
                "execution_type_name":self.store.get_executions_by_id([event.execution_id])[0].properties['Execution_type_name'],
                "stage": stage_ctx.name,
                "pipeline": self.store.get_parent_contexts_by_context(stage_ctx.id)[0].name,
            }
            d1 = pd.DataFrame(
                linked_execution,
                index=[
                    0,
                ],
            )
            df = pd.concat([df, d1], sort=True, ignore_index=True)
        return df

    def get_one_hop_child_artifacts(self, artifact_name: str, pipeline_id: str = None) -> pd.DataFrame:
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
        artifacts_ids = self._get_output_artifacts(self._get_executions_by_input_artifact_id(artifact.id,pipeline_id))
        return self._as_pandas_df(
            self.store.get_artifacts_by_id(artifacts_ids), lambda _artifact: self.get_artifact_df(_artifact)
        )

    def get_one_hop_parent_executions(self, execution_id: t.List[int]) -> t.List[int]:
        """Get artifacts produced by executions that consume given artifact.

        Args:
            artifact name: Name of an artifact.
        Return:
            Output artifacts of all executions that consumed given artifact.
        """
        artifacts_input=self._get_input_artifacts(execution_id)
        arti=self.store.get_artifacts_by_id(artifacts_input)
         
        for i in artifacts_input:
            exec=self._get_executions_by_output_artifact_id(i)
            list_exec=self.store.get_executions_by_id(exec)
#            for id in list_exec:
                #print(self._transform_to_dataframe(id).Execution_type_name,"@@@@@@@@@")

    def get_one_hop_child_executions(self, execution_id: t.List[int]) -> t.List[int]:
        """Get artifacts produced by executions that consume given artifact.

        Args:
            artifact name: Name of an artifact.
        Return:
            Output artifacts of all executions that consumed given artifact.
        """
        artifacts_output=self._get_output_artifacts(execution_id)
        arti=self.store.get_artifacts_by_id(artifacts_output)
        for i in artifacts_output:
            exec=self._get_executions_by_input_artifact_id(i)
            list_exec=self.store.get_executions_by_id(exec)
            for id in list_exec:
                self._transform_to_dataframe(id).Execution_type_name

    def get_all_child_artifacts(self, artifact_name: str) -> pd.DataFrame:
        """Return all downstream artifacts starting from the given artifact.

        Args:
            artifact_name: Artifact name.
        Returns:
            Data frame containing all child artifacts.
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
            artifact_name: Artifact name.
        Returns:
            Data frame containing immediate parent artifactog of given artifact.
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
        Args:
            artifact_name: Artifact name.
        Returns:
            Data frame containing all parent artifacts.
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
        """Return all executions that produced upstream artifacts for the given artifact.
        Args:
            artifact_name: Artifact name.
        Returns:
            Data frame containing all parent executions.
        """
        parent_artifacts: pd.DataFrame = self.get_all_parent_artifacts(artifact_name)
        if parent_artifacts.shape[0] == 0:
            # If it's empty, there's no `id` column and the code below raises an exception.
            return pd.DataFrame()

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

        One artifact can have multiple producer executions (names of artifacts are fully-qualified with hashes). So,
        if two executions produced the same exact artifact, this one artifact will have multiple parent executions.
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
        Args:
            metrics_name: Metrics name.
        Returns:
            Data frame containing all metrics.
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
        """Reads the data slice."""
        # To do checkout if not there
        df = pd.read_parquet(name)
        return df

    def dumptojson(self, pipeline_name: str, exec_id: t.Optional[int] = None) -> t.Optional[str]:
        """Return JSON-parsable string containing details about the given pipeline.
        Args:
            pipeline_name: Name of an AI pipelines.
            exec_id: Optional stage execution ID - filter stages by this execution ID.
        Returns:
            Pipeline in JSON format.
        """
        if exec_id is not None:
            exec_id = int(exec_id)

        def _get_node_attributes(_node: t.Union[mlpb.Context, mlpb.Execution, mlpb.Event], _attrs: t.Dict) -> t.Dict:
            for attr in CONTEXT_LIST:
                #Artifacts getattr call on Type was giving empty string, which was overwriting 
                # the defined types such as Dataset, Metrics, Models
                if getattr(_node, attr, None) is not None and not getattr(_node, attr, None) == "":
                    _attrs[attr] = getattr(_node, attr)

            if "properties" in _attrs:
                _attrs["properties"] = CmfQuery._copy(_attrs["properties"])
            if "custom_properties" in _attrs:
                # TODO: (sergey) why do we need to rename "type" to "user_type" if we just copy into a new dictionary?
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
                        event_attrs = _get_node_attributes(event, {})
                        # An event has only a single Artifact associated with it. 
                        # For every artifact we create an event to link it to the execution.

                        artifacts =  self.store.get_artifacts_by_id([event.artifact_id])
                        artifact_attrs = _get_node_attributes(
                                artifacts[0], {"type": self.store.get_artifact_types_by_id([artifacts[0].type_id])[0].name}
                            )
                        event_attrs["artifact"] = artifact_attrs
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


def test_on_collision() -> None:
    from unittest import TestCase

    tc = TestCase()

    tc.assertEqual(3, len(_KeyMapper.OnCollision))
    tc.assertEqual(0, _KeyMapper.OnCollision.DO_NOTHING.value)
    tc.assertEqual(1, _KeyMapper.OnCollision.RESOLVE.value)
    tc.assertEqual(2, _KeyMapper.OnCollision.RAISE_ERROR.value)


def test_dict_mapper() -> None:
    from unittest import TestCase

    tc = TestCase()

    dm = _DictMapper({"src_key": "tgt_key"}, on_collision=_KeyMapper.OnCollision.RESOLVE)
    tc.assertEqual("tgt_key", dm.get({}, "src_key"))
    tc.assertEqual("other_key", dm.get({}, "other_key"))
    tc.assertEqual("existing_key_1", dm.get({"existing_key": "value"}, "existing_key"))
    tc.assertEqual("existing_key_2", dm.get({"existing_key": "value", "existing_key_1": "value_1"}, "existing_key"))

    dm = _DictMapper({"src_key": "tgt_key"}, on_collision=_KeyMapper.OnCollision.DO_NOTHING)
    tc.assertEqual("existing_key", dm.get({"existing_key": "value"}, "existing_key"))


def test_prefix_mapper() -> None:
    from unittest import TestCase

    tc = TestCase()

    pm = _PrefixMapper("nested_", on_collision=_KeyMapper.OnCollision.RESOLVE)
    tc.assertEqual("nested_src_key", pm.get({}, "src_key"))

    tc.assertEqual("nested_existing_key_1", pm.get({"nested_existing_key": "value"}, "existing_key"))
    tc.assertEqual(
        "nested_existing_key_2",
        pm.get({"nested_existing_key": "value", "nested_existing_key_1": "value_1"}, "existing_key"),
    )

    dm = _PrefixMapper("nested_", on_collision=_KeyMapper.OnCollision.DO_NOTHING)
    tc.assertEqual("nested_existing_key", dm.get({"nested_existing_key": "value"}, "existing_key"))


if __name__ == "__main__":
    test_on_collision()
    test_dict_mapper()
    test_prefix_mapper()
