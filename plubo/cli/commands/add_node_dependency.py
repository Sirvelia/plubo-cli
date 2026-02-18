import sys
import subprocess
from plubo.generators.node_dependency import (
    apply_post_install_actions,
    get_dependency_packages,
    resolve_dependency,
)


def _parse_args(args):
    install_as_dev = False
    package_tokens = []

    for arg in args:
        if arg in {"-D", "--dev"}:
            install_as_dev = True
            continue
        package_tokens.append(arg)

    return package_tokens, install_as_dev

def _build_commands(packages):
    regular_packages = [package["name"] for package in packages if not package["dev"]]
    dev_packages = [package["name"] for package in packages if package["dev"]]
    commands = []

    if regular_packages:
        commands.append(["yarn", "add"] + regular_packages)
    if dev_packages:
        commands.append(["yarn", "add", "--dev"] + dev_packages)

    return commands

def add_node_dependency_command(args):
    if not args:
        print("Usage: plubo node-dep [--dev|-D] <package|preset>")
        print("Example presets: alpinejs, tailwind-css, daisy-ui, hikeflow")
        print("Use --dev/-D to install custom packages as devDependencies.")
        sys.exit(1)

    package_tokens, install_as_dev = _parse_args(args)
    if not package_tokens:
        print("Usage: plubo node-dep [--dev|-D] <package|preset>")
        sys.exit(1)

    package_input = " ".join(package_tokens).strip()
    dependency_option, is_preset = resolve_dependency(package_input)
    packages = get_dependency_packages(dependency_option)

    if not is_preset and install_as_dev:
        for package in packages:
            package["dev"] = True

    commands = _build_commands(packages)
    package_display = ", ".join(package["name"] for package in packages)

    try:
        for command in commands:
            subprocess.run(command, check=True)
        post_install_messages = apply_post_install_actions(dependency_option)
        print(f"✅ Successfully installed: {package_display}")
        for post_install_message in post_install_messages:
            print(f"ℹ️ {post_install_message}")
    except FileNotFoundError:
        print(f"❌ Command not found: {commands[0][0]}")
        sys.exit(1)
    except subprocess.CalledProcessError as error:
        print(f"❌ Installation failed (exit code {error.returncode}): {' '.join(command)}")
        sys.exit(error.returncode)
