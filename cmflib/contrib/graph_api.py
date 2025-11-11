###
# Copyright (2023) Hewlett Packard Enterprise Development LP
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

"""
Introduction:
    This module implements a read-only graph-like API to ML metadata database. It provides high level wrappers such as
    `Pipeline`, `Stage`, `Execution` and `Artifact` that provide user-friendly interface to MLMD concepts (`Context`,
    `Execution` and `Artifact`).

Warning:
    The information provided by classes in this module will become outdated if underlying MLMD database is modified
    at the same time.

    The mechanism to model relations implemented in this module is not directly following MLMD database scheme. For
    instance, users can go directly from artifacts to executions using methods implemented in the `Artifact` class
    not using the concept of events from MLMD library.

    For convenience purposes, this class provides two wrappers for `Context` concept in MLMD - `Pipeline` and `Stage`.

    Users should not create node wrappers (`Pipeline`, `Stage`, `Execution` and `Artifact`) by themselves. Instead,
    users should use `MlmdGraph` class to query nodes, and then traverse graph using nodes' APIs.

How to get started:
    Users should always start exploring data in MLMD database with the `MlmdGraph` class implemented in this module.
"""

import typing as t
from typing import Iterator, TypeVar

from cmfquery import CmfQuery
from ml_metadata import MetadataStore
from ml_metadata.proto import metadata_store_pb2

__all__ = [
    "MlmdNode",
    "MlmdType",
    "Node",
    "Properties",
    "Type",
    "Base",
    "Pipeline",
    "Stage",
    "Execution",
    "Artifact",
    "MlmdGraph",
    "unique",
    "one",
]

MlmdNode = t.Union[metadata_store_pb2.Context, metadata_store_pb2.Execution, metadata_store_pb2.Artifact]
"""Type for all nodes in MLMD library."""

MlmdType = t.Union[metadata_store_pb2.ContextType, metadata_store_pb2.ExecutionType, metadata_store_pb2.ArtifactType]
"""Type for all node types in MLMD library."""

Node = t.TypeVar("Node", bound="Base")
"""Type for all nodes implemented in this module."""


# These are not for exports in `typing` module, so defining them here (only needed for `Properties` class).
KT = TypeVar("KT")
T_co = TypeVar("T_co", covariant=True)
VT_co = TypeVar("VT_co", covariant=True)


class Properties(t.Mapping):
    """Read-only wrapper around MessageMapContainer from MLMD that converts values to python types on the fly.

    This is used to represent `properties` and `custom_properties` of all MLMD nodes (pipelines, stages, executions
    and artifacts). Users should not create instances of this class directly.
    """

    def __init__(self) -> None:
        self._properties: t.Optional[t.Mapping] = None
        """This is really google.protobuf.pyext._message.MessageMapContainer that inherits from MutableMapping"""

    def __str__(self) -> str:
        return str({k: v for k, v in self.items()})

    def __iter__(self) -> Iterator[T_co]:
        for k in self._properties.keys():
            yield k

    def __len__(self) -> int:
        return len(self._properties)

    def __getitem__(self, __key: KT) -> VT_co:
        return _python_value(self._properties[__key])


