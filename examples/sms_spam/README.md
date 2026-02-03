# SMS Spam Classification Example

This example demonstrates the difference between a standard ML pipeline and one enhanced with CMF tracking.

A complete SMS spam classification pipeline that:

- Loads and cleans the SMS Spam Collection dataset
- Extracts features using TF-IDF vectorization
- Trains a baseline Random Forest classifier
- Optimizes the model using GridSearchCV

## Files

- `sms_spam_without_cmf.py` - Standard scikit-learn pipeline
- `sms_spam_with_cmf.py` - Same pipeline with CMF tracking
- For detailed comparison, see [docs/examples/sms_spam_comparison.md](/docs/examples/sms_spam_comparison.md)

## Quick Start

### Step 1: Download the Dataset

```bash
# Navigate to this directory
cd examples/sms_spam

# Create artifacts directory
mkdir -p artifacts

# Download and extract the SMS Spam Collection dataset
wget https://archive.ics.uci.edu/ml/machine-learning-databases/00228/smsspamcollection.zip
unzip smsspamcollection.zip -d artifacts/

# Verify the dataset is in place
ls -l artifacts/SMSSpamCollection
```

### Step 2: Setup CMF (Required for Option B)

**Verify CMF Installation:**

```bash
# Check if cmflib is installed
python -c "import cmflib; print(f'CMF version: {cmflib.__version__}')"
```

If you get an error, install CMF:
```bash
# Install from PyPI
pip install cmflib

# OR install from source (if in CMF development environment)
cd ../../  # Navigate to CMF root
pip install -e .
cd examples/sms_spam
```

**Initialize CMF:**

```bash
# Initialize CMF with local metadata store
cmf init local
```

This creates a local metadata store (default file name: `mlmd`) where CMF will track all pipeline metadata.

### Step 3: Run the Pipeline

**Option A: Without CMF (Basic Pipeline)**

```bash
python sms_spam_without_cmf.py
```

This will:

- Load and clean the dataset
- Extract TF-IDF features
- Train a baseline Random Forest model
- Optimize with GridSearchCV
- Save models to `artifacts/` directory

**Option B: With CMF (Tracked Pipeline)**

```bash
python sms_spam_with_cmf.py
```

This will:

- Everything from Option A, PLUS
- Track all datasets and models in metadata store
- Log hyperparameters and metrics
- Create full lineage from data to models
- Enable querying and comparison

## Expected Output

Both scripts will produce:
```
------ Original Data -------------
    label                                            message
0     ham  Go until jurong point, crazy.. Available only ...
1     ham                      Ok lar... Joking wif u oni...
...

Baseline Model Accuracy: 97.xx%
Best Parameters: {'criterion': 'gini', 'max_depth': 10, 'n_estimators': 100}
Optimized Model Accuracy: 98.xx%
Improvement: +x.xx%
```

## Artifacts Generated

After running, the `artifacts/` directory will contain:

```
artifacts/
├── SMSSpamCollection                                    # Input dataset
├── cleaned_data.tsv                                     # Cleaned dataset
├── tfidf_vectorizer_using_Random_Forest.pkl            # TF-IDF vectorizer
├── baseline_random_forest_spam_classifier.pkl          # Baseline model
└── hyper_tuned_random_forest_spam_classifier_using_GridSearchCV.pkl  # Optimized model
```

**With CMF**, you also get:
```
mlmd/                                                    # Metadata store
└── (SQLite database with all tracked metadata)
```

## Learn More

For a detailed comparison of both approaches and the benefits of using CMF, see:
- **[SMS Spam Comparison Guide](/docs/examples/sms_spam_comparison.md)**

## Requirements

```bash
pip install cmflib scikit-learn pandas joblib
```

Or if you're in the CMF development environment:
```bash
pip install -e .
```

## Troubleshooting

**Issue: Dataset not found**
```
FileNotFoundError: artifacts/SMSSpamCollection
```
**Solution:** Make sure you've downloaded the dataset (Step 1)

**Issue: Missing 'message_cleaned' column**
```
KeyError: 'message_cleaned'
```
**Solution:** The example expects basic text cleaning. Add your text preprocessing logic in Stage 1, or use `df['message']` directly.

**Issue: CMF import error**
```
ModuleNotFoundError: No module named 'cmflib'
```
**Solution:** Install CMF: `pip install cmflib` or `pip install -e .` from the root directory

**Issue: CMF not initialized**
```
Error: CMF is not initialized
```
**Solution:** Run `cmf init local` in the current directory (Step 2)
