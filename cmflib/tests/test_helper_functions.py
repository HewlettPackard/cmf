import unittest
import os
import tempfile
import hashlib
import json
import subprocess
from unittest.mock import patch, MagicMock
from pathlib import Path

from cmflib.utils.helper_functions import (
    is_url, is_git_repo, get_python_env, get_md5_hash, 
    change_dir, is_conda_installed, list_conda_packages_json,
    generate_osdf_token, branch_exists, get_postgres_config
)

class TestHelperFunctions(unittest.TestCase):
    """Tests for helper_functions.py utility functions."""

    def setUp(self):
        """Step 1: Set up test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_dir = os.getcwd()
        os.chdir(self.temp_dir.name)

    def tearDown(self):
        """Step 2: Clean up after tests."""
        os.chdir(self.original_dir)
        self.temp_dir.cleanup()

    def test_is_url(self):
        """Step 1: Test is_url function with various inputs."""
        # Step 1: Valid URLs
        self.assertTrue(is_url("http://example.com"))
        self.assertTrue(is_url("https://example.com/path"))
        self.assertTrue(is_url("ftp://example.com"))
        self.assertTrue(is_url("s3://my-bucket/path"))
        
        # Step 2: Invalid URLs
        self.assertFalse(is_url("not a url"))
        self.assertFalse(is_url("http://"))
        self.assertFalse(is_url("example.com"))
        self.assertFalse(is_url(""))
        self.assertFalse(is_url(None))

    @patch('builtins.print')  # Step 2: Add this to suppress print statements
    def test_is_git_repo(self, mock_print):
        """Step 1: Test is_git_repo function."""
        # Step 1: Test when not in a git repo
        result = is_git_repo()
        self.assertIsNone(result)
        
        # Step 2: Initialize a git repo
        subprocess.run(["git", "init"], check=True, capture_output=True)
        
        # Step 3: Test when in a git repo
        result = is_git_repo()
        self.assertIsNotNone(result)
        self.assertIn("A Git repository already exists in", result)
        self.assertIn(os.path.join(os.getcwd(), '.git'), result)

    @patch('cmflib.utils.helper_functions.is_conda_installed')
    @patch('subprocess.check_output')
    def test_get_python_env_conda(self, mock_check_output, mock_is_conda):
        """Test get_python_env function with conda environment."""
        # Step 1: Mock conda being installed
        mock_is_conda.return_value = True
        
        # Step 2: Mock subprocess outputs
        mock_check_output.side_effect = [
            b"package1=1.0.0\npackage2=2.0.0\n",  # conda list --export
            b"package3==1.0.0\npackage4==2.0.0\n",  # pip freeze
            b"channels:\n  - conda-forge\n  - defaults\n"  # conda config --show channels
        ]
        
        # Step 3: Call the function
        result = get_python_env("test-env")
        
        # Step 4: Verify the result structure
        self.assertIsInstance(result, dict)
        self.assertEqual(result["name"], "test-env")
        self.assertEqual(result["channels"], ["conda-forge", "defaults"])
        self.assertIn("package1=1.0.0", result["dependencies"])
        self.assertIn("package2=2.0.0", result["dependencies"])
        
        # Step 5: Verify pip packages are included
        pip_section = result["dependencies"][-1]
        self.assertIsInstance(pip_section, dict)
        self.assertIn("pip", pip_section)
        self.assertEqual(pip_section["pip"], ["package3==1.0.0", "package4==2.0.0"])

    @patch('cmflib.utils.helper_functions.is_conda_installed')
    @patch('subprocess.check_output')
    def test_get_python_env_pip(self, mock_check_output, mock_is_conda):
        """Step 1: Test get_python_env function with pip environment."""
        # Step 1: Mock conda not being installed
        mock_is_conda.return_value = False
        
        # Step 2: Mock pip freeze output
        mock_check_output.return_value = b"package1==1.0.0\npackage2==2.0.0\n"
        
        result = get_python_env()
        
        # Step 3: Verify the result is a list of pip packages
        self.assertIsInstance(result, list)
        self.assertEqual(result, ["package1==1.0.0", "package2==2.0.0"])

    @patch('subprocess.check_output')
    @patch('builtins.print')  # Step 2: Add this to suppress print statements
    def test_get_python_env_exception(self, mock_print, mock_check_output):
        """Step 1: Test get_python_env function when an exception occurs."""
        # Step 1: Mock subprocess raising an exception
        mock_check_output.side_effect = Exception("Command failed")
        
        result = get_python_env()
        
        # Step 2: Verify the function returns None when an exception occurs
        self.assertIsNone(result)
        
        # Step 3: Verify the error message was printed
        mock_print.assert_called_with("An error occurred: Command failed")

    def test_get_md5_hash(self):
        """Step 1: Test get_md5_hash function."""
        # Step 1: Test with a simple string
        test_string = "test string"
        expected_hash = hashlib.md5(test_string.encode('utf-8')).hexdigest()
        result = get_md5_hash(test_string)
        self.assertEqual(result, expected_hash)
        
        # Step 2: Test with an empty string
        empty_string = ""
        expected_hash = hashlib.md5(empty_string.encode('utf-8')).hexdigest()
        result = get_md5_hash(empty_string)
        self.assertEqual(result, expected_hash)
        
        # Step 3: Test with a complex string
        complex_string = "!@#$%^&*()_+{}|:<>?~`-=[]\\;',./\n\t"
        expected_hash = hashlib.md5(complex_string.encode('utf-8')).hexdigest()
        result = get_md5_hash(complex_string)
        self.assertEqual(result, expected_hash)

    def test_change_dir(self):
        """Step 1: Test change_dir function."""
        # Step 1: Create a subdirectory
        subdir = os.path.join(self.temp_dir.name, "subdir")
        os.makedirs(subdir, exist_ok=True)
        
        # Step 2: Get the current directory
        original_dir = os.getcwd()
        
        # Step 3: Change to the subdirectory
        returned_dir = change_dir(subdir)
        
        # Step 4: Verify the function returned the original directory
        self.assertEqual(returned_dir, original_dir)
        
        # Step 5: Verify we're now in the subdirectory
        self.assertEqual(os.getcwd(), subdir)
        
        # Step 6: Change back to the original directory
        os.chdir(original_dir)
        
        # Step 7: Test when already in the target directory
        returned_dir = change_dir(original_dir)
        
        # Step 8: Verify the function returned the original directory
        self.assertEqual(returned_dir, original_dir)
        
        # Step 9: Verify we're still in the original directory
        self.assertEqual(os.getcwd(), original_dir)

    @patch('subprocess.run')
    def test_is_conda_installed_true(self, mock_run):
        """Step 1: Test is_conda_installed function when conda is installed."""
        # Step 1: Mock subprocess.run to return successfully
        mock_run.return_value = subprocess.CompletedProcess(args=['conda', '--version'], returncode=0, stdout=b'conda 4.10.3\n', stderr=b'')
        
        result = is_conda_installed()
        
        # Step 2: Verify the function returns True when conda is installed
        self.assertTrue(result)
        
        # Step 3: Verify subprocess.run was called with the correct arguments
        mock_run.assert_called_once_with(['conda', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    @patch('subprocess.run')
    def test_is_conda_installed_false(self, mock_run):
        """Step 1: Test is_conda_installed function when conda is not installed."""
        # Step 1: Mock subprocess.run to raise an exception
        mock_run.side_effect = FileNotFoundError("No such file or directory: 'conda'")
        
        result = is_conda_installed()
        
        # Step 2: Verify the function returns False when conda is not installed
        self.assertFalse(result)
        
        # Step 3: Verify subprocess.run was called with the correct arguments
        mock_run.assert_called_once_with(['conda', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    @patch('subprocess.run')
    def test_list_conda_packages_json_success(self, mock_run):
        """Step 1: Test list_conda_packages_json function when successful."""
        # Step 1: Mock subprocess.run to return a JSON string
        mock_json = json.dumps([{"name": "package1", "version": "1.0.0"}, {"name": "package2", "version": "2.0.0"}])
        mock_run.return_value = subprocess.CompletedProcess(args=['conda', 'list', '--json'], returncode=0, stdout=mock_json, stderr='')
        
        result = list_conda_packages_json()
        
        # Step 2: Verify the function returns the parsed JSON
        self.assertEqual(result, [{"name": "package1", "version": "1.0.0"}, {"name": "package2", "version": "2.0.0"}])
        
        # Step 3: Verify subprocess.run was called with the correct arguments
        mock_run.assert_called_once_with(['conda', 'list', '--json'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    @patch('subprocess.run')
    def test_list_conda_packages_json_failure(self, mock_run):
        """Step 1: Test list_conda_packages_json function when it fails."""
        # Step 1: Mock subprocess.run to raise an exception
        mock_run.side_effect = subprocess.CalledProcessError(returncode=1, cmd=['conda', 'list', '--json'])
        
        result = list_conda_packages_json()
        
        # Step 2: Verify the function returns an empty list when it fails
        self.assertEqual(result, [])
        
        # Step 3: Verify subprocess.run was called with the correct arguments
        mock_run.assert_called_once_with(['conda', 'list', '--json'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data="-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJTUt9Us8cKj\nMzEfYyjiWA4R4/M2bS1GB4t7NXp98C3SC6dVMvDuictGeurT8jNbvJZHtCSuYEvu\nNMoSfm76oqFvAp8Gy0iz5sxjZmSnXyCdPEovGhLa0VzMaQ8s+CLOyS56YyCFGeJZ\n-----END PRIVATE KEY-----\n")
    @patch('cryptography.hazmat.primitives.serialization.load_pem_private_key')
    @patch('scitokens.SciToken')
    def test_generate_osdf_token_success(self, mock_scitoken, mock_load_key, mock_open, mock_exists):
        """Step 1: Test generate_osdf_token function when successful."""
        # Step 1: Mock os.path.exists to return True
        mock_exists.return_value = True
        
        # Step 2: Mock the private key loading
        mock_private_key = MagicMock()
        mock_load_key.return_value = mock_private_key
        
        # Step 3: Mock the SciToken
        mock_token = MagicMock()
        mock_token.serialize.return_value = b"dummy.token.string"
        mock_scitoken.return_value = mock_token
        
        # Step 4: Call the function with valid parameters
        result = generate_osdf_token("test-key-id", "/path/to/key.pem", "https://example.com/issuer")
        
        # Step 5: Verify the function returns the expected token
        self.assertEqual(result, "Bearer dummy.token.string")
        
        # Step 6: Verify the token was created with the correct parameters
        mock_scitoken.assert_called_once_with(key=mock_private_key, key_id="test-key-id")
        mock_token.update_claims.assert_called_once()
        mock_token.serialize.assert_called_once_with(issuer="https://example.com/issuer")

    @patch('os.path.exists')
    @patch('builtins.print')  # Step 2: Suppress print statements
    def test_generate_osdf_token_file_not_exists(self, mock_print, mock_exists):
        """Step 1: Test generate_osdf_token function when the key file doesn't exist."""
        # Step 1: Mock os.path.exists to return False
        mock_exists.return_value = False
        
        # Step 2: Call the function
        result = generate_osdf_token("test-key-id", "/path/to/nonexistent/key.pem", "https://example.com/issuer")
        
        # Step 3: Verify the function returns an empty string
        self.assertEqual(result, "")

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data="-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJTUt9Us8cKj\nMzEfYyjiWA4R4/M2bS1GB4t7NXp98C3SC6dVMvDuictGeurT8jNbvJZHtCSuYEvu\nNMoSfm76oqFvAp8Gy0iz5sxjZmSnXyCdPEovGhLa0VzMaQ8s+CLOyS56YyCFGeJZ\n-----END PRIVATE KEY-----\n")
    @patch('builtins.print')  # Step 2: Add this to suppress print statements
    def test_generate_osdf_token_invalid_url(self, mock_print, mock_open, mock_exists):
        """Step 1: Test generate_osdf_token function with an invalid URL."""
        # Step 1: Mock os.path.exists to return True
        mock_exists.return_value = True
        
        # Step 2: Call the function with an invalid URL
        result = generate_osdf_token("test-key-id", "/path/to/key.pem", "not-a-url")
        
        # Step 3: Verify the function returns an empty string
        self.assertEqual(result, "")

    @patch('requests.get')
    def test_branch_exists_true(self, mock_get):
        """Step 1: Test branch_exists function when the branch exists."""
        # Step 1: Mock requests.get to return a 200 status code
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Step 2: Call the function
        result = branch_exists("owner", "repo", "main")
        
        # Step 3: Verify the function returns True
        self.assertTrue(result)
        
        # Step 4: Verify requests.get was called with the correct URL
        mock_get.assert_called_once_with("https://api.github.com/repos/owner/repo/branches/main")

    @patch('requests.get')
    def test_branch_exists_false(self, mock_get):
        """Step 1: Test branch_exists function when the branch doesn't exist."""
        # Step 1: Mock requests.get to return a 404 status code
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        # Step 2: Call the function
        result = branch_exists("owner", "repo", "nonexistent-branch")
        
        # Step 3: Verify the function returns False
        self.assertFalse(result)
        
        # Step 4: Verify requests.get was called with the correct URL
        mock_get.assert_called_once_with("https://api.github.com/repos/owner/repo/branches/nonexistent-branch")

    @patch('os.getenv')
    def test_get_postgres_config(self, mock_getenv):
        """Step 1: Test get_postgres_config function."""
        # Step 1: Mock os.getenv to return test values
        mock_getenv.side_effect = lambda key: {
            'MYIP': '192.168.1.1',
            'HOSTNAME': 'test-host',
            'POSTGRES_DB': 'test-db',
            'POSTGRES_USER': 'test-user',
            'POSTGRES_PASSWORD': 'test-password'
        }.get(key)
        
        # Step 2: Call the function
        result = get_postgres_config()
        
        # Step 3: Verify the function returns the expected config
        expected_config = {
            "host": "test-host",
            "port": "5432",
            "user": "test-user",
            "password": "test-password",
            "dbname": "test-db"
        }
        self.assertEqual(result, expected_config)

    @patch('os.getenv')
    def test_get_postgres_config_localhost(self, mock_getenv):
        """Step 1: Test get_postgres_config function when HOSTNAME is localhost."""
        # Step 1: Mock os.getenv to return test values with HOSTNAME as localhost
        mock_getenv.side_effect = lambda key: {
            'MYIP': '192.168.1.1',
            'HOSTNAME': 'localhost',
            'POSTGRES_DB': 'test-db',
            'POSTGRES_USER': 'test-user',
            'POSTGRES_PASSWORD': 'test-password'
        }.get(key)
        
        # Step 2: Call the function
        result = get_postgres_config()
        
        # Step 3: Verify the function returns the expected config with IP as host
        expected_config = {
            "host": "192.168.1.1",
            "port": "5432",
            "user": "test-user",
            "password": "test-password",
            "dbname": "test-db"
        }
        self.assertEqual(result, expected_config)

if __name__ == '__main__':
    unittest.main()
