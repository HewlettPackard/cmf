from abc import ABC, abstractmethod
from ml_metadata.metadata_store import metadata_store

class CmfStore(ABC):

    def __init__(self, config):
        self.config = config
        super().__init__()

    @abstractmethod
    def connect(self) -> metadata_store.MetadataStore:
        cmf_store = metadata_store.MetadataStore(self.config)
        return cmf_store
