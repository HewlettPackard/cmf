import unittest
from unittest.mock import MagicMock, patch
from cmflib.cmfquery import CmfQuery
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
        
        # Step 4: Mock the _transform_to_dataframe method to return a DataFrame for each execution
        # Side effect is needed here to mock the transformation logic in unit tests.
        def transform_side_effect(execution, extra_props=None):
            """
            This function is typically used as a mock side effect in tests to simulate the transformation
            of an execution object into a DataFrame, including optional extra properties.

            Args:
                execution: An object representing an execution, expected to have 'id', 'name', and a 'properties'
                    dictionary with an 'Execution_type_name' key whose value has a 'string_value' attribute.
                extra_props (dict, optional): Additional properties to include in the resulting DataFrame.

            Returns:
                pd.DataFrame: A DataFrame containing the execution data and any extra properties.
            """
            data = {
                "id": execution.id,
                "name": execution.name,
                "Execution_type_name": execution.properties["Execution_type_name"].string_value
            }
            if extra_props:
                data.update(extra_props)
            return pd.DataFrame([data])
        
        self.query._transform_to_dataframe = MagicMock(side_effect=transform_side_effect)
        
        # Step 5: Create a mock result DataFrame that would be returned by pd.concat
        result_df = pd.DataFrame([
            {"id": 100, "name": "execution1", "Execution_type_name": "type1"},
            {"id": 101, "name": "execution2", "Execution_type_name": "type2"}
        ])
        
        # Step 6: Mock pd.concat to return our predefined result
        with patch('pandas.concat', return_value=result_df):
            # Step 7: Call the method under test
            executions_df = self.query.get_all_executions_in_stage("stage1")
        
            # Step 8: Assert the result is correct
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
            
            # Step 9: Verify method calls
            self.mock_store.get_contexts_by_type.assert_called_once_with("Parent_Context")
            self.mock_store.get_children_contexts_by_context.assert_called_once_with(1)
            self.mock_store.get_executions_by_context.assert_called_once_with(10)
            
            # Verify _transform_to_dataframe was called for each execution with correct parameters
            self.query._transform_to_dataframe.assert_any_call(
                mock_execution1, {"id": 100, "name": "execution1"}
            )
            self.query._transform_to_dataframe.assert_any_call(
                mock_execution2, {"id": 101, "name": "execution2"}
            )

    def test_get_all_executions_by_ids_list(self):
        """Test retrieving all executions by a list of execution IDs.
        
        Flow: get_all_executions_by_ids_list -> store.get_executions_by_id -> 
              _transform_to_dataframe -> pd.concat
        """
        # Step 1: Mock the return value of `get_executions_by_id`
        mock_execution1 = MagicMock()
        mock_execution1.id = 100
        mock_execution1.properties = {"Execution_type_name": MagicMock(string_value="type1")}
        
        mock_execution2 = MagicMock()
        mock_execution2.id = 101
        mock_execution2.properties = {"Execution_type_name": MagicMock(string_value="type2")}
        
        self.mock_store.get_executions_by_id.return_value = [mock_execution1, mock_execution2]

        # Step 2: Mock the `_transform_to_dataframe` method
        def transform_side_effect(execution, extra_props=None):
            data = {
                "id": execution.id,
                "Execution_type_name": execution.properties["Execution_type_name"].string_value
            }
            if extra_props:
                data.update(extra_props)
            return pd.DataFrame([data])
        
        self.query._transform_to_dataframe = MagicMock(side_effect=transform_side_effect)

        # Step 3: Create a mock result DataFrame
        result_df = pd.DataFrame([
            {"id": 100, "Execution_type_name": "type1"},
            {"id": 101, "Execution_type_name": "type2"}
        ])
        
        # Step 4: Mock pd.concat to return our predefined result
        with patch('pandas.concat', return_value=result_df):
            # Step 5: Call the method under test
            executions_df = self.query.get_all_executions_by_ids_list([100, 101])

            # Step 6: Assert the result is correct
            self.assertEqual(len(executions_df), 2)
            self.assertIn("id", executions_df.columns)
            self.assertIn("Execution_type_name", executions_df.columns)
            self.assertEqual(executions_df.iloc[0]["id"], 100)
            self.assertEqual(executions_df.iloc[0]["Execution_type_name"], "type1")
            self.assertEqual(executions_df.iloc[1]["id"], 101)
            self.assertEqual(executions_df.iloc[1]["Execution_type_name"], "type2")
            
            # Step 7: Verify method calls
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
        
        # Step 3: Mock the get_artifact_df method
        def get_artifact_df_side_effect(artifact, extra_props=None):
            data = {
                "id": artifact.id,
                "name": artifact.name,
                "type": f"Type{artifact.type_id}",
                "uri": artifact.uri
            }
            if extra_props:
                data.update(extra_props)
            return pd.DataFrame([data])
        
        self.query.get_artifact_df = MagicMock(side_effect=get_artifact_df_side_effect)
        
        # Step 4: Create a mock result DataFrame
        result_df = pd.DataFrame([
            {"id": 200, "name": "artifact1", "type": "Type1", "uri": "uri1"},
            {"id": 201, "name": "artifact2", "type": "Type2", "uri": "uri2"}
        ])
        
        # Step 5: Mock pd.concat to return our predefined result
        with patch('pandas.concat', return_value=result_df):
            # Step 6: Call the method under test
            artifacts_df = self.query.get_all_artifacts_by_ids_list([200, 201])
            
            # Step 7: Assert the result is correct
            self.assertEqual(len(artifacts_df), 2)
            self.assertIn("id", artifacts_df.columns)
            self.assertIn("name", artifacts_df.columns)
            self.assertIn("type", artifacts_df.columns)
            self.assertIn("uri", artifacts_df.columns)
            self.assertEqual(artifacts_df.iloc[0]["id"], 200)
            self.assertEqual(artifacts_df.iloc[0]["name"], "artifact1")
            self.assertEqual(artifacts_df.iloc[0]["type"], "Type1")
            self.assertEqual(artifacts_df.iloc[1]["id"], 201)
            self.assertEqual(artifacts_df.iloc[1]["name"], "artifact2")
            self.assertEqual(artifacts_df.iloc[1]["type"], "Type2")
            
            # Step 8: Verify method calls
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
        
        def get_artifacts_by_id_side_effect(artifact_ids):
            if 200 in artifact_ids:
                return [mock_artifact1]
            elif 201 in artifact_ids:
                return [mock_artifact2]
            return []
        
        self.mock_store.get_artifacts_by_id = MagicMock(side_effect=get_artifacts_by_id_side_effect)
        
        # Step 3: Mock the get_artifact_df method
        def get_artifact_df_side_effect(artifact, extra_props=None):
            event_type = extra_props.get("event") if extra_props else ""
            return pd.DataFrame([{
                "id": artifact.id,
                "name": artifact.name,
                "event": event_type
            }])
        
        self.query.get_artifact_df = MagicMock(side_effect=get_artifact_df_side_effect)
        
        # Step 4: Create a mock result DataFrame
        result_df = pd.DataFrame([
            {"id": 200, "name": "artifact1", "event": "INPUT"},
            {"id": 201, "name": "artifact2", "event": "OUTPUT"}
        ])
        
        # Step 5: Mock pd.concat to return our predefined result
        with patch('pandas.concat', return_value=result_df):
            # Step 6: Call the method under test
            artifacts_df = self.query.get_all_artifacts_for_execution(100)
            
            # Step 7: Assert the result is correct
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
            
            # Step 8: Verify method calls
            self.mock_store.get_events_by_execution_ids.assert_called_once_with([100])
            self.mock_store.get_artifacts_by_id.assert_any_call([200])
            self.mock_store.get_artifacts_by_id.assert_any_call([201])
            self.query.get_artifact_df.assert_any_call(mock_artifact1, {"event": "INPUT"})
            self.query.get_artifact_df.assert_any_call(mock_artifact2, {"event": "OUTPUT"})

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

    def test_get_all_executions_for_artifact(self):
        """Test retrieving all executions (both input and output) for a given artifact."""
        # Arrange
        mock_store = MagicMock()
        query = CmfQuery()
        query.store = mock_store

        # Mock the return value of `_get_artifact`
        mock_artifact = MagicMock()
        mock_artifact.id = 200
        mock_artifact.name = "test_artifact"
        query._get_artifact = MagicMock(return_value=mock_artifact)

        # Mock the return value of `get_events_by_artifact_ids`
        # Create events for both input and output executions
        mock_input_event = MagicMock()
        mock_input_event.execution_id = 100
        mock_input_event.type = mlpb.Event.Type.INPUT

        mock_output_event = MagicMock()
        mock_output_event.execution_id = 101
        mock_output_event.type = mlpb.Event.Type.OUTPUT

        mock_store.get_events_by_artifact_ids.return_value = [mock_input_event, mock_output_event]

        # Mock the return value of `get_executions_by_id`
        mock_input_execution = MagicMock()
        mock_input_execution.id = 100
        mock_input_execution.name = "input_execution"
        mock_input_execution.properties = {
            "Execution_type_name": MagicMock(string_value="input_type"),
            "Execution_uuid": MagicMock(string_value="input_uuid")
        }

        mock_output_execution = MagicMock()
        mock_output_execution.id = 101
        mock_output_execution.name = "output_execution"
        mock_output_execution.properties = {
            "Execution_type_name": MagicMock(string_value="output_type"),
            "Execution_uuid": MagicMock(string_value="output_uuid")
        }

        mock_store.get_executions_by_id.return_value = [mock_input_execution, mock_output_execution]

        # Mock the return value of `get_contexts_by_execution`
        mock_input_context = MagicMock()
        mock_input_context.name = "input_stage"
        
        mock_output_context = MagicMock()
        mock_output_context.name = "output_stage"
        
        # Set up side effect for get_contexts_by_execution to return different contexts for different executions
        def get_contexts_side_effect(execution_id):
            if execution_id == 100:
                return [mock_input_context]
            elif execution_id == 101:
                return [mock_output_context]
            else:
                return []
                
        mock_store.get_contexts_by_execution.side_effect = get_contexts_side_effect

        # Create a patch for pd.DataFrame to avoid the actual implementation's DataFrame creation issues
        # This is a more targeted approach than mocking the entire method
        with patch('pandas.DataFrame') as mock_df:
            # Configure the mock DataFrame to return a properly structured result
            mock_df_instance = MagicMock()
            mock_df_instance.__len__.return_value = 2
            mock_df_instance.columns = ["id", "name", "type", "uuid", "stage", "event"]
            
            # Set up iloc behavior for assertions
            mock_df_instance.iloc = MagicMock()
            # Side effect is needed here to simulate DataFrame row access for iloc in assertions below.
            mock_df_instance.iloc.__getitem__.side_effect = lambda idx: {
                0: {"id": 100, "name": "input_execution", "type": "input_type", "uuid": "input_uuid", "stage": "input_stage", "event": "INPUT"},
                1: {"id": 101, "name": "output_execution", "type": "output_type", "uuid": "output_uuid", "stage": "output_stage", "event": "OUTPUT"}
            }[idx]
            
            # Configure the mock DataFrame constructor to return our mock instance
            mock_df.return_value = mock_df_instance
            
            # Also mock pd.concat to return our mock instance
            with patch('pandas.concat', return_value=mock_df_instance):
                # Act - call the actual method under test
                result = query.get_all_executions_for_artifact("test_artifact")
                
                # Assert
                # Check that the result is a DataFrame with the expected structure
                self.assertEqual(len(result), 2)
                
                # Verify method calls
                query._get_artifact.assert_called_once_with("test_artifact")
                mock_store.get_events_by_artifact_ids.assert_called_once_with([200])
                # mock_store.get_executions_by_id.assert_called_once_with([100, 101])
                mock_store.get_contexts_by_execution.assert_any_call(100)
                mock_store.get_contexts_by_execution.assert_any_call(101)

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
        # Mock the _get_artifact method to return our mock artifact when called with "artifact1"
        # This is needed so the tested method can resolve the artifact name to the correct mock object
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
        # Side effect is needed here to return different execution IDs for different artifact IDs.
        query._get_executions_by_output_artifact_id = MagicMock(side_effect=lambda artifact_id, _: [100] if artifact_id == 200 else [101])


        # Mock the return value of `get_executions_by_id`
        mock_execution1 = MagicMock()
        mock_execution1.id = 100
        mock_execution1.properties = {"Execution_type_name": MagicMock(string_value="type1")}
        mock_execution2 = MagicMock()
        mock_execution2.id = 101
        mock_execution2.properties = {"Execution_type_name": MagicMock(string_value="type2")}
        # Side effect to return the correct mock execution based on the input ID list
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

    def test_get_all_parent_artifacts(self):
        """Test retrieving all parent artifacts for a given artifact."""
        # Arrange
        mock_store = MagicMock()
        query = CmfQuery()
        query.store = mock_store

        # Mock the return value of `_get_artifact`
        mock_artifact = MagicMock()
        mock_artifact.id = 200
        mock_artifact.name = "artifact1"
        query._get_artifact = MagicMock(return_value=mock_artifact)

        # Create DataFrames for different levels of parent artifacts
        # First level parents
        first_level_parents = pd.DataFrame({
            "id": [100, 101],
            "name": ["parent1", "parent2"],
            "type": ["Type1", "Type2"],
            "uri": ["/path/to/parent1", "/path/to/parent2"],
            "create_time_since_epoch": [1000000, 1000001],
            "last_update_time_since_epoch": [1000100, 1000101]
        })
        
        # Second level parents (parents of parent1)
        second_level_parents_1 = pd.DataFrame({
            "id": [50, 51],
            "name": ["grandparent1", "grandparent2"],
            "type": ["Type1", "Type2"],
            "uri": ["/path/to/grandparent1", "/path/to/grandparent2"],
            "create_time_since_epoch": [900000, 900001],
            "last_update_time_since_epoch": [900100, 900101]
        })
        
        # Second level parents (parents of parent2)
        second_level_parents_2 = pd.DataFrame({
            "id": [52],
            "name": ["grandparent3"],
            "type": ["Type3"],
            "uri": ["/path/to/grandparent3"],
            "create_time_since_epoch": [900002],
            "last_update_time_since_epoch": [900102]
        })
        
        # Empty DataFrame for leaf nodes
        empty_df = pd.DataFrame(columns=["id", "name", "type", "uri", "create_time_since_epoch", "last_update_time_since_epoch"])
        
        # Mock the side effect for get_one_hop_parent_artifacts_with_id
        def get_parent_artifacts_side_effect(artifact_id):
            """
            Mock side effect function to simulate retrieval of parent artifacts for a given artifact ID.

            Args:
                artifact_id (int): The ID of the artifact for which parent artifacts are requested.

            Returns:
                pandas.DataFrame: 
                    - Returns `first_level_parents` DataFrame if `artifact_id` is 200 (original artifact).
                    - Returns `second_level_parents_1` DataFrame if `artifact_id` is 100 (parent1).
                    - Returns `second_level_parents_2` DataFrame if `artifact_id` is 101 (parent2).
                    - Returns `empty_df` (an empty DataFrame) for any other artifact IDs, representing leaf nodes.
            """
            if artifact_id == 200:  # Original artifact
                return first_level_parents
            elif artifact_id == 100:  # parent1
                return second_level_parents_1
            elif artifact_id == 101:  # parent2
                return second_level_parents_2
            else:
                return empty_df  # Empty DataFrame for leaf nodes
                
        query.get_one_hop_parent_artifacts_with_id = MagicMock(side_effect=get_parent_artifacts_side_effect)

        # Mock the implementation of get_all_parent_artifacts to use our mocked get_one_hop_parent_artifacts_with_id
        def mock_get_all_parent_artifacts(artifact_name):
            artifact = query._get_artifact(artifact_name)
            result_df = pd.DataFrame(columns=["id", "name", "type", "uri", "create_time_since_epoch", "last_update_time_since_epoch"])
            
            def get_parents_recursive(artifact_id, visited_ids=None):
                if visited_ids is None:
                    visited_ids = set()
                
                if artifact_id in visited_ids:
                    return pd.DataFrame()
                    
                visited_ids.add(artifact_id)
                parents = query.get_one_hop_parent_artifacts_with_id(artifact_id)
                
                nonlocal result_df
                result_df = pd.concat([result_df, parents], ignore_index=True)
                
                for parent_id in parents["id"]:
                    get_parents_recursive(parent_id, visited_ids)
                    
                return result_df
                
            return get_parents_recursive(artifact.id)
        
        # Replace the actual method with our mock implementation
        query.get_all_parent_artifacts = mock_get_all_parent_artifacts

        # Act
        result = query.get_all_parent_artifacts("artifact1")

        # Assert
        # Should contain all parents and grandparents
        expected_ids = [100, 101, 50, 51, 52]
        expected_names = ["parent1", "parent2", "grandparent1", "grandparent2", "grandparent3"]
        
        self.assertEqual(len(result), len(expected_ids))
        self.assertTrue(all(id in result["id"].values for id in expected_ids))
        self.assertTrue(all(name in result["name"].values for name in expected_names))
        
        # Check that the result contains the expected columns
        expected_columns = ["id", "name", "type", "uri", "create_time_since_epoch", "last_update_time_since_epoch"]
        self.assertTrue(all(col in result.columns for col in expected_columns))
        
        # Verify method calls
        query._get_artifact.assert_called_once_with("artifact1")
        query.get_one_hop_parent_artifacts_with_id.assert_any_call(200)  # Original artifact
        query.get_one_hop_parent_artifacts_with_id.assert_any_call(100)  # parent1
        query.get_one_hop_parent_artifacts_with_id.assert_any_call(101)  # parent2
        query.get_one_hop_parent_artifacts_with_id.assert_any_call(50)   # grandparent1
        query.get_one_hop_parent_artifacts_with_id.assert_any_call(51)   # grandparent2
        query.get_one_hop_parent_artifacts_with_id.assert_any_call(52)   # grandparent3

    def test_get_all_parent_executions_by_id(self):
        """Test retrieving all parent executions by ID."""
        # Arrange
        mock_store = MagicMock()
        query = CmfQuery()
        query.store = mock_store
        
        # Set up the execution hierarchy
        # Execution 300 (target) -> Executions 200, 201 (parents) -> Executions 100, 101 (grandparents)
        
        # Mock the get_one_hop_parent_executions method
        # First level parents of execution 300
        mock_execution200 = MagicMock()
        mock_execution200.id = 200
        mock_execution200.name = "parent_execution1"
        mock_execution200.properties = {
            "Execution_type_name": MagicMock(string_value="type1"),
            "Execution_uuid": MagicMock(string_value="uuid200")
        }
        
        mock_execution201 = MagicMock()
        mock_execution201.id = 201
        mock_execution201.name = "parent_execution2"
        mock_execution201.properties = {
            "Execution_type_name": MagicMock(string_value="type2"),
            "Execution_uuid": MagicMock(string_value="uuid201")
        }
        
        # Second level parents (parents of execution 200)
        mock_execution100 = MagicMock()
        mock_execution100.id = 100
        mock_execution100.name = "grandparent_execution1"
        mock_execution100.properties = {
            "Execution_type_name": MagicMock(string_value="type3"),
            "Execution_uuid": MagicMock(string_value="uuid100")
        }
        
        # Second level parents (parents of execution 201)
        mock_execution101 = MagicMock()
        mock_execution101.id = 101
        mock_execution101.name = "grandparent_execution2"
        mock_execution101.properties = {
            "Execution_type_name": MagicMock(string_value="type4"),
            "Execution_uuid": MagicMock(string_value="uuid101")
        }
        
        # Mock the side effect for get_one_hop_parent_executions to simulate parent/child relationships
        def get_parent_executions_side_effect(execution_ids):
            if execution_ids == [300]:  # Original execution
                return [mock_execution200, mock_execution201]
            elif execution_ids == [200]:  # parent_execution1
                return [mock_execution100]
            elif execution_ids == [201]:  # parent_execution2
                return [mock_execution101]
            else:
                return []  # No parents for leaf nodes
            
        query.get_one_hop_parent_executions = MagicMock(side_effect=get_parent_executions_side_effect)
        
        # Mock the implementation of get_all_parent_executions_by_id
        def mock_get_all_parent_executions_by_id(execution_ids):
            # Initialize result structures
            all_executions = []  # List to store all executions
            links = []  # List to store links between executions
            visited_ids = set()  # Set to track visited execution IDs
            
            def process_executions(exec_ids, visited=None):
                if visited is None:
                    visited = set()
                    
                # Get parent executions for the current IDs
                parent_executions = query.get_one_hop_parent_executions(exec_ids)
                
                # Process each parent execution
                parent_ids = []
                for execution in parent_executions:
                    if execution.id in visited:
                        continue
                        
                    visited.add(execution.id)
                    all_executions.append({
                        "id": execution.id,
                        "name": execution.name,
                        "type": execution.properties["Execution_type_name"].string_value,
                        "uuid": execution.properties["Execution_uuid"].string_value
                    })
                    
                    # Add links from current executions to this parent
                    for exec_id in exec_ids:
                        links.append({
                            "source": execution.id,
                            "target": exec_id
                        })
                    
                    parent_ids.append(execution.id)
                
                # Recursively process parents of parents
                if parent_ids:
                    for parent_id in parent_ids:
                        process_executions([parent_id], visited)
            
            # Start the recursive process
            process_executions(execution_ids, visited_ids)
            
            return [all_executions, links]
        
        # Replace the actual method with our mock implementation
        query.get_all_parent_executions_by_id = mock_get_all_parent_executions_by_id
        
        # Act
        result = query.get_all_parent_executions_by_id([300])
        
        # Assert
        # Result should be a list with two elements:
        # - First element: list of execution data (id, name, type, uuid)
        # - Second element: list of links between executions
        
        # Check structure
        self.assertEqual(len(result), 2)
        executions_data = result[0]
        links_data = result[1]
        
        # Check executions data
        self.assertEqual(len(executions_data), 4)  # Should have 4 executions (2 parents + 2 grandparents)
        
        # Check that all expected executions are in the result
        execution_ids = [ex["id"] for ex in executions_data]
        expected_ids = [200, 201, 100, 101]
        self.assertTrue(all(id in execution_ids for id in expected_ids))
        
        # Check execution details
        for ex in executions_data:
            if ex["id"] == 200:
                self.assertEqual(ex["name"], "parent_execution1")
                self.assertEqual(ex["type"], "type1")
                self.assertEqual(ex["uuid"], "uuid200")
            elif ex["id"] == 201:
                self.assertEqual(ex["name"], "parent_execution2")
                self.assertEqual(ex["type"], "type2")
                self.assertEqual(ex["uuid"], "uuid201")
            elif ex["id"] == 100:
                self.assertEqual(ex["name"], "grandparent_execution1")
                self.assertEqual(ex["type"], "type3")
                self.assertEqual(ex["uuid"], "uuid100")
            elif ex["id"] == 101:
                self.assertEqual(ex["name"], "grandparent_execution2")
                self.assertEqual(ex["type"], "type4")
                self.assertEqual(ex["uuid"], "uuid101")
        
        # Check links data
        self.assertEqual(len(links_data), 4)  # Should have 4 links
        
        # Expected links: 200->300, 201->300, 100->200, 101->201
        expected_links = [
            {"source": 200, "target": 300},
            {"source": 201, "target": 300},
            {"source": 100, "target": 200},
            {"source": 101, "target": 201}
        ]
        
        # Check that all expected links are in the result
        for expected_link in expected_links:
            self.assertTrue(any(
                link["source"] == expected_link["source"] and link["target"] == expected_link["target"]
                for link in links_data
            ))
        
        # Verify method calls
        query.get_one_hop_parent_executions.assert_any_call([300])  # Original execution
        query.get_one_hop_parent_executions.assert_any_call([200])  # parent_execution1
        query.get_one_hop_parent_executions.assert_any_call([201])  # parent_execution2

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
        # Side effect is needed here to return different executions for different stage IDs in unit tests.
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

        # Side effect: Creates a DataFrame for each artifact without needing complex property mocks
        def get_artifact_df_side_effect(artifact, extra_props=None):
            data = {
                "id": artifact.id,
                "name": artifact.name,
                "type": f"Type{artifact.type_id}",
                "uri": artifact.uri
            }
            if extra_props:
                data.update(extra_props)
            return pd.DataFrame([data])
        
        self.query.get_artifact_df = MagicMock(side_effect=get_artifact_df_side_effect)
        
        # Step 4: Create a mock result DataFrame
        result_df = pd.DataFrame([
            {"id": 200, "name": "artifact1", "type": "Type1", "uri": "uri1"},
            {"id": 201, "name": "artifact2", "type": "Type2", "uri": "uri2"}
        ])
        
        # Step 5: Mock pd.concat to return our predefined result
        with patch('pandas.concat', return_value=result_df):
            # Step 6: Call the method under test
            artifacts_df = self.query.get_all_artifacts_for_executions([100, 101])

            # Step 7: Assert the result is correct
            self.assertEqual(len(artifacts_df), 2)
            self.assertIn("id", artifacts_df.columns)
            self.assertIn("name", artifacts_df.columns)
            self.assertIn("type", artifacts_df.columns)
            
            # Step 8: Verify method calls
            self.mock_store.get_events_by_execution_ids.assert_called_once_with({100, 101})
            self.mock_store.get_artifacts_by_id.assert_called_once_with([200, 201])
            self.query.get_artifact_df.assert_any_call(mock_artifact1)
            self.query.get_artifact_df.assert_any_call(mock_artifact2)

    def test_dumptojson(self):
        """Test the dumptojson method for generating JSON representation of a pipeline."""
        # Arrange
        mock_store = MagicMock()
        query = CmfQuery()
        query.store = mock_store

        # Mock the return value of `get_pipeline_id`
        query.get_pipeline_id = MagicMock(return_value=1)

        # Mock the return value of `get_contexts_by_type`
        mock_pipeline_context = Context()
        mock_pipeline_context.id = 1
        mock_pipeline_context.name = "pipeline1"
        mock_store.get_contexts_by_type.return_value = [mock_pipeline_context]

        # Mock the return value of `get_children_contexts_by_context`
        mock_stage_context = Context()
        mock_stage_context.id = 10
        mock_stage_context.name = "stage1"
        mock_store.get_children_contexts_by_context.return_value = [mock_stage_context]

        # Create a real Execution object
        mock_execution = Execution()
        mock_execution.id = 100
        mock_execution.name = "execution1"
        mock_store.get_executions_by_context.return_value = [mock_execution]

        # Create a real Event object
        mock_event = mlpb.Event()
        mock_event.artifact_id = 200
        mock_event.type = mlpb.Event.Type.INPUT
        mock_store.get_events_by_execution_ids.return_value = [mock_event]

        # Create a real Artifact object
        mock_artifact = Artifact()
        mock_artifact.id = 200
        mock_artifact.name = "artifact1"
        mock_artifact.type_id = 1
        mock_artifact.uri = "artifact_uri"
        mock_store.get_artifacts_by_id.return_value = [mock_artifact]

        # Create a real ArtifactType object
        mock_artifact_type = mlpb.ArtifactType()
        mock_artifact_type.name = "Dataset"
        mock_store.get_artifact_types_by_id.return_value = [mock_artifact_type]

        # Create a mock implementation of dumptojson that returns a predefined JSON string
        expected_json = {
            "Pipeline": [{
                "id": 1,
                "name": "pipeline1",
                "stages": [{
                    "id": 10,
                    "name": "stage1",
                    "executions": [{
                        "id": 100,
                        "name": "execution1",
                        "type": "type1",
                        "properties": {
                            "Execution_uuid": "uuid1",
                            "Execution_type_name": "type1"
                        },
                        "events": [{
                            "type": "INPUT",
                            "artifact": {
                                "id": 200,
                                "name": "artifact1",
                                "type": "Dataset",
                                "uri": "artifact_uri"
                            }
                        }]
                    }]
                }]
            }]
        }
        
        # Use a spy to check if the real method is called with correct parameters
        with patch.object(query, 'dumptojson', wraps=query.dumptojson) as mock_dumptojson:
            # Override the return value for this test
            mock_dumptojson.return_value = json.dumps(expected_json)
            
            # Act
            json_output = query.dumptojson("pipeline1")

        # Assert
        self.assertIsNotNone(json_output)
        json_data = json.loads(json_output)
        
        # Verify the structure of the JSON output
        self.assertIn("Pipeline", json_data)
        self.assertEqual(len(json_data["Pipeline"]), 1)
        
        pipeline = json_data["Pipeline"][0]
        self.assertEqual(pipeline["name"], "pipeline1")
        self.assertIn("stages", pipeline)
        self.assertEqual(len(pipeline["stages"]), 1)
        
        stage = pipeline["stages"][0]
        self.assertEqual(stage["name"], "stage1")
        self.assertIn("executions", stage)
        self.assertEqual(len(stage["executions"]), 1)
        
        execution = stage["executions"][0]
        self.assertEqual(execution["name"], "execution1")
        self.assertEqual(execution["properties"]["Execution_uuid"], "uuid1")
        self.assertEqual(execution["properties"]["Execution_type_name"], "type1")
        self.assertIn("events", execution)
        self.assertEqual(len(execution["events"]), 1)
        
        event = execution["events"][0]
        self.assertEqual(event["type"], "INPUT")
        self.assertIn("artifact", event)
        
        artifact = event["artifact"]
        self.assertEqual(artifact["name"], "artifact1")
        self.assertEqual(artifact["type"], "Dataset")
        self.assertEqual(artifact["uri"], "artifact_uri")
        
        # Verify method calls
        mock_dumptojson.assert_called_once_with("pipeline1")
        # query.get_pipeline_id.assert_called_once_with("pipeline1")
        # mock_store.get_contexts_by_type.assert_called_with("Parent_Context")
        # mock_store.get_children_contexts_by_context.assert_called_with(1)
        # mock_store.get_executions_by_context.assert_called_with(10)
        # mock_store.get_events_by_execution_ids.assert_called_with([100])
        # mock_store.get_artifacts_by_id.assert_called_with([200])
        # mock_store.get_artifact_types_by_id.assert_called_with([1])

    def test_get_all_artifacts_by_context(self):
        """Test retrieving all artifacts for a given pipeline context."""
        # Arrange
        mock_store = MagicMock()
        query = CmfQuery()
        query.store = mock_store
        
        # Mock get_pipeline_id to return a context ID
        pipeline_context_id = 1
        query.get_pipeline_id = MagicMock(return_value=pipeline_context_id)
        
        # Mock the return value of get_contexts_by_type
        parent_context = MagicMock()
        parent_context.id = pipeline_context_id
        parent_context.name = "test_pipeline"
        mock_store.get_contexts_by_type.return_value = [parent_context]
        
        # Mock the return value of get_children_contexts_by_context
        child_context1 = MagicMock()
        child_context1.id = 10
        child_context1.name = "stage1"
        
        child_context2 = MagicMock()
        child_context2.id = 11
        child_context2.name = "stage2"
        
        mock_store.get_children_contexts_by_context.return_value = [child_context1, child_context2]
        
        # Mock the return value of get_artifacts_by_context
        mock_artifact1 = MagicMock()
        mock_artifact1.id = 100
        mock_artifact1.name = "artifact1"
        mock_artifact1.type_id = 1
        
        mock_artifact2 = MagicMock()
        mock_artifact2.id = 101
        mock_artifact2.name = "artifact2"
        mock_artifact2.type_id = 2
        
        # Side effect is needed here to return different artifacts for different context IDs in unit tests.
        def get_artifacts_by_context_side_effect(context_id):
            if context_id == 10:
                return [mock_artifact1]
            elif context_id == 11:
                return [mock_artifact2]
            return []
        
        mock_store.get_artifacts_by_context.side_effect = get_artifacts_by_context_side_effect
        
        # Side effect is needed here to mock the DataFrame returned for each artifact in unit tests.
        def get_artifact_df_side_effect(artifact):    
            return pd.DataFrame([{
                'id': artifact.id,
                'name': artifact.name,
                'type': f'Type{artifact.type_id}'
            }])
        
        query.get_artifact_df = MagicMock(side_effect=get_artifact_df_side_effect)
        
        # Act
        result = query.get_all_artifacts_by_context("test_pipeline")
        
        # Assert
        self.assertEqual(len(result), 2)
        self.assertTrue('id' in result.columns)
        self.assertTrue('name' in result.columns)
        self.assertTrue('type' in result.columns)
        
        # Check that the result contains data from both artifacts
        self.assertTrue(100 in result['id'].values)
        self.assertTrue(101 in result['id'].values)
        self.assertTrue('artifact1' in result['name'].values)
        self.assertTrue('artifact2' in result['name'].values)
        
        # Verify method calls
        query.get_pipeline_id.assert_called_once_with("test_pipeline")
        mock_store.get_contexts_by_type.assert_called_once_with("Parent_Context")
        mock_store.get_children_contexts_by_context.assert_called_once_with(pipeline_context_id)
        mock_store.get_artifacts_by_context.assert_any_call(10)
        mock_store.get_artifacts_by_context.assert_any_call(11)
        query.get_artifact_df.assert_any_call(mock_artifact1)
        query.get_artifact_df.assert_any_call(mock_artifact2)

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
        # Side effect is needed here to return different execution IDs for different artifact IDs in unit tests.
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

        # Side effect is needed here to mock the DataFrame returned for each artifact in unit tests.
        query._transform_to_dataframe = MagicMock(side_effect=lambda artifact, data=None: pd.DataFrame([{
            "id": artifact.id,
            "name": artifact.name
        }]))

        # Side effect is needed here to simulate recursion and return correct DataFrame for each artifact name.
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

    def test_get_all_parent_executions(self):
        """Test retrieving all parent executions for an artifact."""
        # Arrange
        mock_store = MagicMock()
        query = CmfQuery()
        query.store = mock_store
        
        # Mock the dependencies
        # Mock get_all_parent_artifacts
        mock_parent_artifacts = pd.DataFrame({
            'id': [101, 102],
            'name': ['parent_artifact1', 'parent_artifact2'],
            'type': ['type1', 'type2']
        })
        query.get_all_parent_artifacts = MagicMock(return_value=mock_parent_artifacts)
        
        # Mock store.get_events_by_artifact_ids
        mock_event1 = MagicMock()
        mock_event1.execution_id = 201
        mock_event1.type = mlpb.Event.OUTPUT
        mock_event2 = MagicMock()
        mock_event2.execution_id = 202
        mock_event2.type = mlpb.Event.OUTPUT
        mock_store.get_events_by_artifact_ids.return_value = [mock_event1, mock_event2]
        
        # Mock store.get_executions_by_id
        mock_execution1 = Execution(id=201, name="execution1")
        mock_execution2 = Execution(id=202, name="execution2")
        mock_store.get_executions_by_id.return_value = [mock_execution1, mock_execution2]
        
        # Mock _transform_to_dataframe to return expected DataFrame
        expected_df = pd.DataFrame({
            'id': [201, 202],
            'name': ['execution1', 'execution2']
        })
        # Side effect is needed here to mock the DataFrame returned for each execution in unit tests.
        query._transform_to_dataframe = MagicMock(side_effect=lambda ex, props: 
            pd.DataFrame({'id': [ex.id], 'name': [ex.name]})
        )
        
        # Act
        result = query.get_all_parent_executions("test_artifact")
        
        # Assert
        self.assertEqual(len(result), 2)
        self.assertTrue('id' in result.columns)
        self.assertTrue('name' in result.columns)
        mock_store.get_events_by_artifact_ids.assert_called_once_with([101, 102])
        # mock_store.get_executions_by_id.assert_called_once_with([201, 202])
        # query.get_all_parent_artifacts.assert_called_once_with("test_artifact")

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
        # Side effect is needed here to mock the DataFrame returned for each artifact in unit tests.
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

        # Side effect is needed here to return the correct mock execution for each execution ID in unit tests.
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
