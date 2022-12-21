# Get started with CMF
***

<font size=5>This section shows end-to-end use of CMF setup. It starts with installation, 
shows how to collect and track information associated with the ML pipeline. 
It guides us on how artifacts and metadata can be handled and stored. 
Also, it shows the use of various repositories for managing artifacts.
With this, CMF provides various APIs through which we can visualize ML parameters.

For details of the commands that will be used below, visit [Detail documentation of CMF commands](cmf_client.md) #Pending(example user1(push) and user2(pull) )  </font>

# Pre-Requisite 

- <font size=5>Python 3.8+ </font >

- <font size=5>cmflib </font >

- <font size=5>Git latest version </font >

- <font size=5>Virtualenv ?</font >
- #pending

Before starting both the users will have to initiate the following steps

#  Installing cmflib
   is mkdir to be added#pending
1. Clone the repository with the following command.

 `git clone #Pending`

2. Redirect to the `cmf folder` and create a virtual environment by running the following command.
<pre>virtualenv env_name</pre>

3. Activate virtual env `env_name` created
<pre>source env_name/bin/activate</pre>

4. Install the library

 Creating the wheel file

```
python setup.py bdist_wheel
cd dist
pip install <cmflib-0.0.1-py2-none-any.whl>

```
or Install directly,
pip install  .

## How it works?
Use case1. 

So to understand the features and process of CMF we will consider two Users. 
User1 has some artifacts and mlmd files which he/she got by running their ML pipeline.
Now if user1 wants to store the data he has 4 repositories available for artifacts and cmf-server for mlmd files.
He/She has to follow the below steps.

##  Initializing various repos

CMF repository is a place where all the artifacts are stored and retrieved from. This will initialize a git repo, and a dvc repo and will add a git remote and dvc remote. 
There are 4 different types of repository local directories, Minio S3 bucket, Amazon S3 bucket and SSH Remote.
For more details [cmf init ](cmf_client.md)


1. Copy contents of the `example-get-started` directory to a separate directory outside this repository.


2. First check whether the current directory is already initialized.
<pre>cmf init show</pre>


You should see something like this on your command line.

<pre>
'cmf' is not configured.
Execute the 'cmf init' command.
</pre>

3.  Now we'll see how to initialize different repos.

      Note: After initializing the MinioS3 repository, first you need to start the minios3 server for this visit. #Pending(link )


| Repo      | Commands to initialize                                                                                                                                                                       |
|-----------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| minioS3   | cmf init minioS3 --url s3://bucket-name --endpoint-url http://localhost:9000 --access-key-id minioadmin --secret-key minioadmin --git-remote-url https://github.com/user/experiment-repo.git |
| amazonS3  | cmf init amazonS3 --url s3://bucket-name --access-key-id XXXXXXXXXXXXX --secret-key XXXXXXXXXXXXX --git-remote-url https://github.com/user/experiment-repo.git                               |
| local     | cmf init local --path /home/user/local-storage --git-remote-url https://github.com/user/experiment-repo.git                                                                                  |
| sshremote | cmf init sshremote --path ssh://127.0.0.1/home/user/ssh-storage --user XXXXX --port 22 --password example@123 --git-remote-url https://github.com/user/experiment-repo.git                   |

Your workspace is now ready for tracking ML metadata with CMF.

4. Execute:  ML Pipeline. This step will run a Machine Learning pipeline and will store its pipeline metadata 
   in an SQLite file named mlmd #PENDING. Then this mlmd file will be used to get artifacts linked to that pipeline.

##  Pushing artifacts to repo initialized and mlmd file to cmf-server. #Pending

1. Execute `cmf artifact push`. This will push all the artifacts to the repo initialized.

   You need to activate the cmf-server before running the metadata command. [Documentation to start cmf-server](cmf-server.md)

1. Execute `cmf metadata push -p [pipeline_name] -f [mlmd_file_path]`. This step will push the mlmd file to the cmf-server.

Use case 2.

Let's consider User2 wants to get those artifacts and the mlmd file.

1. First check whether the current directory is already initialized.
<pre>cmf init show</pre>


You should see something like this on your command line.

<pre>
'cmf' is not configured.
Execute the 'cmf init' command.
</pre>

2. Now user needs to initialize that repo from where artifacts are to be pulled.

Note: To initialize the MinioS3 repository, first you need to start the minios3 server for this visit #Pending Do we need this here as its pulling (link )

| Repo      | Commands to initialize                                                                                                                                                                       |
|-----------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| minioS3   | cmf init minioS3 --url s3://bucket-name --endpoint-url http://localhost:9000 --access-key-id minioadmin --secret-key minioadmin --git-remote-url https://github.com/user/experiment-repo.git |
| amazonS3  | cmf init amazonS3 --url s3://bucket-name --access-key-id XXXXXXXXXXXXX --secret-key XXXXXXXXXXXXX --git-remote-url https://github.com/user/experiment-repo.git                               |
| local     | cmf init local --path /home/user/local-storage --git-remote-url https://github.com/user/experiment-repo.git                                                                                  |
| sshremote | cmf init sshremote --path ssh://127.0.0.1/home/user/ssh-storage --user XXXXX --port 22 --password example@123 --git-remote-url https://github.com/user/experiment-repo.git                   |

Your workspace is now ready for retrieving artifacts with CMF.


##  Pulling artifacts from repo initialized and mlmd file from cmf-server. #Pending

1. Execute `cmf metadata pull -p [pipeline_name] -f [mlmd_file_path]`. This step will pull the mlmd file from the cmf-server.


2. Execute `cmf artifact pull -p [pipeline_name]`. This step will fetch artifact names from mlmd and will download them from the initialized repo.


You need to activate the cmf-server before running the metadata command. To activate [Documentation to start cmf-server](cmf-server.md)
#PENDING do we need this.