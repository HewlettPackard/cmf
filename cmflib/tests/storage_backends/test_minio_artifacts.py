import pytest
import os
from minio.error import S3Error
from cmflib.storage_backends.minio_artifacts import MinioArtifacts
from cmflib.cmf_exception_handling import BucketNotFound


# Fixtures
@pytest.fixture
def dvc_config():
    return {
        "remote.minio.endpointurl": "http://minio.example.com:9000",
        "remote.minio.access_key_id": "test_access_key",
        "remote.minio.secret_access_key": "test_secret_key"
    }


@pytest.fixture
def mock_minio_client(mocker):
    # Create a mock Minio client using pytest-mock
    mock_minio_class = mocker.patch('cmflib.storage_backends.minio_artifacts.Minio')
    
    # Create a mock Minio client instance
    mock_client = mocker.MagicMock()
    mock_minio_class.return_value = mock_client
    
    yield mock_client, mock_minio_class


@pytest.fixture
def minio_artifacts(dvc_config, mock_minio_client):
    mock_client, _ = mock_minio_client
    return MinioArtifacts(dvc_config)


# Tests
def test_init(minio_artifacts, dvc_config, mock_minio_client):
    """Test initialization of MinioArtifacts."""
    mock_client, mock_minio_class = mock_minio_client
    
    # Assert that Minio was called with the correct arguments
    mock_minio_class.assert_called_once_with(
        "minio.example.com:9000", 
        access_key="test_access_key", 
        secret_key="test_secret_key", 
        secure=False
    )
    
    # Assert that the instance variables were set correctly
    assert minio_artifacts.endpoint == "minio.example.com:9000"
    assert minio_artifacts.access_key == "test_access_key"
    assert minio_artifacts.secret_key == "test_secret_key"
    assert minio_artifacts.client == mock_client


def test_download_file_success(minio_artifacts, mock_minio_client, monkeypatch, mocker):
    """Test successful file download."""
    mock_client, _ = mock_minio_client
    
    # Configure the mock Minio client
    mock_client.bucket_exists.return_value = True
    mock_client.fget_object.return_value = mocker.MagicMock()  # Mock response object
    
    # Mock print to prevent actual printing during the test
    monkeypatch.setattr('builtins.print', lambda *args, **kwargs: None)
    
    # Call the method under test
    result = minio_artifacts.download_file(
        current_directory="/current/dir",
        bucket_name="test-bucket",
        object_name="test-object",
        download_loc="/download/path/file.txt"
    )
    
    # Assert the result
    assert result == ("test-object", "/download/path/file.txt", True)
    
    # Verify method calls
    mock_client.bucket_exists.assert_called_once_with("test-bucket")
    mock_client.fget_object.assert_called_once_with(
        "test-bucket", "test-object", "/download/path/file.txt"
    )


def test_download_file_bucket_not_found(minio_artifacts, mock_minio_client, monkeypatch):
    """Test file download when bucket does not exist."""
    mock_client, _ = mock_minio_client
    
    # Configure the mock Minio client
    mock_client.bucket_exists.return_value = False
    
    # Mock print to prevent actual printing during the test
    monkeypatch.setattr('builtins.print', lambda *args, **kwargs: None)
    
    # Call the method under test
    result = minio_artifacts.download_file(
        current_directory="/current/dir",
        bucket_name="test-bucket",
        object_name="test-object",
        download_loc="/download/path/file.txt"
    )
    
    # Assert the result - should return False for success since bucket doesn't exist
    assert result == ("test-object", "/download/path/file.txt", False)
    
    # Verify method calls
    mock_client.bucket_exists.assert_called_once_with("test-bucket")
    mock_client.fget_object.assert_not_called()


