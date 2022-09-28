#!/usr/bin/env python3
import argparse
import os

from cmflib import cmfquery
from cmflib import minio_artifacts
from cmflib.cli.command import CmdBase


class CmdPull(CmdBase):
    def run(self):
        # Put a check to see whether pipline exists or not
        current_directory = os.getcwd()
        mlmd_file_name = "./mlmd"
        if self.args.file_name:
            mlmd_file_name = self.args.file_name
            current_directory = os.path.dirname(self.args.file_name)
        if not os.path.exists(mlmd_file_name):
            return -1, f"{mlmd_file_name} doesn't exists in current directory"
        query = cmfquery.CmfQuery(mlmd_file_name)
        stages = query.get_pipeline_stages(self.args.pipeline_name)


        idendtifiers = []
        for i in stages:
            executions = query.get_all_executions_in_stage(i)  # getting all executions for stages
            dict_executions = executions.to_dict("dict")  # converting it to dictionary
            idendtifiers.append(dict_executions['id'][0])  # id's of execution

        name = []
        url = []
        for idendtifier in idendtifiers:
            artifactss = query.get_all_artifacts_for_execution(idendtifier)  # getting all artifacts

            artifacts_dict = artifactss.to_dict('dict')  # converting it to dictionary
            name.append(list(artifacts_dict['name'].values()))
            url.append(list(artifacts_dict['url'].values()))

        name_list_updated = []
        url_list_updated = []
        for i in range(len(name)):  # getting all the names and urls together
            name_list_updated = name_list_updated + name[i]
            url_list_updated = url_list_updated + url[i]

        final_list = []
        file_name = [(i.split(':'))[0] for i in name_list_updated]  # getting names
        for i in (tuple(zip(file_name, url_list_updated))):
            if type(i[1]) == str and i[1].startswith('s3://'):
                final_list.append(i)
        names_urls = list(set(final_list))  # list of tuple consist of names and urls
        artifact_class_obj = minio_artifacts.minio_artifacts()
        for name_url in names_urls:
            temp = name_url[1].split("/")
            bucket_name = temp[2]
            object_name = temp[3] + "/" + temp[4]
            path_name = current_directory + "/" + name_url[0]
            stmt = artifact_class_obj.download_artifacts(current_directory, bucket_name, object_name, path_name)
            print(stmt)
        return 0


def add_parser(subparsers, parent_parser):
    PULL_HELP = "Pull artifacts from minio S3 bucket"

    parser = subparsers.add_parser(
        "pull",
        parents=[parent_parser],
        description="This is Pull command",
        help=PULL_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "-P",
        "--pipeline_name",
        help="Specify Pipeline name",
        metavar="<pipeline_name>"
    )

    parser.add_argument(
        "-F",
        "--file_name",
        help="Specify mlmd file name",
        metavar="<file_name>"
    )

    parser.set_defaults(func=CmdPull)
<<<<<<< HEAD
=======

>>>>>>> Made changes as per review comments
