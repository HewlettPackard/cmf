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

import argparse
import functools
import inspect
import json
import logging
import os
import sys
import time
import typing as t
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

import yaml

from cmflib.cmf import Cmf

__all__ = [
    "CMFError",
    "Artifact",
    "Dataset",
    "MLModel",
    "MLModelCard",
    "ExecutionMetrics",
    "Context",
    "Parameters",
    "cmf_config",
    "step",
    "prepare_workspace",
    "cli_run",
]

logger = logging.getLogger(__name__)

# Define a generic type variable T that can represent Context, Parameters, or Dict[str, Any]
T = t.TypeVar("T", bound=dict)  


class LogMessage:
    """Helper class to do structured logging.

    Args:
        type_: Message type (aka event type).
        kwargs: Additional keyword arguments to be associated with the event being logged.
    """

    def __init__(self, type_: str, **kwargs) -> None:
        self.type = type_
        self.kwargs = kwargs  # maybe copy?

    def __str__(self) -> str:
        return json.dumps({"type": self.type, **self.kwargs}, cls=JSONEncoder)


msg = LogMessage


class CMFError(Exception):
    """Base exception for CMF."""

    ...


class Artifact:
    """Base class for all artifacts.
    Args:
        uri: Uniform resource identifier (URI) of the given artifact. Does not have to be a file path. Rather,
            it's something that can be used to retrieve an artifact from one of backends.
        params: Dictionary of parameters associated with this artifact. Should be serializable with ML metadata.
    """

    def __init__(self, uri: t.Union[str, Path], params: t.Optional[t.Dict] = None) -> None:
        self.uri = uri if isinstance(uri, str) else uri.as_posix()
        self.params = deepcopy(params or {})

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(uri={self.uri}, params={self.params})"


class Dataset(Artifact):
    """Artifact to represent datasets.

    Note:
        Various dataset splits, when represented as different files or directories, should have different artifacts.
    """

    ...


class MLModel(Artifact):
    """Artifact to represent machine learning models."""

    ...


class MLModelCard(Artifact):
    """Artifact to represent machine learning model cards containing evaluation reports"""

    ...


class ExecutionMetrics(Artifact):
    """Artifact to represent execution metrics.

    Args:
        uri: Uniform resource identifier (URI) of the given artifact. Does not have to be a file path. Rather,
            it's something that can be used to retrieve an artifact from one of backends.
        name: Name of a metric group, e.g., `train_metrics` or `test_metrics`.
        params: Dictionary of metrics. Keys do not have to specify the dataset split these metrics were computed with
            (it's specified with the `name` parameter).
    """

    def __init__(self, uri: t.Union[str, Path], name: str, params: t.Optional[t.Dict] = None) -> None:
        super().__init__(uri, params)
        self.name = name

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(uri={self.uri}, params={self.params}, name={self.name})"


class JSONEncoder(json.JSONEncoder):
    """JSON encoder that can handle instances of the `Artifact` class."""

    def default(self, o: t.Any) -> t.Any:
        if isinstance(o, Artifact):
            return str(o)
        return super().default(o)


class Context(dict):
    """Step context.

    This is not the context as it is defined in MLMD. Rather, it contains runtime parameters for steps, such as, for
    instance, workspace directory or instance of the initialized Cmf.

    If a step function defines this parameter, then it will have the following fields:
        - cmf: Instance of the `cmflib.Cmf`.
    """

    ...


class Parameters(dict):
    """Step parameters.

    These parameters include, for instance, hyperparameters for training ML models (learning rate, batch size etc.)
    """

    @classmethod
    def from_file(cls, stage_name: str, file_name: t.Union[str, Path] = "pipeline.yaml") -> "Parameters":
        """Helper method to load parameters from a `yaml` file.

        Args:
            stage_name: Name of a stage to load parameters for. It is assumed the yaml file is a dictionary where
                top-level keys correspond to stage names. Each top-level key must point to a dictionary containing
                parameters for the given stage.
            file_name: Path to a `yaml` file containing pipeline parameters.
        Returns:
            Instance of this class containing parameters for the requested stage.
        """
        with open(file_name, "rt") as f:
            pipeline_stages_params = yaml.load(f, Loader=yaml.SafeLoader)
            return Parameters(**pipeline_stages_params[stage_name])


