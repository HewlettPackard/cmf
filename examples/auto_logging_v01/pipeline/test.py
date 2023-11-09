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

from sklearn.metrics import accuracy_score
from sklearn.tree import DecisionTreeClassifier

from cmflib.cmf import Cmf
from cmflib.contrib.auto_logging_v01 import Context, Dataset, ExecutionMetrics, MLModel, cli_run, step


@step()
def test(ctx: Context, test_dataset: Dataset, model: MLModel) -> t.Dict[str, ExecutionMetrics]:
    """Test a decision tree classifier on a test dataset.

    This example demonstrates the automated logging of output execution metrics. In your python code:
    ```python
    from cmflib.contrib.auto_logging_v01 import cli_run

    if __name__ == '__main__':
        # python pipeline/test.py test_dataset=workspace/test.pkl model=workspace/model.pkl
        cli_run(test)
    ```

    Args:
        ctx: Context for this step.
            May contain:
                - `workspace`: directory path to store artifacts.
            Will contain:
                - `cmf`: an initialized instance of the Cmf class (no need to call create_context and create_stage).
                    No need to log output artifacts as well - just return them.
        test_dataset: Input test dataset (e.g., produced by the `preprocess` step).
        model: Input ML model (e.g., produced by the `train` step).

    Returns:
        Dictionary that maps an artifact name to artifact description. Names are not used to automatically log artifacts
            to Cmf, only artifacts themselves. The return dictionary will contain one item - `exec_metrics`.
    """

    with open(test_dataset.uri, "rb") as stream:
        dataset: t.Dict = pickle.load(stream)

    with open(model.uri, "rb") as stream:
        clf: DecisionTreeClassifier = pickle.load(stream)

    test_accuracy = accuracy_score(y_true=dataset["y"], y_pred=clf.predict(dataset["x"]))

    # TODO: Fix URI for execution metrics. What should it be?
    cmf: Cmf = ctx["cmf"]
    return {
        "exec_metrics": ExecutionMetrics(
            uri=str(cmf.execution.id) + "/metrics/test", name="test", params={"accuracy": test_accuracy}
        )
    }


if __name__ == "__main__":
    """
    ```shell
    python pipeline/test.py test_dataset=workspace/test.pkl model=workspace/model.pkl
    ```
    """
    cli_run(test)
