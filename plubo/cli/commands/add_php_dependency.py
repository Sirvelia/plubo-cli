import sys
import subprocess
from plubo.generators.php_dependency import (
    apply_post_install_actions,
    get_dependency_package,
    resolve_dependency,
)
from plubo.utils import project

def add_php_dependency_command(args):
    if not args:
        print("Usage: plubo php-dep <package|preset>")
        print("Example presets: routes, roles, logs, checks, jwt")
        sys.exit(1)

    package_input = " ".join(args).strip()
    dependency_option, _ = resolve_dependency(package_input)
    package_name = get_dependency_package(dependency_option)
    command = (
        ["lando", "composer", "require"] + package_name.split()
        if project.is_lando_project()
        else ["composer", "require"] + package_name.split()
    )

    try:
        subprocess.run(command, check=True)
        post_install_messages = apply_post_install_actions(dependency_option)
        print(f"✅ Successfully installed: {package_name}")
        for post_install_message in post_install_messages:
            print(f"ℹ️ {post_install_message}")
    except FileNotFoundError:
        print(f"❌ Command not found: {command[0]}")
        sys.exit(1)
    except subprocess.CalledProcessError as error:
        print(f"❌ Installation failed (exit code {error.returncode}): {' '.join(command)}")
        sys.exit(error.returncode)
