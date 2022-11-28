#!/bin/bash

git init
dvc init -f -q
dvc remote add -d -f local-storage $1
