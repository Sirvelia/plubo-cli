import sys
import subprocess
import json
from pathlib import Path
from plubo.cli.commands.plugin_headers import HEADER_OPTION_TO_LABEL, apply_plugin_header_updates, find_main_plugin_file
from plubo.generators.plugin import rename_plugin
from plubo.generators.php_dependency import (
    apply_post_install_actions as apply_php_post_install_actions,
    get_dependency_package,
    resolve_dependency as resolve_php_dependency,
)
from plubo.generators.node_dependency import (
    apply_post_install_actions as apply_node_post_install_actions,
    get_dependency_packages,
    resolve_dependency as resolve_node_dependency,
)
from plubo.utils import project

USAGE = (
    "Usage: pb-cli create <plugin_name> [--lando] [--blade] "
    "[--php-dep <package|preset>] [--composer-dep <package|preset>] "
    "[--node-dep <package|preset>] "
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
def _parse_create_args(args):
    use_lando = False
    use_blade = False
    php_dependencies = []
    node_dependencies = []
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

        if arg in {"--php-dep", "--composer-dep", "--node-dep"}:
            if index + 1 >= len(args):
                print(f"❌ Missing value for option: {arg}")
                print(USAGE)
                sys.exit(1)

            value = args[index + 1].strip()
            if not value:
                print(f"❌ Empty value is not allowed for option: {arg}")
                print(USAGE)
                sys.exit(1)

            if arg in {"--php-dep", "--composer-dep"}:
                php_dependencies.append(value)
            else:
                node_dependencies.append(value)

            index += 2
            continue

        if arg.startswith("--php-dep=") or arg.startswith("--composer-dep=") or arg.startswith("--node-dep="):
            option, value = arg.split("=", 1)
            value = value.strip()
            if not value:
                print(f"❌ Empty value is not allowed for option: {option}")
                print(USAGE)
                sys.exit(1)

            if option in {"--php-dep", "--composer-dep"}:
                php_dependencies.append(value)
            else:
                node_dependencies.append(value)

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

    return new_name, use_lando, use_blade, header_updates, php_dependencies, node_dependencies


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

def _composer_package_key(package_spec):
    package_spec = (package_spec or "").strip()
    if not package_spec:
        return package_spec

    first_token = package_spec.split()[0]
    if ":" in first_token and "/" in first_token:
        return first_token.split(":", 1)[0]
    return first_token

def _composer_require_command(use_lando, package_spec):
    package_tokens = package_spec.split()
    if use_lando:
        return ["lando", "composer", "require"] + package_tokens
    return ["composer", "require"] + package_tokens

def _build_node_install_commands(packages):
    regular_packages = [package["name"] for package in packages if not package["dev"]]
    dev_packages = [package["name"] for package in packages if package["dev"]]
    commands = []

    if regular_packages:
        commands.append(["yarn", "add"] + regular_packages)
    if dev_packages:
        commands.append(["yarn", "add", "--dev"] + dev_packages)

    return commands

def _merge_node_packages(packages):
    ordered_names = []
    package_dev_flags = {}

    for package in packages:
        package_name = package.get("name")
        if not package_name:
            continue

        package_is_dev = bool(package.get("dev", False))
        if package_name not in package_dev_flags:
            ordered_names.append(package_name)
            package_dev_flags[package_name] = package_is_dev
        else:
            package_dev_flags[package_name] = package_dev_flags[package_name] and package_is_dev

    return [{"name": package_name, "dev": package_dev_flags[package_name]} for package_name in ordered_names]

def _is_blade_requested(php_dependency_inputs):
    for dependency_input in php_dependency_inputs:
        dependency_option, _ = resolve_php_dependency(dependency_input)
        package_name = get_dependency_package(dependency_option)
        if _composer_package_key(package_name) == BLADE_PACKAGE:
            return True
    return False

def _install_php_dependencies(plugin_directory, use_lando, php_dependency_inputs):
    messages = []
    seen_package_keys = set()

    for dependency_input in php_dependency_inputs:
        dependency_option, _ = resolve_php_dependency(dependency_input)
        package_name = get_dependency_package(dependency_option)
        if not package_name:
            continue

        package_key = _composer_package_key(package_name)
        if package_key in seen_package_keys:
            continue
        seen_package_keys.add(package_key)

        required_packages = _load_composer_require(plugin_directory)
        if package_key not in required_packages:
            command = _composer_require_command(use_lando, package_name)
            subprocess.run(command, cwd=str(plugin_directory), check=True)
            messages.append(f"Installed `{package_name}`")
        else:
            messages.append(f"Kept existing `{package_key}` dependency")

        messages.extend(apply_php_post_install_actions(dependency_option, cwd=plugin_directory))

    return messages

def _install_node_dependencies(plugin_directory, node_dependency_inputs):
    messages = []
    dependency_options = []
    packages_to_install = []

    for dependency_input in node_dependency_inputs:
        dependency_option, _ = resolve_node_dependency(dependency_input)
        dependency_options.append(dependency_option)
        packages_to_install.extend(get_dependency_packages(dependency_option))

    merged_packages = _merge_node_packages(packages_to_install)
    commands = _build_node_install_commands(merged_packages)

    for command in commands:
        subprocess.run(command, cwd=str(plugin_directory), check=True)

    if merged_packages:
        package_display = ", ".join(package["name"] for package in merged_packages)
        messages.append(f"Installed `{package_display}`")

    for dependency_option in dependency_options:
        messages.extend(apply_node_post_install_actions(dependency_option, cwd=plugin_directory))

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
    (
        new_name,
        use_lando,
        use_blade,
        header_updates,
        php_dependency_inputs,
        node_dependency_inputs,
    ) = _parse_create_args(args)
    wp_root = project.detect_wp_root()

    if wp_root:
        target_directory = wp_root / "wp-content/plugins"
    else:
        if not _confirm_create_in_current_directory():
            print("❌ Aborted.")
            sys.exit(1)
        target_directory = Path.cwd()

    try:
        target_directory.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        print(f"❌ Failed to prepare target directory `{target_directory}`: {error}")
        sys.exit(1)

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
        main_plugin_file = find_main_plugin_file(plugin_directory, plugin_name)
        if main_plugin_file:
            headers_updated, header_messages = apply_plugin_header_updates(main_plugin_file, header_updates)
            if not headers_updated and header_updates:
                header_messages = [f"Skipped header updates: {header_messages[0]}"]
        elif header_updates:
            header_messages = [f"Skipped header updates: main plugin file not found in `{plugin_directory}`"]
        else:
            header_messages = []

        blade_requested = _is_blade_requested(php_dependency_inputs)
        php_dependencies = list(php_dependency_inputs)
        if use_blade and not blade_requested:
            php_dependencies.append("bladeone")

        post_create_messages = []
        post_create_messages.extend(_install_php_dependencies(plugin_directory, use_lando, php_dependencies))
        post_create_messages.extend(_install_node_dependencies(plugin_directory, node_dependency_inputs))

        if not use_blade and not blade_requested:
            post_create_messages.extend(_disable_blade_support(plugin_directory, use_lando))

        print(f"✅ Plugin created and renamed to: {plugin_name}")
        for header_message in header_messages:
            print(f"ℹ️ {header_message}")
        for post_create_message in post_create_messages:
            print(f"ℹ️ {post_create_message}")
    except FileNotFoundError as error:
        missing_resource = str(error.filename) if error.filename else ""
        if missing_resource in {str(target_directory), str(plugin_directory)}:
            print(f"❌ Directory not found: {missing_resource}")
        else:
            missing_command = missing_resource or command[0]
            print(f"❌ Command not found: {missing_command}")
        sys.exit(1)
    except subprocess.CalledProcessError as error:
        failed_command = error.cmd if isinstance(error.cmd, list) else [str(error.cmd)]
        print(f"❌ Command failed with exit code {error.returncode}: {' '.join(failed_command)}")
        sys.exit(error.returncode)
