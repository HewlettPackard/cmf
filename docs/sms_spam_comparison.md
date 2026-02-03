# SMS Spam Classification: With and Without CMF

This document compares two implementations of the same ML pipeline - one using standard scikit-learn workflow and another enhanced with CMF (Common Metadata Framework) tracking.

> **📁 Want to run this example?** See the [SMS Spam Example](/examples/sms_spam/) with complete setup instructions and runnable code.

## Overview

Both implementations follow the same 4-stage pipeline:

1. **Prepare**: Load and clean the SMS spam dataset
2. **Featurize**: Extract features using TF-IDF vectorization
3. **Train**: Train a baseline Random Forest classifier
4. **Hyperparameter Tuning**: Optimize the model using GridSearchCV

## Code Comparison

### Stage 1: Prepare

<table>
<tr>
<th>Without CMF</th>
<th>With CMF</th>
</tr>
<tr>
<td>

```python
# Load dataset
path = "artifacts/SMSSpamCollection"
df = pd.read_csv(path, sep='\t', 
                 names=['label', 'message'])

# Convert labels to binary
df['label'] = df['label'].map({'ham': 0, 'spam': 1})

# Save cleaned data
cleaned_path = "artifacts/cleaned_data.tsv"
df.to_csv(cleaned_path, sep='\t', index=False)
```

</td>
<td>

```python
# Create CMF context and execution
metawriter.create_context(pipeline_stage="Prepare")
metawriter.create_execution(execution_type="Prep")

# Log and load dataset
path = "artifacts/SMSSpamCollection"
metawriter.log_dataset(path, "input")

df = pd.read_csv(path, sep='\t', 
                 names=['label', 'message'])

# Convert labels to binary
df['label'] = df['label'].map({'ham': 0, 'spam': 1})

# Save and log cleaned data
cleaned_path = "artifacts/cleaned_data.tsv"
df.to_csv(cleaned_path, sep='\t', index=False)
metawriter.log_dataset(cleaned_path, "output", 
                      {'ham': '0', 'spam': '1'})
```

</td>
</tr>
</table>

**What CMF Adds:**
- Creates a pipeline context for "Prepare" stage
- Tracks input dataset location and usage
- Logs output artifacts with metadata (label encoding info)
- Creates lineage between input and output datasets

---

### Stage 2: Featurize

<table>
<tr>
<th>Without CMF</th>
<th>With CMF</th>
</tr>
<tr>
<td>

```python
# Load cleaned data
df = pd.read_csv(cleaned_path, sep='\t')

# Feature extraction using TF-IDF
tfidf = TfidfVectorizer(max_features=3000)
tfidf.fit_transform(df['message_cleaned'])

# Save TF-IDF vectorizer
tf_file = "./artifacts/tfidf_vectorizer.pkl"
joblib.dump(tfidf, tf_file)
```

</td>
<td>

```python
# Create CMF context and execution
metawriter.create_context(pipeline_stage="Featurize")
metawriter.create_execution(execution_type="Feat")

# Log input data
metawriter.log_dataset(cleaned_path, "input", 
                      {'ham': '0', 'spam': '1'})

# Load and process data
df = pd.read_csv(cleaned_path, sep='\t')

# Feature extraction using TF-IDF
tfidf = TfidfVectorizer(max_features=3000)
tfidf.fit_transform(df['message_cleaned'])

# Save and log TF-IDF vectorizer
tf_file = "./artifacts/tfidf_vectorizer.pkl"
joblib.dump(tfidf, tf_file)
metawriter.log_dataset(tf_file, "output", 
                      {"max_features": 3000})
```

</td>
</tr>
</table>

**What CMF Adds:**
- Creates separate context for "Featurize" stage
- Tracks TF-IDF configuration (max_features parameter)
- Links cleaned data input to vectorizer output
- Enables traceability of feature engineering choices

---

### Stage 3: Train

<table>
<tr>
<th>Without CMF</th>
<th>With CMF</th>
</tr>
<tr>
<td>

```python
# Load data and vectorizer
df = pd.read_csv(cleaned_path, sep='\t')
tfidf = joblib.load(tf_file)

# Transform and split data
X = tfidf.fit_transform(
    df['message_cleaned']).toarray()
y = df['label']
X_train, X_test, y_train, y_test = \
    train_test_split(X, y, test_size=0.2, 
                     random_state=42)

# Train Random Forest model
model = RandomForestClassifier(
    n_estimators=100, 
    max_depth=10, 
    random_state=42
)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f'Baseline Accuracy: {accuracy * 100:.2f}%')

# Save model
baseline_model_file = "./artifacts/baseline_rf.pkl"
joblib.dump(model, baseline_model_file)
```

