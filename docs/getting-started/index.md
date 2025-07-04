# Getting Started

This guide provides step-by-step instructions for installing, configuring, and using CMF (Common Metadata Framework) for ML pipeline metadata tracking. Whether you're setting up a local development environment or deploying a production system, this guide will help you get started quickly.

## Installation and Configuration

### Prerequisites

Before installing CMF, ensure you have the following prerequisites:

- **Python**: Version 3.9 to 3.11 (3.10 recommended)
- **Git**: Latest version for code versioning
- **Docker**: For containerized deployment (optional)
- **Storage Backend**: S3, MinIO, or local storage for artifacts

### Installation Options

#### Option 1: Install from PyPI (Recommended)

```bash
# Create virtual environment
python -m venv cmf-env
source cmf-env/bin/activate  # On Windows: cmf-env\Scripts\activate

# Install CMF
pip install cmflib
```

#### Option 2: Install from GitHub (Latest Development)

```bash
# Create virtual environment
python -m venv cmf-env
source cmf-env/bin/activate

# Install from GitHub
pip install git+https://github.com/HewlettPackard/cmf.git
```

#### Option 3: Docker Development Environment

```bash
# Clone repository
git clone https://github.com/HewlettPackard/cmf.git
cd cmf

# Create required directories
mkdir $HOME/workspace
mkdir $HOME/dvc_remote

# Create .env file with configuration
cat > .env << EOF
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
DVC_REMOTE_URL=s3://your-bucket/path
GIT_USER_NAME=your_name
GIT_USER_EMAIL=your_email@example.com
NEO4J_USER_NAME=neo4j
NEO4J_PASSWD=password
EOF

# Start development environment
docker-compose up
```

### Initial Configuration

#### Local Configuration

For local development with SQLite storage:

```bash
# Initialize CMF configuration
cmf init --type=local

# Configure Git (if not already configured)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

#### Server Configuration

For production deployment with PostgreSQL and server:

```bash
# Initialize with server configuration
cmf init --type=server \
  --url=http://your-cmf-server:8080 \
  --neo4j-uri=bolt://your-neo4j:7687 \
  --neo4j-user=neo4j \
  --neo4j-password=your_password

# Configure artifact storage (S3 example)
cmf init --type=s3 \
  --endpoint-url=https://s3.amazonaws.com \
  --access-key-id=your_access_key \
  --secret-access-key=your_secret_key \
  --bucket-name=your-cmf-bucket
```

#### MinIO Configuration

For self-hosted S3-compatible storage:

```bash
# Configure MinIO backend
cmf init --type=minio \
  --endpoint-url=http://your-minio:9000 \
  --access-key-id=minioadmin \
  --secret-access-key=minioadmin \
  --bucket-name=cmf-artifacts
```

### Verification

Verify your installation:

```python
# Test CMF installation
from cmflib import cmf

# Create test instance
cmf_instance = cmf.Cmf(filename="test_mlmd", pipeline_name="test_pipeline")
print("CMF installation successful!")

# Test basic functionality
context = cmf_instance.create_context(pipeline_stage="test")
execution = cmf_instance.create_execution(execution_type="test_run")
print("CMF basic functionality working!")
```

## Basic Usage Examples

### Simple ML Pipeline Example

Here's a complete example of tracking a simple ML pipeline with CMF:

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib
from cmflib import cmf

# Initialize CMF
cmf_instance = cmf.Cmf(
    filename="mlmd",
    pipeline_name="iris_classification"
)

# Create pipeline context
context = cmf_instance.create_context(pipeline_stage="training")

# Data Loading Stage
data_execution = cmf_instance.create_execution(execution_type="data_loading")

# Log input dataset
cmf_instance.log_dataset(
    url="iris_dataset.csv",
    event="input",
    custom_properties={"source": "sklearn", "samples": 150}
)

# Load and prepare data
data = pd.read_csv("iris_dataset.csv")
X = data.drop('target', axis=1)
y = data['target']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Log processed datasets
cmf_instance.log_dataset(
    url="train_data.csv",
    event="output",
    custom_properties={"samples": len(X_train), "features": X_train.shape[1]}
)

cmf_instance.log_dataset(
    url="test_data.csv", 
    event="output",
    custom_properties={"samples": len(X_test), "features": X_test.shape[1]}
)

# Model Training Stage
train_execution = cmf_instance.create_execution(execution_type="model_training")

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Save and log model
joblib.dump(model, "trained_model.pkl")
cmf_instance.log_model(
    path="trained_model.pkl",
    event="output",
    model_framework="sklearn",
    custom_properties={
        "algorithm": "RandomForest",
        "n_estimators": 100,
        "random_state": 42
    }
)

# Model Evaluation Stage
eval_execution = cmf_instance.create_execution(execution_type="model_evaluation")

# Evaluate model
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

# Log metrics
cmf_instance.log_metrics(
    metrics_name="evaluation_metrics",
    custom_properties={
        "accuracy": accuracy,
        "test_samples": len(X_test),
        "model_type": "RandomForestClassifier"
    }
)

print(f"Pipeline completed! Model accuracy: {accuracy:.3f}")
print("All metadata logged to CMF")
```

### Advanced Pipeline with TensorBoard

Example with deep learning and TensorBoard integration:

