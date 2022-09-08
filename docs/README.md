# Common Metadata Framework(CMF)
CMF library helps to collect and store information associated with  ML pipelines. 
It provides  api's to record  and query the metadata associated with ML pipelines.
The framework adopts a data first approach and all artifacts recorded in the framework are versioned and identified by the content hash.<br>
[Detailed documentation of the API's](API.md)

# Getting Started
### Install the library

#### Creating the wheel file

```
python setup.py bdist_wheel
cd dist
pip install <cmflib-0.0.1-py2-none-any.whl>

```
or Install directly,
pip install .

[Quick start](examples/example-get-started/README.md)
### Pre-Requisite
1. Python Version - Needs Python version >=3.6 and <3.9 (Not compatible with Python3.9)<br>
2. Set Environment variables.<br>
   Library uses DVC for artifact versioning and git for code versioning. It requires a set of environment variables to operate DVC and git. The list of environment           variables needed can be found in example-get-started/sample_env.<br>
   Copy sample_env from example-get-started directory to local directory.
   Modify sample_env and run 'source sample_env' to set the environment variables.<br>
3. Copy initialize.sh from example-get-started folder to your local directory.<br>
   Run command - sh initialize.sh <br>
   Before running the script, please ensure that required environment variables are set.<br>
   This configures DVC and git with the provided variables in Step 1.<br> 
   

## Logging metadata with CMF
#### Import of the library to record the metadata
```python
from cmflib import cmf

```

### Create the metadata writer
The metadata writer is responsible to manage the backend to record the metadata.
It also creates a pipeline abstraction, which helps to group individual stages and execution.
```python
cmf = cmf.Cmf(filename="mlmd",
                                  pipeline_name="Test-env")                        
                                  
```
### Create the stage in pipeline.
An ML pipeline can have multiple stages. This context abstraction tracks the stage and its metadata.
A dictionary can be passed to hold the user given metadata. The custom properties is an optional argument
 ```python
context = cmf.create_context(pipeline_stage="Prepare",
                                    custom_properties={"user-metadata1":"metadata_value"})
```

#### Create the execution
A stage in ML pipeline can have multiple executions. Every run is marked as an execution.
This API helps to track the metadata associated with the execution
```python
execution = cmf.create_execution(execution_type="Prepare-1", custom_properties = {"user-metadata1":"metadata_value"})
```
#### Log  artifacts
An Execution could have multiple artifacts associated with it as Input or Output. The path of the artifact provided should be path from root of the repo. 
The metadata associated with the artifact could be logged as an optional argument which takes in a dictionary
```python
cmf.log_dataset(input, "input", custom_properties={"user-metadata1":"metadata_value"})
cmf.log_dataset(output_train, "output", custom_properties={"user-metadata1":"metadata_value"})
cmf.log_dataset(output_test, "output", custom_properties={"user-metadata1":"metadata_value"})
```
#### Log model
A model developed as part of training step or used in a evaluation or inference step can be logged. It can be input or output 
The metadata associated with the artifact could be logged as an optional argument which takes in a dictionary
```python
cmf.log_model(path="model.pkl", event="output", model_framework="SKlearn", model_type="RandomForestClassifier", model_name="RandomForestClassifier:default" )
cmf.log_model(path="model.pkl", event="input", model_framework="SKlearn", model_type="RandomForestClassifier", model_name="RandomForestClassifier:default" )
```
#### Log metrics
Metrics of each step can be logged 
The metadata associated with the artifact could be logged as argument which takes in a dictionary
```python
#Can be called at every epoch or every step in the training. This is logged to a parquet file and commited at the commit stage.
while True: #Inside training loop
     cmf.log_metric("training_metrics", {"loss":loss}) 
cmf.commit_metrics("training_metrics")
```
#### Log Stage metrics
Metrics for each stage.
```python
cmf.log_execution_metrics("metrics", {"avg_prec":avg_prec, "roc_auc":roc_auc})
```
#### Creating the dataslices 
This helps to track a subset of the data. For eg- Accuracy of the model for a slice of data(gender, ethnicity etc)
```python
dataslice = cmf.create_dataslice("slice-a")
for i in range(1,20,1):
    j = random.randrange(100)
    dataslice.add_data("data/raw_data/"+str(j)+".xml")
dataslice.commit()
```
### To use Graph Layer 
CMF library has an optional Graph layer which stores the relationships in a Graph Database(NEO4J)
To use the graph layer, the "graph" parameter in the library init call should be set to true. This is set as false by default.
The library reads the configuration parameters of the Database from the environment variables. 
The  variables "NEO4J_URI", "NEO4J_USER_NAME", "NEO4J_PASSWD" should be either set as environment variables.

```
 export NEO4J_URI="bolt://10.93.244.219:7687"
 export NEO4J_USER_NAME=neo4j
 export NEO4J_PASSWD=neo4j
 
'''
Create the metadata writer
The metadata writer is responsible to manage the backend to record the metadata.
It also creates a pipeline abstraction, which helps to group individual stages and execution.
'''
cmf =  cmf.Cmf(filename="mlmd",
                                  pipeline_name="Test-env", graph=True)

```

### Use a Jupyterlab environment with CMF pre-installed
- CMF is preinstalled in a JupyterLab Notebook Environment.
- Accessible at http://[HOST.IP.AD.DR]:8888 (default token: `docker`)
- Within the Jupyterlab environment, a startup script switches context to `$USER:$GROUP` as specified in `.env`
- `example-get-started` from this repo is bind mounted into `/home/jovyan/example-get-started`
- Update `docker-compose.yml` as needed. For example to bind mount another volume on the host: `/lustre/data/dataspaces/dataspaces_testbed/:/home/jovyan/work`

```
#create .env file in current folder using env-example as a template. #These are used by docker-compose.yml
docker-compose up --build -d
#To Shutdown/Remove (Remove Volumes as well)
docker-compose down -v
```
