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

from typing import Callable, Any
from cmflib import cli
from cmflib.cmf_exception_handling import CmfResponse

import logging

logger = logging.getLogger(__name__)

def exception_handler_decorator(
    target_function: Callable[..., Any]
) -> Callable[..., Any]:
    """
    Decorator to handle CmfResponse exceptions.
    """
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return target_function(*args, **kwargs).handle()
        except CmfResponse as e:
            return e.handle()

    return wrapper


@exception_handler_decorator
def _metadata_push(
    pipeline_name: str, file_name: str, execution_uuid: str, tensorboard_path: str
) -> str:
    """ Pushes metadata file to CMF-server.
    Args:
        pipeline_name: Name of the pipeline.
        file_name: Specify input metadata file name.
        execution_uuid: Optional execution UUID.
        tensorboard_path: Path to tensorboard logs.
    Returns:
        Output from the metadata push command.
    """
    cli_args = [
            "metadata",
            "push",
            "-p",
            pipeline_name,
            "-f",
            file_name,
        ]
    
    # Only append the execution_uuid and tensorboard path flag if a real value was supplied
    if execution_uuid:
        cli_args.extend(["-e", execution_uuid])
    if tensorboard_path:
       cli_args.extend(["-t", tensorboard_path])

    
    cli_args = cli.parse_args(cli_args)
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    logger.info(msg)
    return msg


@exception_handler_decorator
def _metadata_pull(pipeline_name: str, file_name: str, execution_uuid: str) -> str:
    """ Pulls metadata file from CMF-server. 
     Args: 
        pipeline_name: Name of the pipeline. 
        file_name: Specify output metadata file name.
        execution_uuid: Optional execution UUID. 
     Returns: 
        Output from the metadata pull command. 
     """
    # Here, We are not extending the cli_args list directly with execution_uuid 
    # bcaz in our code[cmf/commands/metadata/pull.py], we are assinging execution_uuid as a none 
    # if it is not present 
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
    logger.info(msg)
    return msg


@exception_handler_decorator
def _metadata_export(pipeline_name: str, json_file_name: str, file_name: str) -> str:
    """ Export local metadata's metadata in json format to a json file. 
     Args: 
        pipeline_name: Name of the pipeline. 
        json_file_name: File path of json file. 
        file_name: Specify input metadata file name. 
     Returns: 
        Output from the metadata export command. 
     """
    cli_args = [
            "metadata",
            "export",
            "-p",
            pipeline_name,
            "-f",
            file_name,
        ]
    #  Only append the json_file_name flag if a real value was supplied
    if json_file_name:
       cli_args.extend(["-j", json_file_name])

    cli_args = cli.parse_args(cli_args)
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    return msg


@exception_handler_decorator
def _artifact_push(pipeline_name: str, file_name: str, jobs: str) -> str:
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
            jobs,
        ]
    )
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    return msg


@exception_handler_decorator
def _artifact_pull(pipeline_name: str, file_name: str, artifact_name: str) -> str:
    """ Pulls artifacts from the initialized repository.
    Args:
        pipeline_name: Name of the pipeline.
        file_name: Specify input metadata file name.
        artifact_name: Name of the artifact. 
    Returns:
        Output from the artifact pull command.
    """
    cli_args = [
            "artifact",
            "pull",
            "-p",
            pipeline_name,
            "-f",
            file_name,
        ]
    # Only append the optional artifact name flag if a real value was supplied
    if artifact_name:
         cli_args.extend(["-a", artifact_name])
         
    cli_args = cli.parse_args(cli_args)
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    return msg


@exception_handler_decorator
def _cmf_init_show() -> str:
    """ Initializes and shows details of the CMF command. 
    Returns: 
       Output from the init show command. 
    """ 
    cli_args = cli.parse_args(["init", "show"])
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    return msg


