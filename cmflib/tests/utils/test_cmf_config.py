import pytest
import configparser
import base64
import tempfile
import os
from cmflib.utils.cmf_config import CmfConfig


@pytest.fixture
def temp_config_file():
    """Fixture to create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        file_path = temp_file.name
    
    yield file_path
    
    # Cleanup after test
    if os.path.exists(file_path):
        os.unlink(file_path)


def test_write_config_new_file(temp_config_file):
    """Test writing configurations to a new file."""
    # Define section and attributes
    section_name = "cmf"
    dict_of_attr = {"server-url": "http://example.com", "storage-type": "local"}
    
    # Write config to the new file
    CmfConfig.write_config(temp_config_file, section_name, dict_of_attr)
    
    # Read and verify the file
    config = configparser.ConfigParser()
    with open(temp_config_file, "r") as f:
        config.read_file(f)
    
    # Verify section and values
    assert config.has_section(section_name)
    assert config.get(section_name, "server-url") == "http://example.com"
    assert config.get(section_name, "storage-type") == "local"


def test_write_config_update_existing(temp_config_file):
    """Test updating an existing config file."""
    # First create a file with initial content
    section_name = "cmf"
    dict_of_attr = {"server-url": "http://example.com", "storage-type": "local"}
    CmfConfig.write_config(temp_config_file, section_name, dict_of_attr)
    
    # Now update with a new section
    new_section = "custom"
    new_attrs = {"key1": "value1", "key2": "value2"}
    CmfConfig.write_config(temp_config_file, new_section, new_attrs, file_exists=True)
    
    # Read and verify
    updated_config = configparser.ConfigParser()
    with open(temp_config_file, "r") as f:
        updated_config.read_file(f)
    
    # Check original section remains
    assert updated_config.has_section("cmf")
    assert updated_config.get("cmf", "server-url") == "http://example.com"
    
    # Check new section was added
    assert updated_config.has_section(new_section)
    assert updated_config.get(new_section, "key1") == "value1"
    assert updated_config.get(new_section, "key2") == "value2"


def test_write_config_overwrite_section(temp_config_file):
    """Test overwriting an existing section."""
    # First create a file with initial content
    section_name = "cmf"
    dict_of_attr = {"server-url": "http://example.com", "storage-type": "local"}
    CmfConfig.write_config(temp_config_file, section_name, dict_of_attr)
    
    # Now overwrite the section
    new_attrs = {"new-key": "new-value"}
    CmfConfig.write_config(temp_config_file, section_name, new_attrs, file_exists=True)
    
    # Read and verify
    config = configparser.ConfigParser()
    with open(temp_config_file, "r") as f:
        config.read_file(f)
    
    # Check section exists with new value
    assert config.has_section(section_name)
    assert config.get(section_name, "new-key") == "new-value"
    
    # Check old key is gone
    with pytest.raises(configparser.NoOptionError):
        config.get(section_name, "server-url")


def test_write_config_neo4j_password(temp_config_file):
    """Test writing neo4j password (should be encoded)."""
    # Write neo4j config with password
    section_name = "neo4j"
    dict_of_attr = {"user": "neo4j", "password": "secret123"}
    CmfConfig.write_config(temp_config_file, section_name, dict_of_attr)
    
    # Read and verify
    config = configparser.ConfigParser()
    with open(temp_config_file, "r") as f:
        config.read_file(f)
    
    # Check section exists
    assert config.has_section(section_name)
    
    # Get and decode password
    password = config.get(section_name, "password")
    decoded_password = base64.b64decode(password.encode("UTF-8")).decode("UTF-8")
    
    # Check decoded password
    assert decoded_password == "secret123"


def test_read_config_standard(temp_config_file):
    """Test reading a standard config file with multiple sections."""
    # Create a config file with multiple sections
    config = configparser.ConfigParser()
    
    # Add cmf section
    config.add_section("cmf")
    config.set("cmf", "server-url", "http://example.com")
    config.set("cmf", "storage-type", "local")
    
    # Add neo4j section with encoded password
    config.add_section("neo4j")
    config.set("neo4j", "user", "neo4j")
    config.set("neo4j", "password", "cGFzc3dvcmQ=")  # "password" encoded
    
    # Add custom section
    config.add_section("custom")
    config.set("custom", "key1", "value1")
    config.set("custom", "key2", "value2")
    
    # Write config to file
    with open(temp_config_file, "w") as f:
        config.write(f)
    
    # Read config using CmfConfig
    result = CmfConfig.read_config(temp_config_file)
    
    # Verify all values
    assert result["cmf-server-url"] == "http://example.com"
    assert result["cmf-storage-type"] == "local"
    assert result["neo4j-user"] == "neo4j"
    assert result["neo4j-password"] == "password"
    assert result["custom-key1"] == "value1"
    assert result["custom-key2"] == "value2"


def test_read_config_empty_file(temp_config_file):
    """Test reading an empty config file."""
    # Create empty file
    with open(temp_config_file, "w") as f:
        f.write("")
    
    # Read config
    result = CmfConfig.read_config(temp_config_file)
    
    # Should be empty dict
    assert result == {}


def test_read_config_missing_password(temp_config_file):
    """Test reading a file with missing neo4j password."""
    # Create config with neo4j section but no password
    config = configparser.ConfigParser()
    config.add_section("neo4j")
    config.set("neo4j", "user", "neo4j")
    
    # Write config
    with open(temp_config_file, "w") as f:
        config.write(f)
    
    # Read config
    result = CmfConfig.read_config(temp_config_file)
    
    # Check user exists but password doesn't
    assert result["neo4j-user"] == "neo4j"
    assert "neo4j-password" not in result


def test_read_config_invalid_base64(temp_config_file):
    """Test reading a file with invalid base64 in neo4j password."""
    # Create config with invalid base64 password
    config = configparser.ConfigParser()
    config.add_section("neo4j")
    config.set("neo4j", "user", "neo4j")
    config.set("neo4j", "password", "not-valid-base64!")
    
    # Write config
    with open(temp_config_file, "w") as f:
        config.write(f)
    
    # Should raise exception on invalid base64
    with pytest.raises(Exception):
        CmfConfig.read_config(temp_config_file)