class Type:
    """Semantic type description for all graph nodes (pipelines, stages, executions and artifacts).

    Information source:
        https://github.com/google/ml-metadata/blob/master/ml_metadata/proto/metadata_store.proto
    The following types and associated methods should be used in implementations:
        | Nodes           | MlmdNodes     | Metadata store function   |
        |-----------------|---------------|---------------------------|
        | Pipeline, Stage | ContextType   | get_context_types_by_id   |
        | Execution       | ExecutionType | get_execution_types_by_id |
        | Artifact        | ArtifactType  | get_artifact_types_by_id  |
    All types seem to share many common attributes:
                          id:int64  name:str   version:str   description:str  external_id:str  properties:map
        ContextType          +        +            +               +              +                  +
        ExecutionType        +        +            +               +              +                  +
        ArtifactType         +        +            +               +              +                  +

    Users should not create instances of this class directly - use the `Type.get` method instead. This class maintains
    internal mapping from a type ID to instances of this class. This means there is one instance exists for each MLMD
    type.
    """

    # The values below come from the CMF core library. They are standard type names that CMF uses to differentiate
    # between contexts (pipelines and stages), and natively supported artifacts (datasets, models and metrics) -
    # concepts exposed via CMF public API.

    # No fields are defined for execution and generic artifact types because CMF does not enforce standard
    # names at this level. One aspect to keep in mind that MLMD uses the `type_kind` attribute of a type to
    # differentiate between context, execution and artifact types (that may be stored in one table in a relational
    # backend database).

    # PIPELINE and STAGE are context types.

    PIPELINE = "Parent_Context"
    """Name of a context type (ContextType) for pipelines."""

    STAGE = "Pipeline_Stage"
    """Name of a context type (ContextType) for pipeline stages."""

    # DATASET, MODEL and METRICS are artifact types

    DATASET = "Dataset"
    """Type name (ArtifactType) for `dataset` artifacts."""

    MODEL = "Model"
    """Type name (ArtifactType) for `model` artifacts."""

    METRICS = "Metrics"
    """Type name ArtifactType for execution metrics artifact."""

    def __init__(self) -> None:
        self._type: t.Optional[MlmdType] = None

    @property
    def id(self) -> int:
        return self._type.id

    @property
    def name(self) -> str:
        return self._type.name

    @property
    def version(self) -> str:
        return self._type.version

    @property
    def description(self) -> str:
        return self._type.description

    @property
    def external_id(self) -> str:
        return self._type.external_id

    @property
    def properties(self) -> Properties:
        _properties = Properties()
        _properties._properties = self._type.properties
        return _properties

    _types: t.Dict[int, "Type"] = {}
    """A mapping from type ID to type description."""

    @staticmethod
    def get(store: MetadataStore, node: MlmdNode) -> "Type":
        """Factory method to return the type description.

        Every type (identified by type ID) has only one instance, so getting types should be relatively lightweight
        operation (database is accessed only once for each type ID).

        Args:
            store: Metadata store object from MLMD library.
            node: A node to return type for.
        Returns:
            Instance of this class that wraps one of MLMD classes (ContextType, ExecutionType or ArtifactType).
        """
        if node.type_id not in Type._types:
            if isinstance(node, metadata_store_pb2.Context):
                node_type, get_type_fn = metadata_store_pb2.ContextType, store.get_context_types_by_id
            elif isinstance(node, metadata_store_pb2.Execution):
                node_type, get_type_fn = metadata_store_pb2.ExecutionType, store.get_execution_types_by_id
            elif isinstance(node, metadata_store_pb2.Artifact):
                node_type, get_type_fn = metadata_store_pb2.ArtifactType, store.get_artifact_types_by_id
            else:
                raise NotImplementedError(f"No type description for MLMD node (node={node}).")

            type_ = Type()
            type_._type = one(
                get_type_fn([node.type_id]),
                error=ValueError(f"Broken MLMD database. Expecting exactly one type for type_id = {node.type_id}."),
            )
            Type._types[node.type_id] = type_
        return Type._types[node.type_id]


class Base:
    """Base class for node wrappers providing user-friendly API for pipelines, stages, executions and artifacts in
    MLMD database.

    Instance of child classes are not supposed to be directly created by users. This wrapper does not expose `type`
    and `type_id` fields as defined in MLMD. Instead, users should use the `type` property in this class to access
    type information (calling this method should be a lightweight operation).
    """

    def __init__(self) -> None:
        self._db: t.Optional[CmfQuery] = None
        """Data access layer for MLMD database."""

        self._node: t.Optional[MlmdNode] = None
        """Reference to an entity in MLMD database that this class wraps."""

    def __hash__(self):
        """Compute hash.
        TODO: Is type_id enough to differentiate between pipeline and stage contexts?
        """
        assert self._node is not None, "Internal error: self._node is None in Base.__hash__."
        # I can't use `self._node.__class__.__name__` since Pipelines and Stages have the same MLMD class `Context`.
        return hash((self.__class__.__name__, self._node.type_id, self.id))

    def __eq__(self, other: Node) -> bool:
        assert self._node is not None, "Internal error: self._node is None in Base.__eq__."
        assert other._node is not None, "Internal error: other._node is None in Base.__eq__."
        return isinstance(self, type(other)) and self._node.type_id == other._node.type_id and self.id == other.id

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self.id}, name={self.name}, properties={self.properties}, "
            f"custom_properties={self.custom_properties})"
        )

    @property
    def id(self) -> int:
        return self._node.id

    @property
    def name(self) -> str:
        return self._node.name

    @property
    def properties(self) -> Properties:
        _properties = Properties()
        _properties._properties = self._node.properties
        return _properties

    @property
    def custom_properties(self) -> Properties:
        _properties = Properties()
        _properties._properties = self._node.custom_properties
        return _properties

    @property
    def external_id(self) -> str:
        return self._node.external_id

    # The type_id:int and type:str are not provided, use `type` instead to get full type description.

    @property
    def type(self) -> Type:
        return Type.get(self._db.store, self._node)