@exception_handler_decorator
def _init_local(
    path: str,
    git_remote_url: str,
    cmf_server_url: str,
    neo4j_user: str,
    neo4j_password: str,
    neo4j_uri: str,
) -> str:
    """Initialize local repository"""
    args = [
            "init",
            "local",
            "--path",
            path,
            "--git-remote-url",
            git_remote_url,
            "--cmf-server-url",
            cmf_server_url,
        ]

    # only append neo4j args if they are provided
    if neo4j_user and neo4j_password and neo4j_uri:
        args.extend(
            [
                "--neo4j-user",
                neo4j_user,
                "--neo4j-password",
                neo4j_password,
                "--neo4j-uri",
                neo4j_uri,
            ]
        )
    
    cli_args = cli.parse_args(args)
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    logger.info(msg)
    return msg


@exception_handler_decorator
def _init_minioS3(
    url: str,
    endpoint_url: str,
    access_key_id: str,
    secret_key: str,
    git_remote_url: str,
    cmf_server_url: str,
    neo4j_user: str,
    neo4j_password: str,
    neo4j_uri: str,
) -> str:
    """Initialize minioS3 repository"""
    args = [
            "init",
            "minioS3",
            "--url",
            url,
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
        ]
    # only append neo4j args if they are provided
    if neo4j_user and neo4j_password and neo4j_uri:
        args.extend(
            [
                "--neo4j-user",
                neo4j_user,
                "--neo4j-password",
                neo4j_password,
                "--neo4j-uri",
                neo4j_uri,
            ]
        )
    cli_args = cli.parse_args(args)
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    logger.info(msg)
    return msg
    

@exception_handler_decorator
def _init_amazonS3(
    url: str,
    access_key_id: str,
    secret_key: str,
    session_token: str,
    git_remote_url: str,
    cmf_server_url: str,
    neo4j_user: str,
    neo4j_password: str,
    neo4j_uri: str,
) -> str:
    """Initialize amazonS3 repository"""
    args = [
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
        ]

    # only append neo4j args if they are provided
    if neo4j_user and neo4j_password and neo4j_uri:
        args.extend(
            [
                "--neo4j-user",
                neo4j_user,
                "--neo4j-password",
                neo4j_password,
                "--neo4j-uri",
                neo4j_uri,
            ]
        )
    
    cli_args = cli.parse_args(args)
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    logger.info(msg)
    return msg


@exception_handler_decorator
def _init_sshremote(
    path: str,
    user: str,
    port: str,
    password: str,
    git_remote_url: str,
    cmf_server_url: str,
    neo4j_user: str,
    neo4j_password: str,
    neo4j_uri: str,
) -> str:
    """Initialize sshremote repository"""
    args = [
            "init",
            "sshremote",
            "--path",
            path,
            "--user",
            user,
            "--port",
            port,
            "--password",
            password,
            "--git-remote-url",
            git_remote_url,
            "--cmf-server-url",
            cmf_server_url,
        ]
    # only append neo4j args if they are provided
    if neo4j_user and neo4j_password and neo4j_uri:
        args.extend(
            [
                "--neo4j-user",
                    neo4j_user,
                    "--neo4j-password",
                    neo4j_password,
                    "--neo4j-uri",
                    neo4j_uri,
                ]
            )

    cli_args = cli.parse_args(args)
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    logger.info(msg)
    return msg


@exception_handler_decorator
def _init_osdfremote(
    path: str,
    cache: str,
    key_id: str,
    key_path: str,
    key_issuer: str,
    git_remote_url: str,
    cmf_server_url: str,
    neo4j_user: str,
    neo4j_password: str,
    neo4j_uri: str,
) -> str:
    """Initialize osdfremote repository"""
    args = [
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
    ]
    # only append neo4j args if they are provided
    if neo4j_user and neo4j_password and neo4j_uri:
        args.extend(
            [
                "--neo4j-user",
                    neo4j_user,
                    "--neo4j-password",
                    neo4j_password,
                    "--neo4j-uri",
                    neo4j_uri,
                ]
            )
    cli_args = cli.parse_args(args)
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    logger.info(msg)
    return msg
  

