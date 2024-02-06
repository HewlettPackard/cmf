# Example Machine Learning pipeline with metadata tracking and artifact versioning using CMF.

### Steps to reproduce

1. Copy contents of `` directory to a separate directory outside this repository.

2. Create python virtual environment (version >= 3.7 and < 3.9), install git, install python dependencies

3. Initialise the project using [`cmf init`](./../../docs/cmf_client/cmf_client.md#cmf-init) command.

4. Execute `sh test_script.sh`. This file mimics a Machine Learning pipeline. It has one stage: 
   [parse](./src/parse.py). It will run the pipeline and will store its pipeline metadata in a sqlite file named mlmd
   
5. Execute [`cmf artifact push`](./../../docs/cmf_client/cmf_client.md#cmf-artifact) command to push artifacts to the artifact repo.

6. Execute [`cmf metadata push`](./../../docs/cmf_client/cmf_client.md#cmf-metadata) command to push metadata to central cmf server. To start cmf-server, use [cmf-server.md](./../../docs/cmf_server/cmf-server.md).


### Query 
The stored metadata can be explored using the query layer. Example Jupyter notebook 
[Query_Tester-base_mlmd.ipynb](./Query_Tester-base_mlmd.ipynb) can be found in this directory.

### Clean Up 
Metadata is stored in sqlite file named "mlmd". To clean up, delete the "mlmd" file.
