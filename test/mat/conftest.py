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

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--real-env",
        action="store_true",
        default=False,
        help=(
            "Run tests against your REAL environment.\n"
            "  - Git config tests will temporarily unset your actual git user.name/user.email.\n"
            "  - Values are saved and fully restored after each test.\n"
            "Without this flag, tests use patching/mocking — your environment is never touched."
        ),
    )


@pytest.fixture
def real_env(request):
    """Returns True if --real-env flag was passed, False otherwise."""
    return request.config.getoption("--real-env")


def pytest_configure(config):
    use_real = config.getoption("--real-env", default=False)
    mode = "REAL ENVIRONMENT" if use_real else "PATCHED/MOCKED (safe default)"
    print(f"\n[MAT Framework] Running in mode: {mode}")
    if use_real:
        print(
            "[MAT Framework] WARNING: Tests will temporarily modify your git config.\n"
            "                         Values will be restored automatically after each test."
        )
    else:
        print(
            "[MAT Framework] INFO: No real environment changes will be made.\n"
            "                      To test against your real environment, run with --real-env flag."
        )


@pytest.fixture
def unset_git_config(real_env, tmp_path, monkeypatch):
    """
    Simulates or actually creates an environment where git user.name and
    user.email are not configured, depending on the --real-env flag.

    Without --real-env (default):
        Uses monkeypatch to point HOME to an empty temp dir and disables
        system git config. Your real git config is never touched.

    With --real-env:
        Saves your actual git user.name and user.email, unsets them globally,
        then restores them after the test — regardless of pass/fail.
    """
    import subprocess

    if not real_env:
        # Safe default: patch environment variables only
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
        yield
    else:
        # Real environment: save → unset → restore
        name_result = subprocess.run(
            ["git", "config", "--global", "user.name"],
            capture_output=True, text=True
        )
        email_result = subprocess.run(
            ["git", "config", "--global", "user.email"],
            capture_output=True, text=True
        )
        saved_name = name_result.stdout.strip()
        saved_email = email_result.stdout.strip()

        subprocess.run(["git", "config", "--global", "--unset", "user.name"])
        subprocess.run(["git", "config", "--global", "--unset", "user.email"])

        try:
            yield
        finally:
            # Always restore, even if test fails
            if saved_name:
                subprocess.run(["git", "config", "--global", "user.name", saved_name])
            if saved_email:
                subprocess.run(["git", "config", "--global", "user.email", saved_email])
