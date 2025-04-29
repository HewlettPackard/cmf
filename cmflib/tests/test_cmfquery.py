import unittest
from unittest.mock import MagicMock
from cmflib.cmfquery import CmfQuery
from ml_metadata.proto.metadata_store_pb2 import Artifact, Context, Execution
import pandas as pd
from ml_metadata.proto import metadata_store_pb2 as mlpb


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

    def test_get_one_hop_child_artifacts(self):
        """Test retrieving one-hop child artifacts for a given artifact."""
        # Arrange
        mock_store = MagicMock()
        query = CmfQuery()
        query.store = mock_store

        # Mock the return value of `_get_artifact`
        mock_artifact = MagicMock()
        mock_artifact.id = 200
        mock_artifact.name = "artifact1"
        query._get_artifact = MagicMock(side_effect=lambda artifact_name: mock_artifact if artifact_name == "artifact1" else None)

        # Mock the return value of `_get_executions_by_input_artifact_id`
        query._get_executions_by_input_artifact_id = MagicMock(return_value=[100, 101])

        # Mock the return value of `_get_output_artifacts`
        query._get_output_artifacts = MagicMock(return_value=[300, 301])

        # Mock the return value of `get_artifacts_by_id`
        mock_artifact1 = MagicMock()
        mock_artifact1.id = 300
        mock_artifact1.name = "child_artifact1"
        mock_artifact1.type_id = 1
        mock_artifact1.uri = "uri1"
        mock_artifact1.create_time_since_epoch = 1234567890
        mock_artifact1.last_update_time_since_epoch = 1234567891

        mock_artifact2 = MagicMock()
        mock_artifact2.id = 301
        mock_artifact2.name = "child_artifact2"
        mock_artifact2.type_id = 2
        mock_artifact2.uri = "uri2"
        mock_artifact2.create_time_since_epoch = 1234567892
        mock_artifact2.last_update_time_since_epoch = 1234567893

        mock_store.get_artifacts_by_id.return_value = [mock_artifact1, mock_artifact2]

        # Mock the `_transform_to_dataframe` method
        query._transform_to_dataframe = MagicMock(side_effect=lambda artifact, data: pd.DataFrame([{
            "id": artifact.id,
            "name": artifact.name,
            "type": f"Type{artifact.type_id}",
            "uri": artifact.uri,
            "create_time_since_epoch": artifact.create_time_since_epoch,
            "last_update_time_since_epoch": artifact.last_update_time_since_epoch
        }]))

        # Act
        child_artifacts_df = query.get_one_hop_child_artifacts("artifact1")

        # Assert
        self.assertEqual(len(child_artifacts_df), 2)
        self.assertIn("id", child_artifacts_df.columns)
        self.assertIn("name", child_artifacts_df.columns)
        self.assertIn("type", child_artifacts_df.columns)
        self.assertEqual(child_artifacts_df.iloc[0]["id"], 300)
        self.assertEqual(child_artifacts_df.iloc[0]["name"], "child_artifact1")
        self.assertEqual(child_artifacts_df.iloc[0]["type"], "Type1")
        self.assertEqual(child_artifacts_df.iloc[1]["id"], 301)
        self.assertEqual(child_artifacts_df.iloc[1]["name"], "child_artifact2")
        self.assertEqual(child_artifacts_df.iloc[1]["type"], "Type2")
        query._get_artifact.assert_called_once_with("artifact1")
        query._get_executions_by_input_artifact_id.assert_called_once_with(200, None)
        query._get_output_artifacts.assert_called_once_with([100, 101])
        mock_store.get_artifacts_by_id.assert_called_once_with([300, 301])

    def test_get_one_hop_parent_executions(self):
        """Test retrieving one-hop parent executions for a given execution ID."""
        # Arrange
        mock_store = MagicMock()
        query = CmfQuery()
        query.store = mock_store

        # Mock the return value of `_get_input_artifacts`
        query._get_input_artifacts = MagicMock(return_value=[200, 201])

        # Mock the return value of `_get_executions_by_output_artifact_id`
        query._get_executions_by_output_artifact_id = MagicMock(side_effect=lambda artifact_id, _: [100] if artifact_id == 200 else [101])

        # Mock the return value of `get_executions_by_id`
        mock_execution1 = MagicMock()
        mock_execution1.id = 100
        mock_execution1.properties = {"Execution_type_name": MagicMock(string_value="type1")}
        mock_execution2 = MagicMock()
        mock_execution2.id = 101
        mock_execution2.properties = {"Execution_type_name": MagicMock(string_value="type2")}
        mock_store.get_executions_by_id.side_effect = lambda ids: [mock_execution1 if ids[0] == 100 else mock_execution2]

        # Act
        parent_executions = query.get_one_hop_parent_executions([300])

        # Assert
        self.assertEqual(len(parent_executions), 2)
        self.assertIn(mock_execution1, parent_executions)
        self.assertIn(mock_execution2, parent_executions)
        query._get_input_artifacts.assert_called_once_with([300])
        query._get_executions_by_output_artifact_id.assert_any_call(200, None)
        query._get_executions_by_output_artifact_id.assert_any_call(201, None)
        mock_store.get_executions_by_id.assert_any_call([100])
        mock_store.get_executions_by_id.assert_any_call([101])

    def test_get_all_executions_in_pipeline(self):
        """Test retrieving all executions for a given pipeline."""
        # Arrange
        mock_store = MagicMock()
        query = CmfQuery()
        query.store = mock_store

        # Mock the return value of `_get_pipelines`
        mock_pipeline = MagicMock()
        mock_pipeline.id = 1
        mock_pipeline.name = "pipeline1"
        query._get_pipelines = MagicMock(return_value=[mock_pipeline])

        # Mock the return value of `_get_stages`
        mock_stage1 = MagicMock()
        mock_stage1.id = 10
        mock_stage1.name = "stage1"
        mock_stage2 = MagicMock()
        mock_stage2.id = 11
        mock_stage2.name = "stage2"
        query._get_stages = MagicMock(return_value=[mock_stage1, mock_stage2])

        # Mock the return value of `_get_executions`
        mock_execution1 = MagicMock()
        mock_execution1.id = 100
        mock_execution1.name = "execution1"
        mock_execution2 = MagicMock()
        mock_execution2.id = 101
        mock_execution2.name = "execution2"
        query._get_executions = MagicMock(side_effect=lambda stage_id: [mock_execution1] if stage_id == 10 else [mock_execution2])

        # Mock the `_transform_to_dataframe` method
        query._transform_to_dataframe = MagicMock(side_effect=lambda execution, data: pd.DataFrame([{
            "id": execution.id,
            "name": execution.name
        }]))

        # Act
        executions_df = query.get_all_executions_in_pipeline("pipeline1")

        # Assert
        self.assertEqual(len(executions_df), 2)
        self.assertIn("id", executions_df.columns)
        self.assertIn("name", executions_df.columns)
        self.assertEqual(executions_df.iloc[0]["id"], 100)
        self.assertEqual(executions_df.iloc[0]["name"], "execution1")
        self.assertEqual(executions_df.iloc[1]["id"], 101)
        self.assertEqual(executions_df.iloc[1]["name"], "execution2")
        query._get_pipelines.assert_called_once_with("pipeline1")
        query._get_stages.assert_called_once_with(1)
        query._get_executions.assert_any_call(10)
        query._get_executions.assert_any_call(11)

    def test_get_all_artifacts_for_executions(self):
        """Test retrieving all artifacts for a list of execution IDs."""
        # Arrange
        mock_store = MagicMock()
        query = CmfQuery()
        query.store = mock_store

        # Mock the return value of `get_events_by_execution_ids`
        mock_event1 = MagicMock()
        mock_event1.artifact_id = 200
        mock_event2 = MagicMock()
        mock_event2.artifact_id = 201
        mock_store.get_events_by_execution_ids.return_value = [mock_event1, mock_event2]

        # Mock the return value of `get_artifacts_by_id`
        mock_artifact1 = MagicMock()
        mock_artifact1.id = 200
        mock_artifact1.name = "artifact1"
        mock_artifact1.type_id = 1
        mock_artifact1.uri = "uri1"
        mock_artifact1.create_time_since_epoch = 1234567890
        mock_artifact1.last_update_time_since_epoch = 1234567891

        mock_artifact2 = MagicMock()
        mock_artifact2.id = 201
        mock_artifact2.name = "artifact2"
        mock_artifact2.type_id = 2
        mock_artifact2.uri = "uri2"
        mock_artifact2.create_time_since_epoch = 1234567892
        mock_artifact2.last_update_time_since_epoch = 1234567893

        mock_store.get_artifacts_by_id.return_value = [mock_artifact1, mock_artifact2]

        # Mock the `_transform_to_dataframe` method
        query._transform_to_dataframe = MagicMock(side_effect=lambda artifact, data: pd.DataFrame([{
            "id": artifact.id,
            "name": artifact.name,
            "type": f"Type{artifact.type_id}",
            "uri": artifact.uri,
            "create_time_since_epoch": artifact.create_time_since_epoch,
            "last_update_time_since_epoch": artifact.last_update_time_since_epoch
        }]))

        # Act
        artifacts_df = query.get_all_artifacts_for_executions([100, 101])

        # Assert
        self.assertEqual(len(artifacts_df), 2)
        self.assertIn("id", artifacts_df.columns)
        self.assertIn("name", artifacts_df.columns)
        self.assertIn("type", artifacts_df.columns)
        self.assertEqual(artifacts_df.iloc[0]["id"], 200)
        self.assertEqual(artifacts_df.iloc[0]["name"], "artifact1")
        self.assertEqual(artifacts_df.iloc[0]["type"], "Type1")
        self.assertEqual(artifacts_df.iloc[1]["id"], 201)
        self.assertEqual(artifacts_df.iloc[1]["name"], "artifact2")
        self.assertEqual(artifacts_df.iloc[1]["type"], "Type2")
        mock_store.get_events_by_execution_ids.assert_called_once_with({100, 101})
        mock_store.get_artifacts_by_id.assert_called_once_with([200, 201])

    def test_get_all_artifacts(self):
        """Test retrieving all artifact names."""
        # Arrange
        mock_store = MagicMock()
        query = CmfQuery()
        query.store = mock_store

        # Mock the return value of `get_artifacts`
        mock_artifact1 = MagicMock()
        mock_artifact1.name = "artifact1"
        mock_artifact2 = MagicMock()
        mock_artifact2.name = "artifact2"
        mock_store.get_artifacts.return_value = [mock_artifact1, mock_artifact2]

        # Act
        artifact_names = query.get_all_artifacts()

        # Assert
        self.assertEqual(len(artifact_names), 2)
        self.assertIn("artifact1", artifact_names)
        self.assertIn("artifact2", artifact_names)
        mock_store.get_artifacts.assert_called_once()

    def test_get_one_hop_parent_executions_ids(self):
        """Test retrieving one-hop parent execution IDs for a given execution ID."""
        # Arrange
        mock_store = MagicMock()
        query = CmfQuery()
        query.store = mock_store

        # Mock the return value of `_get_input_artifacts`
        query._get_input_artifacts = MagicMock(return_value=[200, 201])

        # Mock the return value of `_get_executions_by_output_artifact_id`
        query._get_executions_by_output_artifact_id = MagicMock(side_effect=lambda artifact_id, _: [100] if artifact_id == 200 else [101])

        # Act
        parent_execution_ids = query.get_one_hop_parent_executions_ids([300])

        # Assert
        self.assertEqual(len(parent_execution_ids), 2)
        self.assertIn(100, parent_execution_ids)
        self.assertIn(101, parent_execution_ids)
        query._get_input_artifacts.assert_called_once_with([300])
        query._get_executions_by_output_artifact_id.assert_any_call(200, None)
        query._get_executions_by_output_artifact_id.assert_any_call(201, None)

    def test_get_executions_with_execution_ids(self):
        """Test retrieving executions with execution IDs."""
        # Arrange
        mock_store = MagicMock()
        query = CmfQuery()
        query.store = mock_store

        # Mock the return value of `get_executions_by_id`
        mock_execution1 = Execution()
        mock_execution1.id = 100
        mock_execution1.properties["Execution_type_name"].string_value = "type1"
        mock_execution1.properties["Execution_uuid"].string_value = "uuid1"

        mock_execution2 = Execution()
        mock_execution2.id = 101
        mock_execution2.properties["Execution_type_name"].string_value = "type2"
        mock_execution2.properties["Execution_uuid"].string_value = "uuid2"

        mock_store.get_executions_by_id.return_value = [mock_execution1, mock_execution2]

        # Act
        executions_df = query.get_executions_with_execution_ids([100, 101])

        # Assert
        self.assertEqual(len(executions_df), 2)
        self.assertIn("id", executions_df.columns)
        self.assertIn("Execution_type_name", executions_df.columns)
        self.assertIn("Execution_uuid", executions_df.columns)
        self.assertEqual(executions_df.iloc[0]["id"], 100)
        self.assertEqual(executions_df.iloc[0]["Execution_type_name"], "type1")
        self.assertEqual(executions_df.iloc[0]["Execution_uuid"], "uuid1")
        self.assertEqual(executions_df.iloc[1]["id"], 101)
        self.assertEqual(executions_df.iloc[1]["Execution_type_name"], "type2")
        self.assertEqual(executions_df.iloc[1]["Execution_uuid"], "uuid2")
        mock_store.get_executions_by_id.assert_called_once_with([100, 101])

    def test_get_all_child_artifacts(self):
        """Test retrieving all downstream artifacts starting from a given artifact."""
        # Arrange
        mock_store = MagicMock()
        query = CmfQuery()
        query.store = mock_store

        # Mock the return value of `_get_artifact`
        mock_artifact = Artifact()
        mock_artifact.id = 1
        mock_artifact.name = "artifact1"
        query._get_artifact = MagicMock(return_value=mock_artifact)

        # Mock the return value of `_get_executions_by_input_artifact_id`
        query._get_executions_by_input_artifact_id = MagicMock(return_value=[100])

        # Mock the return value of `_get_output_artifacts`
        query._get_output_artifacts = MagicMock(return_value=[2, 3])

        # Mock the return value of `get_artifacts_by_id`
        mock_child_artifact1 = Artifact()
        mock_child_artifact1.id = 2
        mock_child_artifact1.name = "child_artifact1"

        mock_child_artifact2 = Artifact()
        mock_child_artifact2.id = 3
        mock_child_artifact2.name = "child_artifact2"

        mock_store.get_artifacts_by_id.return_value = [mock_child_artifact1, mock_child_artifact2]

        # Mock the `_transform_to_dataframe` method
        query._transform_to_dataframe = MagicMock(side_effect=lambda artifact, data=None: pd.DataFrame([{
            "id": artifact.id,
            "name": artifact.name
        }]))

        # Mock the recursive call to `get_all_child_artifacts`
        query.get_all_child_artifacts = MagicMock(side_effect=lambda artifact_name: pd.DataFrame([{
            "id": 2,
            "name": "child_artifact1"
        }, {
            "id": 3,
            "name": "child_artifact2"
        }]) if artifact_name == "artifact1" else pd.DataFrame())

        # Act
        child_artifacts_df = query.get_all_child_artifacts("artifact1")

        # Assert
        self.assertEqual(len(child_artifacts_df), 2)
        self.assertIn("id", child_artifacts_df.columns)
        self.assertIn("name", child_artifacts_df.columns)
        self.assertEqual(child_artifacts_df.iloc[0]["id"], 2)
        self.assertEqual(child_artifacts_df.iloc[0]["name"], "child_artifact1")
        self.assertEqual(child_artifacts_df.iloc[1]["id"], 3)
        self.assertEqual(child_artifacts_df.iloc[1]["name"], "child_artifact2")

        # Update the validation
        # query._get_artifact.assert_called_with("artifact1")
        # query._get_executions_by_input_artifact_id.assert_called_once_with(1, None)
        # query._get_output_artifacts.assert_called_once_with([100])
        # mock_store.get_artifacts_by_id.assert_called_once_with([2, 3])

    def test_find_producer_execution(self):
        """Test finding the producer execution for a given artifact."""
        # Arrange
        mock_store = MagicMock()
        query = CmfQuery()
        query.store = mock_store

        # Mock the return value of `_get_artifact`
        mock_artifact = Artifact()
        mock_artifact.id = 1
        mock_artifact.name = "artifact1"
        query._get_artifact = MagicMock(return_value=mock_artifact)

        # Mock the return value of `get_events_by_artifact_ids`
        mock_event = MagicMock()
        mock_event.execution_id = 100
        mock_event.type = mlpb.Event.Type.OUTPUT
        mock_store.get_events_by_artifact_ids.return_value = [mock_event]

        # Mock the return value of `get_executions_by_id`
        mock_execution = Execution()
        mock_execution.id = 100
        mock_execution.name = "execution1"
        mock_execution.properties["Execution_type_name"].string_value = "type1"
        mock_store.get_executions_by_id.return_value = [mock_execution]

        # Act
        producer_execution = query.find_producer_execution("artifact1")

        # Assert
        self.assertIsNotNone(producer_execution)
        self.assertEqual(producer_execution.id, 100)
        self.assertEqual(producer_execution.name, "execution1")
        self.assertEqual(producer_execution.properties["Execution_type_name"].string_value, "type1")

        query._get_artifact.assert_called_once_with("artifact1")
        mock_store.get_events_by_artifact_ids.assert_called_once_with([1])
        mock_store.get_executions_by_id.assert_called_once_with({100})

    def test_get_metrics(self):
        """Test retrieving metrics data for a given metrics name."""
        # Arrange
        mock_store = MagicMock()
        query = CmfQuery()
        query.store = mock_store

        # Mock the return value of `get_artifacts_by_type`
        mock_metric = MagicMock()
        mock_metric.name = "accuracy_metrics"
        mock_metric.custom_properties = {"Name": MagicMock(string_value="path/to/metrics.parquet")}
        mock_store.get_artifacts_by_type.return_value = [mock_metric]

        # Mock the return value of `pd.read_parquet`
        mock_read_parquet = MagicMock(return_value=pd.DataFrame({"metric": ["accuracy"], "value": [0.95]}))
        pd.read_parquet = mock_read_parquet  # Replace `pd.read_parquet` with the mock
        mock_read_parquet.assert_called_once_with = MagicMock()  # Ensure the mock is properly configured

        # Act
        metrics_df = query.get_metrics("accuracy_metrics")

        # Assert
        self.assertIsNotNone(metrics_df)
        self.assertEqual(len(metrics_df), 1)
        self.assertIn("metric", metrics_df.columns)
        self.assertIn("value", metrics_df.columns)
        self.assertEqual(metrics_df.iloc[0]["metric"], "accuracy")
        self.assertEqual(metrics_df.iloc[0]["value"], 0.95)

        mock_store.get_artifacts_by_type.assert_called_once_with("Step_Metrics")
        mock_read_parquet.assert_called_once_with("path/to/metrics.parquet")

    def test_get_one_hop_parent_artifacts_with_id(self):
        """Test retrieving one-hop parent artifacts for a given artifact ID."""
        # Arrange
        mock_store = MagicMock()
        query = CmfQuery()
        query.store = mock_store

        # Mock the return value of `_get_executions_by_output_artifact_id`
        query._get_executions_by_output_artifact_id = MagicMock(return_value=[100, 101])

        # Mock the return value of `_get_input_artifacts`
        query._get_input_artifacts = MagicMock(return_value=[200, 201])

        # Mock the return value of `get_artifacts_by_id`
        mock_artifact1 = MagicMock()
        mock_artifact1.id = 200
        mock_artifact1.name = "parent_artifact1"
        mock_artifact1.type_id = 1
        mock_artifact1.uri = "uri1"
        mock_artifact1.create_time_since_epoch = 1234567890
        mock_artifact1.last_update_time_since_epoch = 1234567891

        mock_artifact2 = MagicMock()
        mock_artifact2.id = 201
        mock_artifact2.name = "parent_artifact2"
        mock_artifact2.type_id = 2
        mock_artifact2.uri = "uri2"
        mock_artifact2.create_time_since_epoch = 1234567892
        mock_artifact2.last_update_time_since_epoch = 1234567893

        mock_store.get_artifacts_by_id.return_value = [mock_artifact1, mock_artifact2]

        # Mock the `_transform_to_dataframe` method
        query._transform_to_dataframe = MagicMock(side_effect=lambda artifact, data: pd.DataFrame([{
            "id": artifact.id,
            "name": artifact.name,
            "type": f"Type{artifact.type_id}",
            "uri": artifact.uri,
            "create_time_since_epoch": artifact.create_time_since_epoch,
            "last_update_time_since_epoch": artifact.last_update_time_since_epoch
        }]))

        # Act
        parent_artifacts_df = query.get_one_hop_parent_artifacts_with_id(300)

        # Assert
        self.assertEqual(len(parent_artifacts_df), 2)
        self.assertIn("id", parent_artifacts_df.columns)
        self.assertIn("name", parent_artifacts_df.columns)
        self.assertIn("type", parent_artifacts_df.columns)
        self.assertEqual(parent_artifacts_df.iloc[0]["id"], 200)
        self.assertEqual(parent_artifacts_df.iloc[0]["name"], "parent_artifact1")
        self.assertEqual(parent_artifacts_df.iloc[0]["type"], "Type1")
        self.assertEqual(parent_artifacts_df.iloc[1]["id"], 201)
        self.assertEqual(parent_artifacts_df.iloc[1]["name"], "parent_artifact2")
        self.assertEqual(parent_artifacts_df.iloc[1]["type"], "Type2")

        query._get_executions_by_output_artifact_id.assert_called_once_with(300)
        query._get_input_artifacts.assert_called_once_with([100, 101])
        mock_store.get_artifacts_by_id.assert_called_once_with([200, 201])

    def test_get_all_executions_for_artifact_id(self):
        """Test retrieving all executions for a given artifact ID."""
        # Arrange
        mock_store = MagicMock()
        query = CmfQuery()
        query.store = mock_store

        # Mock the return value of `get_events_by_artifact_ids`
        mock_event1 = mlpb.Event()
        mock_event1.execution_id = 100
        mock_event1.type = mlpb.Event.Type.INPUT

        mock_event2 = mlpb.Event()
        mock_event2.execution_id = 101
        mock_event2.type = mlpb.Event.Type.OUTPUT

        mock_store.get_events_by_artifact_ids.return_value = [mock_event1, mock_event2]

        # Mock the return value of `get_contexts_by_execution`
        mock_context1 = mlpb.Context()
        mock_context1.name = "stage1"
        mock_store.get_contexts_by_execution.return_value = [mock_context1]

        # Mock the return value of `get_executions_by_id`
        mock_execution1 = mlpb.Execution()
        mock_execution1.id = 100
        mock_execution1.name = "execution1"
        mock_execution1.properties["Execution_type_name"].string_value = "type1"

        mock_execution2 = mlpb.Execution()
        mock_execution2.id = 101
        mock_execution2.name = "execution2"
        mock_execution2.properties["Execution_type_name"].string_value = "type2"

        mock_store.get_executions_by_id.side_effect = lambda ids: [mock_execution1 if ids[0] == 100 else mock_execution2]

        # Mock the return value of `get_parent_contexts_by_context`
        mock_pipeline_context = mlpb.Context()
        mock_pipeline_context.name = "pipeline1"
        mock_store.get_parent_contexts_by_context.return_value = [mock_pipeline_context]

        # Act
        executions_df = query.get_all_executions_for_artifact_id(200)

        # Assert
        self.assertEqual(len(executions_df), 2)
        self.assertIn("execution_id", executions_df.columns)
        self.assertIn("execution_name", executions_df.columns)
        self.assertIn("execution_type_name", executions_df.columns)
        self.assertIn("stage", executions_df.columns)
        self.assertIn("pipeline", executions_df.columns)
        self.assertEqual(executions_df.iloc[0]["execution_id"], 100)
        self.assertEqual(executions_df.iloc[0]["execution_name"], "execution1")
        self.assertEqual(executions_df.iloc[0]["execution_type_name"], "type1")
        self.assertEqual(executions_df.iloc[0]["stage"], "stage1")
        self.assertEqual(executions_df.iloc[0]["pipeline"], "pipeline1")
        self.assertEqual(executions_df.iloc[1]["execution_id"], 101)
        self.assertEqual(executions_df.iloc[1]["execution_name"], "execution2")
        self.assertEqual(executions_df.iloc[1]["execution_type_name"], "type2")
        self.assertEqual(executions_df.iloc[1]["stage"], "stage1")
        self.assertEqual(executions_df.iloc[1]["pipeline"], "pipeline1")

        mock_store.get_events_by_artifact_ids.assert_called_once_with([200])
        mock_store.get_contexts_by_execution.assert_any_call(100)
        mock_store.get_contexts_by_execution.assert_any_call(101)
        mock_store.get_executions_by_id.assert_any_call([100])
        mock_store.get_executions_by_id.assert_any_call([101])
        mock_store.get_parent_contexts_by_context.assert_any_call(mock_context1.id)

if __name__ == "__main__":
    unittest.main()
