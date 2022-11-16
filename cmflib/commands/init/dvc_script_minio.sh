#!/bin/bash

dvc init -f
dvc remote add -d -f minio $1
dvc remote modify minio endpointurl $2
dvc remote modify minio access_key_id $3
dvc remote modify minio secret_access_key $4
