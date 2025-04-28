import unittest
from unittest.mock import MagicMock
from cmflib.cmfquery import CmfQuery
from ml_metadata.proto.metadata_store_pb2 import Artifact, Context
import pandas as pd


class TestCmfQuery(unittest.TestCase):

    def test_on_collision(self):
        from cmflib.cmfquery import _KeyMapper
        self.assertEqual(3, len(_KeyMapper.OnCollision))
        self.assertEqual(0, _KeyMapper.OnCollision.DO_NOTHING.value)
        self.assertEqual(1, _KeyMapper.OnCollision.RESOLVE.value)
        self.assertEqual(2, _KeyMapper.OnCollision.RAISE_ERROR.value)

    def test_dict_mapper(self):
        from cmflib.cmfquery import _DictMapper, _KeyMapper

        dm = _DictMapper({"src_key": "tgt_key"}, on_collision=_KeyMapper.OnCollision.RESOLVE)
        self.assertEqual("tgt_key", dm.get({}, "src_key"))
        self.assertEqual("other_key", dm.get({}, "other_key"))
        self.assertEqual("existing_key_1", dm.get({"existing_key": "value"}, "existing_key"))
        self.assertEqual("existing_key_2", dm.get({"existing_key": "value", "existing_key_1": "value_1"}, "existing_key"))

        dm = _DictMapper({"src_key": "tgt_key"}, on_collision=_KeyMapper.OnCollision.DO_NOTHING)
        self.assertEqual("existing_key", dm.get({"existing_key": "value"}, "existing_key"))

    def test_prefix_mapper(self):
        from cmflib.cmfquery import _PrefixMapper, _KeyMapper

        pm = _PrefixMapper("nested_", on_collision=_KeyMapper.OnCollision.RESOLVE)
        self.assertEqual("nested_src_key", pm.get({}, "src_key"))

        self.assertEqual("nested_existing_key_1", pm.get({"nested_existing_key": "value"}, "existing_key"))
        self.assertEqual(
            "nested_existing_key_2",
            pm.get({"nested_existing_key": "value", "nested_existing_key_1": "value_1"}, "existing_key"),
        )

        dm = _PrefixMapper("nested_", on_collision=_KeyMapper.OnCollision.DO_NOTHING)
        self.assertEqual("nested_existing_key", dm.get({"nested_existing_key": "value"}, "existing_key"))

    def test_get_artifact(self):
        # Arrange
        mock_store = MagicMock()
        query = CmfQuery()
        query.store = mock_store

        # Mock the return value of `get_artifacts`
        mock_artifact1 = Artifact(name="artifact1")
        mock_artifact2 = Artifact(name="artifact2")
        mock_store.get_artifacts.return_value = [mock_artifact1, mock_artifact2]

        # Act
        result = query._get_artifact("artifact1")

        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "artifact1")
        mock_store.get_artifacts.assert_called_once()  # assert that get_artifacts was called once

        # Test for non-existent artifact
        result = query._get_artifact("non_existent_artifact")
        self.assertIsNone(result)

    def test_get_pipeline_names(self):
        """Test retrieving pipeline names."""
        # Arrange
        mock_store = MagicMock()
        query = CmfQuery()
        query.store = mock_store

        # Mock the return value of `get_contexts_by_type`
        mock_store.get_contexts_by_type.return_value = [
            Context(name="pipeline1"),
            Context(name="pipeline2"),
        ]

        # Act
        pipeline_names = query.get_pipeline_names()

        # Assert
        self.assertEqual(pipeline_names, ["pipeline1", "pipeline2"])
        mock_store.get_contexts_by_type.assert_called_once_with("Parent_Context")

    def test_get_pipeline_id(self):
        # Arrange
        mock_store = MagicMock()
        query = CmfQuery()
        query.store = mock_store

        # Mock the return value of `get_contexts_by_type`
        mock_pipeline1 = Context(id=1, name="pipeline1")
        mock_pipeline2 = Context(id=2, name="pipeline2")
        mock_store.get_contexts_by_type.return_value = [mock_pipeline1, mock_pipeline2]

        # Act
        pipeline_id = query.get_pipeline_id("pipeline1")

        # Assert
        self.assertEqual(pipeline_id, 1)
        mock_store.get_contexts_by_type.assert_called_once_with("Parent_Context")

        # Test for non-existent pipeline
        pipeline_id = query.get_pipeline_id("non_existent_pipeline")
        self.assertEqual(pipeline_id, -1)

    def test_get_pipeline_stages(self):
        """Test retrieving pipeline stages."""
        # Arrange
        mock_store = MagicMock()
        query = CmfQuery()
        query.store = mock_store

        # Mock the return value of `get_contexts_by_type` and `get_children_contexts_by_context`
        mock_pipeline = Context(id=1, name="pipeline1")
        mock_store.get_contexts_by_type.return_value = [mock_pipeline]
        mock_store.get_children_contexts_by_context.return_value = [
            Context(name="stage1"),
            Context(name="stage2"),
        ]

        # Act
        stages = query.get_pipeline_stages("pipeline1")

        # Assert
        self.assertEqual(stages, ["stage1", "stage2"])
        mock_store.get_contexts_by_type.assert_called_once_with("Parent_Context")
        mock_store.get_children_contexts_by_context.assert_called_once_with(1)

    def test_get_all_executions_by_ids_list(self):
        """Test retrieving all executions by a list of execution IDs."""
        # Arrange
        mock_store = MagicMock()
        query = CmfQuery()
        query.store = mock_store

        # Mock the return value of `get_executions_by_id`
        mock_execution1 = MagicMock()
        mock_execution1.id = 100
        mock_execution1.properties = {"Execution_type_name": MagicMock(string_value="type1")}
        mock_execution2 = MagicMock()
        mock_execution2.id = 101
        mock_execution2.properties = {"Execution_type_name": MagicMock(string_value="type2")}
        mock_store.get_executions_by_id.return_value = [mock_execution1, mock_execution2]

        # Mock the `_transform_to_dataframe` method
        query._transform_to_dataframe = MagicMock(side_effect=lambda execution: pd.DataFrame([{
            "id": execution.id,
            "Execution_type_name": execution.properties["Execution_type_name"].string_value
        }]))

        # Act
        executions_df = query.get_all_executions_by_ids_list([100, 101])

        # Assert
        self.assertEqual(len(executions_df), 2)
        self.assertIn("id", executions_df.columns)
        self.assertIn("Execution_type_name", executions_df.columns)
        self.assertEqual(executions_df.iloc[0]["id"], 100)
        self.assertEqual(executions_df.iloc[0]["Execution_type_name"], "type1")
        self.assertEqual(executions_df.iloc[1]["id"], 101)
        self.assertEqual(executions_df.iloc[1]["Execution_type_name"], "type2")
        mock_store.get_executions_by_id.assert_called_once_with([100, 101])
        query._transform_to_dataframe.assert_any_call(mock_execution1)
        query._transform_to_dataframe.assert_any_call(mock_execution2)

    def test_get_all_artifact_types(self):
        """Test retrieving all artifact types."""
        # Arrange
        mock_store = MagicMock()
        query = CmfQuery()
        query.store = mock_store

        # Mock the return value of `get_artifact_types`
        mock_store.get_artifact_types.return_value = [
            type("ArtifactType", (object,), {"name": "Dataset"})(),
            type("ArtifactType", (object,), {"name": "Model"})(),
            type("ArtifactType", (object,), {"name": "Metrics"})(),
        ]

        # Act
        artifact_types = query.get_all_artifact_types()

        # Assert
        self.assertEqual(len(artifact_types), 3)
        self.assertIn("Dataset", artifact_types)
        self.assertIn("Model", artifact_types)
        self.assertIn("Metrics", artifact_types)
        mock_store.get_artifact_types.assert_called_once()


if __name__ == "__main__":
    unittest.main()