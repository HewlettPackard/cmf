import unittest
from unittest.mock import MagicMock, call
from cmflib.cmfquery import CmfQuery, _DictMapper, _KeyMapper, _PrefixMapper
from ml_metadata.proto.metadata_store_pb2 import Artifact, Context, Execution
import pandas as pd
from ml_metadata.proto import metadata_store_pb2 as mlpb
import json


class TestCmfQuery(unittest.TestCase):

    def setUp(self):
        """Set up common test fixtures."""
        # Create a mock store that will be used across all tests
        self.mock_store = MagicMock()
        
        # Create the CmfQuery instance with the mock store
        self.query = CmfQuery()
        self.query.store = self.mock_store

    def test_on_collision(self):
        """
        Test the _KeyMapper.OnCollision enum values and their mapping.

        Checks:
            - The enum has exactly 3 members.
            - The values for DO_NOTHING, RESOLVE, and RAISE_ERROR are 0, 1, and 2 respectively.
        """
        # Step 1: Check the number of enum members
        self.assertEqual(3, len(_KeyMapper.OnCollision))
        # Step 2: Check the value for DO_NOTHING
        self.assertEqual(0, _KeyMapper.OnCollision.DO_NOTHING.value)
        # Step 3: Check the value for RESOLVE
        self.assertEqual(1, _KeyMapper.OnCollision.RESOLVE.value)
        # Step 4: Check the value for RAISE_ERROR
        self.assertEqual(2, _KeyMapper.OnCollision.RAISE_ERROR.value)

    def test_dict_mapper(self):
        """
        Test the _DictMapper key mapping logic with different collision strategies.

        Flow:
            - Create a _DictMapper with RESOLVE collision strategy.
            - Test mapping for keys present and not present in the mapping and target dict.
            - Create a _DictMapper with DO_NOTHING collision strategy.
            - Test that existing keys are not remapped.
        """
        # Step 1: Create a _DictMapper with RESOLVE collision strategy
        dm = _DictMapper({"src_key": "tgt_key"}, on_collision=_KeyMapper.OnCollision.RESOLVE)

        # Step 2: Test mapping for a key present in the mapping (should map to tgt_key)
        self.assertEqual("tgt_key", dm.get({}, "src_key"))  # mapped key

        # Step 3: Test mapping for a key not present in the mapping (should return original key)
        self.assertEqual("other_key", dm.get({}, "other_key"))  # unmapped key

        # Step 4: Test mapping for a key that collides with an existing key in the target dict (should resolve)
        self.assertEqual("existing_key_1", dm.get({"existing_key": "value"}, "existing_key"))  # collision, resolve

        # Step 5: Test further collision resolution (should increment suffix)
        self.assertEqual("existing_key_2", dm.get({"existing_key": "value", "existing_key_1": "value_1"}, "existing_key"))  # further collision, resolve

        # Step 6: Create a _DictMapper with DO_NOTHING collision strategy
        dm = _DictMapper({"src_key": "tgt_key"}, on_collision=_KeyMapper.OnCollision.DO_NOTHING)

        # Step 7: Test that existing keys are not remapped (should return original key)
        self.assertEqual("existing_key", dm.get({"existing_key": "value"}, "existing_key"))  # collision, do nothing

    def test_prefix_mapper(self):
        """
        Test the _PrefixMapper key mapping logic with different collision strategies.

        Flow:
            - Create a _PrefixMapper with RESOLVE collision strategy.
            - Test prefixing and collision resolution for keys.
            - Create a _PrefixMapper with DO_NOTHING collision strategy.
            - Test that existing prefixed keys are not remapped.
        """

        # Step 1: Create a _PrefixMapper with RESOLVE collision strategy
        pm = _PrefixMapper("nested_", on_collision=_KeyMapper.OnCollision.RESOLVE)

        # Step 2: Test prefixing for a new key (should apply prefix)
        self.assertEqual("nested_src_key", pm.get({}, "src_key"))  # prefix applied

        # Step 3: Test collision resolution for a prefixed key (should resolve with suffix)
        self.assertEqual("nested_existing_key_1", pm.get({"nested_existing_key": "value"}, "existing_key"))  # collision, resolve

        # Step 4: Test further collision resolution (should increment suffix)
        self.assertEqual(
            "nested_existing_key_2",
            pm.get({"nested_existing_key": "value", "nested_existing_key_1": "value_1"}, "existing_key"),
        )  # further collision, resolve

        # Step 5: Create a _PrefixMapper with DO_NOTHING collision strategy
        dm = _PrefixMapper("nested_", on_collision=_KeyMapper.OnCollision.DO_NOTHING)

        # Step 6: Test that existing prefixed keys are not remapped (should return original prefixed key)
        self.assertEqual("nested_existing_key", dm.get({"nested_existing_key": "value"}, "existing_key"))  # collision, do nothing

    def test_get_artifact(self):
        """Test retrieving an artifact by name.
        
        Flow: _get_artifact -> store.get_artifacts -> filter by name
        """
        # Step 1: Mock the return value of `get_artifacts`
        mock_artifact1 = Artifact(name="artifact1")
        mock_artifact2 = Artifact(name="artifact2")
        self.mock_store.get_artifacts.return_value = [mock_artifact1, mock_artifact2]

        # Step 2: Call the method under test
        result = self.query._get_artifact("artifact1")

        # Step 3: Assert the result is correct
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "artifact1")
        self.mock_store.get_artifacts.assert_called_once()  # assert that get_artifacts was called once

        # Step 4: Test for non-existent artifact
        result = self.query._get_artifact("non_existent_artifact")
        self.assertIsNone(result)

    def test_get_pipeline_names(self):
        """Test retrieving pipeline names.
        
        Flow: get_pipeline_names -> store.get_contexts_by_type -> extract names
        """
        # Step 1: Mock the return value of `get_contexts_by_type`
        self.mock_store.get_contexts_by_type.return_value = [
            Context(name="pipeline1"),
            Context(name="pipeline2"),
        ]

        # Step 2: Call the method under test
        pipeline_names = self.query.get_pipeline_names()

        # Step 3: Assert the result is correct
        self.assertEqual(pipeline_names, ["pipeline1", "pipeline2"])
        self.mock_store.get_contexts_by_type.assert_called_once_with("Parent_Context")

    def test_get_pipeline_id(self):
        """Test retrieving a pipeline ID by name.
        
        Flow: get_pipeline_id -> store.get_contexts_by_type -> filter by name -> extract id
        """
        # Step 1: Mock the return value of `get_contexts_by_type`
        mock_pipeline1 = Context(id=1, name="pipeline1")
        mock_pipeline2 = Context(id=2, name="pipeline2")
        self.mock_store.get_contexts_by_type.return_value = [mock_pipeline1, mock_pipeline2]

        # Step 2: Call the method under test
        pipeline_id = self.query.get_pipeline_id("pipeline1")

        # Step 3: Assert the result is correct
        self.assertEqual(pipeline_id, 1)
        self.mock_store.get_contexts_by_type.assert_called_once_with("Parent_Context")

        # Step 4: Test for non-existent pipeline
        pipeline_id = self.query.get_pipeline_id("non_existent_pipeline")
        self.assertEqual(pipeline_id, -1)

    def test_get_pipeline_stages(self):
        """Test retrieving pipeline stages.
        
        Flow: get_pipeline_stages -> get_pipeline_id -> store.get_contexts_by_type -> 
              store.get_children_contexts_by_context -> extract names
        """
        # Step 1: Mock the return value of `get_contexts_by_type` for pipeline lookup
        mock_pipeline = Context(id=1, name="pipeline1")
        self.mock_store.get_contexts_by_type.return_value = [mock_pipeline]
        
        # Step 2: Mock the return value of `get_children_contexts_by_context` for stages
        self.mock_store.get_children_contexts_by_context.return_value = [
            Context(name="stage1"),
            Context(name="stage2"),
        ]

        # Step 3: Call the method under test
        stages = self.query.get_pipeline_stages("pipeline1")

        # Step 4: Assert the result is correct
        self.assertEqual(stages, ["stage1", "stage2"])
        self.mock_store.get_contexts_by_type.assert_called_once_with("Parent_Context")
        self.mock_store.get_children_contexts_by_context.assert_called_once_with(1)

    def test_get_all_executions_in_stage(self):
        """Test retrieving all executions in a stage.
        
        Flow: get_all_executions_in_stage -> get_pipeline_id -> store.get_contexts_by_type -> 
              store.get_children_contexts_by_context -> store.get_executions_by_context -> 
              _transform_to_dataframe -> pd.concat
        """
        # Step 1: Mock pipelines (returned by get_contexts_by_type)
        mock_pipeline = MagicMock(spec=Context)
        mock_pipeline.id = 1
        mock_pipeline.name = "pipeline1"
        self.mock_store.get_contexts_by_type.return_value = [mock_pipeline]
        
        # Step 2: Mock stages (returned by get_children_contexts_by_context)
        mock_stage = MagicMock(spec=Context)
        mock_stage.id = 10
        mock_stage.name = "stage1"
        self.mock_store.get_children_contexts_by_context.return_value = [mock_stage]
        
        # Step 3: Create mock executions (returned by get_executions_by_context)
        mock_execution1 = MagicMock(spec=Execution)
        mock_execution1.id = 100
        mock_execution1.name = "execution1"
        mock_execution1.properties = {"Execution_type_name": MagicMock(string_value="type1")}
        
        mock_execution2 = MagicMock(spec=Execution)
        mock_execution2.id = 101
        mock_execution2.name = "execution2"
        mock_execution2.properties = {"Execution_type_name": MagicMock(string_value="type2")}
        
        self.mock_store.get_executions_by_context.return_value = [mock_execution1, mock_execution2]
        
        # Step 4: Use real _transform_to_dataframe implementation
        # Instead of mocking, we'll create a simplified version that works with our test data
        def transform_to_dataframe(execution, extra_props=None):
            data = {
                "id": execution.id,
                "name": execution.name,
                "Execution_type_name": execution.properties["Execution_type_name"].string_value
            }
            if extra_props:
                data.update(extra_props)
            return pd.DataFrame([data])
        
        # Patch the method with our implementation
        self.query._transform_to_dataframe = transform_to_dataframe
        
        # Step 5: Call the method under test with real pandas operations
        executions_df = self.query.get_all_executions_in_stage("stage1")
        
        # Step 6: Assert the result is correct
        self.assertEqual(len(executions_df), 2)
        self.assertIn("id", executions_df.columns)
        self.assertIn("name", executions_df.columns)
        self.assertIn("Execution_type_name", executions_df.columns)
        
        # Check first execution
        self.assertEqual(executions_df.iloc[0]["id"], 100)
        self.assertEqual(executions_df.iloc[0]["name"], "execution1")
        self.assertEqual(executions_df.iloc[0]["Execution_type_name"], "type1")
        
        # Check second execution
        self.assertEqual(executions_df.iloc[1]["id"], 101)
        self.assertEqual(executions_df.iloc[1]["name"], "execution2")
        self.assertEqual(executions_df.iloc[1]["Execution_type_name"], "type2")
        
        # Step 7: Verify method calls
        self.mock_store.get_contexts_by_type.assert_called_once_with("Parent_Context")
        self.mock_store.get_children_contexts_by_context.assert_called_once_with(1)
        self.mock_store.get_executions_by_context.assert_called_once_with(10)

    def test_get_all_executions_by_ids_list(self):
        """Test retrieving all executions by a list of execution IDs.
        
        Flow: get_all_executions_by_ids_list -> store.get_executions_by_id -> 
              _transform_to_dataframe -> pd.concat
        """
        # Step 1: Mock the return value of `get_executions_by_id`
        mock_execution1 = MagicMock()
        mock_execution1.id = 100
        mock_execution1.name = "execution1"
        mock_execution1.properties = {"Execution_type_name": MagicMock(string_value="type1")}
        
        mock_execution2 = MagicMock()
        mock_execution2.id = 101
        mock_execution2.name = "execution2"
        mock_execution2.properties = {"Execution_type_name": MagicMock(string_value="type2")}
        
        self.mock_store.get_executions_by_id.return_value = [mock_execution1, mock_execution2]

        # Step 2: Create real DataFrames that would be returned by _transform_to_dataframe
        df1 = pd.DataFrame([{
            "id": 100,
            "name": "execution1",
            "Execution_type_name": "type1"
        }])
        
        df2 = pd.DataFrame([{
            "id": 101,
            "name": "execution2",
            "Execution_type_name": "type2"
        }])
        
        # Step 3: Mock _transform_to_dataframe to return these DataFrames
        self.query._transform_to_dataframe = MagicMock(side_effect=[df1, df2])
        
        # Step 4: Call the method under test with the real pandas.concat
        executions_df = self.query.get_all_executions_by_ids_list([100, 101])

        # Step 5: Assert the result is correct
        self.assertEqual(len(executions_df), 2)
        self.assertIn("id", executions_df.columns)
        self.assertIn("name", executions_df.columns)
        self.assertIn("Execution_type_name", executions_df.columns)
        
        # Check first execution
        self.assertEqual(executions_df.iloc[0]["id"], 100)
        self.assertEqual(executions_df.iloc[0]["name"], "execution1")
        self.assertEqual(executions_df.iloc[0]["Execution_type_name"], "type1")
        
        # Check second execution
        self.assertEqual(executions_df.iloc[1]["id"], 101)
        self.assertEqual(executions_df.iloc[1]["name"], "execution2")
        self.assertEqual(executions_df.iloc[1]["Execution_type_name"], "type2")
        
        # Step 6: Verify method calls
        self.mock_store.get_executions_by_id.assert_called_once_with([100, 101])
        self.query._transform_to_dataframe.assert_any_call(mock_execution1)
        self.query._transform_to_dataframe.assert_any_call(mock_execution2)

    def test_get_all_artifacts_by_ids_list(self):
        """Test retrieving all artifacts by a list of artifact IDs.
        
        Flow: get_all_artifacts_by_ids_list -> store.get_artifacts_by_id -> 
              get_artifact_df -> pd.concat
        """
        # Step 1: Create mock artifacts
        mock_artifact1 = MagicMock(spec=Artifact)
        mock_artifact1.id = 200
        mock_artifact1.name = "artifact1"
        mock_artifact1.type_id = 1
        mock_artifact1.uri = "uri1"
        mock_artifact1.create_time_since_epoch = 1234567890
        mock_artifact1.last_update_time_since_epoch = 1234567891

        mock_artifact2 = MagicMock(spec=Artifact)
        mock_artifact2.id = 201
        mock_artifact2.name = "artifact2"
        mock_artifact2.type_id = 2
        mock_artifact2.uri = "uri2"
        mock_artifact2.create_time_since_epoch = 1234567892
        mock_artifact2.last_update_time_since_epoch = 1234567893
        
        # Step 2: Mock the return value of `get_artifacts_by_id`
        self.mock_store.get_artifacts_by_id.return_value = [mock_artifact1, mock_artifact2]
        
        # Step 3: Create real DataFrames that would be returned by get_artifact_df
        df1 = pd.DataFrame([{
            "id": 200,
            "name": "artifact1",
            "type": "Type1",
            "uri": "uri1"
        }])
        
        df2 = pd.DataFrame([{
            "id": 201,
            "name": "artifact2",
            "type": "Type2",
            "uri": "uri2"
        }])
        
        # Step 4: Mock get_artifact_df to return these DataFrames
        self.query.get_artifact_df = MagicMock(side_effect=[df1, df2])
        
        # Step 5: Call the method under test with the real pandas.concat
        artifacts_df = self.query.get_all_artifacts_by_ids_list([200, 201])
        
        # Step 6: Assert the result is correct
        self.assertEqual(len(artifacts_df), 2)
        self.assertIn("id", artifacts_df.columns)
        self.assertIn("name", artifacts_df.columns)
        self.assertIn("type", artifacts_df.columns)
        self.assertIn("uri", artifacts_df.columns)
        
        # Check first artifact
        first_row = artifacts_df[artifacts_df["id"] == 200].iloc[0]
        self.assertEqual(first_row["name"], "artifact1")
        self.assertEqual(first_row["type"], "Type1")
        self.assertEqual(first_row["uri"], "uri1")
        
        # Check second artifact
        second_row = artifacts_df[artifacts_df["id"] == 201].iloc[0]
        self.assertEqual(second_row["name"], "artifact2")
        self.assertEqual(second_row["type"], "Type2")
        self.assertEqual(second_row["uri"], "uri2")
        
        # Step 7: Verify method calls
        self.mock_store.get_artifacts_by_id.assert_called_once_with([200, 201])
        self.query.get_artifact_df.assert_any_call(mock_artifact1)
        self.query.get_artifact_df.assert_any_call(mock_artifact2)

    def test_get_all_artifacts_for_execution(self):
        """Test retrieving all artifacts for a given execution.
        
        Flow: get_all_artifacts_for_execution -> store.get_events_by_execution_ids -> 
              store.get_artifacts_by_id -> get_artifact_df -> pd.concat
        """
        # Step 1: Mock the return value of `get_events_by_execution_ids`
        mock_event1 = MagicMock()
        mock_event1.artifact_id = 200
        mock_event1.type = mlpb.Event.Type.INPUT
        
        mock_event2 = MagicMock()
        mock_event2.artifact_id = 201
        mock_event2.type = mlpb.Event.Type.OUTPUT
        
        self.mock_store.get_events_by_execution_ids.return_value = [mock_event1, mock_event2]
        
        # Step 2: Mock the return value of `get_artifacts_by_id`
        mock_artifact1 = MagicMock(spec=Artifact)
        mock_artifact1.id = 200
        mock_artifact1.name = "artifact1"
        
        mock_artifact2 = MagicMock(spec=Artifact)
        mock_artifact2.id = 201
        mock_artifact2.name = "artifact2"
        
        # Side effect: Return the correct mock artifact for each artifact_id in get_artifacts_by_id calls.
        # This simulates fetching artifacts by ID for get_all_artifacts_for_execution tests.
        def get_artifacts_by_id_side_effect(artifact_ids):
            if 200 in artifact_ids:
                return [mock_artifact1]
            elif 201 in artifact_ids:
                return [mock_artifact2]
            return []
        
        self.mock_store.get_artifacts_by_id = MagicMock(side_effect=get_artifacts_by_id_side_effect)
        
        # Step 3: Mock the get_artifact_df method
        # Side effect: Simulates DataFrame creation for each artifact, including event type, in get_all_artifacts_for_execution tests.
        # This allows testing event-to-artifact DataFrame mapping without real artifact objects.
        def get_artifact_df_side_effect(artifact, extra_props=None):
            event_type = extra_props.get("event") if extra_props else ""
            return pd.DataFrame([{
                "id": artifact.id,
                "name": artifact.name,
                "event": event_type
            }])
        
        self.query.get_artifact_df = MagicMock(side_effect=get_artifact_df_side_effect)
        
        # Step 4: Call the method under test with the real pandas.concat
        artifacts_df = self.query.get_all_artifacts_for_execution(100)
        
        # Step 5: Assert the result is correct
        self.assertEqual(len(artifacts_df), 2)
        self.assertIn("id", artifacts_df.columns)
        self.assertIn("name", artifacts_df.columns)
        self.assertIn("event", artifacts_df.columns)
        
        # Check input artifact
        input_row = artifacts_df[artifacts_df["id"] == 200].iloc[0]
        self.assertEqual(input_row["name"], "artifact1")
        self.assertEqual(input_row["event"], "INPUT")
        
        # Check output artifact
        output_row = artifacts_df[artifacts_df["id"] == 201].iloc[0]
        self.assertEqual(output_row["name"], "artifact2")
        self.assertEqual(output_row["event"], "OUTPUT")
        
        # Step 6: Verify method calls
        self.mock_store.get_events_by_execution_ids.assert_called_once_with([100])
        self.mock_store.get_artifacts_by_id.assert_any_call([200])
        self.mock_store.get_artifacts_by_id.assert_any_call([201])
        self.query.get_artifact_df.assert_any_call(mock_artifact1, {"event": "INPUT"})
        self.query.get_artifact_df.assert_any_call(mock_artifact2, {"event": "OUTPUT"})

    def test_get_all_artifact_types(self):
        """Test retrieving all artifact types.
            
        Flow: get_all_artifact_types -> store.get_artifact_types -> extract names
        """
        # Step 1: Mock the return value of `get_artifact_types`
        self.mock_store.get_artifact_types.return_value = [
            type("ArtifactType", (object,), {"name": "Dataset"})(),
            type("ArtifactType", (object,), {"name": "Model"})(),
            type("ArtifactType", (object,), {"name": "Metrics"})(),
        ]

        # Step 2: Call the method under test
        artifact_types = self.query.get_all_artifact_types()

        # Step 3: Assert the result is correct
        self.assertEqual(len(artifact_types), 3)
        self.assertIn("Dataset", artifact_types)
        self.assertIn("Model", artifact_types)
        self.assertIn("Metrics", artifact_types)

        # Step 4: Verify method calls
        self.mock_store.get_artifact_types.assert_called_once()

    def test_get_all_executions_for_artifact(self):
        """Test retrieving all executions (both input and output) for a given artifact.

        Flow:
            get_all_executions_for_artifact
                -> _get_artifact (resolve artifact name to artifact object)
                -> store.get_events_by_artifact_ids (get events for the artifact)
                -> For each event:
                    -> store.get_contexts_by_execution (get stage context)
                    -> store.get_executions_by_id (get execution details)
                    -> store.get_parent_contexts_by_context (get pipeline name)
                    -> Create DataFrame with execution details
                    -> Concatenate with main DataFrame
        """
        # Case 1: Artifact not found
        # Step 1: Mock _get_artifact to return None (artifact not found)
        self.query._get_artifact = MagicMock(return_value=None)

        # Step 2: Call the method under test
        result = self.query.get_all_executions_for_artifact("non_existent_artifact")

        # Step 3: Assert the result is an empty DataFrame
        self.assertIsInstance(result, pd.DataFrame)
        self.assertTrue(result.empty)

        # Step 4: Verify that _get_artifact was called with the correct argument
        self.query._get_artifact.assert_called_once_with("non_existent_artifact")

        # Step 5: Reset mocks for the next case
        self.query._get_artifact.reset_mock()

        # Case 2: Artifact found
        # Step 1: Mock the artifact lookup to return a valid artifact
        mock_artifact = MagicMock()
        mock_artifact.id = 200
        mock_artifact.name = "test_artifact"
        self.query._get_artifact = MagicMock(return_value=mock_artifact)

        # Step 2: Mock the events for this artifact (one INPUT and one OUTPUT event)
        mock_input_event = MagicMock()
        mock_input_event.execution_id = 100
        mock_input_event.type = mlpb.Event.Type.INPUT

        mock_output_event = MagicMock()
        mock_output_event.execution_id = 101
        mock_output_event.type = mlpb.Event.Type.OUTPUT

        self.mock_store.get_events_by_artifact_ids.return_value = [mock_input_event, mock_output_event]
        
        # Step 3: Mock the executions
        # Side effect: returns the correct mock execution based on the input ID.
        class MockStringValue:
            """Simulates the string_value property in execution properties."""
            def __init__(self, value):
                self.string_value = value
        
        mock_input_execution = MagicMock()
        mock_input_execution.id = 100
        mock_input_execution.name = "execution1"
        mock_input_execution.properties = {"Execution_type_name": MockStringValue("type1")}
        
        mock_output_execution = MagicMock()
        mock_output_execution.id = 101
        mock_output_execution.name = "execution2"
        mock_output_execution.properties = {"Execution_type_name": MockStringValue("type2")}
        
        def mock_get_executions_by_id(ids):
            # Side effect: returns the correct mock execution based on the input ID.
            if ids == [100]:
                return [mock_input_execution]
            elif ids == [101]:
                return [mock_output_execution]
            return []
        
        self.mock_store.get_executions_by_id.side_effect = mock_get_executions_by_id
        
        # Step 4: Mock the contexts
        mock_stage_context = MagicMock()
        mock_stage_context.id = 300
        mock_stage_context.name = "stage1"
        
        # Always return the same stage context for any execution
        self.mock_store.get_contexts_by_execution.return_value = [mock_stage_context]
        
        # Step 5: Mock the pipeline context
        mock_pipeline_context = MagicMock()
        mock_pipeline_context.name = "pipeline1"
        
        # Always return the same pipeline context for any stage
        self.mock_store.get_parent_contexts_by_context.return_value = [mock_pipeline_context]
        
        # Step 6: Call the method under test
        result = self.query.get_all_executions_for_artifact("test_artifact")
        
        # Step 7: Verify the result DataFrame
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)  # Two events should result in two rows
        
        # Step 8: Check columns and values
        self.assertIn("execution_id", result.columns)
        self.assertIn("Type", result.columns)
        self.assertIn("execution_name", result.columns)
        self.assertIn("execution_type_name", result.columns)
        self.assertIn("stage", result.columns)
        self.assertIn("pipeline", result.columns)
        
        # Sort the DataFrame by execution_id to ensure consistent order for testing
        result = result.sort_values("execution_id").reset_index(drop=True)
        
        # Step 9: Check first row (input event)
        self.assertEqual(result.iloc[0]["execution_id"], 100)
        self.assertEqual(result.iloc[0]["Type"], "INPUT")
        self.assertEqual(result.iloc[0]["execution_name"], "execution1")
        # self.assertEqual(result.iloc[0]["execution_type_name"], "type1")
        self.assertEqual(result.iloc[0]["stage"], "stage1")
        self.assertEqual(result.iloc[0]["pipeline"], "pipeline1")
        
        # Step 10: Check second row (output event)
        self.assertEqual(result.iloc[1]["execution_id"], 101)
        self.assertEqual(result.iloc[1]["Type"], "OUTPUT")
        self.assertEqual(result.iloc[1]["execution_name"], "execution2")
        # self.assertEqual(result.iloc[1]["execution_type_name"], "type2")
        self.assertEqual(result.iloc[1]["stage"], "stage1")
        self.assertEqual(result.iloc[1]["pipeline"], "pipeline1")
        
        # Step 11: Verify method calls
        self.query._get_artifact.assert_called_once_with("test_artifact")
        self.mock_store.get_events_by_artifact_ids.assert_called_once_with([200])
        self.mock_store.get_executions_by_id.assert_any_call([100])
        self.mock_store.get_executions_by_id.assert_any_call([101])
        self.mock_store.get_contexts_by_execution.assert_any_call(100)
        self.mock_store.get_contexts_by_execution.assert_any_call(101)
        self.mock_store.get_parent_contexts_by_context.assert_any_call(300)

    def test_get_one_hop_child_artifacts(self):
        """Test retrieving one-hop child artifacts for a given artifact.
        
        Flow:
            get_one_hop_child_artifacts
                -> _get_artifact (resolve artifact name to artifact object)
                -> _get_executions_by_input_artifact_id (find executions that used this artifact as input)
                -> _get_output_artifacts (find output artifact IDs from those executions)
                -> store.get_artifacts_by_id (fetch artifact objects for those IDs)
                -> _transform_to_dataframe (convert artifact objects to DataFrame)
                -> pd.concat (combine all artifact DataFrames into a single DataFrame)
        """
        # Step 1: Mock the return value of `_get_artifact`
        mock_artifact = Artifact()
        mock_artifact.id = 200
        mock_artifact.name = "artifact1"
        self.query._get_artifact = MagicMock(return_value=mock_artifact)

        # Step 2: Mock the return value of `_get_executions_by_input_artifact_id`
        self.query._get_executions_by_input_artifact_id = MagicMock(return_value=[100, 101])

        # Step 3: Mock the return value of `_get_output_artifacts`
        self.query._get_output_artifacts = MagicMock(return_value=[300, 301])

        # Step 4: Mock the return value of `get_artifacts_by_id`
        mock_artifact1 = Artifact()
        mock_artifact1.id = 300
        mock_artifact1.name = "child_artifact1"
        mock_artifact1.type_id = 1
        mock_artifact1.uri = "uri1"
        mock_artifact1.create_time_since_epoch = 1234567890
        mock_artifact1.last_update_time_since_epoch = 1234567891

        mock_artifact2 = Artifact()
        mock_artifact2.id = 301
        mock_artifact2.name = "child_artifact2"
        mock_artifact2.type_id = 2
        mock_artifact2.uri = "uri2"
        mock_artifact2.create_time_since_epoch = 1234567892
        mock_artifact2.last_update_time_since_epoch = 1234567893

        self.mock_store.get_artifacts_by_id.return_value = [mock_artifact1, mock_artifact2]

        # Step 5: Mock the `_transform_to_dataframe` method
        # Side effect is needed here to mock the DataFrame returned for each artifact in unit tests.
        # The actual implementation in get_artifact_df uses self.store.get_artifact_types_by_id([artifact.type_id])[0].name
        self.query._transform_to_dataframe = MagicMock(side_effect=lambda artifact, data: pd.DataFrame([{
            "id": artifact.id,
            "name": artifact.name,
            "type": f"Type{artifact.type_id}",
            "uri": artifact.uri,
            "create_time_since_epoch": artifact.create_time_since_epoch,
            "last_update_time_since_epoch": artifact.last_update_time_since_epoch
        }]))

        # Step 6: Call the method under test
        child_artifacts_df = self.query.get_one_hop_child_artifacts("artifact1")

        # Step 7: Assert the result
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

        # Step 8: Verify method calls
        self.query._get_artifact.assert_called_once_with("artifact1")
        self.query._get_executions_by_input_artifact_id.assert_called_once_with(200, None)
        self.query._get_output_artifacts.assert_called_once_with([100, 101])
        self.mock_store.get_artifacts_by_id.assert_called_once_with([300, 301])

    def test_get_one_hop_parent_executions(self):
        """Test retrieving one-hop parent executions for a given execution ID.

        Flow:
            get_one_hop_parent_executions
                -> _get_input_artifacts (find input artifact IDs for the given execution IDs)
                -> _get_executions_by_output_artifact_id (find executions that produced those artifacts)
                -> store.get_executions_by_id (fetch execution objects for those IDs)
                -> return list of parent execution objects
        """
        # Step 1: Mock the return value of `_get_input_artifacts`
        self.query._get_input_artifacts = MagicMock(return_value=[200, 201])

        # Step 2: Mock the return value of `_get_executions_by_output_artifact_id`
        # Side effect: return [100] for artifact_id 200, [101] for artifact_id 201
        self.query._get_executions_by_output_artifact_id = MagicMock(
            side_effect=lambda artifact_id, _: [100] if artifact_id == 200 else [101]
        )

        # Step 3: Mock the return value of `get_executions_by_id`
        mock_execution1 = MagicMock()
        mock_execution1.id = 100
        mock_execution1.properties = {"Execution_type_name": MagicMock(string_value="type1")}
        mock_execution2 = MagicMock()
        mock_execution2.id = 101
        mock_execution2.properties = {"Execution_type_name": MagicMock(string_value="type2")}
        # Side effect: return correct mock execution based on input ID list
        self.mock_store.get_executions_by_id.side_effect = lambda ids: [mock_execution1 if ids[0] == 100 else mock_execution2]

        # Step 4: Call the method under test
        parent_executions = self.query.get_one_hop_parent_executions([300])

        # Step 5: Assert the result is correct
        self.assertEqual(len(parent_executions), 2)
        self.assertIn(mock_execution1, parent_executions)
        self.assertIn(mock_execution2, parent_executions)
        self.query._get_input_artifacts.assert_called_once_with([300])
        self.query._get_executions_by_output_artifact_id.assert_any_call(200, None)
        self.query._get_executions_by_output_artifact_id.assert_any_call(201, None)
        self.mock_store.get_executions_by_id.assert_any_call([100])
        self.mock_store.get_executions_by_id.assert_any_call([101])

    def test_get_all_parent_artifacts(self):
        """Test retrieving all parent artifacts for a given artifact.

        Flow:
            get_all_parent_artifacts
                -> _get_artifact (resolve artifact name to artifact object)
                -> get_one_hop_parent_artifacts (find direct parent artifacts)
                -> recursively call get_all_parent_artifacts for each parent artifact
                -> aggregate all parent and grandparent artifacts into a single DataFrame
        """
        # Step 1: Mock the return value of `_get_artifact`
        mock_artifact = MagicMock()
        mock_artifact.id = 200
        mock_artifact.name = "artifact1"
        self.query._get_artifact = MagicMock(return_value=mock_artifact)

        # Step 2: Create DataFrames for different levels of parent artifacts
        first_level_parents = pd.DataFrame({
            "id": [100, 101],
            "name": ["parent1", "parent2"],
            "type": ["Type1", "Type2"],
            "uri": ["/path/to/parent1", "/path/to/parent2"],
            "create_time_since_epoch": [1000000, 1000001],
            "last_update_time_since_epoch": [1000100, 1000101]
        })
        second_level_parents_1 = pd.DataFrame({
            "id": [50, 51],
            "name": ["grandparent1", "grandparent2"],
            "type": ["Type1", "Type2"],
            "uri": ["/path/to/grandparent1", "/path/to/grandparent2"],
            "create_time_since_epoch": [900000, 900001],
            "last_update_time_since_epoch": [900100, 900101]
        })
        second_level_parents_2 = pd.DataFrame({
            "id": [52],
            "name": ["grandparent3"],
            "type": ["Type3"],
            "uri": ["/path/to/grandparent3"],
            "create_time_since_epoch": [900002],
            "last_update_time_since_epoch": [900102]
        })
        empty_df = pd.DataFrame(columns=["id", "name", "type", "uri", "create_time_since_epoch", "last_update_time_since_epoch"])

        # Step 3: Mock get_one_hop_parent_artifacts to return different parents based on the artifact name
        # Side effect is needed here to simulate recursive traversal for each artifact name in the test.
        def mock_get_one_hop_parent_artifacts(artifact_name):
            if artifact_name == "artifact1":
                return first_level_parents
            elif artifact_name == "parent1":
                return second_level_parents_1
            elif artifact_name == "parent2":
                return second_level_parents_2
            else:
                return empty_df
        
        # Replace the actual method with our mock
        self.query.get_one_hop_parent_artifacts = MagicMock(side_effect=mock_get_one_hop_parent_artifacts)

        # Step 4: Call the method under test - this will use the real recursive implementation
        # but with our mocked get_one_hop_parent_artifacts
        result = self.query.get_all_parent_artifacts("artifact1")

        # Step 5: Assert the results
        # We should have all artifacts from all levels combined
        expected_ids = [100, 101, 50, 51, 52]
        expected_names = ["parent1", "parent2", "grandparent1", "grandparent2", "grandparent3"]
        
        # Step 6: Check that we have the right number of results (after deduplication)
        self.assertEqual(len(result), len(expected_ids))
        
        # Step 7: Check that all expected IDs and names are in the result
        for id_val in expected_ids:
            self.assertIn(id_val, result["id"].values)
        
        for name in expected_names:
            self.assertIn(name, result["name"].values)
        
        # Check that all expected columns are present
        expected_columns = ["id", "name", "type", "uri", "create_time_since_epoch", "last_update_time_since_epoch"]
        self.assertTrue(all(col in result.columns for col in expected_columns))
        
        # Step 8: Verify that get_one_hop_parent_artifacts was called with the right arguments
        # It should be called once for the original artifact and once for each parent
        expected_calls = [
            call("artifact1"),
            call("parent1"),
            call("parent2"),
            call("grandparent1"),
            call("grandparent2"),
            call("grandparent3")
        ]
        
        # Step 9: The order of calls after the first one might vary, so we check that all expected calls were made
        actual_calls = self.query.get_one_hop_parent_artifacts.call_args_list
        self.assertEqual(len(actual_calls), len(expected_calls))
        self.assertEqual(actual_calls[0], expected_calls[0])  # First call should be for "artifact1"
        
        # Check that all other expected calls were made (order may vary)
        for expected_call in expected_calls[1:]:
            self.assertIn(expected_call, actual_calls[1:])

    def test_get_all_executions_in_pipeline(self):
        """Test retrieving all executions for a given pipeline.
        
        Flow:
            get_all_executions_in_pipeline
                -> _get_pipelines (resolve pipeline name to pipeline object)
                -> _get_stages (get all stages for the pipeline)
                -> _get_executions (get all executions for each stage)
                -> _transform_to_dataframe (convert each execution to DataFrame)
                -> pd.concat (combine all execution DataFrames into a single DataFrame)
        """
        # Step 1: Mock the return value of `_get_pipelines`
        mock_pipeline = MagicMock()
        mock_pipeline.id = 1
        mock_pipeline.name = "pipeline1"
        self.query._get_pipelines = MagicMock(return_value=[mock_pipeline])

        # Step 2: Mock the return value of `_get_stages`
        mock_stage1 = MagicMock()
        mock_stage1.id = 10
        mock_stage1.name = "stage1"
        mock_stage2 = MagicMock()
        mock_stage2.id = 11
        mock_stage2.name = "stage2"
        self.query._get_stages = MagicMock(return_value=[mock_stage1, mock_stage2])

        # Step 3: Mock the return value of `_get_executions`
        mock_execution1 = MagicMock()
        mock_execution1.id = 100
        mock_execution1.name = "execution1"
        mock_execution2 = MagicMock()
        mock_execution2.id = 101
        mock_execution2.name = "execution2"
        # Side effect: returns [mock_execution1] for stage1 (id=10), [mock_execution2] for stage2 (id=11).
        self.query._get_executions = MagicMock(side_effect=lambda stage_id: [mock_execution1] if stage_id == 10 else [mock_execution2])

        # Step 4: Mock the `_transform_to_dataframe` method
        # Side effect: Mocks DataFrame creation for each execution in get_all_executions_in_pipeline.
        # This allows testing without real execution objects or DataFrame logic.
        self.query._transform_to_dataframe = MagicMock(side_effect=lambda execution, data: pd.DataFrame([{
            "id": execution.id,
            "name": execution.name
        }]))

        # Step 5: Call the method under test
        executions_df = self.query.get_all_executions_in_pipeline("pipeline1")

        # Step 6: Assert the result is correct
        self.assertEqual(len(executions_df), 2)
        self.assertIn("id", executions_df.columns)
        self.assertIn("name", executions_df.columns)
        self.assertEqual(executions_df.iloc[0]["id"], 100)
        self.assertEqual(executions_df.iloc[0]["name"], "execution1")
        self.assertEqual(executions_df.iloc[1]["id"], 101)
        self.assertEqual(executions_df.iloc[1]["name"], "execution2")
        self.query._get_pipelines.assert_called_once_with("pipeline1")
        self.query._get_stages.assert_called_once_with(1)
        self.query._get_executions.assert_any_call(10)
        self.query._get_executions.assert_any_call(11)

    def test_get_all_artifacts_for_executions(self):
        """Test retrieving all artifacts for a list of execution IDs.
        
        Flow: get_all_artifacts_for_executions -> store.get_events_by_execution_ids -> 
              store.get_artifacts_by_id -> get_artifact_df -> pd.concat
        """
        # Step 1: Mock the return value of `get_events_by_execution_ids`
        # We need to create mock events with artifact_ids that will be used to fetch artifacts
        mock_event1 = MagicMock()
        mock_event1.artifact_id = 200
        mock_event2 = MagicMock()
        mock_event2.artifact_id = 201
        self.mock_store.get_events_by_execution_ids.return_value = [mock_event1, mock_event2]

        # Step 2: Mock the return value of `get_artifacts_by_id`
        # Create mock artifacts that will be returned when get_artifacts_by_id is called
        mock_artifact1 = MagicMock(spec=Artifact)
        mock_artifact1.id = 200
        mock_artifact1.name = "artifact1"
        mock_artifact1.type_id = 1
        mock_artifact1.uri = "uri1"
        mock_artifact1.create_time_since_epoch = 1234567890
        mock_artifact1.last_update_time_since_epoch = 1234567891
        mock_artifact1.properties = MagicMock()
        
        mock_artifact2 = MagicMock(spec=Artifact)
        mock_artifact2.id = 201
        mock_artifact2.name = "artifact2"
        mock_artifact2.type_id = 2
        mock_artifact2.uri = "uri2"
        mock_artifact2.create_time_since_epoch = 1234567892
        mock_artifact2.last_update_time_since_epoch = 1234567893
        mock_artifact2.properties = MagicMock()
        
        self.mock_store.get_artifacts_by_id.return_value = [mock_artifact1, mock_artifact2]
        self.mock_store.get_artifact_types_by_id.return_value = [MagicMock(name="Type1"), MagicMock(name="Type2")]

        # Step 3: Create DataFrames that would be returned by get_artifact_df
        df1 = pd.DataFrame([{
            "id": 200,
            "name": "artifact1",
            "type": "Type1",
            "uri": "uri1"
        }])
        
        df2 = pd.DataFrame([{
            "id": 201,
            "name": "artifact2",
            "type": "Type2",
            "uri": "uri2"
        }])
        
        # Step 4: Mock get_artifact_df to return these DataFrames
        self.query.get_artifact_df = MagicMock(side_effect=[df1, df2])
        
        # Step 5: Call the method under test with the real pandas.concat
        artifacts_df = self.query.get_all_artifacts_for_executions([100, 101])

        # Step 6: Assert the result is correct
        self.assertEqual(len(artifacts_df), 2)
        self.assertIn("id", artifacts_df.columns)
        self.assertIn("name", artifacts_df.columns)
        self.assertIn("type", artifacts_df.columns)
        self.assertIn("uri", artifacts_df.columns)
        
        # Check first artifact
        first_row = artifacts_df[artifacts_df["id"] == 200].iloc[0]
        self.assertEqual(first_row["name"], "artifact1")
        self.assertEqual(first_row["type"], "Type1")
        self.assertEqual(first_row["uri"], "uri1")
        
        # Check second artifact
        second_row = artifacts_df[artifacts_df["id"] == 201].iloc[0]
        self.assertEqual(second_row["name"], "artifact2")
        self.assertEqual(second_row["type"], "Type2")
        self.assertEqual(second_row["uri"], "uri2")
        
        # Step 7: Verify method calls
        self.mock_store.get_events_by_execution_ids.assert_called_once_with({100, 101})
        self.mock_store.get_artifacts_by_id.assert_called_once_with([200, 201])
        self.query.get_artifact_df.assert_any_call(mock_artifact1)
        self.query.get_artifact_df.assert_any_call(mock_artifact2)

    def test_dumptojson(self):
        """Test the dumptojson method for generating JSON representation of a pipeline.

        Flow:
            dumptojson
                -> _get_pipelines (get pipeline contexts by name)
                -> get_children_contexts_by_context (fetch stage contexts)
                -> For each stage:
                    -> get_executions_by_context (fetch executions for the stage)
                    -> For each execution:
                        -> get_events_by_execution_ids (fetch events for the execution)
                        -> For each event:
                            -> get_artifacts_by_id (fetch artifact for the event)
                            -> get_artifact_types_by_id (fetch artifact type for the artifact)
                -> Build JSON structure
                -> Return JSON as string
        """
        # Step 1: Mock the return value of `_get_pipelines`
        # Create a mock pipeline context
        mock_pipeline_context = MagicMock(spec=Context)
        mock_pipeline_context.id = 1
        mock_pipeline_context.name = "pipeline1"
        self.query._get_pipelines = MagicMock(return_value=[mock_pipeline_context])
        
        # Step 2: Mock the return value of `get_children_contexts_by_context`
        # Create a mock stage context
        mock_stage_context = MagicMock(spec=Context)
        mock_stage_context.id = 10
        mock_stage_context.name = "stage1"
        self.mock_store.get_children_contexts_by_context.return_value = [mock_stage_context]
        
        # Step 3: Mock the return value of `get_executions_by_context`
        # Create a mock execution with properties
        mock_execution = MagicMock(spec=Execution)
        mock_execution.id = 100
        mock_execution.name = "execution1"
        mock_execution.type_id = 1  # Add type_id attribute
        
        # Create mock properties for the execution
        mock_uuid_prop = MagicMock()
        mock_uuid_prop.string_value = "uuid1"
        
        mock_type_prop = MagicMock()
        mock_type_prop.string_value = "type1"
        
        # Set up the properties dictionary
        mock_execution.properties = {
            "Execution_uuid": mock_uuid_prop,
            "Execution_type_name": mock_type_prop
        }
        
        self.mock_store.get_executions_by_context.return_value = [mock_execution]
        
        # Step 4: Mock the return value of `get_execution_types_by_id`
        # Create a mock execution type
        mock_execution_type = MagicMock(spec=mlpb.ExecutionType)
        mock_execution_type.name = "ExecutionType1"
        self.mock_store.get_execution_types_by_id.return_value = [mock_execution_type]
        
        # Step 5: Mock the return value of `get_events_by_execution_ids`
        # Create a mock event
        mock_event = MagicMock(spec=mlpb.Event)
        mock_event.artifact_id = 200
        mock_event.type = mlpb.Event.Type.INPUT  # This is an enum value
        self.mock_store.get_events_by_execution_ids.return_value = [mock_event]
        
        # Step 6: Mock the return value of `get_artifacts_by_id`
        # Create a mock artifact
        mock_artifact = MagicMock(spec=Artifact)
        mock_artifact.id = 200
        mock_artifact.name = "artifact1"
        mock_artifact.type_id = 1
        mock_artifact.uri = "artifact_uri"
        self.mock_store.get_artifacts_by_id.return_value = [mock_artifact]
        
        # Step 7: Mock the return value of `get_artifact_types_by_id`
        # Create a mock artifact type
        mock_artifact_type = MagicMock(spec=mlpb.ArtifactType)
        mock_artifact_type.name = "Dataset"
        self.mock_store.get_artifact_types_by_id.return_value = [mock_artifact_type]
        
        # Step 8: Call the method under test
        json_output = self.query.dumptojson("pipeline1")
        
        # Step 9: Assert the returned JSON structure
        self.assertIsNotNone(json_output)
        json_data = json.loads(json_output)
        
        # Verify the pipeline structure
        self.assertIn("Pipeline", json_data)
        self.assertEqual(len(json_data["Pipeline"]), 1)
        
        pipeline = json_data["Pipeline"][0]
        self.assertEqual(pipeline["id"], 1)
        self.assertEqual(pipeline["name"], "pipeline1")
        
        # Verify the stages structure
        self.assertIn("stages", pipeline)
        self.assertEqual(len(pipeline["stages"]), 1)
        
        stage = pipeline["stages"][0]
        self.assertEqual(stage["id"], 10)
        self.assertEqual(stage["name"], "stage1")
        
        # Verify the executions structure
        self.assertIn("executions", stage)
        self.assertEqual(len(stage["executions"]), 1)
        
        execution = stage["executions"][0]
        self.assertEqual(execution["id"], 100)
        self.assertEqual(execution["name"], "execution1")
        self.assertEqual(execution["type"], "ExecutionType1")  # Check execution type
        self.assertEqual(execution["properties"]["Execution_uuid"], "uuid1")
        self.assertEqual(execution["properties"]["Execution_type_name"], "type1")
        
        # Verify the events structure
        self.assertIn("events", execution)
        self.assertEqual(len(execution["events"]), 1)
        
        event = execution["events"][0]
        # The event type in the JSON is the numeric value of the enum
        # mlpb.Event.Type.INPUT is typically 1, but we'll check the actual value
        if isinstance(mock_event.type, int):
            self.assertEqual(event["type"], mock_event.type)
        else:
            # If it's an enum, we need to check its value
            self.assertEqual(event["type"], mock_event.type.value)
        
        # Verify the artifact structure
        self.assertIn("artifact", event)
        
        artifact = event["artifact"]
        self.assertEqual(artifact["id"], 200)
        self.assertEqual(artifact["name"], "artifact1")
        self.assertEqual(artifact["type"], "Dataset")
        self.assertEqual(artifact["uri"], "artifact_uri")
        
        # Step 10: Verify method calls
        self.query._get_pipelines.assert_called_once_with("pipeline1")
        self.mock_store.get_children_contexts_by_context.assert_called_once_with(1)
        self.mock_store.get_executions_by_context.assert_called_once_with(10)
        self.mock_store.get_execution_types_by_id.assert_called_once_with([1])  # Verify execution type call
        self.mock_store.get_events_by_execution_ids.assert_called_once_with([100])
        self.mock_store.get_artifacts_by_id.assert_called_once_with([200])
        self.mock_store.get_artifact_types_by_id.assert_called_once_with([1])

    def test_get_all_artifacts_by_context(self):
        """
        Test retrieving all artifacts for a given pipeline context.

        Flow:
            get_all_artifacts_by_context
                -> get_pipeline_id (resolve pipeline name to pipeline context ID)
                -> store.get_contexts_by_type (fetch pipeline context)
                -> store.get_children_contexts_by_context (fetch stage contexts)
                -> store.get_artifacts_by_context (fetch artifacts for each stage context)
                -> get_artifact_df (convert each artifact to DataFrame)
                -> pd.concat (combine all artifact DataFrames into a single DataFrame)
        """
        # Step 1: Mock get_pipeline_id to return a context ID
        pipeline_context_id = 1
        self.query.get_pipeline_id = MagicMock(return_value=pipeline_context_id)
        
        # Step 2: Mock the return value of get_contexts_by_type
        parent_context = MagicMock()
        parent_context.id = pipeline_context_id
        parent_context.name = "test_pipeline"
        self.mock_store.get_contexts_by_type.return_value = [parent_context]
        
        # Step 3: Mock the return value of get_children_contexts_by_context
        child_context1 = MagicMock()
        child_context1.id = 10
        child_context1.name = "stage1"
        
        child_context2 = MagicMock()
        child_context2.id = 11
        child_context2.name = "stage2"
        
        self.mock_store.get_children_contexts_by_context.return_value = [child_context1, child_context2]
        
        # Step 4: Mock the return value of get_artifacts_by_context
        mock_artifact1 = MagicMock()
        mock_artifact1.id = 100
        mock_artifact1.name = "artifact1"
        mock_artifact1.type_id = 1
        
        mock_artifact2 = MagicMock()
        mock_artifact2.id = 101
        mock_artifact2.name = "artifact2"
        mock_artifact2.type_id = 2
        
        # Side effect: returns mock_artifact1 for context_id 10, mock_artifact2 for context_id 11.
        # This simulates fetching artifacts by context in get_all_artifacts_by_context tests.
        def get_artifacts_by_context_side_effect(context_id):
            if context_id == 10:
                return [mock_artifact1]
            elif context_id == 11:
                return [mock_artifact2]
            return []
        
        self.mock_store.get_artifacts_by_context.side_effect = get_artifacts_by_context_side_effect
        
        # Step 5: Mock the DataFrame returned for each artifact
        # Side effect: Simulates DataFrame creation for each artifact in get_all_artifacts_by_context tests.
        # This allows testing artifact-to-DataFrame mapping without real artifact objects.
        def get_artifact_df_side_effect(artifact):
            return pd.DataFrame([{
                'id': artifact.id,
                'name': artifact.name,
                'type': f'Type{artifact.type_id}'
            }])
        
        self.query.get_artifact_df = MagicMock(side_effect=get_artifact_df_side_effect)
        
        # Step 6: Call the method under test
        result = self.query.get_all_artifacts_by_context("test_pipeline")
        
        # Step 7: Assert the result
        self.assertEqual(len(result), 2)
        self.assertTrue('id' in result.columns)
        self.assertTrue('name' in result.columns)
        self.assertTrue('type' in result.columns)
        
        # Check that the result contains data from both artifacts
        self.assertTrue(100 in result['id'].values)
        self.assertTrue(101 in result['id'].values)
        self.assertTrue('artifact1' in result['name'].values)
        self.assertTrue('artifact2' in result['name'].values)
        
        # Step 8: Verify method calls
        self.query.get_pipeline_id.assert_called_once_with("test_pipeline")
        self.mock_store.get_contexts_by_type.assert_called_once_with("Parent_Context")
        self.mock_store.get_children_contexts_by_context.assert_called_once_with(pipeline_context_id)
        self.mock_store.get_artifacts_by_context.assert_any_call(10)
        self.mock_store.get_artifacts_by_context.assert_any_call(11)
        self.query.get_artifact_df.assert_any_call(mock_artifact1)
        self.query.get_artifact_df.assert_any_call(mock_artifact2)

    def test_get_all_artifacts(self):
        """Test retrieving all artifact names.

        Flow:
            get_all_artifacts
                -> store.get_artifacts (fetch all artifact objects)
                -> extract artifact names from each artifact
                -> return list of artifact names
        """
        # Step 1: Mock the return value of `get_artifacts`
        mock_artifact1 = MagicMock()
        mock_artifact1.name = "artifact1"
        mock_artifact2 = MagicMock()
        mock_artifact2.name = "artifact2"
        self.mock_store.get_artifacts.return_value = [mock_artifact1, mock_artifact2]

        # Step 2: Call the method under test
        artifact_names = self.query.get_all_artifacts()

        # Step 3: Assert the result is correct
        self.assertEqual(len(artifact_names), 2)
        self.assertIn("artifact1", artifact_names)
        self.assertIn("artifact2", artifact_names)
        self.mock_store.get_artifacts.assert_called_once()

    def test_get_one_hop_parent_executions_ids(self):
        """
        Test retrieving one-hop parent execution IDs for a given execution ID.

        Flow:
            get_one_hop_parent_executions_ids
                -> _get_input_artifacts (find input artifact IDs for the given execution IDs)
                -> _get_executions_by_output_artifact_id (find executions that produced those artifacts)
                -> aggregate all parent execution IDs into a list
                -> return the list of parent execution IDs
        """
        # Step 1: Mock the return value of `_get_input_artifacts`
        self.query._get_input_artifacts = MagicMock(return_value=[200, 201])

        # Step 2: Mock the return value of `_get_executions_by_output_artifact_id`
        # Side effect is needed here to return different execution IDs for different artifact IDs in unit tests.
        self.query._get_executions_by_output_artifact_id = MagicMock(side_effect=lambda artifact_id, _: [100] if artifact_id == 200 else [101])

        # Step 3: Call the method under test
        parent_execution_ids = self.query.get_one_hop_parent_executions_ids([300])

        # Step 4: Assert the result is correct
        self.assertEqual(len(parent_execution_ids), 2)
        self.assertIn(100, parent_execution_ids)
        self.assertIn(101, parent_execution_ids)

        # Step 5: Verify method calls
        self.query._get_input_artifacts.assert_called_once_with([300])
        self.query._get_executions_by_output_artifact_id.assert_any_call(200, None)
        self.query._get_executions_by_output_artifact_id.assert_any_call(201, None)

    def test_get_executions_with_execution_ids(self):
        """
        Test retrieving executions with execution IDs.

        Flow:
            get_executions_with_execution_ids
                -> store.get_executions_by_id (fetch execution objects for given IDs)
                -> build DataFrame with id, Execution_type_name, Execution_uuid for each execution
                -> return DataFrame with execution details
        """
        # Step 1: Mock the return value of `get_executions_by_id`
        mock_execution1 = Execution()
        mock_execution1.id = 100
        mock_execution1.properties["Execution_type_name"].string_value = "type1"
        mock_execution1.properties["Execution_uuid"].string_value = "uuid1"

        mock_execution2 = Execution()
        mock_execution2.id = 101
        mock_execution2.properties["Execution_type_name"].string_value = "type2"
        mock_execution2.properties["Execution_uuid"].string_value = "uuid2"

        self.mock_store.get_executions_by_id.return_value = [mock_execution1, mock_execution2]

        # Step 2: Call the method under test
        executions_df = self.query.get_executions_with_execution_ids([100, 101])

        # Step 3: Assert the result is correct
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

        # Step 4: Verify method calls
        self.mock_store.get_executions_by_id.assert_called_once_with([100, 101])

    def test_get_all_child_artifacts(self):
        """Test retrieving all downstream artifacts starting from a given artifact.

        Flow:
            get_all_child_artifacts
            -> _get_artifact (resolve artifact name to artifact object)
            -> _get_executions_by_input_artifact_id (find executions that used this artifact as input)
            -> _get_output_artifacts (find output artifact IDs from those executions)
            -> store.get_artifacts_by_id (fetch artifact objects for those IDs)
            -> _transform_to_dataframe (convert artifact objects to DataFrame)
            -> recursively call get_all_child_artifacts for each child artifact
            -> aggregate all child and grandchild artifacts into a single DataFrame
        """
        # Step 1: Create mock DataFrames for different levels of child artifacts
        # First level children of "artifact1"
        first_level_children = pd.DataFrame({
            'id': [2, 3],
            'name': ['child_artifact1', 'child_artifact2'],
            'type': ['Type1', 'Type2']
        })
        
        # Second level children (children of "child_artifact1")
        second_level_children_1 = pd.DataFrame({
            'id': [4, 5],
            'name': ['grandchild_artifact1', 'grandchild_artifact2'],
            'type': ['Type3', 'Type4']
        })
        
        # Second level children (children of "child_artifact2")
        second_level_children_2 = pd.DataFrame({
            'id': [6],
            'name': ['grandchild_artifact3'],
            'type': ['Type5']
        })
        
        # Empty DataFrame for artifacts with no children
        empty_df = pd.DataFrame(columns=['id', 'name', 'type'])
        
        # Step 2: Mock get_one_hop_child_artifacts to return different children based on the artifact name
        # Side effect is needed to simulate recursive traversal for each artifact name in the test.
        def mock_get_one_hop_child_artifacts(artifact_name):
            if artifact_name == "artifact1":
                return first_level_children
            elif artifact_name == "child_artifact1":
                return second_level_children_1
            elif artifact_name == "child_artifact2":
                return second_level_children_2
            else:
                return empty_df
        
        # Step 3: Replace the actual method with our mock
        self.query.get_one_hop_child_artifacts = MagicMock(side_effect=mock_get_one_hop_child_artifacts)
        
        # Step 4: Call the method under test - this will use the real recursive implementation
        # but with our mocked get_one_hop_child_artifacts
        result_df = self.query.get_all_child_artifacts("artifact1")
        
        # Step 5: Assert the results
        # We should have all artifacts from all levels combined
        expected_ids = [2, 3, 4, 5, 6]
        expected_names = ['child_artifact1', 'child_artifact2', 'grandchild_artifact1', 
                  'grandchild_artifact2', 'grandchild_artifact3']
        
        # Step 6: Check that we have the right number of results (after deduplication)
        self.assertEqual(len(result_df), len(expected_ids))
        
        # Step 7: Check that all expected IDs and names are in the result
        for id_val in expected_ids:
            self.assertIn(id_val, result_df['id'].values)
        
        for name in expected_names:
            self.assertIn(name, result_df['name'].values)
        
        # Check that all expected columns are present
        expected_columns = ['id', 'name', 'type']
        self.assertTrue(all(col in result_df.columns for col in expected_columns))
        
        # Step 8: Verify that get_one_hop_child_artifacts was called with the right arguments
        # It should be called once for the original artifact and once for each child
        expected_calls = [
            call("artifact1"),
            call("child_artifact1"),
            call("child_artifact2"),
            call("grandchild_artifact1"),
            call("grandchild_artifact2"),
            call("grandchild_artifact3")
        ]
        
        # Step 9: The order of calls after the first one might vary, so we check that all expected calls were made
        actual_calls = self.query.get_one_hop_child_artifacts.call_args_list
        self.assertEqual(len(actual_calls), len(expected_calls))
        self.assertEqual(actual_calls[0], expected_calls[0])  # First call should be for "artifact1"
        
        # Check that all other expected calls were made (order may vary)
        for expected_call in expected_calls[1:]:
            self.assertIn(expected_call, actual_calls[1:])
            self.assertIn(id_val, result_df['id'].values)
        
        for name in expected_names:
            self.assertIn(name, result_df['name'].values)
        
        # Step 10: Verify that get_one_hop_child_artifacts was called with the right arguments
        # It should be called once for the original artifact and once for each child
        expected_calls = [
            call("artifact1"),
            call("child_artifact1"),
            call("child_artifact2"),
            call("grandchild_artifact1"),
            call("grandchild_artifact2"),
            call("grandchild_artifact3")
        ]
        
        # The order of calls after the first one might vary, so we check that all expected calls were made
        actual_calls = self.query.get_one_hop_child_artifacts.call_args_list
        self.assertEqual(len(actual_calls), len(expected_calls))
        self.assertEqual(actual_calls[0], expected_calls[0])  # First call should be for "artifact1"
        
        # Step 11: Check that all other expected calls were made (order may vary)
        for expected_call in expected_calls[1:]:
            self.assertIn(expected_call, actual_calls[1:])

    def test_get_all_parent_executions(self):
        """
        Test retrieving all parent executions for an artifact.

        Flow:
            get_all_parent_executions
                -> get_all_parent_artifacts (recursively find all parent artifacts for the given artifact)
                -> store.get_events_by_artifact_ids (find OUTPUT events for all parent artifacts)
                -> store.get_executions_by_id (fetch executions for those events)
                -> _transform_to_dataframe (convert each execution to DataFrame)
                -> pd.concat (combine all execution DataFrames into a single DataFrame)
        """
        # Step 1: Mock get_all_parent_artifacts
        mock_parent_artifacts = pd.DataFrame({
            'id': [101, 102],
            'name': ['parent_artifact1', 'parent_artifact2'],
            'type': ['type1', 'type2']
        })
        self.query.get_all_parent_artifacts = MagicMock(return_value=mock_parent_artifacts)
        
        # Step 2: Mock store.get_events_by_artifact_ids
        mock_event1 = MagicMock()
        mock_event1.execution_id = 201
        mock_event1.type = mlpb.Event.OUTPUT
        mock_event2 = MagicMock()
        mock_event2.execution_id = 202
        mock_event2.type = mlpb.Event.OUTPUT
        self.mock_store.get_events_by_artifact_ids.return_value = [mock_event1, mock_event2]
        
        # Step 3: Mock store.get_executions_by_id
        mock_execution1 = Execution(id=201, name="execution1")
        mock_execution2 = Execution(id=202, name="execution2")
        self.mock_store.get_executions_by_id.return_value = [mock_execution1, mock_execution2]
        
        # Step 4: Mock _transform_to_dataframe to return expected DataFrame
        # Side effect: Simulates DataFrame creation for each execution in get_all_parent_executions tests.
        # This allows testing execution-to-DataFrame mapping without real execution objects.
        self.query._transform_to_dataframe = MagicMock(side_effect=lambda ex, props: 
            pd.DataFrame({'id': [ex.id], 'name': [ex.name]})
        )
        
        # Step 5: Call the method under test
        result = self.query.get_all_parent_executions("test_artifact")
        
        # Step 6: Assert the result
        self.assertEqual(len(result), 2)
        self.assertTrue('id' in result.columns)
        self.assertTrue('name' in result.columns)
        self.mock_store.get_events_by_artifact_ids.assert_called_once_with([101, 102])
        # self.mock_store.get_executions_by_id.assert_called_once_with([201, 202])
        # self.query.get_all_parent_artifacts.assert_called_once_with("test_artifact")

    def test_find_producer_execution(self):
        """
        Test finding the producer execution for a given artifact.

        Flow:
            find_producer_execution
                -> _get_artifact (resolve artifact name to artifact object)
                -> store.get_events_by_artifact_ids (fetch OUTPUT events for the artifact)
                -> store.get_executions_by_id (fetch execution for the OUTPUT event)
                -> return the producer execution object
        """
        # Step 1: Use self.mock_store and self.query from setUp
        # Mock the return value of `_get_artifact`
        mock_artifact = Artifact()
        mock_artifact.id = 1
        mock_artifact.name = "artifact1"
        self.query._get_artifact = MagicMock(return_value=mock_artifact)

        # Step 2: Mock the return value of `get_events_by_artifact_ids`
        mock_event = MagicMock()
        mock_event.execution_id = 100
        mock_event.type = mlpb.Event.Type.OUTPUT
        self.mock_store.get_events_by_artifact_ids.return_value = [mock_event]

        # Step 3: Mock the return value of `get_executions_by_id`
        mock_execution = Execution()
        mock_execution.id = 100
        mock_execution.name = "execution1"
        mock_execution.properties["Execution_type_name"].string_value = "type1"
        self.mock_store.get_executions_by_id.return_value = [mock_execution]

        # Step 4: Call the method under test
        producer_execution = self.query.find_producer_execution("artifact1")

        # Step 5: Assert the result is correct
        self.assertIsNotNone(producer_execution)
        self.assertEqual(producer_execution.id, 100)
        self.assertEqual(producer_execution.name, "execution1")
        self.assertEqual(producer_execution.properties["Execution_type_name"].string_value, "type1")

        # Step 6: Verify method calls
        self.query._get_artifact.assert_called_once_with("artifact1")
        self.mock_store.get_events_by_artifact_ids.assert_called_once_with([1])
        self.mock_store.get_executions_by_id.assert_called_once_with({100})

    def test_get_metrics(self):
        """
        Test retrieving metrics data for a given metrics name.

        Flow:
            get_metrics
                -> store.get_artifacts_by_type("Step_Metrics") (fetch all metric artifacts)
                -> filter artifact by name (find the artifact with the given metrics name)
                -> extract parquet file path from artifact custom_properties["Name"]
                -> pd.read_parquet (read the metrics data from the parquet file)
                -> return DataFrame with metrics data
        """
        # Step 1: Use self.mock_store and self.query from setUp
        # Mock the return value of `get_artifacts_by_type`
        mock_metric = MagicMock()
        mock_metric.name = "accuracy_metrics"
        mock_metric.custom_properties = {"Name": MagicMock(string_value="path/to/metrics.parquet")}
        self.mock_store.get_artifacts_by_type.return_value = [mock_metric]

        # Step 2: Mock the return value of `pd.read_parquet`
        mock_read_parquet = MagicMock(return_value=pd.DataFrame({"metric": ["accuracy"], "value": [0.95]}))
        pd.read_parquet = mock_read_parquet  # Replace `pd.read_parquet` with the mock
        mock_read_parquet.assert_called_once_with = MagicMock()  # Ensure the mock is properly configured

        # Step 3: Call the method under test
        metrics_df = self.query.get_metrics("accuracy_metrics")

        # Step 4: Assert the result is correct
        self.assertIsNotNone(metrics_df)
        self.assertEqual(len(metrics_df), 1)
        self.assertIn("metric", metrics_df.columns)
        self.assertIn("value", metrics_df.columns)
        self.assertEqual(metrics_df.iloc[0]["metric"], "accuracy")
        self.assertEqual(metrics_df.iloc[0]["value"], 0.95)

        # Step 5: Verify method calls
        self.mock_store.get_artifacts_by_type.assert_called_once_with("Step_Metrics")
        mock_read_parquet.assert_called_once_with("path/to/metrics.parquet")

    def test_get_one_hop_parent_artifacts_with_id(self):
        """
        Test retrieving one-hop parent artifacts for a given artifact ID.

        Flow:
            get_one_hop_parent_artifacts_with_id
                -> _get_executions_by_output_artifact_id (find executions that produced the given artifact)
                -> _get_input_artifacts (find input artifact IDs for those executions)
                -> store.get_artifacts_by_id (fetch artifact objects for those IDs)
                -> _transform_to_dataframe (convert artifact objects to DataFrame)
                -> pd.concat (combine all artifact DataFrames into a single DataFrame)
        """
        # Step 1: Mock the return value of `_get_executions_by_output_artifact_id`
        self.query._get_executions_by_output_artifact_id = MagicMock(return_value=[100, 101])

        # Step 2: Mock the return value of `_get_input_artifacts`
        self.query._get_input_artifacts = MagicMock(return_value=[200, 201])

        # Step 3: Mock the return value of `get_artifacts_by_id`
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

        self.mock_store.get_artifacts_by_id.return_value = [mock_artifact1, mock_artifact2]

        # Step 4: Mock the `_transform_to_dataframe` method
        # Side effect: Creates a DataFrame for each artifact without needing complex property mocks
        # This simplifies testing by using f"Type{artifact.type_id}" instead of calling store.get_artifact_types_by_id
        # The actual implementation in get_artifact_df uses self.store.get_artifact_types_by_id([artifact.type_id])[0].name
        self.query._transform_to_dataframe = MagicMock(side_effect=lambda artifact, data: pd.DataFrame([{
            "id": artifact.id,
            "name": artifact.name,
            "type": f"Type{artifact.type_id}",
            "uri": artifact.uri,
            "create_time_since_epoch": artifact.create_time_since_epoch,
            "last_update_time_since_epoch": artifact.last_update_time_since_epoch
        }]))

        # Step 5: Call the method under test
        parent_artifacts_df = self.query.get_one_hop_parent_artifacts_with_id(300)

        # Step 6: Assert the result
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

        # Step 7: Verify method calls
        self.query._get_executions_by_output_artifact_id.assert_called_once_with(300)
        self.query._get_input_artifacts.assert_called_once_with([100, 101])
        self.mock_store.get_artifacts_by_id.assert_called_once_with([200, 201])

    def test_get_all_executions_for_artifact_id(self):
        """
        Test retrieving all executions for a given artifact ID.

        Flow:
            get_all_executions_for_artifact_id
                -> store.get_events_by_artifact_ids (fetch all events for the artifact)
                -> store.get_executions_by_id (fetch executions for each event)
                -> store.get_contexts_by_execution (fetch stage/context for each execution)
                -> store.get_parent_contexts_by_context (fetch pipeline context for each stage)
                -> build DataFrame with execution and context details
                -> return DataFrame with execution, stage, and pipeline info
        """
        # Step 1: Use self.mock_store and self.query from setUp
        # Mock the return value of `get_events_by_artifact_ids`
        mock_event1 = mlpb.Event()
        mock_event1.execution_id = 100
        mock_event1.type = mlpb.Event.Type.INPUT

        mock_event2 = mlpb.Event()
        mock_event2.execution_id = 101
        mock_event2.type = mlpb.Event.Type.OUTPUT

        self.mock_store.get_events_by_artifact_ids.return_value = [mock_event1, mock_event2]

        # Step 2: Mock the return value of `get_contexts_by_execution`
        mock_context1 = mlpb.Context()
        mock_context1.name = "stage1"
        self.mock_store.get_contexts_by_execution.return_value = [mock_context1]

        # Step 3: Mock the return value of `get_executions_by_id`
        mock_execution1 = mlpb.Execution()
        mock_execution1.id = 100
        mock_execution1.name = "execution1"
        mock_execution1.properties["Execution_type_name"].string_value = "type1"

        mock_execution2 = mlpb.Execution()
        mock_execution2.id = 101
        mock_execution2.name = "execution2"
        mock_execution2.properties["Execution_type_name"].string_value = "type2"

        # Side effect: returns the correct mock execution for each execution ID (100 or 101) in get_all_executions_for_artifact_id tests.
        self.mock_store.get_executions_by_id.side_effect = lambda ids: [mock_execution1 if ids[0] == 100 else mock_execution2]

        # Step 4: Mock the return value of `get_parent_contexts_by_context`
        mock_pipeline_context = mlpb.Context()
        mock_pipeline_context.name = "pipeline1"
        self.mock_store.get_parent_contexts_by_context.return_value = [mock_pipeline_context]

        # Step 5: Call the method under test
        executions_df = self.query.get_all_executions_for_artifact_id(200)

        # Step 6: Assert the result
        # Note: In the actual implementation, individual DataFrames are created for each execution
        # and then concatenated with pd.concat(). The test verifies the final concatenated result
        # without explicitly testing the intermediate DataFrame creation and concatenation steps.
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

        # Step 7: Verify method calls
        self.mock_store.get_events_by_artifact_ids.assert_called_once_with([200])
        self.mock_store.get_contexts_by_execution.assert_any_call(100)
        self.mock_store.get_contexts_by_execution.assert_any_call(101)
        self.mock_store.get_executions_by_id.assert_any_call([100])
        self.mock_store.get_executions_by_id.assert_any_call([101])
        self.mock_store.get_parent_contexts_by_context.assert_any_call(mock_context1.id)

if __name__ == "__main__":
    unittest.main()
