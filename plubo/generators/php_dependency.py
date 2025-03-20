import subprocess
import curses
import json
import os
from pathlib import Path
from plubo.utils import project, interface, colors

DEPENDENCY_OPTIONS = {
    "ROUTES": "joanrodas/plubo-routes",
    "ROLES": "joanrodas/plubo-roles",
    "LOGS": "sirvelia-labs/plubo-logs",
    "CHECKS": "sirvelia-labs/plubo-checks",
    "JWT": "sirvelia/plubo-jwt",
    "CARBON FIELDS": "htmlburger/carbon-fields",
    "ACTION SCHEDULER": "woocommerce/action-scheduler",
    "CUSTOM CODE FIELDS": "joanrodas/custom-code-fields",
    "RETURN": None  # Special case, no package to install
}

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

def install_dependency(stdscr, package_name):
    """Install a specific Composer dependency, handling Lando projects."""
    if not package_name:
        return  # Do nothing if the user selects "Back to Main Menu"

    stdscr.clear()
    interface.draw_background(stdscr, f"⏳ Installing {package_name}...")
    height, width = stdscr.getmaxyx()

    command = ["lando", "composer", "require", package_name] if project.is_lando_project() else ["composer", "require", package_name]
    success = project.run_command(command, Path(os.getcwd()), stdscr)
    message = f"✅ Successfully installed {package_name}" if success else f"❌ Installation failed for {package_name}"
    
    stdscr.addstr(height - 3, 4, message, curses.color_pair(3))
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

        for option, package_name in DEPENDENCY_OPTIONS.items():
            checkmark = ""
            version_info = ""

            if package_name and package_name in installed_dependencies:
                checkmark = "✅"
                version_info = f" {installed_dependencies[package_name]}"
            
            display_text = f"{checkmark} {option} {version_info}".strip()
            menu_options.append(display_text)
            original_names.append(option)  # Keep track of original option names
            
        selected_row, current_row = interface.render_menu(stdscr, menu_options, current_row, height, width)
        
        if selected_row is not None:
            selected_option = original_names[selected_row]
            package_name = DEPENDENCY_OPTIONS[selected_option]
            if package_name is not None:
                install_dependency(stdscr, package_name)
            return