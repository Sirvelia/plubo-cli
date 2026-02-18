from pathlib import Path
import subprocess
import curses
import time
import os
import json
import re
from plubo.utils import project, interface, colors


DEPENDENCY_OPTIONS = {
    "ALPINE.JS": {
        "packages": [
            {"name": "alpinejs", "dev": False},
            {"name": "@types/alpinejs", "dev": True},
        ]
    },
    "TAILWIND CSS": {
        "packages": [
            {"name": "tailwindcss", "dev": True},
        ]
    },
    "DAISY UI": {
        "packages": [
            {"name": "daisyui@latest", "dev": True},
        ]
    },
    "HIKEFLOW": {
        "packages": [
            {"name": "hikeflow", "dev": False},
        ]
    },
    "RETURN": None  # Special case, no package to install
}

def _normalize_token(value):
    return re.sub(r"[^a-z0-9]+", "", value.lower())

def get_dependency_packages(dependency_option):
    """Return a normalized package list with explicit dev flags."""
    if not dependency_option:
        return []

    if isinstance(dependency_option, str):
        return [{"name": package_name, "dev": False} for package_name in dependency_option.split()]

    package_entries = dependency_option.get("packages", [])
    normalized_packages = []

    for entry in package_entries:
        if isinstance(entry, str):
            normalized_packages.append({"name": entry, "dev": bool(dependency_option.get("dev", False))})
            continue

        package_name = entry.get("name")
        if not package_name:
            continue

        normalized_packages.append(
            {"name": package_name, "dev": bool(entry.get("dev", dependency_option.get("dev", False)))}
        )

    return normalized_packages

def resolve_dependency(value):
    """Resolve a preset from user input; fallback to custom package tokens."""
    normalized_value = _normalize_token(value)

    for option_name, dependency_option in DEPENDENCY_OPTIONS.items():
        packages = get_dependency_packages(dependency_option)
        if not packages:
            continue

        candidate_tokens = {_normalize_token(option_name)}
        candidate_tokens.update(_normalize_token(package["name"]) for package in packages)

        if normalized_value in candidate_tokens:
            return dependency_option, True

    return {"packages": [{"name": package_name, "dev": False} for package_name in value.split()]}, False

def get_installed_dependencies():
    """Read package.json and return a dictionary of installed dependencies and versions."""
    package_json_path = "package.json"

    if not os.path.exists(package_json_path):
        return {}

    try:
        with open(package_json_path, "r", encoding="utf-8") as file:
            deps_data = json.load(file)
            
            # Merge dependencies and devDependencies
            dependencies = deps_data.get("dependencies", {})
            dev_dependencies = deps_data.get("devDependencies", {})

            return {**dependencies, **dev_dependencies}  # Merge both dictionaries
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def install_dependency(stdscr, dependency_option):
    """Install a specific Composer dependency, handling Lando projects."""
    packages = get_dependency_packages(dependency_option)
    if not packages:
        return  # Do nothing if the user selects "Back to Main Menu"

    package_names = [package["name"] for package in packages]
    stdscr.clear()
    interface.draw_background(stdscr, f"⏳ Installing {' '.join(package_names)}...")

    height, width = stdscr.getmaxyx()

    commands = []
    regular_packages = [package["name"] for package in packages if not package["dev"]]
    dev_packages = [package["name"] for package in packages if package["dev"]]

    if regular_packages:
        commands.append(["yarn", "add"] + regular_packages)
    if dev_packages:
        commands.append(["yarn", "add", "--dev"] + dev_packages)

    success = True
    for command in commands:
        success = project.run_command(command, Path(os.getcwd()), stdscr)
        if not success:
            break

    package_display = ", ".join(package_names)
    message = (
        f"✅ Successfully installed {package_display}"
        if success
        else f"❌ Installation failed for {package_display}"
    )

    stdscr.addstr(height - 3, 4, message, curses.color_pair(3))
    stdscr.refresh()

    # **Wait for user input before returning**
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
            packages = get_dependency_packages(dependency_option)

            all_packages_installed = bool(packages) and all(
                package["name"] in installed_dependencies for package in packages
            )
            if all_packages_installed:
                checkmark = "✅"

            installed_versions = [
                f'{package["name"]} {installed_dependencies[package["name"]]}'
                for package in packages
                if package["name"] in installed_dependencies
            ]
            if installed_versions:
                version_info = f" ({', '.join(installed_versions)})"

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
