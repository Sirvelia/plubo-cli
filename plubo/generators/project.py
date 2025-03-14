import os
import re
import json
import subprocess
import curses
from pathlib import Path

def detect_plugin_name():
    """Finds the main plugin file and extracts the plugin name from 'Text Domain'."""
    plugin_root = Path(os.getcwd())
    
    for file in plugin_root.glob("*.php"):
        with file.open("r", encoding="utf-8") as f:
            content = f.read()
            match = re.search(r"Text Domain:\s*(.+)", content)
            if match:
                return match.group(1).strip()
    
    return "plugin-placeholder"

def rename_project(stdscr):
    """Main function to handle renaming within the curses menu."""
    curses.curs_set(1)  # Show cursor for input
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Message color
    
    stdscr.nodelay(0)
    stdscr.clear()
    stdscr.addstr(2, 2, "🔄 Rename Plugin")
    stdscr.refresh()
    
    old_name = detect_plugin_name()
    stdscr.addstr(6, 2, f"Current plugin name detected: ")
    stdscr.addstr(old_name, curses.color_pair(3))
    stdscr.addstr(8, 2, "Enter a new plugin name (leave empty to cancel):")
    stdscr.refresh()
    
    # Ensure proper user input handling
    curses.echo()
    stdscr.move(10, 2)
    curses.flushinp()
    new_name = stdscr.getstr().decode("utf-8").strip()
    curses.noecho()
    
    # If the user presses enter without input, do nothing
    if not new_name:
        stdscr.addstr(12, 2, "⚠️ Rename cancelled. Press any key to return.")
        stdscr.refresh()
        stdscr.getch()
        return
    
    stdscr.clear()
    stdscr.addstr(2, 2, f"Renaming {old_name} to {new_name}... ⏳")
    stdscr.refresh()
    rename_plugin(old_name, new_name)
    
    stdscr.addstr(4, 2, "✅ Plugin renamed successfully!")
    stdscr.addstr(6, 2, "Press any key to return to the main menu.")
    stdscr.refresh()
    stdscr.getch()
    curses.curs_set(0)  # Hide cursor

def rename_plugin(old_name, new_name):
    """Replaces the plugin name in all relevant files with correct casing."""
    plugin_root = Path(os.getcwd())  # Get current plugin directory
    parent_directory = plugin_root.parent  # The directory containing the plugin folder
    
    casing_variants = {
        old_name.lower().replace("_", "-"): new_name.lower().replace("_", "-"),
        old_name.upper().replace("-", "_"): new_name.upper().replace("-", "_"),
        old_name.title().replace("-", ""): new_name.title().replace("-", ""),
        old_name.upper().replace("-", "").replace("_", ""): new_name.upper().replace("-", "").replace("_", "-")
    }
    
    # Update PHP files
    for file in plugin_root.rglob("*.php"):
        replace_in_file(file, casing_variants)
    
    # Update JSON files (composer.json, package.json)
    for json_file in ["composer.json", "package.json"]:
        json_path = plugin_root / json_file
        if json_path.exists():
            replace_in_json(json_path, casing_variants)
    
    # Update .pot file
    pot_file = plugin_root / "languages" / f"{old_name.lower()}.pot"
    if pot_file.exists():
        new_pot_file = plugin_root / "languages" / f"{new_name.lower()}.pot"
        replace_in_file(pot_file, casing_variants)
        pot_file.rename(new_pot_file)
    
    # Rename main plugin file
    old_plugin_file = plugin_root / f"{old_name.lower()}.php"
    new_plugin_file = plugin_root / f"{new_name.lower()}.php"
    if old_plugin_file.exists():
        old_plugin_file.rename(new_plugin_file)
    
    # Rename plugin folder
    new_plugin_folder = parent_directory / new_name.lower().replace(" ", "-")  # Normalize new folder name
    if plugin_root.exists():
        plugin_root.rename(new_plugin_folder)
    
    # if is_lando_project():
    #     subprocess.run(["lando", "composer", "update"], check=True)
    
    return new_plugin_folder

def replace_in_file(file_path, replacements):
    """Replaces occurrences of old names with new ones in a file."""
    with file_path.open("r", encoding="utf-8") as f:
        content = f.read()
    
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    with file_path.open("w", encoding="utf-8") as f:
        f.write(content)

def replace_in_json(file_path, replacements):
    """Updates JSON values containing the old name."""
    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    
    def recursive_replace(obj):
        if isinstance(obj, str):
            for old, new in replacements.items():
                obj = obj.replace(old, new)
            return obj
        elif isinstance(obj, dict):
            return {key: recursive_replace(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [recursive_replace(item) for item in obj]
        return obj
    
    updated_data = recursive_replace(data)
    
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(updated_data, f, indent=4)

def is_lando_project():
    """Check if the project is running inside a Lando environment by searching for .lando.yml in parent directories."""
    current_dir = os.getcwd()  # Get the current working directory
    while True:
        lando_file = os.path.join(current_dir, ".lando.yml")
        if os.path.exists(lando_file):
            return True  # Found .lando.yml
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            break  # Reached the root directory
        current_dir = parent_dir
    return False  # .lando.yml not found