def _str_to_bool(val: t.Optional[str]) -> t.Optional[bool]:
    """Convert string value into boolean.

    Args:
        val: String representation of the boolean value.

    Returns:
        True or False.
    """
    if val is None:
        return None
    val = val.lower()
    return val in ("1", "on", "true")


@dataclass
class CmfConfig:
    """CMF configuration.

    CMF for autologging is configured in a hierarchical manner. The following is the respective hierarchy (if certain
    fields are not specified (e.g., they are Nones), they are considered to be not set, and default values defined by
    CMF are used):
        - Default configuration: filename="mlmd", graph=False.
        - Configuration from environment.
        - Configuration from user (see `cmf_config` variable below).
        - Configuration provided via `step` decorator.

    The CMf autologging framework uses the same values for stage and execution names (`pipeline_stage`).
    """

    filename: t.Optional[str] = None
    pipeline_name: t.Optional[str] = None
    pipeline_stage: t.Optional[str] = None
    graph: t.Optional[bool] = None
    is_server: t.Optional[bool] = None

    def update(self, other: "CmfConfig") -> "CmfConfig":
        """Override this configuration with other configuration."""
        if other.filename is not None:
            self.filename = other.filename
        if other.pipeline_name is not None:
            self.pipeline_name = other.pipeline_name
        if other.pipeline_stage is not None:
            self.pipeline_stage = other.pipeline_stage
        if other.graph is not None:
            self.graph = other.graph
        return self

    @classmethod
    def from_env(cls) -> "CmfConfig":
        """Retrieve CMF configuration from environment."""
        return cls(
            filename=os.environ.get("CMF_URI", None),
            pipeline_name=os.environ.get("CMF_PIPELINE", None),
            pipeline_stage=os.environ.get("CMF_STAGE", None),
            graph=_str_to_bool(os.environ.get("CMF_GRAPH", None)),
            is_server=_str_to_bool(os.environ.get("CMF_IS_SERVER", None)),
        )

    @classmethod
    def from_params(cls, **kwargs) -> "CmfConfig":
        """Build CMF configuration using provided parameters."""
        return cls(**kwargs)


cmf_config = CmfConfig()
"""Users can use this object to configure CMF programmatically"""


