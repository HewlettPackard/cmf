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
from cmflib import cmf

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

    """Create CMF object
        mlmd - Name of the sqlite file used to store the metadata 
        active_learning - Pipeline name. All the stages of the same pipeline should 
            have the same name. The same pipeline name is used in cycle_train file and cycle_select
        graph - using neo4j backend to log the relationship. This is optional, but very
            useful to visualize the lineage chains.
    """
    logger = cmf.Cmf("mlmd", "active_learning_demo", graph=True)

    """
    CMF Logging: Create context(stage) Can be train, featurize etc
    """
    _ = logger.create_context("Initial_select", {"Strategy": "Random"})

    """
    CMF Logging: Create Execution(stage) Can be train, featurize etc
    """
    _ = logger.create_execution("Initial_select_with_5percent", {"config": cfg, "env":env_info_dict})

    folder_path = osp.join(cfg.data.train.dataset.img_prefix[0],'JPEGImages')

    """CMF Logging- Log the input dataset
       folder_path - path of the input folder
       "input" - event type , can be input or output
       custom_properties - {"gray_scale": "True", "Background_no_bounding_boxes":"True"}
       can add any metadata eg:statistical or qualitative metadata as key value pairs
    """
    logger.log_dataset(folder_path, "input", {"gray_scale": "True", "Background_no_bounding_boxes":"True"})
    X_L_next, X_U, X_all, all_anns = get_X_L_0(cfg)

    # save initial, randomly selected labeled and unlesected lists
    np.save(args.labeled_next, X_L_next)
    np.save(args.unselected, X_U)
    """CMF Logging"""
    label_next = logger.log_dataset(args.labeled_next, "output", {"cycle":"0"} )

    """CMF Logging 
    Create a DataSlice object- Slices of a dataset(currently only subset of files in a folder)
    """
    dataslice: cmf.Cmf.DataSlice = logger.create_dataslice(name="slice-0")
    uncertanity_vals = {}
    uncertanity_vals["median"] = "-1"
    uncertanity_vals["mean"] = "-1"
    for i in X_L_next:
        file_name = all_anns[0][i] + ".jpg"
        slice_path = osp.join(cfg.data.train.dataset.img_prefix[0], "JPEGImages",file_name) 
        """CMF Logging: Add data to a slice"""
        dataslice.add_data(slice_path, {"Uncertinity": "-1", "key2": "value2"})

    """CMF Logging - Commit the slice when all the data has been added"""
    slice = dataslice.commit(custom_properties = uncertanity_vals)

    """CMF Logging - Linking slice to the numpy file from which it was derived"""
    logger.link_artifacts(label_next, slice)
    logger.log_dataset(args.unselected, "output", {"cycle":"0"})    

if __name__ == '__main__':
    main()
