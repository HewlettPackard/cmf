# Logging APIs

## Initializing CMF

This calls initiates the library and also creates a pipeline object with the name provided.<br/>
Arguments to be passed CMF:
```python
from cmflib import cmf
import ml_metadata as mlmd

cmf: mlmd.proto.Context = cmf.Cmf(
    filename="mlmd", 
    pipeline_name="Test-env"
)  
```

| Arguments         |                                                                                                                                                                                                                                                                                                                                                                                     |
|-------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| filename          | String Path  to the sqlite file to store the metadata                                                                                                                                                                                                                                                                                                                               |
| pipeline_name     | String Name to uniquely identify the pipeline. Note that name is the unique identification for a pipeline.  If a pipeline already exist with the same name, the existing pipeline object is reused                                                                                                                                                                                  |
| custom_properties | Dictionary (Optional Parameter) - Additional properties of the pipeline that needs to be stored                                                                                                                                                                                                                                                                                     |
| graph             | Bool (Optional Parameter) If set to true, the libray also stores the relationships in the provided graph database. <br/> Following environment variables should be set <br/>  NEO4J_URI - The value should be set to the Graph server URI . <br/> export NEO4J_URI="bolt://ip:port" <br/> User name and password <br/> export NEO4J_USER_NAME=neo4j <br/> export NEO4J_PASSWD=neo4j |

Return Object mlmd.proto.Context 

| mlmd.proto.Context Attributes | Type                                              |
|-------------------------------|---------------------------------------------------|
| create_time_since_epoch       | 	int64 create_time_since_epoch                    |
| custom_properties             | 	repeated CustomPropertiesEntry custom_properties |
| id                            | 	int64 id                                         |
| last_update_time_since_epoch  | 	int64 last_update_time_since_epoch               |
| name                          | 	string name                                      |
| properties                    | 	repeated PropertiesEntry properties              |
| type                          | 	string type                                      |
| type_id                       | 	int64 type_id                                    |

## Initializing pipelines stages 
A pipeline may include multiple stages. A unique name should be provided for every Stage in a pipeline.
```python
context: mlmd.proto.Context = cmf.create_context(
    pipeline_stage="Prepare", 
    custom_properties ={"user-metadata1":"metadata_value"}
)
```

Arguments to be passed CMF:

| Arguments         |                                                                                                                                                   |
|-------------------|---------------------------------------------------------------------------------------------------------------------------------------------------|
| pipeline_stage    | String Name of the pipeline Stage                                                                                                                 |
| custom_properties | Dictionary (Optional Parameter) - The developer's can provide key value pairs of additional properties of the stage that needs to be stored.<br/> |

Return Object mlmd.proto.Context 

| mlmd.proto.Context  Attributes | Type                                              |
|--------------------------------|---------------------------------------------------|
| create_time_since_epoch        | 	int64 create_time_since_epoch                    |
| custom_properties              | 	repeated CustomPropertiesEntry custom_properties |
| id                             | 	int64 id                                         |
| last_update_time_since_epoch   | 	int64 last_update_time_since_epoch               |
| name                           | 	string name                                      |
| properties                     | 	repeated PropertiesEntry properties              |
| type                           | 	string type                                      |
| type_id                        | 	int64 type_id                                    |

## Initializing pipeline stage executions 
A stage can have multiple executions. A unique name should ne provided for every execution. Properties of the execution 
can be passed as key value pairs in the custom properties. Eg: The hyper parameters used for the execution can be 
passed.

```python
execution: mlmd.proto.Execution = cmf.create_execution(
    execution_type="Prepare",
    custom_properties = {"Split": split, "Seed": seed}
)
```

execution_type:String - Name of the execution
custom_properties:Dictionary (Optional Parameter)
Return Execution object of type mlmd.proto.Execution


| Arguments         |                                 |
|-------------------|---------------------------------|
| execution_type    | String Name of the execution    |
| custom_properties | Dictionary (Optional Parameter) |

 Return object of type mlmd.proto.Execution

