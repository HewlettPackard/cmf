import pickle
import typing as t
from cmflib.contrib.auto_logging_v01 import (cli_run, Context, Dataset, prepare_workspace, step)
from sklearn.datasets import load_iris
from sklearn.utils import Bunch


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
    dataset_uri = workspace / 'iris.pkl'
    with open(dataset_uri, 'wb') as stream:
        iris: Bunch = load_iris()
        pickle.dump(
            {'data': iris['data'], 'target': iris['target']},
            stream
        )

    return {'dataset': Dataset(dataset_uri)}


if __name__ == '__main__':
    """
    A file will be saved to workspace/iris.pkl
    ```shell
    python pipeline/fetch.py
    ```
    """
    cli_run(fetch)
