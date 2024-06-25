from cmflib.store.cmfstore import CmfStore
from ml_metadata.metadata_store import metadata_store

class SqlliteStore(CmfStore):

    def __init__(self, config):

        self.connection_config = metadata_store.ConnectionConfig() 
        self.connection_config.sqlite.filename_uri = config["filename"]
        self.connection_config.connection_mode  = 3
        super().__init__(self.connection_config)

    def connect(self):
        super().connect()
