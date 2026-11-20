"""
Unit tests for abstract CmfStore class.

Tests the abstract store interface, initialization, and contract validation.
"""

import pytest
from abc import ABC, abstractmethod
from unittest.mock import Mock, MagicMock, patch
from ml_metadata.metadata_store import metadata_store

from cmflib.store.cmfstore import CmfStore


class ConcreteCmfStore(CmfStore):
    """Concrete implementation of CmfStore for testing."""
    
    def connect(self):
        """Implement abstract connect method."""
        return super().connect()


class TestCmfStoreInitialization:
    """Test suite for CmfStore initialization."""
    
    def test_init_with_valid_config(self):
        """Test CmfStore initialization with valid configuration."""
        config = {"host": "localhost", "port": 5432}
        store = ConcreteCmfStore(config)
        
        assert store.config == config
        assert isinstance(store, ABC)
    
    def test_init_with_empty_config(self):
        """Test CmfStore initialization with empty configuration."""
        config = {}
        store = ConcreteCmfStore(config)
        
        assert store.config == {}
    
    def test_init_with_none_config(self):
        """Test CmfStore initialization with None configuration."""
        config = None
        store = ConcreteCmfStore(config)
        
        assert store.config is None
    
    def test_init_with_complex_config(self):
        """Test CmfStore initialization with complex nested configuration."""
        config = {
            "host": "localhost",
            "port": 5432,
            "database": {"name": "cmf_db", "version": "1.0"},
            "credentials": {"user": "admin", "password": "secret"}
        }
        store = ConcreteCmfStore(config)
        
        assert store.config == config
        assert store.config["database"]["name"] == "cmf_db"
        assert store.config["credentials"]["user"] == "admin"
    
    def test_init_with_special_characters_in_config(self):
        """Test CmfStore initialization with special characters in config values."""
        config = {
            "password": "p@ss!w0rd#123",
            "path": "/var/lib/cmf/data",
            "description": "Test store with ü, ö, ü special chars"
        }
        store = ConcreteCmfStore(config)
        
        assert store.config == config


class TestCmfStoreAbstractMethods:
    """Test suite for CmfStore abstract methods."""
    
    def test_connect_is_abstract(self):
        """Test that connect method must be implemented by subclasses."""
        # Verify connect is an abstract method
        assert hasattr(CmfStore.connect, '__isabstractmethod__')
        assert CmfStore.connect.__isabstractmethod__
    
    def test_cannot_instantiate_abstract_class(self):
        """Test that CmfStore cannot be instantiated directly."""
        # Try to instantiate the abstract class directly
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            CmfStore({"host": "localhost"})
    
    @patch('cmflib.store.cmfstore.metadata_store.MetadataStore')
    def test_connect_returns_metadata_store(self, mock_metadata_store):
        """Test that connect method returns MetadataStore instance."""
        mock_store_instance = Mock()
        mock_metadata_store.return_value = mock_store_instance
        
        config = {"host": "localhost"}
        store = ConcreteCmfStore(config)
        result = store.connect()
        
        # Verify MetadataStore was called with config
        mock_metadata_store.assert_called_once_with(config)
        assert result == mock_store_instance


class TestCmfStoreSubclassContract:
    """Test suite for CmfStore subclass contract validation."""
    
    def test_subclass_must_implement_connect(self):
        """Test that subclass must implement connect method."""
        class IncompleteStore(CmfStore):
            """Store without connect implementation."""
            pass
        
        # Should not be able to instantiate without implementing abstract method
        with pytest.raises(TypeError):
            IncompleteStore({"host": "localhost"})
    
    def test_subclass_can_override_init(self):
        """Test that subclass can override __init__ method."""
        class CustomStore(CmfStore):
            def __init__(self, config, extra_param=None):
                self.extra_param = extra_param
                super().__init__(config)
            
            def connect(self):
                return super().connect()
        
        config = {"host": "localhost"}
        store = CustomStore(config, extra_param="test_value")
        
        assert store.config == config
        assert store.extra_param == "test_value"
    
    @patch('cmflib.store.cmfstore.metadata_store.MetadataStore')
    def test_subclass_connect_calls_super(self, mock_metadata_store):
        """Test that subclass connect method can call parent implementation."""
        mock_store_instance = Mock()
        mock_metadata_store.return_value = mock_store_instance
        
        class CustomStore(CmfStore):
            def connect(self):
                # Custom logic before calling parent
                result = super().connect()
                # Custom logic after calling parent
                return result
        
        config = {"host": "localhost"}
        store = CustomStore(config)
        result = store.connect()
        
        assert result == mock_store_instance


