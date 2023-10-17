import typing as t

from contrib.graph_api import Artifact, Execution, Type, one, unique

__all__ = ["Visitor", "Accept", "Stop", "Traverse", "QueryEngine"]


class Visitor:
    """Class that `visits` MLMD artifact nodes.

    Args:
        acceptor: Callable that takes one artifact and returns True if this node should be accepted (stored in
            `Visitor.artifacts` list).
        stopper: Callable that takes a list of accepted artifacts and returns True of graph traversal should stop.
    """

    def __init__(self, acceptor: t.Optional[t.Callable] = None, stopper: t.Optional[t.Callable] = None) -> None:
        self._acceptor = acceptor or Accept.all
        self._stopper = stopper or Stop.never

        self.artifacts: t.List[Artifact] = []
        """List of accepted artifacts."""

        self.stopped: bool = False
        """True if this visitor has accepted all requested artifacts."""

    def visit(self, artifact: Artifact) -> bool:
        """Process artifact and return True if traversal should stop.
        Args:
            artifact: New artifact to process.
        Returns:
            True if graph traversal should stop.
        """
        if self._acceptor(artifact):
            self.artifacts.append(artifact)
        self.stopped = self._stopper(self.artifacts)
        return self.stopped


class Accept:
    """Class that implements various acceptor functions."""

    @staticmethod
    def all(_artifact: Artifact) -> bool:
        """Accept all artifacts."""
        return True

    @staticmethod
    def by_type(type_: str) -> t.Callable:
        """Accept artifacts of this particular type."""

        def _accept(artifact: Artifact) -> bool:
            return artifact.type.name == type_

        return _accept

    @staticmethod
    def by_id(id_: t.Union[int, t.Set[int]]) -> t.Callable:
        """Accept artifacts with this ID or IDs."""

        def _accept_one(artifact: Artifact) -> bool:
            return artifact.id == id_

        def _accept_many(artifact: Artifact) -> bool:
            return artifact.id in id_

        return _accept_one if isinstance(id_, int) else _accept_many


class Stop:
    """Class that implements various graph traversal stoppers."""

    @staticmethod
    def never(_artifacts: t.List[Artifact]) -> bool:
        """Never stop, visit all nodes."""
        return False

    @staticmethod
    def by_accepted_count(count: int) -> t.Callable:
        """Accept this number of artifacts and stop."""

        def _stop(artifacts: t.List[Artifact]) -> bool:
            return len(artifacts) == count

        return _stop


class Traverse:
    """Upstream and downstream traversal algorithms for artifacts."""

    @staticmethod
    def _traverse(artifact: Artifact, visitor: Visitor, direction: str) -> Visitor:
        """Traverse artifacts in upstream or downstream direction.

        Artifact traversal follows `dependency` path. When traversing downstream, all output artifacts of some execution
            depend on any input artifact, while when traversing upstream, only those output artifacts of some execution
            are considered that are inputs to previously visited executions.

        Args:
            artifact: Anchor artifact to start with.
            visitor: An instance of `Visitor` class that decides what artifacts need to be accepted and when traversal
                should stop.
            direction: One of `upstream` or `downstream`.
        """

        if direction not in ("upstream", "downstream"):
            raise ValueError(f"Internal Error: unsupported traversal direction (`{direction}`).")

        def _next_executions(_artifact: Artifact) -> t.List[Execution]:
            return _artifact.consumed_by() if direction == "downstream" else _artifact.produced_by()

        def _next_artifacts(_execution: Execution) -> t.List[Artifact]:
            return _execution.outputs() if direction == "downstream" else _execution.inputs()

        visited: t.Set[int] = set()
        pending: t.List[Execution] = _next_executions(artifact).copy()

        while pending:
            execution: Execution = pending.pop()
            if execution.id in visited:
                continue
            visited.add(execution.id)
            for artifact in _next_artifacts(execution):
                if visitor.visit(artifact):
                    pending.clear()
                    break
                pending.extend((e for e in _next_executions(artifact) if e.id not in visited))

        return visitor

    @staticmethod
    def downstream(artifact: Artifact, visitor: Visitor) -> Visitor:
        return Traverse._traverse(artifact, visitor, "downstream")

    @staticmethod
    def upstream(artifact: Artifact, visitor: Visitor) -> Visitor:
        return Traverse._traverse(artifact, visitor, "upstream")


