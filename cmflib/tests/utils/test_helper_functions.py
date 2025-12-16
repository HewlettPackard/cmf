import pytest
import os
import tempfile
import hashlib
import json
import subprocess

from cmflib.utils.helper_functions import (
    is_url, is_git_repo, get_python_env, get_md5_hash, 
    change_dir, is_conda_installed, list_conda_packages_json,
    generate_osdf_token, branch_exists, get_postgres_config
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_dir = os.getcwd()
        os.chdir(tmp_dir)
        yield tmp_dir
        os.chdir(original_dir)


def test_is_url():
    """Test is_url function with various inputs."""
    # Valid URLs
    assert is_url("http://example.com")
    assert is_url("https://example.com/path")
    assert is_url("ftp://example.com")
    assert is_url("s3://my-bucket/path")
    
    # Invalid URLs
    assert not is_url("not a url")
    assert not is_url("http://")
    assert not is_url("example.com")
    assert not is_url("")
    assert not is_url(None)


def test_is_git_repo(mocker, temp_dir):
    """Test is_git_repo function."""
    # Mock print function
    mock_print = mocker.patch('builtins.print')
    
    # Test when not in a git repo
    result = is_git_repo()
    assert result is None
    
    # Initialize a git repo
    subprocess.run(["git", "init"], check=True, capture_output=True)
    
    # Test when in a git repo
    result = is_git_repo()
    assert result is not None
    assert "A Git repository already exists in" in result
    assert os.path.join(os.getcwd(), '.git') in result


def test_get_python_env_conda(mocker):
    """Test get_python_env function with conda environment."""
    # Mock conda being installed
    mocker.patch('cmflib.utils.helper_functions.is_conda_installed', return_value=True)
    
    # Mock subprocess outputs
    mock_check_output = mocker.patch('subprocess.check_output')
    mock_check_output.side_effect = [
        b"package1=1.0.0\npackage2=2.0.0\n",  # conda list --export
        b"package3==1.0.0\npackage4==2.0.0\n",  # pip freeze
        b"channels:\n  - conda-forge\n  - defaults\n"  # conda config --show channels
    ]
    
    # Call the function
    result = get_python_env("test-env")
    
    # Verify the result structure
    assert isinstance(result, dict)
    assert result["name"] == "test-env"
    assert result["channels"] == ["conda-forge", "defaults"]
    assert "package1=1.0.0" in result["dependencies"]
    assert "package2=2.0.0" in result["dependencies"]
    
    # Verify pip packages are included
    pip_section = result["dependencies"][-1]
    assert isinstance(pip_section, dict)
    assert "pip" in pip_section
    assert pip_section["pip"] == ["package3==1.0.0", "package4==2.0.0"]


def test_get_python_env_pip(mocker):
    """Test get_python_env function with pip environment."""
    # Mock conda not being installed
    mocker.patch('cmflib.utils.helper_functions.is_conda_installed', return_value=False)
    
    # Mock pip freeze output
    mock_check_output = mocker.patch('subprocess.check_output')
    mock_check_output.return_value = b"package1==1.0.0\npackage2==2.0.0\n"
    
    result = get_python_env()
    
    # Verify the result is a list of pip packages
    assert isinstance(result, list)
    assert result == ["package1==1.0.0", "package2==2.0.0"]


def test_get_python_env_exception(mocker):
    """Test get_python_env function when an exception occurs."""
    # Mock subprocess raising an exception
    mock_check_output = mocker.patch('subprocess.check_output')
    mock_check_output.side_effect = Exception("Command failed")
    
    # Mock print function
    mock_print = mocker.patch('builtins.print')
    
    result = get_python_env()
    
    # Verify the function returns None when an exception occurs
    assert result is None
    
    # Verify the error message was printed
    mock_print.assert_called_with("An error occurred: Command failed")


def test_get_md5_hash():
    """Test get_md5_hash function."""
    # Test with a simple string
    test_string = "test string"
    expected_hash = hashlib.md5(test_string.encode('utf-8')).hexdigest()
    result = get_md5_hash(test_string)
    assert result == expected_hash
    
    # Test with an empty string
    empty_string = ""
    expected_hash = hashlib.md5(empty_string.encode('utf-8')).hexdigest()
    result = get_md5_hash(empty_string)
    assert result == expected_hash
    
    # Test with a complex string
    complex_string = "!@#$%^&*()_+{}|:<>?~`-=[]\\;',./\n\t"
    expected_hash = hashlib.md5(complex_string.encode('utf-8')).hexdigest()
    result = get_md5_hash(complex_string)
    assert result == expected_hash


def test_change_dir(temp_dir):
    """Test change_dir function."""
    # Create a subdirectory
    subdir = os.path.join(temp_dir, "subdir")
    os.makedirs(subdir, exist_ok=True)
    
    # Get the current directory
    original_dir = os.getcwd()
    
    # Change to the subdirectory
    returned_dir = change_dir(subdir)
    
    # Verify the function returned the original directory
    assert returned_dir == original_dir
    
    # Verify we're now in the subdirectory
    assert os.getcwd() == subdir
    
    # Change back to the original directory
    os.chdir(original_dir)
    
    # Test when already in the target directory
    returned_dir = change_dir(original_dir)
    
    # Verify the function returned the original directory
    assert returned_dir == original_dir
    
    # Verify we're still in the original directory
    assert os.getcwd() == original_dir


def test_is_conda_installed_true(mocker):
    """Test is_conda_installed function when conda is installed."""
    # Mock subprocess.run to return successfully
    mock_run = mocker.patch('subprocess.run')
    mock_run.return_value = subprocess.CompletedProcess(
        args=['conda', '--version'], 
        returncode=0, 
        stdout=b'conda 4.10.3\n', 
        stderr=b''
    )
    
    result = is_conda_installed()
    
    # Verify the function returns True when conda is installed
    assert result is True
    
    # Verify subprocess.run was called with the correct arguments
    mock_run.assert_called_once_with(
        ['conda', '--version'], 
        check=True, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE
    )


def test_is_conda_installed_false(mocker):
    """Test is_conda_installed function when conda is not installed."""
    # Mock subprocess.run to raise an exception
    mock_run = mocker.patch('subprocess.run')
    mock_run.side_effect = FileNotFoundError("No such file or directory: 'conda'")
    
    result = is_conda_installed()
    
    # Verify the function returns False when conda is not installed
    assert result is False
    
    # Verify subprocess.run was called with the correct arguments
    mock_run.assert_called_once_with(
        ['conda', '--version'], 
        check=True, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE
    )


def test_list_conda_packages_json_success(mocker):
    """Test list_conda_packages_json function when successful."""
    # Mock subprocess.run to return a JSON string
    mock_json = json.dumps([
        {"name": "package1", "version": "1.0.0"}, 
        {"name": "package2", "version": "2.0.0"}
    ])
    mock_run = mocker.patch('subprocess.run')
    mock_run.return_value = subprocess.CompletedProcess(
        args=['conda', 'list', '--json'], 
        returncode=0, 
        stdout=mock_json, 
        stderr=''
    )
    
    result = list_conda_packages_json()
    
    # Verify the function returns the parsed JSON
    assert result == [
        {"name": "package1", "version": "1.0.0"}, 
        {"name": "package2", "version": "2.0.0"}
    ]
    
    # Verify subprocess.run was called with the correct arguments
    mock_run.assert_called_once_with(
        ['conda', 'list', '--json'], 
        check=True, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, 
        text=True
    )


def test_list_conda_packages_json_failure(mocker):
    """Test list_conda_packages_json function when it fails."""
    # Mock subprocess.run to raise an exception
    mock_run = mocker.patch('subprocess.run')
    mock_run.side_effect = subprocess.CalledProcessError(
        returncode=1, 
        cmd=['conda', 'list', '--json']
    )
    
    result = list_conda_packages_json()
    
    # Verify the function returns an empty list when it fails
    assert result == []
    
    # Verify subprocess.run was called with the correct arguments
    mock_run.assert_called_once_with(
        ['conda', 'list', '--json'], 
        check=True, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, 
        text=True
    )


def test_generate_osdf_token_success(mocker):
    """Test generate_osdf_token function when successful."""
    # Mock os.path.exists to return True
    mocker.patch('os.path.exists', return_value=True)
    
    # Mock the file open
    mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data="-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJTUt9Us8cKj\nMzEfYyjiWA4R4/M2bS1GB4t7NXp98C3SC6dVMvDuictGeurT8jNbvJZHtCSuYEvu\nNMoSfm76oqFvAp8Gy0iz5sxjZmSnXyCdPEovGhLa0VzMaQ8s+CLOyS56YyCFGeJZ\n-----END PRIVATE KEY-----\n"))
    
    # Mock the private key loading
    mock_private_key = mocker.MagicMock()
    mock_load_key = mocker.patch('cryptography.hazmat.primitives.serialization.load_pem_private_key', return_value=mock_private_key)
    
    # Mock the SciToken
    mock_token = mocker.MagicMock()
    mock_token.serialize.return_value = b"dummy.token.string"
    mock_scitoken = mocker.patch('scitokens.SciToken', return_value=mock_token)
    
    # Call the function with valid parameters
    result = generate_osdf_token("test-key-id", "/path/to/key.pem", "https://example.com/issuer")
    
    # Verify the function returns the expected token
    assert result == "Bearer dummy.token.string"
    
    # Verify the token was created with the correct parameters
    mock_scitoken.assert_called_once_with(key=mock_private_key, key_id="test-key-id")
    mock_token.update_claims.assert_called_once()
    mock_token.serialize.assert_called_once_with(issuer="https://example.com/issuer")


