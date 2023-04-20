#!/bin/bash

printf "\n[1/2] [RUNNING FAIRNESS COMPUTATION STEPS BEFORE REWINGING...]\n"
python -W ignore  src/gender-classification-cmf-aif-before-rewing.py

printf "\n[2/2] [RUNNING FAIRNESS COMPUTATION STEPS BEFORE REWINGING...]\n"
python -W ignore  src/gender-classification-cmf-aif-after-rewing.py
