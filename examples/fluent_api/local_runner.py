import cmflib.contrib.fluent as cmf
from pipeline import (fetch, preprocess, train, test)


def pipeline():
    """Run IRIS ML pipeline."""
    (cmf.get_work_directory() / 'workspace').mkdir(parents=True, exist_ok=True)
    cmf.set_cmf_parameters(filename='mlmd', graph=False)
    for step in (fetch, preprocess, train, test):
        with cmf.start_step(pipeline='iris', step=step.__name__):
            step()


if __name__ == '__main__':
    pipeline()
