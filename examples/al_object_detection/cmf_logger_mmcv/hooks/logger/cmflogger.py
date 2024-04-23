# Copyright (c) OpenMMLab. All rights reserved.
from mmcv.utils import TORCH_VERSION
from ...dist_utils import master_only
from ..hook import HOOKS
from .base import LoggerHook
import uuid
import dvc.api
import dvc
import pandas as pd
import os
import subprocess
import json
import yaml
import sys


@HOOKS.register_module()
class CmfLoggerHook(LoggerHook):
    """Class to log metrics and (optionally) a trained model to CMF.

    It requires `cmflib`_ to be installed.

    Args:
        exp_name (str, optional): Name of the experiment to be used.
            Default None. If not None, set the active experiment.
            If experiment does not exist, an experiment with provided name
            will be created.
        tags (Dict[str], optional): Tags for the current run.
            Default None. If not None, set tags for the current run.
        log_model (bool, optional): Whether to log an MLflow artifact.
            Default True. If True, log runner.model as an MLflow artifact
            for the current run.
        interval (int): Logging interval (every k iterations). Default: 10.
        ignore_last (bool): Ignore the log of last iterations in each epoch
            if less than `interval`. Default: True.
        reset_flag (bool): Whether to clear the output buffer after logging.
            Default: False.
        by_epoch (bool): Whether EpochBasedRunner is used. Default: True.

    .. _MLflow:
        https://www.mlflow.org/docs/latest/index.html
    """

    def __init__(self,
                 mlmd_file_path = os.path.join('/'+os.environ['DVC_ROOT']) + '/mlmd',
                 exp_name=None,
                 tags=None,
                 log_model=True,
                 interval=10,
                 ignore_last=True,
                 reset_flag=False,
                 by_epoch=True):
        super(CmfLoggerHook, self).__init__(interval, ignore_last,
                                               reset_flag, by_epoch)
        self.mlmdFilePath = mlmd_file_path
        self.exp_name = exp_name
        self.tags = tags
        self.log_model = log_model
        self.import_cmflib() 

    @master_only
    def import_cmflib(self):
        try:
            from cmflib import cmf
            from cmflib import cmfquery
        except ImportError:
            raise ImportError(
                'Please run "pip install cmflib" to install cmflib')
        self.cmf_logger = cmf.Cmf(filename="mlmd", pipeline_name=self.exp_name , graph=True)
        self.context = self.cmf_logger.create_context(os.environ['DVC_STAGE'])
        
        file_ = os.path.isfile(self.mlmdFilePath)

        if file_:
            cmd_exe = {}
            cmf_query = cmfquery.CmfQuery(self.mlmdFilePath)
            pipelines: t.List[str] = cmf_query.get_pipeline_names()
            for pipeline in pipelines:
                pipeline_name = pipeline
                stages: t.List[str] = cmf_query.get_pipeline_stages(pipeline)
                for stage in stages:
                    exe_df: pd.DataFrame = cmf_query.get_all_executions_in_stage(stage)
                    """
                    Parse all the executions in a stage
                    eg- exe_step = ['demo_eval.py', '--trained_model', 'data/model-1', '--enable_df', 'True', '--round', '1']
                    """
                    for index, row in exe_df.iterrows():
                        exe_step = row['Execution']
                        '''
                        if already same execution command has been captured previously use the latest
                        execution id to associate the new metadata
                        '''
                        if None is cmd_exe.get(exe_step, None):
                            cmd_exe[exe_step] = str(row['id']) + "," + stage + "," + pipeline
                        else:
                            if row['id'] > int(cmd_exe.get(exe_step, None).split(',')[0]):
                                cmd_exe[exe_step] = str(row['id']) + "," + stage + "," + pipeline
            
            cmd = cmd_exe.get(str(os.environ['DVC_STAGE'])+'_'+str(os.environ['execution_name']), None)
            if cmd:
                cmf_levels = cmd.split(',')
                self.execution = self.cmf_logger.update_execution(int(cmf_levels[0]))
            else:
                self.execution = self.cmf_logger.create_execution(str(os.environ['DVC_STAGE'])+'_'+str(os.environ['execution_name']), {}, 
                str(os.environ['DVC_STAGE'])+'_'+str(os.environ['execution_name']))

        else:
            self.execution = self.cmf_logger.create_execution(str(os.environ['DVC_STAGE'])+'_'+str(os.environ['execution_name']), {}, 
            str(os.environ['DVC_STAGE'])+'_'+str(os.environ['execution_name']))

    @master_only
    def log(self, runner):
        tags = self.get_loggable_tags(runner)
        mode = self.get_mode(runner)
        if tags:
            prefix = 'Training_Metrics_' + str(os.environ['DVC_STAGE'])+'_'+str(os.environ['execution_name'])
            prefixed = [filename for filename in os.listdir('.') if filename.startswith(prefix)]
            if len(prefixed)>=1:
                end_ = (len(prefixed)//2)+1
            else:
                end_ = 1
            self.commit_name = prefix + '_' + str(end_)
            if mode == 'train':
                self.cmf_logger.log_metric(self.commit_name, tags)
            else:
                # This will log validation metrics in viewable form by hovering over it in liineage
                prefix = 'Validation_Metrics' + str(os.environ['DVC_STAGE'])+'_'+str(os.environ['execution_name'])
                prefixed = [filename for filename in os.listdir('.') if filename.startswith(prefix)]
                if len(prefixed)>=1:
                    end_ = (len(prefixed)//2)+1
                else:
                    end_ = 1
                commit_name = prefix + '_' + str(end_)
                self.cmf_logger.log_execution_metrics(commit_name, tags)

    @master_only
    def after_run(self, runner):
        self.cmf_logger.commit_metrics(self.commit_name)

