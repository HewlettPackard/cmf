# Example Machine Learning pipeline with metadata tracking and artifact versioning using CMF.
<p>
In the traditional apporach in CMF, the typical sequence involves the initialization of the Cmf class, the creation of a context (analogous to a stage in Machine Learning), and the creation an execution before logging datasets, models, or metrics. However, CMF provides a streamlined feature wherein users have the flexibility to log datasets, models, and metrics without the explicit requirement ofcreating a context and an execution. This capability simplifies the logging process and enhances the user experience, allowing for more efficient and concise interactions with the framework.
</p>

### Steps to reproduce

1. Copy contents of `nano-cmf` directory to a separate directory outside this repository.

2. Create python virtual environment (version >= 3.7 and < 3.9), install git, install python dependencies.

3. Initialise the project using [`cmf init`](./../../docs/cmf_client/cmf_client_commands.md#cmf-init) command.

4. Execute `sh test_script.sh`. This file mimics a Machine Learning pipeline. It has one stage: 
   [parse](./src/parse.py). It will run the pipeline and will store its pipeline metadata in a sqlite file named mlmd
   
5. Execute [`cmf artifact push`](./../../docs/cmf_client/cmf_client_commands.md#cmf-artifact) command to push artifacts to the artifact repo.

6. Execute [`cmf metadata push`](./../../docs/cmf_client/cmf_client_commands.md#cmf-metadata) command to push metadata to central CMF Server. To start CMF Server, follow the [CMF Server Installation Guide](./../../docs/setup/index.md#install-cmf-server-with-gui).


### Query 
The stored metadata can be explored using the query layer. Example Jupyter notebook 
[Query_Tester-base_mlmd.ipynb](./Query_Tester-base_mlmd.ipynb) can be found in this directory.

### Clean Up 
Metadata is stored in sqlite file named "mlmd". To clean up, delete the "mlmd" file.
