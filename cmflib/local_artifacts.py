import os
from dvc.api import DVCFileSystem


class local_artifacts:
    def download_artifacts(
        self, current_directory: str, current_dvc_loc: str, download_loc: str
    ):
        obj = True
        try:
            fs = DVCFileSystem("/tmp/cmf/example_get_started/dvc_remote")
            temp = download_loc.split("/")
            temp.pop()
            dir_path = "/".join(temp)
            dir_to_create = os.path.join(current_directory, dir_path)
            os.makedirs(dir_to_create, mode=0o777, exist_ok=True)
            obj = fs.get_file(current_dvc_loc, download_loc)
            if obj == None:
                stmt = f"object {current_dvc_loc} downloaded at {download_loc}."
                return stmt

        except TypeError as exception:
            return f"Check if 'config' file present in .dvc/config. {exception}"
        except Exception as exception:
            return f"This is exception {exception}"
