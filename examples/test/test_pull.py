from cmflib import cmf
import os
from cmflib.cli.utils import find_root
from cmflib.utils.cmf_config import CmfConfig
import requests

def data_pull(pipeline_name,file_path=""):
    server=0

    cmfconfig = os.environ.get("CONFIG_FILE",".cmfconfig")

    # find root_dir of .cmfconfig
    output = find_root(cmfconfig)

    # in case, there is no .cmfconfig file
    if output.find("'cmf' is  not configured") != -1:
        return output

    config_file_path = os.path.join(output, cmfconfig)

    attr_dict = CmfConfig.read_config(config_file_path)
    url = attr_dict.get("cmf-server-ip", "http://127.0.0.1:80")
    try:
        server = requests.get(url)
        if server.status_code!=200:
            print("Server is down !")
            return 
    except:
        print("Server is down !")
        return 
    meta=cmf.metadata_pull(pipeline_name,file_path)
    if file_path=="":
        file_path="./mlmd"
    else:
        file_path=file_path+"/mlmd"
    arti=cmf.artifact_pull(pipeline_name,file_path)

    
if __name__ == '__main__':
    data_pull(pipeline_name="Test-env")
