# Automated artifact logging with CMF

This example implements a four-stage ML pipeline that trains and tests a decision tree classifier from the scikit-learn
library on tiny IRIS dataset.

This example demonstrated one possible approach to do automated logging with Cmf. Automated logging implies developers
do not need (in most cases) directly operate with the Cmf class instance. Instead, the framework automatically logs
execution parameters and input and output artifacts.

Currently, the implementation is in the `cmflib.contrib.auto_logging_v01` module.

Steps to reproduce this example is pretty much the same as those for another CMF example 
([Getting Started](https://hewlettpackard.github.io/cmf/examples/getting_started/)). Quick summary:

- Clone the project and copy content of this directory to some other directory outside the Cmf root directory.
- Initialize python environment, install Cmf (`pip install -e .`) in editable (development mode).
- Install this example dependencies (the only dependency is `scikit-learn`).
- Initialize the Cmf for this example. One quick approach would be to just run `python -m cmflib.contrib.init` (works 
  for quick demo examples).
- Run stages on this pipeline:
    ```
    python pipeline/fetch.py
    python pipeline/preprocess.py dataset=workspace/iris.pkl
    python pipeline/train.py dataset=workspace/train.pkl
    python pipeline/test.py test_dataset=workspace/test.pkl model=workspace/model.pkl
    ```
  
> The code of this example is documented. The documentation of the implementation is in progress.
