from cmflib import cli


def mt_push(pipeline_name, file_name, execution_id):
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

def mt_pull(pipeline_name, file_name, execution_id):
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

def arti_push():
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


def arti_pull(pipeline_name, file_name):

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

def arti_pull_single(pipeline_name, file_name,artifact_name):
    print("inside_cmf_cmd_wrapper")
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


def cmf_cmd_init(): 
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

def init_local(path,git_remote_url,cmf_server_url,neo4j_user,neo4j_password,neo4j_uri):
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


def init_minioS3(url,endpoint_url,access_key_id,secret_key,git_remote_url,cmf_server_url,neo4j_user,neo4j_password,neo4j_uri):
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
    
def init_amazonS3(url,access_key_id,secret_key,git_remote_url,cmf_server_url,neo4j_user,neo4j_password,neo4j_uri):
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

def init_sshremote(path,user,port,password,git_remote_url,cmf_server_url,neo4j_user,neo4j_password,neo4j_uri):
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
