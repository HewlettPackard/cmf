import argparse
import os
import os.path as osp
import time

from mmcv import Config

import mmcv
import numpy as np
from mmdet.apis import set_random_seed
from mmdet.utils import collect_env, get_root_logger
#from mmdet.utils.active_datasets import *
from mmdet.utils.hdc.active_datasets import *


def parse_args():
    parser = argparse.ArgumentParser(description='Initial random selection')
    parser.add_argument('config', help='train config file path')
    parser.add_argument('--labeled_next',
                        help='initial labeled samples list file')
    parser.add_argument('--unselected', help='unselected samples list file')
    parser.add_argument('--work_directory',
                        help='the dir to save logs and model checkpoints')
    parser.add_argument('--seed', type=int, default=666, help='random seed')
    parser.add_argument('--deterministic', action='store_true',
        help='whether to set deterministic options for CUDNN backend.')
    args = parser.parse_args()
    return args

def main():
    args = parse_args()

    assert (args.labeled_next and args.unselected), \
        ('Plase specify file names of initially labeled and unselected '
         'image list files with arguments "--labeled_next" and "--unselected"')

    cfg = Config.fromfile(args.config)

    # work_directory is determined in this priority: CLI > config > default
    if args.work_directory is not None:
        # update work_directory from CLI args if args.work_directory is not None
        cfg.work_directory = args.work_directory
    elif cfg.get('work_directory', None) is None:
        # derive work_directory from config name if cfg.work_directory is None
        cfg.work_directory = osp.join('./work_dirs',
                                     osp.splitext(osp.basename(args.config))[0])

    # create work_directory
    mmcv.mkdir_or_exist(osp.abspath(cfg.work_directory))

    # dump config
    cfg.dump(osp.join(cfg.work_directory,
                      'initial_select_' + osp.basename(args.config)))

    # init the logger before other steps
    log_file = osp.join(cfg.work_directory, 'initial_select.log')
    logger = get_root_logger(log_file=log_file, log_level=cfg.log_level)

    # log env info
    env_info_dict = collect_env()
    env_info = '\n'.join([f'{k}: {v}' for k, v in env_info_dict.items()])
    dash_line = '-' * 60 + '\n'
    logger.info('Environment info:\n' + dash_line + env_info + '\n' + dash_line)

    # log some basic info
    logger.info(f'Config:\n{cfg.pretty_text}')

    # set random seeds
    if args.seed is not None:
        logger.info(
         f'Set random seed to {args.seed}, deterministic: {args.deterministic}')
        set_random_seed(args.seed, deterministic=args.deterministic)
    cfg.seed = args.seed

    X_L_next, X_U, X_all, all_anns = get_X_L_0(cfg)

    # save initial, randomly selected labeled and unlesected lists
    np.save(args.labeled_next, X_L_next)
    np.save(args.unselected, X_U)    

if __name__ == '__main__':
    main()
