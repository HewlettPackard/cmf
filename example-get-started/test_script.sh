#! /bin/bash

python src/prepare.py data/data.xml

python src/featurization.py data/prepared data/features

python src/train.py data/features model.pkl

python src/evaluate.py model.pkl data/features scores.json prc.json roc.json

python src/query.py mlmd
