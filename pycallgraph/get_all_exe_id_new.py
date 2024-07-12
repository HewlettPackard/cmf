from cmflib import cmf, cmfquery, cmf_merger
from pycallgraph2 import PyCallGraph
from pycallgraph2 import Config
from pycallgraph2.output import GraphvizOutput
from pycallgraph2 import GlobbingFilter
import pandas as pd
import typing as t
import json, glob
import os

   
# writing new functions to remove multiple calls to cmfquery functions or ml-metadata functions
def get_all_executions_in_pipeline(pipeline_name, q):
    df = pd.DataFrame()
    pipeline_id = q.get_pipeline_id(pipeline_name)
    for stage in q._get_stages(pipeline_id):
        for execution in q._get_executions(stage.id):
           ex_as_df: pd.DataFrame = q._transform_to_dataframe(
               execution, {"id": execution.id, "name": execution.name}
           )
           df = pd.concat([df, ex_as_df], sort=True, ignore_index=True)
    return df


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
        executions = get_all_executions_in_pipeline(name, query)
        df = pd.concat([df, executions], sort=True, ignore_index=True)
    # check if df is empty return just pipeline_name: {}
    # if df is not empty return dictionary with pipeline_name as key 
    # and df with id, context_type, uuid, context_ID as value.
        if not df.empty:
            execution_ids[name] = df[['id', 'Context_Type', 'Execution_uuid', 'Context_ID']]
        else:
            execution_ids[name] = pd.DataFrame()
    return execution_ids



def get_exe_id() -> None:
    config = Config(max_depth=9)
    config.trace_filter = GlobbingFilter(exclude=["pycallgraph2.*", "selectors.*", "collections.*", "<module>", "email.*", "fsspec.*", "funcy.*", 
                                                   "logging.*", "absl.*", "typing.*", "threading.*", "sre_compile.*", "sre_parse.*", "codecs.*", 
                                                   "warnings.*", "os.*", "subprocess.*", "<lambda>", "encodings.*", "gzip.*", "genericpath.*",
                                                   "_process_posts", "enum.*", "uuid.*", "xml.*", "pandas.*", "numpy.*"])
    graphviz = GraphvizOutput(output_file='executions_id_new.png')
    with PyCallGraph(output=graphviz, config=config):
        mlmdfilePath="/home/ayesha/cmf-server/data/mlmd"
        exeid=get_all_exe_ids(mlmdfilePath)["Test-env"]
        print(exeid)


if __name__ == '__main__':
    get_exe_id()

