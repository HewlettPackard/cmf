import abc
import io
import json
import os
from pathlib import Path
import typing as t
from cmflib.cmf import Cmf
import logging
import atexit

"""
## Introduction

This module implements one possible version of what a CMF fluent API can look like. It tries to achieve the following
goals:

   - Remove some rarely used features from public API (such as typed parameters for pipelines and steps).
   - Automatically create steps if none are present when users call fluent API (e.g., `log_dataset`).
   - Initialize CMF in different usage contexts, for instance, retrieve initialization parameters from environment
     variables. 
   - Automatically identify artifact association with steps (consumed/produced) in certain usage scenarios. 

## Example
   
Assuming a user has developed four functions - `fetch`, `preprocess`, `train` and `test`, the following is the example
of CMF fluent API:

```python
import cmflib.contrib.fluent as cmf

cmf.set_cmf_parameters(filename='mlmd', graph=False)
for step in (fetch, preprocess, train, test):
    with cmf.start_step(pipeline='my_pipeline', step=step.__name__):
        step()
```

## API methods

Methods can be categorized into three buckets:
- Set CMF parameters (`set_cmf_parameters`). These parameters control CMF initialization, and do not include information
  about pipelines, steps and executions.
- Start/end steps (`start_step` and `end_step`). These methods start a new pipeline step and ends currently active 
  pipeline steps. The `start_step` method returns an instance of the `Step` class that can be used as a python context
  manager to automatically end steps.
- Logging methods (`log_dataset`, `log_dataset_with_version`, `log_model`, `log_execution_metrics`, `log_metric` and 
  `log_validation_output`). These methods log input/output artifacts. When these methods accept artifact URL, users
  can provide either a string or a Path object:
  ```python
  ds_path = _workspace / 'iris.pkl'
  with open(ds_path, 'rb') as stream:
      dataset: t.Dict = pickle.load(stream)
  cmf.log_dataset(ds_path, 'input')
  ```
  All these methods will create a new step of one does not present.
"""

logger = logging.getLogger('cmf.fluent')

__all__ = [
    'Step',
    'set_cmf_parameters', 'get_work_directory',
    'start_step', 'end_step',
    'log_dataset', 'log_dataset_with_version',
    'log_model',
    'log_execution_metrics', 'log_metric',
    'log_validation_output'
]


class Step:
    """Object that contains parameters of an active step that can be used as a python context manager.

    It is used with `start_step` method:
    ```python
    with start_step(pipeline='mnist', step='preprocess', properties={'train_size': 0.7}):
        train()
    ```
    """

    def __init__(self) -> None:
        self._end_step: t.Callable = end_step
        self.pipeline_info = {'name': _cmf.parent_context.name, 'id': _cmf.parent_context.id}
        self.step_info = {'name': _cmf.child_context.name, 'id': _cmf.child_context.id}
        self.step_exec_info = {'name': _cmf.execution.name, 'id': _cmf.execution.id}

    def __enter__(self) -> None:
        """Nothing to do on enter."""
        ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """End active step on exit."""
        self._end_step()


_cmf: t.Optional[Cmf] = None
"""If not None, active step is present."""

_cmf_params: t.Optional[t.Dict] = None
"""CMF initialization parameters (such as filename and graph) excluding pipeline parameters."""

_URL = t.Union[str, Path]
_Event = t.Optional[str]
_Properties = t.Optional[t.Dict]


def set_cmf_parameters(filename: t.Optional[str] = None, graph: t.Optional[bool] = None) -> None:
    """Set CMF initialization parameters."""
    global _cmf_params
    if _cmf_params is None:
        _cmf_params = {}
    if filename is not None:
        _cmf_params['filename'] = filename
    if graph is not None:
        _cmf_params['graph'] = graph


def get_work_directory() -> Path:
    """Return artifact path."""
    db_file_path = (_cmf_params or {}).get('filename', None)
    return Path(db_file_path).parent if db_file_path else Path.cwd()


