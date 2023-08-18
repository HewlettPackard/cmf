
import os
from cmflib.cmf_commands_wrapper import (
    cmf_cmd_init,
    init_local,
    init_minioS3,
    init_amazonS3,
    init_sshremote
)

class Cmf_init:
    def __init__(
        self,
        filename: str = "mlmd",
        pipeline_name: str = "",
    ):
        self.filename=filename
        self.pipeline_name=pipeline_name

    def cmf_init_show(self):
        """Check whether repository is initialized(local,minioS3,amazonS3,sshremote)"""
        output = cmf_cmd_init()
        return output

    def cmf_init_local(
        self,
        path: str,
        git_remote_url: str,
        cmf_server_url: str = "",
        neo4j_user: str = "",
        neo4j_password: str = "",
        neo4j_uri: str = "",
    ):
        """Initialize local repository"""
        output = init_local(
            path, git_remote_url, cmf_server_url, neo4j_user, neo4j_password, neo4j_uri
        )
        return output

    def cmf_init_minio(
        self,
        url: str,
        endpoint_url: str,
        access_key_id: str,
        secret_key: str,
        git_remote_url: str,
        cmf_server_url: str = "",
        neo4j_user: str = "",
        neo4j_password: str = "",
        neo4j_uri: str = "",
    ):
        """Initialize minioS3 repository"""
        output = init_minioS3(
            url,
            endpoint_url,
            access_key_id,
            secret_key,
            git_remote_url,
            cmf_server_url,
            neo4j_user,
            neo4j_password,
            neo4j_uri,
        )
        return output
    
    def cmf_init_amazon(
        self,
        url: str,
        access_key_id: str,
        secret_key: str,
        git_remote_url: str,
        cmf_server_url: str = "",
        neo4j_user: str = "",
        neo4j_password: str = "",
        neo4j_uri: str = "",
    ):
        """Initialize amazonS3 repository"""
        output = init_amazonS3(
            url,
            access_key_id,
            secret_key,
            git_remote_url,
            cmf_server_url,
            neo4j_user,
            neo4j_password,
            neo4j_uri,
        )
        return output

    def cmf_init_sshremote(
        self,
        path: str,
        user: str,
        port: int,
        password: str,
        git_remote_url: str,
        cmf_server_url: str = "",
        neo4j_user: str = "",
        neo4j_password: str = "",
        neo4j_uri: str = "",
    ):
        """Initialize sshremote repository"""
        output = init_sshremote(
            path,
            user,
            port,
            password,
            git_remote_url,
            cmf_server_url,
            neo4j_user,
            neo4j_password,
            neo4j_uri,
        )
        return output

