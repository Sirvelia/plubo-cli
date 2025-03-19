import subprocess
import curses
import json
import os
import re
from plubo.utils import project, interface

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

# Define ANSI color mapping for curses
ANSI_COLOR_MAP = {
    '30': curses.COLOR_BLACK,   # Black
    '31': curses.COLOR_RED,     # Red
    '32': curses.COLOR_GREEN,   # Green
    '33': curses.COLOR_YELLOW,  # Yellow
    '34': curses.COLOR_BLUE,    # Blue
    '35': curses.COLOR_MAGENTA, # Magenta
    '36': curses.COLOR_CYAN,    # Cyan
    '37': curses.COLOR_WHITE    # White
}

# Regex pattern to match ANSI escape sequences
ANSI_PATTERN = re.compile(r'\x1B\[(\d+)m')

def init_colors():
    """Initialize color pairs for curses."""
    curses.start_color()
    pair_number = 10  # Start from 10 to avoid conflicts with system colors
    
    for ansi_code, color in ANSI_COLOR_MAP.items():
        curses.init_pair(pair_number, color, curses.COLOR_BLACK)  # Foreground color
        ANSI_COLOR_MAP[ansi_code] = curses.color_pair(pair_number)  # Store curses color pair
        pair_number += 1

def parse_ansi_colors(text):
    """
    Parses ANSI color sequences in a line and returns a list of (text_segment, curses_color_pair).
    Handles multiple colors in a single line.
    """
    segments = []
    last_color = curses.color_pair(17)  # Default color
    parts = ANSI_PATTERN.split(text)

    for part in parts:
        if part.isdigit():  # If it's a color code
            ansi_code = part
            last_color = ANSI_COLOR_MAP.get(ansi_code, curses.color_pair(17))  # Get color pair
        else:
            if part:  # Non-empty text segment
                segments.append((part, last_color))

    return segments

def wrap_text(segments, max_width):
    """
    Wraps long lines into multiple lines while preserving color.
    Returns a list of (line_segments, color) tuples.
    """
    wrapped_lines = []
    current_line = []
    current_length = 0

    for text, color in segments:
        words = text.split(' ')
        for word in words:
            if current_length + len(word) + 1 > max_width:
                wrapped_lines.append(current_line)  # Store the current line
                current_line = []  # Start a new line
                current_length = 0

            current_line.append((word + ' ', color))
            current_length += len(word) + 1

    if current_line:
        wrapped_lines.append(current_line)  # Append any remaining text

    return wrapped_lines

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
    interface.draw_background(stdscr, f"⏳ Installing {package_name}...")
    
    height, width = stdscr.getmaxyx()
    box_height = height - 6  # Leave space for the message
    box_width = width - 8
    box_start_y = 3
    box_start_x = 4

    # Draw the bordered box for output
    output_win = curses.newwin(box_height, box_width, box_start_y, box_start_x)
    output_win.border()
    output_win.scrollok(True)  # Allow scrolling
    output_win.refresh()

    command = ["lando", "composer", "require", package_name] if project.is_lando_project() else ["composer", "require", package_name]
    
    # Start process with live output capture
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

    line_y = 1  # First line inside the box
    inner_width = box_width - 4
    
    while True:
        line = process.stdout.readline()
        if not line and process.poll() is not None:
            break  # Exit loop if process is done and no more output

        # Parse ANSI color codes and split text into segments
        segments = parse_ansi_colors(line.strip())
        wrapped_lines = wrap_text(segments, inner_width)  # Wrap text if necessary

        for wrapped_line in wrapped_lines:
            if line_y >= box_height - 2:  # Scroll if output exceeds window height
                output_win.scroll()
            else:
                line_y += 1

            # **Fix 1: Clear the entire line before writing to prevent artifacts**
            output_win.addstr(line_y, 1, " " * (inner_width + 2), curses.color_pair(10))

            col_x = 2  # Starting position for text inside the box
            for segment_text, color_pair in wrapped_line:
                output_win.addstr(line_y, col_x, segment_text, color_pair)
                col_x += len(segment_text)
        
        output_win.border()  # Keep the border visible
        output_win.refresh()

    process.wait()  # Ensure the process completes

    # Display completion message
    success = process.returncode == 0
    message = f"✅ Successfully installed {package_name}" if success else f"❌ Installation failed for {package_name}"
    
    stdscr.addstr(height - 3, 4, message, curses.color_pair(3))
    # stdscr.addstr(height - 2, 2, "[Press any key to return]", curses.A_BOLD)
    stdscr.refresh()

    # **Wait for user input before returning**
    # stdscr.nodelay(False)  # Set to blocking mode
    stdscr.getch()  # Wait user input

def dependency_menu(stdscr):
    """Display the dependency installation submenu with a background title."""
    curses.curs_set(0)  # Hide cursor   
    stdscr.keypad(True)
    
    init_colors()
    
    current_row = 0
    height, width = stdscr.getmaxyx()

    while True:
        installed_dependencies = get_installed_dependencies()
        menu_options = []
        original_names = []  # To map displayed names back to actual options

        for option, package_name in DEPENDENCY_OPTIONS.items():
            checkmark = ""
            version_info = ""

            if package_name and package_name in installed_dependencies:
                checkmark = "✅"
                version_info = f"--> {installed_dependencies[package_name]}"
            
            display_text = f"{checkmark} {option} {version_info}".strip()
            menu_options.append(display_text)
            original_names.append(option)  # Keep track of original option names
            
        selected_row, current_row = interface.render_menu(stdscr, menu_options, current_row, height, width)
        
        if selected_row is not None:
            selected_option = original_names[selected_row]
            package_name = DEPENDENCY_OPTIONS[selected_option]
            if package_name is not None:
                install_dependency(stdscr, package_name)
            return