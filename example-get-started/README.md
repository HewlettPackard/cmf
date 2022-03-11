
### Steps to reproduce

1. Copy contents of this directory to a separate directory outside this repo.

2. Modify the sample_env file with appropriate values for the exports.

3. Execute - 'source sample_env'

4. Execute - 'sh initialize.sh'

   This will perform the initialization for the directory. This will init a git repo, dvc repo and add a git remote and dvc remote.

5. Execute 'sh test_script.sh'

   This file mimics an ml pipeline. It has the following stages - Prepare, Featurize, Train, Evaluate.

   This should run the pipeline and store its metadata in a sqlite file mlmd.

   Verify that all stages are done using "git log" command.

   You should see commits corresponding to the artifacts that was created.
   
6. Execute "dvc push" to push the artifacts to dvc remote

7. To track the metadata of the artifacts, push the metdata files to git.

    git push origin


### Query 
The stored metadata can be explored using the query layer. Example notebook Query_Tester-base_mlmd.ipynb can be found in this directory.

### Clean Up 
Metadata is stores in sqlite file named "mlmd". To clean up, delete the "mlmd" file.
 
### Steps to test dataslice
python test-data-slice.py
