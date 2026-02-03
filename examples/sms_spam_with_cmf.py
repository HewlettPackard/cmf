"""
SMS Spam Classification Pipeline - With CMF Tracking
Complete ML pipeline with CMF metadata tracking at each stage
"""

import joblib
import pandas as pd
import re
from cmflib.cmf import Cmf
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report


# Initialize CMF
metawriter = Cmf(filepath="mlmd", pipeline_name="SmsSpam", graph=False)


# ============================================================================
# STAGE 1: Prepare - Load and clean the dataset
# ============================================================================

# Create CMF context and execution
metawriter.create_context(pipeline_stage="Prepare")
metawriter.create_execution(execution_type="Prep")

# Log and load dataset
path = "artifacts/SMSSpamCollection"
metawriter.log_dataset(path, "input")

df = pd.read_csv(path, sep='\t', names=['label', 'message'])
print("\n------ Original Data -------------\n")
print(df)

# Convert labels to binary
df['label'] = df['label'].map({'ham': 0, 'spam': 1})

# Clean and save data
cleaned_path = "artifacts/cleaned_data.tsv"
df.to_csv(cleaned_path, sep='\t', index=False)

# Log cleaned data
metawriter.log_dataset(cleaned_path, "output", {'ham': '0', 'spam': '1'})

print("\n------ Data after Feature Encoding -------------\n")
print(df)


# ============================================================================
# STAGE 2: Featurize - Extract features using TF-IDF
# ============================================================================

# Create CMF context and execution
metawriter.create_context(pipeline_stage="Featurize")
metawriter.create_execution(execution_type="Feat")

# Log input data
metawriter.log_dataset(cleaned_path, "input", {'ham': '0', 'spam': '1'})

# Load and process data
df = pd.read_csv(cleaned_path, sep='\t')

# Feature extraction using TF-IDF
tfidf = TfidfVectorizer(max_features=3000)
tfidf.fit_transform(df['message_cleaned'])

# Save and log TF-IDF vectorizer
tf_file = "./artifacts/tfidf_vectorizer_using_Random_Forest.pkl"
joblib.dump(tfidf, tf_file)
metawriter.log_dataset(tf_file, "output", {"max_features": 3000})


# ============================================================================
# STAGE 3: Train - Train basic Random Forest model
# ============================================================================

# Create CMF context and execution
metawriter.create_context(pipeline_stage="Train")
metawriter.create_execution(execution_type="Trn")

# Log input datasets
metawriter.log_dataset(cleaned_path, "input", {'ham': '0', 'spam': '1'})
metawriter.log_dataset(tf_file, "input", {"max_features": 3000})

# Load data and vectorizer
df = pd.read_csv(cleaned_path, sep='\t')
tfidf = joblib.load(tf_file)

# Transform features
X = tfidf.fit_transform(df['message_cleaned']).toarray()
y = df['label']

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Initialize and train Random Forest model with default parameters
model_config = {'n_estimators': 100, 'max_depth': 10, 'random_state': 42}
model = RandomForestClassifier(**model_config)
model.fit(X_train, y_train)

# Evaluate baseline model
y_pred_baseline = model.predict(X_test)
accuracy_baseline = accuracy_score(y_test, y_pred_baseline)
print(f'Baseline Model Accuracy: {accuracy_baseline * 100:.2f}%')

# Save and log baseline model
baseline_model_file = "./artifacts/baseline_random_forest_spam_classifier.pkl"
joblib.dump(model, baseline_model_file)

metawriter.log_model(
    baseline_model_file,
    "output",
    model_framework="SKlearn",
    model_type="Classifier",
    model_name="RandomForestClassifier:Baseline",
    custom_properties=model_config
)

# Log execution metrics
metawriter.log_execution_metrics(
    metrics_name="baseline_training_metrics",
    custom_properties={'accuracy_score': f'{accuracy_baseline * 100:.2f}%'}
)


# ============================================================================
# STAGE 4: Hyperparameter Tuning - Improve model with GridSearchCV
# ============================================================================

# Create CMF context and execution
metawriter.create_context(pipeline_stage="HyperParameterTuning")
metawriter.create_execution(execution_type="HyperPara")

# Log input datasets and baseline model
metawriter.log_dataset(cleaned_path, "input", {'ham': '0', 'spam': '1'})
metawriter.log_dataset(tf_file, "input", {"max_features": 3000})
metawriter.log_model(baseline_model_file, "input", model_framework="SKlearn", 
                     model_type="Classifier", model_name="RandomForestClassifier:Baseline")

# Use the same data split as before (already split in Stage 3)

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

print("Best Parameters:", grid_search.best_params_)

# Evaluate optimized model
y_pred = grid_search.best_estimator_.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f'Optimized Model Accuracy: {accuracy * 100:.2f}%')
print(f'Improvement: {(accuracy - accuracy_baseline) * 100:.2f}%')

# Save and log optimized model
model_file = "./artifacts/hyper_tuned_random_forest_spam_classifier_using_GridSearchCV.pkl"
joblib.dump(grid_search, model_file)

metawriter.log_model(
    model_file,
    "output",
    model_framework="SKlearn",
    model_type="Classifier",
    model_name="RandomForestClassifier:GridSearchCV",
    custom_properties=param_grid
)

# Log execution metrics
metawriter.log_execution_metrics(
    metrics_name="optimized_training_metrics",
    custom_properties={
        'accuracy_score': f'{accuracy * 100:.2f}%',
        'baseline_accuracy': f'{accuracy_baseline * 100:.2f}%',
        'improvement': f'{(accuracy - accuracy_baseline) * 100:.2f}%',
        'best_params': str(grid_search.best_params_)
    }
)
