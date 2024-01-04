# Example Machine Learning pipeline with metadata tracking and artifact versioning using CMF.

### Steps to reproduce

1. Copy contents of `example-get-started` directory to a separate directory outside this repository.

2. Create python virtual environment (version >= 3.6 and < 3.9), install git, install python dependencies

3. Modify the [sample_env](./sample_env) file with appropriate values for the exports.

4. Execute: `source sample_env`. This scrip will export several environment variables used in 
   [initialize.sh](./initialize.sh) script.

5. Execute: `sh initialize.sh`. This step will perform the initialization for the directory. This will init a git repo,
   dvc repo and add a git remote and dvc remote.

6. Execute `sh test_script.sh`. This file mimics a Machine Learning pipeline. It has the following stages: 
   [parse](./src/parse.py), [featurize](./src/featurize.py), [train](./src/train.py) and [test](./src/test.py). It will
   run the pipeline and will store its pipeline metadata in a sqlite file named mlmd. Verify that all stages are done 
   using "git log" command. You should see commits corresponding to the artifacts that was created.
   
7. Execute `dvc push` to push the artifacts to dvc remote.

8. To track the metadata of the artifacts, push the metadata files to git: `git push origin`.


### Query 
The stored metadata can be explored using the query layer. Example Jupyter notebook 
[Query_Tester-base_mlmd.ipynb](./Query_Tester-base_mlmd.ipynb) can be found in this directory.

### Clean Up 
Metadata is stored in sqlite file named "mlmd". To clean up, delete the "mlmd" file.
 
### Steps to test dataslice
Run the following command: `python test-data-slice.py`.
