# Example Machine Learning pipeline with metadata tracking and artifact versioning using CMF.

See [Getting Started Tutorial](./../../docs/examples/getting_started.md) page for an in-depth walkthrough of the example.

### Steps to reproduce

1. Before proceeding, ensure that the CMF library is installed on your system. If not, follow the installation instructions provided in the [Installation & Setup](./../../docs/setup/index.md) page.

2. Copy contents of `example-get-started` directory to a separate directory outside this repository.

3. Initialise the project using [`cmf init`](./../../docs/cmf_client/cmf_client.md#cmf-init) command.

4. Execute `sh test_script.sh`. This file mimics a Machine Learning pipeline. It has the following stages: 
   [parse](./src/parse.py), [featurize](./src/featurize.py), [train](./src/train.py) and [test](./src/test.py). It will
   run the pipeline and will store its pipeline metadata in a sqlite file named mlmd. Verify that all stages are done 
   using "git log" command. You should see commits corresponding to the artifacts that was created.

5. Execute [`cmf artifact push`](./../../docs/cmf_client/cmf_client.md#cmf-artifact) command to push artifacts to the artifact repo.

6. Execute [`cmf metadata push`](./../../docs/cmf_client/cmf_client.md#cmf-metadata) command to push metadata to central cmf server. To start cmf-server, use [cmf-server.md](./../../docs/cmf_server/cmf-server.md).
   
### Query 
The stored metadata can be explored using the query layer. Example Jupyter notebook 
[Query_Tester-base_mlmd.ipynb](./Query_Tester-base_mlmd.ipynb) can be found in this directory.

### Clean Up 
Metadata is stored in sqlite file named "mlmd". To clean up, delete the "mlmd" file.
 
### Steps to test dataslice
Run the following command: `python test-data-slice.py`.
