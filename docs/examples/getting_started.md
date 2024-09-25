# Getting Started

> This example depends on the following packages: `git`. We also recommend installing 
> [anaconda](https://docs.anaconda.com/anaconda/install/linux/) to manage python virtual environments.
> This example was tested in the following environments: 
> 
> - `Ubuntu-22.04 with python-3.10`

This example demonstrates how CMF tracks a metadata associated with executions of various machine learning (ML) 
pipelines. ML pipelines differ from other pipelines (e.g., data Extract-Transform-Load pipelines) by the presence of
ML steps, such as training and testing ML models. More comprehensive ML pipelines may include steps such as deploying a
trained model and tracking its inference parameters (such as response latency, memory consumption etc.). This example, 
located [here](https://github.com/HewlettPackard/cmf/tree/master/examples/example-get-started) implements a simple
pipeline consisting of four steps:

- The [parse](https://github.com/HewlettPackard/cmf/blob/master/examples/example-get-started/src/parse.py) step splits
  the [raw data](https://github.com/HewlettPackard/cmf/tree/master/examples/example-get-started/artifacts) into 
  `train` and `test` raw datasets for training and testing a machine learning model. This step registers one
  input artifact (raw `dataset`) and two output artifacts (train and test `datasets`). 
- The [featurize](https://github.com/HewlettPackard/cmf/blob/master/examples/example-get-started/src/featurize.py)
  step creates two machine learning splits - train and test splits - that will be used by an ML training algorithm to
  train ML models. This step registers two input artifacts (raw train and test datasets) and two output artifacts (
  train and test ML datasets). 
- The next [train](https://github.com/HewlettPackard/cmf/blob/master/examples/example-get-started/src/train.py) step
  trains an ML model (random forest classifier). It registers one input artifact (train ML dataset) and one
  output artifact (trained ML model).
- The fourth [test](https://github.com/HewlettPackard/cmf/blob/master/examples/example-get-started/src/test.py) step
  tests the ML model trained in the third `train` step. This step registers two input artifacts (ML model and test
  dataset) and one output artifact (performance metrics).
- The last [query](https://github.com/HewlettPackard/cmf/blob/master/examples/example-get-started/src/query.py) step
  is a demonstration that shows how pipeline metadata can be retrieved from CMF. It will print metadata associated with
  all executions of the above steps. This means that if you rerun the pipeline again, the output will include not only
  metadata associated with the last run, but also metadata associated with all previous runs.


## Pre-requisites

We start by creating (1) a workspace directory that will contain all files for this example and (2) a python virtual 
environment. Then we will clone the CMF project that contains this example project.
```shell
# Create workspace directory
mkdir cmf_getting_started_example
cd cmf_getting_started_example

# Create and activate Python virtual environment (the Python version may need to be adjusted depending on your system)
conda create -n cmf_getting_started_example python=3.10 
conda activate cmf_getting_started_example

# Clone the CMF project from GitHub and install CMF
git clone https://github.com/HewlettPackard/cmf
pip install ./cmf
```

### Setup a cmf-server

__cmf-server__ is a key interface for the user to explore and track their ML training runs. It allows users to store the metadata file on the cmf-server. The user can retrieve the saved metadata file and can view the content of the saved metadata file using the UI provided by the cmf-server.

Follow [here](./../cmf_server/cmf-server.md) to setup a common cmf-server.

## Project initialization
We need to copy the source tree of the example in its own directory (that must be outside the CMF source tree), and using `cmf init` command
initialize dvc remote directory, git remote url, cmf server and neo4j with appropriate dvc backend for this project .

```shell
# Create a separate copy of the example project
cp -r ./cmf/examples/example-get-started/ ./example-get-started
cd ./example-get-started
```
### cmf init
<pre>
Usage: cmf init local [-h] --path [path] -
                           --git-remote-url [git_remote_url]
                           --cmf-server-url [cmf_server_url]
                           --neo4j-user [neo4j_user]
                           --neo4j-password [neo4j_password]
                           --neo4j-uri [neo4j_uri]
</pre>
`cmf init local` initialises local directory as a cmf artifact repository.
```
cmf init local --path /home/XXXX/local-storage --git-remote-url https://github.com/user/experiment-repo.git --cmf-server-url http://x.x.x.x:8080 --neo4j-user neo4j --neo4j-password password --neo4j-uri bolt://localhost:7687
```

> Replace 'XXXX' with your system username in the following path: /home/XXXX/local-storage

Required Arguments
```
  --path [path]                         Specify local directory path.
  --git-remote-url [git_remote_url]     Specify git repo url.
```
Optional Arguments
```
  -h, --help                          show this help message and exit
  --cmf-server-url [cmf_server_url]   Specify cmf-server url. (default: http://127.0.0.1:80)
  --neo4j-user [neo4j_user]           Specify neo4j user. (default: None)
  --neo4j-password [neo4j_password]   Specify neo4j password. (default: None)
  --neo4j-uri [neo4j_uri]             Specify neo4j uri. Eg bolt://localhost:7687 (default: None)
```
Follow [here](./../cmf_client/cmf_client.md#cmf-init) for more details.

## Project execution
To execute the example pipeline, run the 
[test_script.sh](../../examples/example-get-started/test_script.sh) 
file (before that, study the contents of that file). Basically, that script will run a sequence of steps
common for a typical machine learning project - getting raw data, converting it into machine learning train/test splits,
training and testing a model. The execution of these steps (and parent pipeline) will be recorded by the CMF.
```shell
# Run the example pipeline
sh ./test_script.sh
```

This script will run the pipeline and will store its metadata in a sqlite file named mlmd. Verify that all stages are 
done using `git log` command. You should see commits corresponding to the artifacts that were created.

Under normal conditions, the next steps would be to: (1) execute the `cmf artifact push` command to push the artifacts to the central artifact repository and (2) execute the `cmf metadata push` command to track the metadata of the generated artifacts on a common [cmf server](./../cmf_server/cmf-server.md).

Follow [here](./../cmf_client/cmf_client.md#cmf-init) for more details on `cmf artifact` and `cmf metadata` commands.


## Query 
The stored metadata can be explored using the query layer. Example Jupyter notebook 
[Query_Tester-base_mlmd.ipynb](../../examples/example-get-started/Query_Tester-base_mlmd.ipynb) can be found in this directory.

## Clean Up 
Metadata is stored in sqlite file named "mlmd". To clean up, delete the "mlmd" file.
 
## Steps to test dataslice
Run the following command: `python test-data-slice.py`.
