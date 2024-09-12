# cmflib.cmf_ray_logger.CmfRayLogger


# CmfRayLogger User Guide

## Overview
The `CmfRayLogger` class is designed to log Ray Tune metrics for the CMF (Common Metadata Framework). It tracks the performance and outputs of trials during the tuning process, directly linking metrics to stages of your CMF pipeline.

## Requirements
- Ensure both `cmf` and `raytune` are installed on your system to use the `CmfRayLogger`.

## Installation
To use `CmfRayLogger`, import it in your Python script:

```python
from cmf import cmf_ray_logger
```

## Usage

### Initialization

Create an instance of CmfRayLogger by providing the following parameters:

* pipeline_name: A string representing the name of the CMF pipeline.
* file_path: The file path to the metadata file associated with the CMF pipeline.
* pipeline_stage: The name of the current stage of the CMF pipeline.

Example of instantiation:
```python
logger = cmf_ray_logger.CmfRayLogger(pipeline_name, file_path, pipeline_stage)
```

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

## Output
During each trial, `CmfRayLogger` will automatically create a CMF object with attributes set as `pipeline_name`, `pipeline_stage`, and the CMF execution as `trial_id`. It captures the trial's output and logs it under the metric key `'Output'`.

## Example
Here is a complete example of how to use `CmfRayLogger` with Ray Tune:

```Python
from cmf import cmf_ray_logger
from ray import tune

# Initialize the logger
logger = cmf_ray_logger.CmfRayLogger("ExamplePipeline", "/path/to/metadata.json", "Stage1")

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
```