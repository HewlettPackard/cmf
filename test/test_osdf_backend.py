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
import unittest.mock

from cmflib.cmf_exception_handling import MsgFailure
from cmflib.dvc_wrapper import dvc_add_secret_attribute
from cmflib.utils.helper_functions import OSDF_TOKEN_DISCOVER, discover_bearer_token, resolve_osdf_token


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


@unittest.skipUnless(shutil.which("dvc") and shutil.which("git"), "needs the dvc and git CLIs")
class TestInitOsdfRemote(unittest.TestCase):
    TOKEN = "header.payload.signature"

    def setUp(self):
        self.cwd = os.getcwd()
        self.repo = tempfile.mkdtemp()
        os.chdir(self.repo)
        subprocess.run(["git", "init", "-q"], check=True)
        subprocess.run(["git", "config", "user.name", "t"], check=True)
        subprocess.run(["git", "config", "user.email", "t@example.org"], check=True)
        with open("token", "w") as f:
            f.write(self.TOKEN + "\n")

    def tearDown(self):
        os.chdir(self.cwd)
        shutil.rmtree(self.repo)

    def _init(self, *extra):
        from cmflib import cli
        args = cli.parse_args(["init", "osdfremote", "--path", "https://origin.example.org:8443/ns/cmf",
                               "--access-token", os.path.join(self.repo, "token"),
                               "--git-remote-url", "https://example.org/repo.git", *extra])
        args.func(args).do_run()
        with open(".dvc/config") as f:
            project = f.read()
        with open(".dvc/config.local") as f:
            local = f.read()
        from cmflib.utils.cmf_config import CmfConfig
        return project, local, CmfConfig.read_config(".cmfconfig")

    def test_defaults_verify_tls_and_keep_token_local(self):
        project, local, cmf_config = self._init()
        self.assertNotIn("ssl_verify", project)
        self.assertNotIn(self.TOKEN, project)
        self.assertIn("Bearer " + self.TOKEN, local)
        self.assertEqual(cmf_config["osdf-ssl_verify"], "true")

    def test_no_ssl_verify_is_opt_in(self):
        project, _, cmf_config = self._init("--no-ssl-verify")
        self.assertIn("ssl_verify = false", project)
        self.assertEqual(cmf_config["osdf-ssl_verify"], "false")

    def test_falls_back_to_wlcg_discovery(self):
        from cmflib import cli
        args = cli.parse_args(["init", "osdfremote", "--path", "https://origin.example.org:8443/ns/cmf",
                               "--git-remote-url", "https://example.org/repo.git"])
        env = {"BEARER_TOKEN": "from-env", "HOME": self.repo}
        with unittest.mock.patch.dict(os.environ, env):
            args.func(args).do_run()
            from cmflib.utils.cmf_config import CmfConfig
            cmf_config = CmfConfig.read_config(".cmfconfig")
            self.assertEqual(cmf_config["osdf-access_token"], OSDF_TOKEN_DISCOVER)
            self.assertEqual(resolve_osdf_token(cmf_config, {})[0], "Bearer from-env")


class TestTokenResolution(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        patcher = unittest.mock.patch.dict(os.environ, {"XDG_RUNTIME_DIR": self.dir}, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(shutil.rmtree, self.dir)

    def _write(self, name, text):
        path = os.path.join(self.dir, name)
        with open(path, "w") as f:
            f.write(text)
        return path

    @unittest.skipIf(os.path.exists(f"/tmp/bt_u{os.getuid()}"), "a real /tmp/bt_u<uid> token is present")
    def test_discovery_order(self):
        self.assertEqual(discover_bearer_token(), (None, None))
        self._write(f"bt_u{os.getuid()}", "runtime\n")
        self.assertEqual(discover_bearer_token()[0], "runtime")
        os.environ["BEARER_TOKEN_FILE"] = self._write("tokfile", "file\n")
        self.assertEqual(discover_bearer_token()[0], "file")
        os.environ["BEARER_TOKEN"] = "env"
        self.assertEqual(discover_bearer_token(), ("env", "$BEARER_TOKEN"))

    def test_token_file_is_reread(self):
        path = self._write("tok", "one\n")
        config = {"osdf-access_token": path}
        self.assertEqual(resolve_osdf_token(config, {})[0], "Bearer one")
        self._write("tok", "two\n")
        self.assertEqual(resolve_osdf_token(config, {})[0], "Bearer two")

    def test_missing_token_file_is_an_error_not_a_token(self):
        with self.assertRaises(MsgFailure):
            resolve_osdf_token({"osdf-access_token": os.path.join(self.dir, "gone")}, {})

    def test_raw_token_from_init_is_read_back_from_dvc_config(self):
        password, _ = resolve_osdf_token({"osdf-access_token": "provided"},
                                         {"remote.osdf.password": "Bearer raw"})
        self.assertEqual(password, "Bearer raw")

    @unittest.skipIf(os.path.exists(f"/tmp/bt_u{os.getuid()}"), "a real /tmp/bt_u<uid> token is present")
    def test_discover_without_token_is_an_error(self):
        with self.assertRaises(MsgFailure):
            resolve_osdf_token({"osdf-access_token": OSDF_TOKEN_DISCOVER}, {})


if __name__ == "__main__":
    unittest.main()
