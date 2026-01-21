import pytest
import pandas as pd
import json
from ml_metadata.proto.metadata_store_pb2 import Artifact, Context, Execution
from ml_metadata.proto import metadata_store_pb2 as mlpb
from cmflib.cmfquery import CmfQuery, _DictMapper, _KeyMapper, _PrefixMapper


@pytest.fixture
def query_fixture(mocker):
    """Create a CmfQuery instance with a mock store."""
    mock_store = mocker.Mock()
    query = CmfQuery()
    query.store = mock_store
    return query, mock_store


def test_on_collision(query_fixture):
    """
    Test the _KeyMapper.OnCollision enum values and their mapping.

    Checks:
        - The enum has exactly 3 members.
        - The values for DO_NOTHING, RESOLVE, and RAISE_ERROR are 0, 1, and 2 respectively.
    """
    # Step 1: Check the number of enum members
    assert 3 == len(_KeyMapper.OnCollision)
    
    # Step 2: Check the value for DO_NOTHING
    assert 0 == _KeyMapper.OnCollision.DO_NOTHING.value
    
    # Step 3: Check the value for RESOLVE
    assert 1 == _KeyMapper.OnCollision.RESOLVE.value
    
    # Step 4: Check the value for RAISE_ERROR
    assert 2 == _KeyMapper.OnCollision.RAISE_ERROR.value


def test_dict_mapper(query_fixture):
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
    assert "tgt_key" == dm.get({}, "src_key")  # mapped key

    # Step 3: Test mapping for a key not present in the mapping (should return original key)
    assert "other_key" == dm.get({}, "other_key")  # unmapped key

    # Step 4: Test mapping for a key that collides with an existing key in the target dict (should resolve)
    assert "existing_key_1" == dm.get({"existing_key": "value"}, "existing_key")  # collision, resolve

    # Step 5: Test further collision resolution (should increment suffix)
    assert "existing_key_2" == dm.get({"existing_key": "value", "existing_key_1": "value_1"}, "existing_key")  # further collision, resolve

    # Step 6: Create a _DictMapper with DO_NOTHING collision strategy
    dm = _DictMapper({"src_key": "tgt_key"}, on_collision=_KeyMapper.OnCollision.DO_NOTHING)

    # Step 7: Test that existing keys are not remapped (should return original key)
    assert "existing_key" == dm.get({"existing_key": "value"}, "existing_key")  # collision, do nothing


def test_prefix_mapper(query_fixture):
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
    assert "nested_src_key" == pm.get({}, "src_key")  # prefix applied

    # Step 3: Test collision resolution for a prefixed key (should resolve with suffix)
    assert "nested_existing_key_1" == pm.get({"nested_existing_key": "value"}, "existing_key")  # collision, resolve

    # Step 4: Test further collision resolution (should increment suffix)
    assert "nested_existing_key_2" == pm.get(
        {"nested_existing_key": "value", "nested_existing_key_1": "value_1"}, 
        "existing_key"
    )  # further collision, resolve

    # Step 5: Create a _PrefixMapper with DO_NOTHING collision strategy
    dm = _PrefixMapper("nested_", on_collision=_KeyMapper.OnCollision.DO_NOTHING)

    # Step 6: Test that existing prefixed keys are not remapped (should return original prefixed key)
    assert "nested_existing_key" == dm.get({"nested_existing_key": "value"}, "existing_key")  # collision, do nothing


def test_get_artifact(query_fixture, mocker):
    """Test retrieving an artifact by name.
    
    Flow: _get_artifact -> store.get_artifacts -> filter by name
    """
    query, mock_store = query_fixture
    
    # Step 1: Mock the return value of `get_artifacts`
    mock_artifact1 = mocker.Mock(spec=Artifact)
    mock_artifact1.name = "artifact1"
    
    mock_artifact2 = mocker.Mock(spec=Artifact)
    mock_artifact2.name = "artifact2"
    
    mock_store.get_artifacts.return_value = [mock_artifact1, mock_artifact2]
    
    # Step 2: Call the method under test
    result = query._get_artifact("artifact1")
    
    # Step 3: Assert the result is correct
    assert result is not None
    assert result.name == "artifact1"
    
    # Step 4: Verify method calls
    mock_store.get_artifacts.assert_called_once()
    
    # Step 5: Test case where artifact is not found
    result = query._get_artifact("non_existent_artifact")
    
    # Step 6: Assert the result is None
    assert result is None
    
    # Step 7: Verify method calls (should be called twice now)
    assert mock_store.get_artifacts.call_count == 2


def test_get_pipeline_names(query_fixture, mocker):
    """Test retrieving pipeline names.
    
    Flow: get_pipeline_names -> store.get_contexts_by_type -> extract names
    """
    query, mock_store = query_fixture
    
    # Step 1: Mock the return value of `get_contexts_by_type`
    mock_pipeline1 = mocker.Mock(spec=Context)
    mock_pipeline1.name = "pipeline1"
    
    mock_pipeline2 = mocker.Mock(spec=Context)
    mock_pipeline2.name = "pipeline2"
    
    mock_store.get_contexts_by_type.return_value = [mock_pipeline1, mock_pipeline2]
    
    # Step 2: Call the method under test
    pipeline_names = query.get_pipeline_names()
    
    # Step 3: Assert the result is correct
    assert pipeline_names == ["pipeline1", "pipeline2"]
    
    # Step 4: Verify method calls
    mock_store.get_contexts_by_type.assert_called_once_with("Parent_Context")


def test_get_pipeline_id(query_fixture, mocker):
    """Test retrieving a pipeline ID by name.
    
    Flow: get_pipeline_id -> store.get_contexts_by_type -> filter by name -> extract id
    """
    query, mock_store = query_fixture
    
    # Step 1: Mock the return value of `get_contexts_by_type`
    mock_pipeline1 = mocker.Mock(spec=Context)
    mock_pipeline1.id = 1
    mock_pipeline1.name = "pipeline1"
    
    mock_pipeline2 = mocker.Mock(spec=Context)
    mock_pipeline2.id = 2
    mock_pipeline2.name = "pipeline2"
    
    mock_store.get_contexts_by_type.return_value = [mock_pipeline1, mock_pipeline2]
    
    # Step 2: Call the method under test
    pipeline_id = query.get_pipeline_id("pipeline1")
    
    # Step 3: Assert the result is correct
    assert pipeline_id == 1
    
    # Step 4: Verify method calls
    mock_store.get_contexts_by_type.assert_called_once_with("Parent_Context")
    
    # Step 5: Test for non-existent pipeline
    pipeline_id = query.get_pipeline_id("non_existent_pipeline")
    
    # Step 6: Assert the result is -1 for non-existent pipeline
    assert pipeline_id == -1
    
    # Step 7: Verify method calls (should be called twice now)
    assert mock_store.get_contexts_by_type.call_count == 2


def test_get_pipeline_stages(query_fixture, mocker):
    """Test retrieving pipeline stages.
    
    Flow: get_pipeline_stages -> get_pipeline_id -> store.get_contexts_by_type -> 
          store.get_children_contexts_by_context -> extract names
    """
    query, mock_store = query_fixture
    
    # Step 1: Mock the return value of `get_contexts_by_type` for pipeline lookup
    mock_pipeline = mocker.Mock(spec=Context)
    mock_pipeline.id = 1
    mock_pipeline.name = "pipeline1"
    mock_store.get_contexts_by_type.return_value = [mock_pipeline]
    
    # Step 2: Mock the return value of `get_children_contexts_by_context` for stages
    mock_stage1 = mocker.Mock(spec=Context)
    mock_stage1.name = "stage1"
    
    mock_stage2 = mocker.Mock(spec=Context)
    mock_stage2.name = "stage2"
    
    mock_store.get_children_contexts_by_context.return_value = [mock_stage1, mock_stage2]
    
    # Step 3: Call the method under test
    stages = query.get_pipeline_stages("pipeline1")
    
    # Step 4: Assert the result is correct
    assert stages == ["stage1", "stage2"]
    
    # Step 5: Verify method calls
    mock_store.get_contexts_by_type.assert_called_once_with("Parent_Context")
    mock_store.get_children_contexts_by_context.assert_called_once_with(1)
    
    # Step 6: Test for non-existent pipeline
    mock_store.get_contexts_by_type.return_value = []
    stages = query.get_pipeline_stages("non_existent_pipeline")
    
    # Step 7: Assert the result is an empty list for non-existent pipeline
    assert stages == []
    
    # Step 8: Verify method calls (get_contexts_by_type should be called again)
    assert mock_store.get_contexts_by_type.call_count == 2
    # get_children_contexts_by_context should not be called again
    assert mock_store.get_children_contexts_by_context.call_count == 1


