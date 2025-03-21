import curses
import sys
import time
from plubo.generators import functionality, component, entity, elements, php_dependency, node_dependency, plugin, dependencies
from plubo.utils import project, interface, colors
from plubo.settings import settings
from plubo.cli.dispatcher import dispatch

MENU_OPTIONS_ALL = [
    "ADD FUNCTIONALITY CLASS",
    "ADD COMPONENT CLASS",
    "ADD ENTITY CLASS",
    "ADD ELEMENT",
    "INSTALL PHP DEPENDENCY",
    "INSTALL NODE DEPENDENCY",
    "CHECK DEPENDENCIES",
    "INIT REPO",
    "RENAME PLUGIN",
    "PREPARE RELEASE",
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

    colors.init_colors()            
    
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
        elif selection == "CHECK DEPENDENCIES":
            dependencies.dependency_checker(stdscr)
        elif selection == "PREPARE RELEASE":
            plugin.prepare_release(stdscr)
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
        
def main():
    """Launch the full-screen Plubo CLI with optional direct commands"""
    dispatch(menu)

if __name__ == "__main__":
    main()
