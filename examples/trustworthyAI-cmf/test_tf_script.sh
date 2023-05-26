#!/bin/bash

printf "\n[1/3] [RUNNING FAIRNESS COMPUTATION STEPS BEFORE REWINGING...]\n"
ipython src/gender-classification-cmf-aif-before-rewing.py

printf "\n[2/3] [RUNNING FAIRNESS COMPUTATION STEPS AFTER REWINGING...]\n"
python -W ignore  src/gender-classification-cmf-aif-after-rewing.py


printf "\n[3/3] [RUNNING FAIRNESS COMPUTATION STEPS AFTER  adversarial learning...]\n"
python -W ignore  src/gender-classification-cmf-aif-after-debiasing.py

printf "\n[final simple CNN + Analysis.....]\n"
python -W ignore src/Trustworthy_gender_classification_analysis.py
