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


def _metadata_push(pipeline_name, file_name, execution_uuid, tensorboard_path):
    """ Pushes metadata file to CMF-server.
    Args:
        pipeline_name: Name of the pipeline.
        file_name: Specify input metadata file name.
        execution_uuid: Optional execution UUID.
        tensorboard_path: Path to tensorboard logs.
    Returns:
        Output from the metadata push command.
    """
    cli_args = cli.parse_args(
            [
               "metadata",
               "push",
               "-p",
               pipeline_name,
               "-f",
               file_name,
               "-e",
               execution_uuid,
               "-t",
               tensorboard_path
            ]
           )
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    print(msg)
    return msg


def _metadata_pull(pipeline_name, file_name, execution_uuid):
    """ Pulls metadata file from CMF-server. 
     Args: 
        pipeline_name: Name of the pipeline. 
        file_name: Specify output metadata file name.
        execution_uuid: Optional execution UUID. 
     Returns: 
        Output from the metadata pull command. 
     """
    cli_args = cli.parse_args(
            [
               "metadata",
               "pull",
               "-p",
               pipeline_name,
               "-f",
               file_name,
               "-e",
               execution_uuid,
            ]
           )
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    print(msg)


def _metadata_export(pipeline_name, json_file_name, file_name):
    """ Export local metadata's metadata in json format to a json file. 
     Args: 
        pipeline_name: Name of the pipeline. 
        json_file_name: File path of json file. 
        file_name: Specify input metadata file name. 
     Returns: 
        Output from the metadata export command. 
     """
    cli_args = cli.parse_args(
            [
               "metadata",
               "export",
               "-p",
               pipeline_name,
               "-j",
               json_file_name,
               "-f",
               file_name,
            ]
           )
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    print(msg)
    return msg

def _artifact_push(pipeline_name, file_name, jobs):
    """ Pushes artifacts to the initialized repository.
    Args: 
       pipeline_name: Name of the pipeline. 
       filepath: Path to store the artifact. 
       jobs: Number of jobs to use for pushing artifacts.
    Returns:
        Output from the artifact push command.
    """
    cli_args = cli.parse_args(
            [
               "artifact",
               "push",
               "-p",
               pipeline_name,
               "-f",
               file_name,
               "-j",
               jobs
            ]
           )
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    print(msg)
    return msg


def _artifact_pull(pipeline_name, file_name):
    """ Pulls artifacts from the initialized repository.
    Args:
        pipeline_name: Name of the pipeline.
        file_name: Specify input metadata file name.
    Returns:
        Output from the artifact pull command.
    """
    cli_args = cli.parse_args(
            [
               "artifact",
               "pull",
               "-p",
               pipeline_name,
               "-f",
               file_name,
            ]
           )
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    print(msg)
    return msg


def _artifact_pull_single(pipeline_name, file_name, artifact_name):
    """ Pulls a single artifact from the initialized repository. 
    Args: 
       pipeline_name: Name of the pipeline. 
       file_name: Specify input metadata file name.
       artifact_name: Name of the artifact. 
    Returns:
       Output from the artifact pull command. 
    """
    cli_args = cli.parse_args(
            [
               "artifact",
               "pull",
               "-p",
               pipeline_name,
               "-f",
               file_name,
               "-a",
               artifact_name,
            ]
           )
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    print(msg)
    return msg


