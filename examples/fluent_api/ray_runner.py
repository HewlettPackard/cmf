from pathlib import Path
import json
import ray
from pipeline import (fetch as _fetch, preprocess as _preprocess, train as _train, test as _test)


# Make pipeline step functions ray remotes.
fetch = ray.remote(_fetch)
preprocess = ray.remote(_preprocess)
train = ray.remote(_train)
test = ray.remote(_test)


def pipeline() -> None:
    """Run an IRIS ML pipeline on a ray cluster."""
    # Make sure the `workspace` directory exists. This is an analogy for MLflow's artifact path. There's probably
    # a better way to define it here.
    mlmd_store = Path.cwd() / 'mlmd'
    (mlmd_store.parent / 'workspace').mkdir(parents=True, exist_ok=True)

    # The fluent API can initialize itself from environment variables. Define them.
    pipeline_env = {
        'CMF_FLUENT_INIT_METHOD': 'env',
        'CMF_FLUENT_CMF_PARAMS': json.dumps({'filename': mlmd_store.as_posix(), 'graph': False}),
        'CMF_FLUENT_PIPELINE': 'iris',
        'CMF_FLUENT_STEP': None
    }

    # Run steps in a synchronous manner one step at a time. The code also passes the environment variables so that all
    # steps (running in different processes (including, maybe, remote hosts)), use the same CMF configuration.
    for step in (fetch, preprocess, train, test):
        step_env = pipeline_env.copy()
        step_env['CMF_FLUENT_STEP'] = step.remote.__name__
        ref: ray.ObjectRef = step.options(runtime_env={'env_vars': step_env}).remote()
        ray.get(ref)

    # PS: The code can be refactored. If steps return variables, and other steps accept these variables as inputs, it's
    # possible to define a graph of steps, and just ask to run the last step. Ray will take care about distributing
    # steps across available ray workers, possibly, parallelizing computations.


if __name__ == '__main__':
    pipeline()
