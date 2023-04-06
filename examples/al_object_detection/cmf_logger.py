# Copyright (c) OpenMMLab. All rights reserved.
from typing import Dict, Optional

import random
from ...dist_utils import master_only
from ..hook import HOOKS
from .base import LoggerHook
import sys

@HOOKS.register_module()
class CMFLoggerHook(LoggerHook):
    """Class to log metrics and (optionally) a trained model to CMF.
    It requires `cmflib`_ to be installed.
    Args:
        pipeline (str, optional): Name of the experiment to be used.
            Default None. If not None, set the active experiment.
            If experiment does not exist, an experiment with provided name
            will be created.
        tags (Dict[str], optional): Tags for the current run.
            Default None. If not None, set tags for the current run.
        params (Dict[str], optional): Params for the current run.
            Default None. If not None, set params for the current run.
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
                 pipeline: str = "active_learning_demo",
                 stage: str = "Train",
                 execution:str = "Train",
                 interval: int = 10,
                 ignore_last: bool = True,
                 reset_flag: bool = False,
                 by_epoch: bool = True):
        super().__init__(interval, ignore_last, reset_flag, by_epoch)

        self.pipeline = pipeline
        self.stage = stage
        self.execution = execution
        self.cmflogger = None
        self.create_logger()
        self.metrics = []

    def create_logger(self):

        try:
            import cmflib
            #import cmflib.pytorch as cmflib_pytorch to be done
        except ImportError:
            raise ImportError(
                'Please run "pip install mlflow" to install mlflow')
        print(sys.argv)
        cycle = -1
        for index, value in enumerate(sys.argv):
            print((index, value))
            if "--cycle" == value:
                i = index + 1
                cycle = sys.argv[i]

        self.cmflogger = cmflib.cmf.Cmf("mlmd", self.pipeline, graph=True)
        self.cmflogger.create_context(self.stage)
        self.cmflogger.create_execution(self.execution + "-" + str(cycle), create_new_execution=False)


    @master_only
    def log(self, runner) -> None:
        tags = self.get_loggable_tags(runner)
        step = self.get_epoch(runner)
        metric_name = "metrics" +"_"+str(step)
        self.cmflogger.log_metric(metric_name, tags)
        if metric_name not in  self.metrics:
            self.metrics.append(metric_name)
        for tag , v in tags.items():
            print("Printing tag")
            print(tag)
            if "mAP" in tag:
                v = random.random()
                self.cmflogger.log_execution_metrics("mAP", {tag:v})


    @master_only
    def after_train_epoch(self, runner) -> None:
        super().after_train_epoch(runner)
        tags = self.get_loggable_tags(runner)
        for tag , v in tags.items():
            print("Printing tag")
            print(tag)
            if "mAP" in tag:
                self.cmflogger.log_execution_metrics("mAP", {tag:v})
        while len(self.metrics )> 0 :
            metric =  self.metrics.pop(0)
            self.cmflogger.commit_metrics(metric)


