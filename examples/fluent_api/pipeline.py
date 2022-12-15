import typing as t

from sklearn.metrics import accuracy_score
from sklearn.tree import DecisionTreeClassifier

import cmflib.contrib.fluent as cmf
from pathlib import Path
import pickle
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.utils import Bunch


_pipeline = 'iris'
"""Pipeline name."""

_workspace = Path(__file__).parent / 'workspace'
"""Path to a pipeline workspace containing serialized artifacts (datasets and ML models)."""


def fetch() -> None:
    """Ingest the IRIS dataset into a pipeline."""
    with open(_workspace / 'iris.pkl', 'wb') as stream:
        iris: Bunch = load_iris()
        pickle.dump(
            {'data': iris['data'], 'target': iris['target']},
            stream
        )
        cmf.log_dataset(stream, properties={'name': 'iris', 'type': 'raw'})


def preprocess(params: t.Optional[t.Dict] = None) -> None:
    """Split raw dataset into train/test splits."""
    params = params or {}
    with open(_workspace / 'iris.pkl', 'rb') as stream:
        dataset: t.Dict = pickle.load(stream)
        cmf.log_dataset(stream)

    x_train, x_test, y_train, y_test = train_test_split(
        dataset['data'],
        dataset['target'],
        train_size=float(params.get('train_size', 0.7)),
        shuffle=params.get('shuffle', 'true').lower() == 'true'
    )

    with open(_workspace / 'train.pkl', 'wb') as stream:
        pickle.dump({'x': x_train, 'y': y_train}, stream)
        cmf.log_dataset(stream, properties={'name': 'iris', 'type': 'preprocessed', 'split': 'train'})
    with open(_workspace / 'test.pkl', 'wb') as stream:
        pickle.dump({'x': x_test, 'y': y_test}, stream)
        cmf.log_dataset(stream, properties={'name': 'iris', 'type': 'preprocessed', 'split': 'test'})


def train() -> None:
    """Train a model."""
    with open(_workspace / 'train.pkl', 'rb') as stream:
        dataset: t.Dict = pickle.load(stream)
        cmf.log_dataset(stream)

    clf = DecisionTreeClassifier()
    clf = clf.fit(dataset['x'], dataset['y'])
    cmf.log_execution_metrics(
        'train',
        {'accuracy': accuracy_score(y_true=dataset['y'], y_pred=clf.predict(dataset['x']))}
    )

    with open(_workspace / 'model.pkl', 'wb') as stream:
        pickle.dump(clf, stream)
        cmf.log_model(stream)


def test() -> None:
    """Test a model."""
    with open(_workspace / 'test.pkl', 'rb') as stream:
        dataset: t.Dict = pickle.load(stream)
        cmf.log_dataset(stream)

    with open(_workspace / 'model.pkl', 'rb') as stream:
        clf: DecisionTreeClassifier = pickle.load(stream)
        cmf.log_model(stream)

    cmf.log_execution_metrics(
        'test',
        {'accuracy': accuracy_score(y_true=dataset['y'], y_pred=clf.predict(dataset['x']))}
    )


def pipeline():
    """Run IRIS ML pipeline."""
    _workspace.mkdir(parents=True, exist_ok=True)
    cmf.set_cmf_parameters(filename='mlmd', graph=False)
    for step in (fetch, preprocess, train, test):
        with cmf.start_step(pipeline=_pipeline, step=step.__name__):
            step()


if __name__ == '__main__':
    pipeline()
