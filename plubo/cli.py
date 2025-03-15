import curses
import sys
import time
from plubo.generators import functionality, component, entity, elements, php_dependency, node_dependency, plugin
from plubo.utils import project
from plubo.settings import settings

# Wildcat ASCII Art
WILDCAT_ASCII = r"""
       /\_/\  
      ( o.o )  WELCOME TO PLUBO-CLI!
       > ^ <   
"""


MENU_OPTIONS_ALL = [
    "Add Functionality Class",
    "Add Component Class",
    "Add Entity Class",
    "Install PHP Dependency",
    "Install Node Dependency",
    "Add Element",
    "Create Plugin",
    "Init Repo",
    "Rename Plugin",
    "Settings",
    "Exit"
]

MENU_OPTIONS_WP_ONLY = [
    "Create Plugin",
    "Settings",
    "Exit"
]

MENU_OPTIONS_NO_WP = [
    "Settings",
    "Exit"
]

def get_menu_options():
    """Determine the correct menu options based on the environment."""
    wp_root = project.detect_wp_root()
    if not wp_root:
        return MENU_OPTIONS_NO_WP  # Not in a WordPress installation
    
    plugin_name = project.detect_plugin_name()
    if not plugin_name:
        return MENU_OPTIONS_WP_ONLY  # In WordPress but not inside a plugin
    
    return MENU_OPTIONS_ALL  # Inside a plugin

def draw_background(stdscr):
    """Draws the wildcat and Plubo version in the background"""
    stdscr.clear()
    
    height, width = stdscr.getmaxyx()
    wildcat_lines = WILDCAT_ASCII.split("\n")

    # Center the ASCII wildcat
    start_x = (width // 2) - (max(len(line) for line in wildcat_lines) // 2)
    start_y = 2  # Start near the top
    
    for i, line in enumerate(wildcat_lines):
        stdscr.addstr(start_y + i, start_x, line, curses.color_pair(2))
    
    # Plugin name display
    plugin_name = project.detect_plugin_name()
    if plugin_name:
        plugin_text = f"Plugin: {plugin_name}"
        stdscr.addstr(5, 37, plugin_text, curses.color_pair(3) | curses.A_DIM)
    
    else:
        wp_root = project.detect_wp_root()
        if not wp_root:
            stdscr.addstr(5, 37, "No WordPress installation found!", curses.color_pair(4) | curses.A_DIM)
        else:
            plugin_text = f"WP: {wp_root}"
            stdscr.addstr(5, 37, plugin_text, curses.color_pair(3) | curses.A_DIM)

    # Display the version at the bottom
    version_text = "plubo-cli v0.1"
    stdscr.addstr(height - 2, (width - len(version_text)) // 2, version_text, curses.color_pair(4))

def menu(stdscr):
    """Displays the interactive full-terminal menu"""
    curses.curs_set(0)  # Hide cursor
    stdscr.nodelay(0)
    stdscr.timeout(100)

    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Highlighted option
    curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)  # ASCII Wildcat
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Plugin Name Text
    curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)  # Version Text
            
    stdscr.keypad(True)
    
    # Enable mouse events
    curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)

    current_row = 0
    
    while True:
        menu_options = get_menu_options()
        
        stdscr.clear()
        draw_background(stdscr)  # Keep the wildcat & version persistent
        height, width = stdscr.getmaxyx()

        # Center the menu vertically
        start_y = len(WILDCAT_ASCII.split("\n")) + 4

        for idx, option in enumerate(menu_options):
            x = (width // 2) - (len(option) // 2)
            y = start_y + idx

            if idx == current_row:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(y, x, option)
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(y, x, option)

        stdscr.refresh()

        key = stdscr.getch()
        
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(menu_options) - 1:
            current_row += 1
        elif key == curses.KEY_RESIZE:
            # Handle window resizing by redrawing
            stdscr.clear()
        elif key in [curses.KEY_ENTER, 10, 13]:  # Enter key pressed
            if handle_selection(stdscr, current_row, menu_options, height, width):
                return
        elif key == curses.KEY_MOUSE:
            try:
                _, mouse_x, mouse_y, _, _ = curses.getmouse()
                # Check if the mouse click is within the menu options
                for idx, option in enumerate(menu_options):
                    x = (width // 2) - (len(option) // 2)
                    y = start_y + idx
                    if y == mouse_y and x <= mouse_x < x + len(option):
                        current_row = idx
                        if handle_selection(stdscr, current_row, menu_options, height, width):
                            return
            except curses.error:
                pass
                
def handle_selection(stdscr, current_row, menu_options, height, width):
    """Handle the selection of a menu option"""
    selection = menu_options[current_row]
    
    if selection == "Exit":
        return True # Exit the CLI

    try:
        if selection == "Rename Plugin":
            plugin.rename_project(stdscr)
        elif selection == "Create Plugin":
            plugin.create_project(stdscr)
        elif selection == "Init Repo":
            plugin.init_repo(stdscr)
        elif selection == "Add Functionality Class":
            functionality.add_functionality(stdscr)
        elif selection == "Add Component Class":
            component.add_component(stdscr)
        elif selection == "Add Entity Class":
            entity.add_entity(stdscr)
        elif selection == "Install PHP Dependency":
            php_dependency.dependency_menu(stdscr)
        elif selection == "Install Node Dependency":
            node_dependency.dependency_menu(stdscr)
        elif selection == "Add Element":
            elements.add_element(stdscr)
        elif selection == "Settings":
            settings.draw_settings_menu(stdscr)
        
        # Show success message
        stdscr.addstr(height - 4, (width // 2) - 10, "✅ Action Completed!", curses.color_pair(3))
        stdscr.refresh()
        time.sleep(1)

    except Exception as e:
        stdscr.addstr(height - 4, (width // 2) - 15, f"❌ Error: {str(e)}", curses.color_pair(3))
        stdscr.refresh()
        time.sleep(2)
    
    return False
        
def cli():
    """Launch the full-screen Plubo CLI with optional direct commands"""
     # Check for direct command-line execution
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "rename" and len(sys.argv) == 3:
            new_name = sys.argv[2]
            try:
                plugin.rename_project(new_name)
                print(f"✅ Plugin renamed to {new_name} successfully.")
            except Exception as e:
                print(f"❌ Error: {str(e)}")
            return  # Exit after execution

    # If no direct command, launch the interactive menu
    curses.wrapper(menu)

if __name__ == "__main__":
    cli()