def test_get_all_executions_in_stage(query_fixture, mocker):
    """Test retrieving all executions in a stage.
    
    Flow: get_all_executions_in_stage -> get_pipeline_id -> store.get_contexts_by_type -> 
          store.get_children_contexts_by_context -> store.get_executions_by_context -> 
          _transform_to_dataframe -> pd.concat
    """
    query, mock_store = query_fixture
    
    # Step 1: Mock pipelines (returned by get_contexts_by_type)
    mock_pipeline = mocker.Mock(spec=Context)
    mock_pipeline.id = 1
    mock_pipeline.name = "pipeline1"
    mock_store.get_contexts_by_type.return_value = [mock_pipeline]
    
    # Step 2: Mock stages (returned by get_children_contexts_by_context)
    mock_stage = mocker.Mock(spec=Context)
    mock_stage.id = 10
    mock_stage.name = "stage1"
    mock_store.get_children_contexts_by_context.return_value = [mock_stage]
    
    # Step 3: Mock executions (returned by get_executions_by_context)
    mock_execution1 = mocker.Mock()
    mock_execution1.id = 100
    mock_execution1.name = "execution1"
    mock_execution1.properties = {"Execution_type_name": mocker.Mock(string_value="type1")}
    
    mock_execution2 = mocker.Mock()
    mock_execution2.id = 101
    mock_execution2.name = "execution2"
    mock_execution2.properties = {"Execution_type_name": mocker.Mock(string_value="type2")}
    
    mock_store.get_executions_by_context.return_value = [mock_execution1, mock_execution2]
    
    # Step 4: Create DataFrames that will be returned by _transform_to_dataframe
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
    
    # Step 5: Mock _transform_to_dataframe to return these DataFrames
    # Use side_effect to return a different DataFrame for each execution, matching the order of calls.
    query._transform_to_dataframe = mocker.Mock(side_effect=[df1, df2])
    
    # Step 6: Call the method under test
    executions_df = query.get_all_executions_in_stage("stage1")
    
    # Step 7: Assert the result is correct
    assert len(executions_df) == 2
    assert "id" in executions_df.columns
    assert "name" in executions_df.columns
    assert "Execution_type_name" in executions_df.columns
    
    # Check first execution
    assert executions_df.iloc[0]["id"] == 100
    assert executions_df.iloc[0]["name"] == "execution1"
    assert executions_df.iloc[0]["Execution_type_name"] == "type1"
    
    # Check second execution
    assert executions_df.iloc[1]["id"] == 101
    assert executions_df.iloc[1]["name"] == "execution2"
    assert executions_df.iloc[1]["Execution_type_name"] == "type2"
    
    # Step 8: Verify method calls
    mock_store.get_contexts_by_type.assert_called_once_with("Parent_Context")
    mock_store.get_children_contexts_by_context.assert_called_once_with(1)
    mock_store.get_executions_by_context.assert_called_once_with(10)
    
    # Verify that _transform_to_dataframe was called twice (once for each execution)
    assert query._transform_to_dataframe.call_count == 2
    query._transform_to_dataframe.assert_any_call(mock_execution1, {"id": 100, "name": "execution1"})
    query._transform_to_dataframe.assert_any_call(mock_execution2, {"id": 101, "name": "execution2"})


def test_get_all_executions_by_ids_list(query_fixture, mocker):
    """Test retrieving all executions by a list of execution IDs.
    
    Flow: get_all_executions_by_ids_list -> store.get_executions_by_id -> 
          _transform_to_dataframe -> pd.concat
    """
    query, mock_store = query_fixture
    
    # Step 1: Mock the return value of `get_executions_by_id`
    mock_execution1 = mocker.Mock()
    mock_execution1.id = 100
    mock_execution1.name = "execution1"
    mock_execution1.properties = {"Execution_type_name": mocker.Mock(string_value="type1")}
    
    mock_execution2 = mocker.Mock()
    mock_execution2.id = 101
    mock_execution2.name = "execution2"
    mock_execution2.properties = {"Execution_type_name": mocker.Mock(string_value="type2")}
    
    mock_store.get_executions_by_id.return_value = [mock_execution1, mock_execution2]
    
    # Step 2: Create DataFrames that will be returned by _transform_to_dataframe
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
    # side_effect is needed because get_all_executions_by_ids_list calls _transform_to_dataframe for each execution,
    # so each call should return the corresponding DataFrame (df1 for the first, df2 for the second).
    query._transform_to_dataframe = mocker.Mock(side_effect=[df1, df2])
    
    # Step 4: Call the method under test with the real pandas.concat
    executions_df = query.get_all_executions_by_ids_list([100, 101])

    # Step 5: Assert the result is correct
    assert len(executions_df) == 2
    assert "id" in executions_df.columns
    assert "name" in executions_df.columns
    assert "Execution_type_name" in executions_df.columns
    
    # Check first execution
    assert executions_df.iloc[0]["id"] == 100
    assert executions_df.iloc[0]["name"] == "execution1"
    assert executions_df.iloc[0]["Execution_type_name"] == "type1"
    
    # Check second execution
    assert executions_df.iloc[1]["id"] == 101
    assert executions_df.iloc[1]["name"] == "execution2"
    assert executions_df.iloc[1]["Execution_type_name"] == "type2"
    
    # Step 6: Verify method calls
    mock_store.get_executions_by_id.assert_called_once_with([100, 101])
    assert query._transform_to_dataframe.call_count == 2


def test_get_all_artifacts_by_ids_list(query_fixture, mocker):
    """Test retrieving all artifacts by a list of artifact IDs.
    
    Flow: get_all_artifacts_by_ids_list -> store.get_artifacts_by_id -> 
          get_artifact_df -> pd.concat
    """
    query, mock_store = query_fixture
    
    # Step 1: Create mock artifacts
    mock_artifact1 = mocker.Mock(spec=Artifact)
    mock_artifact1.id = 200
    mock_artifact1.name = "artifact1"
    mock_artifact1.type_id = 1
    mock_artifact1.uri = "uri1"
    mock_artifact1.create_time_since_epoch = 1234567890
    mock_artifact1.last_update_time_since_epoch = 1234567891
    mock_artifact1.properties = {}
    mock_artifact1.custom_properties = {}
    
    mock_artifact2 = mocker.Mock(spec=Artifact)
    mock_artifact2.id = 201
    mock_artifact2.name = "artifact2"
    mock_artifact2.type_id = 2
    mock_artifact2.uri = "uri2"
    mock_artifact2.create_time_since_epoch = 1234567892
    mock_artifact2.last_update_time_since_epoch = 1234567893
    mock_artifact2.properties = {}
    mock_artifact2.custom_properties = {}
    
    # Step 2: Mock the return value of `get_artifacts_by_id`
    mock_store.get_artifacts_by_id.return_value = [mock_artifact1, mock_artifact2]
    
    # Step 3: Create DataFrames that will be returned by get_artifact_df
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
    # Side effect is needed because get_all_artifacts_by_ids_list calls get_artifact_df for each artifact,
    # so each call returns the corresponding DataFrame (df1 for the first, df2 for the second).
    query.get_artifact_df = mocker.Mock(side_effect=[df1, df2])
    
    # Step 5: Call the method under test with the real pandas.concat
    artifacts_df = query.get_all_artifacts_by_ids_list([200, 201])
    
    # Step 6: Assert the result is correct
    assert len(artifacts_df) == 2
    assert "id" in artifacts_df.columns
    assert "name" in artifacts_df.columns
    assert "type" in artifacts_df.columns
    assert "uri" in artifacts_df.columns
    
    # Check first artifact
    first_row = artifacts_df[artifacts_df["id"] == 200].iloc[0]
    assert first_row["name"] == "artifact1"
    assert first_row["type"] == "Type1"
    assert first_row["uri"] == "uri1"
    
    # Check second artifact
    second_row = artifacts_df[artifacts_df["id"] == 201].iloc[0]
    assert second_row["name"] == "artifact2"
    assert second_row["type"] == "Type2"
    assert second_row["uri"] == "uri2"
    
    # Step 7: Verify method calls
    mock_store.get_artifacts_by_id.assert_called_once_with([200, 201])
    query.get_artifact_df.assert_any_call(mock_artifact1)
    query.get_artifact_df.assert_any_call(mock_artifact2)


def test_get_all_artifacts_for_execution(query_fixture, mocker):
    """Test retrieving all artifacts for a given execution.
    
    Flow: get_all_artifacts_for_execution -> store.get_events_by_execution_ids -> 
          store.get_artifacts_by_id -> get_artifact_df -> pd.concat
    """
    query, mock_store = query_fixture
    
    # Step 1: Mock the return value of `get_events_by_execution_ids`
    mock_event1 = mocker.Mock()
    mock_event1.artifact_id = 200
    mock_event1.type = mlpb.Event.Type.INPUT
    
    mock_event2 = mocker.Mock()
    mock_event2.artifact_id = 201
    mock_event2.type = mlpb.Event.Type.OUTPUT
    
    mock_store.get_events_by_execution_ids.return_value = [mock_event1, mock_event2]
    
    # Step 2: Mock the return value of `get_artifacts_by_id`
    mock_artifact1 = mocker.Mock(spec=Artifact)
    mock_artifact1.id = 200
    mock_artifact1.name = "artifact1"
    mock_artifact1.type_id = 1
    mock_artifact1.uri = "uri1"
    mock_artifact1.create_time_since_epoch = 1234567890
    mock_artifact1.last_update_time_since_epoch = 1234567891
    mock_artifact1.properties = {}
    mock_artifact1.custom_properties = {}
    
    mock_artifact2 = mocker.Mock(spec=Artifact)
    mock_artifact2.id = 201
    mock_artifact2.name = "artifact2"
    mock_artifact2.type_id = 2
    mock_artifact2.uri = "uri2"
    mock_artifact2.create_time_since_epoch = 1234567892
    mock_artifact2.last_update_time_since_epoch = 1234567893
    mock_artifact2.properties = {}
    mock_artifact2.custom_properties = {}
    
    # Mock get_artifacts_by_id to return the appropriate artifact based on ID
    # Side effect is needed here to return different artifacts for different input IDs
    # This allows the test to simulate fetching the correct artifact for each event's artifact_id.
    def get_artifacts_by_id_side_effect(ids):
        if 200 in ids:
            return [mock_artifact1]
        elif 201 in ids:
            return [mock_artifact2]
        return []
    
    # Step 3: Mock get_artifacts_by_id to return these DataFrames
    mock_store.get_artifacts_by_id = mocker.Mock(side_effect=get_artifacts_by_id_side_effect)
    
    # Step 4: Mock get_artifact_df to handle the extra_props parameter
    # Side effect is needed here to return different DataFrames for each artifact and event type
    # This allows the test to simulate get_artifact_df returning the correct DataFrame for each artifact/event.
    def get_artifact_df_side_effect(artifact, extra_props=None):
        event_type = extra_props.get("event") if extra_props else None
        if artifact.id == 200:
            return pd.DataFrame([{
                "id": 200,
                "name": "artifact1",
                "type": "Type1",
                "uri": "uri1",
                "event": event_type
            }])
        elif artifact.id == 201:
            return pd.DataFrame([{
                "id": 201,
                "name": "artifact2",
                "type": "Type2",
                "uri": "uri2",
                "event": event_type
            }])
    
    query.get_artifact_df = mocker.Mock(side_effect=get_artifact_df_side_effect)
    
    # Step 5: Call the method under test
    artifacts_df = query.get_all_artifacts_for_execution(100)
    
    # Step 6: Assert the result is correct
    assert len(artifacts_df) == 2
    assert "id" in artifacts_df.columns
    assert "name" in artifacts_df.columns
    assert "type" in artifacts_df.columns
    assert "uri" in artifacts_df.columns
    assert "event" in artifacts_df.columns
    
    # Check first artifact
    input_row = artifacts_df[artifacts_df["event"] == "INPUT"].iloc[0]
    assert input_row["id"] == 200
    assert input_row["name"] == "artifact1"
    
    # Check second artifact
    output_row = artifacts_df[artifacts_df["event"] == "OUTPUT"].iloc[0]
    assert output_row["id"] == 201
    assert output_row["name"] == "artifact2"
    
    # Step 7: Verify method calls
    mock_store.get_events_by_execution_ids.assert_called_once_with([100])
    mock_store.get_artifacts_by_id.assert_any_call([200])
    mock_store.get_artifacts_by_id.assert_any_call([201])
    query.get_artifact_df.assert_any_call(mock_artifact1, {"event": "INPUT"})
    query.get_artifact_df.assert_any_call(mock_artifact2, {"event": "OUTPUT"})


