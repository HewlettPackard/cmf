# Using `Cmf` to track metadata for a ML Pipeline

[example-get-started](https://github.com/HewlettPackard/cmf/tree/master/examples/example-get-started) demonstrates how `Cmf` tracks metadata associated with executions of various machine learning (ML)
pipelines. ML pipelines differ from other pipelines (e.g., data Extract-Transform-Load pipelines) by the presence of
ML stages, such as training and testing ML models. 

More comprehensive ML pipelines may include stages such as deploying a
trained model and tracking its inference parameters (such as response latency, memory consumption, etc.).

This [example](https://github.com/HewlettPackard/cmf/tree/master/examples/example-get-started), implements a simple
pipeline consisting of five stages:

- The [parse](https://github.com/HewlettPackard/cmf/blob/master/examples/example-get-started/src/parse.py) stage splits
  the [raw data](https://github.com/HewlettPackard/cmf/tree/master/examples/example-get-started/artifacts) into
  `train` and `test` raw datasets for training and testing a machine learning model. This stage registers one
  input artifact (raw `dataset`) and two output artifacts (train and test `datasets`).
- The [featurize](https://github.com/HewlettPackard/cmf/blob/master/examples/example-get-started/src/featurize.py)
  stage creates two machine learning splits - train and test splits - that will be used by an ML training algorithm to
  train ML models. This stage registers two input artifacts (raw train and test datasets) and two output artifacts (
  train and test ML datasets).
- The next [train](https://github.com/HewlettPackard/cmf/blob/master/examples/example-get-started/src/train.py) stage
  trains an ML model (random forest classifier). It registers one input artifact (the dataset from the previous step)
  and one output artifact (trained ML model).
- The fourth [test](https://github.com/HewlettPackard/cmf/blob/master/examples/example-get-started/src/test.py) stage
  evaluates the performance and execution of the ML model trained in the `train` step. This stage registers two input
  artifacts (ML model and test dataset) and one output artifact (performance metrics).
- The last [query](https://github.com/HewlettPackard/cmf/blob/master/examples/example-get-started/src/query.py) stage
  displays each stage of the pipeline's metadata as retrieved from the `CMF Server`, aggregated over all executions.
  For example, if you rerun the pipeline again, the output will include not only metadata associated with the latest
  run, but also the metadata associated with previous runs.


## Prerequisites 

Before proceeding, ensure that the `cmflib` is installed on your system. If not, follow the installation instructions provided in the [Installation & Setup](../setup/index.md#install-cmf-library-ie-cmflib) page.

The initial setup requires creating a workspace directory that will contain all files for this example, cloning the `cmf` repository that contains source code and data for this example.

```shell
# Create workspace directory
mkdir cmf_example
cd cmf_example

# Clone the CMF project from GitHub and install CMF
git clone https://github.com/HewlettPackard/cmf
```

## Project initialization
First, copy the code and data for this example into its own directory (that must be outside the `cmf` source tree). Execute the `cmf init` command specifying the Data Version Control (dvc) directory, the URL of the git remote, address of the `CMF Server`, and neo4j credentials along with the appropriate dvc backend for this project.

```shell
# Create a separate copy of the example project
cp -r ./cmf/examples/example-get-started/ ./example-get-started
cd ./example-get-started
```
### cmf init
```
Usage: cmf init local [-h] --path [path]
                           --git-remote-url [git_remote_url]
                           --cmf-server-url [cmf_server_url]
                           --neo4j-user [neo4j_user]
                           --neo4j-password [neo4j_password]
                           --neo4j-uri [neo4j_uri]
```
`cmf init local` initializes the local directory as a cmf artifact repository.
```
cmf init local --path /home/XXXX/local-storage
               --git-remote-url https://github.com/user/experiment-repo.git
               --cmf-server-url http://x.x.x.x:80
               --neo4j-user neo4j
               --neo4j-password password
               --neo4j-uri bolt://localhost:7687
```

> For path provide a folder outside the current working directory, which would serve as the artifact repository. eg :-  /home/username/local-storage

Required Arguments
```
  --path [path]                         Specify local directory path.
  --git-remote-url [git_remote_url]     Specify git repo url.
```
Optional Arguments
```
  -h, --help                          show this help message and exit
  --cmf-server-url [cmf_server_url]   Specify CMF Server URL. (default: http://127.0.0.1:80)
  --neo4j-user [neo4j_user]           Specify neo4j user. (default: None)
  --neo4j-password [neo4j_password]   Specify neo4j password. (default: None)
  --neo4j-uri [neo4j_uri]             Specify neo4j uri. Eg bolt://localhost:7687 (default: None)
```
Follow [here](./../cmf_client/cmf_client_commands.md#cmf-init) for more details.

## Project execution
To execute the example pipeline, run the
[test_script.sh](https://github.com/HewlettPackard/cmf/tree/master/examples/example-get-started)
file. In brief, this script runs a sequence of stages typical of machine learning pipelines - getting raw data,
splitting that data into machine learning train/test datasets, training the model, and evaluating a model. The
execution of these steps (and parent pipeline) will be recorded by the `cmf`.
```shell
# Run the example pipeline
sh ./test_script.sh
```

### Setup a `CMF Server` 

> Note: This setup step is not required if the CMF Server is already configured.

**CMF Server** is a key interface for users to explore and track their ML training runs, allowing them to store metadata files on the CMF Server. Users can retrieve saved metadata files and view their content using the UI provided by the CMF Server.

Follow [here](../setup/index.md#install-cmf-server-with-gui) to set up a common CMF Server.

### Syncing metadata on the `CMF Server`
Metadata generated at each step of the pipeline will be stored in a sqlite file named mlmd. Commits in this
repository correspond to the creation of pipeline artifacts and can be viewed with `git log`.

In production settings, the next steps would be to:

1. Execute the `cmf artifact push` command to push the artifacts to the central artifact repository.
2. Execute the `cmf metadata push` command to track the metadata of the generated artifacts on a common [CMF Server](../setup/index.md#install-cmf-server-with-gui).


Follow [cmf artifact](./../cmf_client/cmf_client_commands.md#cmf-artifact) and [cmf metadata](./../cmf_client/cmf_client_commands.md#cmf-metadata) for more details.

## Query
The stored metadata can be explored using the query layer of `cmf`. The Jupyter notebook
[Query_Tester-base_mlmd.ipynb](https://github.com/HewlettPackard/cmf/tree/master/examples/example-get-started) demonstrates this
functionality and can be adapted for your own uses.

## Clean Up
Metadata is stored in a sqlite file named "mlmd". To clean up, delete the "mlmd" file.

## Steps to test dataslice
Run the following command: `python test-data-slice.py`.
