import pytest
import os
import tempfile
import subprocess
import io
from contextlib import redirect_stdout
from cmflib.utils.dvc_config import DvcConfig, dvc_get_config


@pytest.fixture
def temp_dir_setup():
    """Set up a temporary directory for testing."""
    # Create a temporary directory
    temp_dir = tempfile.TemporaryDirectory()
    # Save the current working directory
    original_dir = os.getcwd()
    # Change to the temporary directory
    os.chdir(temp_dir.name)
    
    # Check if git and dvc are available
    try:
        subprocess.run(["git", "--version"], check=True, capture_output=True)
        subprocess.run(["dvc", "--version"], check=True, capture_output=True)
        git_dvc_available = True
    except (subprocess.SubprocessError, FileNotFoundError):
        git_dvc_available = False
    
    # Yield the temporary directory and availability flag
    yield temp_dir.name, original_dir, git_dvc_available
    
    # Cleanup: restore original directory and remove temp dir
    os.chdir(original_dir)
    temp_dir.cleanup()


def test_dvc_get_config_no_dvc(temp_dir_setup):
    """Test dvc_get_config in a directory without DVC initialization."""
    # Unpack the fixture values
    _, _, _ = temp_dir_setup
    
    # Call the function without initializing DVC
    config_output = dvc_get_config()
    
    # Since no DVC config exists, the output should be an empty string
    assert config_output == ""


def test_get_dvc_config_no_dvc(temp_dir_setup):
    """Test get_dvc_config in a directory without DVC initialization."""
    # Unpack the fixture values
    _, _, _ = temp_dir_setup
    
    # Call the method without initializing DVC
    result = DvcConfig.get_dvc_config()
    
    # The method should return a specific error message
    expected_message = "'cmf' is not configured.\nExecute 'cmf init' command."
    assert result == expected_message


def test_dvc_get_config_with_dvc(temp_dir_setup):
    """Test dvc_get_config with a real DVC repo."""
    # Unpack the fixture values
    _, _, git_dvc_available = temp_dir_setup
    
    # Skip test if git or dvc is not available
    if not git_dvc_available:
        pytest.skip("Git or DVC not available")
    
    # Initialize a git repository
    subprocess.run(["git", "init"], check=True, capture_output=True)
    # Initialize a DVC repository
    subprocess.run(["dvc", "init"], check=True, capture_output=True)
    # Set DVC config values using the CLI
    subprocess.run(["dvc", "config", "core.remote", "myremote"], check=True, capture_output=True)
    subprocess.run(["dvc", "config", "remote.myremote.url", "s3://my-bucket"], check=True, capture_output=True)
    
    # Call the function to get the config as a string
    config_output = dvc_get_config()
    
    # Verify that the output contains the config settings we set
    assert "core.remote=myremote" in config_output
    assert "remote.myremote.url=s3://my-bucket" in config_output


def test_get_dvc_config_with_dvc(temp_dir_setup):
    """Test get_dvc_config with a real DVC repo."""
    # Unpack the fixture values
    _, _, git_dvc_available = temp_dir_setup
    
    # Skip test if git or dvc is not available
    if not git_dvc_available:
        pytest.skip("Git or DVC not available")
    
    # Initialize a git repository
    subprocess.run(["git", "init"], check=True, capture_output=True)
    # Initialize a DVC repository
    subprocess.run(["dvc", "init"], check=True, capture_output=True)
    # Set DVC config values using the CLI
    subprocess.run(["dvc", "config", "core.remote", "myremote"], check=True, capture_output=True)
    subprocess.run(["dvc", "config", "remote.myremote.url", "s3://my-bucket"], check=True, capture_output=True)
    
    # Call the method to get the config as a dictionary
    result = DvcConfig.get_dvc_config()
    
    # Verify the result is a dictionary and contains the correct values
    assert isinstance(result, dict)
    assert result["core.remote"] == "myremote"
    assert result["remote.myremote.url"] == "s3://my-bucket"


