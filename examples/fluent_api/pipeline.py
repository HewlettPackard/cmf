import typing as t

from sklearn.metrics import accuracy_score
from sklearn.tree import DecisionTreeClassifier

import cmflib.contrib.fluent as cmf
import pickle
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.utils import Bunch


def fetch() -> None:
    """Ingest the IRIS dataset into a pipeline."""
    ds_path = cmf.get_work_directory() / 'workspace' / 'iris.pkl'
    with open(ds_path, 'wb') as stream:
        iris: Bunch = load_iris()
        pickle.dump({'data': iris['data'], 'target': iris['target']}, stream)
    cmf.log_dataset(ds_path, 'output', properties={'name': 'iris', 'type': 'raw'})


def preprocess(params: t.Optional[t.Dict] = None) -> None:
    """Split raw dataset into train/test splits."""
    params = params or {}
    ds_path = cmf.get_work_directory() / 'workspace' / 'iris.pkl'
    with open(ds_path, 'rb') as stream:
        dataset: t.Dict = pickle.load(stream)
    cmf.log_dataset(ds_path, 'input')

    x_train, x_test, y_train, y_test = train_test_split(
        dataset['data'],
        dataset['target'],
        train_size=float(params.get('train_size', 0.7)),
        shuffle=params.get('shuffle', 'true').lower() == 'true'
    )

    ds_path = cmf.get_work_directory() / 'workspace' / 'train.pkl'
    with open(ds_path, 'wb') as stream:
        pickle.dump({'x': x_train, 'y': y_train}, stream)
    cmf.log_dataset(ds_path, 'output', properties={'name': 'iris', 'type': 'preprocessed', 'split': 'train'})

    d_path = cmf.get_work_directory() / 'workspace' / 'test.pkl'
    with open(d_path, 'wb') as stream:
        pickle.dump({'x': x_test, 'y': y_test}, stream)
    cmf.log_dataset(d_path, 'output', properties={'name': 'iris', 'type': 'preprocessed', 'split': 'test'})


def train() -> None:
    """Train a model."""
    ds_path = cmf.get_work_directory() / 'workspace' / 'train.pkl'
    with open(ds_path, 'rb') as stream:
        dataset: t.Dict = pickle.load(stream)
    cmf.log_dataset(ds_path, 'input')

    clf = DecisionTreeClassifier().fit(dataset['x'], dataset['y'])
    cmf.log_execution_metrics(
        'train',
        {'accuracy': accuracy_score(y_true=dataset['y'], y_pred=clf.predict(dataset['x']))}
    )

    mdl_path = cmf.get_work_directory() / 'workspace' / 'model.pkl'
    with open(mdl_path, 'wb') as stream:
        pickle.dump(clf, stream)
    cmf.log_model(mdl_path, 'output')


def test() -> None:
    """Test a model."""
    ds_path = cmf.get_work_directory() / 'workspace' / 'test.pkl'
    with open(ds_path, 'rb') as stream:
        dataset: t.Dict = pickle.load(stream)
    cmf.log_dataset(ds_path, 'input')

    mdl_path = cmf.get_work_directory() / 'workspace' / 'model.pkl'
    with open(mdl_path, 'rb') as stream:
        clf: DecisionTreeClassifier = pickle.load(stream)
    cmf.log_model(mdl_path, 'input')

    cmf.log_execution_metrics(
        'test',
        {'accuracy': accuracy_score(y_true=dataset['y'], y_pred=clf.predict(dataset['x']))}
    )
