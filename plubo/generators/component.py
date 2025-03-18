import os
import curses
from pathlib import Path
from plubo.utils import project

# Define the absolute path to the templates directory (sibling folder)
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"  # Move up one level to reach sibling

def add_component(stdscr):
    """Main function to handle component creation within the curses menu."""
    curses.curs_set(1)  # Show cursor for input

    stdscr.nodelay(0)
    stdscr.clear()
    stdscr.addstr(2, 2, "🔄 Add Component")
    stdscr.refresh()

    stdscr.addstr(6, 2, "Component name (leave empty to cancel):")
    stdscr.refresh()

    # Ensure proper user input handling
    curses.echo()
    stdscr.move(8, 2)
    curses.flushinp()
    component_name = stdscr.getstr(curses.color_pair(3)).decode("utf-8").strip()
    curses.noecho()

    # If the user presses enter without input, do nothing
    if not component_name:
        stdscr.addstr(12, 2, "⚠️ Component Creation cancelled. Press any key to return.")
        stdscr.refresh()
        stdscr.getch()
        return

    stdscr.clear()
    stdscr.addstr(2, 2, f"Creating component {component_name}... ⏳")
    stdscr.refresh()

    success, message = create_component(component_name)

    if success:
        stdscr.addstr(4, 2, f"✅ {message}")
    else:
        stdscr.addstr(4, 2, f"❌ {message}")

    stdscr.addstr(8, 2, "Press any key to return to the main menu.")
    stdscr.refresh()
    stdscr.getch()
    curses.curs_set(0)  # Hide cursor


def create_component(component_name):
    """Creates a new component file in the Components directory with the given name."""

    # Define plugin root and components directory
    plugin_root = Path(os.getcwd())  # Plugin directory (assumed current working directory)
    components_dir = plugin_root / "Components"
    template_file = TEMPLATES_DIR / "Component.php"  # Path to the template file

    # Convert component name to PascalCase
    component_class_name = ''.join(word.capitalize() for word in component_name.split('-'))

    # Define file path
    component_file = components_dir / f"{component_class_name}.php"

    # Ensure the Components directory exists
    components_dir.mkdir(parents=True, exist_ok=True)

    # Check if the component file already exists
    if component_file.exists():
        return False, f"Component '{component_class_name}' already exists at {component_file}"

    # Ensure template file exists
    if not template_file.exists():
        return False, f"❌ Template file '{template_file}' not found."

    # Read the template
    with template_file.open("r", encoding="utf-8") as f:
        php_template = f.read()

    # Replace placeholders
    plugin_name = ''.join(word.capitalize() for word in project.detect_plugin_name().split('-'))  # Get actual plugin name
    php_code = php_template.replace("PluginPlaceholder", plugin_name).replace("ComponentName", component_class_name)

    # Write the component file
    component_file.write_text(php_code, encoding="utf-8")
    return True, f"Component '{component_class_name}' created successfully at {component_file}"
