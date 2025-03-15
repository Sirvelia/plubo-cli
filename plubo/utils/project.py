import os
import re
from pathlib import Path

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

def detect_wp_root():
    """Find the WordPress root directory by checking for wp-config.php."""
    current_path = Path(os.getcwd())
    while current_path != current_path.parent:
        if (current_path / "wp-config.php").exists():
            return current_path
        current_path = current_path.parent
    return None

def detect_plugin_name():
    """Finds the main plugin file and extracts the plugin name from 'Text Domain'."""
    plugin_root = Path(os.getcwd())
    
    for file in plugin_root.glob("*.php"):
        with file.open("r", encoding="utf-8") as f:
            content = f.read()
            match = re.search(r"Text Domain:\s*(.+)", content)
            if match:
                return match.group(1).strip()
    
    return None