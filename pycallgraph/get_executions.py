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


def get_executions_by_ids(mlmdfilepath, pipeline_name, exe_ids):
    '''
    Args:
     mlmdfilepath: mlmd file path.
     pipeline_name: name of the pipeline.
     exe_ids: list of execution ids.
   
    Returns:
     returns dataframe of executions using execution_ids.
    '''
    query = cmfquery.CmfQuery(mlmdfilepath)
    #print(exe_ids) 
    df = pd.DataFrame()
    executions = query.get_all_executions_by_ids_list(exe_ids)
    df = pd.concat([df, executions], sort=True, ignore_index=True)
        #df=df.drop('name',axis=1)



def get_executions() -> None:
    config = Config(max_depth=9)
    config.trace_filter = GlobbingFilter(exclude=["pycallgraph2.*", "selectors.*", "collections.*", "<module>", "email.*", "fsspec.*", "funcy.*", 
                                                   "logging.*", "absl.*", "typing.*", "threading.*", "sre_compile.*", "sre_parse.*", "codecs.*", 
                                                   "warnings.*", "os.*", "subprocess.*", "<lambda>", "encodings.*", "gzip.*", "genericpath.*",
                                                   "_process_posts", "enum.*", "uuid.*", "xml.*", "pandas.*", "numpy.*"])
    graphviz = GraphvizOutput(output_file='executions.png')
    with PyCallGraph(output=graphviz, config=config):
        mlmdfilePath="/home/ayesha/cmf-server/data/mlmd"
        pipeline_name="Test-env"
        exeid=get_all_exe_ids(mlmdfilePath)["Test-env"]
        id_list = exeid["id"]
        get_executions_by_ids(mlmdfilePath, pipeline_name, id_list)


if __name__ == '__main__':
    get_executions()
