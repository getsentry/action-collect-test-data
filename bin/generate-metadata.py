#!/usr/bin/env python3
import grp
import os
import pwd
import socket

Environ = dict[str, str]


def relevant_env_var(var: str) -> bool:
    # prefixes and suffixes of environment vars that we may want during
    # debugging, test-result analysis, or traceback normalization
    return var.endswith(("HOME", "PATH")) or var.startswith(
        (
            "USER",
            "HOME",
            "HOST",
            "XDG",
            "LOG",
            "PWD",
            "TMP",
            "PYTHON",
            "GITHUB",
            "RUNNER",
            "CI",
        )
    )


def get_env(env: Environ) -> Environ:
    """Keep the relevant parts of the environment variables."""
    relevant_vars = sorted(var for var in env if relevant_env_var(var))
    return {var: env[var] for var in relevant_vars}


def generate_test_metadata():
    uid = os.getuid()
    gid = os.getgid()
    pw = pwd.getpwuid(uid)
    gr = grp.getgrgid(gid)

    return {
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
