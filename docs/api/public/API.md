## Logging API'S

### 1. Library init call - Cmf()

This calls initiates the library and also creates a pipeline object with the name provided.<br/>
Arguments to be passed CMF:<br/>
```python
cmf = cmf.Cmf(filename="mlmd", pipeline_name="Test-env")

# Returns a Context object of mlmd.proto.Context
```

| Argument | Type | Description |
|----------|------|-------------|
| filename | String | Path to the sqlite file to store the metadata |
| pipeline_name | String | Name to uniquely identify the pipeline. Note that name is the unique identification for a pipeline. If a pipeline already exists with the same name, the existing pipeline object is reused |
| custom_properties | Dictionary (Optional) | Additional properties of the pipeline that needs to be stored |
| graph | Bool (Optional) | If set to true, the library also stores the relationships in the provided graph database. Following environment variables should be set: NEO4J_URI, NEO4J_USER_NAME, NEO4J_PASSWD |

**Return Object:** `mlmd.proto.Context`

| Attribute | Type | Description |
|-----------|------|-------------|
| create_time_since_epoch | int64 | Creation timestamp |
| custom_properties | repeated CustomPropertiesEntry | Custom properties |
| id | int64 | Unique identifier |
| last_update_time_since_epoch | int64 | Last update timestamp |
| name | string | Context name |
| properties | repeated PropertiesEntry | Properties |
| type | string | Context type |
| type_id | int64 | Type identifier |

### 2. create_context - Creates a Stage with properties
A pipeline may include multiple stages. A unique name should be provided for every Stage in a pipeline.</br>
Arguments to be passed CMF:<br/>
```python
context = cmf.create_context(pipeline_stage="Prepare", custom_properties={"user-metadata1":"metadata_value"})
```

| Argument | Type | Description |
|----------|------|-------------|
| pipeline_stage | String | Name of the pipeline Stage |
| custom_properties | Dictionary (Optional) | Key value pairs of additional properties of the stage that needs to be stored |

**Return Object:** `mlmd.proto.Context`

| Attribute | Type | Description |
|-----------|------|-------------|
| create_time_since_epoch | int64 | Creation timestamp |
| custom_properties | repeated CustomPropertiesEntry | Custom properties |
| id | int64 | Unique identifier |
| last_update_time_since_epoch | int64 | Last update timestamp |
| name | string | Context name |
| properties | repeated PropertiesEntry | Properties |
| type | string | Context type |
| type_id | int64 | Type identifier |

### 3. create_execution - Creates an Execution with properties
A stage can have multiple executions. A unique name should ne provided for exery execution. 
Properties of the execution can be paased as key value pairs in the custom properties. Eg: The hyper parameters used for the execution can be passed.
```python
execution = cmf.create_execution(execution_type="Prepare",
                                 custom_properties={"Split": split, "Seed": seed})

# execution_type: String - Name of the execution
# custom_properties: Dictionary (Optional Parameter)
# Returns: Execution object of type mlmd.proto.Execution
```

| Argument | Type | Description |
|----------|------|-------------|
| execution_type | String | Name of the execution |
| custom_properties | Dictionary (Optional) | Additional properties for the execution |

**Return Object:** `mlmd.proto.Execution`

| Attribute | Type | Description |
|-----------|------|-------------|
| create_time_since_epoch | int64 | Creation timestamp |
| custom_properties | repeated CustomPropertiesEntry | Custom properties |
| id | int64 | Unique identifier |
| last_known_state | State | Last known execution state |
| last_update_time_since_epoch | int64 | Last update timestamp |
| name | string | Execution name |
| properties | repeated PropertiesEntry | Properties (Git_Repo, Context_Type, Git_Start_Commit, Pipeline_Type, Context_ID, Git_End_Commit, Execution Command, Pipeline_id) |
| type | string | Execution type |
| type_id | int64 | Type identifier |

### 4. log_dataset - Logs a Dataset and its properties
Tracks a Dataset and its version. The version of the  dataset is automatically obtained from the versioning software(DVC) and tracked as a metadata. 
```python
artifact = cmf.log_dataset("/repo/data.xml", "input", custom_properties={"Source": "kaggle"})
```

