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
import time
import json
import logging
import typing as t
import pandas as pd
from enum import Enum
from google.protobuf.json_format import MessageToDict
from itertools import chain
from ml_metadata.proto import metadata_store_pb2 as mlpb
from cmflib.mlmd_objects import CONTEXT_LIST
from cmflib.cmf_merger import parse_json_to_mlmd
from cmflib.store.postgres import PostgresStore
from cmflib.store.sqllite_store import SqlliteStore
from cmflib.utils.helper_functions import get_postgres_config

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

    def __init__(self, filepath: str = "mlmd", is_server=False) -> None:
        self.filepath = filepath
        temp_store: t.Union[PostgresStore, SqlliteStore]
        if is_server:
            config_dict = get_postgres_config()
            temp_store = PostgresStore(config_dict)
        else:
            temp_store = SqlliteStore({"filename": filepath})
        self.store = temp_store.connect()

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
        node: t.Union[mlpb.Execution, mlpb.Artifact], d: t.Optional[t.Dict] = None  # type: ignore  # Execution, Artifact type not recognized by mypy, using ignore to bypass
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

    def _get_pipelines(self, name: t.Optional[str] = None) -> t.List[mlpb.Context]: # type: ignore  # Context type not recognized by mypy, using ignore to bypass
        """Return list of pipelines with the given name.

        Args:
            name: Piepline name or None to return all pipelines.
        Returns:
            List of objects associated with pipelines.
        """
        pipelines: t.List[mlpb.Context] = self.store.get_contexts_by_type("Parent_Context") # type: ignore  # Context type not recognized by mypy, using ignore to bypass
        if name is not None:
            pipelines = [pipeline for pipeline in pipelines if pipeline.name == name]
        return pipelines

    def _get_pipeline(self, name: str) -> t.Optional[mlpb.Context]: # type: ignore  # Context type not recognized by mypy, using ignore to bypass
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

    def _get_stages(self, pipeline_id: int) -> t.List[mlpb.Context]:    # type: ignore  # Context type not recognized by mypy, using ignore to bypass
        """Return stages for the given pipeline.

        Args:
            pipeline_id: Pipeline ID.
        Returns:
            List of associated pipeline stages.
        """
        return self.store.get_children_contexts_by_context(pipeline_id)

    def _get_executions(self, stage_id: int, execution_id: t.Optional[int] = None) -> t.List[mlpb.Execution]:   # type: ignore  # Execution type not recognized by mypy, using ignore to bypass
        """Return executions of the given stage.

        Args:
            stage_id: Stage identifier.
            execution_id: If not None, return execution with this ID.
        Returns:
            List of executions matching input parameters.
        """
        executions: t.List[mlpb.Execution] = self.store.get_executions_by_context(stage_id) # type: ignore  # Execution type not recognized by mypy, using ignore to bypass
        if execution_id is not None:
            executions = [execution for execution in executions if execution.id == execution_id]
        return executions

    def _get_executions_by_input_artifact_id(self, artifact_id: int, pipeline_id: t.Optional[int] = None) -> t.List[int]:
        """Return stage executions that consumed given input artifact.

        Args:
            artifact_id: Identifier of the input artifact.
        Returns:
            List of stage executions that consumed the given artifact.
        """
        execution_ids = list(set(
            event.execution_id
            for event in self.store.get_events_by_artifact_ids([artifact_id])
            if event.type == mlpb.Event.INPUT   # type: ignore  # Event type not recognized by mypy, using ignore to bypass
        ))
        
        if pipeline_id != None:
            list_exec=self.store.get_executions_by_id(execution_ids)
            execution_ids=[]
            for exe in list_exec:
                if (self._transform_to_dataframe(exe).Pipeline_id.to_string(index=False)) == str(pipeline_id):
                    execution_ids.append(exe.id)
        return execution_ids

    def _get_executions_by_output_artifact_id(self, artifact_id: int, pipeline_id: t.Optional[int] = None) -> t.List[int]:
        """Return stage execution that produced given output artifact.

        Args:
            artifact_id: Identifier of the output artifact.
        Return:
            List of stage executions, should probably be size of 1 or zero.
        """
        execution_ids: t.List[int] = [
            event.execution_id
            for event in self.store.get_events_by_artifact_ids([artifact_id])
            if event.type == mlpb.Event.OUTPUT  # type: ignore  # Event type not recognized by mypy, using ignore to bypass
        ]
        # According to CMF, it's OK to have multiple executions that produce the same exact artifact.
        # if len(execution_ids) >= 2:
        #     logger.warning("%d executions claim artifact (id=%d) as output.", len(execution_ids), artifact_id)
        if pipeline_id != None:
            list_exec = self.store.get_executions_by_id(execution_ids)
            execution_ids = []
            for exe in list_exec:
                if (self._transform_to_dataframe(exe).Pipeline_id.to_string(index=False)) == str(pipeline_id):
                    execution_ids.append(exe.id)
        return execution_ids

    def _get_artifact(self, name: str) -> t.Optional[mlpb.Artifact]:    # type: ignore  # Artifact type not recognized by mypy, using ignore to bypass
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
            if event.type == mlpb.Event.OUTPUT  # type: ignore  # Event type not recognized by mypy, using ignore to bypass
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
            if event.type == mlpb.Event.INPUT   # type: ignore  # Event type not recognized by mypy, using ignore to bypass
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
        pipeline: t.Optional[mlpb.Context] = self._get_pipeline(pipeline_name)  # type: ignore  # Context type not recognized by mypy, using ignore to bypass
        return -1 if not pipeline else pipeline.id

    def get_pipeline_stages(self, pipeline_name: str) -> t.List[str]:
        """Return list of pipeline stages for the pipeline with the given name.

        Args:
            pipeline_name: Name of the pipeline for which stages need to be returned. In CMF, there are no different
                pipelines with the same name.
        Returns:
            List of stage names associated with the given pipeline.
        """
        stages:t.List[str] = []
        for pipeline in self._get_pipelines(pipeline_name):
            stages.extend(stage.name for stage in self._get_stages(pipeline.id))
        return stages

    def get_all_exe_in_stage(self, stage_name: str) -> t.List[mlpb.Execution]:  # type: ignore  # Execution type not recognized by mypy, using ignore to bypass
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

    def get_artifact_df(self, artifact: mlpb.Artifact, d: t.Optional[t.Dict] = None) -> pd.DataFrame:   # type: ignore  # Artifact type not recognized by mypy, using ignore to bypass
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
        artifact: t.Optional[mlpb.Artifact] = self._get_artifact(name)  # type: ignore  # Artifact type not recognized by mypy, using ignore to bypass
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
            event_type = "INPUT" if event.type == mlpb.Event.Type.INPUT else "OUTPUT"   # type: ignore  # Event type not recognized by mypy, using ignore to bypass
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

        artifact: t.Optional[mlpb.Artifact] = self._get_artifact(artifact_name) # type: ignore  # Artifact type not recognized by mypy, using ignore to bypass
        if not artifact:
            return df

        for event in self.store.get_events_by_artifact_ids([artifact.id]):
            stage_ctx = self.store.get_contexts_by_execution(event.execution_id)[0]
            linked_execution = {
                "Type": "INPUT" if event.type == mlpb.Event.Type.INPUT else "OUTPUT",   # type: ignore  # Event type not recognized by mypy, using ignore to bypass
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

    def get_one_hop_child_artifacts(self, artifact_name: str, pipeline_id: t.Optional[int] = None) -> pd.DataFrame:
        """Get artifacts produced by executions that consume given artifact.

        Args:
            artifact name: Name of an artifact.
        Return:
            Output artifacts of all executions that consumed given artifact.
        """
        artifact: t.Optional[mlpb.Artifact] = self._get_artifact(artifact_name)    # type: ignore  # Artifact type not recognized by mypy, using ignore to bypass
        if not artifact:
            return pd.DataFrame()

        # Get output artifacts of executions consumed the above artifact.
        artifacts_ids = self._get_output_artifacts(self._get_executions_by_input_artifact_id(artifact.id, pipeline_id))
        return self._as_pandas_df(
            self.store.get_artifacts_by_id(artifacts_ids), lambda _artifact: self.get_artifact_df(_artifact)
        )

    def get_one_hop_parent_executions(self, execution_id: t.List[int], pipeline_id: t.Optional[int] = None) -> t.List[int]:
        """Get artifacts produced by executions that consume given artifact.

        Args:
            artifact name: Name of an artifact.
        Return:
            Output artifacts of all executions that consumed given artifact.
        """
        artifacts_input = self._get_input_artifacts(execution_id)
        list_exec = []
        exec_ids_added = []
        for i in artifacts_input:
            exec = self._get_executions_by_output_artifact_id(i, pipeline_id)
            if exec not in exec_ids_added:
                exec_ids_added.append(exec)
                list_exec.append(self.store.get_executions_by_id(exec))
        # Flatten list_exec and return as a list of integers
        return list(chain.from_iterable(list_exec))

    def get_one_hop_parent_executions_ids(self, execution_ids: t.List[int], pipeline_id: t.Optional[int] = None) -> t.List[int]:
        """Get parent execution ids for given execution id

        Args: 
           execution_id : Execution id for which parent execution are required
                          It is passed in list, for example execution_id: [1]  
           pipeline_id : Pipeline id
        Return:
           Returns parent executions for given id
        """
        artifact_ids: t.List[int] = self._get_input_artifacts(execution_ids)
        if not artifact_ids:
            return []

        exe_ids = []

        for id in artifact_ids:
            ids = self._get_executions_by_output_artifact_id(id, pipeline_id)
            exe_ids.extend(ids)
        return exe_ids

    def get_executions_with_execution_ids(self, exe_ids: t.List[int]) -> pd.DataFrame:
        """For list of execution ids it returns df with "id, Execution_type_name, Execution_uuid"

        Args:
            execution ids: List of execution ids.
        Return:
            df["id", "Execution_type_name", "Execution_uuid"]
        """
        df = pd.DataFrame()
        executions = self.store.get_executions_by_id(exe_ids)
        execution_id = {}
        for exe in executions:
            temp_dict = {}
            # To get execution_id, exe list[mlmd.proto.execution] is converted to dict using MessageToDict
            execution_id = MessageToDict(exe, preserving_proto_field_name=True) # By default including_default_value_fields=False
            temp_dict['id'] = int(execution_id['id'])
            d1 = self._transform_to_dataframe(exe, temp_dict)       # df {id:,executions}
            df = pd.concat([df, d1], sort=True, ignore_index=True)
        df.drop_duplicates()
        df = df[["id", "Execution_type_name","Execution_uuid"]]
        return df

    def get_all_child_artifacts(self, artifact_name: str) -> pd.DataFrame:
        """Return all downstream artifacts starting from the given artifact.

        Args:
            artifact_name: Artifact name.
        Returns:
            Data frame containing all child artifacts.
        """
        df = pd.DataFrame()
        d1 = self.get_one_hop_child_artifacts(artifact_name)
        df = pd.concat([df, d1], sort=True, ignore_index=True)
        for row in d1.itertuples():
            d1 = self.get_all_child_artifacts(str(row.name))    # Convert row.name to string to ensure compatibility with get_all_child_artifacts method
            # df = df.append(d1, sort=True, ignore_index=True)
            df = pd.concat([df, d1], sort=True, ignore_index=True)
        df = df.drop_duplicates(subset=None, keep="first", inplace=False)
        return df

    def get_one_hop_parent_artifacts(self, artifact_name: str) -> pd.DataFrame:
        """Return input artifacts for the execution that produced the given artifact.

        Args:
            artifact_name: Artifact name.
        Returns:
            Data frame containing immediate parent artifact of given artifact.
        """
        artifact: t.Optional[mlpb.Artifact] = self._get_artifact(artifact_name) # type: ignore  # Artifact type not recognized by mypy, using ignore to bypass
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
        df = pd.concat([df, d1], sort=True, ignore_index=True)
        for row in d1.itertuples():
            d1 = self.get_all_parent_artifacts(str(row.name))   # Convert row.name to string to ensure compatibility with get_all_parent_artifacts method
            # df = df.append(d1, sort=True, ignore_index=True)
            df = pd.concat([df, d1], sort=True, ignore_index=True)
        df = df.drop_duplicates(subset=None, keep="first", inplace=False)
        return df

    def get_all_parent_executions_by_id(self, execution_id: t.List[int], pipeline_id: t.Optional[int] = None) -> t.List[t.List[t.Any]]:
        """
        Retrieve all parent executions for a given execution ID.

        This method recursively finds all parent executions for the provided execution ID(s) within an optional pipeline context.
        It returns a list containing two lists: one with parent execution details and another with source-target links.

        Args:
            execution_id: A list of execution IDs for which to find parent executions.
            pipeline_id: An optional pipeline ID to filter the parent executions. Defaults to None.

        Returns:
            List[int]: A list containing two lists:
            - The first list contains details of parent executions, where each entry is a list with the execution ID, execution type name, and execution UUID.
            - The second list contains dictionaries representing source-target links between executions.
        """
        parent_executions: t.List[t.List[t.Any]] = [[],[]]
        current_execution_id: t.List[int] = execution_id
        list_of_parent_execution_id: t.List[t.List[t.Any]] = []
        link_src_trgt_list: t.List[t.Dict[str, int]] = []
        while current_execution_id:
            parent_execution_ids = self.get_one_hop_parent_executions(current_execution_id, pipeline_id)
            if isinstance(parent_execution_ids, list):  # Ensure 'parent_execution_ids' is a iterable
                for data in parent_execution_ids:
                    if isinstance(data, list):  # Ensure 'data' is iterable
                        for j in data:
                            temp=[j.id, j.properties["Execution_type_name"].string_value, j.properties["Execution_uuid"].string_value]
                            if temp not in parent_executions[0]:
                                link_src_trgt_list.append({"source":j.id, "target":current_execution_id[0]})
                                list_of_parent_execution_id.append(temp)
            if list_of_parent_execution_id:
                parent_executions[0].extend(list_of_parent_execution_id)
                parent_executions[1].extend(link_src_trgt_list)
                for id_name_uuid in list_of_parent_execution_id:
                    current_execution_id = [id_name_uuid[0]]
                    recursive_parents = self.get_all_parent_executions_by_id(current_execution_id, pipeline_id)
                    parent_executions[0].extend(recursive_parents[0])
                    parent_executions[1].extend(recursive_parents[1])
            else:
                break
        return parent_executions

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
            for event in self.store.get_events_by_artifact_ids([int(id) for id in parent_artifacts.id.values.tolist()])
            if event.type == mlpb.Event.OUTPUT  # type: ignore  # Event type not recognized by mypy, using ignore to bypass
        )

        return self._as_pandas_df(
            self.store.get_executions_by_id(execution_ids),
            lambda _exec: self._transform_to_dataframe(_exec, {"id": _exec.id, "name": _exec.name}),
        )

    def find_producer_execution(self, artifact_name: str) -> t.Optional[mlpb.Execution]:    # type: ignore  # Execution type not recognized by mypy, using ignore to bypass
        """Return execution that produced the given artifact.

        One artifact can have multiple producer executions (names of artifacts are fully-qualified with hashes). So,
        if two executions produced the same exact artifact, this one artifact will have multiple parent executions.
        """
        artifact: t.Optional[mlpb.Artifact] = self._get_artifact(artifact_name) # type: ignore  # Artifact type not recognized by mypy, using ignore to bypass
        if not artifact:
            logger.debug("Artifact does not exist (name=%s).", artifact_name)
            return None

        executions_ids = set(
            event.execution_id
            for event in self.store.get_events_by_artifact_ids([artifact.id])

            if event.type == mlpb.Event.OUTPUT  # type: ignore  # Event type not recognized by mypy, using ignore to bypass
        )
        if not executions_ids:
            logger.debug("No producer execution exists for artifact (name=%s, id=%s).", artifact.name, artifact.id)
            return None

        executions: t.List[mlpb.Execution] = self.store.get_executions_by_id(executions_ids)    # type: ignore  # Execution type not recognized by mypy, using ignore to bypass
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


    # writing new functions to remove multiple calls to cmfquery functions or ml-metadata functions
    def get_all_executions_in_pipeline(self, pipeline_name: str) -> pd.DataFrame:
        """Return all executions of the given pipeline as pandas data frame.
        Args:
            pipeline_name:- pipeline name
        Returns:
            Data frame with all executions associated with the given pipeline.
        """
        df = pd.DataFrame()
        pipeline_id = self.get_pipeline_id(pipeline_name)
        for stage in self._get_stages(pipeline_id):
            for execution in self._get_executions(stage.id):
               ex_as_df: pd.DataFrame = self._transform_to_dataframe(
                   execution, {"id": execution.id, "name": execution.name}
               )
               df = pd.concat([df, ex_as_df], sort=True, ignore_index=True)
        return df

    def get_all_artifacts_for_executions(self, execution_ids: t.List[int]) -> pd.DataFrame:
        """Return all artifacts for the list of given executions.

        Args:
            execution_ids: List of Execution identifiers.
        Return:
            Data frame containing artifacts for the list of given executions.
        """
        df = pd.DataFrame()
        # set of artifact ids for list of given execution ids
        artifact_ids = set(
            event.artifact_id
            for event in self.store.get_events_by_execution_ids(set(execution_ids))
            )
        artifacts = self.store.get_artifacts_by_id(list(artifact_ids))
        for artifact in artifacts:
             df = pd.concat(
                    [df, self.get_artifact_df(artifact)], sort=True, ignore_index=True
             )
        return df
    
    def get_one_hop_parent_artifacts_with_id(self, artifact_id: int) -> pd.DataFrame:
        """Return input artifacts for the execution that produced the given artifact.
        Args:
            artifact_id: Artifact id.
        Returns:
            Data frame containing immediate parent artifacts of given artifact/artifacts.
        """
        df = pd.DataFrame()
        input_artifact_ids: t.List[int] = self._get_input_artifacts(self._get_executions_by_output_artifact_id(artifact_id))
        df = self._as_pandas_df(self.store.get_artifacts_by_id(input_artifact_ids), 
                lambda _artifact: self.get_artifact_df(_artifact)
                )
        return df

    def _get_node_attributes(self, _node: t.Union[mlpb.Context, mlpb.Execution, mlpb.Event], _attrs: t.Dict) -> t.Dict: # type: ignore  # Execution, Context, Event type not recognized by mypy, using ignore to bypass
        """
        Extract attributes from a node and return them as a dictionary.

        Args:
            _node (Union[mlpb.Context, mlpb.Execution, mlpb.Event]): The MLMD node (Context, Execution, or Event) to extract attributes from.
            _attrs (Dict): A dictionary to populate with extracted attributes.

        Returns:
            Dict: A dictionary containing the extracted attributes from the node.
        """
        for attr in CONTEXT_LIST:
            if getattr(_node, attr, None) is not None and not getattr(_node, attr, None) == "":
                _attrs[attr] = getattr(_node, attr)

        if "properties" in _attrs:
            _attrs["properties"] = CmfQuery._copy(_attrs["properties"])
        if "custom_properties" in _attrs:
            _attrs["custom_properties"] = CmfQuery._copy(
                _attrs["custom_properties"], key_mapper={"type": "user_type"}
            )
        return _attrs

    def _get_event_attributes(self, execution_id: int) -> t.List[t.Dict]:
        """
        Extract event attributes for a given execution ID.

        Args:
            execution_id (int): The ID of the execution for which event attributes are to be extracted.

        Returns:
            List[Dict]: A list of dictionaries, each containing attributes of an event associated with the execution.
        """
        events = []
        for event in self.store.get_events_by_execution_ids([execution_id]):
            event_attrs = self._get_node_attributes(event, {})
            artifacts = self.store.get_artifacts_by_id([event.artifact_id])
            artifact_attrs = self._get_node_attributes(
                artifacts[0], {"type": self.store.get_artifact_types_by_id([artifacts[0].type_id])[0].name}
            )
            event_attrs["artifact"] = artifact_attrs
            events.append(event_attrs)
        return events

    def _get_execution_attributes(self, stage_id: int, exec_uuid: t.Optional[str] = None, last_sync_time: t.Optional[int] = None) -> t.List[t.Dict]:
        """
        Extract execution attributes for a given stage ID.

        Args:
            stage_id (int): The ID of the stage for which execution attributes are to be extracted.
            exec_uuid (Optional[str]): An optional execution UUID to filter executions. If None, all executions are included.

        Returns:
            List[Dict]: A list of dictionaries, each containing attributes of an execution associated with the stage.
        """
        executions = []
        for execution in self.get_all_executions_by_stage(stage_id, execution_uuid=exec_uuid):
            exec_attrs = self._get_node_attributes(
                execution,
                {
                    "type": self.store.get_execution_types_by_id([execution.type_id])[0].name,
                    "name": execution.name if execution.name != "" else "",
                    "events": self._get_event_attributes(execution.id),
                },
            )

            # what is usual situtaion - 
            #it does not matter if last sync time is given or not we have to add exec_attrs 
            #however if last sync timr is given then we have to check if last_update_time_since_epoch > last_sync_time
            # last_update_time_since epoch

            if last_sync_time:
                if exec_attrs["last_update_time_since_epoch"] > last_sync_time:
                    executions.append(exec_attrs)
            else:
                executions.append(exec_attrs)

        return executions

    def _get_stage_attributes(self, pipeline_id: int, exec_uuid: t.Optional[str] = None, last_sync_time: t.Optional[int] = None) -> t.List[t.Dict]:
        """
        Extract stage attributes for a given pipeline ID.

        Args:
            pipeline_id (int): The ID of the pipeline for which stage attributes are to be extracted.
            exec_uuid (Optional[str]): An optional execution UUID to filter stages. If None, all stages are included.

        Returns:
            List[Dict]: A list of dictionaries, each containing attributes of a stage associated with the pipeline.
        """
        stages = []
        for stage in self._get_stages(pipeline_id):
            stage_attrs = self._get_node_attributes(stage, {"executions": self._get_execution_attributes(stage.id, exec_uuid, last_sync_time)})
            if last_sync_time:
                if len(stage_attrs['executions']) != 0:
                    stages.append(stage_attrs)
                else:
                    if stage_attrs["last_update_time_since_epoch"] > last_sync_time:
                        stages.append(stage_attrs)
            else:
                stages.append(stage_attrs)

        return stages

    def dumptojson(self, pipeline_name: str, exec_uuid: t.Optional[str] = None) -> t.Optional[str]:
        """Return JSON-parsable string containing details about the given pipeline.
        Args:
            pipeline_name: Name of an AI pipelines.
            exec_uuid: Optional stage execution_uuid - filter stages by this execution_uuid.
        Returns:
            Pipeline in JSON format.
        """
        pipelines: t.List[t.Dict] = []
        for pipeline in self._get_pipelines(pipeline_name):
            pipeline_attrs = self._get_node_attributes(pipeline, {"stages": self._get_stage_attributes(pipeline.id, exec_uuid)})
            pipelines.append(pipeline_attrs)

        return json.dumps({"Pipeline": pipelines})

    def extract_to_json(self, last_sync_time: int):
        pipelines = []
        if last_sync_time:
            for pipeline in self._get_pipelines():
                pipeline_attrs = self._get_node_attributes(pipeline, {"stages": self._get_stage_attributes(pipeline.id, None, last_sync_time)})
                if len(pipeline_attrs['stages']) !=0:
                    pipelines.append(pipeline_attrs)
                else:
                    if pipeline_attrs["last_update_time_since_epoch"] > last_sync_time:
                        pipelines.append(pipeline_attrs)
        else:
            for pipeline in self._get_pipelines():
                pipeline_attrs = self._get_node_attributes(pipeline, {"stages": self._get_stage_attributes(pipeline.id)})
                pipelines.append(pipeline_attrs)

        return json.dumps({"Pipeline": pipelines})
    
    def get_all_executions_for_artifact_id(self, artifact_id: int) -> pd.DataFrame:
        """Return executions that consumed and produced given artifact.

        Args:
            artifact_name: Artifact id.
        Returns:
            Pandas data frame containing stage executions, one execution per row.
        """
        df = pd.DataFrame()

        try:
            for event in self.store.get_events_by_artifact_ids([artifact_id]):
                stage_ctx = self.store.get_contexts_by_execution(event.execution_id)[0]
                linked_execution = {
                    "Type": "INPUT" if event.type == mlpb.Event.Type.INPUT else "OUTPUT",   # type: ignore  # Event type not recognized by mypy, using ignore to bypass
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
        except:
            return df
        return df
    
    def get_all_executions_by_stage(self, stage_id: int, execution_uuid: t.Optional[str] = None) -> t.List[mlpb.Execution]: # type: ignore  # Execution type not recognized by mypy, using ignore to bypass
        """
        Return executions of the given stage.

        This function retrieves all executions associated with a specific stage.
        If an execution UUID is provided, it filters the executions to include only those
        that match the given UUID.
        Args:
            stage_id (int): Stage identifier.
            execution_uuid (Optional[str]): If not None, return execution with this UUID.
        Returns:
            List[mlpb.Execution]: List of executions matching input parameters.
        """
        executions: t.List[mlpb.Execution] = self.store.get_executions_by_context(stage_id) # type: ignore  # Execution type not recognized by mypy, using ignore to bypass
        if execution_uuid is None:
            return executions
        executions_with_uuid: t.List[mlpb.Execution] = []   # type: ignore  # Execution type not recognized by mypy, using ignore to bypass
        for execution in executions:
            exec_uuid_list = execution.properties['Execution_uuid'].string_value.split(",")
            if execution_uuid in exec_uuid_list:
                executions_with_uuid.append(execution)
        return executions_with_uuid

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
