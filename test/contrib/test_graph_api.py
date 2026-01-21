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
from pathlib import Path
from tempfile import gettempdir
from unittest import TestCase, skipUnless

from cmflib.contrib.graph_api import (
    Artifact,
    Execution,
    MlmdGraph,
    Node,
    Pipeline,
    Properties,
    Stage,
    Type,
    _graph_node,
    one,
    unique,
)

_TEST_MLMD_FILE = Path(gettempdir(), "mlmd.sqlite")
"""This file must exist for test in this module to run, else they will be skipped."""


class AttrTest:
    """Helper class to run test for an object's attributed.

    Args:
        attr: Name of an object attribute.
        expected_type: Expected type of attribute value.
        test_fn: callable object that takes an attribute value and returns true/false (additional checks).
    """

    def __init__(self, attr: str, expected_type: t.Type, test_fn: t.Optional[t.Callable] = None) -> None:
        self.attr = attr
        self.expected_type = expected_type
        self.test_fn = test_fn or (lambda v: True)

    def __call__(self, test_case: TestCase, obj: t.Any) -> None:
        """Run a test against this attribute.

        Args:
            test_case: Test case instance that runs this test.
            obj: Object to run attribute test for.
        """
        # Test attribute exists and check attribute's value type.
        test_case.assertTrue(hasattr(obj, self.attr), f"Attribute does not exist (attr={self.attr}, node={obj}).")
        value = getattr(obj, self.attr)
        test_case.assertIsInstance(
            value,
            self.expected_type,
            f"Wrong attr type (attr={self.attr}, actual_type={type(value)}, "
            f"expected_type={self.expected_type}, object={obj}).",
        )
        # Run additional tests.
        test_case.assertTrue(
            self.test_fn(value),
            f"Test is false for object attribute (attr={self.attr}, value={value}, "
            f"type={self.expected_type}, object={obj}).",
        )


class ObjTest:
    """Run tests against some object.

    Args:
        expected_type: Expected type of this object.
        attr_tests: Tests for object's attributes.
    """

    def __init__(self, expected_type: t.Type, attr_tests: t.Optional[t.List[AttrTest]] = None) -> None:
        self.expected_type = expected_type
        self.attr_tests = attr_tests or []

    def __call__(self, test_case: TestCase, obj: t.Any) -> None:
        """Run a test against this object.

        Args:
            test_case: Test case instance that runs this test.
            obj: Object to run this test for.
        """
        test_case.assertIsInstance(obj, self.expected_type)
        for attr_test in self.attr_tests:
            attr_test(test_case, obj)


