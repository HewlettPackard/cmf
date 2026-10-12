"""
Unit tests for PostgreSQL store implementation.

Tests PostgreSQL configuration, initialization, and connection management.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from ml_metadata.proto import metadata_store_pb2 as mlpb
from ml_metadata.metadata_store import metadata_store

from cmflib.store.postgres import PostgresStore


class TestPostgresStoreInitialization:
    """Test suite for PostgresStore initialization."""
    
    @patch('cmflib.store.postgres.metadata_store.MetadataStore')
    def test_init_with_valid_config(self, mock_metadata_store):
        """Test PostgresStore initialization with valid configuration."""
        config = {
            "host": "localhost",
            "port": 5432,
            "user": "postgres",
            "password": "admin",
            "dbname": "cmf_db"
        }
        
        store = PostgresStore(config)
        
        # Verify config was stored
        assert store.connection_config is not None
        assert store.connection_config.postgresql.host == "localhost"
        assert store.connection_config.postgresql.port == 5432
        assert store.connection_config.postgresql.user == "postgres"
        assert store.connection_config.postgresql.password == "admin"
        assert store.connection_config.postgresql.dbname == "cmf_db"
    
    @patch('cmflib.store.postgres.metadata_store.MetadataStore')
    def test_init_with_different_host(self, mock_metadata_store):
        """Test initialization with different hostnames."""
        hosts = [
            "127.0.0.1",
            "192.168.1.1",
            "db.example.com",
            "postgresql.internal.company.com"
        ]
        
        for host in hosts:
            config = {
                "host": host,
                "port": 5432,
                "user": "postgres",
                "password": "admin",
                "dbname": "cmf_db"
            }
            store = PostgresStore(config)
            assert store.connection_config.postgresql.host == host
    
    @patch('cmflib.store.postgres.metadata_store.MetadataStore')
    def test_init_with_different_ports(self, mock_metadata_store):
        """Test initialization with different port numbers."""
        ports = [5432, 5433, 3306, 1234, 65535]
        
        for port in ports:
            config = {
                "host": "localhost",
                "port": port,
                "user": "postgres",
                "password": "admin",
                "dbname": "cmf_db"
            }
            store = PostgresStore(config)
            assert store.connection_config.postgresql.port == port
    
    @patch('cmflib.store.postgres.metadata_store.MetadataStore')
    def test_init_with_complex_password(self, mock_metadata_store):
        """Test initialization with complex password containing special characters."""
        passwords = [
            "simple123",
            "p@ss!word#2024",
            "pässwörd",
            "数据库密码",
            "p\"quote'apostrophe"
        ]
        
        for password in passwords:
            config = {
                "host": "localhost",
                "port": 5432,
                "user": "postgres",
                "password": password,
                "dbname": "cmf_db"
            }
            store = PostgresStore(config)
            assert store.connection_config.postgresql.password == password
    
    @patch('cmflib.store.postgres.metadata_store.MetadataStore')
    def test_init_with_database_names(self, mock_metadata_store):
        """Test initialization with various database names."""
        dbnames = [
            "cmf_db",
            "cmf",
            "metadata_store",
            "db_with_underscores",
            "db-with-hyphens"
        ]
        
        for dbname in dbnames:
            config = {
                "host": "localhost",
                "port": 5432,
                "user": "postgres",
                "password": "admin",
                "dbname": dbname
            }
            store = PostgresStore(config)
            assert store.connection_config.postgresql.dbname == dbname


class TestPostgresStoreConfigValidation:
    """Test suite for PostgreSQL configuration validation."""
    
    def test_init_with_missing_host(self):
        """Test initialization with missing host key."""
        config = {
            "port": 5432,
            "user": "postgres",
            "password": "admin",
            "dbname": "cmf_db"
        }
        
        with pytest.raises(KeyError, match="host"):
            PostgresStore(config)
    
    def test_init_with_missing_port(self):
        """Test initialization with missing port key."""
        config = {
            "host": "localhost",
            "user": "postgres",
            "password": "admin",
            "dbname": "cmf_db"
        }
        
        with pytest.raises(KeyError, match="port"):
            PostgresStore(config)
    
    def test_init_with_missing_user(self):
        """Test initialization with missing user key."""
        config = {
            "host": "localhost",
            "port": 5432,
            "password": "admin",
            "dbname": "cmf_db"
        }
        
        with pytest.raises(KeyError, match="user"):
            PostgresStore(config)
    
    def test_init_with_missing_password(self):
        """Test initialization with missing password key."""
        config = {
            "host": "localhost",
            "port": 5432,
            "user": "postgres",
            "dbname": "cmf_db"
        }
        
        with pytest.raises(KeyError, match="password"):
            PostgresStore(config)
    
    def test_init_with_missing_dbname(self):
        """Test initialization with missing dbname key."""
        config = {
            "host": "localhost",
            "port": 5432,
            "user": "postgres",
            "password": "admin"
        }
        
        with pytest.raises(KeyError, match="dbname"):
            PostgresStore(config)
    
    def test_init_with_empty_config(self):
        """Test initialization with empty configuration."""
        config = {}
        
        with pytest.raises(KeyError):
            PostgresStore(config)
    
    def test_init_with_none_config_values(self):
        """Test initialization with None values in config."""
        config = {
            "host": None,
            "port": 5432,
            "user": "postgres",
            "password": "admin",
            "dbname": "cmf_db"
        }
        
        store = PostgresStore(config)
        assert store.connection_config.postgresql.host is None


class TestPostgresStoreConnection:
    """Test suite for PostgreSQL store connection."""
    
    @patch('cmflib.store.postgres.metadata_store.MetadataStore')
    def test_connect_returns_metadata_store(self, mock_metadata_store):
        """Test that connect method returns MetadataStore instance."""
        config = {
            "host": "localhost",
            "port": 5432,
            "user": "postgres",
            "password": "admin",
            "dbname": "cmf_db"
        }
        
        mock_store_instance = Mock()
        mock_metadata_store.return_value = mock_store_instance
        
        store = PostgresStore(config)
        result = store.connect()
        
        # Verify MetadataStore was called with connection config
        mock_metadata_store.assert_called_once()
        assert result == mock_store_instance
    
    @patch('cmflib.store.postgres.metadata_store.MetadataStore')
    def test_connect_uses_connection_config(self, mock_metadata_store):
        """Test that connect uses the properly configured connection_config."""
        config = {
            "host": "db.example.com",
            "port": 5433,
            "user": "admin",
            "password": "secret",
            "dbname": "production_db"
        }
        
        mock_store_instance = Mock()
        mock_metadata_store.return_value = mock_store_instance
        
        store = PostgresStore(config)
        store.connect()
        
        # Verify the connection config passed to MetadataStore
        call_args = mock_metadata_store.call_args
        passed_config = call_args[0][0]
        
        assert passed_config.postgresql.host == "db.example.com"
        assert passed_config.postgresql.port == 5433
        assert passed_config.postgresql.user == "admin"
        assert passed_config.postgresql.password == "secret"
        assert passed_config.postgresql.dbname == "production_db"
    
    @patch('cmflib.store.postgres.metadata_store.MetadataStore')
    def test_connect_exception_handling(self, mock_metadata_store):
        """Test connect method when MetadataStore raises exception."""
        config = {
            "host": "localhost",
            "port": 5432,
            "user": "postgres",
            "password": "admin",
            "dbname": "cmf_db"
        }
        
        mock_metadata_store.side_effect = Exception("Connection failed")
        store = PostgresStore(config)
        
        with pytest.raises(Exception, match="Connection failed"):
            store.connect()


class TestPostgresStoreEdgeCases:
    """Test suite for PostgreSQL store edge cases."""
    
    @patch('cmflib.store.postgres.metadata_store.MetadataStore')
    def test_init_with_empty_string_values(self, mock_metadata_store):
        """Test initialization with empty string values."""
        config = {
            "host": "",
            "port": 5432,
            "user": "",
            "password": "",
            "dbname": ""
        }
        
        store = PostgresStore(config)
        assert store.connection_config.postgresql.host == ""
        assert store.connection_config.postgresql.user == ""
        assert store.connection_config.postgresql.password == ""
        assert store.connection_config.postgresql.dbname == ""
    
    @patch('cmflib.store.postgres.metadata_store.MetadataStore')
    def test_init_with_long_strings(self, mock_metadata_store):
        """Test initialization with very long configuration values."""
        long_password = "p" * 1000
        long_dbname = "d" * 500
        
        config = {
            "host": "localhost",
            "port": 5432,
            "user": "postgres",
            "password": long_password,
            "dbname": long_dbname
        }
        
        store = PostgresStore(config)
        assert len(store.connection_config.postgresql.password) == 1000
        assert len(store.connection_config.postgresql.dbname) == 500
    
    @patch('cmflib.store.postgres.metadata_store.MetadataStore')
    def test_init_with_zero_port(self, mock_metadata_store):
        """Test initialization with port 0."""
        config = {
            "host": "localhost",
            "port": 0,
            "user": "postgres",
            "password": "admin",
            "dbname": "cmf_db"
        }
        
        store = PostgresStore(config)
        assert store.connection_config.postgresql.port == 0
    
    @patch('cmflib.store.postgres.metadata_store.MetadataStore')
    def test_init_with_negative_port(self, mock_metadata_store):
        """Test initialization with negative port number."""
        config = {
            "host": "localhost",
            "port": -1,
            "user": "postgres",
            "password": "admin",
            "dbname": "cmf_db"
        }
        
        store = PostgresStore(config)
        assert store.connection_config.postgresql.port == -1
    
    @patch('cmflib.store.postgres.metadata_store.MetadataStore')
    def test_init_with_ipv6_host(self, mock_metadata_store):
        """Test initialization with IPv6 host address."""
        config = {
            "host": "::1",
            "port": 5432,
            "user": "postgres",
            "password": "admin",
            "dbname": "cmf_db"
        }
        
        store = PostgresStore(config)
        assert store.connection_config.postgresql.host == "::1"
    
    @patch('cmflib.store.postgres.metadata_store.MetadataStore')
    def test_init_with_sql_injection_like_strings(self, mock_metadata_store):
        """Test initialization with SQL injection-like strings in config."""
        config = {
            "host": "localhost'; DROP TABLE users; --",
            "port": 5432,
            "user": "postgres",
            "password": "admin' OR '1'='1",
            "dbname": "cmf_db"
        }
        
        store = PostgresStore(config)
        # Should store as-is (no validation at this level)
        assert "DROP TABLE" in store.connection_config.postgresql.host
        assert "OR" in store.connection_config.postgresql.password
    
    @patch('cmflib.store.postgres.metadata_store.MetadataStore')
    def test_init_with_unicode_in_config(self, mock_metadata_store):
        """Test initialization with Unicode characters."""
        config = {
            "host": "localhost",
            "port": 5432,
            "user": "用户",
            "password": "пароль",
            "dbname": "قاعدة_البيانات"
        }
        
        store = PostgresStore(config)
        assert store.connection_config.postgresql.user == "用户"
        assert store.connection_config.postgresql.password == "пароль"
        assert store.connection_config.postgresql.dbname == "قاعدة_البيانات"


class TestPostgresStoreMultipleInstances:
    """Test suite for multiple PostgreSQL store instances."""
    
    @patch('cmflib.store.postgres.metadata_store.MetadataStore')
    def test_multiple_stores_independent_configs(self, mock_metadata_store):
        """Test multiple PostgresStore instances with different configs."""
        config1 = {
            "host": "localhost",
            "port": 5432,
            "user": "user1",
            "password": "pass1",
            "dbname": "db1"
        }
        
        config2 = {
            "host": "remote.example.com",
            "port": 5433,
            "user": "user2",
            "password": "pass2",
            "dbname": "db2"
        }
        
        store1 = PostgresStore(config1)
        store2 = PostgresStore(config2)
        
        assert store1.connection_config.postgresql.host == "localhost"
        assert store2.connection_config.postgresql.host == "remote.example.com"
        assert store1.connection_config.postgresql.dbname == "db1"
        assert store2.connection_config.postgresql.dbname == "db2"
    
    @patch('cmflib.store.postgres.metadata_store.MetadataStore')
    def test_store_instances_dont_share_state(self, mock_metadata_store):
        """Test that multiple store instances don't share state."""
        config1 = {
            "host": "localhost",
            "port": 5432,
            "user": "postgres",
            "password": "admin",
            "dbname": "cmf_db"
        }
        
        config2 = {
            "host": "remote",
            "port": 5432,
            "user": "postgres",
            "password": "admin",
            "dbname": "cmf_db"
        }
        
        store1 = PostgresStore(config1)
        store2 = PostgresStore(config2)
        
        # Verify they are independent
        assert id(store1.connection_config) != id(store2.connection_config)
        assert store1.connection_config.postgresql.host != store2.connection_config.postgresql.host


class TestPostgresStoreInheritance:
    """Test suite for PostgreSQL store inheritance from CmfStore."""
    
    @patch('cmflib.store.postgres.metadata_store.MetadataStore')
    def test_inherits_from_cmfstore(self, mock_metadata_store):
        """Test that PostgresStore properly inherits from CmfStore."""
        config = {
            "host": "localhost",
            "port": 5432,
            "user": "postgres",
            "password": "admin",
            "dbname": "cmf_db"
        }
        
        store = PostgresStore(config)
        
        # Verify parent config is set
        assert hasattr(store, 'config')
        assert isinstance(store.config, mlpb.ConnectionConfig)
    
    @patch('cmflib.store.postgres.metadata_store.MetadataStore')
    def test_config_attribute_set_by_parent(self, mock_metadata_store):
        """Test that config attribute is properly set through parent class."""
        config = {
            "host": "localhost",
            "port": 5432,
            "user": "postgres",
            "password": "admin",
            "dbname": "cmf_db"
        }
        
        store = PostgresStore(config)
        
        # Parent __init__ should set config to connection_config
        assert store.config == store.connection_config
