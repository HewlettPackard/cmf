import typing as t
from pathlib import Path
import click
from sklearn.metrics import accuracy_score
from sklearn.tree import DecisionTreeClassifier
import cmflib.contrib.fluent as cmf
import pickle
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.utils import Bunch


def workspace(path: t.Optional[str] = None) -> Path:
    """Return directory to read from or write to."""
    return Path(path) if path else cmf.get_work_directory() / 'workspace'


def fetch(output_dir: t.Optional[str] = None) -> None:
    """Ingest the IRIS dataset into a pipeline."""
    ds_path = workspace(output_dir) / 'iris.pkl'
    with open(ds_path, 'wb') as stream:
        iris: Bunch = load_iris()
        pickle.dump({'data': iris['data'], 'target': iris['target']}, stream)
    cmf.log_dataset(ds_path, 'output', properties={'name': 'iris', 'type': 'raw'})


def preprocess(params: t.Optional[t.Dict] = None,
               input_dir: t.Optional[str] = None, output_dir: t.Optional[str] = None) -> None:
    """Split raw dataset into train/test splits."""
    params = params or {}
    ds_path = workspace(input_dir) / 'iris.pkl'
    with open(ds_path, 'rb') as stream:
        dataset: t.Dict = pickle.load(stream)
    cmf.log_dataset(ds_path, 'input')

    x_train, x_test, y_train, y_test = train_test_split(
        dataset['data'],
        dataset['target'],
        train_size=float(params.get('train_size', 0.7)),
        shuffle=params.get('shuffle', 'true').lower() == 'true'
    )

    ds_path = workspace(output_dir) / 'train.pkl'
    with open(ds_path, 'wb') as stream:
        pickle.dump({'x': x_train, 'y': y_train}, stream)
    cmf.log_dataset(ds_path, 'output', properties={'name': 'iris', 'type': 'preprocessed', 'split': 'train'})

    d_path = workspace(output_dir) / 'test.pkl'
    with open(d_path, 'wb') as stream:
        pickle.dump({'x': x_test, 'y': y_test}, stream)
    cmf.log_dataset(d_path, 'output', properties={'name': 'iris', 'type': 'preprocessed', 'split': 'test'})


def train(input_dir: t.Optional[str] = None, output_dir: t.Optional[str] = None) -> None:
    """Train a model."""
    ds_path = workspace(input_dir) / 'train.pkl'
    with open(ds_path, 'rb') as stream:
        dataset: t.Dict = pickle.load(stream)
    cmf.log_dataset(ds_path, 'input')

    clf = DecisionTreeClassifier().fit(dataset['x'], dataset['y'])
    cmf.log_execution_metrics(
        'train',
        {'accuracy': accuracy_score(y_true=dataset['y'], y_pred=clf.predict(dataset['x']))}
    )

    mdl_path = workspace(output_dir) / 'model.pkl'
    with open(mdl_path, 'wb') as stream:
        pickle.dump(clf, stream)
    cmf.log_model(mdl_path, 'output')


def test(input_dir: t.Optional[str] = None) -> None:
    """Test a model."""
    ds_path = workspace(input_dir) / 'test.pkl'
    with open(ds_path, 'rb') as stream:
        dataset: t.Dict = pickle.load(stream)
    cmf.log_dataset(ds_path, 'input')

    mdl_path = workspace(input_dir) / 'model.pkl'
    with open(mdl_path, 'rb') as stream:
        clf: DecisionTreeClassifier = pickle.load(stream)
    cmf.log_model(mdl_path, 'input')

    cmf.log_execution_metrics(
        'test',
        {'accuracy': accuracy_score(y_true=dataset['y'], y_pred=clf.predict(dataset['x']))}
    )


@click.command()
@click.option('-e', '--env', default='local', help='Environment to use (local, ray, pachyderm)')
def main(env: str) -> None:
    pipeline_fn: t.Optional[t.Callable] = None
    if env == 'local':
        import _local
        pipeline_fn = _local.pipeline
    elif env == 'ray':
        import _ray
        pipeline_fn = _ray.pipeline

    if not pipeline_fn:
        print(f"Unrecognized environment: '{env}'")
        exit(1)

    pipeline_fn()


if __name__ == '__main__':
    main()
