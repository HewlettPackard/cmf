import argparse
import copy
import os
import os.path as osp
import time

import mmcv
import torch
import random
import numpy as np
from mmcv import Config, DictAction
from mmcv.parallel import MMDataParallel, MMDistributedDataParallel
from mmcv.runner import init_dist, load_checkpoint, save_checkpoint
from mmcv.utils import get_git_hash

from mmdet import __version__
from mmdet.apis import set_random_seed, train_detector
from mmdet.apis import single_gpu_test, calculate_uncertainty
from mmdet.datasets import build_dataloader, build_dataset
from mmdet.models import build_detector
from mmdet.utils import collect_env, get_root_logger
#from mmdet.utils.active_datasets import *
from mmdet.utils.hdc.active_datasets import *
from tools.utils import losstype
from torch import distributed as dist


def parse_args():
    parser = argparse.ArgumentParser(description='Train a detector')
    parser.add_argument('config', help='train config file path')
    parser.add_argument('--cycle', help='active learning iteration >= 0')
    parser.add_argument('--labeled', help='labeled samples list file')
    parser.add_argument('--unselected', help='unselected samples list file')
    parser.add_argument('--model_prev',
                        help='previous cycle model checkpoint file')
    parser.add_argument('--model', help='model checkpoint file')
    parser.add_argument('--work_directory',
                        help='the dir to save logs and model checkpoints')
    parser.add_argument('--no-validate', action='store_false',
        help='whether not to evaluate the checkpoint during training')
    group_gpus = parser.add_mutually_exclusive_group()
    group_gpus.add_argument('--gpus', type=int,
        help='number of gpus to use (only applicable to non-distributed run)')
    group_gpus.add_argument('--gpu-ids', type=int, nargs='+',
        help='ids of gpus to use (only applicable to non-distributed run)')
    parser.add_argument('--seed', type=int, default=666, help='random seed')
    parser.add_argument('--deterministic', action='store_true',
        help='whether to set deterministic options for CUDNN backend.')
    parser.add_argument('--options', nargs='+', action=DictAction,
                        help='arguments in dict')
    parser.add_argument('--launcher',
                        choices=['none', 'pytorch', 'slurm', 'mpi'],
                        default='none', help='job launcher')
    parser.add_argument('--local_rank', type=int, default=0)
    parser.add_argument('--stage_name', help='Name for current execution')
    parser.add_argument('--execution_name', help='Name for current execution')
    args = parser.parse_args()
    if 'LOCAL_RANK' not in os.environ:
        os.environ['LOCAL_RANK'] = str(args.local_rank)
    return args


