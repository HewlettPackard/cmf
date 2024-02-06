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

from sklearn.model_selection import train_test_split

from cmflib.contrib.auto_logging_v01 import Context, Dataset, Parameters, cli_run, prepare_workspace, step


@step()
def preprocess(ctx: Context, params: Parameters, dataset: Dataset) -> t.Dict[str, Dataset]:
    """Preprocess the IRIS dataset by splitting it into train and test datasets.

    This example demonstrates automated logging of input and output datasets. In your python code:
    ```python
    from cmflib.contrib.auto_logging_v01 import cli_run

    if __name__ == '__main__':
        # python pipeline/preprocess.py dataset=workspace/iris.pkl
        cli_run(preprocess)
    ```

    Args:
        ctx: Context for this step.
            May contain:
                - `workspace`: directory path to store artifacts.
            Will contain:
                - `cmf`: an initialized instance of the Cmf class (no need to call create_context and create_stage).
                    No need to log output artifacts as well - just return them.
        params: Execution parameters. Can contain: `train_size` (train size split ratio, default is 0.7) and `shuffle`
            (whether raw data should be shuffled before splitting, default is true).
        dataset: Input dataset (e.g., produced by the `fetch` step).

    Returns:
        Dictionary that maps an artifact name to artifact description. Names are not used to automatically log artifacts
            to Cmf, only artifacts themselves. The return dictionary will contain two items - `train_dataset` and
            `test_dataset`.
    """
    with open(dataset.uri, "rb") as stream:
        dataset: t.Dict = pickle.load(stream)

    x_train, x_test, y_train, y_test = train_test_split(
        dataset["data"],
        dataset["target"],
        train_size=float(params.get("train_size", 0.7)),
        shuffle=params.get("shuffle", "true").lower() == "true",
    )

    workspace: Path = prepare_workspace(ctx)

    with open(workspace / "train.pkl", "wb") as stream:
        pickle.dump({"x": x_train, "y": y_train}, stream)
    with open(workspace / "test.pkl", "wb") as stream:
        pickle.dump({"x": x_test, "y": y_test}, stream)

    return {"train_dataset": Dataset(workspace / "train.pkl"), "test_dataset": Dataset(workspace / "test.pkl")}


if __name__ == "__main__":
    """
    Files will be saved to workspace/train_dataset.pkl and workspace/test_dataset.pkl
    ```shell
    python pipeline/preprocess.py dataset=workspace/iris.pkl
    ```
    """
    cli_run(preprocess)