def step(pipeline_name: t.Optional[str] = None, pipeline_stage: t.Optional[str] = None) -> t.Callable:
    """Function decorator that automatically logs input and output artifacts for Cmf steps.

    This function decorator adds automated Cmf-based logging of input and output artifacts to user functions. Users must
    define their functions using specific rules. The most general API is the following:

    ```python
    import typing as t
    from cmflib.contrib.auto_logging_v01 import (step, Context, MLModel, Dataset, cli_run)

    @step()
    def test(ctx: Context, params: Parameters, model: MLModel, test_dataset: Dataset) -> t.Optional[t.Dict]:
        ...

    if __name__ == '__main__':
        cli_run(test)
    ```

    The following rules must be followed:
        - All function input parameters must be annotated.
        - A function can accept one or zero parameters of type `Context`, one or zero parameters of type `Parameters`,
            zero or more parameters of type `Artifact` or its derived types, e.g., Dataset, MLModel etc.
        - A function can optionally return a dictionary-like object with string keys and values of type `Artifact` or
            its derived types (Dataset, MLModel) etc.
        - No other parameter types are allowed.

    Functions that satisfy the above rules can be annotated with the `step` decorator that adds automated logging of
    input and output artifacts.

    Note:
        Best practices (mandatory requirement?) require that all input artifacts must already be present in the metadata
        store. The current implementation does not enforce this for now. It means that in order to use some raw dataset
        on a pipeline, a special `ingest` node should be used that, for instance, take a dataset name as a parameter
        and outputs an artifact. This output dataset artifact will be added to metadata store, and is thus becomes
        eligible to be used by other pipeline steps as input artifact.

    This function performs the following steps:
        - It creates an instance of Cmf.
        - It creates a context for this step and then execution. If parameters are present, these parameters will be
            associated with this execution.
        - All input artifacts are logged (input artifacts are all input parameters of type `Artifact`) with CMF as input
            artifacts. No parameters are associated with input artifacts.
        - A step function is called.
        - The return object is observed. If it's a dictionary containing values of type `Artifact`, these values are
            logged as output artifacts.

    If function accepts a parameter of type `Context`, the decorator will add a Cmf instance under the `cmf` key.

    Args:
        pipeline_name: Name of a pipeline. This name override name provided with environment variable `CMF_PIPELINE`.
        pipeline_stage: Name of a pipeline stage (==context name in MLMD terms). If not specified, a function name is
            used.

    TODO: (sergey) rename to stage (or just do `stage = step`)?
    """

    def step_decorator(func: t.Callable) -> t.Callable:
        nonlocal pipeline_name, pipeline_stage

        @functools.wraps(func)
        def _wrapper(*args, **kwargs) -> t.Any:
            from cmflib.cmf import Cmf

            config = CmfConfig.from_params(filename="mlmd", graph=False)
            config = (
                config.update(CmfConfig.from_env())
                .update(cmf_config)
                .update(CmfConfig.from_params(pipeline_name=pipeline_name, pipeline_stage=pipeline_stage))
            )

            if config.pipeline_name is None:
                _module = getattr(func, "__module__", None)
                if _module is not None and "__file__" in _module:
                    config.pipeline_name = Path(_module["__file__"]).stem
            if config.pipeline_stage is None:
                config.pipeline_stage = func.__name__
            if not config.pipeline_name:
                raise CMFError(
                    "The pipeline name is not specified. You have two options to specify the name. Option 1: export "
                    "environmental variable `export CMF_PIPELINE=iris` in linux or `set CMF_PIPELINE=iris` in Windows. "
                    "Option 2: use step annotator's `pipeline_name` parameter, e.g., `@step(pipeline_name=iris)`"
                )

            # Get context, parameters and input artifacts
            ctx, params, inputs = _validate_task_arguments(args, kwargs)

            # Create a pipeline, create a context and an execution
            cmf = Cmf(
                filepath=config.filename or "mlmd", # Ensure filename is always a valid string
                pipeline_name=config.pipeline_name,
                graph=config.graph or False # Ensure graph is always a valid boolean
            )
            _ = cmf.create_context(pipeline_stage=config.pipeline_stage)
            _ = cmf.create_execution(execution_type=config.pipeline_stage, custom_properties=params)
            _log_artifacts(cmf, "input", inputs)

            # Run the step
            if ctx is not None:
                ctx["cmf"] = cmf
            logger.debug(
                msg(
                    "execution",
                    pipeline=config.pipeline_name,
                    stage=config.pipeline_stage,
                    execution_id=cmf.execution.id if cmf.execution else None,
                )
            )
            logger.debug(msg("execution.impl", execution_id=cmf.execution.id if cmf.execution else None, impl=func.__name__))
            logger.debug(
                    msg(
                        "execution.inputs",
                        execution_id=cmf.execution.id if cmf.execution else None,
                        ctx_keys=list((ctx or {}).keys()),
                        params=(params or {}),
                        inputs=inputs,
                    )
                )
            start_time = time.time()
            outputs: t.Optional[t.Dict[str, Artifact]] = func(*args, **kwargs)
            end_time = time.time()

            logger.debug(
                msg(
                    "execution.runtime",
                    execution_id=cmf.execution.id if cmf.execution else None,
                    time_seconds=end_time - start_time,
                )
            )
            logger.debug(
                msg(
                    "execution.outputs",
                    execution_id=cmf.execution.id if cmf.execution else None,
                    outputs=outputs,
                    metrics=list(cmf.metrics.keys()),
                )
            )

            if ctx is not None:
                del ctx["cmf"]

            # Log the output artifacts
            if outputs is not None:
                _log_artifacts(cmf, "output", outputs)

            # Commit all metrics
            for metrics_name in cmf.metrics.keys():
                cmf.commit_metrics(metrics_name)

            # All done
            cmf.finalize()

            return outputs

        return _wrapper

    return step_decorator


