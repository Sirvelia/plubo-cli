import os
import re
import subprocess
import curses
from pathlib import Path
from plubo.utils import interface, colors

def is_lando_project():
    """Check if the project is running inside a Lando environment by searching for .lando.yml in parent directories."""
    current_dir = os.getcwd()  # Get the current working directory
    while True:
        lando_file = os.path.join(current_dir, ".lando.yml")
        if os.path.exists(lando_file):
            return True #subprocess.run(["which", "lando"], capture_output=True, text=True).returncode == 0
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            break  # Reached the root directory
        current_dir = parent_dir
    return False  # .lando.yml not found

def detect_wp_root():
    """Find the WordPress root directory by checking for wp-config.php."""
    current_path = Path(os.getcwd())
    while current_path != current_path.parent:
        if (current_path / "wp-config.php").exists():
            return current_path
        current_path = current_path.parent
    return None

def detect_plugin_name():
    """Finds the main plugin file and extracts the plugin name from 'Text Domain'."""
    plugin_root = Path(os.getcwd())
    
    for file in plugin_root.glob("*.php"):
        with file.open("r", encoding="utf-8") as f:
            content = f.read()
            match = re.search(r"Text Domain:\s*(.+)", content)
            if match:
                return match.group(1).strip()
    
    return None

def is_wp_cli_available():
    """Check if WP-CLI is installed."""
    return subprocess.run(["which", "wp"], capture_output=True, text=True).returncode == 0

def run_command(command, cwd, stdscr):
    """Execute a shell command and display output in curses UI."""
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
    
    # Start process with live output capture
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, cwd=str(cwd))

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

    return process.returncode == 0