```python
import tensorflow as tf
from cmflib import cmf
import os

# Initialize CMF with TensorBoard support
cmf_instance = cmf.Cmf(
    filename="mlmd",
    pipeline_name="deep_learning_pipeline"
)

# Create context for training
context = cmf_instance.create_context(pipeline_stage="deep_training")
execution = cmf_instance.create_execution(execution_type="neural_network_training")

# Set up TensorBoard logging
log_dir = "logs/fit"
tensorboard_callback = tf.keras.callbacks.TensorBoard(
    log_dir=log_dir,
    histogram_freq=1,
    write_graph=True,
    write_images=True
)

# Log training dataset
cmf_instance.log_dataset(
    url="training_data.tfrecord",
    event="input",
    custom_properties={
        "format": "tfrecord",
        "samples": 10000,
        "image_size": "224x224"
    }
)

# Build and train model
model = tf.keras.Sequential([
    tf.keras.layers.Conv2D(32, 3, activation='relu'),
    tf.keras.layers.MaxPooling2D(),
    tf.keras.layers.Conv2D(64, 3, activation='relu'),
    tf.keras.layers.MaxPooling2D(),
    tf.keras.layers.Flatten(),
    tf.keras.layers.Dense(64, activation='relu'),
    tf.keras.layers.Dense(10, activation='softmax')
])

model.compile(
    optimizer='adam',
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

# Train with TensorBoard logging
history = model.fit(
    train_dataset,
    epochs=10,
    validation_data=val_dataset,
    callbacks=[tensorboard_callback]
)

# Save and log model
model.save("trained_cnn_model")
cmf_instance.log_model(
    path="trained_cnn_model",
    event="output",
    model_framework="tensorflow",
    custom_properties={
        "architecture": "CNN",
        "layers": len(model.layers),
        "parameters": model.count_params(),
        "optimizer": "adam"
    }
)

# Log TensorBoard logs to CMF
cmf_instance.log_tensorboard_logs(log_dir)

# Log final metrics
final_accuracy = max(history.history['val_accuracy'])
cmf_instance.log_metrics(
    metrics_name="training_results",
    custom_properties={
        "final_val_accuracy": final_accuracy,
        "epochs": 10,
        "best_epoch": history.history['val_accuracy'].index(final_accuracy) + 1
    }
)

print(f"Training completed! Best validation accuracy: {final_accuracy:.3f}")
```

### Multi-Stage Pipeline Example

Example of a complex pipeline with multiple stages:

```python
from cmflib import cmf

# Initialize CMF for multi-stage pipeline
cmf_instance = cmf.Cmf(
    filename="mlmd",
    pipeline_name="production_ml_pipeline"
)

# Stage 1: Data Collection
data_context = cmf_instance.create_context(pipeline_stage="data_collection")
collection_execution = cmf_instance.create_execution(execution_type="data_ingestion")

cmf_instance.log_dataset(
    url="raw_data_source.db",
    event="input",
    custom_properties={"source": "production_db", "query_time": "2024-01-15T10:00:00Z"}
)

# Stage 2: Data Preprocessing  
preprocess_context = cmf_instance.create_context(pipeline_stage="preprocessing")
preprocess_execution = cmf_instance.create_execution(execution_type="data_cleaning")

cmf_instance.log_dataset(
    url="cleaned_data.parquet",
    event="output", 
    custom_properties={"rows_removed": 1500, "columns_added": 3}
)

# Stage 3: Feature Engineering
feature_context = cmf_instance.create_context(pipeline_stage="feature_engineering")
feature_execution = cmf_instance.create_execution(execution_type="feature_creation")

cmf_instance.log_dataset(
    url="feature_engineered_data.parquet",
    event="output",
    custom_properties={"new_features": 15, "feature_selection": "mutual_info"}
)

# Stage 4: Model Training
train_context = cmf_instance.create_context(pipeline_stage="model_training")
train_execution = cmf_instance.create_execution(execution_type="hyperparameter_tuning")

cmf_instance.log_model(
    path="best_model.pkl",
    event="output",
    model_framework="xgboost",
    custom_properties={"cv_score": 0.87, "hyperparams": {"max_depth": 6, "learning_rate": 0.1}}
)

# Stage 5: Model Validation
validation_context = cmf_instance.create_context(pipeline_stage="validation")
validation_execution = cmf_instance.create_execution(execution_type="cross_validation")

cmf_instance.log_metrics(
    metrics_name="validation_results",
    custom_properties={
        "cv_mean": 0.87,
        "cv_std": 0.02,
        "holdout_score": 0.85,
        "validation_strategy": "5-fold"
    }
)

print("Multi-stage pipeline completed and logged to CMF!")
```

### Querying Pipeline Metadata

Example of querying and analyzing pipeline metadata:

```python
from cmflib import cmfquery

# Initialize query interface
query = cmfquery.CmfQuery(mlmd_path="mlmd")

# Get all pipelines
pipelines = query.get_pipeline_names()
print(f"Available pipelines: {pipelines}")

# Get executions for a specific pipeline
executions = query.get_all_executions_in_pipeline("iris_classification")
print(f"Executions in pipeline: {len(executions)}")

# Get artifacts by type
models = query.get_all_artifacts_by_type("Model")
datasets = query.get_all_artifacts_by_type("Dataset")
metrics = query.get_all_artifacts_by_type("Metrics")

print(f"Total artifacts - Models: {len(models)}, Datasets: {len(datasets)}, Metrics: {len(metrics)}")

# Get lineage for a specific artifact
model_lineage = query.get_upstream_artifacts_by_artifact_name("trained_model.pkl")
print(f"Upstream artifacts for model: {[a.name for a in model_lineage]}")

# Get execution details
for execution in executions[:3]:  # Show first 3 executions
    print(f"Execution: {execution.name}")
    print(f"  Type: {execution.type}")
    print(f"  Properties: {execution.custom_properties}")
    print()
```

This comprehensive getting started guide provides everything needed to begin using CMF effectively, from basic installation to advanced pipeline tracking scenarios.
