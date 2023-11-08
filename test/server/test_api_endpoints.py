from fastapi.testclient import TestClient
from server.app.main import app


client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == ["cmf-server"]


def test_display_executions():
    with TestClient(app) as c:
        response = c.get("/display_executions/Test-env")
        assert response.status_code == 200
        assert response.json() == {'total_items': 4, 'items': [{'Context_ID': 2, 'Context_Type': 'Test-env/Prepare', 'Execution': "['src/parse.py', 'artifacts/data.xml.gz', 'artifacts/parsed']", 'Execution_type_name': 'Test-env/Prepare', 'Execution_uuid': '1afa7676-76f6-11ee-9600-5b8c6d427e3f', 'Git_End_Commit': '', 'Git_Repo': 'https://github.com/varkha-d-sharma/experiment-repo.git', 'Git_Start_Commit': '44bf2ad09d89e24693c8e98b8da8fcecb248fb77', 'Pipeline_Type': 'Test-env', 'Pipeline_id': 1, 'max_features': None, 'min_split': None, 'n_est': None, 'ngrams': None, 'original_create_time_since_epoch': 1698650988149, 'seed': 20170428.0, 'split': 0.2}, {'Context_ID': 3, 'Context_Type': 'Test-env/Featurize', 'Execution': "['src/featurize.py', 'artifacts/parsed', 'artifacts/features']", 'Execution_type_name': 'Test-env/Featurize', 'Execution_uuid': '25c66fa6-76f6-11ee-9600-5b8c6d427e3f', 'Git_End_Commit': '', 'Git_Repo': 'https://github.com/varkha-d-sharma/experiment-repo.git', 'Git_Start_Commit': '44bf2ad09d89e24693c8e98b8da8fcecb248fb77', 'Pipeline_Type': 'Test-env', 'Pipeline_id': 1, 'max_features': 3000.0, 'min_split': None, 'n_est': None, 'ngrams': 2.0, 'original_create_time_since_epoch': 1698651006263, 'seed': None, 'split': None}, {'Context_ID': 4, 'Context_Type': 'Test-env/Train', 'Execution': "['src/train.py', 'artifacts/features', 'artifacts/model']", 'Execution_type_name': 'Test-env/Train', 'Execution_uuid': '3f6f2db2-76f6-11ee-9600-5b8c6d427e3f', 'Git_End_Commit': '', 'Git_Repo': 'https://github.com/varkha-d-sharma/experiment-repo.git', 'Git_Start_Commit': '44bf2ad09d89e24693c8e98b8da8fcecb248fb77', 'Pipeline_Type': 'Test-env', 'Pipeline_id': 1, 'max_features': None, 'min_split': 64.0, 'n_est': 100.0, 'ngrams': None, 'original_create_time_since_epoch': 1698651049311, 'seed': 20170428.0, 'split': None}, {'Context_ID': 5, 'Context_Type': 'Test-env/Evaluate', 'Execution': "['src/test.py', 'artifacts/model', 'artifacts/features', 'artifacts/test_results']", 'Execution_type_name': 'Test-env/Evaluate', 'Execution_uuid': '48ad70d2-76f6-11ee-9600-5b8c6d427e3f', 'Git_End_Commit': '', 'Git_Repo': 'https://github.com/varkha-d-sharma/experiment-repo.git', 'Git_Start_Commit': '44bf2ad09d89e24693c8e98b8da8fcecb248fb77', 'Pipeline_Type': 'Test-env', 'Pipeline_id': 1, 'max_features': None, 'min_split': None, 'n_est': None, 'ngrams': None, 'original_create_time_since_epoch': 1698651064817, 'seed': None, 'split': None}]}

def test_display_artifacts():
    with TestClient(app) as c1:
        response = c1.get("/display_artifacts/Test-env/Dataset")
        assert response.status_code == 200
        assert response.json() == {'total_items': 5, 'items': [{'Commit': '236d9502e0283d91f689d7038b8508a2', 'create_time_since_epoch': 1698651255805, 'git_repo': 'https://github.com/varkha-d-sharma/experiment-repo.git', 'id': 1, 'last_update_time_since_epoch': 1698651255805, 'name': 'artifacts/data.xml.gz', 'original_create_time_since_epoch': 1698650991666, 'type': 'Dataset', 'uri': '236d9502e0283d91f689d7038b8508a2', 'url': 'Test-env:/home/sharvark/local-storage/23/6d9502e0283d91f689d7038b8508a2', 'user-metadata1': 'metadata_value', 'execution_type_name': 'Test-env/Prepare'}, {'Commit': '32b715ef0d71ff4c9e61f55b09c15e75', 'create_time_since_epoch': 1698651255838, 'git_repo': 'https://github.com/varkha-d-sharma/experiment-repo.git', 'id': 2, 'last_update_time_since_epoch': 1698651255838, 'name': 'artifacts/parsed/train.tsv', 'original_create_time_since_epoch': 1698650998240, 'type': 'Dataset', 'uri': '32b715ef0d71ff4c9e61f55b09c15e75', 'url': 'Test-env:/home/sharvark/local-storage/32/b715ef0d71ff4c9e61f55b09c15e75', 'user-metadata1': None, 'execution_type_name': 'Test-env/Prepare,\n Test-env/Featurize'}, {'Commit': '6f597d341ceb7d8fbbe88859a892ef81', 'create_time_since_epoch': 1698651255871, 'git_repo': 'https://github.com/varkha-d-sharma/experiment-repo.git', 'id': 3, 'last_update_time_since_epoch': 1698651255871, 'name': 'artifacts/parsed/test.tsv', 'original_create_time_since_epoch': 1698651001110, 'type': 'Dataset', 'uri': '6f597d341ceb7d8fbbe88859a892ef81', 'url': 'Test-env:/home/sharvark/local-storage/6f/597d341ceb7d8fbbe88859a892ef81', 'user-metadata1': None, 'execution_type_name': 'Test-env/Prepare,\n Test-env/Featurize'}, {'Commit': '4b0798de5dd985eedbb0afee78b9e5aa', 'create_time_since_epoch': 1698651256009, 'git_repo': 'https://github.com/varkha-d-sharma/experiment-repo.git', 'id': 4, 'last_update_time_since_epoch': 1698651256009, 'name': 'artifacts/features/train.pkl', 'original_create_time_since_epoch': 1698651040135, 'type': 'Dataset', 'uri': '4b0798de5dd985eedbb0afee78b9e5aa', 'url': 'Test-env:/home/sharvark/local-storage/4b/0798de5dd985eedbb0afee78b9e5aa', 'user-metadata1': None, 'execution_type_name': 'Test-env/Prepare,\n Test-env/Featurize,\n Test-env/Train'}, {'Commit': 'd7bdfab860e2835ec9681fa9ebdce149', 'create_time_since_epoch': 1698651256041, 'git_repo': 'https://github.com/varkha-d-sharma/experiment-repo.git', 'id': 5, 'last_update_time_since_epoch': 1698651256041, 'name': 'artifacts/features/test.pkl', 'original_create_time_since_epoch': 1698651043625, 'type': 'Dataset', 'uri': 'd7bdfab860e2835ec9681fa9ebdce149', 'url': 'Test-env:/home/sharvark/local-storage/d7/bdfab860e2835ec9681fa9ebdce149', 'user-metadata1': None, 'execution_type_name': 'Test-env/Prepare,\n Test-env/Featurize,\n Test-env/Train,\n Test-env/Evaluate'}]}


def test_display_lineage():
    with TestClient(app) as c:
        response = client.get("/display_lineage/Test-env")
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

