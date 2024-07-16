from cmflib import cmf, cmfquery, cmf_merger
from pycallgraph2 import PyCallGraph
from pycallgraph2 import Config
from pycallgraph2.output import GraphvizOutput
from pycallgraph2 import GlobbingFilter
import pandas as pd
import typing as t
import json, glob
import os


def get_model_data(mlmdfilepath, modelId):
    '''
      This function retrieves the necessary model data required for generating a model card.
      Arguments:
        mlmdfilepath (str): The file path to the metadata.
        modelId (int): The ID of the model for which data is required.
      Returns:
        This function returns a tuple of DataFrames containing the following:
        model_data_df (DataFrame): Metadata related to the model itself.
        model_exe_df (DataFrame): Metadata of the executions in which the specified modelId was an input or output.
        model_input_df (DataFrame): Metadata of input artifacts that led to the creation of the model.
        model_output_df (DataFrame): Metadata of artifacts that used the model as an input.
        The returned DataFrames provide comprehensive metadata for the specified model, aiding in the creation of detailed and accurate model cards.
    '''
    query = cmfquery.CmfQuery(mlmdfilepath)
    pd.set_option('display.max_columns', None)
    model_data_df = pd.DataFrame()
    model_exe_df = pd.DataFrame()
    model_input_df = pd.DataFrame()
    model_output_df = pd.DataFrame()

    # get name from id
    modelName = ""
    model_data_df = query.get_all_artifacts_by_ids_list([modelId])
    # if above dataframe is not empty, we have the dataframe for given modelId with full model related details
    if model_data_df.empty:
        return model_data_df, model_exe_df, model_input_df, model_output_df
    # However following check is done, in case, variable 'modelId' is not an ID for model artifact
    modelType = model_data_df['type'].tolist()[0]
    if not modelType == "Model":
        # making model_data_df empty
        model_data_df = pd.DataFrame()
        return model_data_df, model_exe_df, model_input_df, model_output_df


    # extracting modelName
    modelName = model_data_df['name'].tolist()[0]

    # model's executions data with props and custom props
    exe_df = query.get_all_executions_for_artifact(modelName)
    exe_ids = []
    if not exe_df.empty:
        exe_df.drop(columns=['execution_type_name', 'execution_name'], inplace=True)
        exe_ids = exe_df['execution_id'].tolist()


    if not exe_ids:
         return model_data_df, model_exe_df, model_input_df, model_output_df
    model_exe_df = query.get_all_executions_by_ids_list(exe_ids)
    model_exe_df.drop(columns=['Python_Env', 'Git_Start_Commit', 'Git_End_Commit'], inplace=True)

    in_art_ids =  []
    # input artifacts
    # it is usually not a good practice to use functions starting with _ outside of the file they are defined .. should i change??
    in_art_ids.extend(query._get_input_artifacts(exe_ids))
    if modelId in in_art_ids:
        in_art_ids.remove(modelId)
    model_input_df = query.get_all_artifacts_by_ids_list(in_art_ids)

    out_art_ids = []
    # output artifacts
    out_art_ids.extend(query._get_output_artifacts(exe_ids))
    if modelId in out_art_ids:
        out_art_ids.remove(modelId)
    model_output_df = query.get_all_artifacts_by_ids_list(out_art_ids)

    return model_data_df, model_exe_df, model_input_df, model_output_df



def get_model_card() -> None:
    config = Config(max_depth=9)
    config.trace_filter = GlobbingFilter(exclude=["pycallgraph2.*", "selectors.*", "collections.*", "<module>", "email.*", "fsspec.*", "funcy.*",
                                                   "logging.*", "absl.*", "typing.*", "threading.*", "sre_compile.*", "sre_parse.*", "codecs.*", 
                                                   "warnings.*", "os.*", "subprocess.*", "<lambda>", "encodings.*", "gzip.*", "genericpath.*",
                                                   "_process_posts", "enum.*", "uuid.*", "xml.*", "pandas.*", "numpy.*"])
    graphviz = GraphvizOutput(output_file='model_card.png')
    with PyCallGraph(output=graphviz, config=config):
        mlmd_path="/home/ayesha/cmf-server/data/mlmd"
        modelDataDf, modelExeDf, modelIpDf, modelOpDf = get_model_data(mlmd_path, 6)


if __name__ == '__main__':
    get_model_card()

