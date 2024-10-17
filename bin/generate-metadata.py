#!/usr/bin/env python3
from __future__ import annotations

import grp
import os
import pwd
import socket
import sys
import time

Environ = dict[str, str]


def relevant_env_var(var: str) -> bool:
    # prefixes and suffixes of environment vars that we may want during
    # debugging, test-result analysis, or traceback normalization
    return var.endswith(("HOME", "PATH")) or var.startswith((
        "USER",
        "HOME",
        "HOST",
        "XDG",
        "LOG",
        "PWD",
        "TMP",
        "PYTHON",
        "PYTEST",
        "PIP",
        "NODE",
        "GITHUB",
        "RUNNER",
        "CI",
        "MATRIX",
        "TEST",
    ))


def get_env(env: Environ) -> Environ:
    """Keep the relevant parts of the environment variables."""
    result: Environ = {}

    for var, val in sorted(env.items()):
        if relevant_env_var(var):
            result[var] = env[var]
        else:
            print(f"skipping irrelevant env var: {var}={val}", file=sys.stderr)
    return result


def generate_test_metadata():
    uid = os.getuid()
    gid = os.getgid()
    pw = pwd.getpwuid(uid)
    gr = grp.getgrgid(gid)

    return {
        "time_ns": time.time_ns(),
        "cwd": os.getcwd(),
        "host": socket.getfqdn(),
        "uid": uid,
        "username": pw.pw_name,
        "home": pw.pw_dir,
        "gid": gid,
        "group": gr.gr_name,
        "env": get_env(dict(os.environ)),
    }


def main():
    import json

    print(json.dumps(generate_test_metadata(), indent=2))


if __name__ == "__main__":
    raise SystemExit(main())