@skipUnless(_TEST_MLMD_FILE.exists(), f"The `mlmd.sqlite` does not exist in {gettempdir()}.")
class TestNodes(TestCase):
    def setUp(self):
        self.md = MlmdGraph(_TEST_MLMD_FILE.as_posix())
        """The `md` stands for metadata."""

    def test_types(self) -> None:
        # Test type names for accidental change.
        self.assertEqual(Type.PIPELINE, "Parent_Context")
        self.assertEqual(Type.STAGE, "Pipeline_Stage")
        self.assertEqual(Type.DATASET, "Dataset")
        self.assertEqual(Type.MODEL, "Model")
        self.assertEqual(Type.METRICS, "Metrics")

        # Tester instance for `Type` instances.
        attr_test = ObjTest(
            Type,
            [
                AttrTest("id", int, lambda v: v >= 0),
                AttrTest("name", str, lambda v: len(v) > 0),
                AttrTest("version", str, lambda v: len(v) >= 0),
                AttrTest("description", str, lambda v: len(v) >= 0),
                AttrTest("external_id", str, lambda v: len(v) >= 0),
                AttrTest("properties", Properties),
            ],
        )

        # Test types for pipelines, stages, executions and artifacts.
        def _test_types(_nodes: t.List[Node], _expected_type_name: t.Optional[str] = None) -> None:
            self.assertTrue(len(_nodes) > 0)
            for _node in _nodes:
                if _expected_type_name is not None:
                    self.assertEqual(_node.type.name, _expected_type_name)
                attr_test(self, _node.type)

        _test_types(self.md.pipelines(), Type.PIPELINE)
        _test_types(self.md.stages(), Type.STAGE)
        _test_types(self.md.executions())
        _test_types(self.md.artifacts())

    def test_base(self) -> None:
        pipelines: t.List[Pipeline] = self.md.pipelines()
        self.assertTrue(len(pipelines) > 0)

        pipeline: Pipeline = pipelines[0]
        # Test these properties are read-only.
        self.assertRaises(AttributeError, setattr, pipeline, "id", 1)
        self.assertRaises(AttributeError, setattr, pipeline, "name", "new name")

        # Test properties and custom properties are read only
        with self.assertRaises(TypeError):
            pipeline.properties["key"] = "value"
        with self.assertRaises(TypeError):
            pipeline.custom_properties["key"] = "value"

        # Test users can iterate over properties and custom properties
        for k, v in pipeline.properties.items():
            print("properties (k, v):", k, v)
        for k, v in pipeline.custom_properties.items():
            print("custom_properties (k, v):", k, v)

    def test_pipelines(self) -> None:
        pipelines: t.List[Pipeline] = self.md.pipelines()
        self.assertTrue(len(pipelines) > 0)
        for pipeline in pipelines:
            self.assertIsInstance(pipeline, Pipeline)
            self.assertEqual(pipeline.type.name, Type.PIPELINE)

            self._test_list_of_nodes(pipeline.stages(), Stage, Type.STAGE)
            self._test_list_of_nodes(pipeline.executions(), Execution, None)
            self._test_list_of_nodes(pipeline.artifacts(), Artifact, None)

    def test_stages(self) -> None:
        stages: t.List[Stage] = self.md.stages()
        self.assertTrue(len(stages) > 0)
        for stage in stages:
            self.assertIsInstance(stage.pipeline, Pipeline)
            self.assertEqual(stage.pipeline.type.name, Type.PIPELINE)
            self._test_list_of_nodes(stage.executions(), Execution, None)
            self._test_list_of_nodes(stage.artifacts(), Artifact, None, empty_ok=True)

    def test_executions(self) -> None:
        executions: t.List[Execution] = self.md.executions()
        self.assertTrue(len(executions) > 0)
        for execution in executions:
            self.assertIsInstance(execution.stage, Stage)
            self._test_list_of_nodes(execution.inputs(), Artifact, None, empty_ok=True)
            self._test_list_of_nodes(execution.outputs(), Artifact, None, empty_ok=True)

    def test_artifacts(self) -> None:
        artifacts: t.List[Artifact] = self.md.artifacts()
        self.assertTrue(len(artifacts) > 0)
        for artifact in artifacts:
            # TODO (sergey) in the test MLMD dataset produced_by() returns empty lists sometimes
            self._test_list_of_nodes(artifact.produced_by(), Execution, None, empty_ok=True)
            self._test_list_of_nodes(artifact.consumed_by(), Execution, None, empty_ok=True)

    def _test_list_of_nodes(
        self, nodes: t.List[Node], node_type_cls: t.Type, type_name: t.Optional[str] = None, empty_ok: bool = False
    ) -> None:
        if empty_ok:
            self.assertTrue(len(nodes) >= 0)
        else:
            self.assertTrue(len(nodes) > 0)
        for node in nodes:
            self.assertIsInstance(node, node_type_cls)
            if type_name is not None:
                self.assertEqual(node.type.name, type_name)


