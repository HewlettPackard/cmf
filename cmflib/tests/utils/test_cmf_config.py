import unittest
import configparser
import base64
import tempfile
import os
from cmflib.utils.cmf_config import CmfConfig

class TestCmfConfig(unittest.TestCase):
    """Tests for CmfConfig using real files and objects."""

    def test_write_config(self):
        """Test writing configurations to files."""

        # CASE 1: Writing to a new file
        # Step 1: Create a temporary file and get its name
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            new_file = temp_file.name

        try:
            # Step 2: Define the section name
            section_name = "cmf"
            # Step 3: Define attributes to write
            dict_of_attr = {"server-url": "http://example.com", "storage-type": "local"}
            # Step 4: Write config to the new file
            CmfConfig.write_config(new_file, section_name, dict_of_attr)

            # Step 5: Create a ConfigParser to read the file
            config = configparser.ConfigParser()
            # Step 6: Read the config file
            with open(new_file, "r") as f:
                config.read_file(f)

            # Step 7: Check if section exists
            self.assertTrue(config.has_section(section_name))
            # Step 8: Check value
            self.assertEqual(config.get(section_name, "server-url"), "http://example.com")
            # Step 9: Check value
            self.assertEqual(config.get(section_name, "storage-type"), "local")

            # CASE 2: Updating an existing file
            # Step 1: Define new section
            section_name = "custom"
            # Step 2: Define new attributes
            dict_of_attr = {"key1": "value1", "key2": "value2"}
            # Step 3: Update config file
            CmfConfig.write_config(new_file, section_name, dict_of_attr, file_exists=True)

            # Step 4: Create new ConfigParser
            updated_config = configparser.ConfigParser()
            # Step 5: Read updated file
            with open(new_file, "r") as f:
                updated_config.read_file(f)

            # Step 6: Check original section
            self.assertTrue(updated_config.has_section("cmf"))
            # Step 7: Check value
            self.assertEqual(updated_config.get("cmf", "server-url"), "http://example.com")

            # Step 8: Check new section
            self.assertTrue(updated_config.has_section(section_name))
            # Step 9: Check value
            self.assertEqual(updated_config.get(section_name, "key1"), "value1")
            # Step 10: Check value
            self.assertEqual(updated_config.get(section_name, "key2"), "value2")

            # CASE 3: Overwriting an existing section
            # Step 1: Section to overwrite
            section_name = "cmf"
            # Step 2: New attributes for overwrite
            dict_of_attr = {"new-key": "new-value"}
            # Step 3: Overwrite section
            CmfConfig.write_config(new_file, section_name, dict_of_attr, file_exists=True)

            # Step 4: Create ConfigParser
            overwritten_config = configparser.ConfigParser()
            # Step 5: Read file
            with open(new_file, "r") as f:
                overwritten_config.read_file(f)

            # Step 6: Check section exists
            self.assertTrue(overwritten_config.has_section(section_name))
            # Step 7: Check new value
            self.assertEqual(overwritten_config.get(section_name, "new-key"), "new-value")

            # Step 8: Ensure old key is gone
            with self.assertRaises(configparser.NoOptionError):
                overwritten_config.get(section_name, "server-url")

            # CASE 4: Writing neo4j password (should be encoded)
            # Step 1: Section for neo4j
            section_name = "neo4j"
            # Step 2: Attributes with password
            dict_of_attr = {"user": "neo4j", "password": "secret123"}
            # Step 3: Write with password
            CmfConfig.write_config(new_file, section_name, dict_of_attr, file_exists=True)

            # Step 4: Create ConfigParser
            neo4j_config = configparser.ConfigParser()
            # Step 5: Read file
            with open(new_file, "r") as f:
                neo4j_config.read_file(f)

            # Step 6: Check section exists
            self.assertTrue(neo4j_config.has_section(section_name))
            # Step 7: Get encoded password
            password = neo4j_config.get(section_name, "password")
            # Step 8: Decode password
            decoded_password = base64.b64decode(password.encode("UTF-8")).decode("UTF-8")
            # Step 9: Check decoded password
            self.assertEqual(decoded_password, "secret123")

        finally:
            # Remove the temporary file
            os.unlink(new_file)

    def test_read_config(self):
        """Test reading configurations from files."""

        # CASE 1: Reading a standard config file with multiple sections
        # Step 1: Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            config_file = temp_file.name

        try:
            # Step 2: Create ConfigParser
            config = configparser.ConfigParser()

            # Step 3: Add section
            config.add_section("cmf")
            # Step 4: Set value
            config.set("cmf", "server-url", "http://example.com")
            # Step 5: Set value
            config.set("cmf", "storage-type", "local")

            # Step 6: Add section
            config.add_section("neo4j")
            # Step 7: Set value
            config.set("neo4j", "user", "neo4j")
            # Step 8: Set encoded password ("password")
            config.set("neo4j", "password", "cGFzc3dvcmQ=")

            # Step 9: Add section
            config.add_section("custom")
            # Step 10: Set value
            config.set("custom", "key1", "value1")
            # Step 11: Set value
            config.set("custom", "key2", "value2")

            # Step 12: Write config to file
            with open(config_file, "w") as f:
                config.write(f)

            # Step 13: Read config using CmfConfig
            result = CmfConfig.read_config(config_file)

            # Step 14: Check value
            self.assertEqual(result["cmf-server-url"], "http://example.com")
            # Step 15: Check value
            self.assertEqual(result["cmf-storage-type"], "local")
            # Step 16: Check value
            self.assertEqual(result["neo4j-user"], "neo4j")
            # Step 17: Check decoded password
            self.assertEqual(result["neo4j-password"], "password")
            # Step 18: Check value
            self.assertEqual(result["custom-key1"], "value1")
            # Step 19: Check value
            self.assertEqual(result["custom-key2"], "value2")

            # CASE 2: Reading an empty file
            # Step 1: Overwrite file with empty content
            with open(config_file, "w") as f:
                f.write("")

            # Step 2: Read config
            empty_result = CmfConfig.read_config(config_file)
            # Step 3: Should be empty dict
            self.assertEqual(empty_result, {})

            # CASE 3: Reading a file with missing neo4j password
            # Step 1: Create ConfigParser
            config = configparser.ConfigParser()
            # Step 2: Add section
            config.add_section("neo4j")
            # Step 3: Set value
            config.set("neo4j", "user", "neo4j")
            # Step 4: Write config
            with open(config_file, "w") as f:
                config.write(f)

            # Step 5: Read config
            missing_pw_result = CmfConfig.read_config(config_file)
            # Step 6: Check value
            self.assertEqual(missing_pw_result["neo4j-user"], "neo4j")
            # Step 7: Password should not be present
            self.assertNotIn("neo4j-password", missing_pw_result)

            # CASE 4: Reading a file with invalid base64 in neo4j password
            # Step 1: Create ConfigParser
            config = configparser.ConfigParser()
            # Step 2: Add section
            config.add_section("neo4j")
            # Step 3: Set value
            config.set("neo4j", "user", "neo4j")
            # Step 4: Set invalid base64 password
            config.set("neo4j", "password", "not-valid-base64!")
            # Step 5: Write config
            with open(config_file, "w") as f:
                config.write(f)

            # Step 6: Expect exception on invalid base64
            with self.assertRaises(Exception):
                CmfConfig.read_config(config_file)

        finally:
            # Remove the temporary file
            os.unlink(config_file)

if __name__ == '__main__':
    unittest.main()