def cli_run(step_fn: t.Callable) -> None:
    """Parse command line and run the CMF stage.

    The following syntax for command line arguments is supported.
        - Context parameters: `--ctx name1=value1,name2=value2`.
        - Execution parameters: `--params lr=0.07,batch_size=128`.
        - Other key-value parameters are input artifacts (do not use `--`): `dataset=workspace/iris.pkl`. Names must
            match function parameters.

    Environment variables:
        Users can specify the following environment variables
        - CMF_PIPELINE: Name of a pipeline.
        - CMF_URI: MLMD file name, default is `mlmd`
        - CMG_GRAPH: If set, Neo4J will be used, default is not to use. To enable, set it to `true`.

    Args:
        step_fn: Python function implementing a pipeline stage.

    """
    # Parse command line arguments
    import argparse

    parser = argparse.ArgumentParser(description="CMF step arguments")
    parser.add_argument(
        "--params",
        required=False,
        default="",
        help="Execution parameters for a pipeline step, e.g., --params=train_size=0.7,add_noise=true. Users must define"
        "their functions accepting exactly one positional or keyed argument of type `Parameters` if they want to "
        "be able to accept execution parameters.",
    )
    parser.add_argument(
        "--ctx",
        required=False,
        default="",
        help="Runtime parameters for the step. These parameters define execution environment, e.g., workspace location."
        "Also, users can access the instance of `Cmf` via this context under the `cmf` key. Users must define"
        "their functions accepting exactly one positional or keyed argument of type `Context` if they want to "
        "be able to accept these runtime parameters.",
    )
    parsed, artifacts = parser.parse_known_args(sys.argv[1:])

    # Convert command line arguments into dictionaries
    def _parse_key_value_list(
            _kv_list: t.Union[str, t.List[str]], 
            _dict_cls: t.Type[T] # Ensure _dict_cls is a class type that matches T (e.g., Context, Parameters, dict)
            ) -> T: # The return type dynamically matches the class passed as _dict_cls
        """Convert a string like 'a=3,b=5' into an instance of Context, Parameters, or Dict.
         **Reason for using TypeVar T and Type[T]:**
        - Previously, the return type was Union[Dict, Context, Parameters], which caused mypy warnings because 
          it couldn't infer the exact return type based on _dict_cls.
        - By introducing TypeVar T, we ensure that the return type always matches the class type passed to _dict_cls.
        - This provides stricter type safety, reduces the need for type casting, and resolves mypy warnings.
        """
        _dict: t.Dict[str, t.Any] = {} # Explicit type annotation for clarity
    
        if not _kv_list:
            return _dict_cls(_dict)  # Return an empty instance of the appropriate class (Context/Parameters/Dict)
    
        if isinstance(_kv_list, str):
            _kv_list = _kv_list.split(",")  # Split input string into individual key-value pairs
     
        for _item in _kv_list:
            _k, _v = _item.split("=")
            _dict[_k.strip()] = _v.strip()  # Add key-value pair to the dictionary

        return _dict_cls(_dict)  # Dynamically return an instance matching the _dict_cls type

    params = _parse_key_value_list(parsed.params, Parameters)
    ctx = _parse_key_value_list(parsed.ctx, Context)
    inputs = _parse_key_value_list(artifacts, dict)

    # Call the step function.
    _call_step_with_parameter_check(step_fn, ctx, params, inputs)


