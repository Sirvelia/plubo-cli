import os
from pathlib import Path
import curses
from plubo.utils import project, interface  # Import function to get the plugin name

# Define the absolute path to the templates directory (sibling folder)
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

# Functionality options and their respective PHP templates
FUNCTIONALITY_OPTIONS = {
    "ADMIN MENUS": "Admin/AdminMenus.php",
    "AJAX ACTIONS": "AjaxActions.php",
    "API ENDPOINTS": "ApiEndpoints.php",
    "CART": "Cart.php",
    "CRONS": "Crons.php",
    "CUSTOM FIELDS": "CustomFields.php",
    "ORDERS": "Orders.php",
    "POST ACTIONS": "PostActions.php",
    "PRODUCTS": "Products.php",
    "ROLES": "Roles.php",
    "ROUTES": "Routes.php",
    "SHORTCODES": "Shortcodes.php",
    "TAXONOMIES": "Taxonomies.php",
    "USERS": "Users.php",
    "CUSTOM": "Functionality.php",  # Base template for user-defined classes
    "BACK": None
}

def handle_selection(stdscr, current_row, menu_options, height, width):
    """Handle the selection of a menu option"""
    if current_row < 0 or current_row >= len(menu_options):
        return False  # Invalid selection
    
    selection = menu_options[current_row]
    
    if selection == "BACK":
        return True # Exit the CLI
    
    stdscr.erase()
    interface.draw_background(stdscr, "🔧 Add Functionality")
    
    box_x = (stdscr.getmaxyx()[1] - 50) // 2  # Center box horizontally
    y_start = 8  # Position inputs inside the box
    
    if selection == "CUSTOM":
        custom_name = interface.get_user_input(stdscr, y_start, box_x, "Functionality name (empty to cancel):", 40)
    
        if not custom_name:
            interface.display_message(stdscr, "⚠️ Creation cancelled.", "error", 15)
        else:
            interface.display_message(stdscr, f"Creating functionality {custom_name}... ⏳", "info", 15)
            creation, message = create_functionality(custom_name, "Functionality.php")
            if creation:
                interface.display_message(stdscr, message, "success", 16)
            else:
                interface.display_message(stdscr, message, "error", 16)
    else:
        interface.display_message(stdscr, f"Creating functionality {selection}... ⏳", "info", 15)
        creation, message = create_functionality(selection, FUNCTIONALITY_OPTIONS[selection])
        if creation:
            interface.display_message(stdscr, message, "success", 16)
        else:
            interface.display_message(stdscr, message, "error", 16)
    
    stdscr.getch()

def add_functionality(stdscr):
    """Displays a menu to select a functionality type and creates the corresponding PHP file."""
    curses.curs_set(0)  # Hide cursor   
    stdscr.keypad(True)
    
    menu_options = list(FUNCTIONALITY_OPTIONS.keys())
    current_row = 0
    
    height, width = stdscr.getmaxyx()

    while True:
        selected_row, current_row = interface.render_menu(stdscr, menu_options, current_row, height, width)
        if selected_row is not None:
            if handle_selection(stdscr, selected_row, menu_options, height, width):
                return # Exit the CLI if handle_selection returns True
            


def create_functionality(name, template_filename):
    """Creates a new functionality file based on the given template."""
    plugin_root = Path(os.getcwd())  # Plugin directory (assumed current working directory)
    functionality_dir = plugin_root / "Functionality"
    template_file = TEMPLATES_DIR / template_filename  # Get the template file path

    # Convert name to PascalCase
    class_name = ''.join(word.capitalize() for word in name.split())

    # Handle subfolders like "Admin/AdminMenus.php"
    subfolder, file_name = os.path.split(template_filename)
    file_path = functionality_dir / subfolder / f"{class_name}.php"

    # Ensure the directory structure exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if the file already exists
    if file_path.exists():
        return False, f"Functionality '{class_name}' already exists at {file_path}"

    # Ensure the template exists
    if not template_file.exists():
        return False, f"❌ Template file '{template_file}' not found."

    # Read the template file
    with template_file.open("r", encoding="utf-8") as f:
        php_template = f.read()

    # Replace placeholders
    plugin_name = ''.join(word.capitalize() for word in project.detect_plugin_name().split('-'))  # Get plugin name
    php_code = php_template.replace("PluginPlaceholder", plugin_name).replace("FunctionalityName", class_name)

    # Write the new functionality file
    file_path.write_text(php_code, encoding="utf-8")
    return True, f"Functionality '{class_name}' created successfully at {file_path}"