def start_step(pipeline: t.Optional[str] = None, step: t.Optional[str] = None, properties: t.Dict = None) -> Step:
    """Initialize a new pipeline step.

    If active exists, it will be ended. The return object can be used as a context manager to automatically end the
    step. The `CMF_FLUENT_INIT_METHOD` environment variable can specify initialization mechanism. Currently, the
    following is supported:
        - `env`: initialize step using environment variables.

    The following sequence defines parameter priorities (from highest to lowest): user -> env -> default.
    """
    global _cmf
    if _cmf is not None:
        logger.warning("[start_step] ending active CMF step")
        end_step()

    init_method = os.environ.get('CMF_FLUENT_INIT_METHOD', None)

    params = DefaultParams()
    if init_method == 'env':
        params = EnvParams(params)
    params = UserParams(params, pipeline, step, properties)

    _cmf = Cmf(**params.cmf_parameters(), pipeline_name=params.pipeline(), custom_properties=None)
    _ = _cmf.create_context(pipeline_stage=params.step(), custom_properties=None)
    _ = _cmf.create_execution(execution_type=params.step(), custom_properties=params.step_properties())

    return Step()


def end_step() -> None:
    """End active step if present.

    This method will commit metrics if there are any.
    """
    global _cmf
    if _cmf is not None:
        for name in _cmf.metrics.keys():
            _cmf.commit_metrics(metrics_name=name)
    _cmf = None


def log_dataset(url: _URL, event: _Event = None, properties: _Properties = None) -> None:
    """Log dataset artifact."""
    _maybe_initialize_step()
    url, event = _check_artifact_io(url, event)
    _ = _cmf.log_dataset(url, event, properties)


def log_dataset_with_version(url: _URL, version: str, event: _Event = None, properties: _Properties = None) -> None:
    """Log dataset artifact with version."""
    _maybe_initialize_step()
    url, event = _check_artifact_io(url, event)
    _ = _cmf.log_dataset_with_version(url, version, event, properties)


def log_model(path: _URL, event: _Event = None, model_framework: str = "Default", model_type: str = "Default",
              model_name: str = "Default", properties: _Properties = None) -> None:
    """Log model artifact."""
    _maybe_initialize_step()
    path, event = _check_artifact_io(path, event)
    _ = _cmf.log_model(path, event, model_framework, model_type, model_name, properties)


def log_execution_metrics(metrics_name: str, properties: _Properties = None) -> None:
    """Log execution metrics."""
    _maybe_initialize_step()
    _ = _cmf.log_execution_metrics(metrics_name, properties)


def log_metric(metrics_name: str, properties: _Properties = None) -> None:
    """Log in-progress metrics."""
    _maybe_initialize_step()
    _cmf.log_metric(metrics_name, properties)


def log_validation_output(version: str, properties: _Properties = None) -> None:
    """Log model validation metrics."""
    _maybe_initialize_step()
    _ = _cmf.log_validation_output(version, properties)


def _maybe_initialize_step() -> None:
    """Start a new pipeline step if none exists."""
    global _cmf
    if _cmf is None:
        _ = start_step()


def _check_artifact_io(url: _URL, event: t.Optional[str] = None) -> t.Tuple[str, str]:
    """Convert artifact `url` to string and maybe identify its direction (input/output).
    """
    if isinstance(url, (io.BufferedWriter, io.BufferedReader)):
        raise RuntimeError(
            f"This happens to be not a good idea. This file is still open at this point in time, and because of "
            "buffering, parts of data can still be in memory. It's better to write and close the file, and then add it "
            "to CMF.")
        # _path = Path(url.name).absolute()
        # _event = 'input' if 'r' in url.mode else 'output'
        # if event and event != _event:
        #     raise ValueError(f"Inconsistent parameters: url(value={url}, type={type(url)}, path={_path}) while "
        #                      f"used-provided event is `{event}`.")
        # url, event = _path, _event
    else:
        if not event:
            raise ValueError(f"When url is not a file object, event must be specified.")
    if isinstance(url, Path):
        url = url.absolute().as_posix()
    if not isinstance(url, str):
        raise ValueError(f"Unrecognized URL: url={url}, type={type(url)}.")

    assert isinstance(url, (str, Path)), f"BUG: url={url}, type={type(url)}, event={event}"
    return url, event


