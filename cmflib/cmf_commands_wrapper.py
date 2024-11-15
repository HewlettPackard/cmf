###
# Copyright (2023) Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###

from cmflib import cli


def metadata_push(pipeline_name: str, filepath = "./mlmd", tensorboard_path: str = "", execution_id: str = ""):
    """ Pushes MLMD file to CMF-server.
    Example:
    ```python
         result = metadata_push("example_pipeline", "mlmd_file", "3")
    ```
    Args:
        pipeline_name: Name of the pipeline.
        filepath: Path to the MLMD file.
        tensorboard_path: Path to tensorboard logs.
        execution_id: Optional execution ID.

    Returns:
        Pending
    """
    # Required arguments:  pipeline_name
    # Optional arguments: Execution_ID, filepath (mlmd file path, tensorboard_path)
    cli_args = cli.parse_args(
            [
               "metadata",
               "push",
               "-p",
               pipeline_name,
               "-f",
               filepath,
               "-e",
               execution_id,
               "-t",
               tensorboard_path
            ]
           )
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    print(msg)
    return msg


def metadata_pull(pipeline_name: str, filepath = "./mlmd", execution_id: str = ""):
    """ Pulls MLMD file from CMF-server. 
     Example: 
     ```python 
          result = metadata_pull("example_pipeline", "./mlmd_directory", "execution_123") 
     ``` 
     Args: 
        pipeline_name: Name of the pipeline. 
        filepath: File path to store the MLMD file. 
        execution_id: Optional execution ID. 
     Returns: 
        Pending
     """
    # Required arguments:  pipeline_name 
    #Optional arguments: Execution_ID, filepath(file path to store mlmd file) 
    cli_args = cli.parse_args(
         [
            "metadata",
            "pull",
            "-p",
            pipeline_name,
            "-f",
            filepath,
            "-e",
            execution_id,
         ]
         )
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    print(msg)
    # i don't understand why we are both printing and returning the output
    return msg

def metadata_export(pipeline_name: str, jsonfilepath: str = "", filepath = "./mlmd"):
    """ Export local mlmd's metadata in json format to a json file. 
     Example: 
     ```python 
          result = metadata_pull("example_pipeline", "./jsonfile", "./mlmd_directory") 
     ``` 
     Args: 
        pipeline_name: Name of the pipeline. 
        jsonfilepath: File path of json file. 
        filepath: File path to store the MLMD file. 
     Returns: 
        Pending 
     """
    # Required arguments:  pipeline_name 
    #Optional arguments: jsonfilepath, filepath(file path to store mlmd file) 
    cli_args = cli.parse_args(
         [
            "metadata",
            "export",
            "-p",
            pipeline_name,
            "-j",
            jsonfilepath,
            "-f",
            filepath,
         ]
         )
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    print(msg)
    return msg

def artifact_pull(pipeline_name: str, filepath = "./mlmd"):
    """ Pulls artifacts from the initialized repository.

    Example:
    ```python
         result = artifact_pull("example_pipeline", "./mlmd_directory")
    ```

    Args:
        pipeline_name: Name of the pipeline.
        filepath: Path to store artifacts.
    Returns:
        Pending
    """

    # Required arguments: Pipeline_name
    # Optional arguments: filepath( path to store artifacts)
    cli_args = cli.parse_args(
            [
               "artifact",
               "pull",
               "-p",
               pipeline_name,
               "-f",
               filepath,
            ]
           )
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    print(msg)
    return msg


def artifact_pull_single(pipeline_name: str, filepath: str, artifact_name: str):
    """ Pulls a single artifact from the initialized repository. 
    Example: 
    ```python 
        result = artifact_pull_single("example_pipeline", "./mlmd_directory", "example_artifact") 
    ```
    Args: 
       pipeline_name: Name of the pipeline. 
       filepath: Path to store the artifact. 
       artifact_name: Name of the artifact. 
    Returns:
       Pending 
    """
    # Required arguments: Pipeline_name
    # Optional arguments: filepath( path to store artifacts), artifact_name
    cli_args = cli.parse_args(
            [
               "artifact",
               "pull",
               "-p",
               pipeline_name,
               "-f",
               filepath,
               "-a",
               artifact_name,
            ]
           )
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    print(msg)
    return msg


def artifact_push(pipeline_name: str, filepath = "./mlmd"):
    """ Pushes artifacts to the initialized repository.

    Example:
    ```python
         result = artifact_push("example_pipeline", "./mlmd_directory")
    ```
    Args: 
       pipeline_name: Name of the pipeline. 
       filepath: Path to store the artifact. 
    Returns:
        Pending
    """
    cli_args = cli.parse_args(
            [
               "artifact",
               "push",
               "-p",
               pipeline_name,
               "-f",
               filepath,
            ]
           )
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    print(msg)
    return msg


def cmf_init_show():
    """ Initializes and shows details of the CMF command. 
    Example: 
    ```python 
         result = cmf_init_show() 
    ``` 
    Returns: 
       Pending
    """
    cli_args = cli.parse_args(
            [
               "init",
               "show"
            ]
           )
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    print(msg)
    return msg


