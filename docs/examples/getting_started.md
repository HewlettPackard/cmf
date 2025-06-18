# Getting Started

## Overview
This example demonstrates how CMF tracks metadata associated with a machine learning (ML) pipeline. ML pipelines
differ from other pipelines (e.g., data Extract-Transform-Load pipelines) by the inclusion of ML-specific steps,
such as training and testing ML models which may have metrics associated with their execution. More comprehensive
ML pipelines may include steps such as deploying a trained model and tracking its performance metrics (such as
response latency, memory consumption etc.).

This example trains a binary classifier (using a random forest architecture) on posts from Stack Overflow to identify
whether the content is related to Python. The code and data are located
[here](https://github.com/HewlettPackard/cmf/tree/master/examples/example-get-started).  The pipeline here consists
of four steps described below:

- The [parse](https://github.com/HewlettPackard/cmf/blob/master/examples/example-get-started/src/parse.py) reads in
  the raw XML file representing scraped Stack Overflow posts and extracts the post ID, the text of the post, and a
  label representing whether the post was tagged `python`. These are split into `train` and `test` datasets (as is
  typical of machine learning training) and saved as tab-separated text files. In this step, calls to CMF register
  one input artifact (the original `dataset`) and two output artifacts (parsed `train` and `test` `datasets`).
- The [featurize](https://github.com/HewlettPackard/cmf/blob/master/examples/example-get-started/src/featurize.py)
  step transforms the raw data by applying widely-used natural language processing techniques (tokenization and
  calculating term frequency-inverse document frequency) into features ingestible by the RFC. CMF is called during
  this step to register two input artifacts (the parsed `train` and `test` datasets) and two output artifacts (the
  transformed `train` and `test` datasets).
- The next [train](https://github.com/HewlettPackard/cmf/blob/master/examples/example-get-started/src/train.py) step
  trains the Random forest classifier (RFC) itself and saves the model. It registers one input artifact (the transformed `train`) and one output
  artifact (the trained ML model).
- The fourth [test](https://github.com/HewlettPackard/cmf/blob/master/examples/example-get-started/src/test.py) step
  evaluates the ML model trained in the third `train` step against the training dataset itself. This is done by
  computing the receiver operating (ROC) and precision recall (PRC) curves. Metrics derived from these curves are
  stored in JSON files. Calls to CMF register the two input artifacts (the trained ML model and the transformed
  `train` dataset) and two output artifacts (the ROC and PRC JSON files).
- The last [query](https://github.com/HewlettPackard/cmf/blob/master/examples/example-get-started/src/query.py) step
  demonstrates how the pipeline's metadata can be retrieved from CMF. Note that CMF distinguishes metadata between
  multiple executions of the same pipeline. For example if you rerun the pipeline again, the output will include not only
  metadata associated with the last run, but also metadata associated with the original execution.

## Environment dependencies
This example can be run in most Linux environments which have `git` installed and Python. We highly recommend using
a python virtual environment e.g. pyenv or venv. Here we assume that the user already has python 3.10 installed.

## Pre-requisites
We start by creating (1) a workspace directory that will contain all files for this example and (2) a python virtual
environment. Then we will clone the CMF project that contains this example project.
```shell
# Create workspace directory
mkdir cmf_getting_started_example
cd cmf_getting_started_example

# Create and activate Python virtual environment (the Python version may need to be adjusted depending on your system)
python -m venv cmf/
source cmf/bin/activate

# Clone the CMF project from GitHub and install CMF
git clone https://github.com/HewlettPackard/cmf
pip install ./cmf
pip install -r ./cmf/examples/example-get-started/requirements.txt
```

### Setup a cmf-server

__cmf-server__ is the primary interface for the user to explore and track their ML
training runs allowing users to store the metadata file on the cmf-server. The user
can retrieve the saved metadata file and can view the content of the saved metadata file
using the UI provided by the cmf-server.

Follow [here](./../cmf_server/cmf-server.md) to setup a common cmf-server.

## Project initialization
We need to copy the source tree of the example into its own directory (that must be
outside the CMF source tree), and using `cmf init` command to initialize the dvc remote
directory, git remote url, cmf server, and configure neo4j with appropriate dvc backend
for this project .

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
cmf init local --path /home/XXXX/local-storage \
               --git-remote-url https://github.com/user/experiment-repo.git \
               --cmf-server-url http://x.x.x.x:8080 \
               --neo4j-user neo4j --neo4j-password password \
               --neo4j-uri bolt://localhost:7687
```

> Replace 'XXXX' with your system username in the following path: /home/XXXX/local-storage and x.x.x.x
> the address of the CMF server

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
[test_script.sh](../../examples/example-get-started/test_script.sh) file. Basically, that script will run the sequence of steps
described in the Overview section above.
```shell
# Run the example pipeline
sh ./test_script.sh
```

This script will run the pipeline and store its metadata in a sqlite file named `mlmd`. You can verify the execution by running the `git log` command. Note that, unlike previous versions, a commit is no longer created for every artifact. Instead, a single commit is made at the start and another at the end of the pipeline execution. When a dataset is logged, it is staged with `git add`, but the commit occurs only at the end.

In typical production environments, the next steps would be to: (1) execute the `cmf artifact push` command to push the artifacts to the central artifact repository and (2) execute the `cmf metadata push` command to integrate the metadata of the generated artifacts on a common [cmf server](./../cmf_server/cmf-server.md).

Follow [here](./../cmf_client/cmf_client.md#cmf-init) for more details on `cmf artifact` and `cmf metadata` commands.


## Query
The stored metadata can be explored using the query layer. An example Jupyter notebook
[Query_Tester-base_mlmd.ipynb](../../examples/example-get-started/Query_Tester-base_mlmd.ipynb) can be found in this directory.

## Clean Up
Metadata is stored in sqlite file named "mlmd". To clean up, delete the "mlmd" file.

## Steps to test dataslice
AES: What does this mean? Is this germaine to this example or is it a more advanced feature that could be split into its own example (or a followon to this one)?
Run the following command: `python test-data-slice.py`.
