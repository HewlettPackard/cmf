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
            artifacts = pd.DataFrame()
            if not execution_ids.get(name).empty:
                exe_ids = execution_ids[name]['id'].tolist()
                artifacts = query.get_all_artifacts_for_executions(exe_ids)
            #acknowledging pipeline exist even if df is empty. 
                if artifacts.empty:
                    artifact_ids[name] = pd.DataFrame()   # { pipeline_name: {empty df} }
                else:
                    artifact_ids[name] = {}
                    for art_type in artifacts['type']:
                        filtered_values = artifacts.loc[artifacts['type'] == art_type, ['id', 'name']]
                        artifact_ids[name][art_type] = filtered_values
        # if execution_ids is empty create dictionary with key as pipeline name
        # and value as empty df
            else:
                artifact_ids[name] = pd.DataFrame()
        print(artifact_ids)
        return artifact_ids

def get_artifact_id() -> None:
    config = Config(max_depth=9)
    config.trace_filter = GlobbingFilter(exclude=["pycallgraph2.*", "selectors.*", "collections.*", "<module>", "email.*", "fsspec.*", "funcy.*", 
                                                   "logging.*", "absl.*", "typing.*", "threading.*", "sre_compile.*", "sre_parse.*", "codecs.*", 
                                                   "warnings.*", "os.*", "subprocess.*", "<lambda>", "encodings.*", "gzip.*", "genericpath.*",
                                                   "_process_posts", "enum.*", "uuid.*", "xml.*", "pandas.*", "numpy.*"])
    graphviz = GraphvizOutput(output_file='artifact_id_new.png')
    with PyCallGraph(output=graphviz, config=config):
        mlmdfilePath="/home/sharvark/cmf-server/data/mlmd"
        artifactId=get_all_artifact_ids(mlmdfilePath)


if __name__ == '__main__':
    get_artifact_id()

