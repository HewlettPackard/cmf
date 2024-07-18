from cmflib import cmf, cmfquery, cmf_merger
from pycallgraph2 import PyCallGraph
from pycallgraph2 import Config
from pycallgraph2.output import GraphvizOutput
from pycallgraph2 import GlobbingFilter
import pandas as pd
import typing as t
import json, glob
import os
from get_all_exe_id_new import get_all_exe_ids

"""
calling this function here as this function at the time of execution 
is not part of get_executions() as list of exe ids is created at the time of server start or mlmd push 
"""
exeid=get_all_exe_ids("/home/sharvark/cmf-server/data/mlmd")["Test-env"]
id_list = exeid["id"]

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
        mlmdfilePath="/home/sharvark/cmf-server/data/mlmd"
        pipeline_name="Test-env"
        get_executions_by_ids(mlmdfilePath, pipeline_name, id_list)


if __name__ == '__main__':
    get_executions()