def test_get_all_artifact_types(query_fixture, mocker):
    """Test retrieving all artifact types.
    
    Flow: get_all_artifact_types -> store.get_artifact_types -> extract names
    """
    query, mock_store = query_fixture
    
    # Step 1: Mock the return value of `get_artifact_types`
    # Create mock artifact types with name attribute
    mock_type1 = mocker.Mock()
    mock_type1.name = "Dataset"
    
    mock_type2 = mocker.Mock()
    mock_type2.name = "Model"
    
    mock_type3 = mocker.Mock()
    mock_type3.name = "Metrics"
    
    mock_store.get_artifact_types.return_value = [mock_type1, mock_type2, mock_type3]
    
    # Step 2: Call the method under test
    artifact_types = query.get_all_artifact_types()
    
    # Step 3: Assert the result is correct
    assert len(artifact_types) == 3
    assert "Dataset" in artifact_types
    assert "Model" in artifact_types
    assert "Metrics" in artifact_types
    
    # Step 4: Verify method calls
    mock_store.get_artifact_types.assert_called_once()


def test_get_all_executions_for_artifact(query_fixture, mocker):
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
    query, mock_store = query_fixture
    
    # Case 1: Artifact not found
    # Step 1: Mock _get_artifact to return None (artifact not found)
    query._get_artifact = mocker.Mock(return_value=None)
    
    # Step 2: Call the method under test
    result = query.get_all_executions_for_artifact("nonexistent_artifact")
    
    # Step 3: Assert the result is an empty DataFrame
    assert len(result) == 0
    
    # Case 2: Artifact found with events
    # Step 1: Mock _get_artifact to return a mock artifact
    mock_artifact = mocker.Mock()
    mock_artifact.id = 200
    query._get_artifact = mocker.Mock(return_value=mock_artifact)
    
    # Step 2: Mock the events for this artifact (one INPUT and one OUTPUT event)
    mock_input_event = mocker.Mock()
    mock_input_event.execution_id = 100
    mock_input_event.type = mlpb.Event.Type.INPUT

    mock_output_event = mocker.Mock()
    mock_output_event.execution_id = 101
    mock_output_event.type = mlpb.Event.Type.OUTPUT

    mock_store.get_events_by_artifact_ids.return_value = [mock_input_event, mock_output_event]
    
    # Step 3: Mock the executions
    # Create a helper class for string_value property
    class MockStringValue:
        """Simulates the string_value property in execution properties."""
        def __init__(self, value):
            self.string_value = value
    
    mock_execution1 = mocker.Mock()
    mock_execution1.id = 100
    mock_execution1.name = "execution1"
    mock_execution1.properties = {
        "Execution_type_name": MockStringValue("type1"),
        "Execution_uuid": MockStringValue("uuid1")
    }
    
    mock_execution2 = mocker.Mock()
    mock_execution2.id = 101
    mock_execution2.name = "execution2"
    mock_execution2.properties = {
        "Execution_type_name": MockStringValue("type2"),
        "Execution_uuid": MockStringValue("uuid2")
    }
    
    # Mock get_executions_by_id to return the appropriate execution based on ID
    # Side effect is needed so that each call returns the correct execution for the given ID,
    # simulating the real store behavior for different execution IDs in the test.
    def get_executions_by_id_side_effect(ids):
        if 100 in ids:
            return [mock_execution1]
        elif 101 in ids:
            return [mock_execution2]
        return []
    
    mock_store.get_executions_by_id = mocker.Mock(side_effect=get_executions_by_id_side_effect)
    
    # Step 4: Mock the contexts for each execution
    mock_stage_context1 = mocker.Mock()
    mock_stage_context1.id = 10
    mock_stage_context1.name = "stage1"
    
    mock_stage_context2 = mocker.Mock()
    mock_stage_context2.id = 11
    mock_stage_context2.name = "stage2"
    
    # Mock get_contexts_by_execution to return the appropriate context based on execution ID.
    # Side effect is needed to simulate different stage contexts for each execution ID,
    # because the tested method expects to retrieve the correct stage for each execution event.
    def get_contexts_by_execution_side_effect(execution_id):
        if execution_id == 100:
            return [mock_stage_context1]
        elif execution_id == 101:
            return [mock_stage_context2]
        return []
    
    mock_store.get_contexts_by_execution = mocker.Mock(side_effect=get_contexts_by_execution_side_effect)
    
    # Step 5: Mock the pipeline contexts
    mock_pipeline_context1 = mocker.Mock()
    mock_pipeline_context1.name = "pipeline1"
    
    mock_pipeline_context2 = mocker.Mock()
    mock_pipeline_context2.name = "pipeline2"
    
    # Mock get_parent_contexts_by_context to return the appropriate pipeline context
    # Side effect is needed here to simulate different parent pipeline contexts for each stage context ID,
    # as the tested method expects to retrieve the correct pipeline for each execution's stage.
    def get_parent_contexts_by_context_side_effect(context_id):
        if context_id == 10:
            return [mock_pipeline_context1]
        elif context_id == 11:
            return [mock_pipeline_context2]
        return []
    
    mock_store.get_parent_contexts_by_context = mocker.Mock(side_effect=get_parent_contexts_by_context_side_effect)
    
    # Step 6: Call the method under test
    result = query.get_all_executions_for_artifact("test_artifact")
    
    # Step 7: Verify the result DataFrame
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2  # Two events should result in two rows
    
    # Step 8: Check columns and values
    assert "execution_id" in result.columns
    assert "Type" in result.columns
    assert "execution_name" in result.columns
    assert "execution_type_name" in result.columns
    assert "stage" in result.columns
    assert "pipeline" in result.columns
    
    # Sort the DataFrame by execution_id to ensure consistent order for testing
    result = result.sort_values("execution_id")


