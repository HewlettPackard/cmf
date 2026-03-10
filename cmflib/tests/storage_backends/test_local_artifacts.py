import pytest
import os
from cmflib.storage_backends.local_artifacts import LocalArtifacts


# Fixtures
@pytest.fixture
def dvc_config():
    return {
        "remote.local-storage.url": "/path/to/local/repository"
    }


@pytest.fixture
def mock_dvc_fs(mocker):
    # Create a mock DVCFileSystem using pytest-mock
    mock_dvc_fs_class = mocker.patch('cmflib.storage_backends.local_artifacts.DVCFileSystem')
    
    # Create a mock DVCFileSystem instance
    mock_fs = mocker.MagicMock()
    mock_dvc_fs_class.return_value = mock_fs
    
    yield mock_fs, mock_dvc_fs_class


@pytest.fixture
def local_artifacts(dvc_config, mock_dvc_fs):
    mock_fs, _ = mock_dvc_fs
    return LocalArtifacts(dvc_config)


# Tests
def test_init(local_artifacts, dvc_config, mock_dvc_fs):
    """Test initialization of LocalArtifacts."""
    mock_fs, mock_dvc_fs_class = mock_dvc_fs
    
    # Assert that DVCFileSystem was called with the correct arguments
    mock_dvc_fs_class.assert_called_once_with(
        "/path/to/local/repository"
    )
    
    # Assert that the instance variable was set correctly
    assert local_artifacts.fs == mock_fs


def test_download_file_success(local_artifacts, mock_dvc_fs, monkeypatch):
    """Test successful file download."""
    mock_fs, _ = mock_dvc_fs
    
    # Configure the mock DVCFileSystem
    mock_fs.get_file.return_value = None
    
    # Mock print and os.makedirs to prevent actual operations
    monkeypatch.setattr('builtins.print', lambda *args, **kwargs: None)
    monkeypatch.setattr(os, 'makedirs', lambda path, mode, exist_ok: None)
    
    # Call the method under test
    result = local_artifacts.download_file(
        current_directory="/current/dir",
        object_name="files/md5/a2/37457aa730c396e5acdbc5a64c8453",
        download_loc="/download/path/file.txt"
    )
    
    # Assert the result
    assert result == ("files/md5/a2/37457aa730c396e5acdbc5a64c8453", "/download/path/file.txt", True)
    
    # Verify method calls
    mock_fs.get_file.assert_called_once_with(
        "files/md5/a2/37457aa730c396e5acdbc5a64c8453", "/download/path/file.txt"
    )


def test_download_file_failure(local_artifacts, mock_dvc_fs, monkeypatch):
    """Test file download failure."""
    mock_fs, _ = mock_dvc_fs
    
    # Configure the mock DVCFileSystem
    mock_fs.get_file.return_value = "Error"
    
    # Mock print and os.makedirs to prevent actual operations
    monkeypatch.setattr('builtins.print', lambda *args, **kwargs: None)
    monkeypatch.setattr(os, 'makedirs', lambda path, mode, exist_ok: None)
    
    # Call the method under test
    result = local_artifacts.download_file(
        current_directory="/current/dir",
        object_name="files/md5/a2/37457aa730c396e5acdbc5a64c8453",
        download_loc="/download/path/file.txt"
    )
    
    # Assert the result
    assert result == ("files/md5/a2/37457aa730c396e5acdbc5a64c8453", "/download/path/file.txt", False)


def test_download_file_exception(local_artifacts, mock_dvc_fs, monkeypatch):
    """Test file download with exception."""
    mock_fs, _ = mock_dvc_fs
    
    # Configure the mock DVCFileSystem
    mock_fs.get_file.side_effect = Exception("Test exception")
    
    # Mock print and os.makedirs to prevent actual operations
    monkeypatch.setattr('builtins.print', lambda *args, **kwargs: None)
    monkeypatch.setattr(os, 'makedirs', lambda path, mode, exist_ok: None)
    
    # Call the method under test
    result = local_artifacts.download_file(
        current_directory="/current/dir",
        object_name="files/md5/a2/37457aa730c396e5acdbc5a64c8453",
        download_loc="/download/path/file.txt"
    )
    
    # Assert the result
    assert result == ("files/md5/a2/37457aa730c396e5acdbc5a64c8453", "/download/path/file.txt", False)


def test_download_directory_success(local_artifacts, mock_dvc_fs, monkeypatch, mocker):
    """Test successful directory download."""
    mock_fs, _ = mock_dvc_fs
    
    # Configure the mock DVCFileSystem
    mock_fs.get_file.return_value = None
    
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
    result = local_artifacts.download_directory(
        current_directory="/current/dir",
        object_name="files/md5/c9/d8fdacc0d942cf8d7d95b6301cfb97.dir",
        download_loc="/download/path/dir"
    )
    
    # Assert the result
    assert result == (2, 2, True)
    
    # Verify method calls
    mock_fs.get_file.assert_any_call(
        "files/md5/c9/d8fdacc0d942cf8d7d95b6301cfb97.dir", "/download/path/dir/dir"
    )
    
    # Verify get_file calls for individual files
    mock_fs.get_file.assert_any_call(
        "files/md5/a2/37457aa730c396e5acdbc5a64c8453", "/download/path/dir/file1.txt"
    )
    mock_fs.get_file.assert_any_call(
        "files/md5/b2/37457aa730c396e5acdbc5a64c8453", "/download/path/dir/file2.txt"
    )


