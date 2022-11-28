#!/bin/bash

git init
dvc init -f -q
dvc remote add -d -f ssh-storage $1
dvc remote modify ssh-storage user $2
dvc remote modify ssh-storage port $3
dvc remote modify ssh-storage password $4
