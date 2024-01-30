import mmcv
import numpy as np
import time
import random

def get_X_L_0(cfg):
    # load dataset anns
    anns = load_ann_list(cfg.data.train.dataset.ann_file)
    # get all indexes
    X_all = np.arange(len(anns[0]))
    # randomly select labeled set
    np.random.shuffle(X_all)
    X_L = X_all[:cfg.X_L_0_size].copy()
    X_U = X_all[-cfg.X_L_0_size:].copy()
    #X_U = [0]*cfg.X_L_0_size

    X_L.sort()
    X_U.sort()
    return X_L, X_U, X_all, anns


def create_X_L_file(cfg, X_L, anns, cycle):
    # split labeled set into 2007 and 2012
    # create labeled ann files
    X_L_path = []
    save_folder = cfg.work_directory + '/cycle' + str(cycle)
    mmcv.mkdir_or_exist(save_folder)
    path = save_folder + '/trainval_X_L' + '.txt'
    time.sleep(random.uniform(0,3))
    np.savetxt(path, anns[0][X_L], fmt='%s')
    X_L_path.append(path)
    # update cfg
    cfg.data.train.dataset.ann_file = X_L_path
    cfg.data.train.times = cfg.X_L_repeat
    return cfg


def create_X_U_file(cfg, X_U, anns, cycle):
    # split unlabeled set into 2007 and 2012
    # create labeled ann files
    X_U_path = []
    time.sleep(random.uniform(0,3))
    save_folder = cfg.work_directory + '/cycle' + str(cycle)
    mmcv.mkdir_or_exist(save_folder)
    path = save_folder + '/trainval_X_U'+'.txt'
    np.savetxt(path, anns[0][X_U], fmt='%s')
    X_U_path.append(path)
    # update cfg
    cfg.data.train.dataset.ann_file = X_U_path
    cfg.data.train.times = cfg.X_U_repeat
    return cfg


def load_ann_list(paths):
    anns = []
    for path in paths:
        anns.append(np.loadtxt(path, dtype='str'))
    return anns


def update_X_L(uncertainty, X_all, X_L, X_S_size, return_X_S=False):
    uncertainty = uncertainty.cpu().numpy()
    all_X_U = np.array(list(set(X_all) - set(X_L)))
    uncertainty_X_U = uncertainty[all_X_U]
    arg = uncertainty_X_U.argsort()
    X_S = all_X_U[arg[-X_S_size:]]
    X_L_next = np.concatenate((X_L, X_S))
    all_X_U_next = np.array(list(set(X_all) - set(X_L_next)))
    np.random.shuffle(all_X_U_next)
    X_U_next = all_X_U_next[:X_L_next.shape[0]]
    if X_L_next.shape[0] > X_U_next.shape[0]:
        np.random.shuffle(X_L_next)
        X_U_next = np.concatenate((X_U_next, X_L_next[:X_L_next.shape[0] - X_U_next.shape[0]]))
    X_L_next.sort()
    X_U_next.sort()
    if return_X_S:
        return X_L_next, X_U_next, X_S
    else:
        return X_L_next, X_U_next