class Pipeline(Base):
    """Class that represents AI pipelines by wrapping the `Context` concept in MLMD.

    Users should not create instances of this class - use `MlmdGraph` class instead or other node wrappers.
    """

    def __init__(self) -> None:
        super().__init__()

    def stages(self) -> t.List["Stage"]:
        """Return list of all stages in this pipeline."""
        # noinspection PyProtectedMember
        stage_contexts: t.List[metadata_store_pb2.Context] = self._db._get_stages(pipeline_id=self.id)
        return [_graph_node(Stage, self._db, ctx, {"_pipeline": self}) for ctx in stage_contexts]

    def executions(self) -> t.List["Execution"]:
        """Return list of all executions in this pipeline"""
        executions: t.List[Execution] = []
        for stage in self.stages():
            executions.extend(stage.executions())
        return executions

    def artifacts(self) -> t.List["Artifact"]:
        """Return list of all unique artifacts consumed and produced by executions of this pipeline."""
        artifacts: t.List[Artifact] = []
        for execution in self.executions():
            artifacts.extend(execution.inputs())
            artifacts.extend(execution.outputs())
        return unique(artifacts, "id")


class Stage(Base):
    """Class that represents pipeline stages by wrapping the `Context` concept in MLMD.

    Users should not create instances of this class - use `MlmdGraph` class instead or other node wrappers.
    """

    def __init__(self) -> None:
        super().__init__()

        self._pipeline: t.Optional[Pipeline] = None
        """Parent pipeline (lazily initialized)."""

    @property
    def pipeline(self) -> Pipeline:
        """Return parent pipeline."""
        if self._pipeline is None:
            self._pipeline = _graph_node(
                Pipeline, self._db, one(self._db.store.get_parent_contexts_by_context(context_id=self.id))
            )
        return self._pipeline

    def executions(self) -> t.List["Execution"]:
        """Return list of all executions of this stage."""
        # noinspection PyProtectedMember
        executions: t.List[metadata_store_pb2.Execution] = self._db._get_executions(stage_id=self.id)
        return [_graph_node(Execution, self._db, execution, {"_stage": self}) for execution in executions]

    def artifacts(self) -> t.List["Artifact"]:
        """Return list of unique artifacts consumed and produced by executions of this stage."""
        artifacts: t.List[Artifact] = []
        for execution in self.executions():
            artifacts.extend(execution.inputs())
            artifacts.extend(execution.outputs())
        return unique(artifacts, "id")


class Execution(Base):
    """Class that represents stage executions wrapping the `Execution` concept in MLMD.

    Users should not create instances of this class - use `MlmdGraph` class instead or other node wrappers.
    """

    def __init__(self) -> None:
        super().__init__()

        self._stage: t.Optional[Stage] = None
        """Stage for this execution (lazily initialized)."""

    @property
    def stage(self) -> Stage:
        """Return stage of this execution."""
        if self._stage is None:
            self._stage = _graph_node(
                Stage, self._db, one(self._db.store.get_contexts_by_execution(execution_id=self.id))
            )
        return self._stage

    def inputs(self) -> t.List["Artifact"]:
        """Return list of unique input artifacts for this execution."""
        # noinspection PyProtectedMember
        artifacts: t.List[metadata_store_pb2.Artifact] = unique(
            self._db.store.get_artifacts_by_id(self._db._get_input_artifacts([self.id])), key="id"
        )
        return [_graph_node(Artifact, self._db, artifact) for artifact in artifacts]

    def outputs(self) -> t.List["Artifact"]:
        """Return list of unique output artifacts for this execution."""
        # noinspection PyProtectedMember
        artifacts: t.List[metadata_store_pb2.Artifact] = unique(
            self._db.store.get_artifacts_by_id(self._db._get_output_artifacts([self.id])), key="id"
        )
        return [_graph_node(Artifact, self._db, artifact) for artifact in artifacts]