def test_get_one_hop_child_artifacts(query_fixture, mocker):
    """Test retrieving one-hop child artifacts for a given artifact.
    
    Flow:
        get_one_hop_child_artifacts
            -> _get_artifact (resolve artifact name to artifact object)
            -> _get_executions_by_input_artifact_id (find executions that used this artifact as input)
            -> _get_output_artifacts (find output artifact IDs from those executions)
            -> store.get_artifacts_by_id (fetch artifact objects)
            -> get_artifact_df (convert each artifact to DataFrame)
            -> pd.concat (combine all artifact DataFrames into a single DataFrame)
    """
    query, mock_store = query_fixture
    
    # Step 1: Mock _get_artifact
    mock_artifact = mocker.Mock()
    mock_artifact.id = 100
    query._get_artifact = mocker.Mock(return_value=mock_artifact)
    
    # Step 2: Mock store.get_events_by_artifact_ids for _get_executions_by_input_artifact_id
    mock_input_event = mocker.Mock()
    mock_input_event.execution_id = 300
    mock_input_event.type = mlpb.Event.INPUT
    
    mock_store.get_events_by_artifact_ids.return_value = [mock_input_event]
    
    # Step 3: Mock _get_output_artifacts
    query._get_output_artifacts = mocker.Mock(return_value=[200, 201])

    # Step 4: Mock the return value of `get_artifacts_by_id`
    mock_artifact1 = mocker.Mock()
    mock_artifact1.id = 200
    mock_artifact1.name = "child_artifact1"
    mock_artifact1.type_id = 1
    mock_artifact1.uri = "uri1"
    mock_artifact1.create_time_since_epoch = 1234567890
    mock_artifact1.last_update_time_since_epoch = 1234567891

    mock_artifact2 = mocker.Mock()
    mock_artifact2.id = 201
    mock_artifact2.name = "child_artifact2"
    mock_artifact2.type_id = 2
    mock_artifact2.uri = "uri2"
    mock_artifact2.create_time_since_epoch = 1234567892
    mock_artifact2.last_update_time_since_epoch = 1234567893
    
    mock_store.get_artifacts_by_id.return_value = [mock_artifact1, mock_artifact2]
    
    # Step 5: Mock get_artifact_df to return DataFrames for each artifact
    df1 = pd.DataFrame([{
        "id": 200,
        "name": "child_artifact1",
        "type": "Type1",
        "uri": "uri1",
        "create_time_since_epoch": 1234567890,
        "last_update_time_since_epoch": 1234567891
    }])
    
    df2 = pd.DataFrame([{
        "id": 201,
        "name": "child_artifact2",
        "type": "Type2",
        "uri": "uri2",
        "create_time_since_epoch": 1234567892,
        "last_update_time_since_epoch": 1234567893
    }])
    
    # The `side_effect` for `get_artifact_df` is used to return a different DataFrame for each artifact,
    # simulating the conversion of each mock artifact to its corresponding DataFrame.
    query.get_artifact_df = mocker.Mock(side_effect=[df1, df2])
    
    # Step 6: Call the method under test
    result = query.get_one_hop_child_artifacts("parent_artifact")
    
    # Step 7: Assert the result
    assert len(result) == 2
    assert "id" in result.columns
    assert "name" in result.columns
    assert "type" in result.columns
    assert "uri" in result.columns
    
    # Check first child artifact
    first_row = result[result["id"] == 200].iloc[0]
    assert first_row["name"] == "child_artifact1"
    assert first_row["type"] == "Type1"
    
    # Check second child artifact
    second_row = result[result["id"] == 201].iloc[0]
    assert second_row["name"] == "child_artifact2"
    assert second_row["type"] == "Type2"
    
    # Step 8: Verify method calls
    query._get_artifact.assert_called_once_with("parent_artifact")
    mock_store.get_events_by_artifact_ids.assert_called_once_with([100])
    query._get_output_artifacts.assert_called_once_with([300])
    mock_store.get_artifacts_by_id.assert_called_once_with([200, 201])
    query.get_artifact_df.assert_any_call(mock_artifact1)
    query.get_artifact_df.assert_any_call(mock_artifact2)


def test_get_one_hop_parent_executions(query_fixture, mocker):
    """Test retrieving one-hop parent executions for a given execution ID.

    Flow:
        get_one_hop_parent_executions
            -> _get_input_artifacts (find input artifact IDs for the given execution IDs)
            -> _get_executions_by_output_artifact_id (find executions that produced those artifacts)
            -> store.get_executions_by_id (fetch execution objects for those IDs)
            -> return list of parent execution objects
    """
    query, mock_store = query_fixture
    
    # Step 1: Mock the return value of `_get_input_artifacts`
    query._get_input_artifacts = mocker.Mock(return_value=[200, 201])
    
    # Step 2: Mock the return value of `_get_executions_by_output_artifact_id`
    # Side effect is needed here to return different execution IDs for different artifact IDs
    def mock_get_executions_by_output_artifact_id(artifact_id, pipeline_id=None):
        if artifact_id == 200:
            return [100]
        elif artifact_id == 201:
            return [101]
        return []
    
    query._get_executions_by_output_artifact_id = mocker.Mock(side_effect=mock_get_executions_by_output_artifact_id)
    
    # Step 3: Mock the return value of `get_executions_by_id`
    mock_execution1 = mocker.Mock()
    mock_execution1.id = 100
    mock_execution1.properties = {"Execution_type_name": mocker.Mock(string_value="type1")}
    
    mock_execution2 = mocker.Mock()
    mock_execution2.id = 101
    mock_execution2.properties = {"Execution_type_name": mocker.Mock(string_value="type2")}
    
    # Side effect: return correct mock execution based on input ID list
    # Needed because get_one_hop_parent_executions calls get_executions_by_id separately for each parent execution ID.
    def mock_get_executions_by_id(ids):
        if ids[0] == 100:
            return [mock_execution1]
        elif ids[0] == 101:
            return [mock_execution2]
        return []
    
    mock_store.get_executions_by_id = mocker.Mock(side_effect=mock_get_executions_by_id)
    
    # Step 4: Call the method under test
    parent_executions = query.get_one_hop_parent_executions([300])
    
    # Step 5: Assert the result is correct
    assert len(parent_executions) == 2
    assert parent_executions[0].id == 100
    assert parent_executions[0].properties["Execution_type_name"].string_value == "type1"
    assert parent_executions[1].id == 101
    assert parent_executions[1].properties["Execution_type_name"].string_value == "type2"
    
    # Step 6: Verify method calls
    query._get_input_artifacts.assert_called_once_with([300])
    query._get_executions_by_output_artifact_id.assert_any_call(200, None)
    query._get_executions_by_output_artifact_id.assert_any_call(201, None)
    mock_store.get_executions_by_id.assert_any_call([100])
    mock_store.get_executions_by_id.assert_any_call([101])


def test_get_all_parent_artifacts(query_fixture, mocker):
    """Test retrieving all parent artifacts for a given artifact.
    
    Flow:
        get_all_parent_artifacts
            -> get_one_hop_parent_artifacts (recursively find all parent artifacts for the given artifact)
            -> pd.concat (combine all parent artifact DataFrames into a single DataFrame)
    """
    query, mock_store = query_fixture
    
    # Step 1: Create DataFrames for different levels of parent artifacts
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
        "id": [60, 61],
        "name": ["grandparent3", "grandparent4"],
        "type": ["Type3", "Type4"],
        "uri": ["/path/to/grandparent3", "/path/to/grandparent4"],
        "create_time_since_epoch": [800000, 800001],
        "last_update_time_since_epoch": [800100, 800101]
    })
    
    empty_df = pd.DataFrame(columns=["id", "name", "type", "uri", "create_time_since_epoch", "last_update_time_since_epoch"])

    # Step 2: Mock get_one_hop_parent_artifacts to return different parents based on the artifact name
    # Side effect is needed here to simulate recursive traversal for each artifact name in the test.
    # This allows the test to mimic the recursive parent lookup logic of get_all_parent_artifacts.
    def mock_get_one_hop_parent_artifacts(artifact_name):
        if artifact_name == "artifact1":
            return first_level_parents
        elif artifact_name == "parent1":
            return second_level_parents_1
        elif artifact_name == "parent2":
            return second_level_parents_2
        else:
            return empty_df
    
    query.get_one_hop_parent_artifacts = mocker.Mock(side_effect=mock_get_one_hop_parent_artifacts)
    
    # Step 3: Call the method under test
    result = query.get_all_parent_artifacts("artifact1")
    
    # Step 4: Assert the result
    assert len(result) == 6  # 2 first-level + 2 second-level from parent1 + 2 second-level from parent2
    
    # Check that all parent artifacts are included
    assert set(result["name"].tolist()) == {
        "parent1", "parent2", "grandparent1", "grandparent2", "grandparent3", "grandparent4"
    }
    
    # Step 5: Verify method calls
    # The method should be called for the original artifact and each parent
    query.get_one_hop_parent_artifacts.assert_any_call("artifact1")
    query.get_one_hop_parent_artifacts.assert_any_call("parent1")
    query.get_one_hop_parent_artifacts.assert_any_call("parent2")


def test_get_all_executions_in_pipeline(query_fixture, mocker):
    """Test retrieving all executions for a given pipeline.
    
    Flow:
        get_all_executions_in_pipeline
            -> _get_pipelines (resolve pipeline name to pipeline object)
            -> _get_stages (get all stages for the pipeline)
            -> _get_executions (get all executions for each stage)
            -> _transform_to_dataframe (convert each execution to DataFrame)
            -> pd.concat (combine all execution DataFrames into a single DataFrame)
    """
    query, mock_store = query_fixture
    
    # Step 1: Mock the return value of `_get_pipelines`
    mock_pipeline = mocker.Mock(spec=Context)
    mock_pipeline.id = 1
    mock_pipeline.name = "pipeline1"
    query._get_pipelines = mocker.Mock(return_value=[mock_pipeline])
    
    # Step 2: Mock the return value of `_get_stages`
    mock_stage1 = mocker.Mock(spec=Context)
    mock_stage1.id = 10
    mock_stage1.name = "stage1"
    
    mock_stage2 = mocker.Mock(spec=Context)
    mock_stage2.id = 11
    mock_stage2.name = "stage2"
    
    query._get_stages = mocker.Mock(return_value=[mock_stage1, mock_stage2])
    
    # Step 3: Mock the return value of `_get_executions`
    mock_execution1 = mocker.Mock()
    mock_execution1.id = 100
    mock_execution1.name = "execution1"
    
    mock_execution2 = mocker.Mock()
    mock_execution2.id = 101
    mock_execution2.name = "execution2"
    
    # Side effect: returns [mock_execution1] for stage1 (id=10), [mock_execution2] for stage2 (id=11)
    # Needed because _get_executions is called for each stage and should return the correct executions per stage.
    query._get_executions = mocker.Mock(
        side_effect=lambda stage_id: [mock_execution1] if stage_id == 10 else [mock_execution2]
    )
    
    # Step 4: Mock the `_transform_to_dataframe` method
    # Side effect: Returns a DataFrame for each execution; required to simulate DataFrame creation per execution.
    query._transform_to_dataframe = mocker.Mock(
        side_effect=lambda execution, data: pd.DataFrame([{
            "id": execution.id,
            "name": execution.name
        }])
    )
    
    # Step 5: Call the method under test
    executions_df = query.get_all_executions_in_pipeline("pipeline1")
    
    # Step 6: Assert the result is correct
    assert len(executions_df) == 2
    assert "id" in executions_df.columns
    assert "name" in executions_df.columns
    
    # Check first execution
    assert executions_df.iloc[0]["id"] == 100
    assert executions_df.iloc[0]["name"] == "execution1"
    
    # Check second execution
    assert executions_df.iloc[1]["id"] == 101
    assert executions_df.iloc[1]["name"] == "execution2"
    
    # Step 7: Verify method calls
    query._get_pipelines.assert_called_once_with("pipeline1")
    query._get_stages.assert_called_once_with(1)
    query._get_executions.assert_any_call(10)
    query._get_executions.assert_any_call(11)
    
    # Verify that _transform_to_dataframe was called twice (once for each execution)
    assert query._transform_to_dataframe.call_count == 2
    query._transform_to_dataframe.assert_any_call(mock_execution1, {"id": 100, "name": "execution1"})
    query._transform_to_dataframe.assert_any_call(mock_execution2, {"id": 101, "name": "execution2"})


