import requests
import json

#This function posts mlmd data to mlmd_push api on cmf-server
def call_mlmd_push(json_payload, url, exec_id):
    url_to_pass = f"{url}/mlmd_push"
    json_data = {"id": exec_id, "json_payload": json_payload}
    response = requests.post(url_to_pass, json=json_data)           #Post request
    # print("Status code -", response.status_code)
    return response

#This function gets mlmd data from mlmd_pull api from cmf-server
def call_mlmd_pull(url,pipeline_name):
    url_to_pass = f"{url}/mlmd_pull/{pipeline_name}"
    response = requests.get(url_to_pass)                            #Get request
    return response
