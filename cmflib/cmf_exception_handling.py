"""Exceptions raised by the CMF."""

class CmfException(Exception):
    """Base class for all dvc exceptions."""

    def __init__(self, return_code=None, *args):
        self.return_code = return_code
        super().__init__(*args)

class MissingRequiredArgument(CmfException):
    def __init__(self,pipeline_name,return_code=1):
        self.pipeline_name = pipeline_name 
        super().__init__(return_code)

    def handle(self):
        return f"Pipeline_name {self.pipeline_name} doesnt exist"
    
class FileNotFound(CmfException):
    def __init__(self,file_name,return_code=2):
        self.file_name =file_name
        super().__init__(return_code)
    
    def handle(self):
        return f"File Not Found: {self.file_name}"

class BucketNotFound(CmfException):
    def __init__(self,return_code=9):
        super().__init__(return_code)
 
    def handle(self):
        return f"Bucket doesnt exist"

class ExecutionsNotFound(CmfException):
    def __init__(self, return_code=6):
        super().__init__(return_code)
 
    def handle(self):
        return f"Executions not found"

class ArtifactNotFound(CmfException):
    def __init__(self,artifact_name, return_code=7):
        self.artifact_name = artifact_name
        super().__init__(return_code)
 
    def handle(self):
        return f"{self.artifact_name} not found"


class ObjectDownloadSuccess(CmfException):
    def __init__(self,temp_object_name,temp_download_loc, return_code=6):
        self.temp_object_name = temp_object_name
        self.temp_download_loc = temp_download_loc
        super().__init__(return_code)

    def handle(self):
        return f"object {self.temp_object_name} downloaded at {self.temp_download_loc}."
    
class Minios3ServerInactive(CmfException):
    def __init__(self,return_code=8):
        super().__init__(return_code)

    def handle(self):
        return f"MinioS3 server failed to start!!!"