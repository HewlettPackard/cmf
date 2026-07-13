###
# Copyright (2024) Hewlett Packard Enterprise Development LP
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

"""
MAT Test Suite: Git Config Validation Feature
PR: Added git user.name/user.email check before cmf init commands.

Covers:
  - check_git_config() in dvc_wrapper.py
  - GitConfigNotSet exception in cmf_exception_handling.py
  - CmdInitLocal raises GitConfigNotSet when git config is missing
"""

import argparse
import pytest
from unittest.mock import patch

from cmflib.dvc_wrapper import check_git_config
from cmflib.cmf_exception_handling import GitConfigNotSet


# ---------------------------------------------------------------------------
# Suite 1: check_git_config() unit tests
# ---------------------------------------------------------------------------

class TestCheckGitConfig:

    def test_returns_true_when_git_is_configured(self):
        """
        check_git_config() returns True in the current environment.
        Assumes the developer running the tests has git user.name and
        user.email configured (standard requirement for contributing).
        """
        result = check_git_config()
        assert result is True, (
            "Expected check_git_config() to return True.\n"
            "Make sure 'git config user.name' and 'git config user.email' are set."
        )

    def test_returns_false_when_git_config_is_unset(self, unset_git_config):
        """
        check_git_config() returns False when HOME points to an empty directory
        (no ~/.gitconfig) and system config is disabled.
        The unset_git_config fixture handles setup and teardown safely.
        """
        result = check_git_config()
        assert result is False, (
            "Expected check_git_config() to return False when git config is not set."
        )


# ---------------------------------------------------------------------------
# Suite 2: GitConfigNotSet exception tests
# ---------------------------------------------------------------------------

class TestGitConfigNotSetException:

    def test_return_code_is_127(self):
        """GitConfigNotSet uses return code 127 (command not configured)."""
        exc = GitConfigNotSet()
        assert exc.return_code == 127

    def test_status_is_failure(self):
        """GitConfigNotSet is a CmfFailure — status must be 'failure'."""
        exc = GitConfigNotSet()
        assert exc.status == "failure"

    def test_handle_contains_missing_config_names(self):
        """handle() includes the names of the missing config keys."""
        exc = GitConfigNotSet(missing_configs=["user.name", "user.email"])
        message = exc.handle()
        assert "user.name" in message
        assert "user.email" in message

    def test_handle_contains_fix_instructions(self):
        """handle() tells the user how to fix the problem with git config commands."""
        exc = GitConfigNotSet(missing_configs=["user.name", "user.email"])
        message = exc.handle()
        assert "git config --global user.name" in message
        assert "git config --global user.email" in message

    def test_handle_default_when_no_configs_provided(self):
        """handle() produces a meaningful message even when missing_configs is empty."""
        exc = GitConfigNotSet()
        message = exc.handle()
        assert "ERROR" in message
        assert "git" in message.lower()


# ---------------------------------------------------------------------------
# Suite 3: CmdInitLocal raises GitConfigNotSet when git config is missing
# ---------------------------------------------------------------------------

class TestCmdInitLocalGitConfigCheck:

    def test_init_local_raises_git_config_not_set(self, real_env, unset_git_config):
        """
        CmdInitLocal.run() raises GitConfigNotSet when git config is missing.

        Without --real-env: patches check_git_config to return False (no system changes).
        With    --real-env: git user.name/email are temporarily unset via unset_git_config
                            fixture, so check_git_config() returns False for real.
        """
        from cmflib.commands.init.local import CmdInitLocal

        args = argparse.Namespace(
            path=None,
            git_remote_url=None,
            neo4j_user=None,
            neo4j_password=None,
            neo4j_uri=None,
            cmf_server_url="http://127.0.0.1:80",
        )

        cmd = CmdInitLocal(args)

        if real_env:
            # Real env: git config is actually unset by unset_git_config fixture
            with pytest.raises(GitConfigNotSet):
                cmd.run(live=None)
        else:
            # Patched: simulate missing git config without touching system
            with patch("cmflib.commands.init.local.check_git_config", return_value=False):
                with pytest.raises(GitConfigNotSet):
                    cmd.run(live=None)

    def test_init_local_does_not_raise_when_git_config_is_set(self, real_env):
        """
        CmdInitLocal.run() does NOT raise GitConfigNotSet when git config is valid.

        Without --real-env: patches check_git_config to return True (no system changes).
        With    --real-env: uses your actual git config (which must be set).
        """
        from cmflib.commands.init.local import CmdInitLocal

        args = argparse.Namespace(
            path=None,
            git_remote_url=None,
            neo4j_user=None,
            neo4j_password=None,
            neo4j_uri=None,
            cmf_server_url="http://127.0.0.1:80",
        )

        cmd = CmdInitLocal(args)

        if real_env:
            # Real env: your actual git config is used
            with pytest.raises(Exception) as exc_info:
                cmd.run(live=None)
            assert not isinstance(exc_info.value, GitConfigNotSet), (
                "GitConfigNotSet should not be raised when git config is valid."
            )
        else:
            # Patched: simulate valid git config
            with patch("cmflib.commands.init.local.check_git_config", return_value=True):
                with pytest.raises(Exception) as exc_info:
                    cmd.run(live=None)
                assert not isinstance(exc_info.value, GitConfigNotSet), (
                    "GitConfigNotSet should not be raised when git config is valid."
                )
