import subprocess
import curses
import time
from plubo.utils import project

DEPENDENCY_OPTIONS = {
    "Routes": "joanrodas/plubo-routes",
    "Roles": "joanrodas/plubo-roles",
    "Logs": "Sirvelia-Labs/plubo-logs",
    "Checks": "Sirvelia-Labs/plubo-checks",
    "Jwt": "sirvelia/plubo-jwt",
    "Carbon Fields": "htmlburger/carbon-fields",
    "Action Scheduler": "woocommerce/action-scheduler",
    "Back to Main Menu": None  # Special case, no package to install
}

# Wildcat ASCII Art
WILDCAT_ASCII = r"""
       /\_/\  
      ( o.o )  WELCOME TO PLUBO-CLI!
       > ^ <  
"""

def install_dependency(stdscr, package_name):
    """Install a specific Composer dependency, handling Lando projects."""
    if not package_name:
        return  # Do nothing if the user selects "Back to Main Menu"

    curses.endwin()  # Exit curses mode so the user can interact normally
    print(f"\n⏳ Installing {package_name}...\n")  # Inform user

    command = ["lando", "composer", "require", package_name] if project.is_lando_project() else ["composer", "require", package_name]
    
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=None, stderr=None)
    process.communicate()  # Wait for process to complete

    # Restore curses mode
    curses.initscr()
    stdscr.clear()
    stdscr.refresh()

    success = process.returncode == 0
    message = f"✅ Successfully installed {package_name}" if success else f"❌ Installation failed for {package_name}"
    stdscr.addstr(0, 0, message, curses.color_pair(3))
    stdscr.refresh()
    time.sleep(2)  # Pause before returning

def dependency_menu(stdscr):
    """Display the dependency installation submenu with a background title."""
    curses.curs_set(0)  # Hide cursor
    stdscr.nodelay(0)
    stdscr.timeout(100)
    curses.mousemask(1)  # Enable mouse support

    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Highlight color
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Message color

    current_row = 0
    options = list(DEPENDENCY_OPTIONS.keys())  # Get option names

    while True:
        stdscr.clear()
        draw_background_with_title(stdscr, "INSTALL COMPOSER DEPENDENCY")

        height, width = stdscr.getmaxyx()
        start_y = len(WILDCAT_ASCII.split("\n")) + 5  # Adjust menu position below the wildcat

        for idx, option in enumerate(options):
            x = 10
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
        elif key == curses.KEY_DOWN and current_row < len(options) - 1:
            current_row += 1
        elif key in [curses.KEY_ENTER, 10, 13]:  # Enter key pressed
            selection = options[current_row]
            package_name = DEPENDENCY_OPTIONS[selection]

            if selection == "Back to Main Menu":
                break  # Return to the main menu

            install_dependency(stdscr, package_name)
        
        elif key == curses.KEY_MOUSE:
            try:
                _, mouse_x, mouse_y, _, _ = curses.getmouse()
                for idx, option in enumerate(options):
                    x = 10
                    y = start_y + idx
                    if y == mouse_y and x <= mouse_x < x + len(option):
                        current_row = idx
                        package_name = DEPENDENCY_OPTIONS[options[current_row]]

                        if options[current_row] == "Back to Main Menu":
                            return  # Exit

                        install_dependency(stdscr, package_name)
                        break
            except curses.error:
                pass


def draw_background_with_title(stdscr, title):
    """Draws the wildcat and a submenu title in the background"""
    stdscr.clear()
    
    height, width = stdscr.getmaxyx()
    wildcat_lines = WILDCAT_ASCII.split("\n")

    # Center the ASCII wildcat
    start_x = (width // 2) - (max(len(line) for line in wildcat_lines) // 2)
    start_y = 2  # Start near the top

    for i, line in enumerate(wildcat_lines):
        stdscr.addstr(start_y + i, start_x, line, curses.color_pair(2))

    # Display the title
    title_x = (width // 2) - (len(title) // 2)
    stdscr.addstr(start_y + len(wildcat_lines) + 1, title_x, title, curses.color_pair(3))

    # Display the version at the bottom
    version_text = "plubo-cli v0.1"
    stdscr.addstr(height - 2, (width - len(version_text)) // 2, version_text, curses.color_pair(3))
