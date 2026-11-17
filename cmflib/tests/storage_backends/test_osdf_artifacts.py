import pytest
import os
import requests
import hashlib
from cmflib.storage_backends.osdf_artifacts import (
    OSDFremoteArtifacts,
    generate_cached_url,
    download_and_verify_file
)


# Fixtures
@pytest.fixture
def dvc_config():
    return {
        "remote.osdf.url": "https://osdf-origin.example.org",
        "remote.osdf.custom_auth_header": "Authorization",
        "remote.osdf.password": "test_token"
    }


@pytest.fixture
def osdf_artifacts(dvc_config):
    return OSDFremoteArtifacts(dvc_config)


class FakeStreamResponse:
    """Stands in for a streamed requests.Response."""

    def __init__(self, status_code=200, chunks=(b"test ", b"data")):
        self.status_code = status_code
        self.chunks = chunks

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def iter_content(self, chunk_size=None):
        yield from self.chunks

    @property
    def content(self):
        raise AssertionError("download must stream, not read the whole body into memory")


TEST_DATA_MD5 = hashlib.md5(b"test data").hexdigest()


def _fake_get(monkeypatch, response, calls=None):
    def fake_get(*args, **kwargs):
        if calls is not None:
            calls.append(kwargs)
        return response
    monkeypatch.setattr(requests, "get", fake_get)


def test_download_and_verify_file_streams_to_target(monkeypatch, tmp_path):
    calls = []
    _fake_get(monkeypatch, FakeStreamResponse(), calls)
    target = tmp_path / "file.txt"

    ok, msg = download_and_verify_file("https://example.org/f", {}, str(target), "file.txt", TEST_DATA_MD5, 10)

    assert ok is True
    assert "matches MLMD records" in msg
    assert target.read_bytes() == b"test data"
    assert not (tmp_path / "file.txt.part").exists()
    assert calls[0]["stream"] is True
    assert calls[0]["verify"] is True


def test_download_and_verify_file_hash_mismatch_keeps_existing_file(monkeypatch, tmp_path):
    _fake_get(monkeypatch, FakeStreamResponse(chunks=(b"corrupt",)))
    target = tmp_path / "file.txt"
    target.write_bytes(b"test data")

    ok, msg = download_and_verify_file("https://example.org/f", {}, str(target), "file.txt", TEST_DATA_MD5, 10)

    assert ok is False
    assert "does NOT match MLMD records" in msg
    assert target.read_bytes() == b"test data"
    assert not (tmp_path / "file.txt.part").exists()


def test_download_and_verify_file_http_error(monkeypatch, tmp_path):
    _fake_get(monkeypatch, FakeStreamResponse(status_code=404))
    target = tmp_path / "file.txt"

    ok, msg = download_and_verify_file("https://example.org/f", {}, str(target), "file.txt", TEST_DATA_MD5, 10)

    assert ok is False
    assert "HTTP 404" in msg
    assert not target.exists()


def test_download_and_verify_file_empty_artifact(monkeypatch, tmp_path):
    _fake_get(monkeypatch, FakeStreamResponse(chunks=()))
    target = tmp_path / "empty.txt"

    ok, _ = download_and_verify_file("https://example.org/f", {}, str(target), "empty.txt",
                                     hashlib.md5(b"").hexdigest(), 10)

    assert ok is True
    assert target.read_bytes() == b""


def test_download_and_verify_file_passes_verify_flag(monkeypatch, tmp_path):
    calls = []
    _fake_get(monkeypatch, FakeStreamResponse(), calls)

    download_and_verify_file("https://example.org/f", {}, str(tmp_path / "f"), "f", TEST_DATA_MD5, 10, verify=False)

    assert calls[0]["verify"] is False


def test_download_and_verify_file_timeout(monkeypatch):
    """Test download_and_verify_file function with timeout."""
    # Mock requests.get to raise a timeout exception
    def mock_get_timeout(*args, **kwargs):
        raise requests.exceptions.Timeout("Request timed out")
    
    monkeypatch.setattr(requests, 'get', mock_get_timeout)
    
    # Call the function
    result = download_and_verify_file(
        host="https://example.org/file.txt",
        headers={"Authorization": "Bearer token"},
        remote_file_path="/path/to/downloaded/file.txt",
        local_path="file.txt",
        artifact_hash="some_hash",
        timeout=10
    )
    
    # Assert the result
    assert result == (False, "The request timed out.")