def test_download_file_s3_error(minio_artifacts, mock_minio_client, monkeypatch):
    """Test file download with S3Error."""
    mock_client, _ = mock_minio_client
    
    # Configure the mock Minio client
    mock_client.bucket_exists.return_value = True
    mock_client.fget_object.side_effect = S3Error(
        code="NoSuchKey",
        message="The specified key does not exist.",
        resource="test-object",
        request_id="test-request-id",
        host_id="test-host-id",
        response=None
    )
    
    # Mock print to prevent actual printing during the test
    monkeypatch.setattr('builtins.print', lambda *args, **kwargs: None)
    
    # Call the method under test
    result = minio_artifacts.download_file(
        current_directory="/current/dir",
        bucket_name="test-bucket",
        object_name="test-object",
        download_loc="/download/path/file.txt"
    )
    
    # Assert the result
    assert result == ("test-object", "/download/path/file.txt", False)
    
    # Verify method calls
    mock_client.bucket_exists.assert_called_once_with("test-bucket")
    mock_client.fget_object.assert_called_once_with(
        "test-bucket", "test-object", "/download/path/file.txt"
    )


def test_download_file_general_exception(minio_artifacts, mock_minio_client, monkeypatch):
    """Test file download with a general exception."""
    mock_client, _ = mock_minio_client
    
    # Configure the mock Minio client
    mock_client.bucket_exists.return_value = True
    mock_client.fget_object.side_effect = Exception("Test exception")
    
    # Mock print to prevent actual printing during the test
    monkeypatch.setattr('builtins.print', lambda *args, **kwargs: None)
    
    # Call the method under test
    result = minio_artifacts.download_file(
        current_directory="/current/dir",
        bucket_name="test-bucket",
        object_name="test-object",
        download_loc="/download/path/file.txt"
    )
    
    # Assert the result
    assert result == ("test-object", "/download/path/file.txt", False)


def test_download_directory_success(minio_artifacts, mock_minio_client, monkeypatch, mocker):
    """Test successful directory download."""
    mock_client, _ = mock_minio_client
    
    # Configure the mock Minio client
    mock_client.bucket_exists.return_value = True
    mock_client.fget_object.return_value = mocker.MagicMock()  # Mock response object
    
    # Mock the file open and read operations
    tracked_files = [
        {'relpath': 'file1.txt', 'md5': 'a237457aa730c396e5acdbc5a64c8453'},
        {'relpath': 'file2.txt', 'md5': 'b237457aa730c396e5acdbc5a64c8453'}
    ]
    
    # Mock os functions to prevent actual file operations
    monkeypatch.setattr('builtins.print', lambda *args, **kwargs: None)
    monkeypatch.setattr(os.path, 'exists', lambda _: True)
    monkeypatch.setattr(os, 'makedirs', lambda path, mode, exist_ok: None)
    monkeypatch.setattr(os, 'remove', lambda _: None)
    
    # Use mocker.mock_open to mock the file operations
    m = mocker.mock_open(read_data=str(tracked_files))
    monkeypatch.setattr('builtins.open', m)
    
    # Call the method under test
    result = minio_artifacts.download_directory(
        current_directory="/current/dir",
        bucket_name="test-bucket",
        object_name="files/md5/c9/d8fdacc0d942cf8d7d95b6301cfb97.dir",
        download_loc="/download/path/dir"
    )
    
    # Assert the result
    assert result == (2, 2, True)
    
    # Verify method calls
    mock_client.bucket_exists.assert_called_once_with("test-bucket")
    
    # Verify fget_object calls for .dir file and individual files
    mock_client.fget_object.assert_any_call(
        "test-bucket", "files/md5/c9/d8fdacc0d942cf8d7d95b6301cfb97.dir", "/download/path/dir/temp_dir"
    )
    
    # Verify fget_object calls for individual files
    mock_client.fget_object.assert_any_call(
        "test-bucket", "files/md5/a2/37457aa730c396e5acdbc5a64c8453", "/download/path/dir/file1.txt"
    )
    mock_client.fget_object.assert_any_call(
        "test-bucket", "files/md5/b2/37457aa730c396e5acdbc5a64c8453", "/download/path/dir/file2.txt"
    )