def _cmf_cmd_init():
    """ Initializes and shows details of the CMF command. 
    Returns: 
       Output from the init show command. 
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


def _init_local(path, git_remote_url, cmf_server_url, neo4j_user, neo4j_password, neo4j_uri):
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
    return msg


def _init_minioS3(url, endpoint_url, access_key_id, secret_key, git_remote_url, cmf_server_url, neo4j_user, neo4j_password, neo4j_uri):
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
    return msg
    

def _init_amazonS3(url, access_key_id, secret_key, session_token, git_remote_url, cmf_server_url, neo4j_user, neo4j_password, neo4j_uri):
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
    return msg


def _init_sshremote(path,user, port, password, git_remote_url, cmf_server_url, neo4j_user, neo4j_password, neo4j_uri):
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
    return msg


def _init_osdfremote(path, cache, key_id, key_path, key_issuer, git_remote_url, cmf_server_url, neo4j_user, neo4j_password, neo4j_uri):
    """Initialize osdfremote repository"""
    cli_args = cli.parse_args(
            [
               "init",
               "osdf",
               "--path",
               path,
               "--cache",
               cache,
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
    return msg
  
    
def _artifact_list(pipeline_name, file_name, artifact_name):
    """ Displays artifacts from the input metadata file with a few properties in a 7-column table, limited to 20 records per page.
    Args: 
       pipeline_name: Name of the pipeline. 
       file_name: Specify input metadata file name. 
       artifact_name: Artifacts for particular artifact name.
    Returns:
       Output from the artifact list command. 
    """
    cli_args = cli.parse_args(
            [
               "artifact",
               "list",
               "-p",
               pipeline_name,
               "-f",
               file_name,
               "-a",
               artifact_name
            ]
           )
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    print(msg)
    return msg


def _pipeline_list(file_name):
    """ Display a list of pipeline name(s) from the available input metadata file.
    Args:
        file_name: Specify input metadata file name. 
    Returns:
        Output from the pipeline list command.
    """
    cli_args = cli.parse_args(
            [
               "pipeline",
               "list",
               "-f",
               file_name
            ]
           )
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    print(msg)
    return msg


def _execution_list(pipeline_name, file_name, execution_uuid):
    """Displays executions from the input metadata file with a few properties in a 7-column table, limited to 20 records per page.
    Args: 
       pipeline_name: Name of the pipeline. 
       file_name: Specify input metadata file name.
       execution_uuid: Specify the execution uuid to retrieve execution.
    Returns:
       Output from the execution list command. 
    """
    cli_args = cli.parse_args(
            [
               "execution",
               "list",
               "-p",
               pipeline_name,
               "-f",
               file_name,
               "-e",
               execution_uuid
            ]
           )
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    print(msg)
    return msg

def _repo_push(pipeline_name, file_name, tensorboard_path, execution_uuid, jobs):
    """ Push artifacts, metadata files, and source code to the user's artifact repository, cmf-server, and git respectively.
    Args: 
       pipeline_name: Name of the pipeline. 
       file_name: Specify input metadata file name.
       execution_uuid: Specify execution uuid.
       tensorboard_path: Path to tensorboard logs.
       jobs: Number of jobs to use for pushing artifacts.
    Returns:
       Output from the repo push command. 
    """
    cli_args = cli.parse_args(
            [
               "repo",
               "push",
               "-p",
               pipeline_name,
               "-f",
               file_name,
               "-e",
               execution_uuid,
               "-t",
               tensorboard_path,
               "-j",
               jobs
            ]
           )
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    print(msg)
    return msg


def _repo_pull(pipeline_name, file_name, execution_uuid):
    """ Pull artifacts, metadata files, and source code from the user's artifact repository, cmf-server, and git respectively.
    Args: 
       pipeline_name: Name of the pipeline. 
       file_name: Specify output metadata file name.
       execution_uuid: Specify execution uuid.
    Returns:
       Output from the repo pull command. 
    """
    cli_args = cli.parse_args(
            [
               "repo",
               "pull",
               "-p",
               pipeline_name,
               "-f",
               file_name,
               "-e",
               execution_uuid
            ]
           )
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    print(msg)
    return msg


def _dvc_ingest(file_name):
   """ Ingests metadata from the dvc.lock file into the CMF. 
       If an existing MLMD file is provided, it merges and updates execution metadata 
       based on matching commands, or creates new executions if none exist.
    Args: 
       file_name: Specify input metadata file name.
    Returns:
       Output from the dvc ingest command. 
   """
   cli_args = cli.parse_args(
            [
               "dvc",
               "ingest",
               "-f",
               file_name,
            ]
           )
   cmd = cli_args.func(cli_args)
   msg = cmd.do_run()
   print(msg)
   return msg