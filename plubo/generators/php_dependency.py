import subprocess
import curses
import json
import os
from pathlib import Path
from plubo.utils import project, interface
from plubo.generators import functionality
from plubo.generators.dependency_utils import DependencyScaffoldUtils

DEPENDENCY_OPTIONS = {
    "ROUTES": {"package": "joanrodas/plubo-routes"},
    "ROLES": {"package": "joanrodas/plubo-roles"},
    "LOGS": {"package": "sirvelia-labs/plubo-logs"},
    "CHECKS": {"package": "sirvelia-labs/plubo-checks"},
    "JWT": {"package": "sirvelia/plubo-jwt"},
    "CARBON FIELDS": {
        "package": "htmlburger/carbon-fields",
        "post_install": [
            "scaffold_carbon_fields_functionality",
        ],
    },
    "ACTION SCHEDULER": {
        "package": "woocommerce/action-scheduler",
        "post_install": [
            "scaffold_crons_functionality",
        ],
    },
    "CUSTOM CODE FIELDS": {"package": "joanrodas/custom-code-fields"},
    "RETURN": None  # Special case, no package to install
}

def get_dependency_package(dependency_option):
    if not dependency_option:
        return None
    if isinstance(dependency_option, str):
        return dependency_option
    return dependency_option.get("package")

def get_post_install_actions(dependency_option):
    if not isinstance(dependency_option, dict):
        return []
    actions = dependency_option.get("post_install", [])
    return [action for action in actions if isinstance(action, str)]

def resolve_dependency(value):
    normalized_value = DependencyScaffoldUtils.normalize_token(value)

    for option_name, dependency_option in DEPENDENCY_OPTIONS.items():
        package_name = get_dependency_package(dependency_option)
        if not package_name:
            continue

        candidate_tokens = {
            DependencyScaffoldUtils.normalize_token(option_name),
            DependencyScaffoldUtils.normalize_token(package_name),
        }
        candidate_tokens.update(DependencyScaffoldUtils.normalize_token(token) for token in package_name.split("/"))

        if normalized_value in candidate_tokens:
            return dependency_option, True

    return {"package": value}, False

def _scaffold_carbon_fields_functionality(cwd):
    created, message = functionality.create_functionality("Custom Fields", "CustomFields.php")
    return [message if created else message]

def _scaffold_crons_functionality(cwd):
    created, message = functionality.create_functionality("Crons", "Crons.php")
    return [message if created else message]

def apply_post_install_actions(dependency_option, cwd=None):
    cwd = Path(cwd) if cwd else Path(os.getcwd())
    messages = []
    action_handlers = {
        "scaffold_carbon_fields_functionality": _scaffold_carbon_fields_functionality,
        "scaffold_crons_functionality": _scaffold_crons_functionality,
    }

    for action in get_post_install_actions(dependency_option):
        handler = action_handlers.get(action)
        if not handler:
            messages.append(f"Skipped unknown post-install action `{action}`")
            continue

        try:
            messages.extend(handler(cwd))
        except Exception as error:
            messages.append(f"Failed post-install action `{action}`: {error}")

    return messages

def get_installed_dependencies():
    """Read composer.json and return a dictionary of installed dependencies and versions."""
    composer_json_path = "composer.json"

    if not os.path.exists(composer_json_path):
        return {}

    try:
        with open(composer_json_path, "r", encoding="utf-8") as file:
            composer_data = json.load(file)
            return composer_data.get("require", {})  # Get dependencies from require section
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def get_latest_version(package_name):
    """Retrieve the latest available version of a Composer package."""
    try:
        command = ["lando", "composer", "show", "--all", package_name] if project.is_lando_project() else ["composer", "show", "--all", package_name]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        
        for line in result.stdout.split("\n"):
            if line.startswith("versions :"):
                versions = line.split(":")[1].strip().split(", ")
                return versions[-1]  # Latest version is usually the last in the list
    except subprocess.CalledProcessError:
        return None  # Error occurred

def install_dependency(stdscr, dependency_option):
    """Install a specific Composer dependency, handling Lando projects."""
    package_name = get_dependency_package(dependency_option)
    if not package_name:
        return  # Do nothing if the user selects "Back to Main Menu"

    stdscr.clear()
    interface.draw_background(stdscr, f"⏳ Installing {package_name}...")
    height, width = stdscr.getmaxyx()

    command = ["lando", "composer", "require", package_name] if project.is_lando_project() else ["composer", "require", package_name]
    success = project.run_command(command, Path(os.getcwd()), stdscr)
    message = f"✅ Successfully installed {package_name}" if success else f"❌ Installation failed for {package_name}"
    post_install_messages = []
    if success:
        post_install_messages = apply_post_install_actions(dependency_option, cwd=Path(os.getcwd()))
    
    stdscr.addstr(height - 3, 4, message, curses.color_pair(3))
    if post_install_messages:
        stdscr.addstr(height - 2, 4, f"ℹ️ {post_install_messages[-1][: max(0, width - 8)]}", curses.color_pair(3))
    stdscr.refresh()

    stdscr.getch()  # Wait user input

def dependency_menu(stdscr):
    """Display the dependency installation submenu with a background title."""
    curses.curs_set(0)  # Hide cursor   
    stdscr.keypad(True)
        
    current_row = 0
    height, width = stdscr.getmaxyx()

    while True:
        installed_dependencies = get_installed_dependencies()
        menu_options = []
        original_names = []  # To map displayed names back to actual options

        for option, dependency_option in DEPENDENCY_OPTIONS.items():
            checkmark = ""
            version_info = ""
            package_name = get_dependency_package(dependency_option)

            if package_name and package_name in installed_dependencies:
                checkmark = "✅"
                version_info = f" {installed_dependencies[package_name]}"
            
            display_text = f"{checkmark} {option} {version_info}".strip()
            menu_options.append(display_text)
            original_names.append(option)  # Keep track of original option names
            
        selected_row, current_row = interface.render_menu(stdscr, menu_options, current_row, height, width)
        
        if selected_row is not None:
            selected_option = original_names[selected_row]
            dependency_option = DEPENDENCY_OPTIONS[selected_option]
            if dependency_option is not None:
                install_dependency(stdscr, dependency_option)
            return
