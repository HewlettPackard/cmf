###
# Copyright (2024) Hewlett Packard Enterprise Development LP
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

#!/usr/bin/env python3
from typing import Optional, List

class CmfResponse(Exception):
    """
    Response and Exceptions raised by the CMF.
    CmfResponse includes two child classes,
        1. CmfSuccess
        2. CmfFailure
    On the basis of success and failure various child classes are created.

    Base class for all the cmf responses and  exceptions.
    """

    def __init__(self, return_code=None, status="failure", *args):
        self.return_code = return_code
        self.status = status
        super().__init__(*args)


class CmfFailure(CmfResponse):
    def __init__(self, return_code=None, *args):
        super().__init__(return_code, status="failure", *args)


# Subclass for Success Cases
class CmfSuccess(CmfResponse):
    def __init__(self, return_code=None, *args):
        super().__init__(return_code, status="success", *args)


"""CMF Success Class"""


class ExecutionsAlreadyExists(CmfSuccess):
    def __init__(self, return_code=201):
        super().__init__(return_code)

    def handle(self):
        return "INFO: Executions already exists."


class ObjectDownloadSuccess(CmfSuccess):
    def __init__(self, object_name, download_loc, return_code=202):
        self.object_name = object_name
        self.download_loc = download_loc
        super().__init__(return_code)

    def handle(self):
        return f"SUCCESS: Object {self.object_name} downloaded at {self.download_loc}."


class BatchDownloadSuccess(CmfSuccess):
    def __init__(self, files_downloaded, return_code=203):
        self.files_downloaded = files_downloaded
        super().__init__(return_code)

    def handle(self):
        return f"SUCCESS: Number of files downloaded = {self.files_downloaded }."


class MlmdFilePullSuccess(CmfSuccess):
    def __init__(self, full_path_to_dump, return_code=204):
        self.full_path_to_dump = full_path_to_dump
        super().__init__(return_code)

    def handle(self):
        return f"SUCCESS: {self.full_path_to_dump} is successfully pulled."


class MlmdFilePushSuccess(CmfSuccess):
    def __init__(self, file_name, return_code=205):
        self.file_name = file_name
        super().__init__(return_code)

    def handle(self):
        return f"SUCCESS: {self.file_name} is successfully pushed."


class TensorboardPushSuccess(CmfSuccess):
    def __init__(self, tensorboard_file_name: str = "All", return_code=206):
        self.tensorboard_file_name = tensorboard_file_name
        super().__init__(return_code)

    def handle(self):
        if self.tensorboard_file_name == "All":
            return f"SUCCESS: All tensorboard logs pushed successfully."
        return (
            f"tensorboard logs: file {self.tensorboard_file_name} pushed successfully."
        )


class CmfInitComplete(CmfSuccess):
    def __init__(self, return_code=207):
        super().__init__(return_code)

    def handle(self):
        return "SUCCESS: cmf init complete."


class CmfInitShow(CmfSuccess):
    def __init__(self, attr_str, return_code=208):
        self.attr_str = attr_str
        super().__init__(return_code)

    def handle(self):
        return f"{self.attr_str}"


class ArtifactPushSuccess(CmfSuccess):
    def __init__(self, message, return_code=209):
        self.message = message
        super().__init__(return_code)

    def handle(self):
        return self.message


class MetadataExportToJson(CmfSuccess):
    def __init__(self, full_path_to_dump, return_code=210):
        self.full_path_to_dump = full_path_to_dump
        super().__init__(return_code)

    def handle(self):
        return f"SUCCESS: metadata successfully exported in {self.full_path_to_dump}."


# This class is created for messages like "Done", "Records not found"
class MsgSuccess(CmfSuccess):
    def __init__(
        self,
        msg_str: Optional[str] = None,
        msg_list: Optional[List[str]] = None,
        return_code=211,
    ):
        self.msg_str = msg_str
        self.msg_list = msg_list
        super().__init__(return_code)

    def handle(self):
        if self.msg_list != None:
            return self.msg_list
        else:
            return self.msg_str


""" CMF FAILURE CLASSES"""


class PipelineNotFound(CmfFailure):
    def __init__(self, pipeline_name, return_code=101):
        self.pipeline_name = pipeline_name
        super().__init__(return_code)

    def handle(self):
        return f"ERROR: Pipeline name {self.pipeline_name} doesn't exist."


class FileNotFound(CmfFailure):
    def __init__(self, file_name, directory, return_code=102):
        self.directory = directory
        self.file_name = file_name
        super().__init__(return_code)

    def handle(self):
        return f"ERROR: File {self.file_name} doesn't exists in {self.directory} directory."


class BucketNotFound(CmfFailure):
    def __init__(self, bucket_name, return_code=103):
        self.bucket_name = bucket_name
        super().__init__(return_code)

    def handle(self):
        return f"ERROR: Bucket {self.bucket_name} doesn't exist."


class ExecutionsNotFound(CmfFailure):
    def __init__(self, return_code=104):
        super().__init__(return_code)

    def handle(self):
        return f"ERROR: Executions not found."


