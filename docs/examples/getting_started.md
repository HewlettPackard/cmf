# Using `cmf` to track metadata for a ML Pipeline - NEDDS TO BE UPDATED

This example demonstrates how `cmf` tracks metadata associated with executions of various machine learning (ML)
pipelines. ML pipelines differ from other pipelines (e.g., data Extract-Transform-Load pipelines) by the presence of
ML steps, such as training and testing ML models. 

More comprehensive ML pipelines may include steps such as deploying a
trained model and tracking its inference parameters (such as response latency, memory consumption, etc.).

This example, located [here](https://github.com/HewlettPackard/cmf/tree/master/examples/example-get-started), implements a simple
pipeline consisting of five steps:

- The [parse](https://github.com/HewlettPackard/cmf/blob/master/examples/example-get-started/src/parse.py) step splits
  the [raw data](https://github.com/HewlettPackard/cmf/tree/master/examples/example-get-started/artifacts) into
  `train` and `test` raw datasets for training and testing a machine learning model. This step registers one
  input artifact (raw `dataset`) and two output artifacts (train and test `datasets`).
- The [featurize](https://github.com/HewlettPackard/cmf/blob/master/examples/example-get-started/src/featurize.py)
  step creates two machine learning splits - train and test splits - that will be used by an ML training algorithm to
  train ML models. This step registers two input artifacts (raw train and test datasets) and two output artifacts (
  train and test ML datasets).
- The next [train](https://github.com/HewlettPackard/cmf/blob/master/examples/example-get-started/src/train.py) step
  trains an ML model (random forest classifier). It registers one input artifact (the dataset from the previous step)
  and one output artifact (trained ML model).
- The fourth [test](https://github.com/HewlettPackard/cmf/blob/master/examples/example-get-started/src/test.py) step
  evaluates the performance and execution of the ML model trained in the `train` step. This step registers two input
  artifacts (ML model and test dataset) and one output artifact (performance metrics).
- The last [query](https://github.com/HewlettPackard/cmf/blob/master/examples/example-get-started/src/query.py) step
  displays each step of the pipeline's metadata as retrieved from the `cmf-server`, aggregated over all executions.
  For example, if you rerun the pipeline again, the output will include not only metadata associated with the latest
  run, but also the metadata associated with previous runs.
