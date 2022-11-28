#!/usr/bin/env python3
import argparse
import os

from cmflib import cmfquery
from cmflib import (
    minio_artifacts,
    local_artifacts,
    amazonS3_artifacts,
    sshremote_artifacts,
)
from cmflib.cli.command import CmdBase
from cmflib.dvc_config import dvc_config


class CmdArtifactPull(CmdBase):
    def run(self):
        # Put a check to see whether pipline exists or not
        current_directory = os.getcwd()
        mlmd_file_name = "./mlmd"
        if self.args.file_name:
            mlmd_file_name = self.args.file_name
            current_directory = os.path.dirname(self.args.file_name)
        if not os.path.exists(mlmd_file_name):
            return f"{mlmd_file_name} doesn't exists in current directory"
        query = cmfquery.CmfQuery(mlmd_file_name)
        stages = query.get_pipeline_stages(self.args.pipeline_name)

        identifiers = []
        for i in stages:
            executions = query.get_all_executions_in_stage(
                i
            )  # getting all executions for stages
            dict_executions = executions.to_dict("dict")  # converting it to dictionary
            identifiers.append(dict_executions["id"][0])  # id's of execution

        name = []
        url = []
        for identifier in identifiers:
            get_artifacts = query.get_all_artifacts_for_execution(
                identifier
            )  # getting all artifacts

            artifacts_dict = get_artifacts.to_dict(
                "dict"
            )  # converting it to dictionary
            name.append(list(artifacts_dict["name"].values()))
            url.append(list(artifacts_dict["url"].values()))

        name_list_updated = []
        url_list_updated = []
        for i in range(len(name)):  # getting all the names and urls together
            name_list_updated = name_list_updated + name[i]
            url_list_updated = url_list_updated + url[i]

        final_list = []
        file_name = [(i.split(":"))[0] for i in name_list_updated]  # getting names
        for i in tuple(zip(file_name, url_list_updated)):
            if type(i[1]) == str:
                final_list.append(i)
        names_urls = list(set(final_list))  # list of tuple consist of names and urls
        # print(names_urls)
        dvc_config_op = dvc_config.get_dvc_config()
        print(dvc_config_op)
        if dvc_config_op[0] == "minio":
            minio_class_obj = minio_artifacts.minio_artifacts()
            for name_url in names_urls:
                temp = name_url[1].split("/")
                bucket_name = temp[2]
                object_name = temp[3] + "/" + temp[4]
                path_name = current_directory + "/" + name_url[0]
                stmt = minio_class_obj.download_artifacts(
                    dvc_config_op, current_directory, bucket_name, object_name, path_name
                )
                print(stmt)
        elif dvc_config_op[0] == "local-storage":
            local_class_obj = local_artifacts.local_artifacts()
            print(names_urls)
            print(dvc_config_op)
            for name_url in names_urls:
                temp = name_url[1].split("/")
                temp_length = len(temp)
                download_loc = current_directory + "/" + name_url[0]
                current_dvc_loc = (
                    temp[(temp_length - 2)] + "/" + temp[(temp_length - 1)]
                )
                print(current_dvc_loc)
                #stmt = local_class_obj.download_artifacts(
                 #   dvc_config_op, current_directory, current_dvc_loc, name_url[0]
                #)
                #print(stmt)
        elif dvc_config_op[0] == "ssh-storage":
            sshremote_class_obj = sshremote_artifacts.sshremote_artifacts()
            print(name_url)
        elif dvc_config_op[0] == "amazons3":
            amazonS3_class_obj = amazonS3_artifacts.amazonS3_artifacts()
            for name_url in names_urls:
                temp = name_url[1].split("/")
                print(temp)
                bucket_name = temp[2]
                object_name = f"{temp[3]}/{temp[4]}/{temp[5]}"
                path_name = current_directory + "/" + name_url[0]
                stmt = amazonS3_class_obj.download_artifacts(
                    dvc_config_op, current_directory, bucket_name, object_name, path_name
                )
                print(stmt)
        else:
            pass
        return 0


def add_parser(subparsers, parent_parser):
    PULL_HELP = "Pull artifacts from local/remote repo"

    parser = subparsers.add_parser(
        "pull",
        parents=[parent_parser],
        description="Pull artifacts from local/remote repo",
        help=PULL_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    required_arguments = parser.add_argument_group("required arguments")

    required_arguments.add_argument(
        "-p",
        "--pipeline-name",
        required=True,
        help="Specify Pipeline name",
        metavar="<pipeline_name>",
    )

    parser.add_argument(
        "-f", "--file-name", help="Specify mlmd file name", metavar="<file_name>"
    )

    parser.set_defaults(func=CmdArtifactPull)
