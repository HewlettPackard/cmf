# Copyright (c) OpenMMLab. All rights reserved.

###
# Copyright (2024) Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###

from mmcv.utils import TORCH_VERSION
from ...dist_utils import master_only
from ..hook import HOOKS
from .base import LoggerHook
import uuid
import os
import sys


@HOOKS.register_module()
class CmfLoggerHook(LoggerHook):
    """Class to log metrics and (optionally) a trained model to CMF.

    It requires `cmflib`_ to be installed.

    Args:
        mlmd_file_path (str): Path to mlmd file.
        exp_name (str, optional): Name of the experiment to be used.
            Default None. If not None, set the active experiment.
            If experiment_name does not exist, an experiment_name
            with be created using uuid.
        tags (Dict[str], optional): Tags for the current run.
            Default None. If not None, set tags for the current run.
        interval (int): Logging interval (every k iterations). Default: 10.
        ignore_last (bool): Ignore the log of last iterations in each epoch
            if less than `interval`. Default: True.
        reset_flag (bool): Whether to clear the output buffer after logging.
            Default: False.
        by_epoch (bool): Whether EpochBasedRunner is used. Default: True.
    """
    Training_metric_count = 1
    Validation_metric_count = 1
    
    @master_only
    def __init__(self,
                 mlmd_file_path = os.path.join('/'+os.environ['DVC_ROOT']) + '/mlmd',
                 exp_name=None,
                 tags=None,
                 interval=10, #needed by super class
                 ignore_last=True, #needed by super class
                 reset_flag=False, #needed by super class
                 by_epoch=True): #needed by super class
        super(CmfLoggerHook, self).__init__(interval, ignore_last,
                                               reset_flag, by_epoch)
        self.mlmdFilePath = mlmd_file_path
        self.exp_name = exp_name if exp_name else str(uuid.uuid4())
        self.tags = tags

        try:
            from cmflib import cmf
            from cmflib import cmfquery
        except ImportError:
            raise ImportError(
                'Please run "pip install cmflib" to install cmflib')
        self.cmf_logger = cmf.Cmf(filename=self.mlmdFilePath, pipeline_name=self.exp_name , graph=True)
        self.context = self.cmf_logger.create_context(os.environ['stage_name'])
        
        cmd = str(' '.join(sys.argv)) 
        self.execution = self.cmf_logger.create_execution(
            str(os.environ['stage_name'])+'_'+str(os.environ['execution_name']), 
            {}, 
            cmd = str(cmd), 
            create_new_execution=False
            )
        
        self.prefix = 'Training_Metrics_' + str(os.environ['stage_name'])+'_'+str(os.environ['execution_name'])

    @master_only
    def log(self, runner):
        tags = self.get_loggable_tags(runner)
        mode = self.get_mode(runner)
        self.mode = mode
        if tags:
            if mode == 'train':
                self.commit_name = self.prefix + '_' + str(CmfLoggerHook.Training_metric_count)
                self.cmf_logger.log_metric(self.commit_name, tags)
                
            else:
                prefix = 'Validation_Metrics_' + str(os.environ['stage_name'])+'_'+str(os.environ['execution_name'])
                commit_name = prefix + '_' + str(CmfLoggerHook.Validation_metric_count)
                self.cmf_logger.log_execution_metrics(commit_name, tags)
                CmfLoggerHook.Validation_metric_count+=1

    @master_only
    def after_run(self, runner):
        self.cmf_logger.commit_metrics(self.commit_name)
        CmfLoggerHook.Training_metric_count+=1