def test_download_and_verify_file_general_exception(monkeypatch):
    """Test download_and_verify_file function with general exception."""
    # Mock requests.get to raise a general exception
    def mock_get_exception(*args, **kwargs):
        raise Exception("Connection error")
    
    monkeypatch.setattr(requests, 'get', mock_get_exception)
    
    # Call the function
    result = download_and_verify_file(
        host="https://example.org/file.txt",
        headers={"Authorization": "Bearer token"},
        remote_file_path="/path/to/downloaded/file.txt",
        local_path="file.txt",
        artifact_hash="some_hash",
        timeout=10
    )
    
    # Assert the result
    assert result == (False, "Connection error")


# Tests for OSDFremoteArtifacts class
def test_download_artifacts_origin_success(osdf_artifacts, dvc_config, monkeypatch, mocker):
    """Test successful artifact download from origin."""
    # Mock dependencies
    mock_download_verify = mocker.MagicMock(return_value=(True, "Download successful"))
    monkeypatch.setattr('cmflib.storage_backends.osdf_artifacts.download_and_verify_file', mock_download_verify)
    
    # Mock os.path.join and os.path.abspath
    monkeypatch.setattr(os.path, 'join', lambda *args: '/'.join(args))
    monkeypatch.setattr(os.path, 'abspath', lambda path: "/abs/path/to/local_file.txt")
    
    # Mock os.makedirs to prevent actual directory creation
    monkeypatch.setattr(os, 'makedirs', lambda *args, **kwargs: None)
    
    # Call the method under test
    object_name, download_loc, success = osdf_artifacts.download_file(
        host="https://origin.example.org/file.txt",
        cache="",  # Empty cache means fetch from origin
        current_directory="/current/dir",
        object_name="/path/to/remote_file.txt",
        download_loc="local_file.txt",
        artifact_hash="test_hash"
    )
    
    # Assert the result
    assert success is True
    assert object_name == "/path/to/remote_file.txt"
    assert download_loc == "/abs/path/to/local_file.txt"
    # Verify download_and_verify_file was called
    assert mock_download_verify.called


def test_download_artifacts_cache_success(osdf_artifacts, dvc_config, monkeypatch, mocker):
    """Test successful artifact download from cache."""
    # Mock dependencies
    mock_download_verify = mocker.MagicMock(return_value=(True, "Download from cache successful"))
    monkeypatch.setattr('cmflib.storage_backends.osdf_artifacts.download_and_verify_file', mock_download_verify)
    
    mock_generate_cached_url = mocker.MagicMock(return_value="https://cache.example.org/file.txt")
    monkeypatch.setattr('cmflib.storage_backends.osdf_artifacts.generate_cached_url', mock_generate_cached_url)
    
    # Mock os.path.join and os.path.abspath
    monkeypatch.setattr(os.path, 'join', lambda *args: '/'.join(args))
    monkeypatch.setattr(os.path, 'abspath', lambda path: "/abs/path/to/local_file.txt")
    
    # Mock os.makedirs to prevent actual directory creation
    monkeypatch.setattr(os, 'makedirs', lambda *args, **kwargs: None)
    
    # Call the method under test
    object_name, download_loc, success = osdf_artifacts.download_file(
        host="https://origin.example.org/file.txt",
        cache="https://cache.example.org",
        current_directory="/current/dir",
        object_name="/path/to/remote_file.txt",
        download_loc="local_file.txt",
        artifact_hash="test_hash"
    )
    
    # Assert the result
    assert success is True
    assert object_name == "/path/to/remote_file.txt"
    assert download_loc == "/abs/path/to/local_file.txt"
    # Verify generate_cached_url was called
    assert mock_generate_cached_url.called


def test_download_artifacts_cache_fallback_to_origin(osdf_artifacts, dvc_config, monkeypatch, mocker):
    """Test fallback to origin when cache download fails."""
    # Mock dependencies
    mock_download_verify = mocker.MagicMock(side_effect=[
        (False, "Cache download failed"),
        (True, "Origin download successful")
    ])
    monkeypatch.setattr('cmflib.storage_backends.osdf_artifacts.download_and_verify_file', mock_download_verify)
    
    mock_generate_cached_url = mocker.MagicMock(return_value="https://cache.example.org/file.txt")
    monkeypatch.setattr('cmflib.storage_backends.osdf_artifacts.generate_cached_url', mock_generate_cached_url)
    
    # Mock os.path.join and os.path.abspath
    monkeypatch.setattr(os.path, 'join', lambda *args: '/'.join(args))
    monkeypatch.setattr(os.path, 'abspath', lambda path: "/abs/path/to/local_file.txt")
    
    # Mock os.makedirs to prevent actual directory creation
    monkeypatch.setattr(os, 'makedirs', lambda *args, **kwargs: None)
    
    # Mock print to prevent actual printing during the test
    monkeypatch.setattr('builtins.print', lambda *args, **kwargs: None)
    
    # Call the method under test
    object_name, download_loc, success = osdf_artifacts.download_file(
        host="https://origin.example.org/file.txt",
        cache="https://cache.example.org",
        current_directory="/current/dir",
        object_name="/path/to/remote_file.txt",
        download_loc="local_file.txt",
        artifact_hash="test_hash"
    )
    
    # Assert the result
    assert success is True
    assert object_name == "/path/to/remote_file.txt"
    assert download_loc == "/abs/path/to/local_file.txt"
    # Verify download_and_verify_file was called twice (cache + origin)
    assert mock_download_verify.call_count == 2