def test_get_dvc_config_with_complex_values(temp_dir_setup):
    """Test get_dvc_config with values containing special characters."""
    # Unpack the fixture values
    _, _, git_dvc_available = temp_dir_setup
    
    # Skip test if git or dvc is not available
    if not git_dvc_available:
        pytest.skip("Git or DVC not available")
    
    # Initialize a git repository
    subprocess.run(["git", "init"], check=True, capture_output=True)
    # Initialize a DVC repository
    subprocess.run(["dvc", "init"], check=True, capture_output=True)
    # Add a remote with a URL containing special characters
    subprocess.run(["dvc", "remote", "add", "storage", "s3://my-storage-bucket"], check=True, capture_output=True)
    # Set config values with special characters for that remote
    subprocess.run(["dvc", "remote", "modify", "storage", "access_key_id", "AKIAIOSFODNN7EXAMPLE"], check=True, capture_output=True)
    subprocess.run(["dvc", "remote", "modify", "storage", "secret_access_key", "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"], check=True, capture_output=True)
    
    # Call the method to get the config as a dictionary
    result = DvcConfig.get_dvc_config()
    
    # Verify the dictionary contains the complex values
    assert isinstance(result, dict)
    assert result["remote.storage.access_key_id"] == "AKIAIOSFODNN7EXAMPLE"
    assert result["remote.storage.secret_access_key"] == "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"


def test_dvc_get_config_with_malformed_data(temp_dir_setup):
    """Test dvc_get_config with malformed configuration data."""
    # Unpack the fixture values
    _, _, git_dvc_available = temp_dir_setup
    
    # Skip test if git or dvc is not available
    if not git_dvc_available:
        pytest.skip("Git or DVC not available")
    
    # Initialize a git repository
    subprocess.run(["git", "init"], check=True, capture_output=True)
    # Initialize a DVC repository
    subprocess.run(["dvc", "init"], check=True, capture_output=True)
    # Manually append a malformed line to the DVC config file
    with open(".dvc/config", "a") as f:
        f.write("\nmalformed_line_without_equals_sign\n")
    
    # Call dvc_get_config, which should handle the malformed config gracefully
    config_output = dvc_get_config()
    
    # The output should be an empty string due to error handling
    assert config_output == ""


def test_get_dvc_config_with_malformed_data_handling(temp_dir_setup):
    """Test how get_dvc_config handles malformed configuration data."""
    # Unpack the fixture values
    _, _, git_dvc_available = temp_dir_setup
    
    # Skip test if git or dvc is not available
    if not git_dvc_available:
        pytest.skip("Git or DVC not available")
    
    # Initialize a git repository
    subprocess.run(["git", "init"], check=True, capture_output=True)
    # Initialize a DVC repository
    subprocess.run(["dvc", "init"], check=True, capture_output=True)
    # Manually append a malformed line to the DVC config file
    with open(".dvc/config", "a") as f:
        f.write("\nmalformed_line_without_equals_sign\n")
    
    # Call the method, which should return the error message since dvc_get_config returns an empty string
    result = DvcConfig.get_dvc_config()
    expected_message = "'cmf' is not configured.\nExecute 'cmf init' command."
    assert result == expected_message


def test_main_function(temp_dir_setup):
    """Test the main function with real DVC config."""
    # Unpack the fixture values
    _, _, git_dvc_available = temp_dir_setup
    
    # Skip test if git or dvc is not available
    if not git_dvc_available:
        pytest.skip("Git or DVC not available")
    
    # Initialize a git repository
    subprocess.run(["git", "init"], check=True, capture_output=True)
    # Initialize a DVC repository
    subprocess.run(["dvc", "init"], check=True, capture_output=True)
    # Set a DVC config value
    subprocess.run(["dvc", "config", "core.remote", "storage"], check=True, capture_output=True)
    
    # Import the main function from the module
    from cmflib.utils.dvc_config import main
    
    # Capture stdout to verify the output of the main function
    stdout_capture = io.StringIO()
    with redirect_stdout(stdout_capture):
        main()
    output = stdout_capture.getvalue().strip()
    
    # Verify the output contains the config value we set
    assert "'core.remote': 'storage'" in output
