import os
import curses
from pathlib import Path
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
    "RETURN TO MAIN MENU": "None"
}

def handle_selection(stdscr, current_row, menu_options, height, width):
    """Handle the selection of a menu option"""
    if current_row < 0 or current_row >= len(menu_options):
        return False  # Invalid selection
    
    selection = menu_options[current_row]
    
    if selection == "RETURN TO MAIN MENU":
        return True # Exit the CLI
    
    if selection == "Custom":
        curses.curs_set(1)  # Show cursor for input
        stdscr.clear()
        stdscr.addstr(2, 2, "Custom Functionality Name:")
        stdscr.refresh()

        curses.echo()
        stdscr.move(4, 2)
        curses.flushinp()
        custom_name = stdscr.getstr().decode("utf-8").strip()
        curses.noecho()
        curses.curs_set(0)  # Hide cursor

        if not custom_name:
            stdscr.addstr(8, 2, "⚠️ Functionality creation cancelled.")
            stdscr.refresh()
            stdscr.getch()
            return

        success, message = create_functionality(custom_name, "Functionality.php")
    else:
        success, message = create_functionality(selection, FUNCTIONALITY_OPTIONS[selection])

    stdscr.clear()
    if success:
        stdscr.addstr(4, 2, f"✅ {message}")
    else:
        stdscr.addstr(4, 2, f"❌ {message}")

    stdscr.addstr(8, 2, "Press any key to return to the main menu.")
    stdscr.refresh()
    stdscr.getch()

def add_functionality(stdscr):
    """Displays a menu to select a functionality type and creates the corresponding PHP file."""

    stdscr.nodelay(0)
    stdscr.clear()
    stdscr.addstr(2, 2, "🔧 Add Functionality")
    stdscr.refresh()

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

