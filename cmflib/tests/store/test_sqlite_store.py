"""
Unit tests for SQLite store implementation.

Tests SQLite configuration, initialization, file handling, and connection management.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, ANY
import tempfile
import os

from ml_metadata.proto import metadata_store_pb2 as mlpb
from ml_metadata.metadata_store import metadata_store

# Import from actual module (note: sqllite_store has a typo in the filename)
try:
    from cmflib.store.sqllite_store import SqlliteStore
except ImportError:
    from cmflib.store.sqlite_store import SqlliteStore


class TestSqliteStoreInitialization:
    """Test suite for SQLite store initialization."""
    
    @patch('cmflib.store.sqllite_store.metadata_store.MetadataStore')
    def test_init_with_valid_config(self, mock_metadata_store):
        """Test SqlliteStore initialization with valid configuration."""
        config = {"filename": "/path/to/database.db"}
        store = SqlliteStore(config)
        
        # Verify config was stored
        assert store.connection_config is not None
        assert store.connection_config.sqlite.filename_uri == "/path/to/database.db"
        assert store.connection_config.sqlite.connection_mode == 3  # READWRITE_OPENCREATE
    
    @patch('cmflib.store.sqllite_store.metadata_store.MetadataStore')
    def test_init_with_relative_path(self, mock_metadata_store):
        """Test initialization with relative file path."""
        config = {"filename": "cmf.db"}
        store = SqlliteStore(config)
        
        assert store.connection_config.sqlite.filename_uri == "cmf.db"
    
    @patch('cmflib.store.sqllite_store.metadata_store.MetadataStore')
    def test_init_with_absolute_path(self, mock_metadata_store):
        """Test initialization with absolute file path."""
        config = {"filename": "/var/lib/cmf/metadata.db"}
        store = SqlliteStore(config)
        
        assert store.connection_config.sqlite.filename_uri == "/var/lib/cmf/metadata.db"
    
    @patch('cmflib.store.sqllite_store.metadata_store.MetadataStore')
    def test_init_with_windows_path(self, mock_metadata_store):
        """Test initialization with Windows-style path."""
        config = {"filename": "C:\\Users\\cmf\\metadata.db"}
        store = SqlliteStore(config)
        
        assert store.connection_config.sqlite.filename_uri == "C:\\Users\\cmf\\metadata.db"
    
    @patch('cmflib.store.sqllite_store.metadata_store.MetadataStore')
    def test_init_with_different_filenames(self, mock_metadata_store):
        """Test initialization with various database filenames."""
        filenames = [
            "cmf.db",
            "metadata.sqlite",
            "metadata.sqlite3",
            "db_2024.db",
            "cmf_prod_db.sqlite"
        ]
        
        for filename in filenames:
            config = {"filename": filename}
            store = SqlliteStore(config)
            assert store.connection_config.sqlite.filename_uri == filename
    
    @patch('cmflib.store.sqllite_store.metadata_store.MetadataStore')
    def test_connection_mode_is_set_to_readwrite_opencreate(self, mock_metadata_store):
        """Test that connection mode is always set to READWRITE_OPENCREATE (3)."""
        config = {"filename": "test.db"}
        store = SqlliteStore(config)
        
        # Connection mode should always be 3 (READWRITE_OPENCREATE)
        assert store.connection_config.sqlite.connection_mode == 3


class TestSqliteStoreConfigValidation:
    """Test suite for SQLite configuration validation."""
    
    def test_init_with_missing_filename(self):
        """Test initialization with missing filename key."""
        config = {}
        
        with pytest.raises(KeyError, match="filename"):
            SqlliteStore(config)
    
    def test_init_with_none_filename(self):
        """Test initialization with None filename."""
        config = {"filename": None}
        store = SqlliteStore(config)
        
        assert store.connection_config.sqlite.filename_uri is None
    
    def test_init_with_empty_filename(self):
        """Test initialization with empty filename string."""
        config = {"filename": ""}
        store = SqlliteStore(config)
        
        assert store.connection_config.sqlite.filename_uri == ""
    
    def test_init_with_multiple_keys_ignores_extra(self):
        """Test that extra keys in config are ignored."""
        config = {
            "filename": "test.db",
            "extra_key": "extra_value",
            "another_key": 123
        }
        store = SqlliteStore(config)
        
        # Should only use filename key
        assert store.connection_config.sqlite.filename_uri == "test.db"


class TestSqliteStoreConnection:
    """Test suite for SQLite store connection."""
    
    @patch('cmflib.store.sqllite_store.metadata_store.MetadataStore')
    def test_connect_returns_metadata_store(self, mock_metadata_store):
        """Test that connect method returns MetadataStore instance."""
        config = {"filename": "test.db"}
        mock_store_instance = Mock()
        mock_metadata_store.return_value = mock_store_instance
        
        store = SqlliteStore(config)
        result = store.connect()
        
        # Verify MetadataStore was called
        mock_metadata_store.assert_called_once()
        assert result == mock_store_instance
    
    @patch('cmflib.store.sqllite_store.metadata_store.MetadataStore')
    def test_connect_uses_connection_config(self, mock_metadata_store):
        """Test that connect uses the properly configured connection_config."""
        config = {"filename": "/var/lib/cmf/metadata.db"}
        mock_store_instance = Mock()
        mock_metadata_store.return_value = mock_store_instance
        
        store = SqlliteStore(config)
        store.connect()
        
        # Verify the connection config passed to MetadataStore
        call_args = mock_metadata_store.call_args
        passed_config = call_args[0][0]
        
        assert passed_config.sqlite.filename_uri == "/var/lib/cmf/metadata.db"
        assert passed_config.sqlite.connection_mode == 3
    
    @patch('cmflib.store.sqllite_store.metadata_store.MetadataStore')
    def test_connect_exception_handling(self, mock_metadata_store):
        """Test connect method when MetadataStore raises exception."""
        config = {"filename": "test.db"}
        mock_metadata_store.side_effect = Exception("Database connection failed")
        store = SqlliteStore(config)
        
        with pytest.raises(Exception, match="Database connection failed"):
            store.connect()
    
    @patch('cmflib.store.sqllite_store.metadata_store.MetadataStore')
    def test_connect_with_readonly_path(self, mock_metadata_store):
        """Test connect with read-only file path."""
        config = {"filename": "/usr/share/cmf/metadata.db"}
        mock_store_instance = Mock()
        mock_metadata_store.return_value = mock_store_instance
        
        store = SqlliteStore(config)
        store.connect()
        
        # Should still try to connect even with read-only path
        mock_metadata_store.assert_called_once()


class TestSqliteStoreEdgeCases:
    """Test suite for SQLite store edge cases."""
    
    @patch('cmflib.store.sqllite_store.metadata_store.MetadataStore')
    def test_init_with_very_long_path(self, mock_metadata_store):
        """Test initialization with very long file path."""
        long_path = "/path/" + "subdir/" * 100 + "database.db"
        config = {"filename": long_path}
        store = SqlliteStore(config)
        
        assert store.connection_config.sqlite.filename_uri == long_path
        assert len(store.connection_config.sqlite.filename_uri) > 500
    
    @patch('cmflib.store.sqllite_store.metadata_store.MetadataStore')
    def test_init_with_special_characters_in_path(self, mock_metadata_store):
        """Test initialization with special characters in file path."""
        paths = [
            "/path/with spaces/database.db",
            "/path/with-dashes/db.db",
            "/path/with_underscores/database.db",
            "/path/with.dots/database.db",
            "/path/with(parens)/database.db",
            "/path/with[brackets]/database.db"
        ]
        
        for path in paths:
            config = {"filename": path}
            store = SqlliteStore(config)
            assert store.connection_config.sqlite.filename_uri == path
    
    @patch('cmflib.store.sqllite_store.metadata_store.MetadataStore')
    def test_init_with_unicode_in_path(self, mock_metadata_store):
        """Test initialization with Unicode characters in file path."""
        paths = [
            "/path/to/数据库/metadata.db",
            "/path/to/база_данных.db",
            "/path/to/قاعدة_البيانات.db",
            "/path/with_émojis/🗄️.db"
        ]
        
        for path in paths:
            config = {"filename": path}
            store = SqlliteStore(config)
            assert store.connection_config.sqlite.filename_uri == path
    
    @patch('cmflib.store.sqllite_store.metadata_store.MetadataStore')
    def test_init_with_sql_injection_like_filename(self, mock_metadata_store):
        """Test initialization with SQL injection-like filename."""
        config = {"filename": "'; DROP TABLE metadata; --.db"}
        store = SqlliteStore(config)
        
        # Should store as-is (URI path, not SQL)
        assert store.connection_config.sqlite.filename_uri == "'; DROP TABLE metadata; --.db"
    
    @patch('cmflib.store.sqllite_store.metadata_store.MetadataStore')
    def test_init_with_uri_format_filename(self, mock_metadata_store):
        """Test initialization with URI-format filename."""
        config = {"filename": "file:///path/to/database.db?mode=rw"}
        store = SqlliteStore(config)
        
        assert store.connection_config.sqlite.filename_uri == "file:///path/to/database.db?mode=rw"
    
    @patch('cmflib.store.sqllite_store.metadata_store.MetadataStore')
    def test_init_with_memory_database(self, mock_metadata_store):
        """Test initialization with in-memory SQLite database."""
        config = {"filename": ":memory:"}
        store = SqlliteStore(config)
        
        assert store.connection_config.sqlite.filename_uri == ":memory:"
    
    @patch('cmflib.store.sqllite_store.metadata_store.MetadataStore')
    def test_init_with_temporary_database(self, mock_metadata_store):
        """Test initialization with temporary SQLite database."""
        config = {"filename": ""}
        store = SqlliteStore(config)
        
        # Empty string typically means temporary database
        assert store.connection_config.sqlite.filename_uri == ""
    
    @patch('cmflib.store.sqllite_store.metadata_store.MetadataStore')
    def test_connection_mode_never_changes(self, mock_metadata_store):
        """Test that connection mode is always 3 regardless of config."""
        configs = [
            {"filename": "test.db"},
            {"filename": "/path/to/db.sqlite"},
            {"filename": ":memory:"},
            {"filename": ""}
        ]
        
        for config in configs:
            store = SqlliteStore(config)
            assert store.connection_config.sqlite.connection_mode == 3


class TestSqliteStoreMultipleInstances:
    """Test suite for multiple SQLite store instances."""
    
    @patch('cmflib.store.sqllite_store.metadata_store.MetadataStore')
    def test_multiple_stores_independent_configs(self, mock_metadata_store):
        """Test multiple SqlliteStore instances with different configs."""
        config1 = {"filename": "database1.db"}
        config2 = {"filename": "/var/lib/cmf/database2.db"}
        config3 = {"filename": ":memory:"}
        
        store1 = SqlliteStore(config1)
        store2 = SqlliteStore(config2)
        store3 = SqlliteStore(config3)
        
        assert store1.connection_config.sqlite.filename_uri == "database1.db"
        assert store2.connection_config.sqlite.filename_uri == "/var/lib/cmf/database2.db"
        assert store3.connection_config.sqlite.filename_uri == ":memory:"
    
    @patch('cmflib.store.sqllite_store.metadata_store.MetadataStore')
    def test_store_instances_dont_share_state(self, mock_metadata_store):
        """Test that multiple store instances don't share state."""
        config1 = {"filename": "db1.sqlite"}
        config2 = {"filename": "db2.sqlite"}
        
        store1 = SqlliteStore(config1)
        store2 = SqlliteStore(config2)
        
        # Verify they are independent
        assert id(store1.connection_config) != id(store2.connection_config)
        assert store1.connection_config.sqlite.filename_uri != store2.connection_config.sqlite.filename_uri