def cmf_init(type: str = "",
        path: str = "",
        git_remote_url: str = "",
        cmf_server_url: str = "",
        neo4j_user: str = "",
        neo4j_password: str = "",
        neo4j_uri: str = "",
        url: str = "",
        endpoint_url: str = "",
        access_key_id: str = "",
        secret_key: str = "",
        session_token: str = "",
        user: str = "",
        password: str = "",
        port: int = 0,
        osdf_path: str = "",
        key_id: str = "",
        key_path: str = "",
        key_issuer: str = "",
         ):

    """ Initializes the CMF configuration based on the provided parameters. 
    Example:
    ```python
       cmf_init( type="local", 
                 path="/path/to/re",
                 git_remote_url="git@github.com:user/repo.git",
                 cmf_server_url="http://cmf-server"
                 neo4j_user", 
                 neo4j_password="password",
                 neo4j_uri="bolt://localhost:76"
               )
    ```
    Args: 
       type: Type of repository ("local", "minioS3", "amazonS3", "sshremote")
       path: Path for the local repository. 
       git_remote_url: Git remote URL for version control.
       cmf_server_url: CMF server URL.
       neo4j_user: Neo4j database username.
       neo4j_password: Neo4j database password.
       neo4j_uri: Neo4j database URI.
       url: URL for MinioS3 or AmazonS3.
       endpoint_url: Endpoint URL for MinioS3.
       access_key_id: Access key ID for MinioS3 or AmazonS3.
       secret_key: Secret key for MinioS3 or AmazonS3. 
       session_token: Session token for AmazonS3.
       user: SSH remote username.
       password: SSH remote password. 
       port: SSH remote port
    Returns:
       Output based on the initialized repository type.
    """

    if type == "":
        return print("Error: Type is not provided")
    if type not in ["local","minioS3","amazonS3","sshremote","osdfremote"]:
        return print("Error: Type value is undefined"+ " "+type+".Expected: "+",".join(["local","minioS3","amazonS3","sshremote","osdfremote"]))

    if neo4j_user != "" and  neo4j_password != "" and neo4j_uri != "":
        pass
    elif neo4j_user == "" and  neo4j_password == "" and neo4j_uri == "":
        pass
    else:
        return print("Error: Enter all neo4j parameters.") 

    args={'path': path,
        'git_remote_url': git_remote_url,
        'url': url,
        'endpoint_url': endpoint_url,
        'access_key_id': access_key_id,
        'secret_key': secret_key,
        'session_token': session_token,
        'user': user,
        'password': password,
        'osdf_path': osdf_path,
        'key_id': key_id,
        'key_path': key_path, 
        'key-issuer': key_issuer,
        }

    status_args=non_related_args(type, args)

    if type == "local" and path != "" and  git_remote_url != "" :
        """Initialize local repository"""
        cli_args = cli.parse_args(
            [
               "init",
               "local",
               "--path",
               path,
               "--git-remote-url",
               git_remote_url,
               "--cmf-server-url",
               cmf_server_url,
               "--neo4j-user",
               neo4j_user,
               "--neo4j-password",
               neo4j_password,
               "--neo4j-uri",
               neo4j_uri 
            ]
           )
        cmd = cli_args.func(cli_args)
        msg = cmd.do_run()
        print(msg)
        if status_args != []:
            print("There are non-related arguments: "+",".join(status_args)+".Please remove them.")
        return msg
         
    elif type == "minioS3" and url != "" and endpoint_url != "" and access_key_id != "" and secret_key != "" and git_remote_url != "":
        """Initialize minioS3 repository"""
        cli_args = cli.parse_args(
            [
               "init",
               "minioS3",
               "--url",
               url ,  
               "--endpoint-url",
               endpoint_url,        
               "--access-key-id",
               access_key_id,
               "--secret-key",
               secret_key,
               "--git-remote-url",
               git_remote_url,
               "--cmf-server-url",
               cmf_server_url,
               "--neo4j-user",
               neo4j_user,
               "--neo4j-password",
               neo4j_password,
               "--neo4j-uri",
               neo4j_uri 
            ]
           )
        cmd = cli_args.func(cli_args)
        msg = cmd.do_run()
        print(msg)
        if status_args != []:
            print("There are non-related arguments: "+",".join(status_args)+".Please remove them.")
        return msg

    elif type == "amazonS3" and url != "" and access_key_id != "" and secret_key != "" and git_remote_url != "":
        """Initialize amazonS3 repository"""
        cli_args = cli.parse_args(
            [
               "init",
               "amazonS3",
               "--url",
               url,
               "--access-key-id",
               access_key_id,
               "--secret-key",
               secret_key,
               "--session-token",
               session_token,
               "--git-remote-url",
               git_remote_url,
               "--cmf-server-url",
               cmf_server_url,
               "--neo4j-user",
               neo4j_user,
               "--neo4j-password",
               neo4j_password,
               "--neo4j-uri",
               neo4j_uri 
            ]
           )
        cmd = cli_args.func(cli_args)
        msg = cmd.do_run()
        print(msg)
    
        if status_args != []:
            print("There are non-related arguments: "+",".join(status_args)+".Please remove them.")

        return msg

    elif type == "sshremote" and path != "" and user != "" and port != 0 and password != "" and git_remote_url != "":
        """Initialize sshremote repository"""
        cli_args = cli.parse_args(
            [
               "init",
               "sshremote",
               "--path",
               path,
               "--user",
               user , 
               "--port",
               port,
               "--password",
               password,
               "--git-remote-url",
               git_remote_url,
               "--cmf-server-url",
               cmf_server_url,
               "--neo4j-user",
               neo4j_user,
               "--neo4j-password",
               neo4j_password,
               "--neo4j-uri",
               neo4j_uri 
            ]
           )
        cmd = cli_args.func(cli_args)
        msg = cmd.do_run()
        print(msg)
        if status_args != []:
            print("There are non-related arguments: "+",".join(status_args)+".Please remove them.")

        return msg

    elif type == "osdfremote" and osdf_path != "" and key_id != "" and key_path != 0 and key_issuer != "" and git_remote_url != "":
        """Initialize osdfremote repository"""
        cli_args = cli.parse_args(
            [
               "init",
               "osdf",
               "--path",
               path,
               "--key-id",
               key_id, 
               "--key-path",
               key_path,
               "--key-issuer",
               key_issuer,
               "--git-remote-url",
               git_remote_url,
               "--cmf-server-url",
               cmf_server_url,
               "--neo4j-user",
               neo4j_user,
               "--neo4j-password",
               neo4j_password,
               "--neo4j-uri",
               neo4j_uri 
            ]
           )
        cmd = cli_args.func(cli_args)
        msg = cmd.do_run()
        print(msg)
        if status_args != []:
            print("There are non-related arguments: "+",".join(status_args)+".Please remove them.")

        return msg

    else:
        print("Error: Enter all arguments")
        