def test_get_all_artifacts_for_executions(query_fixture, mocker):
    """Test retrieving all artifacts for a list of execution IDs.
    
    Flow: get_all_artifacts_for_executions -> store.get_events_by_execution_ids -> 
          store.get_artifacts_by_id -> get_artifact_df -> pd.concat
    """
    query, mock_store = query_fixture
    
    # Step 1: Mock the return value of `get_events_by_execution_ids`
    # We need to create mock events with artifact_ids that will be used to fetch artifacts
    mock_event1 = mocker.Mock()
    mock_event1.artifact_id = 200
    mock_event1.type = mlpb.Event.Type.INPUT
    
    mock_event2 = mocker.Mock()
    mock_event2.artifact_id = 201
    mock_event2.type = mlpb.Event.Type.OUTPUT
    
    mock_store.get_events_by_execution_ids.return_value = [mock_event1, mock_event2]
    
    # Step 2: Mock the return value of `get_artifacts_by_id`
    mock_artifact1 = mocker.Mock(spec=Artifact)
    mock_artifact1.id = 200
    mock_artifact1.name = "artifact1"
    mock_artifact1.type_id = 1
    mock_artifact1.uri = "uri1"
    
    mock_artifact2 = mocker.Mock(spec=Artifact)
    mock_artifact2.id = 201
    mock_artifact2.name = "artifact2"
    mock_artifact2.type_id = 2
    mock_artifact2.uri = "uri2"
    
    mock_store.get_artifacts_by_id.return_value = [mock_artifact1, mock_artifact2]
    
    # Step 3: Create DataFrames that will be returned by get_artifact_df
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
    # Side effect is needed because get_all_artifacts_for_executions calls get_artifact_df for each artifact,
    # so each call should return the corresponding DataFrame (df1 for the first, df2 for the second).
    query.get_artifact_df = mocker.Mock(side_effect=[df1, df2])
    
    # Step 5: Call the method under test
    artifacts_df = query.get_all_artifacts_for_executions([100, 101])
    
    # Step 6: Assert the result is correct
    assert len(artifacts_df) == 2
    assert "id" in artifacts_df.columns
    assert "name" in artifacts_df.columns
    assert "type" in artifacts_df.columns
    assert "uri" in artifacts_df.columns
    
    # Check first artifact
    first_row = artifacts_df[artifacts_df["id"] == 200].iloc[0]
    assert first_row["name"] == "artifact1"
    assert first_row["type"] == "Type1"
    assert first_row["uri"] == "uri1"
    
    # Check second artifact
    second_row = artifacts_df[artifacts_df["id"] == 201].iloc[0]
    assert second_row["name"] == "artifact2"
    assert second_row["type"] == "Type2"
    assert second_row["uri"] == "uri2"
    
    # Step 7: Verify method calls
    mock_store.get_events_by_execution_ids.assert_called_once_with({100, 101})
    mock_store.get_artifacts_by_id.assert_called_once_with([200, 201])
    query.get_artifact_df.assert_any_call(mock_artifact1)
    query.get_artifact_df.assert_any_call(mock_artifact2)


def test_dumptojson(query_fixture, mocker):
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
    query, mock_store = query_fixture
    
    # Step 1: Mock the pipeline context
    mock_pipeline_context = mocker.Mock(spec=Context)
    mock_pipeline_context.id = 1
    mock_pipeline_context.name = "pipeline1"
    query._get_pipelines = mocker.Mock(return_value=[mock_pipeline_context])
    
    # Step 2: Mock the stage context
    mock_stage_context = mocker.Mock(spec=Context)
    mock_stage_context.id = 10
    mock_stage_context.name = "stage1"
    mock_store.get_children_contexts_by_context.return_value = [mock_stage_context]
    
    # Step 3: Mock the execution
    mock_execution = mocker.Mock(spec=Execution)
    mock_execution.id = 100
    mock_execution.name = "execution1"
    mock_execution.type_id = 1  # Add type_id attribute
    mock_execution.properties = {
        "Execution_uuid": mocker.Mock(string_value="uuid1"),
        "Execution_type_name": mocker.Mock(string_value="type1")
    }
    mock_store.get_executions_by_context.return_value = [mock_execution]
    
    # Step 4: Mock the execution type
    mock_execution_type = mocker.Mock()
    mock_execution_type.name = "ExecutionType1"
    mock_store.get_execution_types_by_id.return_value = [mock_execution_type]
    
    # Step 5: Mock the event
    mock_event = mocker.Mock(spec=mlpb.Event)
    mock_event.artifact_id = 200
    mock_event.type = mlpb.Event.INPUT  # This is an enum value (3)
    mock_store.get_events_by_execution_ids.return_value = [mock_event]
    
    # Step 6: Mock the artifact - ensure all required attributes are set
    mock_artifact = mocker.Mock(spec=Artifact)
    mock_artifact.id = 200
    mock_artifact.name = "artifact1"
    mock_artifact.uri = "artifact_uri"
    mock_artifact.type_id = 300  # Make sure type_id is set
    mock_artifact.properties = {}  # Add properties dictionary
    mock_artifact.custom_properties = {}  # Add custom_properties dictionary
    mock_store.get_artifacts_by_id.return_value = [mock_artifact]
    
    # Step 7: Mock the artifact type
    mock_artifact_type = mocker.Mock()
    mock_artifact_type.name = "Dataset"
    mock_store.get_artifact_types_by_id.return_value = [mock_artifact_type]
    
    # Step 8: Call the method under test
    result_json = query.dumptojson("pipeline1")
    
    # Step 9: Parse the JSON result
    result = json.loads(result_json)
    
    # Step 10: Assert the structure and content
    assert "Pipeline" in result
    assert len(result["Pipeline"]) == 1
    
    pipeline = result["Pipeline"][0]
    assert pipeline["id"] == 1
    assert pipeline["name"] == "pipeline1"
    assert "stages" in pipeline
    assert len(pipeline["stages"]) == 1
    
    stage = pipeline["stages"][0]
    assert stage["id"] == 10
    assert stage["name"] == "stage1"
    assert "executions" in stage
    assert len(stage["executions"]) == 1
    
    execution = stage["executions"][0]
    assert execution["id"] == 100
    assert execution["name"] == "execution1"
    assert execution["properties"]["Execution_uuid"] == "uuid1"
    assert execution["properties"]["Execution_type_name"] == "type1"
    assert "events" in execution
    assert len(execution["events"]) == 1
    
    event = execution["events"][0]
    # Check that the event type is the numeric value 3 (INPUT)
    assert event["type"] == 3
    assert "artifact" in event
    
    artifact = event["artifact"]
    assert artifact["id"] == 200
    assert artifact["name"] == "artifact1"
    assert artifact["type"] == "Dataset"
    assert artifact["uri"] == "artifact_uri"
    
    # Step 11: Verify method calls
    query._get_pipelines.assert_called_once_with("pipeline1")
    mock_store.get_children_contexts_by_context.assert_called_once_with(1)
    mock_store.get_executions_by_context.assert_called_once_with(10)
    mock_store.get_events_by_execution_ids.assert_called_once_with([100])
    mock_store.get_artifacts_by_id.assert_called_once_with([200])
    mock_store.get_artifact_types_by_id.assert_called_once_with([300])


