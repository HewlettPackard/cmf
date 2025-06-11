import unittest
import os
import sys
import tempfile
import subprocess
import io
from contextlib import redirect_stdout
from cmflib.utils.dvc_config import DvcConfig, dvc_get_config

class TestDvcConfig(unittest.TestCase):
    """Tests for DvcConfig class using real methods."""

    def setUp(self):
        """Set up test environment before each test."""
        # 1. Create a temporary directory to isolate the test environment.
        self.temp_dir = tempfile.TemporaryDirectory()
        # 2. Save the current working directory to restore it later.
        self.original_dir = os.getcwd()
        # 3. Change to the temporary directory for all file operations.
        os.chdir(self.temp_dir.name)
        
        # 4. Check if both git and dvc are installed and available in PATH.
        try:
            subprocess.run(["git", "--version"], check=True, capture_output=True)
            subprocess.run(["dvc", "--version"], check=True, capture_output=True)
            self.git_dvc_available = True  # Both tools are available.
        except (subprocess.SubprocessError, FileNotFoundError):
            self.git_dvc_available = False  # At least one tool is missing.
    
    def tearDown(self):
        """Clean up after each test."""
        # 1. Restore the original working directory.
        os.chdir(self.original_dir)
        # 2. Delete the temporary directory and all its contents.
        self.temp_dir.cleanup()

    def test_dvc_get_config_no_dvc(self):
        """Test dvc_get_config in a directory without DVC initialization."""
        # 1. Do not initialize DVC, just call the function.
        config_output = dvc_get_config()
        # 2. Since no DVC config exists, the output should be an empty string.
        self.assertEqual(config_output, "")

    def test_get_dvc_config_no_dvc(self):
        """Test get_dvc_config in a directory without DVC initialization."""
        # 1. Do not initialize DVC, just call the method.
        result = DvcConfig.get_dvc_config()
        # 2. The method should return a specific error message.
        expected_message = "'cmf' is not configured.\nExecute 'cmf init' command."
        self.assertEqual(result, expected_message)

    def test_dvc_get_config_with_dvc(self):
        """Test dvc_get_config with a real DVC repo."""
        # 1. Skip test if git or dvc is not available.
        if not self.git_dvc_available:
            self.skipTest("Git or DVC not available")
        # 2. Initialize a git repository.
        subprocess.run(["git", "init"], check=True, capture_output=True)
        # 3. Initialize a DVC repository.
        subprocess.run(["dvc", "init"], check=True, capture_output=True)
        # 4. Set DVC config values using the CLI.
        subprocess.run(["dvc", "config", "core.remote", "myremote"], check=True, capture_output=True)
        subprocess.run(["dvc", "config", "remote.myremote.url", "s3://my-bucket"], check=True, capture_output=True)
        # 5. Call the function to get the config as a string.
        config_output = dvc_get_config()
        # 6. Verify that the output contains the config settings we set.
        self.assertIn("core.remote=myremote", config_output)
        self.assertIn("remote.myremote.url=s3://my-bucket", config_output)

    def test_get_dvc_config_with_dvc(self):
        """Test get_dvc_config with a real DVC repo."""
        # 1. Skip test if git or dvc is not available.
        if not self.git_dvc_available:
            self.skipTest("Git or DVC not available")
        # 2. Initialize a git repository.
        subprocess.run(["git", "init"], check=True, capture_output=True)
        # 3. Initialize a DVC repository.
        subprocess.run(["dvc", "init"], check=True, capture_output=True)
        # 4. Set DVC config values using the CLI.
        subprocess.run(["dvc", "config", "core.remote", "myremote"], check=True, capture_output=True)
        subprocess.run(["dvc", "config", "remote.myremote.url", "s3://my-bucket"], check=True, capture_output=True)
        # 5. Call the method to get the config as a dictionary.
        result = DvcConfig.get_dvc_config()
        # 6. Verify the result is a dictionary and contains the correct values.
        self.assertIsInstance(result, dict)
        self.assertEqual(result["core.remote"], "myremote")
        self.assertEqual(result["remote.myremote.url"], "s3://my-bucket")

    def test_get_dvc_config_with_complex_values(self):
        """Test get_dvc_config with values containing special characters."""
        # 1. Skip test if git or dvc is not available.
        if not self.git_dvc_available:
            self.skipTest("Git or DVC not available")
        # 2. Initialize a git repository.
        subprocess.run(["git", "init"], check=True, capture_output=True)
        # 3. Initialize a DVC repository.
        subprocess.run(["dvc", "init"], check=True, capture_output=True)
        # 4. Add a remote with a URL containing special characters.
        subprocess.run(["dvc", "remote", "add", "storage", "s3://my-storage-bucket"], check=True, capture_output=True)
        # 5. Set config values with special characters for that remote.
        subprocess.run(["dvc", "remote", "modify", "storage", "access_key_id", "AKIAIOSFODNN7EXAMPLE"], check=True, capture_output=True)
        subprocess.run(["dvc", "remote", "modify", "storage", "secret_access_key", "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"], check=True, capture_output=True)
        # 6. Call the method to get the config as a dictionary.
        result = DvcConfig.get_dvc_config()
        # 7. Verify the dictionary contains the complex values.
        self.assertIsInstance(result, dict)
        self.assertEqual(result["remote.storage.access_key_id"], "AKIAIOSFODNN7EXAMPLE")
        self.assertEqual(result["remote.storage.secret_access_key"], "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY")

    def test_dvc_get_config_with_malformed_data(self):
        """Test dvc_get_config with malformed configuration data."""
        # 1. Skip test if git or dvc is not available.
        if not self.git_dvc_available:
            self.skipTest("Git or DVC not available")
        # 2. Initialize a git repository.
        subprocess.run(["git", "init"], check=True, capture_output=True)
        # 3. Initialize a DVC repository.
        subprocess.run(["dvc", "init"], check=True, capture_output=True)
        # 4. Manually append a malformed line to the DVC config file.
        with open(".dvc/config", "a") as f:
            f.write("\nmalformed_line_without_equals_sign\n")
        # 5. Call dvc_get_config, which should handle the malformed config gracefully.
        config_output = dvc_get_config()
        # 6. The output should be an empty string due to error handling.
        self.assertEqual(config_output, "")

    def test_get_dvc_config_with_malformed_data_handling(self):
        """Test how get_dvc_config handles malformed configuration data."""
        # 1. Skip test if git or dvc is not available.
        if not self.git_dvc_available:
            self.skipTest("Git or DVC not available")
        # 2. Initialize a git repository.
        subprocess.run(["git", "init"], check=True, capture_output=True)
        # 3. Initialize a DVC repository.
        subprocess.run(["dvc", "init"], check=True, capture_output=True)
        # 4. Manually append a malformed line to the DVC config file.
        with open(".dvc/config", "a") as f:
            f.write("\nmalformed_line_without_equals_sign\n")
        # 5. Call the method, which should return the error message since dvc_get_config returns an empty string.
        result = DvcConfig.get_dvc_config()
        expected_message = "'cmf' is not configured.\nExecute 'cmf init' command."
        self.assertEqual(result, expected_message)

    def test_main_function(self):
        """Test the main function with real DVC config."""
        # 1. Skip test if git or dvc is not available.
        if not self.git_dvc_available:
            self.skipTest("Git or DVC not available")
        # 2. Initialize a git repository.
        subprocess.run(["git", "init"], check=True, capture_output=True)
        # 3. Initialize a DVC repository.
        subprocess.run(["dvc", "init"], check=True, capture_output=True)
        # 4. Set a DVC config value.
        subprocess.run(["dvc", "config", "core.remote", "storage"], check=True, capture_output=True)
        # 5. Import the main function from the module.
        from cmflib.utils.dvc_config import main
        # 6. Capture stdout to verify the output of the main function.
        stdout_capture = io.StringIO()
        with redirect_stdout(stdout_capture):
            main()
        output = stdout_capture.getvalue().strip()
        # 7. Verify the output contains the config value we set.
        self.assertIn("'core.remote': 'storage'", output)

if __name__ == '__main__':
    unittest.main()
