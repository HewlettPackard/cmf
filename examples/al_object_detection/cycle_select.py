import argparse
import os
import os.path as osp
import time

import mmcv
import torch
import random
import numpy as np
from mmcv import Config, DictAction
from mmcv.parallel import MMDataParallel, MMDistributedDataParallel
from mmcv.runner import init_dist, load_checkpoint
from tools.fuse_conv_bn import fuse_module

from mmdet import __version__
from mmdet.apis import set_random_seed, single_gpu_test, calculate_uncertainty
from mmdet.core import wrap_fp16_model
from mmdet.datasets import build_dataloader, build_dataset
from mmdet.models import build_detector
from mmdet.utils import collect_env, get_root_logger
from mmdet.utils.active_datasets import *


def parse_args():
    parser = argparse.ArgumentParser(description='Select informative images')
    parser.add_argument('config', help='train config file path')
    parser.add_argument('--cycle', help='active learning iteration >= 0')
    parser.add_argument('--model', help='model checkpoint file')
    parser.add_argument('--labeled', help='labeled samples list file')
    parser.add_argument('--labeled_next',
                        help='next cycle labeled samples list file')
    parser.add_argument('--unselected', help='unselected samples list file')
    parser.add_argument('--work_directory',
                        help='the dir to save logs and model checkpoints')
    parser.add_argument(
            '--fuse-conv-bn',
            action='store_true',
            help='Whether to fuse conv and bn, this will slightly increase'
            'the inference speed')
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
    args = parser.parse_args()
    if 'LOCAL_RANK' not in os.environ:
        os.environ['LOCAL_RANK'] = str(args.local_rank)
    return args


def main():
    args = parse_args()

    assert (args.cycle and args.model and args.labeled and
            args.labeled_next and args.unselected), \
        ('Please specify active learning cycle, model checkpoint file name '
         'and file names of labeled, next cycle labeled and unselected '
         'image list files with arguments "--cycle", "--model", "--labeled", '
         '"--labeled_next" and "--unselected"')

    cfg = Config.fromfile(args.config)
    if args.options is not None:
        cfg.merge_from_dict(args.options)

    # set cudnn_benchmark
    if cfg.get('cudnn_benchmark', False):
        torch.backends.cudnn.benchmark = True

    # no pretrained parts - model will be later loaded from file
    cfg.model.pretrained = None
    if cfg.model.get('neck'):
        if cfg.model.neck.get('rfp_backbone'):
            if cfg.model.neck.rfp_backbone.get('pretrained'):
                cfg.model.neck.rfp_backbone.pretrained = None

    # work_directory is determined in this priority: CLI > config > default
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

    # dump config
    cfg.dump(osp.join(cfg.work_directory,
                      f'cycle_select{args.cycle}_' + osp.basename(args.config)))

    # init the logger before other steps
    log_file = osp.join(cfg.work_directory, f'cycle_select{args.cycle}.log')
    logger = get_root_logger(log_file=log_file, log_level=cfg.log_level)

    # log env info
    env_info_dict = collect_env()
    env_info = '\n'.join([f'{k}: {v}' for k, v in env_info_dict.items()])
    dash_line = '-' * 60 + '\n'
    logger.info('Environment info:\n' + dash_line + env_info + '\n' + dash_line)

    # log some basic info
    logger.info(f'Distributed training: {distributed}')
    logger.info(f'Config:\n{cfg.pretty_text}')

    # set random seeds
    if args.seed is not None:
        logger.info( 
         f'Set random seed to {args.seed}, deterministic: {args.deterministic}')
        set_random_seed(args.seed, deterministic=args.deterministic)
    cfg.seed = args.seed

    # build the dataloader
    dataset = build_dataset(cfg.data.test)
    data_loader = build_dataloader(dataset, samples_per_gpu=1,
                                   workers_per_gpu=cfg.data.workers_per_gpu,
                                   dist=False, shuffle=False)

    # build the model and load checkpoint
    model = build_detector(cfg.model, train_cfg=None, test_cfg=cfg.test_cfg)
    fp16_cfg = cfg.get('fp16', None)
    if fp16_cfg is not None:
        wrap_fp16_model(model)
    checkpoint = load_checkpoint(model, args.model, map_location='cpu')
    if args.fuse_conv_bn:
        model = fuse_module(model)

    # calculate uncertainty
    uncertainty = calculate_uncertainty(cfg, model, data_loader,
                                        return_box=False)

    # update labeled set 
    all_anns = load_ann_list(cfg.data.train.dataset.ann_file)
    if len(all_anns[0]) == 1:
        X_all = np.arange(len(all_anns))
    else:
        j = 0
        for i in range(len(all_anns)):
            j += len(all_anns[i])
        X_all = np.arange(j) 
    X_L = np.load(args.labeled)
    X_L_next, X_U = update_X_L(uncertainty, X_all, X_L, cfg.X_S_size)

    # save next cycle labeled and unlesected lists
    np.save(args.labeled_next, X_L_next)
    np.save(args.unselected, X_U)


if __name__ == '__main__':
    main()
