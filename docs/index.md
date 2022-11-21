# CMF in a nutshell

CMF (Common Metadata Framework) library helps to collect and store information associated with  Machine Learning (ML) 
pipelines. It provides  APIs to record  and query the metadata associated with ML pipelines. The framework adopts a 
data first approach and all artifacts recorded in the framework are versioned and identified by the content hash.

## Installation
CMF requires 3.6 <= Python < 3.9. Create python virtual environment with virtualenv:
```shell
virtualenv --python=3.8 .cmf
source .cmf/bin/actiave
```
or conda
```shell
conda create -n cmf python=3.8
conda activate cmf
```

Install the latest version of CMF from GitHub
```shell
pip install https://github.com/HewlettPackard/cmf
```

## Quick Example
Simple "getting started" example is described [here](examples/getting_started.md). 
   
## API Overview

**Import CMF**.
```python
from cmflib import cmf
```

**Create the metadata writer**. The metadata writer is responsible to manage the backend to record the metadata. It 
also creates a pipeline abstraction, which helps to group individual stages and execution.
```python
cmf = cmf.Cmf(
   filename="mlmd",
   pipeline_name="Test-env"
)                                                       
```

**Create a stage on a pipeline**. An ML pipeline can have multiple stages. This context abstraction tracks the stage 
and its metadata. A dictionary can be passed to hold the user given metadata. The custom properties is an optional 
argument.
```python
context = cmf.create_context(
    pipeline_stage="Prepare",
    custom_properties={"user-metadata1":"metadata_value"}
)
```

**Create a stage execution**. A stage in ML pipeline can have multiple executions. Every run is marked as an execution. This 
API helps to track the metadata associated with the execution.
```python
execution = cmf.create_execution(
    execution_type="Prepare-1", 
   custom_properties = {"user-metadata1":"metadata_value"}
)
```

**Log  artifacts**. An Execution could have multiple artifacts associated with it as Input or Output. The path of the 
artifact provided should be path from root of the repo. The metadata associated with the artifact could be logged as an 
optional argument which takes in a dictionary.
```python
cmf.log_dataset(input, "input", custom_properties={"user-metadata1":"metadata_value"})
cmf.log_dataset(output_train, "output", custom_properties={"user-metadata1":"metadata_value"})
cmf.log_dataset(output_test, "output", custom_properties={"user-metadata1":"metadata_value"})
```

**Log a model**. A model developed as part of training step or used in a evaluation or inference step can be logged. It 
can be input or output The metadata associated with the artifact could be logged as an optional argument which takes in 
a dictionary.
```python
cmf.log_model(
   path="model.pkl", event="output", model_framework="SKlearn", model_type="RandomForestClassifier", 
   model_name="RandomForestClassifier:default" 
)
cmf.log_model(
   path="model.pkl", event="input", model_framework="SKlearn", model_type="RandomForestClassifier", 
   model_name="RandomForestClassifier:default" 
)
```

**Log metrics**. Metrics of each step can be logged. The metadata associated with the artifact could be logged as 
argument which takes in a dictionary.
```python
#Can be called at every epoch or every step in the training. This is logged to a parquet file and committed at the 
# commit stage.

#Inside training loop
while True: 
     cmf.log_metric("training_metrics", {"loss": loss}) 
cmf.commit_metrics("training_metrics")
```

**Log Stage metrics**. Metrics for each stage.
```python
cmf.log_execution_metrics("metrics", {"avg_prec": avg_prec, "roc_auc": roc_auc})
```

**Creating the dataslices**. This helps to track a subset of the data. For eg- Accuracy of the model for a slice of 
data (gender, ethnicity etc.).
```python
dataslice = cmf.create_dataslice("slice-a")
for i in range(1, 20, 1):
    j = random.randrange(100)
    dataslice.add_data("data/raw_data/"+str(j)+".xml")
dataslice.commit()
```

## Graph Layer overview 
CMF library has an optional Graph layer which stores the relationships in a Graph Database(NEO4J). To use the graph 
layer, the "graph" parameter in the library init call should be set to true. This is set as false by default. The 
library reads the configuration parameters of the Database from the environment variables. The  variables `NEO4J_URI`, 
`NEO4J_USER_NAME`, `NEO4J_PASSWD` should be either set as environment variables.

```shell
export NEO4J_URI="bolt://10.93.244.219:7687"
export NEO4J_USER_NAME=neo4j
export NEO4J_PASSWD=neo4j 
```

**Create the metadata writer**. The metadata writer is responsible to manage the backend to record the metadata. It also 
creates a pipeline abstraction, which helps to group individual stages and execution.
```python
cmf =  cmf.Cmf(
   filename="mlmd",
   pipeline_name="Test-env", 
   graph=True
)
```

## Jupyterlab environment with CMF pre-installed
- CMF is pre-installed in a JupyterLab Notebook Environment.
- Accessible at `http://[HOST.IP.AD.DR]:8888` (default token: `docker`).
- Within the Jupyterlab environment, a startup script switches context to `$USER:$GROUP` as specified in `.env`.
- The `example-get-started` from this repo is bind mounted into `/home/jovyan/example-get-started`.
- Update `docker-compose.yml` as needed. For example to bind mount another volume on the 
  host: `/lustre/data/dataspaces/dataspaces_testbed/:/home/jovyan/work`

```shell
#create .env file in current folder using env-example as a template. #These are used by docker-compose.yml
docker-compose up --build -d

#To Shutdown/Remove (Remove Volumes as well)
docker-compose down -v
```

## Community
!!! help

    Common Metadata Framework and its documentation are in active stage of development and are very new. If there is
    anything unclear, missing or there's a typo, please, open an issue or pull request 
    on [GitHub](https://github.com/HewlettPackard/cmf).
