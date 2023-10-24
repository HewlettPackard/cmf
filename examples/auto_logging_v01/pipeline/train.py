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

import pickle
import typing as t
from pathlib import Path

from sklearn.metrics import accuracy_score
from sklearn.tree import DecisionTreeClassifier

from cmflib.cmf import Cmf
from cmflib.contrib.auto_logging_v01 import (
    Context,
    Dataset,
    ExecutionMetrics,
    MLModel,
    Parameters,
    cli_run,
    prepare_workspace,
    step,
)


@step()
def train(ctx: Context, params: Parameters, train_dataset: Dataset) -> t.Dict[str, t.Union[MLModel, ExecutionMetrics]]:
    """Train a decision tree classifier.

    This example demonstrates automated logging of output models and execution metrics. In your python code:
    ```python
    from cmflib.contrib.auto_logging_v01 import cli_run

    if __name__ == '__main__':
        # python pipeline/train.py dataset=workspace/train.pkl
        cli_run(train)
    ```

    Args:
        ctx: Context for this step.
            May contain:
                - `workspace`: directory path to store artifacts.
            Will contain:
                - `cmf`: an initialized instance of the Cmf class (no need to call create_context and create_stage).
                    No need to log output artifacts as well - just return them.
        params: Execution parameters. Not used now in this implementation.
        train_dataset: Input train dataset (e.g., produced by the `preprocess` step).

    Returns:
        Dictionary that maps an artifact name to artifact description. Names are not used to automatically log artifacts
            to Cmf, only artifacts themselves. The return dictionary will contain two items - `model` and
            `exec_metrics`.
    """
    with open(train_dataset.uri, "rb") as stream:
        dataset: t.Dict = pickle.load(stream)

    clf = DecisionTreeClassifier()
    clf = clf.fit(dataset["x"], dataset["y"])
    train_accuracy = accuracy_score(y_true=dataset["y"], y_pred=clf.predict(dataset["x"]))

    workspace: Path = prepare_workspace(ctx)
    with open(workspace / "model.pkl", "wb") as stream:
        pickle.dump(clf, stream)

    # TODO: Fix URI for execution metrics. What should it be?
    cmf: Cmf = ctx["cmf"]
    return {
        "model": MLModel(workspace / "model.pkl"),
        "exec_metrics": ExecutionMetrics(
            uri=str(cmf.execution.id) + "/metrics/train", name="train", params={"accuracy": train_accuracy}
        ),
    }


if __name__ == "__main__":
    """
    A model will be saved to workspace/model.pkl
    ```shell
    python pipeline/train.py dataset=workspace/train.pkl
    ```
    """
    cli_run(train)
