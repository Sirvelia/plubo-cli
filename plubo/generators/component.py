import os
import curses
from pathlib import Path
from plubo.utils import project, interface

# Define the absolute path to the templates directory (sibling folder)
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"  # Move up one level to reach sibling

def add_component(stdscr):
    """Main function to handle component creation within the curses menu."""
    stdscr.erase()
    interface.draw_background(stdscr, "🔄 Add Component")
    
    box_x = (stdscr.getmaxyx()[1] - 50) // 2  # Center box horizontally
    y_start = 8  # Position inputs inside the box
    
    component_name = interface.get_user_input(stdscr, y_start, box_x, "Plugin name (empty to cancel):", 40)
    
    if not component_name:
        interface.display_message(stdscr, "⚠️ Creation cancelled.", "error", 15)
    else:
        interface.display_message(stdscr, f"Creating component {component_name}... ⏳", "info", 15)
        creation, message = create_component(component_name)
        if creation:
            interface.display_message(stdscr, message, "success", 16)
        else:
            interface.display_message(stdscr, message, "error", 16)
            
    stdscr.getch()  # Waits for a key press before returning

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
