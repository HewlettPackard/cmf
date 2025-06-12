import pytest
import os
import botocore.exceptions
from cmflib.storage_backends.amazonS3_artifacts import AmazonS3Artifacts


# Fixtures
@pytest.fixture
def dvc_config():
    return {
        "remote.amazons3.access_key_id": "test_access_key",
        "remote.amazons3.secret_access_key": "test_secret_key",
        "remote.amazons3.session_token": "test_session_token"
    }


@pytest.fixture
def mock_s3_client(mocker):
    # Create a mock S3 client using pytest-mock
    mock_boto3_client = mocker.patch('boto3.client')
    
    # Create a mock S3 client
    mock_s3 = mocker.MagicMock()
    
    # Set up the exceptions attribute properly
    mock_s3.exceptions = mocker.MagicMock()
    mock_s3.exceptions.ClientError = botocore.exceptions.ClientError
    
    mock_boto3_client.return_value = mock_s3
    
    yield mock_s3, mock_boto3_client


@pytest.fixture
def s3_artifacts(dvc_config, mock_s3_client):
    mock_s3, _ = mock_s3_client
    return AmazonS3Artifacts(dvc_config)


# Tests
def test_init(s3_artifacts, dvc_config, mock_s3_client):
    """Test initialization of AmazonS3Artifacts."""
    mock_s3, mock_boto3_client = mock_s3_client
    
    # Assert that boto3.client was called with the correct arguments
    mock_boto3_client.assert_called_once_with(
        's3',
        aws_access_key_id='test_access_key',
        aws_secret_access_key='test_secret_key',
        aws_session_token='test_session_token'
    )
    
    # Assert that the instance variables were set correctly
    assert s3_artifacts.access_key == 'test_access_key'
    assert s3_artifacts.secret_key == 'test_secret_key'
    assert s3_artifacts.session_token == 'test_session_token'
    assert s3_artifacts.s3 == mock_s3


def test_download_file_success(s3_artifacts, mock_s3_client, monkeypatch):
    """Test successful file download."""
    mock_s3, _ = mock_s3_client
    
    # Configure the mock S3 client
    mock_s3.head_bucket.return_value = {}
    mock_s3.download_file.return_value = None
    
    # Mock os.makedirs to prevent actual directory creation
    monkeypatch.setattr(os, 'makedirs', lambda path, mode, exist_ok: None)
    
    # Call the method under test
    result = s3_artifacts.download_file(
        current_directory="/current/dir",
        bucket_name="test-bucket",
        object_name="test-object",
        download_loc="/download/path/file.txt"
    )
    
    # Assert the result
    assert result == ("test-object", "/download/path/file.txt", True)
    
    # Verify method calls
    mock_s3.head_bucket.assert_called_once_with(Bucket="test-bucket")
    mock_s3.download_file.assert_called_once_with(
        "test-bucket", "test-object", "/download/path/file.txt"
    )


def test_download_file_failure(s3_artifacts, mock_s3_client, monkeypatch):
    """Test file download failure."""
    mock_s3, _ = mock_s3_client
    
    # Configure the mock S3 client
    mock_s3.head_bucket.return_value = {}
    mock_s3.download_file.return_value = "Error"
    
    # Mock os.makedirs to prevent actual directory creation
    monkeypatch.setattr(os, 'makedirs', lambda path, mode, exist_ok: None)
    
    # Call the method under test
    result = s3_artifacts.download_file(
        current_directory="/current/dir",
        bucket_name="test-bucket",
        object_name="test-object",
        download_loc="/download/path/file.txt"
    )
    
    # Assert the result
    assert result == ("test-object", "/download/path/file.txt", False)


def test_download_file_bucket_not_exists(s3_artifacts, mock_s3_client, monkeypatch):
    """Test file download when bucket does not exist."""
    mock_s3, _ = mock_s3_client
    
    # Configure the mock S3 client to raise a ClientError
    error_response = {'Error': {'Code': '404'}}
    mock_s3.head_bucket.side_effect = mock_s3.exceptions.ClientError(
        error_response, 'HeadBucket'
    )
    
    # Mock os.makedirs to prevent actual directory creation
    monkeypatch.setattr(os, 'makedirs', lambda path, mode, exist_ok: None)
    
    # Call the method under test
    result = s3_artifacts.download_file(
        current_directory="/current/dir",
        bucket_name="test-bucket",
        object_name="test-object",
        download_loc="/download/path/file.txt"
    )
    
    # Assert the result
    assert result == ("test-object", "/download/path/file.txt", False)


