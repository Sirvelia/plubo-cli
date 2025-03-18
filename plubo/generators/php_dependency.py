import subprocess
import curses
import json
import os
from plubo.utils import project

DEPENDENCY_OPTIONS = {
    "Routes": "joanrodas/plubo-routes",
    "Roles": "joanrodas/plubo-roles",
    "Logs": "sirvelia-labs/plubo-logs",
    "Checks": "sirvelia-labs/plubo-checks",
    "Jwt": "sirvelia/plubo-jwt",
    "Carbon Fields": "htmlburger/carbon-fields",
    "Action Scheduler": "woocommerce/action-scheduler",
    "Back to Main Menu": None  # Special case, no package to install
}

# Wildcat ASCII Art
WILDCAT_ASCII = r"""
       /\_/\  
      ( o.o )
       > ^ <  
"""

def get_installed_dependencies():
    """Read composer.json and return a dictionary of installed dependencies and versions."""
    composer_json_path = "composer.json"

    if not os.path.exists(composer_json_path):
        return {}

    try:
        with open(composer_json_path, "r", encoding="utf-8") as file:
            composer_data = json.load(file)
            return composer_data.get("require", {})  # Get dependencies from require section
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def install_dependency(stdscr, package_name):
    """Install a specific Composer dependency, handling Lando projects."""
    if not package_name:
        return  # Do nothing if the user selects "Back to Main Menu"

    stdscr.clear()
    stdscr.addstr(1, 2, f"⏳ Installing {package_name}...", curses.A_BOLD)  # Display message
    stdscr.refresh()
    
    height, width = stdscr.getmaxyx()
    box_height = height - 6  # Leave space for the message
    box_width = width - 4
    box_start_y = 3
    box_start_x = 2

    # Draw the bordered box for output
    output_win = curses.newwin(box_height, box_width, box_start_y, box_start_x)
    output_win.border()
    output_win.scrollok(True)  # Allow scrolling
    output_win.refresh()

    command = ["lando", "composer", "require", package_name] if project.is_lando_project() else ["composer", "require", package_name]
    
    # Start process with live output capture
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

    line_y = 1  # First line inside the box
    while True:
        line = process.stdout.readline()
        if not line and process.poll() is not None:
            break  # Exit loop if process is done and no more output

        if line_y >= box_height - 2:  # Scroll if output exceeds window height
            output_win.scroll()
        else:
            line_y += 1

        output_win.addstr(line_y, 2, line.strip())  # Display new line inside box
        output_win.border()  # Keep the border visible
        output_win.refresh()

    process.wait()  # Ensure the process completes

    # Display completion message
    success = process.returncode == 0
    message = f"✅ Successfully installed {package_name}" if success else f"❌ Installation failed for {package_name}"
    
    stdscr.addstr(height - 3, 2, message, curses.color_pair(3))
    stdscr.addstr(height - 2, 2, "[Press any key to return]", curses.A_BOLD)
    stdscr.refresh()

    # **Wait for user input before returning**
    stdscr.nodelay(False)  # Set to blocking mode
    stdscr.getch()  # Wait user input

def dependency_menu(stdscr):
    """Display the dependency installation submenu with a background title."""
    curses.curs_set(0)  # Hide cursor
    stdscr.nodelay(0)
    stdscr.timeout(100)
    curses.mousemask(1)  # Enable mouse support
    
    installed_dependencies = get_installed_dependencies()

    current_row = 0
    options = list(DEPENDENCY_OPTIONS.keys())  # Get option names

    while True:
        stdscr.clear()
        draw_background_with_title(
            stdscr,
            "WELCOME TO PLUBO-CLI!",  # Title
            "Plugin: new-plugiiin",   # Subtitle
            6,  # Title color (cyan)
            3   # Subtitle color (yellow)
        )

        height, width = stdscr.getmaxyx()
        start_y = len(WILDCAT_ASCII.split("\n")) + 5  # Adjust menu position below the wildcat

        for idx, option in enumerate(options):
            x = 10
            y = start_y + idx
            
            package_name = DEPENDENCY_OPTIONS[option]
            checkmark = ""
            version_info = ""

            if package_name and package_name in installed_dependencies:
                checkmark = "✅"
                version_info = f"--> Current version: {installed_dependencies[package_name]}"

            display_text = f"{checkmark} {option} {version_info}".strip()

            if idx == current_row:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(y, x, display_text)
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(y, x, display_text)

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


def draw_background_with_title(stdscr, title, subtitle, title_color, subtitle_color):
    """Draws the wildcat ASCII on the left and the title & subtitle aligned to its right."""
    stdscr.clear()

    height, width = stdscr.getmaxyx()

    # Align the title & subtitle
    title_x = 2
    title_y = 2

    subtitle_x = title_x  # Subtitle aligned with title
    subtitle_y = title_y + 1  # Right below the title

    # Print title & subtitle
    stdscr.addstr(title_y, title_x, title, curses.color_pair(title_color) | curses.A_BOLD)
    stdscr.addstr(subtitle_y, subtitle_x, subtitle, curses.color_pair(subtitle_color))

    # Display the version at the bottom
    version_text = "plubo-cli v0.1"
    stdscr.addstr(height - 2, (width - len(version_text)) // 2, version_text, curses.color_pair(3))

    # stdscr.refresh()