</td>
<td>

```python
# Create CMF context and execution
metawriter.create_context(pipeline_stage="Train")
metawriter.create_execution(execution_type="Trn")

# Log input datasets
metawriter.log_dataset(cleaned_path, "input", 
                      {'ham': '0', 'spam': '1'})
metawriter.log_dataset(tf_file, "input", 
                      {"max_features": 3000})

# Load data and vectorizer
df = pd.read_csv(cleaned_path, sep='\t')
tfidf = joblib.load(tf_file)

# Transform and split data
X = tfidf.fit_transform(
    df['message_cleaned']).toarray()
y = df['label']
X_train, X_test, y_train, y_test = \
    train_test_split(X, y, test_size=0.2, 
                     random_state=42)

# Train Random Forest model
model_config = {
    'n_estimators': 100, 
    'max_depth': 10, 
    'random_state': 42
}
model = RandomForestClassifier(**model_config)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f'Baseline Accuracy: {accuracy * 100:.2f}%')

# Save and log model
baseline_model_file = "./artifacts/baseline_rf.pkl"
joblib.dump(model, baseline_model_file)

metawriter.log_model(
    baseline_model_file,
    "output",
    model_framework="SKlearn",
    model_type="Classifier",
    model_name="RandomForestClassifier:Baseline",
    custom_properties=model_config
)

# Log metrics
metawriter.log_execution_metrics(
    metrics_name="baseline_training_metrics",
    custom_properties={
        'accuracy_score': f'{accuracy * 100:.2f}%'
    }
)
```

</td>
</tr>
</table>

**What CMF Adds:**
- Tracks all hyperparameters used for training
- Logs model as a distinct artifact type (not just a file)
- Records model framework, type, and name for easy identification
- Captures training metrics with execution context
- Links input data and vectorizer to the trained model

---

### Stage 4: Hyperparameter Tuning

<table>
<tr>
<th>Without CMF</th>
<th>With CMF</th>
</tr>
<tr>
<td>

```python
# Define hyperparameter grid
param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [5, 10, 15],
    'criterion': ['gini', 'entropy']
}

# Perform grid search
grid_search = GridSearchCV(
    estimator=RandomForestClassifier(),
    param_grid=param_grid,
    scoring='accuracy',
    cv=5
)
grid_search.fit(X_train, y_train)

# Evaluate
y_pred = grid_search.best_estimator_.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f'Optimized Accuracy: {accuracy * 100:.2f}%')
print(f'Improvement: {(accuracy - accuracy_baseline) * 100:.2f}%')

# Save optimized model
model_file = "./artifacts/optimized_rf.pkl"
joblib.dump(grid_search, model_file)
```

</td>
<td>

```python
# Create CMF context and execution
metawriter.create_context(
    pipeline_stage="HyperParameterTuning")
metawriter.create_execution(execution_type="HyperPara")

# Log inputs including baseline model
metawriter.log_dataset(cleaned_path, "input", 
                      {'ham': '0', 'spam': '1'})
metawriter.log_dataset(tf_file, "input", 
                      {"max_features": 3000})
metawriter.log_model(baseline_model_file, "input", 
    model_framework="SKlearn", 
    model_type="Classifier")

# Define hyperparameter grid
param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [5, 10, 15],
    'criterion': ['gini', 'entropy']
}

# Perform grid search
grid_search = GridSearchCV(
    estimator=RandomForestClassifier(),
    param_grid=param_grid,
    scoring='accuracy',
    cv=5
)
grid_search.fit(X_train, y_train)

# Evaluate
y_pred = grid_search.best_estimator_.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f'Optimized Accuracy: {accuracy * 100:.2f}%')
print(f'Improvement: {(accuracy - accuracy_baseline) * 100:.2f}%')

# Save and log optimized model
model_file = "./artifacts/optimized_rf.pkl"
joblib.dump(grid_search, model_file)

metawriter.log_model(
    model_file,
    "output",
    model_framework="SKlearn",
    model_type="Classifier",
    model_name="RandomForestClassifier:GridSearchCV",
    custom_properties=param_grid
)

# Log comprehensive metrics
metawriter.log_execution_metrics(
    metrics_name="optimized_training_metrics",
    custom_properties={
        'accuracy_score': f'{accuracy * 100:.2f}%',
        'baseline_accuracy': f'{accuracy_baseline * 100:.2f}%',
        'improvement': f'{(accuracy - accuracy_baseline) * 100:.2f}%',
        'best_params': str(grid_search.best_params_)
    }
)
```