def test_get_all_artifacts_by_context(query_fixture, mocker):
    """Test retrieving all artifacts for a given pipeline context.

    Flow:
        get_all_artifacts_by_context
            -> get_pipeline_id (resolve pipeline name to pipeline context ID)
            -> store.get_contexts_by_type (fetch pipeline context)
            -> store.get_children_contexts_by_context (fetch stage contexts)
            -> store.get_artifacts_by_context (fetch artifacts for each stage context)
            -> get_artifact_df (convert each artifact to DataFrame)
            -> pd.concat (combine all artifact DataFrames into a single DataFrame)
    """
    query, mock_store = query_fixture
    
    # Step 1: Mock get_pipeline_id to return a context ID
    pipeline_context_id = 1
    query.get_pipeline_id = mocker.Mock(return_value=pipeline_context_id)
    
    # Step 2: Mock the return value of get_contexts_by_type
    parent_context = mocker.Mock()
    parent_context.id = pipeline_context_id
    parent_context.name = "test_pipeline"
    mock_store.get_contexts_by_type.return_value = [parent_context]
    
    # Step 3: Mock the return value of get_children_contexts_by_context
    child_context1 = mocker.Mock()
    child_context1.id = 10
    child_context1.name = "stage1"
    
    child_context2 = mocker.Mock()
    child_context2.id = 11
    child_context2.name = "stage2"
    
    mock_store.get_children_contexts_by_context.return_value = [child_context1, child_context2]
    
    # Step 4: Mock the return value of get_artifacts_by_context
    mock_artifact1 = mocker.Mock()
    mock_artifact1.id = 100
    mock_artifact1.name = "artifact1"
    mock_artifact1.type_id = 1
    
    mock_artifact2 = mocker.Mock()
    mock_artifact2.id = 101
    mock_artifact2.name = "artifact2"
    mock_artifact2.type_id = 2
    
    # Side effect to return different artifacts for different context IDs.
    # This is needed because get_artifacts_by_context is called for each stage context separately.
    def get_artifacts_by_context_side_effect(context_id):
        if context_id == 10:
            return [mock_artifact1]
        elif context_id == 11:
            return [mock_artifact2]
        return []
    
    mock_store.get_artifacts_by_context.side_effect = get_artifacts_by_context_side_effect
    
    # Step 5: Mock the DataFrame returned for each artifact
    df1 = pd.DataFrame([{
        'id': 100,
        'name': 'artifact1',
        'type': 'Type1'
    }])
    
    df2 = pd.DataFrame([{
        'id': 101,
        'name': 'artifact2',
        'type': 'Type2'
    }])
    
    # Side effect to return different DataFrames for different artifacts
    # Needed because get_artifact_df is called for each artifact, so each call must return the correct DataFrame.
    def get_artifact_df_side_effect(artifact):
        if artifact.id == 100:
            return df1
        elif artifact.id == 101:
            return df2
        return pd.DataFrame()
    
    query.get_artifact_df = mocker.Mock(side_effect=get_artifact_df_side_effect)
    
    # Step 6: Call the method under test
    result = query.get_all_artifacts_by_context("test_pipeline")
    
    # Step 7: Assert the result
    assert len(result) == 2
    assert 'id' in result.columns
    assert 'name' in result.columns
    assert 'type' in result.columns
    
    # Check that the result contains data from both artifacts
    assert 100 in result['id'].values
    assert 101 in result['id'].values
    assert 'artifact1' in result['name'].values
    assert 'artifact2' in result['name'].values
    
    # Step 8: Verify method calls
    query.get_pipeline_id.assert_called_once_with("test_pipeline")
    mock_store.get_contexts_by_type.assert_called_once_with("Parent_Context")
    mock_store.get_children_contexts_by_context.assert_called_once_with(pipeline_context_id)
    mock_store.get_artifacts_by_context.assert_any_call(10)
    mock_store.get_artifacts_by_context.assert_any_call(11)
    query.get_artifact_df.assert_any_call(mock_artifact1)
    query.get_artifact_df.assert_any_call(mock_artifact2)


def test_get_all_artifacts(query_fixture, mocker):
    """Test retrieving all artifact names.

    Flow:
        get_all_artifacts
            -> store.get_artifacts (fetch all artifact objects)
            -> extract artifact names from each artifact
            -> return list of artifact names
    """
    query, mock_store = query_fixture
    
    # Step 1: Mock the return value of `get_artifacts`
    mock_artifact1 = mocker.Mock()
    mock_artifact1.name = "artifact1"
    
    mock_artifact2 = mocker.Mock()
    mock_artifact2.name = "artifact2"
    
    mock_artifact3 = mocker.Mock()
    mock_artifact3.name = "artifact3"
    
    mock_store.get_artifacts.return_value = [mock_artifact1, mock_artifact2, mock_artifact3]
    
    # Step 2: Call the method under test
    artifact_names = query.get_all_artifacts()
    
    # Step 3: Assert the result is correct
    assert len(artifact_names) == 3
    assert "artifact1" in artifact_names
    assert "artifact2" in artifact_names
    assert "artifact3" in artifact_names
    
    # Step 4: Verify method calls
    mock_store.get_artifacts.assert_called_once()


def test_get_one_hop_parent_executions_ids(query_fixture, mocker):
    """Test retrieving one-hop parent execution IDs for a given execution ID.

    Flow:
        get_one_hop_parent_executions_ids
            -> _get_input_artifacts (find input artifact IDs for the given execution IDs)
            -> _get_executions_by_output_artifact_id (find executions that produced those artifacts)
            -> aggregate all parent execution IDs into a list
            -> return the list of parent execution IDs
    """
    query, mock_store = query_fixture
    
    # Step 1: Mock the return value of `_get_input_artifacts`
    query._get_input_artifacts = mocker.Mock(return_value=[200, 201])

    # Step 2: Mock the return value of `_get_executions_by_output_artifact_id`
    # Side effect is needed here to return different execution IDs for different artifact IDs in unit tests.
    # This allows the test to simulate the mapping of each input artifact to its producing execution.
    def mock_get_executions_by_output_artifact_id(artifact_id, pipeline_id=None):
        if artifact_id == 200:
            return [100]
        elif artifact_id == 201:
            return [101]
        return []
    
    query._get_executions_by_output_artifact_id = mocker.Mock(side_effect=mock_get_executions_by_output_artifact_id)

    # Step 3: Call the method under test
    parent_execution_ids = query.get_one_hop_parent_executions_ids([300])

    # Step 4: Assert the result is correct
    assert len(parent_execution_ids) == 2
    assert 100 in parent_execution_ids
    assert 101 in parent_execution_ids

    # Step 5: Verify method calls
    query._get_input_artifacts.assert_called_once_with([300])
    query._get_executions_by_output_artifact_id.assert_any_call(200, None)
    query._get_executions_by_output_artifact_id.assert_any_call(201, None)


def test_get_executions_with_execution_ids(query_fixture, mocker):
    """Test retrieving executions with execution IDs.

    Flow:
        get_executions_with_execution_ids
            -> store.get_executions_by_id (fetch execution objects for given IDs)
            -> build DataFrame with id, Execution_type_name, Execution_uuid for each execution
            -> return DataFrame with execution details
    """
    query, mock_store = query_fixture
    
    # Step 1: Mock the return value of `get_executions_by_id`
    # Create mock executions with the necessary structure
    mock_execution1 = mocker.Mock()
    mock_execution1.id = 100
    mock_execution1.properties = {
        "Execution_type_name": mocker.Mock(string_value="type1"),
        "Execution_uuid": mocker.Mock(string_value="uuid1")
    }

    mock_execution2 = mocker.Mock()
    mock_execution2.id = 101
    mock_execution2.properties = {
        "Execution_type_name": mocker.Mock(string_value="type2"),
        "Execution_uuid": mocker.Mock(string_value="uuid2")
    }

    mock_store.get_executions_by_id.return_value = [mock_execution1, mock_execution2]
    
    # Step 2: Mock MessageToDict to return a dictionary with the expected structure
    # Side effect is needed so each call returns a dict with the correct execution id, matching the real MessageToDict output per execution.
    mocker.patch('cmflib.cmfquery.MessageToDict', side_effect=lambda exe, **kwargs: {"id": exe.id})
    
    # Step 3: Mock _transform_to_dataframe to return a DataFrame with the expected structure
    # Side effect is required so each call returns a DataFrame for the corresponding execution.
    # This simulates the real method which processes each execution separately.
    def transform_side_effect(execution, extra_props=None):
        data = {
            "id": extra_props["id"] if extra_props else execution.id,
            "Execution_type_name": execution.properties["Execution_type_name"].string_value,
            "Execution_uuid": execution.properties["Execution_uuid"].string_value
        }
        return pd.DataFrame([data])
    
    query._transform_to_dataframe = mocker.Mock(side_effect=transform_side_effect)
    
    # Step 4: Call the method under test
    executions_df = query.get_executions_with_execution_ids([100, 101])
    
    # Step 5: Assert the result is correct
    assert isinstance(executions_df, pd.DataFrame)
    assert len(executions_df) == 2
    
    # Check columns
    assert "id" in executions_df.columns
    assert "Execution_type_name" in executions_df.columns
    assert "Execution_uuid" in executions_df.columns
    
    # Check values for first execution
    first_row = executions_df[executions_df["id"] == 100].iloc[0]
    assert first_row["Execution_type_name"] == "type1"
    assert first_row["Execution_uuid"] == "uuid1"
    
    # Check values for second execution
    second_row = executions_df[executions_df["id"] == 101].iloc[0]
    assert second_row["Execution_type_name"] == "type2"
    assert second_row["Execution_uuid"] == "uuid2"

    # Step 6: Verify method calls
    mock_store.get_executions_by_id.assert_called_once_with([100, 101])
    assert query._transform_to_dataframe.call_count == 2