def test_download_artifacts_both_fail(osdf_artifacts, dvc_config, monkeypatch, mocker):
    """Test when both cache and origin downloads fail."""
    # Mock dependencies
    mock_download_verify = mocker.MagicMock(side_effect=[
        (False, "Cache download failed"),
        (False, "Origin download failed")
    ])
    monkeypatch.setattr('cmflib.storage_backends.osdf_artifacts.download_and_verify_file', mock_download_verify)
    
    mock_generate_cached_url = mocker.MagicMock(return_value="https://cache.example.org/file.txt")
    monkeypatch.setattr('cmflib.storage_backends.osdf_artifacts.generate_cached_url', mock_generate_cached_url)
    
    # Mock os.path.join and os.path.abspath
    monkeypatch.setattr(os.path, 'join', lambda *args: '/'.join(args))
    monkeypatch.setattr(os.path, 'abspath', lambda path: "/abs/path/to/local_file.txt")
    
    # Mock os.makedirs to prevent actual directory creation
    monkeypatch.setattr(os, 'makedirs', lambda *args, **kwargs: None)
    
    # Mock print to prevent actual printing during the test
    monkeypatch.setattr('builtins.print', lambda *args, **kwargs: None)
    
    # Call the method under test
    object_name, download_loc, success = osdf_artifacts.download_file(
        host="https://origin.example.org/file.txt",
        cache="https://cache.example.org",
        current_directory="/current/dir",
        object_name="/path/to/remote_file.txt",
        download_loc="local_file.txt",
        artifact_hash="test_hash"
    )
    
    # Assert the result
    assert success is False
    assert object_name == "/path/to/remote_file.txt"


# Test with tmp_path fixture for actual file operations
def test_with_tmp_path(osdf_artifacts, dvc_config, monkeypatch, tmp_path):
    """Test using pytest's tmp_path fixture for actual file operations."""
    # Create a test file in the temporary directory
    test_file = tmp_path / "test_file.txt"
    test_content = b"test data for MD5 calculation"
    test_hash = hashlib.md5(test_content).hexdigest()
    
    # Mock download_and_verify_file to actually create a file
    def mock_download_verify(host, headers, remote_file_path, local_path, artifact_hash, timeout):
        with open(local_path, 'wb') as f:
            f.write(test_content)
        return True, f"Hash {test_hash} matches MLMD records. Download took 0.50 seconds."
    
    monkeypatch.setattr('cmflib.storage_backends.osdf_artifacts.download_and_verify_file', mock_download_verify)
    
    # Mock os.path.join and os.path.abspath to use the temporary path
    monkeypatch.setattr(os.path, 'join', lambda *args: str(tmp_path.joinpath(*args[1:])))
    monkeypatch.setattr(os.path, 'abspath', lambda path: str(test_file))
    
    # Mock os.makedirs to prevent actual directory creation
    monkeypatch.setattr(os, 'makedirs', lambda *args, **kwargs: None)
    
    # Call the method under test
    object_name, download_loc, success = osdf_artifacts.download_file(
        host="https://origin.example.org/file.txt",
        cache="",  # Empty cache means fetch from origin
        current_directory=str(tmp_path),
        object_name="/path/to/remote_file.txt",
        download_loc=str(test_file),
        artifact_hash=test_hash
    )
    
    # Assert the result
    assert success is True
    assert object_name == "/path/to/remote_file.txt"
    assert download_loc == str(test_file)
    
    # Verify the file was actually created with the correct content
    assert test_file.exists()
    assert test_file.read_bytes() == test_content
    
    # Verify the MD5 hash of the file
    calculated_hash = hashlib.md5(test_file.read_bytes()).hexdigest()
    assert calculated_hash == test_hash


# Add more complex parameterized tests
# Note: Parametrized tests for download_artifacts removed because download_artifacts method
# doesn't exist in OSDFremoteArtifacts. The actual method is download_file() with different
# parameters and return values. Basic functionality is covered by the tests above.
