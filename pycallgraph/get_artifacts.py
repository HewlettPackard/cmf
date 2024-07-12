from cmflib import cmf, cmfquery, cmf_merger
from pycallgraph2 import PyCallGraph
from pycallgraph2 import Config
from pycallgraph2.output import GraphvizOutput
from pycallgraph2 import GlobbingFilter
import pandas as pd
import typing as t
import json, glob
import os


def get_all_exe_ids(mlmdfilepath):
    '''
    Returns:
        returns a dictionary which has pipeline_name as key and dataframe which includes {id,Execution_uuid,Context_Type,Context_id} as value.
    '''

    query = cmfquery.CmfQuery(mlmdfilepath)
    execution_ids = {}
    names = query.get_pipeline_names()
    for name in names:
        df = pd.DataFrame()    # df is emptied to store execution ids for next pipeline.
        stages = query.get_pipeline_stages(name)
        for stage in stages:
            executions = query.get_all_executions_in_stage(stage)
            df = pd.concat([df, executions], sort=True, ignore_index=True)
    # check if df is empty return just pipeline_name: {}
    # if df is not empty return dictionary with pipeline_name as key 
    # and df with id, context_type, uuid, context_ID as value.
        if not df.empty:
            execution_ids[name] = df[['id', 'Context_Type', 'Execution_uuid', 'Context_ID']]
        else:
            execution_ids[name] = pd.DataFrame()
    return execution_ids


def get_all_artifact_ids(mlmdfilepath):
    # following is a dictionary of dictionary
    # First level dictionary key is pipeline_name
    # First level dicitonary value is nested dictionary
    # Nested dictionary key is type i.e. Dataset, Model, etc.
    # Nested dictionary value is ids i.e. set of integers
        artifact_ids = {}
        query = cmfquery.CmfQuery(mlmdfilepath)
        names = query.get_pipeline_names()
        execution_ids = get_all_exe_ids(mlmdfilepath)
        for name in names:
            df = pd.DataFrame()
            if not execution_ids.get(name).empty:
                exe_ids = execution_ids[name]['id'].tolist()
                for id in exe_ids:
                    artifacts = query.get_all_artifacts_for_execution(id)
                    df = pd.concat([df, artifacts], sort=True, ignore_index=True)
            #acknowledging pipeline exist even if df is empty. 
                if df.empty:
                    artifact_ids[name] = pd.DataFrame()   # { pipeline_name: {empty df} }
                else:
                    df.sort_values("id", inplace=True)
                    df.drop_duplicates(subset="id", keep='first', inplace=True)
                    artifact_ids[name] = {}
                    for art_type in df['type']:
                        filtered_values = df.loc[df['type'] == art_type, ['id', 'name']]
                        artifact_ids[name][art_type] = filtered_values
        # if execution_ids is empty create dictionary with key as pipeline name
        # and value as empty df
            else:
                artifact_ids[name] = pd.DataFrame()
        return artifact_ids


def get_artifact_types(mlmdfilepath):
        query = cmfquery.CmfQuery(mlmdfilepath)
        artifact_types = query.get_all_artifact_types()
        return artifact_types



def get_artifacts(mlmdfilepath, pipeline_name, art_type, artifact_ids):
        query = cmfquery.CmfQuery(mlmdfilepath)
        names = query.get_pipeline_names()  # getting all pipeline names in mlmd
        df = pd.DataFrame()
        for name in names:
            if name == pipeline_name:
                df = query.get_all_artifacts_by_ids_list(artifact_ids)
                if len(df) == 0:
                    return
                df = df.drop_duplicates()
                art_names = df['name'].tolist()
                name_dict = {}
                name_list = []
                exec_type_name_list = []
                exe_type_name = pd.DataFrame()
                for name in art_names:
                    executions = query.get_all_executions_for_artifact(name)
                    exe_type_name = pd.concat([exe_type_name, executions], ignore_index=True)
                    execution_type_name = exe_type_name["execution_type_name"].drop_duplicates().tolist()
                    execution_type_name = [str(element).split('"')[1] for element in execution_type_name]
                    execution_type_name_str = ',\n '.join(map(str, execution_type_name))
                    name_list.append(name)
                    exec_type_name_list.append(execution_type_name_str)
                name_dict['name'] = name_list
                name_dict['execution_type_name'] = exec_type_name_list
                name_df = pd.DataFrame(name_dict)
                merged_df = df.merge(name_df, on='name', how='left')
                merged_df['name'] = merged_df['name'].apply(lambda x: x.split(':')[0] if ':' in x else x)
                merged_df = merged_df.loc[merged_df["type"] == art_type]
                result = merged_df.to_json(orient="records")
                tempout = json.loads(result)


def artifacts() -> None:
    config = Config(max_depth=9)
    config.trace_filter = GlobbingFilter(exclude=["pycallgraph2.*", "selectors.*", "collections.*", "<module>", "email.*", "fsspec.*", "funcy.*", "pygtrie.*", "json.*", "posixpath.*",
                                                   "logging.*", "absl.*", "typing.*", "threading.*", "sre_compile.*", "sre_parse.*", "codecs.*", "voluptuous.*", "_compression.*", 
                                                   "warnings.*", "os.*", "subprocess.*", "<lambda>", "encodings.*", "gzip.*", "genericpath.*", "random.*", "abc.*", 
                                                   "_process_posts", "enum.*", "uuid.*", "xml.*", "pandas.*", "numpy.*"])
    graphviz = GraphvizOutput(output_file='artifacts.png')
    with PyCallGraph(output=graphviz, config=config):
        mlmdfilePath="/home/sharvark/cmf-server/data/mlmd"
        pipeline_name="Test-env"
        artifactsId = get_all_artifact_ids(mlmdfilePath)["Test-env"]["Dataset"]["id"]
        artifactsTypes = get_artifact_types(mlmdfilePath)[0]
        get_artifacts(mlmdfilePath, pipeline_name, artifactsTypes, artifactsId)

if __name__ == '__main__':
    artifacts()
