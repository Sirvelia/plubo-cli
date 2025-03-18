import curses
import time
from plubo.utils import project

# PB-CLI Game Boy ASCII Art
PB_CLI_ASCII = [
    "╔═╗╔╗    ╔═╗╦  ╦",
    "╠═╝╠╩╗───║  ║  ║",
    "╩  ╚═╝   ╚═╝╩═╝╩"
]

def draw_background(stdscr, title=None):
    """Draws the UI background, title, and project information, but excludes the menu."""
    stdscr.clear()
    height, width = stdscr.getmaxyx()

    # Outer Border
    stdscr.addstr(1, 1, "╔" + "═" * (width - 4) + "╗", curses.color_pair(3))
    for y in range(2, height - 2):
        stdscr.addstr(y, 1, "║" + " " * (width - 4) + "║", curses.color_pair(3))
    stdscr.addstr(height - 2, 1, "╚" + "═" * (width - 4) + "╝", curses.color_pair(3))

    # ASCII Art Title (If Available)
    if title:
        stdscr.addstr(2, (width - len(title)) // 2, title, curses.color_pair(2) | curses.A_BOLD)
        text_position = 3
    else:
        text_position = 5
        for i, line in enumerate(PB_CLI_ASCII):
            stdscr.addstr(2 + i, (width // 2) - (len(line) // 2), line, curses.color_pair(3) | curses.A_BOLD)

    # Plugin Name / WordPress Path Info
    plugin_name = project.detect_plugin_name()
    if plugin_name:
        plugin_text = f"Plugin: {plugin_name}"
        stdscr.addstr(text_position, (width - len(plugin_text)) // 2, plugin_text, curses.color_pair(3) | curses.A_DIM)
    else:
        wp_root = project.detect_wp_root()
        if not wp_root:
            wp_text = f"No WordPress installation found!"
            stdscr.addstr(text_position, (width - len(wp_text)) // 2, wp_text, curses.color_pair(3) | curses.A_DIM)
        else:
            wp_text = f"WP: {wp_root}"
            stdscr.addstr(text_position, (width - len(wp_text)) // 2, wp_text, curses.color_pair(3) | curses.A_DIM)

    # Display the version at the bottom
    version_text = "plubo-cli v0.1"
    stdscr.addstr(height - 4, (width - len(version_text)) // 2, version_text, curses.color_pair(3))

    stdscr.refresh()
    
def render_menu(stdscr, menu_options, current_row, height, width):
    # Calculate menu width based on the longest option
    menu_width = max(len(option) for option in menu_options) + 6
    menu_x = (width - menu_width) // 2  # Center the menu
    menu_y = 8
    
    # Outer Border
    stdscr.addstr(1, 2, "╔" + "═" * (width - 6) + "╗", curses.color_pair(3))
    for y in range(2, height - 2):
        stdscr.addstr(y, 2, "║" + " " * (width - 6) + "║", curses.color_pair(3))
    stdscr.addstr(height - 2, 2, "╚" + "═" * (width - 6) + "╝", curses.color_pair(3))

    # TITLE
    for i, line in enumerate(PB_CLI_ASCII):
        stdscr.addstr(2 + i, (width // 2) - (len(line) // 2), line, curses.color_pair(3) | curses.A_BOLD)
    
    # Plugin name display
    plugin_name = project.detect_plugin_name()
    if plugin_name:
        plugin_text = f"Plugin: {plugin_name}"
        stdscr.addstr(5, (width - len(plugin_text)) // 2, plugin_text, curses.color_pair(3) | curses.A_DIM)
    
    else:
        wp_root = project.detect_wp_root()
        if not wp_root:
            wp_text = f"No WordPress installation found!"
            stdscr.addstr(5, (width - len(wp_text)) // 2, wp_text, curses.color_pair(3) | curses.A_DIM)
        else:
            wp_text = f"WP: {wp_root}"
            stdscr.addstr(5, (width - len(wp_text)) // 2, wp_text, curses.color_pair(3) | curses.A_DIM)

    # Inner Box for Menu
    stdscr.addstr(menu_y - 1, menu_x, "╔" + "═" * (menu_width - 2) + "╗", curses.color_pair(3))
    for y in range(len(menu_options) + 0):
        stdscr.addstr(menu_y + y, menu_x, "║" + " " * (menu_width - 2) + "║", curses.color_pair(3))
    stdscr.addstr(menu_y + len(menu_options) + 0, menu_x, "╚" + "═" * (menu_width - 2) + "╝", curses.color_pair(3))

    # Display menu options
    for idx, option in enumerate(menu_options):
        x = menu_x + 4  
        y = menu_y + idx  

        if idx == current_row:
            stdscr.attron(curses.color_pair(2))
            stdscr.addstr(y, x - 2, "▶ ")  
            stdscr.addstr(y, x, option)
            stdscr.attroff(curses.color_pair(2))
        else:
            stdscr.addstr(y, x, option, curses.color_pair(1))
    
    # Display the version at the bottom
    version_text = "plubo-cli v0.1"
    stdscr.addstr(height - 3, (width - len(version_text)) // 2, version_text, curses.color_pair(3))


    stdscr.refresh()
    key = stdscr.getch()
    
    if key == curses.KEY_UP and current_row > 0:
        current_row -= 1
    elif key == curses.KEY_DOWN and current_row < len(menu_options) - 1:
        current_row += 1
    elif key == curses.KEY_RESIZE:
        return None, current_row
    elif key in [curses.KEY_ENTER, 10, 13]:  # Enter key pressed
        return current_row, current_row
    elif key == curses.KEY_MOUSE:
        try:
            _, mouse_x, mouse_y, _, _ = curses.getmouse()  
            for idx, option in enumerate(menu_options):
                y = menu_y + 0 + idx  # Match menu item y-position
                if mouse_y == y:
                    return idx, current_row
        except curses.error:
            pass
    
    return None, current_row

def draw_title(stdscr, title):
    """Draws a centered title for settings pages."""
    height, width = stdscr.getmaxyx()
    stdscr.addstr(2, (width - len(title)) // 2, title, curses.color_pair(2) | curses.A_BOLD)

def display_message(stdscr, message, msg_type="info"):
    """Displays a status message with color based on type."""
    color_map = {"success": 1, "error": 4, "info": 2}
    stdscr.addstr(15, 4, message, curses.color_pair(color_map.get(msg_type, 2)) | curses.A_BOLD)
    stdscr.refresh()


def draw_input_box(stdscr, y, x, question_lines, input_lines, box_width, border_color, text_color, hidden=False):
    """
    Redraws the entire input box based on the current content.
    Returns the current box height.
    """
    # Calculate the total box height: question lines + input lines + 2 borders (top and bottom)
    box_height = len(question_lines) + len(input_lines) + 2

    # Draw top border
    stdscr.addstr(y - 1, x, "╔" + "═" * (box_width - 2) + "╗", border_color)

    # Draw question lines (with consistent padding)
    for i, line in enumerate(question_lines):
        stdscr.addstr(y + i, x, "║", border_color)
        stdscr.addstr(y + i, x + 2, line.ljust(box_width - 4), border_color)
        stdscr.addstr(y + i, x + box_width - 1, "║", border_color)

    # Draw input lines starting right after the question lines (with same padding)
    input_start_y = y + len(question_lines)
    for i, line in enumerate(input_lines):
        display_str = "*" * len(line) if hidden else line
                
        stdscr.addstr(input_start_y + i, x, "║ ", border_color)  # Left border
        stdscr.addstr(input_start_y + i, x + 2, display_str.ljust(box_width - 4), text_color)  # Input text
        stdscr.addstr(input_start_y + i, x + box_width - 2, " ║", border_color)  # Right border
        

    # Draw bottom border after the input area
    stdscr.addstr(input_start_y + len(input_lines), x, "╚" + "═" * (box_width - 2) + "╝", border_color)
    stdscr.refresh()
    
    return box_height

def get_user_input(stdscr, y, x, question, max_width, hidden=False):
    """
    Handles user input in an input box with auto-wrapping, dynamic box expansion, and proper border adjustment.
    """
    curses.echo()
    if hidden:
        curses.noecho()

    # Determine box width (including borders and padding)
    input_box_width = max(max_width + 4, 20)

    # Wrap the question text into multiple lines if needed
    question_lines = []
    words = question.split()
    current_line = ""
    for word in words:
        # Reserve space for the 2 spaces used for padding ("║ " and " ║")
        if len(current_line) + len(word) + (1 if current_line else 0) > input_box_width - 4:
            question_lines.append(current_line)
            current_line = word
        else:
            current_line = f"{current_line} {word}" if current_line else word
    if current_line:
        question_lines.append(current_line)

    input_str = ""
    previous_box_height = 20

    while True:
        # Auto-wrap the input string into lines of length max_width
        input_lines = [input_str[i:i+max_width] for i in range(0, len(input_str), max_width)]
        if not input_lines:
            input_lines = [""]

        # Compute new box height
        current_box_height = len(question_lines) + len(input_lines) + 2

        # Clear extra rows if the previous box was taller
        if previous_box_height > current_box_height:
            for row in range(y - 1 + current_box_height, y - 1 + previous_box_height):
                stdscr.addstr(row, x, " " * input_box_width, curses.color_pair(1))

        # Redraw the entire input box with updated content
        previous_box_height = draw_input_box(
            stdscr, y, x, question_lines, input_lines, input_box_width,
            curses.color_pair(3), curses.color_pair(1), hidden
        )

        # Calculate cursor position: end of the last input line
        cursor_line = len(input_lines) - 1
        cursor_col = len(input_lines[-1])
        # Move the cursor inside the input area (x + 2 to account for left border and padding)
        stdscr.move(y + len(question_lines) + cursor_line, x + 2 + cursor_col)
        stdscr.refresh()

        char = stdscr.getch()
        if char in [10, 13]:  # Enter key submits input
            break
        elif char in [127, curses.KEY_BACKSPACE]:  # Handle backspace
            if input_str:
                input_str = input_str[:-1]
        elif 32 <= char <= 126:  # Printable characters
            input_str += chr(char)

    curses.noecho()
    return input_str.strip()