def test_get_all_child_artifacts(query_fixture, mocker):
    """Test retrieving all child artifacts for a given artifact.
    
    Flow:
        get_all_child_artifacts
            -> get_one_hop_child_artifacts (recursively find all child artifacts for the given artifact)
            -> pd.concat (combine all child artifact DataFrames into a single DataFrame)
    """
    query, mock_store = query_fixture
    
    # Step 1: Create DataFrames for different levels of child artifacts
    first_level_children = pd.DataFrame({
        "id": [200, 201],
        "name": ["child_artifact1", "child_artifact2"],
        "type": ["Type1", "Type2"],
        "uri": ["/path/to/child1", "/path/to/child2"],
        "create_time_since_epoch": [1100000, 1100001],
        "last_update_time_since_epoch": [1100100, 1100101]
    })
    
    second_level_children_1 = pd.DataFrame({
        "id": [250, 251],
        "name": ["grandchild1", "grandchild2"],
        "type": ["Type1", "Type2"],
        "uri": ["/path/to/grandchild1", "/path/to/grandchild2"],
        "create_time_since_epoch": [1200000, 1200001],
        "last_update_time_since_epoch": [1200100, 1200101]
    })
    
    second_level_children_2 = pd.DataFrame({
        "id": [260, 261],
        "name": ["grandchild3", "grandchild4"],
        "type": ["Type3", "Type4"],
        "uri": ["/path/to/grandchild3", "/path/to/grandchild4"],
        "create_time_since_epoch": [1300000, 1300001],
        "last_update_time_since_epoch": [1300100, 1300101]
    })
    
    # Empty DataFrame for artifacts with no children
    empty_df = pd.DataFrame(columns=["id", "name", "type"])
    
    # Step 2: Mock get_one_hop_child_artifacts to return different children based on the artifact name
    # Side effect is needed to simulate recursive traversal for each artifact name in the test.
    # This allows the test to mimic the recursive child lookup logic of get_all_child_artifacts.
    def mock_get_one_hop_child_artifacts(artifact_name):
        if artifact_name == "artifact1":
            return first_level_children
        elif artifact_name == "child_artifact1":
            return second_level_children_1
        elif artifact_name == "child_artifact2":
            return second_level_children_2
        else:
            return empty_df
    
    query.get_one_hop_child_artifacts = mocker.Mock(side_effect=mock_get_one_hop_child_artifacts)
    
    # Step 3: Call the method under test
    result = query.get_all_child_artifacts("artifact1")
    
    # Step 4: Assert the result
    assert len(result) == 6  # 2 first-level + 2 second-level from child1 + 2 second-level from child2
    
    # Check that all child artifacts are included
    assert set(result["name"].tolist()) == {
        "child_artifact1", "child_artifact2", "grandchild1", "grandchild2", "grandchild3", "grandchild4"
    }
    
    # Step 5: Verify method calls
    # The method should be called for the original artifact and each child
    query.get_one_hop_child_artifacts.assert_any_call("artifact1")
    query.get_one_hop_child_artifacts.assert_any_call("child_artifact1")
    query.get_one_hop_child_artifacts.assert_any_call("child_artifact2")


def test_get_all_parent_executions(query_fixture, mocker):
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
    query, mock_store = query_fixture
    
    # Step 1: Mock get_all_parent_artifacts
    mock_parent_artifacts = pd.DataFrame({
        'id': [101, 102],
        'name': ['parent_artifact1', 'parent_artifact2'],
        'type': ['type1', 'type2']
    })
    
    query.get_all_parent_artifacts = mocker.Mock(return_value=mock_parent_artifacts)
    
    # Step 2: Mock store.get_events_by_artifact_ids
    # The implementation calls get_events_by_artifact_ids with all artifact IDs at once
    mock_event1 = mocker.Mock()
    mock_event1.execution_id = 201
    mock_event1.type = mlpb.Event.OUTPUT
    
    mock_event2 = mocker.Mock()
    mock_event2.execution_id = 202
    mock_event2.type = mlpb.Event.OUTPUT
    
    # Mock to return both events when called with both artifact IDs
    mock_store.get_events_by_artifact_ids.return_value = [mock_event1, mock_event2]
    
    # Step 3: Mock store.get_executions_by_id
    mock_execution1 = mocker.Mock()
    mock_execution1.id = 201
    mock_execution1.name = "parent_execution1"
    mock_execution1.properties = {"Execution_type_name": mocker.Mock(string_value="type1")}
    
    mock_execution2 = mocker.Mock()
    mock_execution2.id = 202
    mock_execution2.name = "parent_execution2"
    mock_execution2.properties = {"Execution_type_name": mocker.Mock(string_value="type2")}
    
    # The implementation calls get_executions_by_id with all execution IDs at once
    mock_store.get_executions_by_id.return_value = [mock_execution1, mock_execution2]
    
    # Step 4: Mock _transform_to_dataframe
    df1 = pd.DataFrame([{
        'id': 201,
        'name': 'parent_execution1',
        'Execution_type_name': 'type1'
    }])
    
    df2 = pd.DataFrame([{
        'id': 202,
        'name': 'parent_execution2',
        'Execution_type_name': 'type2'
    }])
    
    # Create a combined DataFrame that will be returned by the mocked pd.concat
    combined_df = pd.DataFrame([
        {
            'id': 201,
            'name': 'parent_execution1',
            'Execution_type_name': 'type1'
        },
        {
            'id': 202,
            'name': 'parent_execution2',
            'Execution_type_name': 'type2'
        }
    ])
    
    # Mock _transform_to_dataframe to return the appropriate DataFrame based on execution ID
    # Side effect is needed so each call returns the correct DataFrame for the corresponding execution.
    def transform_side_effect(execution, *args, **kwargs):
        if execution.id == 201:
            return df1
        elif execution.id == 202:
            return df2
    
    query._transform_to_dataframe = mocker.Mock(side_effect=transform_side_effect)
    
    # Mock pandas.concat to return our combined DataFrame
    mocker.patch('pandas.concat', return_value=combined_df)
    
    # Step 5: Call the method under test
    result = query.get_all_parent_executions("child_artifact")
    
    # Step 6: Assert the result
    assert len(result) == 2
    assert "id" in result.columns
    assert "name" in result.columns
    assert "Execution_type_name" in result.columns
    
    # Check first execution
    first_row = result[result["id"] == 201].iloc[0]
    assert first_row["name"] == "parent_execution1"
    assert first_row["Execution_type_name"] == "type1"
    
    # Check second execution
    second_row = result[result["id"] == 202].iloc[0]
    assert second_row["name"] == "parent_execution2"
    assert second_row["Execution_type_name"] == "type2"
    
    # Step 7: Verify method calls
    query.get_all_parent_artifacts.assert_called_once_with("child_artifact")
    # The implementation calls get_events_by_artifact_ids with all artifact IDs at once
    mock_store.get_events_by_artifact_ids.assert_called_once_with([101, 102])
    # The implementation calls get_executions_by_id with all execution IDs at once
    mock_store.get_executions_by_id.assert_called_once_with({201, 202})
    
    # Verify that _transform_to_dataframe was called twice (once for each execution)
    assert query._transform_to_dataframe.call_count == 2


def test_find_producer_execution(query_fixture, mocker):
    """
    Test finding the producer execution for a given artifact.

    Flow:
        find_producer_execution
            -> _get_artifact (resolve artifact name to artifact object)
            -> store.get_events_by_artifact_ids (fetch OUTPUT events for the artifact)
            -> store.get_executions_by_id (fetch execution for the OUTPUT event)
            -> return the producer execution object
    """
    query, mock_store = query_fixture
    
    # Step 1: Mock _get_artifact
    mock_artifact = mocker.Mock()
    mock_artifact.id = 100
    mock_artifact.name = "artifact1"
    
    query._get_artifact = mocker.Mock(return_value=mock_artifact)
    
    # Step 2: Mock get_events_by_artifact_ids
    # Create a mock event with OUTPUT type
    mock_output_event = mocker.Mock()
    mock_output_event.execution_id = 200
    mock_output_event.type = mlpb.Event.OUTPUT
    
    # Create a mock event with INPUT type (should be ignored)
    mock_input_event = mocker.Mock()
    mock_input_event.execution_id = 300
    mock_input_event.type = mlpb.Event.INPUT
    
    # Return both events when get_events_by_artifact_ids is called
    mock_store.get_events_by_artifact_ids.return_value = [mock_output_event, mock_input_event]
    
    # Step 3: Mock get_executions_by_id
    mock_execution = mocker.Mock()
    mock_execution.id = 200
    mock_execution.name = "producer_execution"
    
    mock_store.get_executions_by_id.return_value = [mock_execution]
    
    # Step 4: Call the method under test
    result = query.find_producer_execution("artifact1")
    
    # Step 5: Assert the result
    assert result is not None
    assert result.id == 200
    assert result.name == "producer_execution"
    
    # Step 6: Verify method calls
    query._get_artifact.assert_called_once_with("artifact1")
    mock_store.get_events_by_artifact_ids.assert_called_once_with([100])
    mock_store.get_executions_by_id.assert_called_once_with({200})
    
    # Step 7: Test case where artifact is not found
    query._get_artifact.reset_mock()
    query._get_artifact.return_value = None
    
    result = query.find_producer_execution("non_existent_artifact")
    
    assert result is None
    query._get_artifact.assert_called_once_with("non_existent_artifact")
    
    # Step 8: Test case where no OUTPUT events are found
    query._get_artifact.reset_mock()
    query._get_artifact.return_value = mock_artifact
    
    mock_store.get_events_by_artifact_ids.reset_mock()
    mock_store.get_events_by_artifact_ids.return_value = [mock_input_event]  # Only INPUT event
    
    result = query.find_producer_execution("artifact1")
    
    assert result is None
    query._get_artifact.assert_called_once_with("artifact1")
    mock_store.get_events_by_artifact_ids.assert_called_once_with([100])
    # get_executions_by_id should not be called since no OUTPUT events were found
    assert mock_store.get_executions_by_id.call_count == 1  # Still 1 from previous call