@atexit.register
def unload():
    """Callback function to end the active step if present when this module is unloaded."""
    end_step()


class Params(abc.ABC):
    """Base class that defines APIs to retrieve pipeline and step parameters."""

    def __init__(self, parent: t.Optional['Params'] = None) -> None:
        self.parent = parent

    def cmf_parameters(self) -> t.Dict:
        """Return dictionary of CMF initialization parameters (excluding pipeline information)."""
        ...

    def pipeline(self) -> str:
        """Return pipeline name."""
        ...

    def step(self) -> str:
        """Return step name."""
        ...

    def step_properties(self) -> t.Dict:
        """Return step execution properties."""
        ...


class DefaultParams(Params):
    """Default parameter provider.

    TODO: This does not work (probably, pipeline and step should not have the same names?)
    """

    def __init__(self) -> None:
        super().__init__()

    def cmf_parameters(self) -> t.Dict:
        return {'filename': 'mlmd', 'graph': False}

    def pipeline(self) -> str:
        return 'default'

    def step(self) -> str:
        return 'default'

    def step_properties(self) -> t.Dict:
        return {}


class EnvParams(Params):
    """Parameter provider that retrieves information from environment.

    To enable this, set the following environment variable `CMF_FLUENT_INIT_METHOD = 'env'`, e.g:
    ```python
    step_env = {
        'CMF_FLUENT_INIT_METHOD': 'env',
        'CMF_FLUENT_CMF_PARAMS': json.dumps({'filename': 'mlmd', 'graph': False}),
        'CMF_FLUENT_PIPELINE': 'iris',
        'CMF_FLUENT_STEP': 'fetch'
    }
    ```
    The following environment variables are supported:
    - `CMF_FLUENT_CMF_PARAMS`: JSON-string dictionary containing `filename` and `graph` keys.
    - `CMF_FLUENT_PIPELINE`: string defining a pipeline name.
    - `CMF_FLUENT_STEP`: string defining a step name.
    - `CMF_FLUENT_STEP_PROPERTIES`: JSON-string dictionary containing execution properties.
    """

    def __init__(self, parent: t.Optional[Params] = None) -> None:
        super().__init__(parent or DefaultParams())

    def cmf_parameters(self) -> t.Dict:
        return self._get_dict('CMF_FLUENT_CMF_PARAMS', self.parent.cmf_parameters())

    def pipeline(self) -> str:
        return self._get_string('CMF_FLUENT_PIPELINE', self.parent.pipeline())

    def step(self) -> str:
        return self._get_string('CMF_FLUENT_STEP', self.parent.step())

    def step_properties(self) -> t.Dict:
        return self._get_dict('CMF_FLUENT_STEP_PROPERTIES', self.parent.step_properties())

    @staticmethod
    def _get_string(env_var: str, default: str) -> str:
        value = os.environ.get(env_var, None)
        return value if value is not None else default

    @staticmethod
    def _get_dict(env_var: str, default: t.Dict) -> t.Dict:
        params = os.environ.get(env_var, None)
        return json.loads(params) if params else default


class UserParams(Params):
    """Parameter provider that uses parameters provided by a user."""

    def __init__(self, parent: t.Optional[Params] = None,
                 pipeline: t.Optional[str] = None, step: t.Optional[str] = None,
                 step_properties: t.Optional[t.Dict] = None) -> None:
        super().__init__(parent or DefaultParams())
        self._pipeline = pipeline
        self._step = step
        self._step_properties = step_properties

    def cmf_parameters(self) -> t.Dict:
        return self._get_value(_cmf_params, self.parent.cmf_parameters())

    def pipeline(self) -> str:
        return self._get_value(self._pipeline, self.parent.pipeline())

    def step(self) -> str:
        return self._get_value(self._step, self.parent.step())

    def step_properties(self) -> t.Dict:
        return self._get_value(self._step_properties, self.parent.step_properties())

    @staticmethod
    def _get_value(value: t.Any, default: t.Any) -> t.Any:
        return value if value is not None else default
