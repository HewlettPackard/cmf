import argparse
import os
import os.path as osp
import json

from mmcv import Config

import mmcv
import numpy as np
from mmdet.apis import set_random_seed
from mmdet.utils import get_root_logger

def parse_args():
    parser = argparse.ArgumentParser(
        description='Output list of images to be labeled')
    parser.add_argument('config', help='train config file path')
    parser.add_argument('--selected',
        help='numpy file with indexes of samples labeled before this cycle')
    parser.add_argument('--selected_next',
        help='numpy file with indexes of samples to be labeled in this cycle')
    parser.add_argument('--train',
        help='file with list of all training samples')
    parser.add_argument('--map',
        help='file with mapping between image number names and full names')
    parser.add_argument('--label_next',
        help='text file with list of samples to be labeled in this cycle')
    parser.add_argument('--labeled',
        help='text file with list of all samples labeled after this cycle')
    parser.add_argument('--unlabeled',
        help='text file with list of all samples unlabeled after this cycle')
    parser.add_argument('--cycle_config',
        help='config file with active learning cycle and seed')
    parser.add_argument('--cycle_config_next',
        help='config file with next active learning cycle and seed')
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

    assert (args.selected and args.selected_next and args.train and
            args.map and args.label_next and args.labeled and
            args.unlabeled and args.cycle_config and args.cycle_config_next), \
        ('Plase specify file names of numpy lists of images labeled before '
         'this cycle and in this cycle with arguments "--selected" and '
         '"--selected_next". Also specify the file name with the list of all '
         'images that the lists of selected and unselected samples point to, '
         'with argument "--train". Then specify file name for the map between '
         'image number names and full image names with argument "--map". '
         'Finally, specify names for text files output by this code with lists '
         'of images to be labeled in this cycle, all labeled after this cycle '
         'and remaining unlabeled, with arguments "--label_next", "--labeled" '
         'and "--unlabeled". Also specify config file with active learning '
         'cycle number and random number generator seed with argument '
         '"--cycle_config" and the name of the next cycle config file output '
         'by this code with argument "--cycle_config_next"')

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

    stage_name = args.stage_name
    os.environ['stage_name'] = stage_name

    execution_name = args.execution_name
    os.environ['execution_name'] = execution_name

    # init the logger before other steps
    log_file = osp.join(cfg.work_directory, 'input_sample_lists.log')
    logger = get_root_logger(log_file=log_file, log_level=cfg.log_level)

    # set random seed
    if args.seed is not None:
        logger.info(
         f'Set random seed to {args.seed}, deterministic: {args.deterministic}')
        set_random_seed(args.seed, deterministic=args.deterministic)
    cfg.seed = args.seed

    # load the map of image number to image name
    map = {}
    with open(args.map) as f:
        for line in f:
            tokens = line.split(",")
            assert (len(tokens) == 2), \
                (f'Invalid format of file {args.map} : Expected 2 tokens '
                 'per line, received {len(tokens)} : {line}') 
            map[int(tokens[0])] = tokens[1].strip()

    # get the lists of images to label, all labeled and unlabeled
    labeled_indexes = np.load(args.selected)
    labeled_next_indexes = np.load(args.selected_next)
    to_label_indexes = np.array(list(set(labeled_next_indexes) - 
                                     set(labeled_indexes)))
    with open(args.train) as f:
        line = f.readline().strip()
    num_digits = len(line)
    all = np.loadtxt(args.train, dtype=np.uintc)
    to_label = all[to_label_indexes]
    to_label.sort()
    labeled = all[labeled_next_indexes]
    labeled.sort()
    unlabeled = np.delete(all, labeled_next_indexes)
    unlabeled.sort()

    # save the lists after converting from file numbers to file names in
    # the list of images to label
    with open(args.label_next, 'w') as f:
        for image_number in to_label:
            image_name = map[image_number]
            f.write(image_name + "\n")
    np.savetxt(args.labeled, labeled, fmt='%0'+str(num_digits)+'u')
    np.savetxt(args.unlabeled, unlabeled, fmt='%0'+str(num_digits)+'u')

    # Update active learning config file with new cycle and random number
    # generator seed
    cycle_config = {}
    with open(args.cycle_config) as f:
        cycle_config = json.load(f)
    cycle_config['al_cycle'] += 1
    cycle_config['next_cycle'] += 1
    rng = np.random.default_rng(args.seed)
    cycle_config['al_seed'] = int(rng.integers(1000))
    with open(args.cycle_config_next, "w") as f:
        json.dump(cycle_config, f, indent = 4)

if __name__ == '__main__':
    main()
