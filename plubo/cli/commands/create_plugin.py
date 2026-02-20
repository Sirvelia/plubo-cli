import sys
import subprocess
import json
from pathlib import Path
from plubo.generators.plugin import rename_plugin
from plubo.generators.php_dependency import apply_post_install_actions, get_dependency_package, resolve_dependency
from plubo.utils import project

USAGE = "Usage: pb-cli create <plugin_name> [--lando] [--blade]"
BLADE_PACKAGE = "eftec/bladeone"
BLADE_LOADER_PATHS = (
    "Includes/BladeLoader.php",
    "includes/BladeLoader.php",
    "Includes/bladeloader.php",
    "includes/bladeloader.php",
)


def _parse_create_args(args):
    use_lando = False
    use_blade = False
    name_parts = []

    for arg in args:
        if arg == "--lando":
            use_lando = True
            continue
        if arg == "--blade":
            use_blade = True
            continue

        if arg.startswith("--"):
            print(f"❌ Unknown option: {arg}")
            print(USAGE)
            sys.exit(1)

        name_parts.append(arg)

    new_name = " ".join(name_parts).strip()
    if not new_name:
        print(USAGE)
        sys.exit(1)

    return new_name, use_lando, use_blade


def _confirm_create_in_current_directory():
    print("⚠️ No WordPress installation detected.")
    print(f"The plugin will be created in the current directory: {Path.cwd()}")

    try:
        answer = input("Continue? [y/N]: ").strip().lower()
    except EOFError:
        return False

    return answer in {"y", "yes"}

def _load_composer_require(plugin_directory):
    composer_json_path = plugin_directory / "composer.json"
    if not composer_json_path.exists():
        return {}

    try:
        composer_data = json.loads(composer_json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}

    required_packages = composer_data.get("require", {})
    if not isinstance(required_packages, dict):
        return {}
    return required_packages

def _enable_blade_support(plugin_directory, use_lando):
    messages = []
    dependency_option, _ = resolve_dependency("bladeone")
    package_name = get_dependency_package(dependency_option) or BLADE_PACKAGE
    required_packages = _load_composer_require(plugin_directory)

    if package_name not in required_packages:
        command = (
            ["lando", "composer", "require", package_name]
            if use_lando
            else ["composer", "require", package_name]
        )
        subprocess.run(command, cwd=str(plugin_directory), check=True)
        messages.append(f"Installed `{package_name}`")
    else:
        messages.append(f"Kept existing `{package_name}` dependency")

    messages.extend(apply_post_install_actions(dependency_option, cwd=plugin_directory))
    return messages

def _disable_blade_support(plugin_directory, use_lando):
    messages = []
    required_packages = _load_composer_require(plugin_directory)

    if BLADE_PACKAGE in required_packages:
        command = (
            ["lando", "composer", "remove", BLADE_PACKAGE]
            if use_lando
            else ["composer", "remove", BLADE_PACKAGE]
        )
        subprocess.run(command, cwd=str(plugin_directory), check=True)
        messages.append(f"Removed `{BLADE_PACKAGE}`")
    else:
        messages.append(f"`{BLADE_PACKAGE}` was not installed")

    removed_loader = False
    for relative_path in BLADE_LOADER_PATHS:
        loader_path = plugin_directory / relative_path
        if loader_path.exists():
            loader_path.unlink()
            removed_loader = True
            messages.append(f"Removed `{relative_path}`")

    if not removed_loader:
        messages.append("BladeLoader file was not present")

    return messages


def create_plugin_command(args):
    new_name, use_lando, use_blade = _parse_create_args(args)
    wp_root = project.detect_wp_root()

    if wp_root:
        target_directory = wp_root / "wp-content/plugins"
    else:
        if not _confirm_create_in_current_directory():
            print("❌ Aborted.")
            sys.exit(1)
        target_directory = Path.cwd()

    plugin_name = new_name.lower().replace(" ", "-")
    plugin_directory = target_directory / plugin_name

    command = (
        ["lando", "composer", "create-project", "joanrodas/plubo", plugin_name]
        if use_lando
        else ["composer", "create-project", "joanrodas/plubo", plugin_name]
    )

    try:
        subprocess.run(command, cwd=str(target_directory), check=True)
        rename_plugin("plugin-placeholder", new_name, plugin_directory)
        post_create_messages = (
            _enable_blade_support(plugin_directory, use_lando)
            if use_blade
            else _disable_blade_support(plugin_directory, use_lando)
        )
        print(f"✅ Plugin created and renamed to: {plugin_name}")
        for post_create_message in post_create_messages:
            print(f"ℹ️ {post_create_message}")
    except FileNotFoundError as error:
        missing_command = error.filename or command[0]
        print(f"❌ Command not found: {missing_command}")
        sys.exit(1)
    except subprocess.CalledProcessError as error:
        failed_command = error.cmd if isinstance(error.cmd, list) else [str(error.cmd)]
        print(f"❌ Command failed with exit code {error.returncode}: {' '.join(failed_command)}")
        sys.exit(error.returncode)
