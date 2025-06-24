#from cmfstore import CmfStore
from cmflib.store.cmfstore import CmfStore
from ml_metadata.proto import metadata_store_pb2 as mlpb
from ml_metadata.metadata_store import metadata_store

class PostgresStore(CmfStore):

    def __init__(self, config):
        self.connection_config = mlpb.ConnectionConfig()
        self.connection_config.postgresql.host = config["host"]
        self.connection_config.postgresql.port = config["port"]
        self.connection_config.postgresql.user = config["user"]
        self.connection_config.postgresql.password = config["password"]
        self.connection_config.postgresql.dbname = config["dbname"]
        super().__init__(self.connection_config)

    def connect(self) -> metadata_store.MetadataStore:
        cmf_store = super().connect()
        return cmf_store