class QueryEngine:
    """Query and search engine for ML and pipeline metadata.

    This implementation uses the graph API to access metadata. Basic metadata search is supported by graph API
    (`MlmdGraph`) by providing the following features:
        - Iterating over graph nodes: pipelines, stages, executions and artifacts.
        - Traversing the metadata graph using the following relations:
            pipeline  -> stages, executions, artifacts
            stage     -> pipeline, executions, artifacts
            execution -> stage, artifacts (inputs and outputs)
            artifact  -> executions (consumed_by and produced_by)

    This class is based on `MlmdGraph` to provide high-level query and search features for multiple common use cases.
    """

    def __init__(self) -> None:
        ...

    def is_model_trained_on_dataset(self, model: Artifact, dataset: Artifact) -> bool:
        """Return true if this model was trained on this dataset.

        Args:
            model: Machine learning model
            dataset: Training dataset.
        Returns:
            True if this model was trained on this dataset.

        TODO: (sergey) How do I know if this dataset was used as a train and not test or validation dataset?
        """
        _check_artifact_type(model, Type.MODEL)
        _check_artifact_type(dataset, Type.DATASET)
        visitor: Visitor = Traverse.downstream(dataset, Visitor(Accept.by_id(model.id), Stop.by_accepted_count(1)))
        return visitor.stopped

    def is_on_the_same_lineage_path(self, artifacts: t.List[Artifact]) -> bool:
        """Determine if all artifacts belong to one lineage path.

        Args:
            artifacts: List of artifacts.
        Returns:
            True when all artifacts are connected via dependency chain.
        """
        if not artifacts:
            return False

        artifacts = unique(artifacts.copy(), "id")
        if len(artifacts) == 1:
            return True

        anchor_artifact = artifacts.pop(0)
        ids = set((artifact.id for artifact in artifacts))
        # TODO (sergey) can this accept the same node multiple times so that visited nodes are counted wrong?
        visitor = Visitor(Accept.by_id(ids), Stop.by_accepted_count(len(ids)))

        visitor = Traverse.upstream(anchor_artifact, visitor)
        if not visitor.stopped:
            visitor = Traverse.downstream(anchor_artifact, visitor)

        return visitor.stopped

    def get_datasets_by_dataset(self, dataset: Artifact) -> t.List[Artifact]:
        """Return all datasets produced by executions that directly or indirectly depend on this dataset.

        Args:
            dataset Training dataset.
        Returns:
            Datasets that directly or indirectly depend on input dataset.
        """
        _check_artifact_type(dataset, Type.DATASET)
        visitor: Visitor = Traverse.downstream(dataset, Visitor(Accept.by_type(Type.DATASET)))
        return visitor.artifacts

    def get_models_by_dataset(self, dataset: Artifact) -> t.List[Artifact]:
        """Get all models that depend on this dataset.
        Args:
            dataset: Dataset
        Returns:
            List of unique models trained on the given dataset.
        """
        _check_artifact_type(dataset, Type.DATASET)
        visitor = Traverse.downstream(dataset, Visitor(Accept.by_type(Type.MODEL)))
        return visitor.artifacts

    def get_metrics_by_models(self, models: t.List[Artifact]) -> t.List[Artifact]:
        """Return metrics for each model.

        A model and its metrics are `siblings`, i.e., they must be in the list of output artifacts of some execution.

        Args:
            models: List of models.
        Returns:
            List of artifacts that have `Type.METRICS` type. There's one to one correspondence of models in an input
            list and metrics in an output list.
        """
        metrics: t.List[t.Optional[Artifact]] = [None] * len(models)
        for idx, model in enumerate(models):
            if model.type.name != Type.MODEL:
                raise ValueError(f"Input artifact is not a model (idx={idx}, artifact={model}).")
            execution: Execution = one(
                model.produced_by,
                error=NotImplementedError(
                    f"Multiple producer executions ({len(model.produced_by)}) are not supported yet."
                ),
            )
            metrics[idx] = one(
                [a for a in execution.outputs() if a.type.name == Type.METRICS],
                return_none_if_empty=True,
                error=NotImplementedError("Multiple metrics in one execution are not supported yet."),
            )
        return metrics

    def get_metrics_by_executions(self, executions: t.List[Execution]) -> t.List[Artifact]:
        """Return metrics for each execution.

        Args:
            executions: List of executions.
        Returns:
            List of metrics. There's one to one correspondence of executions in an input list and metrics in
                an output list.
        """
        metrics: t.List[t.Optional[Artifact]] = [None] * len(executions)
        for idx, execution in enumerate(executions):
            metrics[idx] = one(
                [a for a in execution.outputs if a.type.name == Type.METRICS],
                return_none_if_empty=True,
                error=NotImplementedError("Multiple metrics in one execution are not supported yet."),
            )
        return metrics


def _check_artifact_type(artifact: Artifact, type_name: str) -> None:
    """Helper function to check input artifact has required type.

    Args:
        artifact: Input artifact.
        type_name: Name of a type that this artifact is expected to be.
    Raises:
        ValueError when types mismatch.
    """
    if artifact.type.name != type_name:
        raise ValueError(f"Invalid artifact type (type={artifact.type}). Expected type is '{type_name}'.")