| Argument | Type | Description |
|----------|------|-------------|
| url | String | The path to the dataset |
| event | String | Takes arguments INPUT or OUTPUT |
| custom_properties | Dictionary | The Dataset properties |

**Return Object:** `mlmd.proto.Artifact`

| Attribute | Type | Description |
|-----------|------|-------------|
| create_time_since_epoch | int64 | Creation timestamp |
| custom_properties | repeated CustomPropertiesEntry | Custom properties |
| id | int64 | Unique identifier |
| last_update_time_since_epoch | int64 | Last update timestamp |
| name | string | Artifact name |
| properties | repeated PropertiesEntry | Properties (Commit, Git_Repo) |
| state | State | Artifact state |
| type | string | Artifact type |
| type_id | int64 | Type identifier |
| uri | string | Artifact URI |

### 5. log_model - Logs a model and its properties.
```python
cmf.log_model(path="path/to/model.pkl",
              event="output",
              model_framework="SKlearn",
              model_type="RandomForestClassifier",
              model_name="RandomForestClassifier:default")

# Returns an Artifact object of type mlmd.proto.Artifact
```

| Argument | Type | Description |
|----------|------|-------------|
| path | String | Path to the model file |
| event | String | Takes arguments INPUT or OUTPUT |
| model_framework | String | Framework used to create model |
| model_type | String | Type of Model Algorithm used |
| model_name | String | Name of the Algorithm used |
| custom_properties | Dictionary | The model properties |

**Return Object:** `mlmd.proto.Artifact`

| Attribute | Type | Description |
|-----------|------|-------------|
| create_time_since_epoch | int64 | Creation timestamp |
| custom_properties | repeated CustomPropertiesEntry | Custom properties |
| id | int64 | Unique identifier |
| last_update_time_since_epoch | int64 | Last update timestamp |
| name | string | Artifact name |
| properties | repeated PropertiesEntry | Properties (commit, model_framework, model_type, model_name) |
| state | State | Artifact state |
| type | string | Artifact type |
| type_id | int64 | Type identifier |
| uri | string | Artifact URI |

### 6. log_execution_metrics Logs the metrics for the execution
```python
cmf.log_execution_metrics(metrics_name="Training_Metrics", custom_properties={"auc": auc, "loss": loss})
```

|Arguments||
|-------|------|
|metrics_name| String Name to identify the metrics|
|custom_properties| Dictionary Metrics|

### 7. log_metrics Logs the per Step metrics for fine grained tracking
The metrics provided is stored in a parquet file. The commit_metrics call add the parquet file in the version control framework.
The metrics written in the parquet file can be retrieved using the read_metrics call
```python
# Can be called at every epoch or every step in the training.
# This is logged to a parquet file and committed at the commit stage.
while True:  # Inside training loop
    metawriter.log_metric("training_metrics", {"loss": loss})
metawriter.commit_metrics("training_metrics")
```

|Arguments for log_metric |    |
|-------|------|
|metrics_name| String Name to identify the metrics|
|custom_properties| Dictionary Metrics|

|Arguments for commit_metrics |    |
|-------|------|
|metrics_name| String Name to identify the metrics|

### 8. create_dataslice
This helps to track a subset of the data. Currently supported only for file abstractions. 
For eg- Accuracy of the model for a slice of data(gender, ethnicity etc)
```python
dataslice = cmf.create_dataslice("slice-a")
```

|Arguments for create_dataslice |    |
|-------||
|name| String Name to identify the dataslice
Returns a Dataslice object

### 9. add_data Adds data to a dataslice.
Currently supported only for file abstractions.
Pre condition - The parent folder, containing the file should already be versioned. 
```python
dataslice.add_data("data/raw_data/" + str(j) + ".xml")
```

|Arguments||
|-------|------|
|name| String Name to identify the file to be added to the dataslice

### 10. Dataslice Commit - Commits the created dataslice
The created dataslice is versioned and added to underneath data versioning softwarre
```python
dataslice.commit()
```
