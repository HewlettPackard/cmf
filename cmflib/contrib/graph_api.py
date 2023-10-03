import typing as t
from typing import KT, Iterator, T_co, VT_co

from cmfquery import CmfQuery
from ml_metadata import ListOptions
from ml_metadata.proto import metadata_store_pb2 as mlpb

MlmdNode = t.Union[mlpb.Context, mlpb.Execution, mlpb.Artifact]
Node = t.TypeVar("Node", bound="Base")


_PIPELINE_CONTEXT_NAME = "Parent_Context"
"""Name of a context type for pipelines."""

_STAGE_CONTEXT_NAME = "Pipeline_Stage"
"""Name of a context type for pipeline stages."""


class Properties(t.Mapping):
    """Read-only wrapper around MessageMapContainer that converts values to python types on the fly.
    This is used to represent `properties` and `custom_properties` of all MLMD nodes (pipelines, stages, executions
    and artifacts).
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
        return get_python_value(self._properties[__key])


class Base:
    """Base class for wrappers that provide user-friendly API for MLMD's pipelines, stages, executions and artifacts.

    Instance of child classes are not supposed to be directly created by users, so class members are "protected".
    """

    def __init__(self) -> None:
        self._db: t.Optional[CmfQuery] = None
        """Data access layer for MLMD."""

        self._node: t.Optional[MlmdNode] = None
        """Reference to an entity in MLMD that this class wraps."""

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

    # @property
    # def type_id(self) -> int:
    #     return self._node.type_id

    # @property
    # def type(self) -> str:
    #     return self._node.type

    # @property
    # def external_id(self) -> id:
    #     return self._node.external_id

    @classmethod
    def _create(cls, db: CmfQuery, node: MlmdNode, attrs: t.Optional[t.Dict] = None) -> Node:
        """Create class instance (users are not supposed to call this method by themselves).
        Args:
            db: Data access layer.
            node: MLMD's node.
            attrs: Optional attributes to set on newly created class instance (with `setattr` function).
        Returns:
            Instance of one of child classes.
        """
        obj = cls()
        obj._db = db
        obj._node = node
        if attrs:
            for name, value in attrs.items():
                setattr(obj, name, value)
        return obj

    @classmethod
    def _unique(cls, nodes: t.List[MlmdNode]) -> t.List[MlmdNode]:
        """Return unique input elements in the input list using the `id` attribute as a unique key.
        Args:
            nodes: List of input elements.
        Returns:
            New list containing unique elements in `nodes`. Duplicates are identified using the `id` attribute.
        """
        ids = set(node.id for node in nodes)
        return [node for node in nodes if node.id in ids]

    @classmethod
    def _one(cls, nodes: t.List[t.Any]) -> t.Any:
        """Ensure input list contains exactly one element and return it.
        Args:
            nodes: List of input elements.
        Returns:
            First element in the list.
        Raises:
            ValueError error if length of `nodes` is not 1.
        """
        if len(nodes) != 1:
            raise ValueError(f"List (len={len(nodes)}) expected to contain one element.")
        return nodes[0]


class Pipeline(Base):
    """Class that represents AI pipelines."""

    def __init__(self) -> None:
        super().__init__()

    def stages(self, query: t.Optional[str] = None) -> t.List["Stage"]:
        """Return list of all stages in this pipeline."""
        _mandatory_query = f"parent_contexts_a.name = '{self.name}'"
        stage_contexts: t.List[mlpb.Context] = self._db._get_stages(pipeline_id=self.id)
        return [Stage._create(self._db, ctx, {"_pipeline": self}) for ctx in stage_contexts]

    def executions(self) -> t.List["Execution"]:
        """Return list of all executions in this pipeline"""
        executions: t.List[Execution] = []
        for stage in self.stages():
            executions.extend(stage.executions())
        return executions

    def artifacts(self) -> t.List["Artifact"]:
        """Return list of all unique artifacts consumed and produced by this pipeline."""
        artifacts: t.List[Artifact] = []
        for execution in self.executions():
            artifacts.extend(execution.inputs)
            artifacts.extend(execution.outputs)
        return self._unique(artifacts)


class Stage(Base):
    """Class that represents pipeline stages."""

    def __init__(self) -> None:
        super().__init__()

        self._pipeline: t.Optional[Pipeline] = None
        """Parent pipeline (lazily initialized)."""

    @property
    def pipeline(self) -> Pipeline:
        """Return parent pipeline."""
        if self._pipeline is None:
            pipeline_context: mlpb.Context = self._one(
                self._db.store.get_parent_contexts_by_context(context_id=self.id)
            )
            self._pipeline = Pipeline._create(self._db, pipeline_context)
        return self._pipeline

    def executions(self) -> t.List["Execution"]:
        """Return list of all executions for this stage."""
        executions: t.List[mlpb.Execution] = self._db._get_executions(stage_id=self.id)
        return [Execution._create(self._db, execution, {"_stage": self}) for execution in executions]

    def artifacts(self) -> t.List["Artifact"]:
        """Return list of unique artifacts consumed and produced by this pipeline."""
        artifacts: t.List[Artifact] = []
        for execution in self.executions():
            artifacts.extend(execution.inputs)
            artifacts.extend(execution.outputs)
        return self._unique(artifacts)


class Execution(Base):
    """Class that represents stage executions."""

    def __init__(self) -> None:
        super().__init__()

        self._stage: t.Optional[Stage] = None
        """Stage for this execution (lazily initialized)."""

    @property
    def stage(self) -> Stage:
        if self._stage is None:
            stage_context: mlpb.Context = self._one(self._db.store.get_contexts_by_execution(execution_id=self.id))
            self._stage = Stage._create(self._db, stage_context)
        return self._stage

    @property
    def inputs(self) -> t.List["Artifact"]:
        """Return list of unique input artifacts for this execution."""
        artifacts: t.List[mlpb.Artifact] = self._unique(
            self._db.store.self.store.get_artifacts_by_id(self._db._get_input_artifacts([self.id]))
        )
        return [Artifact._create(self._db, artifact) for artifact in artifacts]

    @property
    def outputs(self) -> t.List["Artifact"]:
        """Return list of unique output artifacts for this execution."""
        artifacts: t.List[mlpb.Artifact] = self._unique(
            self._db.store.self.store.get_artifacts_by_id(self._db._get_output_artifacts([self.id]))
        )
        return [Artifact._create(self._db, artifact) for artifact in artifacts]


class Artifact(Base):
    """Class that represents artifacts."""

    def __init__(self) -> None:
        super().__init__()

        self._consumed_by: t.Optional[t.List[Execution]] = None
        """List of unique executions that consumed this artifact (lazily initialized)."""

        self._produced_by: t.Optional[t.List[Execution]] = None
        """List of unique executions that produced this artifact (lazily initialized)."""

    @property
    def uri(self) -> str:
        return self._node.uri

    @property
    def consumed_by(self) -> t.List[Execution]:
        """Return all executions that have consumed this artifact."""
        if self._consumed_by is None:
            executions: t.List[mlpb.Execution] = self._unique(
                self._db.store.get_executions_by_id(self._db._get_executions_by_input_artifact_id(artifact_id=self.id))
            )
            self._consumed_by = [Execution._create(self._db, execution) for execution in executions]
        return self._consumed_by

    @property
    def produced_by(self) -> t.List[Execution]:
        """Return all executions that have produced this artifact"""
        if self._produced_by is None:
            executions: t.List[mlpb.Execution] = self._unique(
                self._db.store.get_executions_by_id(self._db._get_executions_by_output_artifact_id(artifact_id=self.id))
            )
            self._produced_by = [Execution._create(self._db, execution) for execution in executions]
        return self._produced_by


class MetadataStore:
    """`Entry point` for traversing the MLMD database using graph-like API.

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

    def _check_context_types(
        self,
        contexts: t.List[mlpb.Context],
        type_name: str,
    ):
        ctx_type: mlpb.ContextType = self._db.store.get_context_type(type_name)
        for context in contexts:
            if context.type_id != ctx_type.id:
                raise ValueError(
                    f"MLMD query returned contexts of the wrong type (actual_type_id={context.type_id}, "
                    f"expected_type_id={ctx_type.id}). "
                    f"Did you forget to specify the type as part of the query (type = '{type_name}')?"
                )

    def _search_contexts(
        self, ctx_type_name: str, ctx_wrapper_cls: t.Type[t.Union["Pipeline", "Stage"]], query: t.Optional[str] = None
    ) -> t.Union[t.List["Pipeline"], t.List["Stage"]]:
        if query is None:
            query = f"type = '{ctx_type_name}'"
        contexts: t.List[mlpb.Context] = self._db.store.get_contexts(self.list_options(query))
        self._check_context_types(contexts, ctx_type_name)
        return [ctx_wrapper_cls._create(self._db, ctx) for ctx in contexts]

    def pipelines(self, query: t.Optional[str] = None) -> t.List["Pipeline"]:
        """Retrieve pipelines.
        Pipelines are represented as contexts in MLMD with type attributed equal to `Parent_Context`.
        Args:
            query: The `filter_query` field for the `ListOptions` instance. See class doc strings for examples.
        Raises:
            ValueError when query is present, and results in contexts that are not pipelines.
        Known limitations:
            When query is not None, it must define type (type = 'Parent_Context'), when ID is present this may not be
            required though.
            No filtering is supported by stage ID (no big deal).
        Query examples:
            Filtering by basic node attributes.
                See class foc strings.
            Filter by stage attributes (child_contexts_a is the stage context). There is a bug that prevents using the
            ID for filtering by stage ID. It's fixed in MLMD version 1.14.0 (CMF uses the earlier version).
                "child_contexts_a.name LIKE 'text-generation/%'"
        """
        return self._search_contexts(_PIPELINE_CONTEXT_NAME, Pipeline, query)

    def stages(self, query: t.Optional[str] = None) -> t.List["Stage"]:
        """Retrieve stages.
        Stages are represented as contexts in MLMD with type attributed equal to `Pipeline_Stage`.
        Args:
            query: The `filter_query` field for the `ListOptions` instance. See class doc strings for examples.
        Raises:
            ValueError when query is present, and results in contexts that are not stages.
        Known limitations:
            When query is not None, it must define type (type = 'Stage_Context'), when ID is present this may not be
            required though.
            No filtering is supported by pipeline ID (pretty significant feature).
        Query examples:
            Filtering by basic node attributes
                See class foc strings.
            Filter by pipeline attributes (parent_contexts_a is the pipeline context). There is a bug that prevents
            using the ID for filtering by pipeline ID. It's fixed in MLMD version 1.14.0 (CMF uses the earlier version).
                "parent_contexts_a.name = 'text-classification'", "parent_contexts_a.name LIKE '%-generation'",
                "parent_contexts_a.type = 'Parent_Context'"
        """
        return self._search_contexts(_STAGE_CONTEXT_NAME, Stage, query)

    def executions(self) -> t.List["Execution"]:
        """Retrieve stage executions.
        See `pipelines` method for more details.
        """
        executions: t.List[mlpb.Execution] = self._db.store.get_executions()
        return [Execution._create(self._db, execution) for execution in executions]

    def artifacts(self, query: t.Optional[str] = None) -> t.List["Artifact"]:
        """
        # Find artifact with this ID
            id = 1315
        # Find artifacts with a particular ArtifactType
            type = 'Model'
            type = 'Dataset'
        # Find artifacts using pattern matching
            name LIKE 'models/%'
            name LIKE '%falcon%'
            name LIKE 'datasets/%'
        # Search using properties and custom_properties:
            properties.url.string_value LIKE '%a655dead548f56fe3409321b3569a3%'
            properties.pipeline_tag.string_value = 'text-classification'
            custom_properties.pipeline_tag.string_value = 'text-classification'
        """
        artifacts: t.List[mlpb.Artifact] = self._db.store.get_artifacts(self.list_options(query))
        return [Artifact._create(self._db, artifact) for artifact in artifacts]

    @staticmethod
    def list_options(query: t.Optional[str] = None) -> t.Optional[ListOptions]:
        list_options: t.Optional[ListOptions] = None
        if query:
            list_options = ListOptions(filter_query=query)
        return list_options


def get_python_value(value: mlpb.Value) -> t.Union[str, int, float]:
    """Convert MLMD value to a python value.
    Args:
        value: MLMD value.
    Returns:
        Python value.
    """
    if value.HasField("string_value"):
        return value.string_value
    elif value.HasField("int_value"):
        return value.int_value
    elif value.HasField("double_value"):
        return value.double_value
    raise NotImplementedError("Only string, int and double fields are supported.")
