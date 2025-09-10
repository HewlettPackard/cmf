import os
from cmflib import cmfquery,cmf
from cmflib.cli.utils import find_root
from cmflib.utils.cmf_config import CmfConfig
import requests

def data_push(file_path,pipeline_name):
    server=0
    query=cmfquery.CmfQuery(file_path)
    if pipeline_name in query.get_pipeline_names():
   
        cmfconfig = os.environ.get("CONFIG_FILE",".cmfconfig")

        # find root_dir of .cmfconfig
        output = find_root(cmfconfig)

        # in case, there is no .cmfconfig file
        if output.find("'cmf' is  not configured") != -1:
            return output

        config_file_path = os.path.join(output, cmfconfig)

        attr_dict = CmfConfig.read_config(config_file_path)
        url = attr_dict.get("cmf-server-url", "http://127.0.0.1:8080")

        try:
            server = requests.get(url)
            if server.status_code!=200:
                print("Server is down !")
                return 
        except:
            print("Server is down !")
            return 
        meta=cmf.metadata_push(pipeline_name,file_path)
        arti=cmf.artifact_push()
    else:
        print("Pipeline name "+pipeline_name+ " doesn't exists.")    
if __name__ == '__main__':
    data_push("./mlmd",pipeline_name="Test-env")
