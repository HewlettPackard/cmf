import requests

def test_display_pipelines():
    url = "http://10.93.244.204:3000/display_pipelines"
    response = requests.get(url)
    assert response.status_code == 200
    assert "Test-env" in response.json()
