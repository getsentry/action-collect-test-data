#!/usr/bin/env python3
from __future__ import annotations

import os
import socket
import time
from unittest import mock

import generate_metadata as M  # the module under test
import pytest


class DescribeRelevantEnvVar:
    def it_identifies_relevant_environment_variables(self):
        # Positive cases
        assert M.relevant_env_var("HOME") is True
        assert M.relevant_env_var("PATH") is True
        assert M.relevant_env_var("USER") is True
        assert M.relevant_env_var("PYTHONPATH") is True
        assert M.relevant_env_var("GITHUB_TOKEN") is True
        assert M.relevant_env_var("TEST_RESULT") is True

        # Negative cases
        assert M.relevant_env_var("IRRELEVANT") is False
        assert M.relevant_env_var("SECRET_KEY") is False


class DescribeGetEnv:
    def it_keeps_only_relevant_environment_variables(
        self, capfd: pytest.CaptureFixture[str]
    ):
        test_env = {
            "HOME": "/home/user",
            "PATH": "/usr/bin:/bin",
            "USER": "testuser",
            "IRRELEVANT": "should_be_skipped",
            "SECRET": "should_be_skipped_too",
        }

        result = M.get_env(test_env)

        # Check that relevant variables are kept
        assert result == {
            "HOME": "/home/user",
            "PATH": "/usr/bin:/bin",
            "USER": "testuser",
        }

        # Check that we logged the skipped variables
        captured = capfd.readouterr()
        assert captured.out == ""
        assert captured.err == """\
skipping irrelevant env var: IRRELEVANT=should_be_skipped
skipping irrelevant env var: SECRET=should_be_skipped_too
"""
        assert (
            "skipping irrelevant env var: IRRELEVANT=should_be_skipped"
            in captured.err
        )
        assert (
            "skipping irrelevant env var: SECRET=should_be_skipped_too"
            in captured.err
        )


class DescribeGenerateTestMetadata:
    def it_generates_complete_metadata(self):
        # fake all external calls to make the test deterministic
        fake_time_ns = 1617979146000000000
        fake_cwd = "/test/directory"
        fake_hostname = "test-host.example.com"
        fake_uid = 1000
        fake_username = "testuser"
        fake_home = "/home/testuser"
        fake_gid = 1000
        fake_group = "testgroup"
        fake_env = {"HOME": fake_home, "USER": fake_username}

        with (
            mock.patch.object(time, "time_ns", return_value=fake_time_ns),
            mock.patch.object(os, "getcwd", return_value=fake_cwd),
            mock.patch.object(socket, "getfqdn", return_value=fake_hostname),
            mock.patch.object(os, "getuid", return_value=fake_uid),
            mock.patch.object(os, "getgid", return_value=fake_gid),
            mock.patch.object(os, "environ", fake_env),
            mock.patch("pwd.getpwuid") as mock_getpwuid,
            mock.patch("grp.getgrgid") as mock_getgrgid,
        ):

            # Set up the mocked pwd and grp returns
            mock_pw = mock_getpwuid.return_value
            mock_pw.pw_name = fake_username
            mock_pw.pw_dir = fake_home

            mock_getgrgid.return_value.gr_name = fake_group

            # Run the function
            result = M.generate_test_metadata()

        # Verify the result
        assert result == {
            "time_ns": fake_time_ns,
            "cwd": fake_cwd,
            "host": fake_hostname,
            "uid": fake_uid,
            "username": fake_username,
            "home": fake_home,
            "gid": fake_gid,
            "group": fake_group,
            "env": fake_env,
        }


class DescribeMain:
    def it_prints_metadata_as_json(self, capfd: pytest.CaptureFixture[str]):
        # Create a simplified metadata for testing
        test_metadata = {
            "time_ns": 1617979146000000000,
            "host": "test-host",
            "env": {"USER": "testuser"},
        }

        with mock.patch.object(
            M, "generate_test_metadata", return_value=test_metadata
        ):
            M.main()

        # Check the printed output
        captured = capfd.readouterr()

        # We don't need to test the exact formatting, just that it contains our data
        assert '"time_ns": 1617979146000000000' in captured.out
        assert '"host": "test-host"' in captured.out
        assert '"USER": "testuser"' in captured.out
