import requests
import json


def call_mlmd_push(json_payload, url):
    url_to_pass = f"{url}/mlmd_push"
    x = requests.post(url_to_pass, json=json_payload)
    # print(x.json())
    print("Status code -", x.status_code)
