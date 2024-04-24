#!/bin/bash

printf "\n[RUNNING PARSE STEP         ]\n"
python src/parse.py artifacts/data.xml.gz artifacts/parsed

