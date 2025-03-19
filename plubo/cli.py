import curses
import sys
import time
from plubo.generators import functionality, component, entity, elements, php_dependency, node_dependency, plugin
from plubo.utils import project, interface
from plubo.settings import settings

MENU_OPTIONS_ALL = [
    "ADD FUNCTIONALITY CLASS",
    "ADD COMPONENT CLASS",
    "ADD ENTITY CLASS",
    "INSTALL PHP DEPENDENCY",
    "INSTALL NODE DEPENDENCY",
    "ADD ELEMENT",
    "CREATE PLUGIN",
    "INIT REPO",
    "RENAME PLUGIN",
    "SETTINGS",
    "EXIT"
]

MENU_OPTIONS_WP_ONLY = [
    "CREATE PLUGIN",
    "SETTINGS",
    "EXIT"
]

MENU_OPTIONS_NO_WP = [
    "SETTINGS",
    "EXIT"
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

    
def menu(stdscr):
    """Displays the interactive full-terminal menu"""
    curses.curs_set(0)  # Hide cursor
    stdscr.keypad(True)

    curses.start_color()
    # Check if terminal supports custom colors
    if curses.can_change_color():
        curses.init_color(1, 15 * 4, 56 * 4, 15 * 4)  # Dark Green (Text)
        curses.init_color(2, 155 * 4, 188 * 4, 15 * 4)  # Light Green (Background)
        curses.init_color(3, 48 * 4, 98 * 4, 48 * 4)  # Medium Green (Borders)

        # Set color pairs
        curses.init_pair(1, 1, curses.COLOR_WHITE)  # Normal Text (Dark Green on Light Green)
        curses.init_pair(2, 4, curses.COLOR_WHITE)  # Highlighted Option
        curses.init_pair(3, 3, curses.COLOR_WHITE)  # Titles & Borders
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_WHITE)  # Error messages
        curses.init_pair(5, 1, 2)  # Terminal

    else:
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_WHITE)  # Normal text
        curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_WHITE)  # Highlighted text
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Titles & Borders
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_WHITE)  # Error messages
        curses.init_pair(5, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Terminal
            
    
    # Enable mouse events
    curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)

    current_row = 0
    
    # Get initial screen size
    height, width = stdscr.getmaxyx()
    
     # Ensure minimum size for UI
    min_height, min_width = 12, 40  # Prevent tiny windows
    if height < min_height or width < min_width:
        stdscr.addstr(0, 0, "Terminal too small! Resize and restart.", curses.color_pair(4))
        stdscr.refresh()
        time.sleep(2)
        return    
        
    while True:
        menu_options = get_menu_options()
        selected_row, current_row = interface.render_menu(stdscr, menu_options, current_row, height, width)
        if selected_row is not None:
            if handle_selection(stdscr, selected_row, menu_options, height, width):
                return # Exit the CLI if handle_selection returns True
        
                
def handle_selection(stdscr, current_row, menu_options, height, width):
    """Handle the selection of a menu option"""
    if current_row < 0 or current_row >= len(menu_options):
        return False  # Invalid selection
    
    selection = menu_options[current_row]
    
    if selection == "EXIT":
        return True # Exit the CLI

    try:
        if selection == "RENAME PLUGIN":
            plugin.rename_project(stdscr)
        elif selection == "CREATE PLUGIN":
            plugin.create_project(stdscr)
        elif selection == "INIT REPO":
            plugin.init_repo(stdscr)
        elif selection == "ADD FUNCTIONALITY CLASS":
            functionality.add_functionality(stdscr)
        elif selection == "ADD COMPONENT CLASS":
            component.add_component(stdscr)
        elif selection == "ADD ENTITY CLASS":
            entity.add_entity(stdscr)
        elif selection == "INSTALL PHP DEPENDENCY":
            php_dependency.dependency_menu(stdscr)
        elif selection == "INSTALL NODE DEPENDENCY":
            node_dependency.dependency_menu(stdscr)
        elif selection == "ADD ELEMENT":
            elements.add_element(stdscr)
        elif selection == "SETTINGS":
            settings.draw_settings_menu(stdscr)
        
        # Show success message
        stdscr.addstr(height - 4, (width // 2) - 10, "✅ Action Completed!", curses.color_pair(3))
        curses.doupdate()
        # time.sleep(1)

    except Exception as e:
        stdscr.addstr(height - 4, (width // 2) - 15, f"❌ Error: {str(e)}", curses.color_pair(3))
        curses.doupdate()
        # time.sleep(2)
    
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
