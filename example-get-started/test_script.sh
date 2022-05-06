#!/bin/bash

printf "\n[1/5] [RUNNING PARSE STEP         ]\n"
python src/parse.py artifacts/data.xml.gz artifacts/parsed

printf "\n[2/5] [RUNNING FEATURIZE STEP     ]\n"
python src/featurize.py artifacts/parsed artifacts/features

printf "\n[3/5] [RUNNING TRAIN STEP         ]\n"
python src/train.py artifacts/features artifacts/model

printf "\n[4/5] [RUNNING TEST STEP          ]\n"
python src/test.py artifacts/model artifacts/features artifacts/test_results

printf "\n[5/5] [RUNNING OPTIONAL QUERY STEP]\n"
python src/query.py mlmd
