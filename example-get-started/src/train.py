###
# Copyright (2022) Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###

import os
import pickle
import sys

import numpy as np
import yaml
from sklearn.ensemble import RandomForestClassifier
from cmflib import cmf

'''
Input : train.pkl
Output : Model.pkl
'''


params = yaml.safe_load(open("params.yaml"))["train"]

metawriter =  cmf.Cmf(filename="mlmd",
                                  pipeline_name="Test-env")
context = metawriter.create_context(pipeline_stage="Train")
execution = metawriter.create_execution(execution_type="Train-execution")

if len(sys.argv) != 3:
    sys.stderr.write("Arguments error. Usage:\n")
    sys.stderr.write("\tpython train.py features model\n")
    sys.exit(1)

input = sys.argv[1]
output = sys.argv[2]
seed = params["seed"]
n_est = params["n_est"]
min_split = params["min_split"]


metawriter.log_dataset(input+"/train.pkl", "input")

with open(os.path.join(input, "train.pkl"), "rb") as fd:
    matrix = pickle.load(fd)

labels = np.squeeze(matrix[:, 1].toarray())
x = matrix[:, 2:]

sys.stderr.write("Input matrix size {}\n".format(matrix.shape))
sys.stderr.write("X matrix size {}\n".format(x.shape))
sys.stderr.write("Y matrix size {}\n".format(labels.shape))

clf = RandomForestClassifier(
    n_estimators=n_est, min_samples_split=min_split, n_jobs=2, random_state=seed
)

clf.fit(x, labels)

with open(output, "wb") as fd:
    pickle.dump(clf, fd)

metawriter.log_model(path=output, event="output", model_framework="SKlearn", model_type="RandomForestClassifier", model_name="RandomForestClassifier:default" )

