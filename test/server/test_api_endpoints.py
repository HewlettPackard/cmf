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

        print(expected_content)

        # Remove these keys from the json data 
        keys_to_remove = ["Execution_uuid", "max_features", "min_split",
                "n_est", "ngrams", "original_create_time_since_epoch",
                "seed", "split"]

        # remove the above keys from json data
        for index in sorted(keys_to_remove, reverse=True):
            del expected_content[index]

        # remove the above keys from response data
        response = response.json()
        print(response)

        for index in sorted(keys_to_remove, reverse=True):
            del response[index]

        # Check that the response  content matches the expected content
        assert response == expected_content

def test_display_artifacts():
    with TestClient(app) as c:
        response = c.get("/display_artifacts/"+pipeline_name+"/Dataset")
        assert response.status_code == 200
        with open("test-data/artifacts.json", "r") as file:
            expected_content = json.load(file)

        print(expected_content)
        # Remove these keys from the json data
        keys_to_remove = ["Commit", "create_time_since_epoch", "last_update_time_since_epoch",
                "original_create_time_since_epoch"]

        # remove the above keys from json data
        for index in sorted(keys_to_remove, reverse=True):
            del expected_content[index]

        # remove the above keys from response data
        response = response.json()
        print(response)

        for index in sorted(keys_to_remove, reverse=True):
            del response[index]

        # Check that the response  content matches the expected content
        assert response == expected_content


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

