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

def get_artifact_id() -> None:
    config = Config(max_depth=9)
    config.trace_filter = GlobbingFilter(exclude=["pycallgraph2.*", "selectors.*", "collections.*", "<module>", "email.*", "fsspec.*", "funcy.*", 
                                                   "logging.*", "absl.*", "typing.*", "threading.*", "sre_compile.*", "sre_parse.*", "codecs.*", 
                                                   "warnings.*", "os.*", "subprocess.*", "<lambda>", "encodings.*", "gzip.*", "genericpath.*",
                                                   "_process_posts", "enum.*", "uuid.*", "xml.*", "pandas.*", "numpy.*"])
    graphviz = GraphvizOutput(output_file='artifact_id.png')
    with PyCallGraph(output=graphviz, config=config):
        mlmdfilePath="/home/ayesha/cmf-server/data/mlmd"
        artifactId=get_all_artifact_ids(mlmdfilePath)


if __name__ == '__main__':
    get_artifact_id()