class TestSqliteStoreInheritance:
    """Test suite for SQLite store inheritance from CmfStore."""
    
    @patch('cmflib.store.sqllite_store.metadata_store.MetadataStore')
    def test_inherits_from_cmfstore(self, mock_metadata_store):
        """Test that SqlliteStore properly inherits from CmfStore."""
        config = {"filename": "test.db"}
        store = SqlliteStore(config)
        
        # Verify parent config is set
        assert hasattr(store, 'config')
        assert isinstance(store.config, mlpb.ConnectionConfig)
    
    @patch('cmflib.store.sqllite_store.metadata_store.MetadataStore')
    def test_config_attribute_set_by_parent(self, mock_metadata_store):
        """Test that config attribute is properly set through parent class."""
        config = {"filename": "test.db"}
        store = SqlliteStore(config)
        
        # Parent __init__ should set config to connection_config
        assert store.config == store.connection_config
    
    @patch('cmflib.store.sqllite_store.metadata_store.MetadataStore')
    def test_has_connect_method(self, mock_metadata_store):
        """Test that SqlliteStore has connect method from parent."""
        config = {"filename": "test.db"}
        store = SqlliteStore(config)
        
        assert hasattr(store, 'connect')
        assert callable(store.connect)


class TestSqliteStorePathHandling:
    """Test suite for SQLite file path handling."""
    
    @patch('cmflib.store.sqllite_store.metadata_store.MetadataStore')
    def test_path_with_trailing_slash(self, mock_metadata_store):
        """Test path with trailing slash."""
        config = {"filename": "/var/lib/cmf/"}
        store = SqlliteStore(config)
        
        assert store.connection_config.sqlite.filename_uri == "/var/lib/cmf/"
    
    @patch('cmflib.store.sqllite_store.metadata_store.MetadataStore')
    def test_path_with_dot_notation(self, mock_metadata_store):
        """Test path with dot notation (relative paths)."""
        config = {"filename": "./metadata.db"}
        store = SqlliteStore(config)
        
        assert store.connection_config.sqlite.filename_uri == "./metadata.db"
    
    @patch('cmflib.store.sqllite_store.metadata_store.MetadataStore')
    def test_path_with_double_dot_notation(self, mock_metadata_store):
        """Test path with double dot notation (parent directory)."""
        config = {"filename": "../data/metadata.db"}
        store = SqlliteStore(config)
        
        assert store.connection_config.sqlite.filename_uri == "../data/metadata.db"
    
    @patch('cmflib.store.sqllite_store.metadata_store.MetadataStore')
    def test_path_with_symlink_like_notation(self, mock_metadata_store):
        """Test path that could be a symlink."""
        config = {"filename": "/etc/cmf/links/database.db"}
        store = SqlliteStore(config)
        
        assert store.connection_config.sqlite.filename_uri == "/etc/cmf/links/database.db"
    
    @patch('cmflib.store.sqllite_store.metadata_store.MetadataStore')
    def test_home_directory_expansion_not_performed(self, mock_metadata_store):
        """Test that tilde (~) in path is stored as-is (not expanded)."""
        config = {"filename": "~/cmf/metadata.db"}
        store = SqlliteStore(config)
        
        # Tilde should be stored as-is (no expansion at this level)
        assert store.connection_config.sqlite.filename_uri == "~/cmf/metadata.db"


class TestSqliteStoreConnectionModeDetails:
    """Test suite for SQLite connection mode specifics."""
    
    @patch('cmflib.store.sqllite_store.metadata_store.MetadataStore')
    def test_readwrite_opencreate_mode_value(self, mock_metadata_store):
        """Test that connection mode is specifically READWRITE_OPENCREATE (3)."""
        config = {"filename": "test.db"}
        store = SqlliteStore(config)
        
        # READWRITE_OPENCREATE = 3
        # This mode allows:
        # - Reading from database
        # - Writing to database
        # - Creating database if it doesn't exist
        assert store.connection_config.sqlite.connection_mode == 3
    
    @patch('cmflib.store.sqllite_store.metadata_store.MetadataStore')
    def test_connection_mode_consistent_across_instances(self, mock_metadata_store):
        """Test that connection mode is consistent across all instances."""
        stores = [
            SqlliteStore({"filename": f"db{i}.sqlite"})
            for i in range(5)
        ]
        
        for store in stores:
            assert store.connection_config.sqlite.connection_mode == 3
