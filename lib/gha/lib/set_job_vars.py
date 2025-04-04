#!/usr/bin/env python3
"""
set more GITHUB_ vars

environment variable reference:
    https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/store-information-in-variables#default-environment-variables
"""
from __future__ import annotations

from typing import Any
from typing import TypeAlias

Environ: TypeAlias = dict[str, str]
ExitCode: TypeAlias = None | int | str

class NoJSONError(Exception): pass


def sh_json(cmd: tuple[str, ...], env: Environ) -> Any:
    import json
    import shlex
    import subprocess
    import sys

    print("+", shlex.join(cmd), file=sys.stderr)
    result = subprocess.run(cmd, stdout=subprocess.PIPE, env=env)
    if result.returncode != 0:
      raise NoJSONError
    return json.loads(result.stdout)


def gha_get_jobs(env: Environ, debug: bool = False):
    if debug:
        env = env.copy()
        env["GH_DEBUG"] = "api"

    try:
        return sh_json(
            (
                "gh",
                "api",
                "/".join((
                    "repos",
                    env["GITHUB_REPOSITORY"],
                    "actions/runs",
                    env["GITHUB_RUN_ID"],
                    "attempts",
                    env["GITHUB_RUN_ATTEMPT"],
                    "jobs",
                )),
            ),
            env,
        )
    except NoJSONError:
        return None


def select_job(jobs: list[dict[str, str]], runner_name: str):
    # NOTE: look at newest jobs first, in case a runner has been reused
    for job in sorted(jobs, key=lambda job: job['created_at'], reverse=True):
        if job["runner_name"] == runner_name:
            return job
    else:
        raise ValueError("no such job found!")


def set_job_vars(env: Environ) -> ExitCode:
    if (jobs := gha_get_jobs(env)) is None:
        print("retrying failed command, with debug:")
        if (jobs := gha_get_jobs(env, debug=True)) is None:
            error_message = """

Error: Please update your Github Actions job definition to include the
actions.read permission:

  permissions:
    actions: "read"

"""
            print(error_message, file=open(env["GITHUB_STEP_SUMMARY"], "a"))
            return error_message

    job = select_job(jobs['jobs'], env["RUNNER_NAME"])

    print("The missing GITHUB_ environment variables:")
    env_vars = f"""\
GITHUB_JOB_ID={job["id"]}
GITHUB_JOB_NAME={job["name"]}
GITHUB_MATRIX={env["GITHUB_MATRIX"]}
GITHUB_MATRIX_INDEX={env["GITHUB_MATRIX_INDEX"]}
GITHUB_MATRIX_TOTAL={env["GITHUB_MATRIX_TOTAL"]}
"""
    print(env_vars)
    print(env_vars, file=open(env["GITHUB_ENV"], "a"))


def main() -> ExitCode:
    from os import environ

    return set_job_vars(env=dict(environ))


if __name__ == "__main__":
    raise SystemExit(main())
