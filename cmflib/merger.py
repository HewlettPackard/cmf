from cmflib import cmf
import json


def parse_json_to_mlmd(mlmd_json):
    mlmd_data = json.loads(mlmd_json)
    type(mlmd_data)
    pipelines = mlmd_data["Pipeline"]
    print(type(pipelines))
    pipeline = pipelines[0]
    print(type(pipeline))
    pipeline_name = pipeline["name"]
    print(type(pipeline_name))
    cmf_class = cmf.Cmf(filename="mlmd", pipeline_name=pipeline_name)
    for stage in mlmd_data['Pipeline'][0]['stages']:
        _ = cmf_class.create_context(pipeline_stage=stage['name'], custom_properties=stage['custom_properties'])
        print(stage['name'])
        for execution in stage['executions']:
            print(execution['type'])
            _ = cmf_class.merge_created_execution(execution['type'], execution['properties']['Execution'], execution['custom_properties'])
            for event in execution['events']:
                artifact_type = event['artifact']['type']
                event_type = event['type']
                artifact_name = (event['artifact']['name'].split(':'))[0]
                custom_props = event['artifact']['custom_properties']
                props = event['artifact']['properties']
                uri = event['artifact']['uri']
                if artifact_type == "Dataset" and event_type == 3:
                    uri = event['artifact']['uri']
                    git_repo_props = props['git_repo']
                    artifact_full_path = f"{git_repo_props}/{artifact_name}"
                    print(artifact_full_path)
                    cmf_class.log_dataset_with_version(artifact_full_path, uri,  "input", custom_properties=custom_props)
                elif artifact_type == "Dataset" and event_type == 4:
                    uri = event['artifact']['uri']
                    git_repo_props = props['git_repo']
                    artifact_full_path = f"{git_repo_props}/{artifact_name}"
                    print(artifact_full_path)
                    cmf_class.log_dataset_with_version(artifact_full_path, uri,  "output",
                      custom_properties=custom_props)
                elif artifact_type == "Model" and event_type == 3:
                    # uri = event['artifact']['uri']
                    # props["uri"] = uri
                    # model_framework = props['model_framework']
                    # model_type = props['model_type']
                    # model_name = props['model_name']
                    cmf_class.log_model_with_version(path=artifact_name, event="input",props=props,
                     custom_properties=props)
                elif artifact_type == "Model" and event_type == 4:
                    # uri = event['artifact']['uri']
                    # props["uri"] = uri
                    # model_framework = props['model_framework']
                    # model_type = props['model_type']
                    # model_name = props['model_name']
                    # #print(props[""])
                    # #props["uri"] = props
                    # print(model_framework)
                    # print(model_type)
                    # print(model_name)
                    # print(artifact_name)
                    # print(type(artifact_name))
                    cmf_class.log_model_with_version(path=artifact_name, event="output", props=props,
                     custom_properties=props)
                elif artifact_type == "Metrics":
                    cmf_class.log_execution_metrics(artifact_name, custom_props)
                else:
                    pass



if __name__ == "__main__":
    pass
