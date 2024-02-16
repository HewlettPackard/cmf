###
# Copyright (2022) Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###

import json
import os
from cmflib import cmf


# mlmd is created from metadata passed in Json format
def parse_json_to_mlmd(mlmd_json, path_to_store, cmd, exec_id):
    mlmd_data = json.loads(mlmd_json)
    # type(mlmd_data)
    pipelines = mlmd_data["Pipeline"]
    # print(type(pipelines))
    pipeline = pipelines[0]
    # print(type(pipeline))
    pipeline_name = pipeline["name"]
    # print(type(pipeline_name))
    stage = {}
    if cmd == "push":
        data = create_original_time_since_epoch(mlmd_data)
    else:
        data = mlmd_data
    graph = False
    if os.getenv('NEO4J_URI', "") != "":
        graph = True
    cmf_class = cmf.Cmf(filename=path_to_store, pipeline_name=pipeline_name,
                        graph=graph, is_server=True)
    for stage in data["Pipeline"][0]["stages"]:  # Iterates over all the stages
        if exec_id is None:
            list_executions = [execution for execution in stage["executions"]]
        elif exec_id is not None:
            list_executions = [
                execution
                for execution in stage["executions"]
                if execution["id"] == int(exec_id)
            ]
        else:
            return "Invalid execution id given."

        for execution in list_executions:  # Iterates over all the executions
            _ = cmf_class.merge_created_context(
            pipeline_stage = stage['name'],
            custom_properties = stage["custom_properties"],
            )
            _ = cmf_class.merge_created_execution(
                execution["properties"]["Context_Type"],
                execution["properties"]["Execution"],
                execution["properties"],
                execution["custom_properties"],
                execution["name"]
            )
            for event in execution["events"]:  # Iterates over all the events
                artifact_type = event["artifact"]["type"]
                event_type = event["type"]
                artifact_name = (event["artifact"]["name"].split(":"))[0]
                custom_props = event["artifact"]["custom_properties"]
                props = event["artifact"]["properties"]
                # print(props,'props')
                uri = event["artifact"]["uri"]
                if artifact_type == "Dataset" and event_type == 3:
                    cmf_class.log_dataset_with_version(
                        artifact_name,
                        uri,
                        "input",
                        props,
                        custom_properties=custom_props,
                    )
                elif artifact_type == "Dataset" and event_type == 4:
                    cmf_class.log_dataset_with_version(
                        artifact_name,
                        uri,
                        "output",
                        props,
                        custom_properties=custom_props,
                    )
                elif artifact_type == "Model" and event_type == 3:
                    props["uri"] = uri
                    cmf_class.log_model_with_version(
                        path=artifact_name,
                        event="input",
                        props=props,
                        custom_properties=custom_props,
                    )
                elif artifact_type == "Model" and event_type == 4:
                    props["uri"] = uri
                    cmf_class.log_model_with_version(
                        path=artifact_name,
                        event="output",
                        props=props,
                        custom_properties=custom_props,
                    )
                elif artifact_type == "Metrics":
                    # print(props,'parse')
                    cmf_class.log_execution_metrics_from_client(event["artifact"]["name"], custom_props)
                elif artifact_type == "Dataslice":
                    dataslice = cmf_class.create_dataslice(event["artifact"]["name"])
                    dataslice.commit_existing(uri, custom_props)
                elif artifact_type == "Step_Metrics":
                    cmf_class.commit_existing_metrics(event["artifact"]["name"], uri, custom_props)
                else:
                    pass


# create_time_since_epoch is appended to mlmd pushed to cmf-server as original_create_time_since_epoch
def create_original_time_since_epoch(mlmd_data):
    stages = []
    execution = []
    artifact = []
    original_stages = []
    original_execution = []
    original_artifact = []
    mlmd_data["Pipeline"][0]["original_create_time_since_epoch"] = mlmd_data[
        "Pipeline"
    ][0]["create_time_since_epoch"]
    for i in mlmd_data["Pipeline"][0]["stages"]:
        i["custom_properties"]["original_create_time_since_epoch"] = i[
            "create_time_since_epoch"
        ]
        original_stages.append(
            i["custom_properties"]["original_create_time_since_epoch"]
        )
        stages.append(i["create_time_since_epoch"])
        # print(i['custom_properties']['original_create_time_since_epoch'])
        for j in i["executions"]:
            j["custom_properties"]["original_create_time_since_epoch"] = j[
                "create_time_since_epoch"
            ]
            original_execution.append(
                j["custom_properties"]["original_create_time_since_epoch"]
            )
            execution.append(j["create_time_since_epoch"])
            # print(j['custom_properties']['original_create_time_since_epoch'])
            for k in j["events"]:
                k["artifact"]["custom_properties"][
                    "original_create_time_since_epoch"
                ] = k["artifact"]["create_time_since_epoch"]
                original_artifact.append(
                    k["artifact"]["custom_properties"][
                        "original_create_time_since_epoch"
                    ]
                )
                artifact.append(k["artifact"]["create_time_since_epoch"])
                # print(k['artifact']['custom_properties']['original_create_time_since_epoch'])

    return mlmd_data



