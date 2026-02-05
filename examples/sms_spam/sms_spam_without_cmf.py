"""
SMS Spam Classification Pipeline - Without CMF
A complete ML pipeline for spam detection using Random Forest
"""

import joblib
import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report


# ============================================================================
# STAGE 1: Prepare - Load and clean the dataset
# ============================================================================

# Load dataset
path = "artifacts/SMSSpamCollection"
df = pd.read_csv(path, sep='\t', names=['label', 'message'])

print("\n------ Original Data -------------\n")
print(df)

# Convert labels to binary (0 for ham, 1 for spam)
df['label'] = df['label'].map({'ham': 0, 'spam': 1})

# Clean the data (text preprocessing)
# Add your cleaning logic here and save
cleaned_path = "artifacts/cleaned_data.tsv"
df.to_csv(cleaned_path, sep='\t', index=False)

print("\n------ Data after Feature Encoding -------------\n")
print(df)


# ============================================================================
# STAGE 2: Featurize - Extract features using TF-IDF
# ============================================================================

# Load cleaned data
df = pd.read_csv(cleaned_path, sep='\t')

# Feature extraction using TF-IDF
tfidf = TfidfVectorizer(max_features=3000)
tfidf.fit_transform(df['message_cleaned'])

# Save TF-IDF vectorizer
tf_file = "./artifacts/tfidf_vectorizer_using_Random_Forest.pkl"
joblib.dump(tfidf, tf_file)


# ============================================================================
# STAGE 3: Train - Train basic Random Forest model
# ============================================================================

# Load data and vectorizer
df = pd.read_csv(cleaned_path, sep='\t')
tfidf = joblib.load(tf_file)

# Transform data
X = tfidf.fit_transform(df['message_cleaned']).toarray()
y = df['label']

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Initialize and train Random Forest model with default parameters
model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
model.fit(X_train, y_train)

# Evaluate baseline model
y_pred_baseline = model.predict(X_test)
accuracy_baseline = accuracy_score(y_test, y_pred_baseline)
print(f'Baseline Model Accuracy: {accuracy_baseline * 100:.2f}%')

# Save baseline model
baseline_model_file = "./artifacts/baseline_random_forest_spam_classifier.pkl"
joblib.dump(model, baseline_model_file)


# ============================================================================
# STAGE 4: Hyperparameter Tuning - Improve model with GridSearchCV
# ============================================================================

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

# Fit and find best model
grid_search.fit(X_train, y_train)

print("Best Parameters:", grid_search.best_params_)

# Evaluate optimized model
y_pred = grid_search.best_estimator_.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f'Optimized Model Accuracy: {accuracy * 100:.2f}%')
print(f'Improvement: {(accuracy - accuracy_baseline) * 100:.2f}%')

# Save optimized model
model_file = "./artifacts/hyper_tuned_random_forest_spam_classifier_using_GridSearchCV.pkl"
joblib.dump(grid_search, model_file)
