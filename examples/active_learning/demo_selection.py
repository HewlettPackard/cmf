import argparse
import numpy as np
import torch
from utils import get_dataset, get_net, get_strategy, get_trained_net
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
parser.add_argument('--trained_model', type=str, default="model", help="path of trained model")
parser.add_argument('--dataset_name', type=str, default="MNIST", choices=["MNIST", "FashionMNIST", "SVHN", "CIFAR10"], help="dataset")
parser.add_argument('--enable_df', type=bool, default=False, help="Enable df")
parser.add_argument('--df_strategy_weight', type=float, default=0.5, help="weight of the strategy")
parser.add_argument('--df_pipeline_name', type=str, default="active-learning-dvc-withdeps", help="Strategy datafoundation") 
parser.add_argument('--df_strategy_name', type=str, default="KMeansSampling", help="Strategy datafoundation") 
parser.add_argument('--round', type=int, default=1, help="round") 
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
rd = args.round


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
#model_path = args.trained_model+"-"+str(rd-1)
model_path = args.trained_model
net = get_trained_net(args.dataset_name, device, model_path)                   # load network
strategy = get_strategy(args.strategy_name)(dataset, net)  # load strategy
strategy_df = get_strategy(args.df_strategy_name)(dataset, net)
# start experiment
dataset.initialize_labels(args.n_init_labeled)
print(f"number of labeled pool: {args.n_init_labeled}")
print(f"number of unlabeled pool: {dataset.n_pool-args.n_init_labeled}")
print(f"number of testing pool: {dataset.n_test}")
print()

prev_model = model_path
print(prev_model)



###-- Selection Stage --###
metawriter2 = cmf.Cmf(filename="mlmd", pipeline_name=args.df_pipeline_name, graph=True)
_ = metawriter2.create_context(pipeline_stage="Selection-"+str(rd))
_ = metawriter2.create_execution(execution_type="Selection", custom_properties={"n_init_labeled":args.n_init_labeled,\
                "n_pool-args_n_init_labeled":dataset.n_pool-args.n_init_labeled, "n_test":dataset.n_test})

_ = metawriter2.log_dataset(original_folder_path, "input", custom_properties={"Type": args.dataset_name})

_ = metawriter2.log_model(prev_model, "input", model_framework="Torch", model_type="CNN",
        model_name=args.dataset_name
    )
# query
if args.enable_df is True:
#query_idxs = strategy.query(args.n_query)

    print("Came to data foundation")

    selection_df = cmf.Cmf(filename="mlmd", pipeline_name=args.df_pipeline_name, graph=True)
    _ = selection_df.create_context(pipeline_stage="DatafoundationSelection-"+str(rd))
    _ = selection_df.create_execution(execution_type="DatafoundationSelection", custom_properties={"n_init_labeled":args.n_init_labeled,\
                "n_pool-args_n_init_labeled":dataset.n_pool-args.n_init_labeled, "n_test":dataset.n_test})

    _ = selection_df.log_dataset(original_folder_path, "input", custom_properties={"Type": args.dataset_name})

    _ = selection_df.log_model(prev_model, "input", model_framework="Torch", model_type="CNN",
        model_name=args.dataset_name
        )  

    scores = strategy.query_scores(args.n_query)
    scores_df = strategy_df.query_scores(args.n_query)

    scores_df_file = "data/dfscores-round-"+str(rd)+".txt"
    np.savetxt(scores_df_file, scores_df.numpy())
    _ = selection_df.log_dataset(scores_df_file, "output", custom_properties={"Type": args.df_strategy_name})

    stratgey_scores = "data/scores-round-"+str(rd)+".txt"
    np.savetxt(stratgey_scores, scores.numpy())
    _ = metawriter2.log_dataset(stratgey_scores, "output", custom_properties={"Type": args.strategy_name})
    #cumulative_scores = scores[1]+0.7*scores_df[1]
    cumulative_scores = torch.add(scores[1], scores_df[1], alpha=args.df_strategy_weight)
    query_idxs = scores[0][[cumulative_scores.sort()[1][:args.n_query]]]


    scoring_df = cmf.Cmf(filename="mlmd", pipeline_name=args.df_pipeline_name, graph=True)
    _ = scoring_df.create_context(pipeline_stage="Scoring-"+str(rd))
    _ = scoring_df.create_execution(execution_type="Scoring", custom_properties={"n_init_labeled":args.n_init_labeled,\
                "n_pool-args_n_init_labeled":dataset.n_pool-args.n_init_labeled, "n_test":dataset.n_test})
    _ = scoring_df.log_dataset(scores_df_file, "input", custom_properties={"Type": args.dataset_name})
    _ = scoring_df.log_dataset(stratgey_scores, "input", custom_properties={"Type": args.dataset_name})


    path = "data/round-"+str(rd)+".txt"
    np.savetxt(path, torch.Tensor(query_idxs).numpy())
    _ = scoring_df.log_dataset(path, "output", custom_properties={"Weight": args.df_strategy_weight})
    query_idxs = query_idxs.int()

else:
    query_idxs = strategy.query(args.n_query)
    path = "data/round-"+str(rd)+".txt"
    np.savetxt(path, torch.Tensor(query_idxs).numpy())
    _ = metawriter2.log_dataset(path, "output", custom_properties={"Type": args.strategy_name})

print(type(query_idxs))
print(path)
