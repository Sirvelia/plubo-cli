"""PyInstaller runtime hook.

Prevents bundled OpenSSL/libcurl libraries from leaking into child processes
(`composer`, `php`, `git`, etc.), which can otherwise cause version conflicts
with system libraries in target containers.
"""

import os
import subprocess


_ORIGINAL_POPEN = subprocess.Popen
_LIB_PATH_KEYS = ("LD_LIBRARY_PATH", "DYLD_LIBRARY_PATH", "LIBPATH")


def _sanitized_subprocess_env(env):
    base_env = dict(os.environ if env is None else env)

    for key in _LIB_PATH_KEYS:
        original_key = f"{key}_ORIG"
        if original_key in os.environ:
            base_env[key] = os.environ[original_key]
        else:
            base_env.pop(key, None)

    return base_env


class _SanitizedEnvPopen(_ORIGINAL_POPEN):
    def __init__(self, *args, **kwargs):
        kwargs["env"] = _sanitized_subprocess_env(kwargs.get("env"))
        super().__init__(*args, **kwargs)


subprocess.Popen = _SanitizedEnvPopen