def prepare_workspace(ctx: Context, namespace: t.Optional[str] = None) -> Path:
    """Ensure the workspace directory exists.

    Workspace is a place where we store various files.

    Args:
        ctx: Context for this step. If it does not contain `workspace` parameter, current working directory is used.
        namespace: Relative path within workspace (relative directory path) that a step is requesting to create.

    Returns:
        Path to the workspace directory.
    """
    workspace = Path(ctx.get("workspace", Path.cwd() / "workspace"))
    if namespace:
        workspace = workspace / namespace
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace


def _call_step_with_parameter_check(fn: t.Callable, ctx: Context, params: Parameters, inputs: t.Dict) -> None:
    """The goal is to make sure the fn's API accept provided `context`, `params` and `inputs`.

    Args:
        fn: User function implementing the pipeline step.
        ctx: Context to be passed to this function.
        params: Parameters to be passed to this function.
        inputs: Input artifacts to be passed to this function.
    """
    # We will be modifying inputs, so need to make a copy.
    _unrecognized_artifacts = set(inputs.keys())

    # Get function parameters (named and their annotations)
    signature: inspect.Signature = inspect.signature(fn)
    fn_specs = argparse.Namespace(kwargs={}, needs_ctx=False, needs_params=False)
    for param in signature.parameters.values():
        if issubclass(param.annotation, Context):
            fn_specs.kwargs[param.name] = ctx or Context()
            fn_specs.needs_ctx = True
        elif issubclass(param.annotation, Parameters):
            fn_specs.kwargs[param.name] = params or Parameters()
            fn_specs.needs_params = True
        elif issubclass(param.annotation, Artifact):
            if param.name not in inputs:
                raise CMFError(
                    f"Missing input artifact (name={param.name}) for function {fn}. You have provided the following "
                    f"inputs: {inputs.keys()}."
                )
            if isinstance(inputs[param.name], Artifact):
                fn_specs.kwargs[param.name] = inputs[param.name]
            elif isinstance(inputs[param.name], str):
                fn_specs.kwargs[param.name] = _uri_to_artifact(inputs[param.name], param.annotation)
            else:
                raise CMFError(
                    f"Unrecognized artifact value: name={param.name}, value={inputs[param.name]}. Supported values are "
                    "instances of `Artifact` class or strings. In the latter case, string values are assumed to "
                    "be URIs."
                )

            _unrecognized_artifacts.remove(param.name)
        else:
            raise CMFError(
                f"Unrecognized function parameter: fn={fn}, param={param.name}, annotation={param.annotation}. A valid "
                "CMF step function must annotate all its parameters, and only `Context`, `Parameter` and parents of "
                "`Artifact` are allowed."
            )

    # Check we have used all provided inputs
    if _unrecognized_artifacts:
        raise CMFError(
            f"The following input artifacts have not been accepted by the step "
            f"function ({fn}): ({_unrecognized_artifacts})."
        )
    # Check that this function does accept context and parameters if they are present
    if ctx and not fn_specs.needs_ctx:
        raise CMFError(f"Context is provided (keys={ctx.keys()}) but function ({fn}) does not accept context.")
    if params and not fn_specs.needs_params:
        raise CMFError(f"Params are provided (keys={params.keys()}) but function ({fn}) does not accept params.")

    # All done - call the function
    fn(**fn_specs.kwargs)


