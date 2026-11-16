"""
Pytest configuration and fixtures for CMF tests.

This module sets up mocking for external dependencies (ml_metadata, pandas, dvc, etc.)
that may not be installed in the test environment.

Note: Some dependency mocks may be duplicated with an earlier PR's conftest.py.
Keep only what's essential for cmf.py imports and ml_metadata setup.
"""

import sys
from types import ModuleType
from unittest.mock import MagicMock

# Mock external dependencies that cmf.py imports directly
sys.modules['pandas'] = MagicMock()
sys.modules['neo4j'] = MagicMock()
sys.modules['neo4j.driver'] = MagicMock()
sys.modules['dvc'] = MagicMock()
sys.modules['dvc.api'] = MagicMock()
sys.modules['dvc.repo'] = MagicMock()
sys.modules['dvc.exceptions'] = MagicMock()
sys.modules['git'] = MagicMock()
sys.modules['git.repo'] = MagicMock()
sys.modules['readchar'] = MagicMock()
sys.modules['boto3'] = MagicMock()
sys.modules['paramiko'] = MagicMock()
sys.modules['ray'] = MagicMock()
sys.modules['pyarrow'] = MagicMock()
sys.modules['tabulate'] = MagicMock()
sys.modules['click'] = MagicMock()


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


# ContextualMagicMock for flexible protobuf object mocking
class ContextualMagicMock(MagicMock):
    """MagicMock that returns new MagicMocks for any attribute access."""
    def __getattr__(self, name):
        if name.startswith('_'):
            return super().__getattr__(name)
        return MagicMock()


# Create mock ml_metadata modules using ModuleType
ml_metadata_pb2_module = ModuleType('metadata_store_pb2')
ml_metadata_pb2_module.ConnectionConfig = MockConnectionConfig

# Add protobuf object mocks
ml_metadata_pb2_module.Context = ContextualMagicMock()
ml_metadata_pb2_module.Execution = ContextualMagicMock()
ml_metadata_pb2_module.Artifact = ContextualMagicMock()
ml_metadata_pb2_module.Event = ContextualMagicMock()
ml_metadata_pb2_module.Attribution = ContextualMagicMock()
ml_metadata_pb2_module.Association = ContextualMagicMock()
ml_metadata_pb2_module.Value = ContextualMagicMock()
ml_metadata_pb2_module.Property = ContextualMagicMock()
ml_metadata_pb2_module.PropertyType = ContextualMagicMock()
ml_metadata_pb2_module.ArtifactType = ContextualMagicMock()
ml_metadata_pb2_module.ExecutionType = ContextualMagicMock()
ml_metadata_pb2_module.ContextType = ContextualMagicMock()

# Add constants that may be referenced
ml_metadata_pb2_module.STRING = 1
ml_metadata_pb2_module.INT = 2
ml_metadata_pb2_module.DOUBLE = 3

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
