#!/bin/bash

dvc init -f
dvc remote add -d -f local-storage $1
