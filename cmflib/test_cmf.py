import pytest
from cmflib import cmf	

class TestClass:
    def test_cmf_init_show(self):
        #with pytest.raises(SystemExit):
        _=cmf.cmf_init_show()
  
    def test_cmf_init_local(self):
        _=cmf.cmf_init(type="locl",path="/home/chobey/local-storage",git_remote_url="https://github.com",neo4j_user='neo4j',neo4j_password="neo4j")

    def test_cmf_init_minios3(self):
        _=cmf.cmf_init(type="minioS3",url="http://localhost",endpoint_url="https://github.com",access_key_id='xxxxxxxx',secret_key_id="neo4j",git_remote_url="https://github.com")

    def test_cmf_init_amazonS3(self):
        _=cmf.cmf_init(type="amazonS3",path="/home/chobey/local-storage",git_remote_url="https://github.com")

    def test_cmf_init_sshremote(self):
        _=cmf.cmf_init(type="sshremote",path="/home/chobey/local-storage",git_remote_url="https://github.com")

