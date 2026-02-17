import sys
import subprocess
from pathlib import Path
from plubo.generators.plugin import rename_plugin
from plubo.utils import project

USAGE = "Usage: pb-cli create <plugin_name> [--lando]"


def _parse_create_args(args):
    use_lando = False
    name_parts = []

    for arg in args:
        if arg == "--lando":
            use_lando = True
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

    return new_name, use_lando


def _confirm_create_in_current_directory():
    print("⚠️ No WordPress installation detected.")
    print(f"The plugin will be created in the current directory: {Path.cwd()}")

    try:
        answer = input("Continue? [y/N]: ").strip().lower()
    except EOFError:
        return False

    return answer in {"y", "yes"}


def create_plugin_command(args):
    new_name, use_lando = _parse_create_args(args)
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
        print(f"✅ Plugin created and renamed to: {plugin_name}")
    except FileNotFoundError:
        print(f"❌ Command not found: {command[0]}")
        sys.exit(1)
    except subprocess.CalledProcessError as error:
        print(f"❌ Command failed with exit code {error.returncode}: {' '.join(command)}")
        sys.exit(error.returncode)
