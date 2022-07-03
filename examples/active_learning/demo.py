import argparse
import numpy as np
import torch
from utils import get_dataset, get_net, get_strategy
from pprint import pprint
from cmflib import cmf
from linear_regression import LinearPredictor
import matplotlib.pyplot as plt
import matplotlib

#matplotlib.use('Agg')
parser = argparse.ArgumentParser()
parser.add_argument('--seed', type=int, default=1, help="random seed")
parser.add_argument('--n_init_labeled', type=int, default=10000, help="number of init labeled samples")
parser.add_argument('--n_query', type=int, default=10, help="number of queries per round")
parser.add_argument('--n_round', type=int, default=10, help="number of rounds")
parser.add_argument('--dataset_name', type=str, default="MNIST", choices=["MNIST", "FashionMNIST", "SVHN", "CIFAR10"], help="dataset")
parser.add_argument('--enable_df', type=bool, default=False, help="Enable df")
parser.add_argument('--df_strategy_weight', type=float, default=0.5, help="weight of the strategy")
parser.add_argument('--df_pipeline_name', type=str, default="active-learning-dvc-withdeps", help="Strategy datafoundation") 
parser.add_argument('--df_strategy_name', type=str, default="KMeansSampling", help="Strategy datafoundation") 
parser.add_argument('--strategy_name', type=str, default="EntropySampling", 
                    choices=["RandomSampling", 
                             "LeastConfidence", 
                             "MarginSampling", 
                             "EntropySampling", 
                             "LeastConfidenceDropout", 
                             "MarginSamplingDropout", 
                             "EntropySamplingDropout", 
                             "KMeansSampling",
                             "KCenterGreedy", 
                             "BALDDropout", 
                             "AdversarialBIM", 
                             "AdversarialDeepFool"], help="query strategy")
args = parser.parse_args()
pprint(vars(args))
print()


###-- Preparation Stage --###
metawriter = cmf.Cmf(filename="mlmd", pipeline_name=args.df_pipeline_name, graph=True)
_ = metawriter.create_context(pipeline_stage="Prepare", custom_properties=vars(args))
_ = metawriter.create_execution(execution_type="Prepare", custom_properties=vars(args))

# fix random seed
np.random.seed(args.seed)
torch.manual_seed(args.seed)
torch.backends.cudnn.enabled = False

# device
use_cuda = torch.cuda.is_available()
device = torch.device("cuda" if use_cuda else "cpu")

dataset = get_dataset(args.dataset_name)                   # load dataset

#--cmf--#
original_folder_path = "data/"+args.dataset_name
_ = metawriter.log_dataset(original_folder_path, "output", custom_properties={"Type": args.dataset_name})

net = get_net(args.dataset_name, device)                   # load network
strategy = get_strategy(args.strategy_name)(dataset, net)  # load strategy
strategy_df = get_strategy(args.df_strategy_name)(dataset, net)
# start experiment
dataset.initialize_labels(args.n_init_labeled)
print(f"number of labeled pool: {args.n_init_labeled}")
print(f"number of unlabeled pool: {dataset.n_pool-args.n_init_labeled}")
print(f"number of testing pool: {dataset.n_test}")
print()

###-- Selection Stage --###
metawriter2 = cmf.Cmf(filename="mlmd", pipeline_name=args.df_pipeline_name, graph=True)
_ = metawriter2.create_context(pipeline_stage="Selected-0")
_ = metawriter2.create_execution(execution_type="Selected", custom_properties={"n_init_labeled":args.n_init_labeled,\
                "n_pool-args-n_init_labeled":dataset.n_pool-args.n_init_labeled, "n_test":dataset.n_test})
_ = metawriter2.log_dataset(original_folder_path, "input", custom_properties={"Type": args.dataset_name})


# round 0 accuracy
print("Round 0")
labeled_idxs, labeled_data = strategy.dataset.get_labeled_data()
path = "data/round-0.txt"
np.savetxt(path, torch.Tensor(labeled_idxs).numpy())

#--cmf--#
_ = metawriter2.log_dataset(path, "output", custom_properties={"Type": args.dataset_name})




###-- Train Stage --###
metawriter2 = cmf.Cmf(filename="mlmd", pipeline_name=args.df_pipeline_name, graph=True)
_ = metawriter2.create_context(pipeline_stage="Train-0")
_ = metawriter2.create_execution(execution_type="Train", custom_properties={"n_init_labeled":args.n_init_labeled,\
                "n_pool-args-n_init_labeled":dataset.n_pool-args.n_init_labeled, "n_test":dataset.n_test})

_ = metawriter2.log_dataset(path, "input", custom_properties={"Type": args.dataset_name})
strategy.train()

#saving the model
model_path = "data/model-" + str(0)
strategy.save_model(model_path)

_ = metawriter2.log_model(model_path, "output", model_framework="Torch", model_type="CNN",
        model_name=args.dataset_name
    )
print(model_path)
###-- Evaluate Stage --###

_ = metawriter2.create_context(pipeline_stage="Evaluate-"+str(0))
_ = metawriter2.create_execution(execution_type="Evaluate", custom_properties={"n_init_labeled":args.n_init_labeled,\
                "n_pool-args_n_init_labeled":dataset.n_pool-args.n_init_labeled, "n_test":dataset.n_test})

preds = strategy.predict(dataset.get_test_data(), model_path)


#--cmf--#

_ = metawriter2.log_model(model_path, "input", model_framework="Torch", model_type="CNN",
        model_name=args.dataset_name
)
print(f"Round 0 testing accuracy: {dataset.cal_test_acc(preds)}")
accuracy = dataset.cal_test_acc(preds)

_ = metawriter2.log_execution_metrics("Test", {"accuracy":accuracy})
prev_model = model_path
