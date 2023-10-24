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

from sklearn.datasets import load_iris
from sklearn.utils import Bunch

from cmflib.contrib.auto_logging_v01 import Context, Dataset, cli_run, prepare_workspace, step


@step()
def fetch(ctx: Context) -> t.Dict[str, Dataset]:
    """Fetch IRIS dataset and serialize its data and target arrays in a pickle file.

    This example demonstrates automated logging of output datasets. In your python code:
    ```python
    from cmflib.contrib.auto_logging_v01 import cli_run

    if __name__ == '__main__':
        # python pipeline/fetch.py
        cli_run(fetch)
    ```

    Args:
        ctx: Context for this step.
            May contain:
                - `workspace`: directory path to store artifacts.
            Will contain:
                - `cmf`: an initialized instance of the Cmf class (no need to call create_context and create_stage).
                    No need to log output artifacts as well - just return them.

    Returns:
        Dictionary that maps an artifact name to artifact description. Names are not used to automatically log artifacts
            to Cmf, only artifacts themselves.
    """
    workspace = prepare_workspace(ctx)
    dataset_uri = workspace / "iris.pkl"
    with open(dataset_uri, "wb") as stream:
        iris: Bunch = load_iris()
        pickle.dump({"data": iris["data"], "target": iris["target"]}, stream)

    return {"dataset": Dataset(dataset_uri)}


if __name__ == "__main__":
    """
    A file will be saved to workspace/iris.pkl
    ```shell
    python pipeline/fetch.py
    ```
    """
    cli_run(fetch)