def test_download_directory_success(s3_artifacts, mock_s3_client, monkeypatch, mocker):
    """Test successful directory download."""
    mock_s3, _ = mock_s3_client
    
    # Configure the mock S3 client
    mock_s3.head_bucket.return_value = {}
    mock_s3.download_file.return_value = None
    
    # Mock the file open and read operations
    tracked_files = [
        {'relpath': 'file1.txt', 'md5': 'a237457aa730c396e5acdbc5a64c8453'},
        {'relpath': 'file2.txt', 'md5': 'b237457aa730c396e5acdbc5a64c8453'}
    ]
    
    # Mock os functions to prevent actual file operations
    monkeypatch.setattr(os.path, 'exists', lambda _: True)
    monkeypatch.setattr(os, 'makedirs', lambda path, mode, exist_ok: None)
    monkeypatch.setattr(os, 'remove', lambda _: None)
    
    # Use mocker.mock_open to mock the file operations
    m = mocker.mock_open(read_data=str(tracked_files))
    monkeypatch.setattr('builtins.open', m)
    
    # Call the method under test
    result = s3_artifacts.download_directory(
        current_directory="/current/dir",
        bucket_name="test-bucket",
        object_name="files/md5/c9/d8fdacc0d942cf8d7d95b6301cfb97.dir",
        download_loc="/download/path/dir"
    )
    
    # Assert the result
    assert result == (2, 2, True)
    
    # Verify method calls
    mock_s3.head_bucket.assert_called_once_with(Bucket="test-bucket")
    
    # Verify download_file calls for .dir file and individual files
    mock_s3.download_file.assert_any_call(
        "test-bucket", "files/md5/c9/d8fdacc0d942cf8d7d95b6301cfb97.dir", "/download/path/dir/temp_dir"
    )
    
    # Verify download_file calls for individual files
    mock_s3.download_file.assert_any_call(
        "test-bucket", "files/md5/a2/37457aa730c396e5acdbc5a64c8453", "/download/path/dir/file1.txt"
    )
    mock_s3.download_file.assert_any_call(
        "test-bucket", "files/md5/b2/37457aa730c396e5acdbc5a64c8453", "/download/path/dir/file2.txt"
    )


def test_download_directory_dir_file_not_found(s3_artifacts, mock_s3_client, monkeypatch):
    """Test directory download when .dir file is not found."""
    mock_s3, _ = mock_s3_client
    
    # Configure the mock S3 client
    mock_s3.head_bucket.return_value = {}
    
    # Configure download_file to raise an exception
    error_response = {'Error': {'Code': '404'}}
    mock_s3.download_file.side_effect = mock_s3.exceptions.ClientError(
        error_response, 'GetObject'
    )
    
    # Mock os.makedirs to prevent actual directory creation
    monkeypatch.setattr(os, 'makedirs', lambda path, mode, exist_ok: None)
    
    # Call the method under test
    result = s3_artifacts.download_directory(
        current_directory="/current/dir",
        bucket_name="test-bucket",
        object_name="files/md5/c9/d8fdacc0d942cf8d7d95b6301cfb97.dir",
        download_loc="/download/path/dir"
    )
    
    # Assert the result
    assert result == (1, 0, False)


# Add parameterized tests
@pytest.mark.parametrize("bucket_exists,download_success,expected_result", [
    (True, True, ("test-object", "/download/path/file.txt", True)),
    (True, False, ("test-object", "/download/path/file.txt", False)),
    (False, None, ("test-object", "/download/path/file.txt", False)),
])
def test_download_file_parametrized(s3_artifacts, mock_s3_client, monkeypatch, 
                                   bucket_exists, download_success, expected_result):
    """Parameterized test for file download with different scenarios."""
    mock_s3, _ = mock_s3_client
    
    # Mock os.makedirs to prevent actual directory creation
    monkeypatch.setattr(os, 'makedirs', lambda path, mode, exist_ok: None)
    
    # Configure the mock S3 client based on parameters
    if bucket_exists:
        mock_s3.head_bucket.return_value = {}
        if download_success:
            mock_s3.download_file.return_value = None
        else:
            mock_s3.download_file.return_value = "Error"
    else:
        error_response = {'Error': {'Code': '404'}}
        mock_s3.head_bucket.side_effect = mock_s3.exceptions.ClientError(
            error_response, 'HeadBucket'
        )
    
    # Call the method under test
    result = s3_artifacts.download_file(
        current_directory="/current/dir",
        bucket_name="test-bucket",
        object_name="test-object",
        download_loc="/download/path/file.txt"
    )
    
    # Assert the result
    assert result == expected_result
