import sys
import re
import subprocess
from plubo.generators.php_dependency import DEPENDENCY_OPTIONS
from plubo.utils import project


def _normalize_token(value):
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _resolve_package(value):
    normalized_value = _normalize_token(value)

    for option, package_name in DEPENDENCY_OPTIONS.items():
        if not package_name:
            continue

        candidate_tokens = {
            _normalize_token(option),
            _normalize_token(package_name),
        }
        candidate_tokens.update(_normalize_token(token) for token in package_name.split())

        if normalized_value in candidate_tokens:
            return package_name

    return value

def add_php_dependency_command(args):
    if not args:
        print("Usage: plubo php-dep <package|preset>")
        print("Example presets: routes, roles, logs, checks, jwt")
        sys.exit(1)

    package_input = " ".join(args).strip()
    package_name = _resolve_package(package_input)
    command = (
        ["lando", "composer", "require"] + package_name.split()
        if project.is_lando_project()
        else ["composer", "require"] + package_name.split()
    )

    try:
        subprocess.run(command, check=True)
        print(f"✅ Successfully installed: {package_name}")
    except FileNotFoundError:
        print(f"❌ Command not found: {command[0]}")
        sys.exit(1)
    except subprocess.CalledProcessError as error:
        print(f"❌ Installation failed (exit code {error.returncode}): {' '.join(command)}")
        sys.exit(error.returncode)
