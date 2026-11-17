###
# Copyright (2026) Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###

"""Offline tests for the OSDF remote: no origin, cache or token needed."""

import os
import shutil
import subprocess
import tempfile
import unittest

from cmflib.dvc_wrapper import dvc_add_secret_attribute


@unittest.skipUnless(shutil.which("dvc") and shutil.which("git"), "needs the dvc and git CLIs")
class TestSecretStaysOutOfGit(unittest.TestCase):
    def setUp(self):
        self.cwd = os.getcwd()
        self.repo = tempfile.mkdtemp()
        os.chdir(self.repo)
        for cmd in (["git", "init", "-q"], ["dvc", "init", "-q"],
                    ["dvc", "remote", "add", "-d", "osdf", "https://origin.example.org/ns"],
                    # what cmflib before this change wrote
                    ["dvc", "remote", "modify", "osdf", "password", "Bearer old"]):
            subprocess.run(cmd, check=True, capture_output=True)

    def tearDown(self):
        os.chdir(self.cwd)
        shutil.rmtree(self.repo)

    def _read(self, path):
        with open(path) as f:
            return f.read()

    def test_password_moves_to_local_config(self):
        self.assertTrue(dvc_add_secret_attribute("osdf", "password", "Bearer new"))
        self.assertNotIn("password", self._read(".dvc/config"))
        self.assertIn("Bearer new", self._read(".dvc/config.local"))
        merged = subprocess.run(["dvc", "config", "-l"], check=True, capture_output=True, text=True).stdout
        self.assertIn("remote.osdf.password=Bearer new", merged)

    def test_local_config_is_git_ignored(self):
        dvc_add_secret_attribute("osdf", "password", "Bearer new")
        ignored = subprocess.run(["git", "check-ignore", "-q", ".dvc/config.local"])
        self.assertEqual(ignored.returncode, 0)


if __name__ == "__main__":
    unittest.main()
