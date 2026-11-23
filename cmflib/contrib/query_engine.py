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

import typing as t

from contrib.graph_api import Artifact, Execution, Node, Type, one, unique

__all__ = ["Visitor", "Accept", "Stop", "Traverse", "QueryEngine"]


class Visitor:
    """Class that `visits` MLMD artifact nodes.

    It is used to traverse MLMD graph and to collect artifacts of interest. An artifact is collected if it is accepted
    by an acceptor function.

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
    """Class that implements various acceptor functions.

    They are used to inform graph visitors if a particular artifact (or node in general) should be collected. All
    acceptor functions must accept one parameter of type `Node` and return True if this artifact is "accepted", e.g.,
    matchers user criteria.
    """

    @staticmethod
    def all(_node: Node) -> bool:
        """Accept all artifacts."""
        return True

    @staticmethod
    def by_type(type_: str) -> t.Callable:
        """Accept artifacts of this particular type."""

        def _accept(node: Node) -> bool:
            return node.type.name == type_

        return _accept

    @staticmethod
    def by_id(id_: t.Union[int, t.Set[int]]) -> t.Callable:
        """Accept artifacts with this ID or IDs."""

        def _accept_one(node: Node) -> bool:
            return node.id == id_

        def _accept_many(node: Node) -> bool:
            return node.id in id_

        return _accept_one if isinstance(id_, int) else _accept_many


class Stop:
    """Class that implements various graph traversal stoppers.

    Teh visitor instance can instruct the traversal algorithm to stop after visiting each artifact in a graph. Stopper
    functions are used to determine if traversal should be stopped. A stopper function accepts one argument - list of
    collected (accepted) artifacts so far, and returns True if traversal should be stopped.
    """

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


# noinspection PyMethodMayBeStatic
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

    TODO (sergey) Some methods assume (for simplicity) that any given artifact has only one producer execution.
    """

    def __init__(self) -> None:
        ...

    def is_direct_descendant(self, parent: Artifact, child: Artifact) -> bool:
        """Return true if the given child is the direct descendant of the given parent.

        This implementation assumes that the iven child was produced by exactly one execution. The parent and
        child must then be related as: [parent] --input-> execution --output--> [child]

        Args:
             parent: Candidate parent.
             child: Candidate child.
        Returns:
            True if given child is the direct descendant of the given parent.
        """
        # FIXME (sergey) assumption is there's only one producer execution.
        execution: Execution = one(child.produced_by())
        input_ids: t.Set[int] = set((artifact.id for artifact in execution.inputs()))
        return parent.id in input_ids

    def is_descendant(self, ancestor: Artifact, descendant: Artifact) -> bool:
        """Identify if `descendant` artifact depends on `ancestor` artifact implicitly or explicitly.

        Args:
            ancestor: Artifact that is supposedly resulted in descendant.
            descendant: Artifact that is supposedly depend on ancestor.
        Returns:
            True if ancestor and descendant are on the same lineage path, and descendant is the downstream for ancestor.
        """
        visitor: Visitor = Traverse.downstream(
            ancestor, Visitor(Accept.by_id(descendant.id), Stop.by_accepted_count(1))
        )
        return visitor.stopped

    def is_on_the_same_lineage_path(self, artifacts: t.List[Artifact]) -> bool:
        """Determine if all artifacts belong to one lineage path.

        Args:
            artifacts: List of artifacts.
        Returns:
            True when all artifacts are connected via a dependency chain.
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

    def get_siblings(
        self, artifact: Artifact, select: t.Optional[t.Callable[[Artifact], bool]] = None
    ) -> t.List[Artifact]:
        """Get all siblings of the given node.

        Siblings in this method are defined as other artifacts produced by the same execution that produced this
        artifact. It is assumed there's one producer execution. The artifact itself is not sibling to itself.

        Args:
            artifact: Artifact.
            select: Callable object that accepts an artifact and returns True if this artifact should be added to list
                of siblings. The artifact itself is excluded from siblings automatically.
        """
        # FIXME (sergey) assumption is there's only one producer execution.
        execution: Execution = one(artifact.produced_by())
        siblings = [sibling for sibling in execution.outputs() if sibling.id != artifact.id]
        return _select(siblings, select)

    def get_direct_descendants(
        self,
        parent: Artifact,
        select_executions_fn: t.Optional[t.Callable[[Execution], bool]] = None,
        select_artifact_fn: t.Optional[t.Callable[[Artifact], bool]] = None,
    ) -> t.List[t.Tuple[Execution, t.List[Artifact]]]:
        """Return all direct descendants (immediate children) of the given parent artifact.

        Immediate descendants are those for which `is_direct_descendant` method returns True - see doc strings for more
        details.

        """
        descendants: t.List[t.Tuple[Execution, t.List[Artifact]]] = []
        executions = _select(parent.consumed_by(), select_executions_fn)
        for execution in executions:
            execution_outputs = _select(execution.outputs(), select_artifact_fn)
            if execution_outputs:
                descendants.append((execution, execution_outputs))
        return descendants

    def get_descendants(
        self, artifact: Artifact, select_fn: t.Optional[t.Callable[[Artifact], bool]] = None
    ) -> t.List[Artifact]:
        """Get all descendants of the given artifact.

        A descendant is defined as an artifact reachable starting the anchor node and traversing downstream.

        Args:
            artifact: Anchor artifact.
            select_fn: Only those artifacts for which this callable returns True are returned.
        Returns:
            List of all descendants artifacts for which select_fn(descendant) == True.
        """
        visitor: Visitor = Traverse.downstream(artifact, Visitor(acceptor=select_fn))
        return visitor.artifacts

    def is_model_trained_on_dataset(self, model: Artifact, dataset: Artifact) -> bool:
        """Return true if this model was trained on this dataset.

        This method verifies there is a path between the `dataset` and the `model`, in other words, the model should
        be reachable when traversing MLMD graph starting from the `dataset` node in the downstream direction.
        Depending on adopted best practices, there maybe an easier (better to some extent) approach to test this. In
        some cases, a model and a dataset must be connected to the same execution in order to be related via
        `trained_on` relation.

        Args:
            model: Machine learning model
            dataset: Training dataset.
        Returns:
            True if this model was trained on this dataset.
        """
        _check_artifact_type(model, Type.MODEL)
        _check_artifact_type(dataset, Type.DATASET)
        return self.is_descendant(ancestor=dataset, descendant=model)

    def get_datasets_by_dataset(
        self, dataset: Artifact, select_fn: t.Optional[t.Callable[[Artifact], bool]]
    ) -> t.List[Artifact]:
        """Return all datasets produced by executions that directly or indirectly depend on this dataset.

        Args:
            dataset: Training dataset.
            select_fn: Function to select datasets matching certain criteria. This function does not need to check
                artifact type - datasets are selected automatically.
        Returns:
            Datasets that directly or indirectly depend on input dataset.
        """
        _check_artifact_type(dataset, Type.DATASET)
        return self.get_descendants(dataset, _combine_select_fn(Accept.by_type(Type.DATASET), select_fn))

    def get_models_by_dataset(
        self, dataset: Artifact, select_fn: t.Optional[t.Callable[[Artifact], bool]]
    ) -> t.List[Artifact]:
        """Get all models that depend on this dataset.
        Args:
            dataset: Dataset
            select_fn: Function to select models matching certain criteria. This function does not need to check
                artifact type - models are selected automatically.
        Returns:
            List of unique models trained on the given dataset.
        """
        _check_artifact_type(dataset, Type.DATASET)
        return self.get_descendants(dataset, _combine_select_fn(Accept.by_type(Type.MODEL), select_fn))

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
            _check_artifact_type(model, Type.MODEL)
            metrics[idx] = one(
                self.get_siblings(model, Accept.by_type(Type.METRICS)),
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
            # FIXME (sergey): It is assumed there's one or zero metric artifacts for each execution.
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


def _select(items: t.List, select_fn: t.Optional[t.Callable[[t.Any], bool]] = None) -> t.List:
    """Select items from `items` using select_fn condition.

    Args:
        items: Input list of items.
        select_fn: Callable object that accepts one item from items and returns True if it should be selected.
    Returns:
         Input list if `select_fn` is None, else those items for which select_fn(item) returns True.
    """
    if not select_fn:
        return items
    return [item for item in items if select_fn(item)]


def _combine_select_fn(func_a: t.Callable, func_b: t.Optional[t.Callable] = None) -> t.Callable:
    """Combine two selection functions using AND operator.

    Selection function is a function that takes one parameter and returns True or False.

    Args:
        func_a: First selection function is always present.
        func_b: Second selection function is optional.
    Returns:
        func_a if func_b is None else new function that implements func_a(input) and func_b(input)
    """
    if func_b is None:
        return func_a

    def _combined_fn(node: t.Any) -> bool:
        return func_a(node) and func_b(node)

    return _combined_fn
