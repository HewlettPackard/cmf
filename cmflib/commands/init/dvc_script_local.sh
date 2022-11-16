#!/bin/bash

dvc init -f
dvc remote add -d -f myremote $1
