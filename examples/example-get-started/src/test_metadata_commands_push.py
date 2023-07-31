from cmflib.cmf import Cmf
import os
from cmflib.cli.utils import find_root
from cmflib.utils.cmf_config import CmfConfig
import requests

def data_push(file_path,pipeline_name):
    server=0
    cmf = Cmf(file_path,pipeline_name)
    arti=cmf.artifact_push()
    
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
    meta=cmf.metadata_push()
    
if __name__ == '__main__':
    data_push("./mlmd",pipeline_name="active_learning")
