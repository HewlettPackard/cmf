"""

"""
import argparse
import functools
import inspect
import os
import sys
from pathlib import Path
import typing as t
from copy import deepcopy
from cmflib.cmf import Cmf


class CMFError(Exception):
    ...


class Artifact:
    """Base class for all artifacts.
    Args:
        uri: Uniform resource identifier (URI) of the given artifact. Does not have to be a file system path. Rather,
            it's something that can be used to retrieve an artifact from one of backends.
        params: Dictionary of parameters associated with this artifact.
    """
    def __init__(self, uri: t.Union[str, Path], params: t.Optional[t.Dict] = None) -> None:
        self.uri = uri if isinstance(uri, str) else uri.as_posix()
        self.params = deepcopy(params or {})


class Dataset(Artifact):
    """Artifact to represent datasets."""
    ...


class MLModel(Artifact):
    """Artifact to represent machine learning models."""
    ...


class ExecutionMetrics(Artifact):
    """Artifact to represent execution metrics."""
    def __init__(self, uri: t.Union[str, Path], name: str, params: t.Optional[t.Dict] = None) -> None:
        super().__init__(uri, params)
        self.name = name


class Context(dict):
    """Step context.

    This is no the context as it is defined in MLMD. Rather, it contains runtime parameters for steps, such as, for
    instance, workspace directory or instance of the initialized Cmf.
    """
    ...


class Parameters(dict):
    """Step parameters."""
    ...


def step(pipeline_name: t.Optional[str] = None, pipeline_stage: t.Optional[str] = None) -> t.Callable:
    """Function decorator that automatically logs input and output artifacts for Cmf steps."""
    def step_decorator(func: t.Callable) -> t.Callable:
        nonlocal pipeline_name, pipeline_stage
        options = {
            'pipeline_name': pipeline_name, 'pipeline_stage': pipeline_stage
        }

        @functools.wraps(func)
        def _wrapper(*args, **kwargs):
            from cmflib.cmf import Cmf
            options.update(
                pipeline_name=options['pipeline_name'] or os.environ.get('CMF_PIPELINE', None),
                filename=os.environ.get('CMF_URI', 'mlmd'),
                graph=os.environ.get('CMF_GRAPH', 'false').lower() == 'true',
                pipeline_stage=options['pipeline_stage'] or func.__name__
            )
            options['pipeline_name'] = options['pipeline_name'] or os.environ.get('CMF_PIPELINE', None)
            options['cmf_uri'] = os.environ.get('CMF_URI', 'mlmd')
            if not options['pipeline_name']:
                raise CMFError(
                    "The pipeline name is not specified. You have two options to specify the name. Option 1: export "
                    "environmental variable `export CMF_PIPELINE=iris` in linux or `set CMF_PIPELINE=iris` in Windows. "
                    "Option 2: use step annotator's `pipeline_name` parameter, e.g., `@step(pipeline_name=iris)`"
                )

            # Get context, parameters and input artifacts
            ctx, params, inputs = _validate_task_arguments(args, kwargs)

            # Create a pipeline, create a context and an execution
            cmf = Cmf(filename=options['filename'], pipeline_name=options['pipeline_name'], graph=options['graph'])
            _ = cmf.create_context(pipeline_stage=options['pipeline_stage'])
            _ = cmf.create_execution(execution_type=options['pipeline_stage'], custom_properties=params)
            _log_artifacts(cmf, 'input', inputs)

            # Run the step
            if ctx is not None:
                ctx['cmf'] = cmf
            outputs: t.Optional[t.Dict[str, Artifact]] = func(*args, **kwargs)
            outputs = outputs or {}
            if ctx is not None:
                del ctx['cmf']

            # Log the output artifacts
            _log_artifacts(cmf, 'output', outputs)

        return _wrapper

    return step_decorator


