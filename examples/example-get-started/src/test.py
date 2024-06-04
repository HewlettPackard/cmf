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
import collections
import os
import json
import math
import pickle
import click
import sklearn.metrics as metrics
from cmflib import cmf

__all__ = ['test']


def test(model_dir: str, dataset_dir: str, output_dir: str) -> None:
    """ Test machine learning model.
    Args:
        model_dir: Path to a directory containing model.pkl file.
        dataset_dir: Path to a directory containing test.tsv file.
        output_dir: Path to a dataset that will contain several files with performance metrics (scores.json, prc.json
            and roc.json).

    Machine Learning Artifacts:
        Input: ${model_dir}/model.pkl, ${dataset_dir}/test.pkl
        Output: ExecutionMetrics
    """
    os.makedirs(output_dir, exist_ok=True)
    Artifacts = collections.namedtuple('Artifacts', ['model', 'dataset', 'scores', 'prc', 'roc'])
    artifacts = Artifacts(
        model=os.path.join(model_dir, 'model.pkl'),
        dataset=os.path.join(dataset_dir, "test.pkl"),
        scores=os.path.join(output_dir, 'scores.json'),
        prc=os.path.join(output_dir, 'prc.json'),
        roc=os.path.join(output_dir, 'roc.json')
    )
    graph_env = os.getenv("NEO4J", "False")
    graph = True if graph_env == "True" or graph_env == "TRUE" else False
    metawriter = cmf.Cmf(filepath="mlmd", pipeline_name="Test-env", graph=graph)
    _ = metawriter.create_context(pipeline_stage="Evaluate")
    _ = metawriter.create_execution(execution_type="Evaluate-execution")

    # TODO: Sergey - how do I know these custom properties here?
    metawriter.log_model(
        path=artifacts.model, event="input", model_framework="sklearn", model_type="RandomForest",
        model_name="RandomForest_default"
    )
    _ = metawriter.log_dataset(artifacts.dataset, "input")

    with open(artifacts.model, "rb") as fd:
        model = pickle.load(fd)
    with open(artifacts.dataset, "rb") as fd:
        dataset = pickle.load(fd)

    labels = dataset[:, 1].toarray()
    x = dataset[:, 2:]

    predictions_by_class = model.predict_proba(x)
    predictions = predictions_by_class[:, 1]

    precision, recall, prc_thresholds = metrics.precision_recall_curve(labels, predictions)
    fpr, tpr, roc_thresholds = metrics.roc_curve(labels, predictions)

    avg_prec = metrics.average_precision_score(labels, predictions)
    roc_auc = metrics.roc_auc_score(labels, predictions)

    # ROC has a drop_intermediate arg that reduces the number of points.
    # https://scikit-learn.org/stable/modules/generated/sklearn.metrics.roc_curve.html#sklearn.metrics.roc_curve.
    # PRC lacks this arg, so we manually reduce to 1000 points as a rough estimate.
    nth_point = math.ceil(len(prc_thresholds) / 1000)
    prc_points = list(zip(precision, recall, prc_thresholds))[::nth_point]
    with open(artifacts.prc, "w") as fd:
        json.dump(
            {
                "prc": [
                    {"precision": p, "recall": r, "threshold": t}
                    for p, r, t in prc_points
                ]
            },
            fd,
            indent=4,
        )

    with open(artifacts.roc, "w") as fd:
        json.dump(
            {
                "roc": [
                    {"fpr": fp, "tpr": tp, "threshold": t}
                    for fp, tp, t in zip(fpr, tpr, roc_thresholds)
                ]
            },
            fd,
            indent=4,
        )

    exec_metrics = dict(avg_prec=avg_prec, roc_auc=roc_auc)
    with open(artifacts.scores, "w") as fd:
        json.dump(exec_metrics, fd, indent=4)
    _ = metawriter.log_execution_metrics("metrics", exec_metrics)


@click.command()
@click.argument('model_dir', required=True, type=str)
@click.argument('dataset_dir', required=True, type=str)
@click.argument('output_dir', required=True, type=str)
def test_cli(model_dir: str, dataset_dir: str, output_dir: str) -> None:
    test(model_dir, dataset_dir, output_dir)


if __name__ == '__main__':
    test_cli()
