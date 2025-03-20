import subprocess
import curses
import time
import os
import json
from plubo.utils import project, interface, colors


DEPENDENCY_OPTIONS = {
    "ALPINE.JS": "alpinejs @types/alpinejs",
    "TAILWIND CSS": "tailwindcss",
    "DAISY UI": "daisyui@latest",
    "HIKEFLOW": "hikeflow",
    "RETURN": None  # Special case, no package to install
}

def get_installed_dependencies():
    """Read package.json and return a dictionary of installed dependencies and versions."""
    package_json_path = "package.json"

    if not os.path.exists(package_json_path):
        return {}

    try:
        with open(package_json_path, "r", encoding="utf-8") as file:
            deps_data = json.load(file)
            
            # Merge dependencies and devDependencies
            dependencies = deps_data.get("dependencies", {})
            dev_dependencies = deps_data.get("devDependencies", {})

            return {**dependencies, **dev_dependencies}  # Merge both dictionaries
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

    command = ["yarn", "add"] + package_name.split()
    
    # Start process with live output capture
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

    line_y = 1  # First line inside the box
    inner_width = box_width - 4
    
    while True:
        line = process.stdout.readline()
        if not line and process.poll() is not None:
            break  # Exit loop if process is done and no more output

        # Parse ANSI color codes and split text into segments
        segments = colors.parse_ansi_colors(line.strip())
        wrapped_lines = colors.wrap_text(segments, inner_width)  # Wrap text if necessary

        for wrapped_line in wrapped_lines:
            if line_y >= box_height - 2:  # Scroll if output exceeds window height
                output_win.scroll()
            else:
                line_y += 1

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
    stdscr.refresh()

    # **Wait for user input before returning**
    stdscr.getch()  # Wait user input

def dependency_menu(stdscr):
    """Display the dependency installation submenu with a background title."""
    curses.curs_set(0)  # Hide cursor   
    stdscr.keypad(True)
        
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
                version_info = f" {installed_dependencies[package_name]}"
            
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