def _uri_to_artifact(uri: str, annotation: t.Any) -> Artifact:
    """Naive implementation to return instance of an artifact based upon function's parameter annotation.

    Args:
        uri: Artifact URI, e.g., file path.
        annotation: Function annotation for this artifact. All valid Cmf steps within this automated logging framework
            must have their parameters annotated.

    Returns:
        Artifact instance associated with this parameter.
    """
    if issubclass(annotation, Dataset):
        return Dataset(uri)
    elif issubclass(annotation, MLModel):
        return MLModel(uri)
    raise CMFError(f"Cannot convert URI to an Artifact instance: uri={uri}, annotation={annotation}.")


def _validate_task_arguments(
    args: t.Tuple, kwargs: t.Dict
) -> t.Tuple[t.Optional[Context], t.Optional[Parameters], t.Dict]:
    """Check parameters to be passed to a Cmf's step function.
    Args:
        args: Positional parameters to be passed. Can only be of the following two types: `Context`, `Parameter`.
        kwargs: Keyed parameters to be passed. Can be of the following type: `Context`, `Parameter` and `Artifact`.

    Returns:
        A tuple with three elements containing `Context` parameter, `Parameters` parameter and dictionary with
        artifacts. Some values can be None if not present in args and kwargs.
    """
    context: t.Optional[Context] = None  # Task execution context.
    params: t.Optional[Parameters] = None  # Task parameters.
    inputs: t.Dict = {}  # Task input artifacts.

    def _set_exec_context(_value: t.Any) -> None:
        nonlocal context
        if context is not None:
            raise CMFError("Multiple execution contexts are not allowed.")
        context = _value

    def _set_parameters(_value: t.Any) -> None:
        nonlocal params
        if params is not None:
            raise CMFError("Multiple parameter dictionaries are not allowed.")
        params = _value

    # Parse task positional parameters.
    for value in args:
        if isinstance(value, Context):
            _set_exec_context(value)
        elif isinstance(value, Parameters):
            _set_parameters(value)
        else:
            raise CMFError(
                f"Invalid positional parameter (value={value}, type={type(value)}). Only Context and "
                "Parameters could be positional parameters. All other parameters must be keyword parameters."
            )

    # Parse task keyword parameters.
    for key, value in kwargs.items():
        if isinstance(value, Context):
            _set_exec_context(value)
        elif isinstance(value, Parameters):
            _set_parameters(value)
        elif isinstance(value, Artifact):
            inputs[key] = value
        else:
            raise CMFError(
                f"Invalid keyword parameter type (name={key}, value={value}, type={type(value)}). "
                "Expecting one of: `Context`, `Parameters` or `Artifact`."
            )

    return context, params, inputs


def _log_artifacts(
    cmf: Cmf,
    event: str,
    artifacts: t.Union[
        Artifact,
        t.List[Artifact],
        t.Tuple[Artifact],
        t.Set[Artifact],
        t.Mapping[str, t.Union[Artifact, t.List[Artifact]]] # Use Mapping for better type compatibility
    ]
) -> None:
    """Log artifacts with Cmf.
    Args:
        cmf: Instance of initialized Cmf.
        event: One of `input` or `output` (whether these artifacts input or output artifacts).
        artifacts: Dictionary that maps artifacts names to artifacts. Names are not used, only artifacts.
    """
    if isinstance(artifacts, dict):
        for artifact in artifacts.values():
            _log_artifacts(cmf, event, artifact)
    elif isinstance(artifacts, (list, tuple, set)):
        for artifact in artifacts:
            _log_artifacts(cmf, event, artifact)
    elif isinstance(artifacts, Dataset):
        cmf.log_dataset(url=artifacts.uri, event=event, custom_properties=artifacts.params)
    elif isinstance(artifacts, MLModel):
        cmf.log_model(path=artifacts.uri, event=event, **artifacts.params)
    elif isinstance(artifacts, ExecutionMetrics):
        cmf.log_execution_metrics(artifacts.name, artifacts.params)
    else:
        raise CMFError(f"Can't log unrecognized artifact: type={type(artifacts)}, artifacts={str(artifacts)}")
