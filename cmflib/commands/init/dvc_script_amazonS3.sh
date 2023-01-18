#!/bin/bash

dvc init -q
dvc remote add -d -f amazons3 $1
dvc remote modify amazons3 access_key_id $2
dvc remote modify amazons3 secret_access_key $3
