"""
    Exceptions raised by the CMF.
    CmfResponse includes two child classes 
           1. CmfSuccess
           2. CmfFailure
    On the basis of success and failure various child classes are created

"""

class CmfResponse(Exception):
    """Base class for all cmf exceptions."""

    def __init__(self, return_code=None,  status="failure", *args):
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


class PipelineNameNotFound(CmfFailure):
    def __init__(self,pipeline_name,return_code=101):
        self.pipeline_name = pipeline_name 
        super().__init__(return_code)

    def handle(self):
        return f"Pipeline_name {self.pipeline_name} doesn't exist"

    
class FileNotFound(CmfFailure):
    def __init__(self,file_name,return_code=102):
        self.file_name =file_name
        super().__init__(return_code)
    
    def handle(self):
        return f"File Not Found: {self.file_name}"

class BucketNotFound(CmfFailure):
    def __init__(self,return_code=103):
        super().__init__(return_code)
 
    def handle(self):
        return f"Bucket doesnt exist"

class ExecutionsAlreadyExists(CmfSuccess):
    def __init__(self, return_code=201):
        super().__init__(return_code)
 
    @staticmethod
    def handle():
        return "Executions already exists."


class ExecutionsNotFound(CmfFailure):
    def __init__(self, return_code=104):
        super().__init__(return_code)
 
    def handle(self):
        return f"Executions not found"
    
class ExecutionIDNotFound(CmfFailure):
    def __init__(self,exec_id, return_code=105):
        self.exec_id = exec_id
        super().__init__(return_code)
 
    def handle(self):
        return f"Error: Execution id {self.exec_id} is not present in mlmd."
    
class ArtifactNotFound(CmfFailure):
    def __init__(self,artifact_name, return_code=106):
        self.artifact_name = artifact_name
        super().__init__(return_code)
 
    def handle(self):
        return f"Artifact {self.artifact_name} not found"


class ObjectDownloadSuccess(CmfSuccess):
    def __init__(self,object_name,download_loc, return_code=202):
        self.object_name = object_name
        self.download_loc = download_loc
        super().__init__(return_code)

    def handle(self):
        return f"object {self.object_name} downloaded at {self.download_loc}."
    
class ObjectDownloadFailure(CmfFailure):
    def __init__(self,object_name, return_code=107):
        self.object_name = object_name
        super().__init__(return_code)

    def handle(self):
        return f"object {self.object_name} is not downloaded."
    
class BatchDownloadFailure(CmfFailure):
    def __init__(self,files_downloaded, Files_failed_to_download, return_code=108):
        self.files_downloaded = files_downloaded
        self.Files_failed_to_download = Files_failed_to_download
        super().__init__(return_code)

    def handle(self):
        return f"Number of files downloaded = {self.files_downloaded }. Files failed to download = {self.Files_failed_to_download}"

class BatchDownloadSuccess(CmfSuccess):
    def __init__(self,files_downloaded, return_code=203):
        self.files_downloaded = files_downloaded
        super().__init__(return_code)

    def handle(self):
        return f"Number of files downloaded = {self.files_downloaded }."

class Minios3ServerInactive(CmfFailure):
    def __init__(self,return_code=109):
        super().__init__(return_code)

    def handle(self):
        return f"MinioS3 server failed to start!!!"

class CmfNotConfigured(CmfFailure):
    def __init__(self,message, return_code=110):
        self.message = message
        super().__init__(return_code)

    def handle(self):
        return self.message

class MlmdNotFoundOnServer(CmfFailure):
    def __init__(self, return_code=111):
        super().__init__(return_code)

    def handle(self):
        return "mlmd file not available on cmf-server."

class MlmdFilePulledSuccess(CmfSuccess):
    def __init__(self,full_path_to_dump, return_code=204):
        self.full_path_to_dump = full_path_to_dump
        super().__init__(return_code)

    def handle(self):
        return f"SUCCESS: {self.full_path_to_dump} is successfully pulled."
    
class MlmdFilePushedSuccess(CmfSuccess):
    def __init__(self, return_code=205):
        super().__init__(return_code)
    
    @staticmethod
    def handle():
        return f"mlmd is successfully pushed."


    
class UpdateCmfVersion(CmfFailure):
    def __init__(self, return_code=112):
        super().__init__(return_code)

    def handle(self):
        return "ERROR: You need to update cmf to the latest version. Unable to push metadata file."

class MlmdAndTensorboardPushSuccess(CmfSuccess):
    def __init__(self, tensorboard_file_name:str = "All", return_code=206):
        self.tensorboard_file_name = tensorboard_file_name
        super().__init__(return_code)

    def handle(self):
        if self.tensorboard_file_name == "All":
            return f"tensorboard logs: files pushed successfully" 
        return f"tensorboard logs: file {self.tensorboard_file_push_message} pushed successfully" 
    
class MlmdAndTensorboardPushFailure(CmfFailure):
    def __init__(self,tensorboard_file_name,response_text, return_code=113):
        self.tensorboard_file_name = tensorboard_file_name
        self.response_text = response_text
        super().__init__(return_code)

    def handle(self):
        return f"ERROR: Failed to upload file {self.file_name}. Server response: {self.response_text}"


class ArgumentNotProvided(CmfFailure):
    def __init__(self, return_code=114):
        super().__init__(return_code)

    def handle(self):
        return "ERROR: Provide user, password and uri for neo4j initialization."

class CmfInitFailed(CmfFailure):
    def __init__(self, return_code=115):
        super().__init__(return_code)

    def handle(self):
        return "cmf init failed."

class CmfInitComplete(CmfSuccess):
    def __init__(self, return_code=207):
        super().__init__(return_code)

    def handle(self):
        return "cmf init complete."

class CmfInitShow(CmfSuccess):
    def __init__(self,result, attr_str, return_code=208):
        self.result = result
        self.attr_str = attr_str
        super().__init__(return_code)

    def handle(self):
        return f"{self.result}\n{self.attr_str}"

class CmfServerNotAvailable(CmfFailure):
    def __init__(self, return_code=116):
        super().__init__(return_code)

    def handle(self):
        return "ERROR: cmf-server is not available."

class InternalServerError(CmfFailure):
    def __init__(self, return_code=117):
        super().__init__(return_code)

    def handle(self):
        return "ERROR: Internal server error."

class MlmdFilePulledFailure(CmfFailure):
    def __init__(self, return_code=204):
        super().__init__(return_code)

    def handle(self):
        return "ERROR: Unable to pull mlmd."

class CurrentDirectoryNotfound(CmfFailure):
    def __init__(self,current_dir, return_code=118):
        self.current_dir = current_dir
        super().__init__(return_code)

    def handle(self):
        return f"{self.current_dir} doesn't exists."

class FileNameNotfound(CmfFailure):
    def __init__(self, return_code=119):
        super().__init__(return_code)

    def handle(self):
        return "Provide path with file name."

class NoDataFoundOsdf(CmfFailure):
    def __init__(self, return_code=120):
        super().__init__(return_code)

    def handle(self):
        return "No data received from the server."

class InvalidTensorboardFilePath(CmfFailure):
    def __init__(self, return_code=121):
        super().__init__(return_code)

    def handle(self):
        return "ERROR: Invalid data path. Provide valid file/folder path for tensorboard logs!!"

class ArtifactPushSuccess(CmfSuccess):
    def __init__(self, message, return_code=205):
        self.message = message
        super().__init__(return_code)

    def handle(self):
        return self.message