class ExecutionUUIDNotFound(CmfFailure):
    def __init__(self, exec_uuid, return_code=105):
        self.exec_uuid = exec_uuid
        super().__init__(return_code)

    def handle(self):
        return f"ERROR: Execution uuid {self.exec_uuid} is not present in mlmd."


class ArtifactNotFound(CmfFailure):
    def __init__(self, artifact_name, return_code=106):
        self.artifact_name = artifact_name
        super().__init__(return_code)

    def handle(self):
        return f"ERROR: Artifact {self.artifact_name} not found."


class ObjectDownloadFailure(CmfFailure):
    def __init__(self, object_name, return_code=107):
        self.object_name = object_name
        super().__init__(return_code)

    def handle(self):
        return f"Object {self.object_name} is not downloaded."


class BatchDownloadFailure(CmfFailure):
    def __init__(self, files_downloaded, Files_failed_to_download, return_code=108):
        self.files_downloaded = files_downloaded
        self.Files_failed_to_download = Files_failed_to_download
        super().__init__(return_code)

    def handle(self):
        return f"INFO: Number of files downloaded = {self.files_downloaded }. Files failed to download = {self.Files_failed_to_download}."


class Minios3ServerInactive(CmfFailure):
    def __init__(self, return_code=109):
        super().__init__(return_code)

    def handle(self):
        return f"ERROR: MinioS3 server is not running!!!"


class CmfNotConfigured(CmfFailure):
    def __init__(self, message, return_code=110):
        self.message = message
        super().__init__(return_code)

    def handle(self):
        return self.message


class MlmdNotFoundOnServer(CmfFailure):
    def __init__(self, return_code=111):
        super().__init__(return_code)

    def handle(self):
        return "ERROR: Metadata file not available on cmf-server."


class UpdateCmfVersion(CmfFailure):
    def __init__(self, return_code=112):
        super().__init__(return_code)

    def handle(self):
        return "ERROR: You need to update cmf to the latest version. Unable to push metadata file."


class TensorboardPushFailure(CmfFailure):
    def __init__(self, tensorboard_file_name, response_text, return_code=113):
        self.tensorboard_file_name = tensorboard_file_name
        self.response_text = response_text
        super().__init__(return_code)

    def handle(self):
        return f"ERROR: Failed to upload file {self.tensorboard_file_name}. Server response: {self.response_text}."


class Neo4jArgumentNotProvided(CmfFailure):
    def __init__(self, return_code=114):
        super().__init__(return_code)

    def handle(self):
        return "ERROR: Provide user, password and uri for neo4j initialization."


class CmfInitFailed(CmfFailure):
    def __init__(self, return_code=115):
        super().__init__(return_code)

    def handle(self):
        return "ERROR: cmf init failed."


class CmfServerNotAvailable(CmfFailure):
    def __init__(self, return_code=116):
        super().__init__(return_code)

    def handle(self):
        return "ERROR: cmf-server is not available."


class InternalServerError(CmfFailure):
    def __init__(self, return_code=117):
        super().__init__(return_code)

    def handle(self):
        return "cmf-server error: The server encountered an unexpected error."


class MlmdFilePullFailure(CmfFailure):
    def __init__(self, return_code=118):
        super().__init__(return_code)

    def handle(self):
        return "ERROR: Unable to pull metadata file."


class DirectoryNotfound(CmfFailure):
    def __init__(self, dir, return_code=119):
        self.dir = dir
        super().__init__(return_code)

    def handle(self):
        return f"ERROR: {self.dir} doesn't exists."


class FileNameNotfound(CmfFailure):
    def __init__(self, return_code=120):
        super().__init__(return_code)

    def handle(self):
        return "ERROR: Provide path with file name."


class NoDataFoundOsdf(CmfFailure):
    def __init__(self, return_code=121):
        super().__init__(return_code)

    def handle(self):
        return "ERROR: No data received from the server."


class InvalidTensorboardFilePath(CmfFailure):
    def __init__(self, return_code=122):
        super().__init__(return_code)

    def handle(self):
        return "ERROR: Invalid tensorboard logs path. Provide valid file/folder path for tensorboard logs!!"


class DuplicateArgumentNotAllowed(CmfFailure):
    def __init__(self, argument_name, argument_flag, return_code=123):
        self.argument_flag = argument_flag
        self.argument_name = argument_name
        super().__init__(return_code)

    def handle(self):
        return f"Error: You can only provide one {self.argument_name} using the {self.argument_flag} flag."


class MissingArgument(CmfFailure):
    def __init__(self, argument_name, return_code=124):
        self.argument_name = argument_name
        super().__init__(return_code)

    def handle(self):
        return f"Error: Missing {self.argument_name}"


class NoChangesMadeInfo(CmfFailure):
    def __init__(self, return_code=125):
        super().__init__(return_code)

    def handle(self):
        return "INFO: No changes made to the file. Operation aborted."


class MsgFailure(CmfFailure):
    def __init__(
        self,
        msg_str: Optional[str] = None,
        msg_list: Optional[List[str]] = None,
        return_code=126,
    ):
        self.msg_str = msg_str
        self.msg_list = msg_list
        super().__init__(return_code)

    def handle(self):
        if self.msg_list != None:
            return self.msg_list
        else:
            return self.msg_str
