import sys
import re
import subprocess
from plubo.generators.node_dependency import DEPENDENCY_OPTIONS


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

def add_node_dependency_command(args):
    if not args:
        print("Usage: plubo node-dep <package|preset>")
        print("Example presets: alpinejs, tailwind-css, daisy-ui, hikeflow")
        sys.exit(1)

    package_input = " ".join(args).strip()
    package_name = _resolve_package(package_input)
    command = ["yarn", "add"] + package_name.split()

    try:
        subprocess.run(command, check=True)
        print(f"✅ Successfully installed: {package_name}")
    except FileNotFoundError:
        print(f"❌ Command not found: {command[0]}")
        sys.exit(1)
    except subprocess.CalledProcessError as error:
        print(f"❌ Installation failed (exit code {error.returncode}): {' '.join(command)}")
        sys.exit(error.returncode)
