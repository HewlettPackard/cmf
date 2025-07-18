from cmflib.cmf_init import Cmf_init
import sys

cmf = Cmf_init()
_=cmf.cmf_init_show()

_ = cmf.cmf_init_local("/home/user/local-storage","https://github.com/user/experiment-repo.git","http://127.0.0.1")

#_ = cmf.cmf_init_sshremote("ssh://127.0.0.1/home/user/ssh-storage", "XXXXX","22","example@123","https://github.com/user/experiment-repo.git")
#,"http://127.0.0.1:8080", "neo4j ","password" ,"bolt://localhost:7687")

#_=cmf.cmf_init_local("/home/user/local-storage","https://github.com/user/experiment-repo.git","http://127.0.0.1:8080", "neo4j ","password" )
#,"bolt://localhost:7687")

#_=cmf.cmf_init_amazonS3("s3://bucket-name,"XXXXXXXXXXXXX","XXXXXXXXXXXXX","https://github.com/user/experiment-repo.git")

