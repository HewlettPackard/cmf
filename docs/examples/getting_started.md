# Getting Started

## Steps to reproduce

Copy contents of
[example-get-started](https://github.com/HewlettPackard/cmf/tree/master/examples/example-get-started) directory to a 
separate directory outside the project root repository.


Create python virtual environment (version >= 3.6 and < 3.9), install git, install python dependencies

Modify the [sample_env](https://github.com/HewlettPackard/cmf/blob/master/examples/example-get-started/sample_env) 
file with appropriate values for the exports.

Execute: `source sample_env`. This scrip will export several environment variables used in 
[initialize.sh](https://github.com/HewlettPackard/cmf/blob/master/examples/example-get-started/initialize.sh) script.

Execute: `sh initialize.sh`. This step will perform the initialization for the directory. This will init a git repo,
dvc repo and add a git remote and dvc remote.

Execute `sh test_script.sh`. This file mimics a Machine Learning pipeline. It has the following stages: 
[parse](./src/parse.py), 
[featurize](./src/featurize.py), 
[train](./src/train.py) and 
[test](./src/test.py). 
It will run the pipeline and will store its pipeline metadata in a sqlite file named mlmd. Verify that all stages are done 
using "git log" command. You should see commits corresponding to the artifacts that was created.
   
Execute `dvc push` to push the artifacts to dvc remote.

To track the metadata of the artifacts, push the metadata files to git: `git push origin`.


## Query 
The stored metadata can be explored using the query layer. Example Jupyter notebook 
[Query_Tester-base_mlmd.ipynb](./Query_Tester-base_mlmd.ipynb) can be found in this directory.

## Clean Up 
Metadata is stored in sqlite file named "mlmd". To clean up, delete the "mlmd" file.
 
## Steps to test dataslice
Run the following command: `python test-data-slice.py`.
