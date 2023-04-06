# Copyright (c) OpenMMLab. All rights reserved.
from typing import Dict, Optional

from mmcv.utils import master_only
from mmcv.runner.hooks import HOOKS
from mmcv.runner.base_runner import LoggerHook


@HOOKS.register_module()
class CMFLoggerHook(LoggerHook):
    """Class to log metrics and (optionally) a trained model to CMF.
    It requires `cmflib`_ to be installed.
    Args:
        pipeline (str, optional): Name of the pipleine to be used.
        Stage (str, optional): Name of the stage(Train, Featurize etc) to be used.
        Execution - Name of the execution to be used
        interval (int): Logging interval (every k iterations). Default: 10.
        ignore_last (bool): Ignore the log of last iterations in each epoch
            if less than `interval`. Default: True.
        reset_flag (bool): Whether to clear the output buffer after logging.
            Default: False.
        by_epoch (bool): Whether EpochBasedRunner is used. Default: True.
    """

    def __init__(self,
                 pipeline: str = "active_learning",
                 stage: str = "train",
                 params: Optional[Dict] = None,
                 interval: int = 10,
                 ignore_last: bool = True,
                 reset_flag: bool = False,
                 by_epoch: bool = True):
        super().__init__(interval, ignore_last, reset_flag, by_epoch)
        self.import_cmflib
        self.pipeline = pipeline
        self.stage = stage
        self.params = params


    def import_cmflib(self) -> None:
        try:
            import cmflib
            #import cmflib.pytorch as cmflib_pytorch to be done
        except ImportError:
            raise ImportError(
                'Please run "pip install cmflib" to install cmflib')
        self.cmflogger = cmflib.cmf.Cmf("mlmd", "active_learning", graph=True)
        self.cmflogger.create_context("train")
        self.cmflogger.create_execution("execution")
        #self.cmf_pytorch = cmf_pytorch


    @master_only
    def log(self, runner) -> None:
        tags = self.get_loggable_tags(runner)
        for tag, val in tags.items():
            self.task_logger.report_scalar(tag, tag, val,
                                           self.get_iter(runner))
            self.cmflogger.log_metrics(tag + str(self.get_iter(runner)), {tag:str(val)})

