# Copyright (c) OpenMMLab. All rights reserved.
from mmcv.utils import TORCH_VERSION
from ...dist_utils import master_only
from ..hook import HOOKS
from .base import LoggerHook


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
                 exp_name=None,
                 tags=None,
                 log_model=True,
                 interval=10,
                 ignore_last=True,
                 reset_flag=False,
                 by_epoch=True):
        super(CmfLoggerHook, self).__init__(interval, ignore_last,
                                               reset_flag, by_epoch)
        self.exp_name = exp_name
        self.tags = tags
        self.log_model = log_model
        self.import_cmflib()

    def import_cmflib(self):
        try:
            from cmflib import cmf
        except ImportError:
            raise ImportError(
                'Please run "pip install cmflib" to install cmflib')
        self.cmf_logger = cmf.Cmf(pipeline_name="Active_learning", graph=True)
        self.context = self.cmf_logger.create_context("Training")
        self.execution = self.cmf_logger.create_execution("Training")


    @master_only
    def log(self, runner):
        tags = self.get_loggable_tags(runner)
        print(tags)
        print(self.get_iter(runner))
        if tags:
            self.cmf_logger.log_execution_metrics("metrics_"+ str(self.get_iter(runner)), tags)