def non_related_args(type : str, args : dict):
    available_args=[i for i, j in args.items() if j != ""]
    local=["path", "git_remote_url"]
    minioS3=["url", "endpoint_url", "access_key_id", "secret_key", "git_remote_url"]
    amazonS3=["url", "access_key_id", "secret_key", "session_token", "git_remote_url"]
    sshremote=["path", "user", "port", "password", "git_remote_url"]
    osdfremote=["osdf_path", "key_id", "key_path", "key-issuer", "git_remote_url"]


    dict_repository_args={"local" : local, "minioS3" : minioS3, "amazonS3" : amazonS3, "sshremote" : sshremote}
    
    for repo,arg in dict_repository_args.items():
        if repo ==type:
            non_related_args=list(set(available_args)-set(dict_repository_args[repo]))
    return non_related_args


def pipeline_list(filepath = "./mlmd"):
    """ Display list of pipline for current mlmd.

    Example:
    ```python
         result = _pipeline_list("./mlmd_directory")
    ```

    Args:
        filepath: File path to store the MLMD file. 
    Returns:
        Pending
    """

    # Optional arguments: filepath( path to store the MLMD file)
    cli_args = cli.parse_args(
            [
               "pipeline",
               "list",
               "-f",
               filepath
            ]
           )
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    print(msg)
    return msg


def execution_list(pipeline_name: str, filepath = "./mlmd", execution_id: str = "", long = True):
    """ Display list of execution for given pipeline.
    Example: 
    ```python 
        result = _execution_list("example_pipeline", "./mlmd_directory", "example_execution_id", "long") 
    ```
    Args: 
       pipeline_name: Name of the pipeline. 
       filepath: Path to store the mlmd file. 
       execution_id: Executions for particular execution id. 
       long: Detailed summary regarding execution.
    Returns:
       Pending
    """
    # Required arguments: pipeline_name
    # Optional arguments: filepath( path to store mlmd file), execution_id, long
    cli_args = cli.parse_args(
            [
               "execution",
               "list",
               "-p",
               pipeline_name,
               "-f",
               filepath,
               "-e",
               execution_id,
               "-l",
               long
            ]
           )
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    print(msg)
    return msg


def artifact_list(pipeline_name: str, filepath = "./mlmd", artifact_name: str = "", long = True):
    """ Display list of artifact for given pipeline.
    Example: 
    ```python 
        result = _artifact_list("example_pipeline", "./mlmd_directory", "example_artifact_name", "long") 
    ```
    Args: 
       pipeline_name: Name of the pipeline. 
       filepath: Path to store the mlmd file. 
       artifact_name: Artifacts for particular artifact name. 
       long: Detailed summary regarding artifact.
    Returns:
       Pending
    """
    # Required arguments: pipeline_name
    # Optional arguments: filepath( path to store mlmd file), artifact_name, long
    cli_args = cli.parse_args(
            [
               "artifact",
               "list",
               "-p",
               pipeline_name,
               "-f",
               filepath,
               "-a",
               artifact_name,
               "-l",
               long
            ]
           )
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    print(msg)
    return msg