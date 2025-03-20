import os
from pathlib import Path
from plubo.utils import project, interface  # Import function to get the plugin name

# Define the absolute path to the templates directory (sibling folder)
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"  # Move up one level to reach sibling

def add_entity(stdscr):
    """Main function to handle entity creation within the curses menu."""
    stdscr.erase()
    interface.draw_background(stdscr, "🔄 Add Entity")
    
    box_x = (stdscr.getmaxyx()[1] - 50) // 2  # Center box horizontally
    y_start = 8  # Position inputs inside the box
    
    entity_name = interface.get_user_input(stdscr, y_start, box_x, "Entity name (empty to cancel):", 40)
    
    if not entity_name:
        interface.display_message(stdscr, "⚠️ Creation cancelled.", "error", 15)
    else:
        interface.display_message(stdscr, f"Creating entity {entity_name}... ⏳", "info", 15)
        creation, message = create_entity(entity_name)
        if creation:
            interface.display_message(stdscr, message, "success", 16)
        else:
            interface.display_message(stdscr, message, "error", 16)
    stdscr.getch()  # Waits for a key press before returning


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
