import pytest
import os
import tempfile
import hashlib
import json
import subprocess

from cmflib.utils.helper_functions import (
    is_url, is_git_repo, get_python_env, get_md5_hash, 
    change_dir, generate_osdf_token, branch_exists, get_postgres_config,
    validate_and_examine_osdf_token, display_table, fetch_cmf_config_path,
    calculate_md5
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

def test_get_python_env_pip(mocker):
    """Test get_python_env function with pip environment."""
    # Mock CONDA_PREFIX to None to simulate non-conda environment
    mocker.patch('os.getenv', return_value=None)
    
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
    
    # Mock logger.error function
    mock_logger = mocker.patch('cmflib.utils.helper_functions.logger.error')
    
    result = get_python_env()
    
    # Verify the function returns None when an exception occurs
    assert result is None
    
    # Verify the error message was logged
    mock_logger.assert_called_once()
    assert "Command failed" in str(mock_logger.call_args)


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
    mocker.patch('os.getenv', side_effect=lambda key, default=None: {
        'POSTGRES_HOST': 'test-host',
        'POSTGRES_PORT': '5432',
        'POSTGRES_DB': 'test-db',
        'POSTGRES_USER': 'test-user',
        'POSTGRES_PASSWORD': 'test-password'
    }.get(key, default))
    
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
    """Test get_postgres_config function when POSTGRES_HOST is localhost."""
    # Mock os.getenv to return test values with POSTGRES_HOST as localhost
    mocker.patch('os.getenv', side_effect=lambda key, default=None: {
        'POSTGRES_HOST': 'localhost',
        'POSTGRES_PORT': '5432',
        'POSTGRES_DB': 'test-db',
        'POSTGRES_USER': 'test-user',
        'POSTGRES_PASSWORD': 'test-password'
    }.get(key, default))
    
    # Call the function
    result = get_postgres_config()
    
    # Verify the function returns the expected config with localhost as host
    expected_config = {
        "host": "localhost",
        "port": "5432",
        "user": "test-user",
        "password": "test-password",
        "dbname": "test-db"
    }
    assert result == expected_config


def test_validate_and_examine_osdf_token_valid(mocker):
    """Test validate_and_examine_osdf_token function with a valid token."""
    import jwt
    from datetime import datetime, timezone, timedelta
    
    # Create a valid token that expires in the future
    future_time = datetime.now(timezone.utc) + timedelta(hours=1)
    payload = {
        "iss": "https://example.com/issuer",
        "sub": "test-subject",
        "aud": "test-audience",
        "scope": "storage.read:/ storage.write:/",
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": int(future_time.timestamp())
    }
    token_str = jwt.encode(payload, "secret", algorithm="HS256")
    
    # Mock logger.info
    mock_logger_info = mocker.patch('cmflib.utils.helper_functions.logger.info')
    
    # Call the function
    result = validate_and_examine_osdf_token(f"Bearer {token_str}", "test-source")
    
    # Verify the function returns True for a valid token
    assert result is True
    
    # Verify logger.info was called
    assert mock_logger_info.call_count > 0


def test_validate_and_examine_osdf_token_expired(mocker):
    """Test validate_and_examine_osdf_token function with an expired token."""
    import jwt
    from datetime import datetime, timezone, timedelta
    
    # Create an expired token
    past_time = datetime.now(timezone.utc) - timedelta(hours=1)
    payload = {
        "iss": "https://example.com/issuer",
        "sub": "test-subject",
        "aud": "test-audience",
        "scope": "storage.read:/ storage.write:/",
        "iat": int((datetime.now(timezone.utc) - timedelta(hours=2)).timestamp()),
        "exp": int(past_time.timestamp())
    }
    token_str = jwt.encode(payload, "secret", algorithm="HS256")
    
    # Mock logger methods
    mock_logger_info = mocker.patch('cmflib.utils.helper_functions.logger.info')
    mock_logger_warning = mocker.patch('cmflib.utils.helper_functions.logger.warning')
    
    # Call the function
    result = validate_and_examine_osdf_token(token_str)
    
    # Verify the function returns False for an expired token
    assert result is False
    
    # Verify logger.warning was called
    assert mock_logger_warning.call_count > 0


def test_validate_and_examine_osdf_token_invalid(mocker):
    """Test validate_and_examine_osdf_token function with an invalid token."""
    # Mock logger.error
    mock_logger_error = mocker.patch('cmflib.utils.helper_functions.logger.error')
    
    # Call the function with an invalid token
    result = validate_and_examine_osdf_token("invalid.token.string")
    
    # Verify the function returns False for an invalid token
    assert result is False
    
    # Verify logger.error was called
    assert mock_logger_error.call_count > 0


def test_display_table(mocker):
    """Test display_table function."""
    import pandas as pd
    
    # Create a sample DataFrame
    df = pd.DataFrame({
        'Name': ['Alice', 'Bob', 'Charlie'],
        'Age': [25, 30, 35],
        'City': ['New York', 'Los Angeles', 'Chicago']
    })
    
    # Mock logger.info
    mock_logger_info = mocker.patch('cmflib.utils.helper_functions.logger.info')
    
    # Mock readchar.readchar to return 'q' (quit)
    mock_readchar = mocker.patch('readchar.readchar', return_value='q')
    
    # Call the function
    display_table(df, ['Name', 'Age', 'City'])
    
    # Verify logger.info was called (for the table display)
    assert mock_logger_info.call_count > 0


def test_fetch_cmf_config_path_success(mocker):
    """Test fetch_cmf_config_path function when successful."""
    # Mock DvcConfig.get_dvc_config to return a valid dict
    mock_dvc_config = {'remote': 'test-remote'}
    mocker.patch('cmflib.utils.dvc_config.DvcConfig.get_dvc_config', return_value=mock_dvc_config)
    
    # Mock find_root to return a valid path (patch it where it's used in helper_functions)
    mocker.patch('cmflib.utils.helper_functions.find_root', return_value='/test/root')
    
    # Call the function
    dvc_output, config_file_path = fetch_cmf_config_path()
    
    # Verify the function returns the expected values
    assert dvc_output == mock_dvc_config
    assert config_file_path == '/test/root/.cmfconfig'


def test_fetch_cmf_config_path_not_configured(mocker):
    """Test fetch_cmf_config_path function when CMF is not configured."""
    from cmflib.cmf_exception_handling import CmfNotConfigured
    
    # Mock DvcConfig.get_dvc_config to return a non-dict value
    mocker.patch('cmflib.utils.dvc_config.DvcConfig.get_dvc_config', return_value="error")
    
    # Call the function and expect an exception
    with pytest.raises(CmfNotConfigured):
        fetch_cmf_config_path()


def test_fetch_cmf_config_path_root_not_found(mocker):
    """Test fetch_cmf_config_path function when root is not found."""
    from cmflib.cmf_exception_handling import CmfNotConfigured
    
    # Mock DvcConfig.get_dvc_config to return a valid dict
    mock_dvc_config = {'remote': 'test-remote'}
    mocker.patch('cmflib.utils.dvc_config.DvcConfig.get_dvc_config', return_value=mock_dvc_config)
    
    # Mock find_root to return an error message (patch it where it's used in helper_functions)
    mocker.patch('cmflib.utils.helper_functions.find_root', return_value="'cmf' is not configured")
    
    # Call the function and expect an exception
    with pytest.raises(CmfNotConfigured):
        fetch_cmf_config_path()


def test_calculate_md5_success(temp_dir):
    """Test calculate_md5 function with a valid file."""
    # Create a test file
    test_file = os.path.join(temp_dir, "test_file.txt")
    test_content = "This is a test file for MD5 calculation."
    
    with open(test_file, 'w') as f:
        f.write(test_content)
    
    # Calculate expected MD5 hash
    expected_hash = hashlib.md5(test_content.encode('utf-8')).hexdigest()
    
    # Call the function
    result = calculate_md5(test_file)
    
    # Verify the function returns the correct hash
    assert result == expected_hash


def test_calculate_md5_file_not_found(mocker):
    """Test calculate_md5 function when the file doesn't exist."""
    # Mock os.path.isfile to return False
    mocker.patch('os.path.isfile', return_value=False)
    
    # Mock logger.error
    mock_logger_error = mocker.patch('cmflib.utils.helper_functions.logger.error')
    
    # Mock sys.exit to raise SystemExit (simulating actual exit behavior)
    mocker.patch('sys.exit', side_effect=SystemExit(1))
    
    # Call the function with a non-existent file and expect SystemExit
    with pytest.raises(SystemExit) as exc_info:
        calculate_md5("/path/to/nonexistent/file.txt")
    
    # Verify logger.error was called
    assert mock_logger_error.call_count > 0
    
    # Verify the exit code is 1
    assert exc_info.value.code == 1


def test_calculate_md5_large_file(temp_dir):
    """Test calculate_md5 function with a large file."""
    # Create a large test file (larger than 4MB chunk size)
    test_file = os.path.join(temp_dir, "large_file.bin")
    chunk_size = 4096 * 1024  # 4MB
    
    # Write data in chunks to create a file larger than the read chunk size
    with open(test_file, 'wb') as f:
        # Write 5MB of data (5 * 1MB)
        for _ in range(5):
            f.write(b'A' * (1024 * 1024))
    
    # Calculate expected MD5 hash
    expected_md5 = hashlib.md5()
    with open(test_file, 'rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            expected_md5.update(chunk)
    
    # Call the function
    result = calculate_md5(test_file)
    
    # Verify the function returns the correct hash
    assert result == expected_md5.hexdigest()
