import sys
import subprocess
from plubo.generators.plugin import rename_plugin
from plubo.utils import project

def create_plugin_command(args):
    if not args:
        print("Usage: plubo create <plugin_name>")
        sys.exit(1)

    new_name = " ".join(args).strip()
    wp_root = project.detect_wp_root()

    if not wp_root:
        print("❌ No WordPress installation detected. Aborting.")
        sys.exit(1)

    plugin_name = new_name.lower().replace(" ", "-")
    plugins_directory = wp_root / "wp-content/plugins"
    plugin_directory = plugins_directory / plugin_name

    command = (
        ["lando", "composer", "create-project", "joanrodas/plubo", plugin_name]
        if project.is_lando_project()
        else ["composer", "create-project", "joanrodas/plubo", plugin_name]
    )

    try:
        subprocess.run(command, cwd=str(plugins_directory), check=True)
        rename_plugin("plugin-placeholder", new_name, plugin_directory)
        print(f"✅ Plugin created and renamed to: {plugin_name}")
    except FileNotFoundError:
        print(f"❌ Command not found: {command[0]}")
        sys.exit(1)
    except subprocess.CalledProcessError as error:
        print(f"❌ Command failed with exit code {error.returncode}: {' '.join(command)}")
        sys.exit(error.returncode)