def test_download_directory_bucket_not_found(minio_artifacts, mock_minio_client, monkeypatch):
    """Test directory download when bucket does not exist."""
    mock_client, _ = mock_minio_client
    
    # Configure the mock Minio client
    mock_client.bucket_exists.return_value = False
    
    # Mock print to prevent actual printing during the test
    monkeypatch.setattr('builtins.print', lambda *args, **kwargs: None)
    monkeypatch.setattr(os, 'makedirs', lambda path, mode, exist_ok: None)
    
    # Call the method under test and check for exception
    with pytest.raises(BucketNotFound):
        minio_artifacts.download_directory(
            current_directory="/current/dir",
            bucket_name="test-bucket",
            object_name="files/md5/c9/d8fdacc0d942cf8d7d95b6301cfb97.dir",
            download_loc="/download/path/dir"
        )
    
    # Verify method calls
    mock_client.bucket_exists.assert_called_once_with("test-bucket")
    mock_client.fget_object.assert_not_called()


def test_download_directory_dir_file_not_found(minio_artifacts, mock_minio_client, monkeypatch):
    """Test directory download when .dir file is not found."""
    mock_client, _ = mock_minio_client
    
    # Configure the mock Minio client
    mock_client.bucket_exists.return_value = True
    mock_client.fget_object.side_effect = S3Error(
        code="NoSuchKey",
        message="The specified key does not exist.",
        resource="files/md5/c9/d8fdacc0d942cf8d7d95b6301cfb97.dir",
        request_id="test-request-id",
        host_id="test-host-id",
        response=None
    )
    
    # Mock print and os.makedirs to prevent actual operations
    monkeypatch.setattr('builtins.print', lambda *args, **kwargs: None)
    monkeypatch.setattr(os, 'makedirs', lambda path, mode, exist_ok: None)
    
    # Call the method under test
    result = minio_artifacts.download_directory(
        current_directory="/current/dir",
        bucket_name="test-bucket",
        object_name="files/md5/c9/d8fdacc0d942cf8d7d95b6301cfb97.dir",
        download_loc="/download/path/dir"
    )
    
    # Assert the result - 1 total file (the .dir file), 0 downloaded, False for overall success
    assert result == (1, 0, False)


def test_download_directory_partial_success(minio_artifacts, mock_minio_client, monkeypatch, mocker):
    """Test directory download with some files failing."""
    mock_client, _ = mock_minio_client
    
    # Configure the mock Minio client
    mock_client.bucket_exists.return_value = True
    
    # Set up side effects for fget_object to succeed for .dir file and first file, but fail for second file
    def side_effect(*args, **kwargs):
        if args[1] == "files/md5/b2/37457aa730c396e5acdbc5a64c8453":
            raise S3Error(
                code="NoSuchKey",
                message="The specified key does not exist.",
                resource=args[1],
                request_id="test-request-id",
                host_id="test-host-id",
                response=None
            )
        return mocker.MagicMock()  # Return mock response for successful calls
    
    mock_client.fget_object.side_effect = side_effect
    
    # Mock the file open and read operations
    tracked_files = [
        {'relpath': 'file1.txt', 'md5': 'a237457aa730c396e5acdbc5a64c8453'},
        {'relpath': 'file2.txt', 'md5': 'b237457aa730c396e5acdbc5a64c8453'}
    ]
    
    # Mock os functions to prevent actual file operations
    monkeypatch.setattr('builtins.print', lambda *args, **kwargs: None)
    monkeypatch.setattr(os.path, 'exists', lambda _: True)
    monkeypatch.setattr(os, 'makedirs', lambda path, mode, exist_ok: None)
    monkeypatch.setattr(os, 'remove', lambda _: None)
    
    # Use mocker.mock_open to mock the file operations
    m = mocker.mock_open(read_data=str(tracked_files))
    monkeypatch.setattr('builtins.open', m)
    
    # Call the method under test
    result = minio_artifacts.download_directory(
        current_directory="/current/dir",
        bucket_name="test-bucket",
        object_name="files/md5/c9/d8fdacc0d942cf8d7d95b6301cfb97.dir",
        download_loc="/download/path/dir"
    )
    
    # Assert the result - 2 total files, 1 downloaded, False for overall success
    assert result == (2, 1, False)


