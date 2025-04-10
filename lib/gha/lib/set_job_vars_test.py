#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest import mock

import pytest
import set_job_vars as M  # the module under test


class DescribeShStdout:
    def it_captures_command_output(self, capfd: pytest.CaptureFixture[str]):
        result = M.sh_stdout(("echo", "test output"))
        assert result == "test output\n"
        captured = capfd.readouterr()
        assert "+ echo 'test output'\n" == captured.err
        assert "" == captured.out

    def it_handles_command_failures(self):
        with pytest.raises(Exception):
            M.sh_stdout(("false",))

    def it_respects_debug_level(self, capfd: pytest.CaptureFixture[str]):
        with mock.patch.object(M, "DEBUG", 0):
            M.sh_stdout(("echo", "silent"))
        assert capfd.readouterr() == ("", "")


class DescribeGhAppGetJobs:
    def it_fetches_jobs_data(self):
        with mock.patch.object(M, "sh_stdout", return_value='{"jobs": []}'):
            result = M.gh_app_get_jobs("owner/repo", "run_id", "attempt_id")
        assert result == {"jobs": []}

    def it_handles_json_parse_errors(self):
        with mock.patch.object(M, "sh_stdout", return_value="invalid json"):
            result = M.gh_app_get_jobs("owner/repo", "run_id", "attempt_id")
        assert result is None


class DescribeGhaGetJobs:
    def it_calls_gh_app_get_jobs_with_env_vars(self):
        """Test gha_get_jobs calls gh_app_get_jobs with environment variables."""

        def fake_sh_stdout(cmd: tuple[str, ...]) -> str:
            assert cmd == (
                "gh",
                "api",
                "repos/test/repo/actions/runs/run123/attempts/attempt1/jobs",
            )
            return ""

        with mock.patch.object(
            M,
            "ENV",
            {
                "GITHUB_REPOSITORY": "test/repo",
                "GITHUB_RUN_ID": "run123",
                "GITHUB_RUN_ATTEMPT": "attempt1",
            },
        ):
            with mock.patch.object(M, "sh_stdout", fake_sh_stdout):
                M.gha_get_jobs()


class DescribeSelectJob:
    def it_selects_job_by_runner_name(self):
        jobs = [
            {"runner_name": "runner1", "created_at": "2023-01-01", "id": "1"},
            {"runner_name": "runner2", "created_at": "2023-01-02", "id": "2"},
        ]

        job = M.select_job(jobs, "runner2")
        assert job["id"] == "2"

    def it_prefers_newest_job_for_same_runner(self):
        jobs = [
            {"runner_name": "runner1", "created_at": "2023-01-01", "id": "1"},
            {"runner_name": "runner1", "created_at": "2023-01-02", "id": "2"},
        ]

        job = M.select_job(jobs, "runner1")
        assert job["id"] == "2"

    def it_raises_exception_when_no_matching_job(self):
        jobs = [{"runner_name": "runner1", "created_at": "2023-01-01"}]

        with pytest.raises(ValueError, match="no such job found!"):
            M.select_job(jobs, "missing_runner")


class DescribeEnvironmentVariableFormatting:
    def it_formats_simple_values(self):
        env = {"KEY1": "value1", "KEY2": "value2"}

        assert list(M.format_github_env_vars(env)) == [
            "KEY1=value1",
            "KEY2=value2",
        ]

    def it_formats_multiline_values(self):
        env = {"MULTILINE": "line1\nline2\nline3"}

        assert list(M.format_github_env_vars(env)) == [
            "MULTILINE<<EOF\nline1\nline2\nline3\nEOF"
        ]

    def it_handles_empty_env(self):
        assert list(M.format_github_env_vars({})) == []


class DescribeGetJobVars:
    def it_gets_job_variables(self):
        mock_jobs = {
            "jobs": [{
                "id": "job123",
                "name": "test job",
                "runner_name": "test-runner",
                "created_at": "2023-01-01",
            }]
        }

        with mock.patch.object(M, "gha_get_jobs", return_value=mock_jobs):
            with mock.patch.object(
                M,
                "ENV",
                {
                    "RUNNER_NAME": "test-runner",
                    "GITHUB_MATRIX": "{}",
                    "GITHUB_MATRIX_INDEX": "0",
                    "GITHUB_MATRIX_TOTAL": "1",
                },
            ):
                job_vars = M.get_job_vars()

        assert job_vars == {
            "GITHUB_JOB_ID": "job123",
            "GITHUB_JOB_NAME": "test job",
            "GITHUB_MATRIX": "{}",
            "GITHUB_MATRIX_INDEX": "0",
            "GITHUB_MATRIX_TOTAL": "1",
        }

    def it_is_helpful_on_failure(self, capfd: pytest.CaptureFixture[str]):
        """it should retry with debug, then show permission help"""
        with mock.patch.object(M, "gha_get_jobs", return_value=None):
            with pytest.raises(M.GithubPermissionError) as err:
                M.get_job_vars()

        assert err.match("update your Github Action")
        assert err.match('actions: "read"')

        captured = capfd.readouterr()
        assert "retrying failed command, with debug:\n" == captured.err
        assert "" == captured.out


class DescribeSetJobVars:
    def it_returns_formatted_job_vars(self, capfd: pytest.CaptureFixture[str]):
        mock_job_vars = {
            "GITHUB_JOB_ID": "job123",
            "GITHUB_JOB_NAME": "test job",
        }

        with mock.patch.object(M, "get_job_vars", return_value=mock_job_vars):
            lines = list(M.set_job_vars())

        assert lines == ["GITHUB_JOB_ID=job123", "GITHUB_JOB_NAME=test job"]

        captured = capfd.readouterr()
        assert "The missing GITHUB_ environment variables:\n" == captured.err
        assert "" == captured.out


class DescribeMainFunctionality:

    def run(self, tmp_path: Path, fake_set_job_vars: Any):
        env_file = tmp_path / "github_env"
        summary_file = tmp_path / "summary"

        with (
            mock.patch.object(M, "set_job_vars", fake_set_job_vars),
            mock.patch.object(
                M,
                "ENV",
                {
                    "GITHUB_ENV": str(env_file),
                    "GITHUB_STEP_SUMMARY": str(summary_file),
                },
            ),
        ):
            M.main()
        return env_file, summary_file

    def assert_expected(
        self, outfile: Path, capfd: pytest.CaptureFixture[str], expected: str
    ):
        assert outfile.read_text() == expected

        captured = capfd.readouterr()
        assert captured.out == expected
        assert captured.err == ""

    def it_writes_variables_to_github_env_file(
        self, capfd: pytest.CaptureFixture[str], tmp_path: Path
    ):
        """Test main writes variables to GITHUB_ENV file."""

        def fake_set_job_vars() -> M.Lines:
            yield "line1"
            yield "line2"

        env_file, _ = self.run(tmp_path, fake_set_job_vars)
        self.assert_expected(env_file, capfd, "line1\nline2\n")

    def it_writes_error_to_step_summary_on_user_error(
        self, capfd: pytest.CaptureFixture[str], tmp_path: Path
    ):
        error_message = "Test user error"

        def fake_set_job_vars() -> M.Lines:
            raise M.UserError(error_message)

        _, summary_file = self.run(tmp_path, fake_set_job_vars)
        self.assert_expected(summary_file, capfd, error_message + "\n")