def test_get_metrics(query_fixture, monkeypatch):
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
    query, mock_store = query_fixture
    
    # Step 1: Mock the return value of `get_artifacts_by_type`
    mock_metric = mock_store.Mock()
    mock_metric.name = "accuracy_metrics"
    
    # Create a mock for the Name property
    mock_name = mock_store.Mock()
    mock_name.string_value = "path/to/metrics.parquet"
    mock_metric.custom_properties = {"Name": mock_name}
    
    mock_store.get_artifacts_by_type.return_value = [mock_metric]
    
    # Step 2: Create a mock DataFrame to return
    mock_df = pd.DataFrame({"metric": ["accuracy"], "value": [0.95]})
    
    # Step 3: Use monkeypatch to mock pd.read_parquet to always return our mock_df
    # regardless of the input path
    def mock_read_parquet(path):
        return mock_df
    
    monkeypatch.setattr(pd, "read_parquet", mock_read_parquet)
    
    # Step 4: Call the method under test
    result = query.get_metrics("accuracy_metrics")
    
    # Step 5: Assert the result is correct
    assert result is not None
    assert len(result) == 1
    assert "metric" in result.columns
    assert "value" in result.columns
    assert result.iloc[0]["metric"] == "accuracy"
    assert result.iloc[0]["value"] == 0.95
    
    # Step 6: Verify method calls
    mock_store.get_artifacts_by_type.assert_called_once_with("Step_Metrics")
    
    # Test case where metrics artifact is not found
    mock_store.get_artifacts_by_type.reset_mock()
    mock_store.get_artifacts_by_type.return_value = []
    
    result = query.get_metrics("nonexistent_metrics")
    assert result is None
    mock_store.get_artifacts_by_type.assert_called_once_with("Step_Metrics")


def test_get_one_hop_parent_artifacts_with_id(query_fixture, mocker):
    """
    Test retrieving one-hop parent artifacts for a given artifact ID.

    Flow:
        get_one_hop_parent_artifacts_with_id
            -> _get_executions_by_output_artifact_id (find executions that produced the given artifact)
            -> _get_input_artifacts (find input artifact IDs for those executions)
            -> store.get_artifacts_by_id (fetch artifact objects for those IDs)
            -> get_artifact_df (convert each artifact to DataFrame)
            -> pd.concat (combine all artifact DataFrames into a single DataFrame)
    """
    query, mock_store = query_fixture
    
    # Step 1: Mock the return value of `_get_executions_by_output_artifact_id`
    query._get_executions_by_output_artifact_id = mocker.Mock(return_value=[100, 101])

    # Step 2: Mock the return value of `_get_input_artifacts`
    query._get_input_artifacts = mocker.Mock(return_value=[200, 201])

    # Step 3: Mock the return value of `get_artifacts_by_id`
    mock_artifact1 = mocker.Mock()
    mock_artifact1.id = 200
    mock_artifact1.name = "parent_artifact1"
    mock_artifact1.type_id = 1
    mock_artifact1.uri = "uri1"
    mock_artifact1.create_time_since_epoch = 1234567890
    mock_artifact1.last_update_time_since_epoch = 1234567891

    mock_artifact2 = mocker.Mock()
    mock_artifact2.id = 201
    mock_artifact2.name = "parent_artifact2"
    mock_artifact2.type_id = 2
    mock_artifact2.uri = "uri2"
    mock_artifact2.create_time_since_epoch = 1234567892
    mock_artifact2.last_update_time_since_epoch = 1234567893

    mock_store.get_artifacts_by_id.return_value = [mock_artifact1, mock_artifact2]

    # Step 4: Mock the `get_artifact_df` method
    # Create DataFrames for each artifact
    df1 = pd.DataFrame([{
        "id": 200,
        "name": "parent_artifact1",
        "type": "Type1",
        "uri": "uri1",
        "create_time_since_epoch": 1234567890,
        "last_update_time_since_epoch": 1234567891
    }])
    
    df2 = pd.DataFrame([{
        "id": 201,
        "name": "parent_artifact2",
        "type": "Type2",
        "uri": "uri2",
        "create_time_since_epoch": 1234567892,
        "last_update_time_since_epoch": 1234567893
    }])
    
    # Mock get_artifact_df to return the appropriate DataFrame based on the artifact ID
    # Side effect is needed so each call returns the correct DataFrame for the corresponding artifact,
    # simulating the real method which processes each artifact separately.
    def get_artifact_df_side_effect(artifact, extra_props=None):
        if artifact.id == 200:
            return df1
        elif artifact.id == 201:
            return df2
        return pd.DataFrame()
    
    query.get_artifact_df = mocker.Mock(side_effect=get_artifact_df_side_effect)

    # Step 5: Call the method under test
    parent_artifacts_df = query.get_one_hop_parent_artifacts_with_id(300)

    # Step 6: Assert the result
    assert len(parent_artifacts_df) == 2
    assert "id" in parent_artifacts_df.columns
    assert "name" in parent_artifacts_df.columns
    assert "type" in parent_artifacts_df.columns
    
    # Check first parent artifact
    first_row = parent_artifacts_df[parent_artifacts_df["id"] == 200].iloc[0]
    assert first_row["name"] == "parent_artifact1"
    assert first_row["type"] == "Type1"
    assert first_row["uri"] == "uri1"
    
    # Check second parent artifact
    second_row = parent_artifacts_df[parent_artifacts_df["id"] == 201].iloc[0]
    assert second_row["name"] == "parent_artifact2"
    assert second_row["type"] == "Type2"
    assert second_row["uri"] == "uri2"

    # Step 7: Verify method calls
    query._get_executions_by_output_artifact_id.assert_called_once_with(300)
    query._get_input_artifacts.assert_called_once_with([100, 101])
    mock_store.get_artifacts_by_id.assert_called_once_with([200, 201])
    
    # Verify that get_artifact_df was called for each artifact
    assert query.get_artifact_df.call_count == 2
    query.get_artifact_df.assert_any_call(mock_artifact1)
    query.get_artifact_df.assert_any_call(mock_artifact2)


def test_get_all_executions_for_artifact_id(query_fixture, mocker):
    """Test retrieving all executions for a given artifact ID.
    
    Flow:
        get_all_executions_for_artifact_id
            -> store.get_events_by_artifact_ids (fetch all events for the artifact)
            -> store.get_executions_by_id (fetch executions for each event)
            -> store.get_contexts_by_execution (fetch stage/context for each execution)
            -> store.get_parent_contexts_by_context (fetch pipeline context for each stage)
            -> build DataFrame with execution and context details
            -> return DataFrame with execution, stage, and pipeline info
    """
    query, mock_store = query_fixture
    
    # Step 1: Mock the return value of `get_events_by_artifact_ids`
    mock_event1 = mocker.Mock()
    mock_event1.execution_id = 100
    mock_event1.type = mlpb.Event.Type.INPUT

    mock_event2 = mocker.Mock()
    mock_event2.execution_id = 101
    mock_event2.type = mlpb.Event.Type.OUTPUT
    
    mock_store.get_events_by_artifact_ids.return_value = [mock_event1, mock_event2]
    
    # Step 2: Mock the return value of `get_contexts_by_execution`
    mock_stage_context1 = mocker.Mock()
    mock_stage_context1.id = 10
    mock_stage_context1.name = "stage1"
    
    mock_stage_context2 = mocker.Mock()
    mock_stage_context2.id = 11
    mock_stage_context2.name = "stage2"
    
    # Mock get_contexts_by_execution to return the appropriate context based on execution ID.
    # Side effect is needed here to simulate different stage contexts for each execution ID.
    # This ensures that when get_contexts_by_execution is called with a specific execution_id,
    # it returns the correct mock stage context for that execution, as expected by the test logic.
    def get_contexts_by_execution_side_effect(execution_id):
        if execution_id == 100:
            return [mock_stage_context1]
        elif execution_id == 101:
            return [mock_stage_context2]
        return []
    
    mock_store.get_contexts_by_execution = mocker.Mock(side_effect=get_contexts_by_execution_side_effect)
    
    # Step 3: Mock the return value of `get_executions_by_id`
    mock_execution1 = mocker.Mock()
    mock_execution1.id = 100
    mock_execution1.name = "execution1"
    mock_execution1.properties = {"Execution_type_name": mocker.Mock(string_value="type1")}
    
    mock_execution2 = mocker.Mock()
    mock_execution2.id = 101
    mock_execution2.name = "execution2"
    mock_execution2.properties = {"Execution_type_name": mocker.Mock(string_value="type2")}
    
    mock_store.get_executions_by_id.return_value = [mock_execution1, mock_execution2]
    
    # Step 4: Mock the return value of `get_parent_contexts_by_context`
    mock_pipeline_context1 = mocker.Mock()
    mock_pipeline_context1.name = "pipeline1"
    
    mock_pipeline_context2 = mocker.Mock()
    mock_pipeline_context2.name = "pipeline2"
    
    # Mock get_parent_contexts_by_context to return the appropriate pipeline context
    # Side effect is needed here to simulate different parent pipeline contexts for each stage context ID.
    # This ensures that when get_parent_contexts_by_context is called with a specific context_id,
    # it returns the correct pipeline context for that stage, matching the test's expectations.
    def get_parent_contexts_by_context_side_effect(context_id):
        if context_id == 10:
            return [mock_pipeline_context1]
        elif context_id == 11:
            return [mock_pipeline_context2]
        return []
    
    mock_store.get_parent_contexts_by_context = mocker.Mock(side_effect=get_parent_contexts_by_context_side_effect)
    
    # Step 5: Call the method under test
    result = query.get_all_executions_for_artifact_id(200)
    
    # Step 6: Assert the result
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2  # Two events should result in two rows
    
    # Step 7: Check columns and values
    assert "execution_id" in result.columns
    assert "Type" in result.columns
    assert "execution_name" in result.columns
    assert "execution_type_name" in result.columns
    assert "stage" in result.columns
    assert "pipeline" in result.columns
    
    # Sort the DataFrame by execution_id to ensure consistent order for testing
    result = result.sort_values("execution_id")
