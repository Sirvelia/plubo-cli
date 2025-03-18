import os
import curses
from pathlib import Path
from plubo.utils import project  # Import function to get the plugin name

# Define the absolute path to the templates directory (sibling folder)
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"  # Move up one level to reach sibling

def add_entity(stdscr):
    """Main function to handle entity creation within the curses menu."""
    curses.curs_set(1)  # Show cursor for input

    stdscr.nodelay(0)
    stdscr.clear()
    stdscr.addstr(2, 2, "🔄 Add Entity")
    stdscr.refresh()

    stdscr.addstr(6, 2, "Entity name (leave empty to cancel):")
    stdscr.refresh()

    # Ensure proper user input handling
    curses.echo()
    stdscr.move(8, 2)
    curses.flushinp()
    entity_name = stdscr.getstr(curses.color_pair(3)).decode("utf-8").strip()
    curses.noecho()

    # If the user presses enter without input, do nothing
    if not entity_name:
        stdscr.addstr(12, 2, "⚠️ Entity Creation cancelled. Press any key to return.")
        stdscr.refresh()
        stdscr.getch()
        return

    stdscr.clear()
    stdscr.addstr(2, 2, f"Creating entity {entity_name}... ⏳")
    stdscr.refresh()

    success, message = create_entity(entity_name)

    if success:
        stdscr.addstr(4, 2, f"✅ {message}")
    else:
        stdscr.addstr(4, 2, f"❌ {message}")

    stdscr.addstr(8, 2, "Press any key to return to the main menu.")
    stdscr.refresh()
    stdscr.getch()
    curses.curs_set(0)  # Hide cursor


def create_entity(entity_name):
    """Creates a new entity file in the Entities directory with the given name."""

    # Define plugin root and entities directory
    plugin_root = Path(os.getcwd())  # Plugin directory (assumed current working directory)
    entities_dir = plugin_root / "Entities"
    template_file = TEMPLATES_DIR / "Entity.php"  # Path to the template file

    # Convert entity name to PascalCase
    entity_class_name = ''.join(word.capitalize() for word in entity_name.split('-'))

    # Define file path
    entity_file = entities_dir / f"{entity_class_name}.php"

    # Ensure the Entities directory exists
    entities_dir.mkdir(parents=True, exist_ok=True)

    # Check if the entity file already exists
    if entity_file.exists():
        return False, f"Entity '{entity_class_name}' already exists at {entity_file}"

    # Ensure template file exists
    if not template_file.exists():
        return False, f"❌ Template file '{template_file}' not found."

    # Read the template
    with template_file.open("r", encoding="utf-8") as f:
        php_template = f.read()

    # Replace placeholders
    plugin_name = ''.join(word.capitalize() for word in project.detect_plugin_name().split('-'))  # Get actual plugin name
    php_code = php_template.replace("PluginPlaceholder", plugin_name).replace("EntityName", entity_class_name)

    # Write the entity file
    entity_file.write_text(php_code, encoding="utf-8")
    return True, f"Entity '{entity_class_name}' created successfully at {entity_file}"