def test_generate_osdf_token_file_not_exists(mocker):
    """Test generate_osdf_token function when the key file doesn't exist."""
    # Mock os.path.exists to return False
    mocker.patch('os.path.exists', return_value=False)
    
    # Mock print function
    mock_print = mocker.patch('builtins.print')
    
    # Call the function
    result = generate_osdf_token("test-key-id", "/path/to/nonexistent/key.pem", "https://example.com/issuer")
    
    # Verify the function returns an empty string
    assert result == ""


def test_generate_osdf_token_invalid_url(mocker):
    """Test generate_osdf_token function with an invalid URL."""
    # Mock os.path.exists to return True
    mocker.patch('os.path.exists', return_value=True)
    
    # Mock the file open
    mocker.patch('builtins.open', mocker.mock_open(read_data="-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJTUt9Us8cKj\nMzEfYyjiWA4R4/M2bS1GB4t7NXp98C3SC6dVMvDuictGeurT8jNbvJZHtCSuYEvu\nNMoSfm76oqFvAp8Gy0iz5sxjZmSnXyCdPEovGhLa0VzMaQ8s+CLOyS56YyCFGeJZ\n-----END PRIVATE KEY-----\n"))
    
    # Mock print function
    mock_print = mocker.patch('builtins.print')
    
    # Call the function with an invalid URL
    result = generate_osdf_token("test-key-id", "/path/to/key.pem", "not-a-url")
    
    # Verify the function returns an empty string
    assert result == ""