class TestCmfStoreEdgeCases:
    """Test suite for CmfStore edge cases."""
    
    def test_config_with_none_values(self):
        """Test CmfStore initialization with None values in config."""
        config = {"host": None, "port": None, "user": None}
        store = ConcreteCmfStore(config)
        
        assert store.config == config
        assert store.config["host"] is None
    
    def test_config_with_boolean_values(self):
        """Test CmfStore initialization with boolean config values."""
        config = {
            "ssl_enabled": True,
            "autocommit": False,
            "debug": True
        }
        store = ConcreteCmfStore(config)
        
        assert store.config == config
        assert store.config["ssl_enabled"] is True
        assert store.config["autocommit"] is False
    
    def test_config_with_numeric_values(self):
        """Test CmfStore initialization with numeric config values."""
        config = {
            "port": 5432,
            "max_connections": 100,
            "timeout": 30.5,
            "retries": 0
        }
        store = ConcreteCmfStore(config)
        
        assert store.config == config
        assert isinstance(store.config["port"], int)
        assert isinstance(store.config["timeout"], float)
    
    def test_config_with_list_values(self):
        """Test CmfStore initialization with list values in config."""
        config = {
            "hosts": ["localhost", "127.0.0.1", "example.com"],
            "ports": [5432, 5433, 5434],
            "empty_list": []
        }
        store = ConcreteCmfStore(config)
        
        assert store.config == config
        assert len(store.config["hosts"]) == 3
        assert store.config["empty_list"] == []
    
    def test_config_immutability_concern(self):
        """Test that config object is stored as reference (not copied)."""
        config = {"host": "localhost", "port": 5432}
        store = ConcreteCmfStore(config)
        
        # Modify original config
        config["port"] = 5433
        
        # Store should reflect the change (shallow copy behavior)
        assert store.config["port"] == 5433
    
    def test_very_long_config_values(self):
        """Test CmfStore with very long string config values."""
        long_password = "p" * 10000
        very_long_description = "d" * 50000
        
        config = {
            "password": long_password,
            "description": very_long_description
        }
        store = ConcreteCmfStore(config)
        
        assert len(store.config["password"]) == 10000
        assert len(store.config["description"]) == 50000
    
    def test_config_with_unicode_characters(self):
        """Test CmfStore with Unicode characters in config."""
        config = {
            "description": "测试中文 тест العربية",
            "path": "/var/lib/cmf/数据库",
            "password": "pässwörd"
        }
        store = ConcreteCmfStore(config)
        
        assert store.config == config
        assert "测试中文" in store.config["description"]


class TestCmfStoreMultipleInstances:
    """Test suite for multiple CmfStore instances."""
    
    def test_multiple_instances_with_different_configs(self):
        """Test creating multiple CmfStore instances with different configs."""
        config1 = {"host": "localhost", "port": 5432}
        config2 = {"host": "remote.example.com", "port": 5432}
        
        store1 = ConcreteCmfStore(config1)
        store2 = ConcreteCmfStore(config2)
        
        assert store1.config != store2.config
        assert store1.config["host"] == "localhost"
        assert store2.config["host"] == "remote.example.com"
    
    def test_multiple_instances_isolation(self):
        """Test that multiple instances don't interfere with each other."""
        config1 = {"host": "localhost"}
        config2 = {"host": "remote"}
        
        store1 = ConcreteCmfStore(config1)
        store2 = ConcreteCmfStore(config2)
        
        # Modify config1's dict
        config1["port"] = 5432
        
        # store1 should be affected (reference), but store2 should not
        assert "port" in store1.config
        assert "port" not in store2.config
