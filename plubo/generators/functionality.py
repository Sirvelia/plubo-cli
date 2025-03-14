import os
import curses
from pathlib import Path
from plubo.generators import project  # Import function to get the plugin name

# Define the absolute path to the templates directory (sibling folder)
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

# Functionality options and their respective PHP templates
FUNCTIONALITY_OPTIONS = {
    "Admin Menus": "Admin/AdminMenus.php",
    "Ajax Actions": "AjaxActions.php",
    "Api Endpoints": "ApiEndpoints.php",
    "Cart": "Cart.php",
    "Crons": "Crons.php",
    "Custom Fields": "CustomFields.php",
    "Orders": "Orders.php",
    "Post Actions": "PostActions.php",
    "Products": "Products.php",
    "Roles": "Roles.php",
    "Routes": "Routes.php",
    "Shortcodes": "Shortcodes.php",
    "Taxonomies": "Taxonomies.php",
    "Users": "Users.php",
    "Custom": "Functionality.php"  # Base template for user-defined classes
}

def add_functionality(stdscr):
    """Displays a menu to select a functionality type and creates the corresponding PHP file."""
    curses.curs_set(0)  # Hide cursor
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Message color

    stdscr.nodelay(0)
    stdscr.clear()
    stdscr.addstr(2, 2, "🔧 Add Functionality")
    stdscr.refresh()

    options = list(FUNCTIONALITY_OPTIONS.keys())
    current_row = 0

    while True:
        stdscr.clear()
        stdscr.addstr(2, 2, "🔧 Select a Functionality Type:")
        
        for idx, option in enumerate(options):
            x = 4
            y = 4 + idx
            if idx == current_row:
                stdscr.attron(curses.color_pair(3))
                stdscr.addstr(y, x, option)
                stdscr.attroff(curses.color_pair(3))
            else:
                stdscr.addstr(y, x, option)

        stdscr.refresh()
        key = stdscr.getch()

        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(options) - 1:
            current_row += 1
        elif key in [curses.KEY_ENTER, 10, 13]:  # Enter key pressed
            selection = options[current_row]

            if selection == "Custom":
                curses.curs_set(1)  # Show cursor for input
                stdscr.clear()
                stdscr.addstr(2, 2, "Enter Custom Functionality Name:")
                stdscr.refresh()

                curses.echo()
                stdscr.move(4, 2)
                curses.flushinp()
                custom_name = stdscr.getstr().decode("utf-8").strip()
                curses.noecho()

                if not custom_name:
                    stdscr.addstr(8, 2, "⚠️ Functionality creation cancelled.")
                    stdscr.refresh()
                    stdscr.getch()
                    curses.curs_set(0)  # Hide cursor
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
            curses.curs_set(0)  # Hide cursor


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