def test_download_directory_general_exception(minio_artifacts, mock_minio_client, monkeypatch):
    """Test directory download with a general exception."""
    mock_client, _ = mock_minio_client
    
    # Configure the mock Minio client
    mock_client.bucket_exists.return_value = True
    mock_client.fget_object.side_effect = Exception("Test exception")
    
    # Mock print and os.makedirs to prevent actual operations
    monkeypatch.setattr('builtins.print', lambda *args, **kwargs: None)
    monkeypatch.setattr(os, 'makedirs', lambda path, mode, exist_ok: None)
    
    # Call the method under test
    result = minio_artifacts.download_directory(
        current_directory="/current/dir",
        bucket_name="test-bucket",
        object_name="files/md5/c9/d8fdacc0d942cf8d7d95b6301cfb97.dir",
        download_loc="/download/path/dir"
    )
    
    # Assert the result - 1 total file (the .dir file), 0 downloaded, False for overall success
    assert result == (1, 0, False)


# Add parameterized tests
@pytest.mark.parametrize("bucket_exists,fget_success,expected_result", [
    (True, True, ("test-object", "/download/path/file.txt", True)),
    (True, False, ("test-object", "/download/path/file.txt", False)),
    (False, None, ("test-object", "/download/path/file.txt", False)),
])
def test_download_file_parametrized(minio_artifacts, mock_minio_client, monkeypatch, mocker,
                                   bucket_exists, fget_success, expected_result):
    """Parameterized test for file download with different scenarios."""
    mock_client, _ = mock_minio_client
    
    # Mock print to prevent actual printing during the test
    monkeypatch.setattr('builtins.print', lambda *args, **kwargs: None)
    
    # Configure the mock Minio client based on parameters
    mock_client.bucket_exists.return_value = bucket_exists
    
    if bucket_exists and not fget_success:
        mock_client.fget_object.side_effect = S3Error(
            code="NoSuchKey",
            message="The specified key does not exist.",
            resource="test-object",
            request_id="test-request-id",
            host_id="test-host-id",
            response=None
        )
    else:
        mock_client.fget_object.return_value = mocker.MagicMock()
    
    # Call the method under test
    result = minio_artifacts.download_file(
        current_directory="/current/dir",
        bucket_name="test-bucket",
        object_name="test-object",
        download_loc="/download/path/file.txt"
    )
    
    # Assert the result
    assert result == expected_result


# Test with tmp_path fixture for actual file operations
def test_with_tmp_path(minio_artifacts, mock_minio_client, monkeypatch, tmp_path, mocker):
    """Test using pytest's tmp_path fixture for actual file operations."""
    mock_client, _ = mock_minio_client
    
    # Configure the mock Minio client
    mock_client.bucket_exists.return_value = True
    
    # Create a side effect that actually creates a file
    def fake_fget_object(bucket_name, object_name, file_path):
        with open(file_path, 'w') as f:
            f.write(f"Content for {object_name}")
        return mocker.MagicMock()
    
    mock_client.fget_object.side_effect = fake_fget_object
    
    # Create a test file path in the temporary directory
    test_file = tmp_path / "test_file.txt"
    
    # Mock print to prevent actual printing during the test
    monkeypatch.setattr('builtins.print', lambda *args, **kwargs: None)
    
    # Call the method under test
    result = minio_artifacts.download_file(
        current_directory="/current/dir",
        bucket_name="test-bucket",
        object_name="test-object",
        download_loc=str(test_file)
    )
    
    # Assert the result
    assert result == ("test-object", str(test_file), True)
    
    # Verify the file was actually created
    assert test_file.exists()
    assert test_file.read_text() == "Content for test-object"
