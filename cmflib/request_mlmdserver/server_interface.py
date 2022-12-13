import requests
import json


def call_mlmd_push(json_payload, url, exec_id):
    url_to_pass = f"{url}/mlmd_push"
    json_data = {"id": exec_id, "json_payload": json_payload}
    output = requests.post(url_to_pass, json=json_data)
    # print(x.json())
    print("Status code -", output.status_code)
    return output.status_code


def call_mlmd_pull(url):
    url_to_pass = f"{url}/mlmd_pull"
    output = requests.get(url_to_pass)
    return output
