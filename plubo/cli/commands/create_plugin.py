import sys
import subprocess
import json
import re
from pathlib import Path
from plubo.generators.plugin import rename_plugin
from plubo.generators.php_dependency import apply_post_install_actions, get_dependency_package, resolve_dependency
from plubo.utils import project

USAGE = (
    "Usage: pb-cli create <plugin_name> [--lando] [--blade] "
    "[--plugin-name <name>] [--plugin-uri <url>] [--author <name>] "
    "[--author-uri <url>] [--description <text>] "
    "[--requires-plugins <plugins>] [--version <version>]"
)
BLADE_PACKAGE = "eftec/bladeone"
BLADE_LOADER_PATHS = (
    "Includes/BladeLoader.php",
    "includes/BladeLoader.php",
    "Includes/bladeloader.php",
    "includes/bladeloader.php",
)
HEADER_OPTION_TO_LABEL = {
    "--plugin-name": "Plugin Name",
    "--plugin-uri": "Plugin URI",
    "--author": "Author",
    "--author-uri": "Author URI",
    "--description": "Description",
    "--requires-plugins": "Requires Plugins",
    "--version": "Version",
}


def _parse_create_args(args):
    use_lando = False
    use_blade = False
    name_parts = []
    header_updates = {}
    index = 0

    while index < len(args):
        arg = args[index]
        if arg == "--lando":
            use_lando = True
            index += 1
            continue
        if arg == "--blade":
            use_blade = True
            index += 1
            continue

        if arg in HEADER_OPTION_TO_LABEL:
            if index + 1 >= len(args):
                print(f"❌ Missing value for option: {arg}")
                print(USAGE)
                sys.exit(1)

            value = args[index + 1].strip()
            if not value:
                print(f"❌ Empty value is not allowed for option: {arg}")
                print(USAGE)
                sys.exit(1)

            header_updates[HEADER_OPTION_TO_LABEL[arg]] = value
            index += 2
            continue

        matched_inline_option = False
        for option, header_label in HEADER_OPTION_TO_LABEL.items():
            prefix = f"{option}="
            if arg.startswith(prefix):
                value = arg[len(prefix):].strip()
                if not value:
                    print(f"❌ Empty value is not allowed for option: {option}")
                    print(USAGE)
                    sys.exit(1)

                header_updates[header_label] = value
                matched_inline_option = True
                break

        if matched_inline_option:
            index += 1
            continue

        if arg.startswith("--"):
            print(f"❌ Unknown option: {arg}")
            print(USAGE)
            sys.exit(1)

        name_parts.append(arg)
        index += 1

    new_name = " ".join(name_parts).strip()
    if not new_name:
        print(USAGE)
        sys.exit(1)

    return new_name, use_lando, use_blade, header_updates


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


def _find_main_plugin_file(plugin_directory, plugin_slug):
    expected_file = plugin_directory / f"{plugin_slug}.php"
    if expected_file.exists():
        return expected_file

    for php_file in plugin_directory.glob("*.php"):
        try:
            content = php_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        if "Plugin Name:" in content and "Text Domain:" in content:
            return php_file

    return None


def _apply_plugin_header_updates(plugin_file, header_updates):
    if not header_updates:
        return []

    content = plugin_file.read_text(encoding="utf-8")
    header_match = re.search(r"/\*[\s\S]*?Plugin Name:[\s\S]*?\*/", content)
    if not header_match:
        return [f"Skipped header updates: no plugin header found in `{plugin_file.name}`"]

    header_block = header_match.group(0)
    updated_header = header_block

    for field, value in header_updates.items():
        pattern = re.compile(rf"(^\s*\*?\s*{re.escape(field)}\s*:\s*).*$", re.MULTILINE)
        if pattern.search(updated_header):
            updated_header = pattern.sub(lambda match: f"{match.group(1)}{value}", updated_header, count=1)
            continue

        updated_header = updated_header.replace("*/", f" * {field}: {value}\n */", 1)

    updated_content = content[:header_match.start()] + updated_header + content[header_match.end():]
    plugin_file.write_text(updated_content, encoding="utf-8")
    return [f"Updated plugin headers in `{plugin_file.name}`"]


def create_plugin_command(args):
    new_name, use_lando, use_blade, header_updates = _parse_create_args(args)
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
        main_plugin_file = _find_main_plugin_file(plugin_directory, plugin_name)
        if main_plugin_file:
            header_messages = _apply_plugin_header_updates(main_plugin_file, header_updates)
        elif header_updates:
            header_messages = [f"Skipped header updates: main plugin file not found in `{plugin_directory}`"]
        else:
            header_messages = []
        post_create_messages = (
            _enable_blade_support(plugin_directory, use_lando)
            if use_blade
            else _disable_blade_support(plugin_directory, use_lando)
        )
        print(f"✅ Plugin created and renamed to: {plugin_name}")
        for header_message in header_messages:
            print(f"ℹ️ {header_message}")
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