def test_branch_exists_true(mocker):
    """Test branch_exists function when the branch exists."""
    # Mock requests.get to return a 200 status code
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_get = mocker.patch('requests.get', return_value=mock_response)
    
    # Call the function
    result = branch_exists("owner", "repo", "main")
    
    # Verify the function returns True
    assert result is True
    
    # Verify requests.get was called with the correct URL
    mock_get.assert_called_once_with("https://api.github.com/repos/owner/repo/branches/main")


def test_branch_exists_false(mocker):
    """Test branch_exists function when the branch doesn't exist."""
    # Mock requests.get to return a 404 status code
    mock_response = mocker.MagicMock()
    mock_response.status_code = 404
    mock_get = mocker.patch('requests.get', return_value=mock_response)
    
    # Call the function
    result = branch_exists("owner", "repo", "nonexistent-branch")
    
    # Verify the function returns False
    assert result is False
    
    # Verify requests.get was called with the correct URL
    mock_get.assert_called_once_with("https://api.github.com/repos/owner/repo/branches/nonexistent-branch")


def test_get_postgres_config(mocker):
    """Test get_postgres_config function."""
    # Mock os.getenv to return test values
    mocker.patch('os.getenv', side_effect=lambda key: {
        'MYIP': '192.168.1.1',
        'HOSTNAME': 'test-host',
        'POSTGRES_DB': 'test-db',
        'POSTGRES_USER': 'test-user',
        'POSTGRES_PASSWORD': 'test-password'
    }.get(key))
    
    # Call the function
    result = get_postgres_config()
    
    # Verify the function returns the expected config
    expected_config = {
        "host": "test-host",
        "port": "5432",
        "user": "test-user",
        "password": "test-password",
        "dbname": "test-db"
    }
    assert result == expected_config


def test_get_postgres_config_localhost(mocker):
    """Test get_postgres_config function when HOSTNAME is localhost."""
    # Mock os.getenv to return test values with HOSTNAME as localhost
    mocker.patch('os.getenv', side_effect=lambda key: {
        'MYIP': '192.168.1.1',
        'HOSTNAME': 'localhost',
        'POSTGRES_DB': 'test-db',
        'POSTGRES_USER': 'test-user',
        'POSTGRES_PASSWORD': 'test-password'
    }.get(key))
    
    # Call the function
    result = get_postgres_config()
    
    # Verify the function returns the expected config with IP as host
    expected_config = {
        "host": "192.168.1.1",
        "port": "5432",
        "user": "test-user",
        "password": "test-password",
        "dbname": "test-db"
    }
    assert result == expected_config