@exception_handler_decorator
def _artifact_list(pipeline_name: str, file_name: str, artifact_name: str) -> str:
    """Displays artifacts from the input metadata file with a few properties
    in a 7-column table, limited to 20 records per page.
    Args:
       pipeline_name: Name of the pipeline.
       file_name: Specify input metadata file name.
       artifact_name: Artifacts for particular artifact name.
    Returns:
       Output from the artifact list command.
    """
    cli_args = [
            "artifact",
            "list",
            "-p",
            pipeline_name,
            "-f",
            file_name,
        ]
    # Only append the optional artifact name flag if a real value was supplied
    if artifact_name:
        cli_args.extend(["-a", artifact_name])

    cli_args = cli.parse_args(cli_args)
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    logger.info(msg)
    return msg


@exception_handler_decorator
def _pipeline_list(file_name: str) -> str:
    """ Display a list of pipeline name(s) from the available input metadata file.
    Args:
        file_name: Specify input metadata file name. 
    Returns:
        Output from the pipeline list command.
    """
    cli_args = cli.parse_args(["pipeline", "list", "-f", file_name])
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    return msg


@exception_handler_decorator
def _execution_list(pipeline_name: str, file_name: str, execution_uuid: str) -> str:
    """Displays executions from the input metadata file with a few properties
    in a 7-column table, limited to 20 records per page.
    Args:
       pipeline_name: Name of the pipeline.
       file_name: Specify input metadata file name.
       execution_uuid: Specify the execution uuid to retrieve execution.
    Returns:
       Output from the execution list command.
    """
    args = [
        "execution",
        "list",
        "-p",
        pipeline_name,
        "-f",
        file_name,
    ]
    # Only append the optional execution uuid flag if a real value was supplied
    if execution_uuid:
        args.extend(["-e", execution_uuid])

    cli_args = cli.parse_args(args)
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    logger.info(msg)
    return msg


@exception_handler_decorator
def _repo_push(
    pipeline_name: str,
    file_name: str,
    tensorboard_path: str,
    execution_uuid: str,
    jobs: str,
) -> str:
    """Push artifacts, metadata files, and source code to the user's artifact
    repository, cmf-server, and git respectively.
    Args:
       pipeline_name: Name of the pipeline.
       file_name: Specify input metadata file name.
       execution_uuid: Specify execution uuid.
       tensorboard_path: Path to tensorboard logs.
       jobs: Number of jobs to use for pushing artifacts.
    Returns:
       Output from the repo push command.
    """
    cli_args = [
            "repo",
            "push",
            "-p",
            pipeline_name,
            "-f",
            file_name,
            ]
    # Only append the execution_uuid, tensorboard path and jobs flag if a real value was supplied
    if execution_uuid:
        cli_args.extend(["-e", execution_uuid])
    if tensorboard_path:
        cli_args.extend(["-t", tensorboard_path])
    if jobs:
        cli_args.extend(["-j", jobs])

    cli_args = cli.parse_args(cli_args)
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    logger.info(msg)
    return msg

@exception_handler_decorator
def _repo_pull(pipeline_name: str, file_name: str, execution_uuid: str) -> str:
    """Pull artifacts, metadata files, and source code from the user's artifact
    repository, cmf-server, and git respectively.
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
            execution_uuid,
        ]
    )
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    logger.info(msg)
    return msg


@exception_handler_decorator
def _dvc_ingest(file_name: str) -> str:
   """Ingests metadata from the dvc.lock file into the CMF.
       If an existing MLMD file is provided, it merges and updates execution
       metadata based on matching commands, or creates new executions if none exist.
    Args:
       file_name: Specify input metadata file name.
    Returns:
       Output from the dvc ingest command.
   """
   cli_args = cli.parse_args(["dvc", "ingest", "-f", file_name])
   cmd = cli_args.func(cli_args)
   msg = cmd.do_run()
   logger.info(msg)
   return msg
