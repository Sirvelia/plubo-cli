import curses
import time
from plubo.generators import functionality, component, entity, elements, php_dependency, node_dependency, project

# Wildcat ASCII Art
WILDCAT_ASCII = r"""
       /\_/\  
      ( o.o )  WELCOME TO PLUBO-CLI!
       > ^ <  
"""

MENU_OPTIONS = [
    "Add Functionality Class",
    "Add Component Class",
    "Add Entity Class",
    "Install PHP Dependency",
    "Install Node Dependency",
    "Add Element",
    "Rename Plugin",
    "Exit"
]

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

    # Display the version at the bottom
    version_text = "plubo-cli v0.1"
    stdscr.addstr(height - 2, (width - len(version_text)) // 2, version_text, curses.color_pair(3))

def menu(stdscr):
    """Displays the interactive full-terminal menu"""
    curses.curs_set(0)  # Hide cursor
    stdscr.nodelay(0)
    stdscr.timeout(100)

    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Highlighted option
    curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)  # ASCII Wildcat
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Version Text
            
    stdscr.keypad(True)
    
    # Enable mouse events
    curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)

    current_row = 0

    while True:
        stdscr.clear()
        draw_background(stdscr)  # Keep the wildcat & version persistent
        height, width = stdscr.getmaxyx()

        # Center the menu vertically
        start_y = len(WILDCAT_ASCII.split("\n")) + 4

        for idx, option in enumerate(MENU_OPTIONS):
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
        elif key == curses.KEY_DOWN and current_row < len(MENU_OPTIONS) - 1:
            current_row += 1
        elif key == curses.KEY_RESIZE:
            # Handle window resizing by redrawing
            stdscr.clear()
        elif key in [curses.KEY_ENTER, 10, 13]:  # Enter key pressed
            if handle_selection(stdscr, current_row, height, width):
                return
        elif key == curses.KEY_MOUSE:
            try:
                _, mouse_x, mouse_y, _, _ = curses.getmouse()
                # Check if the mouse click is within the menu options
                for idx, option in enumerate(MENU_OPTIONS):
                    x = (width // 2) - (len(option) // 2)
                    y = start_y + idx
                    if y == mouse_y and x <= mouse_x < x + len(option):
                        current_row = idx
                        if handle_selection(stdscr, current_row, height, width):
                            return
            except curses.error:
                pass
                
def handle_selection(stdscr, current_row, height, width):
    """Handle the selection of a menu option"""
    selection = MENU_OPTIONS[current_row]
    
    if selection == "Exit":
        return True # Exit the CLI

    try:
        if selection == "Rename Plugin":
            project.rename_project(stdscr)
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
    """Launch the full-screen Plubo CLI with the wildcat background"""
    curses.wrapper(menu)

if __name__ == "__main__":
    cli()
