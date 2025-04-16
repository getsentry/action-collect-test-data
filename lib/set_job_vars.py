#!/usr/bin/env python3
"""
set more GITHUB_ vars

environment variable reference:
    https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/store-information-in-variables#default-environment-variables
"""
from __future__ import annotations

from os import environ
from typing import TYPE_CHECKING
from typing import Any
from typing import Iterator
from typing import TypeAlias

if TYPE_CHECKING:
    from _typeshed import SupportsWrite

Environ: TypeAlias = dict[str, str]
ExitCode: TypeAlias = None | int | str
Lines: TypeAlias = Iterator[str]

# module defaults, to be overridden in test
ENV: Environ = environ.copy()
ENV["DEBUG"] = ENV.get("DEBUG") or "1"
DEBUG = int(ENV["DEBUG"])

del environ  # hygiene -- keep our environment clean!


class UserError(Exception):
    """expected user behavior; suppress stack trace"""


class GithubPermissionError(UserError):
    pass


def info(*msg: object):
    from sys import stderr

    print(*msg, file=stderr)


def tee(msg: object, *files: SupportsWrite[str]):
    for file in files:
        file.write(str(msg) + "\n")


def sh_stdout(cmd: tuple[str, ...]) -> str:
    import shlex
    import subprocess

    if DEBUG > 0:
        info("+", shlex.join(cmd))
    return subprocess.check_output(cmd, encoding="UTF-8", env=ENV)


def gh_app_get_jobs(repo: str, run: str, attempt: str) -> Any:
    import json

    try:
        result = json.loads(
            sh_stdout((
                "gh",
                "api",
                "/".join((
                    "repos",
                    repo,
                    "actions/runs",
                    run,
                    "attempts",
                    attempt,
                    "jobs",
                )),
            ))
        )
    except json.JSONDecodeError:
        return None

    if DEBUG:
        info("JOBS:", json.dumps(result, indent=2))
    return result


def gha_get_jobs():
    return gh_app_get_jobs(
        ENV["GITHUB_REPOSITORY"],
        ENV["GITHUB_RUN_ID"],
        ENV["GITHUB_RUN_ATTEMPT"],
    )


def select_job(jobs: list[dict[str, str]], runner_name: str):
    # NOTE: look at newest jobs first, in case a runner has been reused
    for job in sorted(jobs, key=lambda job: job["created_at"], reverse=True):
        if job["runner_name"] == runner_name:
            return job
    else:
        raise ValueError("no such job found!")


def format_github_env_vars(env: Environ) -> Lines:
    """Format environment variables as a string for the GITHUB_ENV file"""
    # https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/workflow-commands-for-github-actions#environment-files
    for key, val in env.items():
        if "\n" in val:
            sep, end = "<<EOF\n", "\nEOF"
        else:
            sep, end = "=", ""
        yield f"{key}{sep}{val}{end}"


def get_job_vars() -> Environ:
    jobs = gha_get_jobs()
    if jobs is None:
        info("retrying failed command, with debug:")
        ENV["GH_DEBUG"] = "api"
        gha_get_jobs()  # just to show debug output
        raise GithubPermissionError("""

Error: Please update your Github Actions job definition to include the
actions.read permission:

  permissions:
    actions: "read"

""")

    job = select_job(jobs["jobs"], ENV["RUNNER_NAME"])

    return {
        "GITHUB_JOB_ID": str(job["id"]),
        "GITHUB_JOB_NAME": job["name"],
        "GITHUB_MATRIX": ENV["GITHUB_MATRIX"],
        "GITHUB_MATRIX_INDEX": ENV["GITHUB_MATRIX_INDEX"],
        "GITHUB_MATRIX_TOTAL": ENV["GITHUB_MATRIX_TOTAL"],
    }


def set_job_vars() -> Lines:
    job_vars = get_job_vars()
    info("The missing GITHUB_ environment variables:")
    for line in format_github_env_vars(job_vars):
        yield line


def main() -> ExitCode:
    from sys import stdout

    try:
        with open(ENV["GITHUB_ENV"], "a") as GITHUB_ENV:
            for line in set_job_vars():
                tee(line, GITHUB_ENV, stdout)
    except UserError as err:
        tee(err, open(ENV["GITHUB_STEP_SUMMARY"], "a"), stdout)


if __name__ == "__main__":
    raise SystemExit(main())
