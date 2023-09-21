# Jupyter Notebook

This folder contains two files:
- training_cmf_push.ipynb
- training_cmf_pull.ipynb

## 1. training_cmf_push.ipynb
This file shows how user can push the metadata and artifacts to the CMF-server using CMF commands.
Following are the steps:

1. Checking if the repositories are initialized.
2. Initializing repositories(local,minioS3,amazonS3,sshremote) so that to push artifacts to initialized repository. 
3. Running multiple stages to create metadata using CMF API's.
4. Pushing this metadata to CMF-server.
5. Pushing artifacts to initialized repositories.

<b>Note: Executions and artifacts after pushing can be analyzed on server(http://url:3000).

## 2. training_cmf_pull.ipynb
This file shows how to pull metadata from CMF-server and download artifacts from initialized repository to local.  
Following are the steps:

1. Checking if the repositories are initialized.
2. Initializing repositories(local,minioS3,amazonS3,sshremote) so that to push artifacts to initialized repository. 
3. Pulling metadata from CMF-server to local.
4. Pulling artifacts from initialized repositories.