class Artifact(Base):
    """Class that represents artifacts in MLMD by wrapping the `Artifact` concept in MLMD.

    Users should not create instances of this class - use `MlmdGraph` class instead or other node wrappers.

    TODO (sergey) Need to brainstorm the idea of providing artifact-specific classes derived from this class.
    """

    def __init__(self) -> None:
        super().__init__()

        self._consumed_by: t.Optional[t.List[Execution]] = None
        """List of unique executions that consumed this artifact (lazily initialized)."""

        self._produced_by: t.Optional[t.List[Execution]] = None
        """List of unique executions that produced this artifact (lazily initialized)."""

    @property
    def uri(self) -> str:
        return self._node.uri

    def consumed_by(self) -> t.List[Execution]:
        """Return all executions that have consumed this artifact.

        Users must not modify the returned list.
        """
        if self._consumed_by is None:
            # noinspection PyProtectedMember
            executions: t.List[metadata_store_pb2.Execution] = unique(
                self._db.store.get_executions_by_id(self._db._get_executions_by_input_artifact_id(artifact_id=self.id)),
                key="id",
            )
            self._consumed_by = [_graph_node(Execution, self._db, execution) for execution in executions]
        return self._consumed_by

    def produced_by(self) -> t.List[Execution]:
        """Return all executions that have produced this artifact.

        Users must not modify the returned list. How come one artifact is produced by multiple executions? The CMF
        uses hashes of artifacts to determine the artifacts' uniqueness. If multiple executions have happened to produce
        artifacts with the same content (so, hashes are the same), then there will be one record of this in MLMD
        database.
        """
        if self._produced_by is None:
            # noinspection PyProtectedMember
            executions: t.List[metadata_store_pb2.Execution] = unique(
                self._db.store.get_executions_by_id(
                    self._db._get_executions_by_output_artifact_id(artifact_id=self.id)
                ),
                key="id",
            )
            self._produced_by = [_graph_node(Execution, self._db, execution) for execution in executions]
        return self._produced_by


class MlmdGraph:
    """`Entry point` for traversing the MLMD database using graph-like API.

    [Opinionated]. Graph libraries typically implement a `Graph` class that provides at least two methods to iterate
    over nodes and edges. In addition, other methods are also implemented that compute various graph characteristics.
    At the moment of implementing this initial version, it is a bit confusing to differentiate between various MLMD
    node kinds (contexts, executions and artifacts) and CMF (semantic) types (pipelines, stages, executions, models,
    artifacts, datasets, models and metrics). This is the reason for not implementing the `nodes` method. Instead,
    multiple methods are implemented to return CMF nodes.

    Many methods in this class support the `query` string argument. This is the same as the `filter_query` field in
    the `ListOptions`, which is an input argument of several methods in MLMD that retrieve nodes of various types. The
    not-so-detailed description of what this string can look like can be found here:
        https://github.com/google/ml-metadata/blob/master/ml_metadata/proto/metadata_store.proto
    Many MLMD node types have same attributes, such as `id`, `name`, `properties`, `custom_properties` and others. The
    following functionality has been tested.
        Common node attributes:
            "id = 1113", "id != 1113", "id IN (1113, 1)", "name = 'text-generation'", "name != 'text-generation'",
            "name LIKE '%-generation'"

    Args:
        file_path: Path to an MLMD database.

    """

    def __init__(self, file_path: str) -> None:
        self._db = CmfQuery(filepath=file_path)
        """Data access layer for MLMD."""

    def pipelines(self) -> t.List["Pipeline"]:
        """Return all pipelines."""
        pipelines: t.List[metadata_store_pb2.Context] = self._db.store.get_contexts_by_type(Type.PIPELINE)
        return [_graph_node(Pipeline, self._db, pipeline) for pipeline in pipelines]

    def stages(self) -> t.List["Stage"]:
        """Return all stages."""
        stages: t.List[metadata_store_pb2.Context] = self._db.store.get_contexts_by_type(Type.STAGE)
        return [_graph_node(Stage, self._db, stage) for stage in stages]

    def executions(self) -> t.List["Execution"]:
        """Return all stage executions."""
        executions: t.List[metadata_store_pb2.Execution] = self._db.store.get_executions()
        return [_graph_node(Execution, self._db, execution) for execution in executions]

    def artifacts(self) -> t.List["Artifact"]:
        """Return all artifacts."""
        artifacts: t.List[metadata_store_pb2.Artifact] = self._db.store.get_artifacts()
        return [_graph_node(Artifact, self._db, artifact) for artifact in artifacts]