def test_download_directory_partial_success(local_artifacts, mock_dvc_fs, monkeypatch, mocker):
    """Test directory download with some files failing."""
    mock_fs, _ = mock_dvc_fs
    
    # Configure the mock DVCFileSystem for the .dir file
    mock_fs.get_file.side_effect = [
        None,  # Success for the .dir file
        None,  # Success for the first file
        "Error"  # Failure for the second file
    ]
    
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
    result = local_artifacts.download_directory(
        current_directory="/current/dir",
        object_name="files/md5/c9/d8fdacc0d942cf8d7d95b6301cfb97.dir",
        download_loc="/download/path/dir"
    )
    
    # Assert the result - 2 total files, 1 downloaded, False for overall success
    assert result == (2, 1, False)


def test_download_directory_dir_file_not_found(local_artifacts, mock_dvc_fs, monkeypatch):
    """Test directory download when .dir file is not found."""
    mock_fs, _ = mock_dvc_fs
    
    # Configure the mock DVCFileSystem to raise an exception for the .dir file
    mock_fs.get_file.side_effect = Exception("File not found")
    
    # Mock print to prevent actual printing during the test
    monkeypatch.setattr('builtins.print', lambda *args, **kwargs: None)
    monkeypatch.setattr(os, 'makedirs', lambda path, mode, exist_ok: None)
    
    # Call the method under test
    result = local_artifacts.download_directory(
        current_directory="/current/dir",
        object_name="files/md5/c9/d8fdacc0d942cf8d7d95b6301cfb97.dir",
        download_loc="/download/path/dir"
    )
    
    # Assert the result - 1 total file (the .dir file), 0 downloaded, False for overall success
    assert result == (1, 0, False)


def test_download_directory_no_slash_in_download_loc(local_artifacts, mock_dvc_fs, monkeypatch, mocker):
    """Test directory download with no slash in download_loc."""
    mock_fs, _ = mock_dvc_fs
    
    # Configure the mock DVCFileSystem
    mock_fs.get_file.return_value = None
    
    # Mock the file open and read operations
    tracked_files = [
        {'relpath': 'file1.txt', 'md5': 'a237457aa730c396e5acdbc5a64c8453'}
    ]
    
    # Mock os functions to prevent actual file operations
    monkeypatch.setattr('builtins.print', lambda *args, **kwargs: None)
    monkeypatch.setattr(os.path, 'exists', lambda _: True)
    monkeypatch.setattr(os, 'makedirs', lambda path, mode, exist_ok: None)
    monkeypatch.setattr(os, 'remove', lambda _: None)
    
    # Use mocker.mock_open to mock the file operations
    m = mocker.mock_open(read_data=str(tracked_files))
    monkeypatch.setattr('builtins.open', m)
    
    # Call the method under test with a download_loc that has no slash
    result = local_artifacts.download_directory(
        current_directory="/current/dir",
        object_name="files/md5/c9/d8fdacc0d942cf8d7d95b6301cfb97.dir",
        download_loc="dir"  # No slash in the path
    )
    
    # Assert the result
    assert result == (1, 1, True)


# Add parameterized tests
@pytest.mark.parametrize("get_file_return,expected_success", [
    (None, True),  # Success case
    ("Error", False),  # Error case
    (Exception("Test exception"), False)  # Exception case
])
def test_download_file_parametrized(local_artifacts, mock_dvc_fs, monkeypatch, 
                                   get_file_return, expected_success):
    """Parameterized test for file download with different scenarios."""
    mock_fs, _ = mock_dvc_fs
    
    # Configure the mock DVCFileSystem based on parameters
    if isinstance(get_file_return, Exception):
        mock_fs.get_file.side_effect = get_file_return
    else:
        mock_fs.get_file.return_value = get_file_return
    
    # Mock print and os.makedirs to prevent actual operations
    monkeypatch.setattr('builtins.print', lambda *args, **kwargs: None)
    monkeypatch.setattr(os, 'makedirs', lambda path, mode, exist_ok: None)
    
    # Call the method under test
    result = local_artifacts.download_file(
        current_directory="/current/dir",
        object_name="files/md5/a2/37457aa730c396e5acdbc5a64c8453",
        download_loc="/download/path/file.txt"
    )
    
    # Assert the result
    assert result == ("files/md5/a2/37457aa730c396e5acdbc5a64c8453", "/download/path/file.txt", expected_success)


# Test using tmp_path fixture for actual file operations
def test_with_tmp_path(local_artifacts, mock_dvc_fs, monkeypatch, tmp_path):
    """Test using pytest's tmp_path fixture for actual file operations."""
    mock_fs, _ = mock_dvc_fs
    
    # Configure the mock DVCFileSystem
    def fake_get_file(src, dst):
        # Actually create the file
        with open(dst, 'w') as f:
            f.write("test content")
        return None
    
    mock_fs.get_file.side_effect = fake_get_file
    
    # Create a test file path in the temporary directory
    test_file = tmp_path / "test_file.txt"
    
    # Call the method under test with the temporary path
    result = local_artifacts.download_file(
        current_directory="/current/dir",
        object_name="files/md5/a2/37457aa730c396e5acdbc5a64c8453",
        download_loc=str(test_file)
    )
    
    # Assert the result
    assert result == ("files/md5/a2/37457aa730c396e5acdbc5a64c8453", str(test_file), True)
    
    # Verify the file was actually created
    assert test_file.exists()
    assert test_file.read_text() == "test content"
