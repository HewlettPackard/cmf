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
import sys
import yaml
import pickle
import click
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from cmflib.cmf import Cmf

__all__ = ['train']


def train(input_dir: str, output_dir: str) -> None:
    """Train Machine Learning model.
    Args:
        input_dir: Path to a directory containing train.pkl file.
        output_dir: Path to a directory that will contain model.pkl file.

    Machine Learning Artifacts:
        Input: ${input_dir}/train.pkl
        Output: ${output_dir}/model.pkl
    """
    params = yaml.safe_load(open("params.yaml"))["train"]
    graph_env = os.getenv("NEO4J", "False")
    graph = True if graph_env == "True" or graph_env == "TRUE" else False
    metawriter = Cmf(filepath="mlmd", pipeline_name="Test-env", graph=graph)
    _ = metawriter.create_context(pipeline_stage="Train")
    _ = metawriter.create_execution(execution_type="Train-execution", custom_properties=params)

    train_ds = os.path.join(input_dir, "train.pkl")
    _ = metawriter.log_dataset(train_ds, "input")
    with open(train_ds, "rb") as fd:
        matrix = pickle.load(fd)

    labels = np.squeeze(matrix[:, 1].toarray())
    x = matrix[:, 2:]

    sys.stderr.write("Input matrix size {}\n".format(matrix.shape))
    sys.stderr.write("X matrix size {}\n".format(x.shape))
    sys.stderr.write("Y matrix size {}\n".format(labels.shape))

    clf = RandomForestClassifier(
        n_estimators=params["n_est"], min_samples_split=params["min_split"], n_jobs=2, random_state=params["seed"]
    )
    clf.fit(x, labels)

    os.makedirs(output_dir, exist_ok=True)
    model_file = os.path.join(output_dir, 'model.pkl')
    with open(model_file, "wb") as fd:
        pickle.dump(clf, fd)

    _ = metawriter.log_metric("training_metrics", {"train_loss": 10})
    _ = metawriter.commit_metrics("training_metrics")

    _ = metawriter.log_model(
        path=model_file, event="output", model_framework="SKlearn", model_type="RandomForestClassifier",
        model_name="RandomForestClassifier:default"
    )
    metawriter.finalize()


@click.command()
@click.argument('input_dir', required=True, type=str)
@click.argument('output_dir', required=True, type=str)
def train_cli(input_dir: str, output_dir: str) -> None:
    train(input_dir, output_dir)


if __name__ == '__main__':
    train_cli()