| mlmd.proto.Execution Attributes |                                                                                                                                                                |
|---------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| create_time_since_epoch	        | int64 create_time_since_epoch                                                                                                                                  |
| custom_properties	              | repeated CustomPropertiesEntry custom_properties                                                                                                               |
| id	                             | int64 id                                                                                                                                                       |
| last_known_state	               | State last_known_state                                                                                                                                         |
| last_update_time_since_epoch    | 	int64 last_update_time_since_epoch                                                                                                                            |
| name	                           | string name                                                                                                                                                    |
| properties	                     | repeated PropertiesEntry properties [Git_Repo, Context_Type, Git_Start_Commit, Pipeline_Type, Context_ID, Git_End_Commit, Execution(Command used), Pipeline_id |
| type	                           | string type                                                                                                                                                    |
| type_id                         | 	int64 type_id                                                                                                                                                 |

## Loging ML datasets 
Tracks a Dataset and its version. The version of the  dataset is automatically obtained from the versioning software(DVC) and tracked as a metadata. 
```python
artifact: mlmd.proto.Artifact = cmf.log_dataset(
    "/repo/data.xml", "input", 
    custom_properties={"Source":"kaggle"}
)
```

| Arguments         | Description                            |
|-------------------|----------------------------------------|
| url               | String The path to the dataset         |
| event             | String Takes arguments INPUT OR OUTPUT |
| custom_properties | Dictionary The Dataset properties      |

Returns an Artifact object of type mlmd.proto.Artifact

| mlmd.proto.Artifact Attributes | Description                                            |
|--------------------------------|--------------------------------------------------------|
| create_time_since_epoch        | 	int64 create_time_since_epoch                         |
| custom_properties              | 	repeated CustomPropertiesEntry custom_properties      |
| id                             | 	int64 id                                              |
| last_update_time_since_epoch   | 	int64 last_update_time_since_epoch                    |
| name                           | 	string name                                           |
| properties                     | 	repeated PropertiesEntry properties(Commit, Git_Repo) |
| state                          | 	State state                                           |
| type                           | 	string type                                           |
| type_id                        | 	int64 type_id                                         |
| uri                            | 	string uri                                            |

## Logging ML models 
```python
artifact: mlmd.proto.Artifact= cmf.log_model(
    path="path/to/model.pkl", 
    event="output", 
    model_framework="SKlearn", 
    model_type="RandomForestClassifier", 
    model_name="RandomForestClassifier:default"
)
```

| Arguments         | Description                            |
|-------------------|----------------------------------------|
| path              | String Path to the model model file    |
| event             | String Takes arguments INPUT OR OUTPUT |
| model_framework   | String Framework used to create model  |
| model_type        | String Type of Model Algorithm used    |
| model_name        | String Name of the Algorithm used      |
| custom_properties | Dictionary The model properties        |

Returns Atifact object of type mlmd.proto.Artifact

| mlmd.proto.Artifact Attributes | Description                                                                           |
|--------------------------------|---------------------------------------------------------------------------------------|
| create_time_since_epoch        | 	int64 create_time_since_epoch                                                        |
| custom_properties              | 	repeated CustomPropertiesEntry custom_properties                                     |
| id                             | 	int64 id                                                                             |
| last_update_time_since_epoch   | 	int64 last_update_time_since_epoch                                                   |
| name                           | 	string name                                                                          |
| properties                     | 	repeated PropertiesEntry properties(commit, model_framework, model_type, model_name) |
| state                          | 	State state                                                                          |
| type                           | 	string type                                                                          |
| type_id                        | 	int64 type_id                                                                        |
| uri                            | 	string uri                                                                           |

## Logging execution metrics for coarse-grained tracking 

```python
cmf.log_execution_metrics(
    metrics_name :"Training_Metrics", 
    {"auc":auc,"loss":loss}
)
```

| Arguments         | Description                         |
|-------------------|-------------------------------------|
| metrics_name      | String Name to identify the metrics |
| custom_properties | Dictionary Metrics                  |

## Logging per-step metrics for fine-grained tracking 
The metrics provided is stored in a parquet file. The commit_metrics call add the parquet file in the version control framework.
The metrics written in the parquet file can be retrieved using the read_metrics call
```python
#Can be called at every epoch or every step in the training. This is logged to a parquet file and committed 
# at the commit stage.

#Inside training loop
while True: 
     metawriter.log_metric("training_metrics", {"loss":loss}) 
metawriter.commit_metrics("training_metrics")
```

| Arguments for log_metric | Description                         |
|--------------------------|-------------------------------------|
| metrics_name             | String Name to identify the metrics |
| custom_properties        | Dictionary Metrics                  |

| Arguments for commit_metrics | Description                         |
|------------------------------|-------------------------------------|
| metrics_name                 | String Name to identify the metrics |

## Creating dataslices
This helps to track a subset of the data. Currently supported only for file abstractions. 
For eg- Accuracy of the model for a slice of data(gender, ethnicity etc)
```python
dataslice = cmf.create_dataslice("slice-a")
```

| Arguments for create_dataslice |                                        |
|--------------------------------|----------------------------------------|
| name                           | String Name to identify the dataslice  |
Returns a Dataslice object

## Adding data to dataslices
Currently supported only for file abstractions.
Pre condition - The parent folder, containing the file should already be versioned. 
```python
dataslice.add_data("data/raw_data/"+str(j)+".xml")
```

| Arguments | Description                                                   |
|-----------|---------------------------------------------------------------|
| name      | String Name to identify the file to be added to the dataslice |

## Committing dataslices 
The created dataslice is versioned and added to underneath data versioning software
```python
dataslice.commit()
```
