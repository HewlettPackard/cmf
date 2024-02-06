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


def _metadata_push(pipeline_name, file_name, execution_id):
    cli_args = cli.parse_args(
            [
               "metadata",
               "push",
               "-p",
               pipeline_name,
               "-f",
               file_name,
               "-e",
               execution_id
            ]
           )
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    print(msg)
    return msg

def _metadata_pull(pipeline_name, file_name, execution_id):
    cli_args = cli.parse_args(
            [
               "metadata",
               "pull",
               "-p",
               pipeline_name,
               "-f",
               file_name,
               "-e",
               execution_id
            ]
           )
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    print(msg)
    return msg

def _artifact_push():
    cli_args = cli.parse_args(
            [
               "artifact",
               "push",

            ]
           )
    cmd = cli_args.func(cli_args)
    msg = cmd.do_run()
    print(msg)
    return msg


def _artifact_pull(pipeline_name, file_name):

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

def _artifact_pull_single(pipeline_name, file_name,artifact_name):
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

def _init_local(path,git_remote_url,cmf_server_url,neo4j_user,neo4j_password,neo4j_uri):
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


def _init_minioS3(url,endpoint_url,access_key_id,secret_key,git_remote_url,cmf_server_url,neo4j_user,neo4j_password,neo4j_uri):
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
    
def _init_amazonS3(url,access_key_id,secret_key,git_remote_url,cmf_server_url,neo4j_user,neo4j_password,neo4j_uri):
    cli_args = cli.parse_args(
            [
               "init",
               "amazonS3",
               "--url",
               url ,  
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

def _init_sshremote(path,user,port,password,git_remote_url,cmf_server_url,neo4j_user,neo4j_password,neo4j_uri):
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
