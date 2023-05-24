from cmflib import cmfquery
import pandas as pd


def get_executions(mlmdfilepath, pipeline_name):
    query = cmfquery.CmfQuery(mlmdfilepath)
    stages = query.get_pipeline_stages(pipeline_name)
    df = pd.DataFrame()
    for stage in stages:
        executions = query.get_all_executions_in_stage(stage)
        if str(executions.Pipeline_Type[0]) == pipeline_name:
            df = pd.concat([df, executions], sort=True, ignore_index=True)
    return df


# This function fetches all the artifacts available in given mlmd
def get_artifacts(mlmdfilepath, pipeline_name,data):
    query = cmfquery.CmfQuery(mlmdfilepath)
    names = query.get_pipeline_names()  # getting all pipeline names in mlmd
    identifiers = []
    for name in names:
        if name==pipeline_name:
            stages = query.get_pipeline_stages(name)
            for stage in stages:
                executions = query.get_all_executions_in_stage(stage)
                dict_executions = executions.to_dict("dict")  # converting it to dictionary
                identifiers.append(dict_executions['id'][0])

    name = []
    url = []
    df = pd.DataFrame()
    for identifier in identifiers:
        get_artifacts = query.get_all_artifacts_for_execution(identifier)  # getting all artifacts
        artifacts_dict = get_artifacts.to_dict('dict')  # converting it to dictionary
        df = pd.concat([df, get_artifacts], sort=True, ignore_index=True)
    if data=="artifact_type":
        df=list(set(df['type']))
    else:
        df=df.loc[df['type'] == data]
    return df



