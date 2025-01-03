# cmflib.cmf_ray_logger.CmfRayLogger


# CmfRayLogger User Guide

## Overview
The `CmfRayLogger` class is designed to log Ray Tune metrics for the CMF (Common Metadata Framework). It tracks the performance and outputs of trials during the tuning process, directly linking metrics to stages of your CMF pipeline.

## Requirements
- Ensure both `cmf` and `raytune` are installed on your system to use the `CmfRayLogger`.

## Installation
To use `CmfRayLogger`, import it in your Python script:

```python
from cmflib import cmf_ray_logger
```

## Usage

### Initialization

Create an instance of CmfRayLogger by providing the following parameters:

* pipeline_name: A string representing the name of the CMF pipeline.
* file_path: The file path to the metadata file associated with the CMF pipeline.
* pipeline_stage: The name of the current stage of the CMF pipeline.
* data_dir (optional): A directory path where trial data should be logged. If the path is within the CMF directory, it should be relative. If it is outside, it must be an absolute path. Default vale is `None`.

Example of instantiation:
```python
logger = cmf_ray_logger.CmfRayLogger(pipeline_name, file_path, pipeline_stage. data_dir)
```
Here, the `data_dir` argument is used to log the dataset at the start of each trial. Ensure that this path is relative if within the CMF directory and absolute if external to the CMF directory.

## Integration with Ray Tune

After initializing the logger, it should be passed to Ray Tune’s `tune.run` method via the `callbacks` parameter. This setup allows `CmfRayLogger` to log metrics for each trial based on the pipeline configuration and trial execution details.

```Python
from ray import tune

# Example configuration for Ray Tune
config = {
    # Your configuration details
}

tune.run(
    <your_trainable>,
    config=config,
    callbacks=[logger]
)
```

## Model Logging
`CmfRayLogger` can now log the model during trials. To enable this, the `train.report` method must include a special key: `"model_path"`. The value of `"model_path"` should be a relative path pointing to the saved model within the CMF directory.

Important: Ensure that the `"model_path"` is relative, as the DVC wrapper expects all paths nested within the CMF directory to be relative.
```Python
train.report({
    "accuracy": 0.95,
    "loss": 0.05,
    "model_path": "models/example_model.pth"
})
```



## Output
During each trial, `CmfRayLogger` will automatically create a CMF object with attributes set as `pipeline_name`, `pipeline_stage`, and the CMF execution as `trial_id`. It captures the trial's output and logs it under the metric key `'Output'`. Additionally, it logs the dataset at the start of each trial (if data_dir is specified) and logs the model based on the `"model_path"` key in `train.report`.

## Example
Here is a complete example of how to use `CmfRayLogger` with Ray Tune:

```Python
from cmflib import cmf_ray_logger
from ray import tune

# Initialize the logger
logger = cmf_ray_logger.CmfRayLogger("ExamplePipeline", "/path/to/metadata.json", "Stage1", "path/to/data_dir")

# Configuration for tuning
config = {
    # Configuration details
}

# Execute the tuning process
tune.run(
    <your_trainable>,
    config=config,
    callbacks=[logger]
)

# Reporting within your trainable function
train.report({
    "accuracy": 0.95,
    "loss": 0.05,
    "model_path": "path/to/models/example_model.pth"
})
```