def main():
    args = parse_args()

    assert (args.cycle and args.labeled and args.unselected and args.model), \
        ('Please specify active learning cycle, file names of labeled '
         'and unselected image list files, and model checkpoint file '
         'with arguments "--cycle", "--labeled", "--unselected" and "model"')

    cfg = Config.fromfile(args.config)
    if args.options is not None:
        cfg.merge_from_dict(args.options)

    # set cudnn_benchmark
    if cfg.get('cudnn_benchmark', False):
        torch.backends.cudnn.benchmark = True

    # work_directory is determined in this priority: CLI > config > defasult
    if args.work_directory is not None:
        # update work_directory from CLI args if args.work_directory is not None
        cfg.work_directory = args.work_directory
    elif cfg.get('work_directory', None) is None:
        # derive work_directory from config name if cfg.work_directory is None
        cfg.work_directory = osp.join('./work_dirs',
                                     osp.splitext(osp.basename(args.config))[0])

    # TO DO: placeholder for distributed processing. Will require code changes
    if args.gpu_ids is not None:
        cfg.gpu_ids = args.gpu_ids
    else:
        cfg.gpu_ids = range(1) if args.gpus is None else range(args.gpus)

    # init distributed env first, since logger depends on the dist info.
    if args.launcher == 'none':
        distributed = False
    else:
        distributed = True
        init_dist(args.launcher, **cfg.dist_params)

    # create work_directory
    mmcv.mkdir_or_exist(osp.abspath(cfg.work_directory))

    stage_name = args.stage_name
    os.environ['stage_name'] = stage_name

    execution_name = args.execution_name
    os.environ['execution_name'] = execution_name
    # dump config
    cfg.dump(osp.join(cfg.work_directory,
                      f'cycle_train{args.cycle}_' + osp.basename(args.config)))

    # init the logger before other steps
    timestamp = time.strftime('%Y%m%d_%H%M%S', time.localtime())
    log_file = osp.join(cfg.work_directory, f'cycle_train{args.cycle}.log')
    logger = get_root_logger(log_file=log_file, log_level=cfg.log_level)

    # init the meta dict to record some important information
    #  such as environment info and seed, which will be logged
    meta = dict()

    # log env info
    env_info_dict = collect_env()
    env_info = '\n'.join([f'{k}: {v}' for k, v in env_info_dict.items()])
    dash_line = '-' * 60 + '\n'
    logger.info('Environment info:\n' + dash_line + env_info + '\n' + dash_line)
    meta['env_info'] = env_info

    # log some basic info
    logger.info(f'Distributed training: {distributed}')
    logger.info(f'Config:\n{cfg.pretty_text}')

    # set random seeds
    if args.seed is not None:
        logger.info(
         f'Set random seed to {args.seed}, deterministic: {args.deterministic}')
        set_random_seed(args.seed, deterministic=args.deterministic)
    cfg.seed = args.seed
    meta['seed'] = args.seed

    # load lists of all, labeled and unselected images
    all_anns = load_ann_list(cfg.data.train.dataset.ann_file)

    if len(all_anns[0]) == 1:
        X_all = np.arange(len(all_anns))
    else:
        j = 0
        for i in range(len(all_anns)):
            j += len(all_anns[i])
        X_all = np.arange(j)
    X_L = np.load(args.labeled)
    X_U = np.load(args.unselected)
    cycle = args.cycle
    cfg.cycles = list((args.cycle))
    initial_step = cfg.lr_config.step

    # get the config of the labeled dataset
    cfg = create_X_L_file(cfg, X_L, all_anns, cycle)

    # build the model and load checkpoint, if specified
    if args.model_prev is not None:
        cfg.model.pretrained = None
        if cfg.model.get('neck'):
            if cfg.model.neck.get('rfp_backbone'):
                if cfg.model.neck.rfp_backbone.get('pretrained'):
                    cfg.model.neck.rfp_backbone.pretrained = None
    model = build_detector(cfg.model, train_cfg=cfg.train_cfg,
                           test_cfg=cfg.test_cfg)
    if args.model_prev is not None:
        checkpoint = load_checkpoint(model, args.model_prev)

    # load dataset
    datasets = [build_dataset(cfg.data.train)]
    if len(cfg.workflow) == 2:
    
        val_dataset = copy.deepcopy(cfg.data.val)
        val_dataset.pipeline = cfg.data.train.dataset.pipeline
        datasets.append(build_dataset(val_dataset))
    model.CLASSES = datasets[0].CLASSES

    # save mmdet version, config file content and class names in
    # checkpoints as meta data
    if cfg.checkpoint_config is None:
        cfg.checkpoint_config = dict()
    cfg.checkpoint_config.meta = dict(
        mmdet_version=__version__ + get_git_hash()[:7],
        config=cfg.pretty_text, CLASSES=datasets[0].CLASSES)

    for epoch in range(cfg.epoch):
        # Only in the last 3 epoch does the learning rate need to be reduced
        #  and the model needs to be evaluated.
        if epoch == cfg.epoch - 1:
            cfg.lr_config.step = initial_step
            cfg.evaluation.interval = cfg.epoch_ratio[0]
        else:
            cfg.lr_config.step = [1000]
            cfg.evaluation.interval = 100

        # ---------- Label Set Training ----------

        if epoch == 0:
            cfg = create_X_L_file(cfg, X_L, all_anns, cycle)

            if dist.is_initialized():
                torch.distributed.barrier()
            datasets = [build_dataset(cfg.data.train)]
            losstype.update_vars(0)
            cfg.total_epochs = cfg.epoch_ratio[0]
            cfg_bak = cfg.deepcopy()
            time.sleep(2)
            for name, value in model.named_parameters():
                value.requires_grad = True
            train_detector(model, datasets, cfg,
                           distributed=distributed,
                           validate=(not args.no_validate),
                           timestamp=timestamp, meta=meta)
            cfg = cfg_bak

        # ---------- Re-weighting and Minimizing Instance Uncertainty ----------

        cfg_u = create_X_U_file(cfg.deepcopy(), X_U, all_anns, cycle)
        cfg = create_X_L_file(cfg, X_L, all_anns, cycle)
        if dist.is_initialized():
            torch.distributed.barrier()

        datasets_u = [build_dataset(cfg_u.data.train)]
        datasets = [build_dataset(cfg.data.train)]
        losstype.update_vars(1)
        cfg_u.total_epochs = cfg_u.epoch_ratio[1]
        cfg.total_epochs = cfg.epoch_ratio[1]
        cfg_u_bak = cfg_u.deepcopy()
        cfg_bak = cfg.deepcopy()
        time.sleep(2)
        for name, value in model.named_parameters():
            if name in cfg.theta_f_1:
                value.requires_grad = False
            elif name in cfg.theta_f_2:
                value.requires_grad = False
            else:
                value.requires_grad = True
        train_detector(model, [datasets, datasets_u], [cfg, cfg_u],
                       distributed=distributed,
                       validate=(not args.no_validate),
                       timestamp=timestamp, meta=meta)
        cfg_u = cfg_u_bak
        cfg = cfg_bak

        # ---------- Re-weighting and Maximizing Instance Uncertainty ----------

        cfg_u = create_X_U_file(cfg.deepcopy(), X_U, all_anns, cycle)
        cfg = create_X_L_file(cfg, X_L, all_anns, cycle)

        if dist.is_initialized():
            torch.distributed.barrier()
        datasets_u = [build_dataset(cfg_u.data.train)]
        datasets = [build_dataset(cfg.data.train)]
        losstype.update_vars(2)
        cfg_u.total_epochs = cfg_u.epoch_ratio[1]
        cfg.total_epochs = cfg.epoch_ratio[1]
        cfg_u_bak = cfg_u.deepcopy()
        cfg_bak = cfg.deepcopy()
        time.sleep(2)
        for name, value in model.named_parameters():
            if name in cfg.theta_f_1:
                value.requires_grad = True
            elif name in cfg.theta_f_2:
                value.requires_grad = True
            else:
                value.requires_grad = False
        train_detector(model, [datasets, datasets_u], [cfg, cfg_u],
                       distributed=distributed,
                       validate=(not args.no_validate),
                       timestamp=timestamp, meta=meta)
        cfg_u = cfg_u_bak
        cfg = cfg_bak

        # ---------- Label Set Training ----------

        cfg = create_X_L_file(cfg, X_L, all_anns, cycle)

        if dist.is_initialized():
            torch.distributed.barrier()
        datasets = [build_dataset(cfg.data.train)]
        losstype.update_vars(0)
        cfg.total_epochs = cfg.epoch_ratio[0]
        cfg_bak = cfg.deepcopy()
        for name, value in model.named_parameters():
            value.requires_grad = True
        time.sleep(2)
        train_detector(model, datasets, cfg,
                       distributed=distributed,
                       validate=args.no_validate,
                       timestamp=timestamp, meta=meta)
        cfg = cfg_bak

    # save the model to checkpoint
    save_checkpoint(model, args.model, meta=cfg.checkpoint_config.meta)


if __name__ == '__main__':
    main()