def unique(items: t.List, key: t.Optional[t.Union[str, t.Callable]] = None) -> t.List:
    """Return unique input items in the input list, possible using `key` to determine uniqueness of items.

    Always maintains order of items when `key` is not none. When key is none, order is maintained starting python 3.6.

    Args:
        items: List of input items.
        key: Attribute name or a function that computes `item` key. The `operator.attrgetter` is used
            when type is string (so nested structured are supported, e.g., "type.id"). If it is None, items are
            considered to be keys.
    Returns:
        New list containing unique items according to specified key.
    """
    if key is None:
        return list(dict.fromkeys(items))
    if isinstance(key, str):
        from operator import attrgetter

        key = attrgetter(key)

    keys, unique_items = set(), []
    for item in items:
        item_key = key(item)
        if item_key not in keys:
            keys.add(item_key)
            unique_items.append(item)
    return unique_items


def one(items: t.List[t.Any], return_none_if_empty: bool = False, error: t.Any = None) -> t.Any:
    """Return the only element in the input list.

    Args:
        items: List of input items.
        return_none_if_empty: If true, return None when `items` is empty, if false - raise `error`.
        error: This is thrown when `items` contains wrong number of items.
    Returns:
        The only item in the list or None if list is empty and return_none_if_empty is true.
    Raises:
        ValueError error if length of `nodes` is not 1 when `error` is None or `error`.
    """
    if not items and return_none_if_empty:
        return None
    if len(items) != 1:
        if error is None:
            error = ValueError(f"List (len={len(items)}) expected to contain one element.")
        raise error
    return items[0]


def _python_value(value: metadata_store_pb2.Value) -> t.Union[str, int, float]:
    """Convert MLMD value to a python value.
    Args:
        value: MLMD value.
    Returns:
        Python value.

    TODO: debug under what circumstances this function receives a non-`metadata_store_pb2.Value` values (this
        happens when testing `Type.properties`).
    """
    if isinstance(value, (str, int, float)):
        return value
    elif isinstance(value, metadata_store_pb2.Value):
        if value.HasField("string_value"):
            return value.string_value
        elif value.HasField("int_value"):
            return value.int_value
        elif value.HasField("double_value"):
            return value.double_value
        raise NotImplementedError(f"Unsupported `metadata_store_pb2.Value` value (value={value}).")
    raise NotImplementedError(f"Unsupported value type (type={type(value)})")


def _graph_node(node_type: t.Type[Node], db: CmfQuery, mlmd_node: MlmdNode, attrs: t.Optional[t.Dict] = None) -> Node:
    """Create class instance (users are not supposed to call this method by themselves).
    Args:
        node_type: Graph node type to create (Pipeline, Stage, Execution or Stage) derived from Base.
        db: Data access layer.
        mlmd_node: Node in MLMD database.
        attrs: Optional attributes to set on newly created class instance (with `setattr` function).
    Returns:
        Instance of one of child classes.
    """
    node = node_type()
    node._db = db
    node._node = mlmd_node
    if attrs:
        for name, value in attrs.items():
            setattr(node, name, value)
    return node
