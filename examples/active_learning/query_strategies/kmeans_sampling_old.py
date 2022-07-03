import numpy as np
from .strategy import Strategy
from sklearn.cluster import KMeans

class KMeansSampling(Strategy):
    def __init__(self, dataset, net):
        super(KMeansSampling, self).__init__(dataset, net)

    def query(self, n):
        unlabeled_idxs, unlabeled_data = self.dataset.get_unlabeled_data()
        embeddings = self.get_embeddings(unlabeled_data)
        embeddings = embeddings.numpy()
        print("n is " + str(n))
        cluster_learner = KMeans(n_clusters=n)
        cluster_learner.fit(embeddings)
        print("embedding shape")
        print(embeddings.shape)
        cluster_idxs = cluster_learner.predict(embeddings)
        print("Printing cluster length")
        print((cluster_idxs.shape))
        print("printing cluster idx")
        print(cluster_idxs)
        centers = cluster_learner.cluster_centers_[cluster_idxs]
        print("length of centers")
        print((centers.shape))
        dis = (embeddings - centers)**2
        print("printnig shape")
        print(len(dis))
        print(dis)
        dis = dis.sum(axis=1)
        print("priting distance")
        print(dis[0])
        print("embedding shape 0")
        print(embeddings.shape[0])
        print("distance from cluster shape")
        print((dis[cluster_idxs==1]).shape)
        print(dis[cluster_idxs==1])
        print("distance from cluster argmin")
        for i in range(n):
            print("======")
            print([cluster_idxs==i])
            print([dis[cluster_idxs==i].argmin()])
            print([dis[cluster_idxs==i].min()])
        print([cluster_idxs==i][dis[cluster_idxs==i].argmin()] for i in range(n))

        q_idxs = np.array([np.arange(embeddings.shape[0])[cluster_idxs==i][dis[cluster_idxs==i].argmin()] for i in range(n)])
        print("index")
        print(q_idxs)
        return unlabeled_idxs[q_idxs]
