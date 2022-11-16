import requests
import json


def call_mlmd_push(json_payload, url):
    url_to_pass = f"{url}/mlmd_push"
    x = requests.post(url_to_pass, json=json_payload)
    # print(x.json())
    print("Status code -", x.status_code)

def call_mlmd_pull(url):
    url_to_pass = f"{url}/mlmd_pull"
    mlmd_file_data=requests.get(url_to_pass)
    return mlmd_file_data