</td>
</tr>
</table>

**What CMF Adds:**
- ✅ Tracks the baseline model as input to optimization stage
- ✅ Records complete hyperparameter search space
- ✅ Logs comparison metrics (baseline vs optimized)
- ✅ Creates full lineage: baseline model → tuning process → optimized model

---

## Key Benefits of Using CMF

### 1. **Complete Lineage Tracking**

**Without CMF:**
- No record of which dataset version was used
- No link between data, vectorizer, and models
- Cannot trace how models evolved

**With CMF:**
- Full data lineage from raw data → cleaned data → features → models
- Every artifact knows its inputs and outputs
- Can trace any model back to its exact training data

### 2. **Reproducibility**

**Without CMF:**
- Hyperparameters might be scattered in code/notebooks
- No guaranteed record of exact configurations used
- Hard to reproduce specific model versions

**With CMF:**
- All hyperparameters logged as metadata
- Complete record of model configurations
- Can query: "Which model used max_features=3000?"
- Easy to reproduce any past experiment

### 3. **Experiment Comparison**

**Without CMF:**
- Manual tracking in spreadsheets or notebooks
- Easy to lose track of experiment variations
- Difficult to compare metrics across runs

**With CMF:**
- Automatic metric logging per execution
- Query capabilities: "Show all models with accuracy > 95%"
- Compare baseline vs optimized models systematically

### 4. **Pipeline Visibility**

**Without CMF:**
- Pipeline stages exist only in code organization
- No runtime visibility into execution flow
- Hard to debug which stage failed

**With CMF:**
- Explicit pipeline stage contexts
- Execution tracking per stage
- Clear visibility: Prepare → Featurize → Train → Tune

### 5. **Collaboration & Governance**

**Without CMF:**
- Team members may not know which models were tried
- No centralized metadata repository
- Difficult to audit ML workflows

**With CMF:**
- Centralized metadata store (MLMD)
- Team can query and discover past experiments
- Audit trail: who ran what, when, with which data
- Enables ML governance and compliance

### 6. **Model Registry Capabilities**

**Without CMF:**
- Models are just files on disk
- No metadata about model characteristics
- Manual tracking of model versions

**With CMF:**
- Models logged with framework, type, and name
- Rich metadata (hyperparameters, metrics, lineage)
- Foundation for model registry and deployment

---

## Summary

| Aspect | Without CMF | With CMF |
|--------|-------------|----------|
| **Code Overhead** | Minimal | +5-10 lines per stage |
| **Lineage Tracking** | ❌ None | ✅ Complete |
| **Reproducibility** | ⚠️ Manual | ✅ Automatic |
| **Experiment Comparison** | ⚠️ Manual | ✅ Queryable |
| **Pipeline Visibility** | ❌ Limited | ✅ Full |
| **Collaboration** | ⚠️ Difficult | ✅ Easy |
| **Governance/Audit** | ❌ None | ✅ Built-in |
| **Learning Curve** | Easy | Moderate |

---

## Try It Yourself

Ready to see the difference in action?

### 🚀 Run the Example

Complete runnable code and setup instructions are available in the [SMS Spam Example](/examples/sms_spam/) directory.

**Quick steps:**
1. Navigate to `examples/sms_spam/`
2. Download the dataset (instructions in README)
3. Run `sms_spam_without_cmf.py` to see the basic pipeline
4. Run `sms_spam_with_cmf.py` to see CMF tracking in action
5. Query the metadata to explore tracked information

See the [SMS Spam Example README](/examples/sms_spam/README.md) for detailed instructions.

---

## Conclusion

CMF adds a lightweight tracking layer that transforms a standard ML workflow into a fully traceable, reproducible, and collaborative pipeline. The small code overhead (5-10 lines per stage) provides significant benefits in terms of lineage, reproducibility, and experiment management - essential for production ML systems.
