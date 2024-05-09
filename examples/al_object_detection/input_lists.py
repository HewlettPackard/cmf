import argparse
import os
import os.path as osp
import uuid
import json

from mmcv import Config

import mmcv
import numpy as np
from mmdet.apis import set_random_seed
from mmdet.utils import get_root_logger

def parse_args():
    parser = argparse.ArgumentParser(
        description='Input lists of labeled and unlabeled images')
    parser.add_argument('config', help='train config file path')
    parser.add_argument('--labeled',
        help='file with list of labaled training samples')
    parser.add_argument('--unlabeled',
        help='file with list of unlabeled samples to consider for training')
    parser.add_argument('--train',
        help='file with list of all training samples')
    parser.add_argument('--selected',
        help='numpy file with indexes of selected samples from training list')
    parser.add_argument('--unselected',
        help='numpy file with indexes of unselected samples from training list')
    parser.add_argument('--work_directory',
                        help='the dir to save logs and model checkpoints')
    parser.add_argument('--seed', type=int, default=666, help='random seed')
    parser.add_argument('--deterministic', action='store_true',
        help='whether to set deterministic options for CUDNN backend.')
    
    parser.add_argument('--stage_name', help='Name for current execution')

    parser.add_argument('--execution_name', help='Name for current execution')

    args = parser.parse_args()
    return args

def main():
    args = parse_args()


    assert (args.labeled and args.unlabeled and 
            args.train and args.selected and args.unselected), \
        ('Plase specify file names of labeled and unlabeled '
         'image list text files with arguments "--labeled" and "--unlabeled". '
         'Also specify file name of the list of all samples created by this '
         'code with argument "--train" and file names for indexes of labeled '
         'and unselected samples in this file with arguments "--selected" and '
         '"--unselected".')

    cfg = Config.fromfile(args.config)

    # work_directory is determined in this priority: CLI > config > default
    if args.work_directory is not None:
        # update work_directory from CLI args if args.work_directory is not None
        cfg.work_directory = args.work_directory
    elif cfg.get('work_directory', None) is None:
        # derive work_directory from config name if cfg.work_directory is None
        cfg.work_directory = osp.join('./work_dirs',
                                     osp.splitext(osp.basename(args.config))[0])

    stage_name = args.stage_name
    os.environ['stage_name'] = stage_name

    execution_name = args.execution_name
    os.environ['execution_name'] = execution_name

    # create work_directory
    mmcv.mkdir_or_exist(osp.abspath(cfg.work_directory))

    # init the logger before other steps
    log_file = osp.join(cfg.work_directory, 'input_sample_lists.log')
    logger = get_root_logger(log_file=log_file, log_level=cfg.log_level)

    # set random seed
    if args.seed is not None:
        logger.info(
         f'Set random seed to {args.seed}, deterministic: {args.deterministic}')
        set_random_seed(args.seed, deterministic=args.deterministic)
    cfg.seed = args.seed

    # create and save sample lists 
    with open(args.labeled) as f:
        line = f.readline().strip()
    num_digits = len(line)
    #labeled = np.loadtxt(args.labeled, dtype=np.uintc)
    #unlabeled = np.loadtxt(args.unlabeled, dtype=np.uintc)
    labeled = np.loadtxt(args.labeled, dtype=str)
    unlabeled = np.loadtxt(args.unlabeled, dtype=str)
    num_labeled = len(labeled)
    all = np.concatenate((labeled, unlabeled))
    all_sorted_indexes = np.argsort(all)
    all = all[all_sorted_indexes]
    labeled_indexes = np.nonzero(all_sorted_indexes < num_labeled)[0]
    unlabeled_indexes = np.nonzero(all_sorted_indexes >= num_labeled)[0]
    num_unlabeled = len(unlabeled_indexes)
    if num_unlabeled >= num_labeled :
        np.random.shuffle(unlabeled_indexes)
        unlabeled_indexes = unlabeled_indexes[:num_labeled]
    else :
        np.random.shuffle(labeled_indexes)
        unlabeled_indexes = np.concatenate(
            (unlabeled_indexes, labeled_indexes[:num_labeled - num_unlabeled]))
    labeled_indexes.sort()
    unlabeled_indexes.sort()
    #np.savetxt(args.train, all, fmt='%0'+str(num_digits)+'u')
    np.savetxt(args.train, all, fmt='%s')
    np.save(args.selected, labeled_indexes)
    np.save(args.unselected, unlabeled_indexes)

    my_uuid = str(uuid.uuid4())
    dict_ = {'uuid_var': my_uuid}
    with open('uuid.json','w') as f:
        json.dump(dict_, f) 

if __name__ == '__main__':
    main()
