import json
from fastapi.testclient import TestClient
from server.app.main import app


client = TestClient(app)
pipeline_name = "Test-env"
artifact_type = "Dataset"

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == ["cmf-server"]


def test_display_executions():
    with TestClient(app) as c:
        response = c.get("/display_executions/" + pipeline_name)
        assert response.status_code == 200

        # Load executions from the inpute test-data/executions.json file
        with open("test-data/executions.json", "r") as file:
            expected_content = json.load(file)

        # Remove these keys from the json data
        keys_to_remove = ["Execution_uuid", "max_features", "min_split",
                "n_est", "ngrams", "original_create_time_since_epoch",
                "seed", "split", "Git_Start_Commit"]

        # Remove the specified keys from each item
        filtered_expected = {"total_items": expected_content["total_items"], "items": []}
        for item in expected_content["items"]:
            filtered_item = {key: value for key, value in item.items() if key not in keys_to_remove}
            filtered_expected["items"].append(filtered_item)

        # remove the above keys from response data
        response = response.json()

        # Remove the specified keys from each item
        filtered_response = {"total_items": response["total_items"], "items": []}
        for item in response["items"]:
            filtered_item = {key: value for key, value in item.items() if key not in keys_to_remove}
            filtered_response["items"].append(filtered_item)

        #print("filtered_response", filtered_response)

        assert filtered_response == filtered_expected

def test_display_artifacts():
    with TestClient(app) as c:
        response = c.get("/display_artifacts/"+pipeline_name+"/Dataset")
        assert response.status_code == 200
        with open("test-data/artifacts.json", "r") as file:
            expected_content = json.load(file)

        # Remove these keys from the json data
        keys_to_remove = ["Commit", "create_time_since_epoch", "last_update_time_since_epoch",
                "original_create_time_since_epoch", "url"]

        # Remove the specified keys from each item
        filtered_expected = {"total_items": expected_content["total_items"], "items": []}
        for item in expected_content["items"]:
            filtered_item = {key: value for key, value in item.items() if key not in keys_to_remove}
            filtered_expected["items"].append(filtered_item)

        #print("filtered_expected", filtered_expected)

        # remove the above keys from response data
        response = response.json()

        # Remove the specified keys from each item
        filtered_response = {"total_items": response["total_items"], "items": []}
        for item in response["items"]:
            filtered_item = {key: value for key, value in item.items() if key not in keys_to_remove}
            filtered_response["items"].append(filtered_item)

        assert filtered_response == filtered_expected


def test_display_lineage():
    with TestClient(app) as c:
        response = client.get("/display_lineage/" + pipeline_name)
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"


def test_display_artifact_types():
    response = client.get("/display_artifact_types")
    assert response.status_code == 200
    assert response.json() == ['Dataset', 'Model', 'Metrics']

def test_display_pipelines():
    response = client.get("/display_pipelines")
    assert response.status_code == 200
    assert response.json() == ["Test-env"]

