import json
import os
import subprocess
import curses
from plubo.utils import interface
from packaging import version as packaging_version

def get_composer_dependencies(composer_file="composer.json"):
    """
    Reads composer.json and returns a dictionary of dependencies with their current versions.
    """
    if not os.path.exists(composer_file):
        return {}
    
    try:
        with open(composer_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("require", {})
    except json.JSONDecodeError:
        return {}


def get_latest_composer_version(package_name):
    """
    Uses 'composer show --all' to get the list of available versions for a package.
    Filters out non-stable versions (like dev-main) and returns the highest stable version.
    """
    try:
        result = subprocess.run(
            ["composer", "show", "--all", package_name],
            capture_output=True, text=True, check=True
        )
        versions = []
        for line in result.stdout.splitlines():
            if line.startswith("versions :"):
                versions_line = line.split(":", 1)[1].strip()
                # Remove asterisks and split by comma
                raw_versions = [v.strip(" *") for v in versions_line.split(",")]
                # Filter versions that appear to be stable (start with a digit)
                versions = [v for v in raw_versions if v and v[0].isdigit()]
                break

        if versions:
            # Sort versions using packaging.version for proper semantic versioning comparison
            sorted_versions = sorted(versions, key=lambda v: packaging_version.parse(v))
            return sorted_versions[-1]
        return None
    except subprocess.CalledProcessError:
        return None

def check_composer_dependencies():
    """
    Checks all dependencies in composer.json for outdated versions.
    Returns a dict where keys are package names and values are a dict with
    'current' and 'latest' version information.
    """
    deps = get_composer_dependencies()
    outdated = {}
    
    for package, current_version in deps.items():
        latest_version = get_latest_composer_version(package)
        if latest_version and latest_version != current_version:
            outdated[package] = {"current": current_version, "latest": latest_version}
    
    return outdated

def get_yarn_outdated():
    """
    Uses 'yarn outdated --json' to get outdated packages from package.json.
    Returns a dictionary mapping package names to a dict with 'current' and 'latest' versions.
    This version uses check=False so that non-zero exit codes (which indicate outdated packages)
    do not cause an exception.
    """
    try:
        result = subprocess.run(
            ["yarn", "outdated", "--json"],
            capture_output=True, text=True, check=False
        )
    except Exception as e:
        return {}

    outdated = {}
    # Yarn outputs multiple JSON objects (one per line)
    for line in result.stdout.splitlines():
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue

        if data.get("type") == "table":
            table = data.get("data", {})
            head = table.get("head", [])
            body = table.get("body", [])
            try:
                pkg_idx = head.index("Package")
                current_idx = head.index("Current")
                latest_idx = head.index("Latest")
            except ValueError:
                continue

            for row in body:
                package = row[pkg_idx]
                current = row[current_idx]
                latest = row[latest_idx]
                if current != latest:
                    outdated[package] = {"current": current, "latest": latest}
    return outdated

def dependency_checker(stdscr):
    """
    Integrates the dependency checker with the current curses interface.
    Displays outdated Composer dependencies (if any) or a success message.
    """
    stdscr.clear()
    interface.draw_background(stdscr, "🔍 Dependency Checker")
    height, width = stdscr.getmaxyx()
    
    # Display initial message
    # interface.display_message(stdscr, "Checking Composer dependencies...", "info", 2)
    # stdscr.refresh()
    
    # Check dependencies
    outdated = check_composer_dependencies()
    
    # Prepare display lines
    display_lines = []
    if not outdated:
        display_lines.append("All Composer dependencies are up to date.")
    else:
        display_lines.append("Outdated Composer dependencies detected:")
        for package, versions in outdated.items():
            display_lines.append(f" - {package}: {versions['current']} → {versions['latest']}")
    
    outdated = get_yarn_outdated()
    display_lines.append("")
    if not outdated:
        display_lines.append("All Yarn dependencies are up to date.")
    else:
        display_lines.append("Outdated Yarn dependencies detected:")
        for package, versions in outdated.items():
            display_lines.append(f" - {package}: {versions['current']} → {versions['latest']}")
    
    
    # Display results starting a few lines down
    y_start = 6
    for i, line in enumerate(display_lines):
        if y_start + i < height - 2:
            stdscr.addstr(y_start + i, 4, line, curses.color_pair(1))
    stdscr.refresh()
    
    # Wait for user input before returning to the main menu
    stdscr.getch()

# Example integration into the CLI main loop:
# You could add an option in your main menu that calls dependency_checker via curses.wrapper(dependency_checker)