def cli_run(step_fn: t.Callable) -> None:
    """Parse command line and execute CMF step.

    Command line named arguments:
        - Context parameters: --ctx name=value
        - Execution parameters: --param name=value
        - Other key-value parameters are input artifacts: name=value

    Environment variables:
        - CMF_PIPELINE [mandatory]: pipeline name

    """
    # Pase command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='CMF step arguments')
    parser.add_argument(
        '--params', required=False, default='',
        help='Execution parameters for a pipeline step, e.g., --params=train_size=0.7,add_noise=true. Users must define'
             'their functions accepting exactly one positional or keyed argument of type `Parameters` if they want to '
             'be able to accept execution parameters.'
    )
    parser.add_argument(
        '--ctx', required=False, default='',
        help='Runtime parameters for the step. These parameters define execution environment, e.g., workspace location.'
             'Also, users can access the instance of `Cmf` via this context under the `cmf` key. Users must define'
             'their functions accepting exactly one positional or keyed argument of type `Context` if they want to '
             'be able to accept these runtime parameters.'
    )
    parsed, artifacts = parser.parse_known_args(sys.argv[1:])

    # Convert command line arguments into dictionaries
    def _parse_key_value_list(_kv_list: t.Union[str, t.List[str]], _dict_cls) -> t.Union[t.Dict, Context, Parameters]:
        """Convert a string like 'a=3,b=5' into a dictionary."""
        _dict = _dict_cls()
        if not _kv_list:
            return _dict
        if isinstance(_kv_list, str):
            _kv_list = _kv_list.split(',')
        for _item in _kv_list:
            _k, _v = _item.split('=')
            _dict[_k.strip()] = _v.strip()
        return _dict

    params = _parse_key_value_list(parsed.params, Parameters)
    ctx = _parse_key_value_list(parsed.ctx, Context)
    inputs = _parse_key_value_list(artifacts, dict)

    # Call the step function.
    _call_step_with_parameter_check(step_fn, ctx, params, inputs)


def prepare_workspace(ctx: Context) -> Path:
    """Ensure the workspace directory exists.

    Workspace is a place where we store various files.
    """
    workspace = Path(ctx.get('workspace', Path.cwd() / 'workspace'))
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace


def _call_step_with_parameter_check(fn: t.Callable, ctx: Context, params: Parameters, inputs: t.Dict) -> None:
    """The goal is to make sure the fn's API accept provided `context`, `params` and `inputs`."""
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
    """Naive implementation to return instance of an artifact based upon function's parameter annotation."""
    if issubclass(annotation, Dataset):
        return Dataset(uri)
    elif issubclass(annotation, MLModel):
        return MLModel(uri)
    raise CMFError(f"Cannot convert URI to an Artifact instance: uri={uri}, annotation={annotation}.")


def _validate_task_arguments(
    args: t.Tuple, kwargs: t.Dict
) -> t.Tuple[t.Optional[Context], t.Optional[Parameters], t.Dict]:
    """Check parameters to be passed to a Cmf's step function."""
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
                f"Invalid keyword parameter (key={key}, value={value}, type={type(value)})"
            )

    return context, params, inputs


def _log_artifacts(cmf: Cmf, event: str, artifacts: t .Dict[str, Artifact]) -> None:
    """Log artifacts with Cmf.
    Args:
        cmf: Instance of initialized Cmf.
        event: One of `input` or `output` (whether these artifacts input or output artifacts).
        artifacts: Dictionary that maps artifacts names to artifacts. Names are not used, only artifacts.
    """
    for name, artifact in artifacts.items():
        if isinstance(artifact, Dataset):
            cmf.log_dataset(url=artifact.uri, event=event, custom_properties=artifact.params)
        elif isinstance(artifact, MLModel):
            cmf.log_model(path=artifact.uri, event=event, **artifact.params)
        elif isinstance(artifact, ExecutionMetrics):
            cmf.log_execution_metrics(artifact.name, artifact.params)
        else:
            raise CMFError(f"Can't log unrecognized artifact: type={type(artifact)}, artifact={str(artifact)}")