@skipUnless(_TEST_MLMD_FILE.exists(), f"The `mlmd.sqlite` does not exist in {gettempdir()}.")
class TestGraphAPI(TestCase):
    def setUp(self):
        self.md = MlmdGraph(_TEST_MLMD_FILE.as_posix())
        """The `md` stands for metadata."""

    def _compare_nodes(self, node1: Node, node2: Node, must_equal: bool = True) -> None:
        """Check that two graph nodes are the same or different by invoking `hash` and `__eq__` methods."""
        assert_fn = self.assertEqual if must_equal else self.assertNotEqual
        assert_fn(hash(node1), hash(node2))
        assert_fn(node1, node2)

    def _test_nodes(self, nodes: t.List[Node], obj_test: ObjTest, other_types: t.List[t.Type[Node]]) -> None:
        """Run common tests for graph nodes."""
        # Check node type and common attributes
        for node in nodes:
            obj_test(self, node)

        # Check __hash__ and __eq__ methods
        _graph_node(obj_test.expected_type, nodes[0]._db, nodes[0]._node)
        self._compare_nodes(
            nodes[0], _graph_node(obj_test.expected_type, nodes[0]._db, nodes[0]._node), must_equal=True
        )
        self._compare_nodes(nodes[0], nodes[1], must_equal=False)
        for other_type in other_types:
            self._compare_nodes(nodes[0], _graph_node(other_type, nodes[0]._db, nodes[0]._node), must_equal=False)

    def _test_psa(self, nodes: t.List[Node], expected_node_type: t.Type, other_types: t.List[t.Type[Node]]) -> None:
        """Run tests against metadata nodes for Pipelines, Stages and Attributes."""
        self.assertTrue(len(nodes) > 0)
        self._test_nodes(
            nodes,
            ObjTest(
                expected_node_type,
                [
                    AttrTest("id", int, lambda v: v >= 0),
                    AttrTest("name", str, lambda v: len(v) > 0),
                    AttrTest("type", Type),
                ],
            ),
            other_types,
        )

    def test_pipelines(self) -> None:
        self._test_psa(self.md.pipelines(), Pipeline, [Stage, Execution, Artifact])

    def test_stages(self) -> None:
        self._test_psa(self.md.stages(), Stage, [Pipeline, Execution, Artifact])

    def test_artifacts(self) -> None:
        self._test_psa(self.md.artifacts(), Artifact, [Pipeline, Execution, Stage])

    def test_executions(self) -> None:
        """Run tests for executions.

        TODO: (sergey) value of the `name` attribute is empty for some or all executions. Is this expected?
        """
        executions: t.List[Execution] = self.md.executions()
        self.assertTrue(len(executions) > 0)
        self._test_nodes(
            executions,
            ObjTest(
                Execution,
                [
                    AttrTest("id", int, lambda v: v >= 0),
                    AttrTest("name", str, lambda v: len(v) >= 0),
                    AttrTest("type", Type),
                ],
            ),
            [Pipeline, Stage, Artifact],
        )


@skipUnless(_TEST_MLMD_FILE.exists(), f"The `mlmd.sqlite` does not exist in {gettempdir()}.")
class TestListOperators(TestCase):
    def setUp(self):
        self.md = MlmdGraph(_TEST_MLMD_FILE.as_posix())
        """The `md` stands for metadata."""

    def test_one(self) -> None:
        # Check default parameters
        self.assertEqual(one([1]), 1)
        self.assertRaises(ValueError, one, [])
        self.assertRaises(RuntimeError, one, [], error=RuntimeError())

        # Check input is empty
        self.assertIsNone(one([], return_none_if_empty=True))
        self.assertIsNone(one([], return_none_if_empty=True, error=RuntimeError()))

        # Check input contains multiple elements
        self.assertRaises(ValueError, one, [1, 2])
        self.assertRaises(ValueError, one, [1, 2], return_none_if_empty=True)
        self.assertRaises(RuntimeError, one, [1, 2], return_none_if_empty=True, error=RuntimeError())

    def test_unique(self) -> None:
        #
        self.assertListEqual(unique([1, 2, 3, 4]), [1, 2, 3, 4])
        self.assertListEqual(unique([12, 12, 45, 66, 67, 888]), [12, 45, 66, 67, 888])
        self.assertListEqual(unique([12, 45, 66, 67, 66, 888]), [12, 45, 66, 67, 888])
        self.assertListEqual(unique([45, 12, 45, 66, 67, 66, 888]), [45, 12, 66, 67, 888])
        self.assertListEqual(unique([12, 45, 66, 67, 888, 888]), [12, 45, 66, 67, 888])

        #
        ps: t.List[Pipeline] = self.md.pipelines()
        self.assertListEqual(unique([ps[0], ps[1]], "id"), [ps[0], ps[1]])
        self.assertListEqual(unique([ps[0], ps[0]], "id"), [ps[0]])
