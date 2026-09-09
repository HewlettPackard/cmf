"""
Pytest configuration and fixtures for CMF tests.

This module sets up mocking for external dependencies like ml_metadata
that may not be installed in the test environment.
"""

import sys
from types import ModuleType
from unittest.mock import MagicMock

# Create a proper ConnectionConfig class that can be used with isinstance
class MockConnectionConfig:
    """Mock ConnectionConfig that behaves like a real config object."""
    def __init__(self):
        # Create separate MagicMock objects for each instance
        # to ensure they don't share state
        self.sqlite = MagicMock()
        self.sqlite.filename_uri = None
        self.sqlite.connection_mode = None
        self.postgresql = MagicMock()
        self.postgresql.host = None
        self.postgresql.port = None
        self.postgresql.user = None
        self.postgresql.password = None
        self.postgresql.dbname = None

# Create mock modules using ModuleType for better control
ml_metadata_pb2_module = ModuleType('metadata_store_pb2')
ml_metadata_pb2_module.ConnectionConfig = MockConnectionConfig

# Create the metadata_store sub-module
metadata_store_submodule = ModuleType('metadata_store')
metadata_store_submodule.MetadataStore = MagicMock()

# Create the ml_metadata.metadata_store package/module
ml_metadata_store_module = ModuleType('metadata_store')
ml_metadata_store_module.metadata_store = metadata_store_submodule
ml_metadata_store_module.MetadataStore = MagicMock()

ml_metadata_proto_module = ModuleType('proto')
ml_metadata_proto_module.metadata_store_pb2 = ml_metadata_pb2_module

ml_metadata_module = ModuleType('ml_metadata')
ml_metadata_module.proto = ml_metadata_proto_module
ml_metadata_module.metadata_store = ml_metadata_store_module

# Register modules in sys.modules
sys.modules['ml_metadata'] = ml_metadata_module
sys.modules['ml_metadata.proto'] = ml_metadata_proto_module
sys.modules['ml_metadata.proto.metadata_store_pb2'] = ml_metadata_pb2_module
sys.modules['ml_metadata.metadata_store'] = ml_metadata_store_module
sys.modules['ml_metadata.metadata_store.metadata_store'] = metadata_store_submodule






