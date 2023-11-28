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

        with open("test-data/executions.json", "r") as file:
            expected_content = json.load(file)

        # Check that the response JSON content matches the expected content
        assert response.json() == expected_content

def test_display_artifacts():
    with TestClient(app) as c:
        response = c.get("/display_artifacts/"+pipeline_name+"/Dataset")
        assert response.status_code == 200
        with open("test-data/artifacts.json", "r") as file:
            expected_content = json.load(file)

        # Check that the response JSON content matches the expected content
        assert response.json() == expected_content


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

