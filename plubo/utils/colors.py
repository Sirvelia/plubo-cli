import curses
import re

# Define RGB mappings for terminals that support color changes
CUSTOM_RGB_COLORS = {
    '30': (20, 20, 20),      # Dark Gray (Better Black)
    '31': (200, 40, 40),     # Vibrant Red
    '32': (40, 200, 40),     # Bright Green
    '33': (255, 200, 50),    # Golden Yellow
    '34': (50, 120, 255),    # Deep Blue
    '35': (200, 50, 200),    # Electric Purple
    '36': (50, 200, 200),    # Neon Cyan
    '37': (230, 230, 230),   # Bright White
    '90': (100, 100, 100),   # Gray (Bright Black)
    '91': (255, 80, 80),     # Bright Red
    '92': (80, 255, 80),     # Bright Green
    '93': (255, 230, 80),    # Bright Yellow
    '94': (120, 170, 255),   # Soft Blue
    '95': (230, 120, 255),   # Light Magenta
    '96': (120, 255, 255),   # Light Cyan
    '97': (255, 255, 255)    # True White
}

# Regex pattern to match ANSI escape sequences
ANSI_PATTERN = re.compile(r'\x1B\[(\d+)m')

def init_colors():
    curses.start_color()

    if curses.can_change_color():
        curses.init_color(1, 15 * 4, 56 * 4, 15 * 4)  # Dark Green (Text)
        # curses.init_color(2, 155 * 4, 188 * 4, 15 * 4)  # Light Green (Background)
        curses.init_color(2, 902, 906, 784) # BACKGROUND
        curses.init_color(3, 48 * 4, 98 * 4, 48 * 4)  # Medium Green (Borders)
        curses.init_color(4, 863, 78, 235) # RED
        curses.init_color(5, 196, 322, 659)

        # Set color pairs
        curses.init_pair(1, 1, 2)  # Normal Text (Dark Green on Light Green)
        curses.init_pair(2, 5, 2)  # Highlighted Option
        curses.init_pair(3, 3, 2)  # Titles & Borders
        curses.init_pair(4, 4, 2)  # Error messages
        
        pair_number = 10  # Start from 10 to avoid conflicts

        for ansi_code, (r, g, b) in CUSTOM_RGB_COLORS.items():
            if pair_number < curses.COLOR_PAIRS:
                # Scale RGB (0-255) to curses range (0-1000)
                r_scaled = int((r / 255) * 1000)
                g_scaled = int((g / 255) * 1000)
                b_scaled = int((b / 255) * 1000)

                curses.init_color(pair_number, r_scaled, g_scaled, b_scaled)
                curses.init_pair(pair_number, pair_number, curses.COLOR_BLACK)

                # Assign the color pair to ANSI map
                CUSTOM_RGB_COLORS[ansi_code] = curses.color_pair(pair_number)
                pair_number += 1
    else:
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_WHITE)  # Normal text
        curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_WHITE)  # Highlighted text
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Titles & Borders
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_WHITE)  # Error messages
        
        # Standard curses color fallback
        FALLBACK_ANSI_COLORS = {
            '30': curses.COLOR_BLACK, '31': curses.COLOR_RED, '32': curses.COLOR_GREEN,
            '33': curses.COLOR_YELLOW, '34': curses.COLOR_BLUE, '35': curses.COLOR_MAGENTA,
            '36': curses.COLOR_CYAN, '37': curses.COLOR_WHITE,
            '90': curses.COLOR_BLACK, '91': curses.COLOR_RED, '92': curses.COLOR_GREEN,
            '93': curses.COLOR_YELLOW, '94': curses.COLOR_BLUE, '95': curses.COLOR_MAGENTA,
            '96': curses.COLOR_CYAN, '97': curses.COLOR_WHITE
        }

        pair_number = 10
        for ansi_code, color in FALLBACK_ANSI_COLORS.items():
            if pair_number < curses.COLOR_PAIRS:
                curses.init_pair(pair_number, color, curses.COLOR_BLACK)
                CUSTOM_RGB_COLORS[ansi_code] = curses.color_pair(pair_number)
                pair_number += 1

    # Handle ANSI reset (0)
    CUSTOM_RGB_COLORS['0'] = curses.color_pair(0)  # Default terminal colors

def parse_ansi_colors(text):
    """
    Parses ANSI color sequences in a line and returns a list of (text_segment, curses_color_pair).
    Handles multiple colors in a single line.
    """
    segments = []
    last_color = curses.color_pair(0)  # Default terminal color
    parts = ANSI_PATTERN.split(text)

    for part in parts:
        if part.isdigit():  # If it's a color code
            ansi_code = part
            if ansi_code == '0':  # Reset to default
                last_color = curses.color_pair(0)
            else:
                last_color = CUSTOM_RGB_COLORS.get(ansi_code, last_color)  # Keep last color if unknown
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