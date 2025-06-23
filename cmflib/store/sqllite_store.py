from cmflib.store.cmfstore import CmfStore
from ml_metadata.metadata_store import metadata_store
from ml_metadata.proto import metadata_store_pb2 as mlpb

class SqlliteStore(CmfStore):

    def __init__(self, config):

        self.connection_config = mlpb.ConnectionConfig()
        self.connection_config.sqlite.filename_uri = config["filename"]
        self.connection_config.sqlite.connection_mode  = 3 # READWRITE_OPENCREATE
        super().__init__(self.connection_config)

    def connect(self) -> metadata_store.MetadataStore:
        cmf_store = super().connect()
        return cmf_store

