import numpy as np
import torch
from .strategy import Strategy
from torch.nn.functional import normalize

class EntropySampling(Strategy):
    def __init__(self, dataset, net):
        super(EntropySampling, self).__init__(dataset, net)

    def query(self, n):
        unlabeled_idxs, unlabeled_data = self.dataset.get_unlabeled_data()
        probs = self.predict_prob(unlabeled_data)
        log_probs = torch.log(probs)
        uncertainties = (probs*log_probs).sum(1)
        return unlabeled_idxs[uncertainties.sort()[1][:n]]

    def query_scores(self, n):
        unlabeled_idxs, unlabeled_data = self.dataset.get_unlabeled_data()
        probs = self.predict_prob(unlabeled_data)
        log_probs = torch.log(probs)

        uncertainties = (probs*log_probs).sum(1)
        min_value = torch.min(uncertainties)
        uncertainties = torch.add(uncertainties, abs(min_value))

        tc = normalize(uncertainties, p=2.0, dim = 0)    
        #scores = torch.zeros([len(unlabeled_idxs), 2])
        scores = torch.stack((torch.from_numpy(unlabeled_idxs), tc), 0)
        #scores = torch.tensor([torch.tensor(unlabeled_idxs), tc])
        #t = torch.zeros([2,n])
        #A namedtuple of (values, indices) is returned, 
        #where the values are the sorted values and 
        #indices are the indices of the elements in the original input tensor.
        #Indexes - uncertainties.sort()[1][:n](sort in ascending order and return the top n indexes)
        #unlabeled_idxs[uncertainties.sort()[1][:n]] - get the unleabeled index value from the the sorted indexes
        #t[0] = torch.from_numpy(unlabeled_idxs[uncertainties.sort()[1][:n]])#Indexes - uncertainties.sort()[1][:n](ascending order
        #t[1] = uncertainties.sort()[0][:n] #values
        return scores

