#!/bin/bash

dvc init -q
dvc remote add -d -f local-storage $1
