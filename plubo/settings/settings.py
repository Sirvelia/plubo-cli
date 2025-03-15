import curses
import time
from plubo.settings.Config import Config

def get_menu_options():
    """Dynamically retrieves menu options, including custom domains."""
    custom_domains = get_custom_domains()
    return [
        "Configure GitHub",
        "Configure GitLab",
        "Add Custom Domain",
        *custom_domains,  # Dynamically append custom domains
        "Back"
    ]

def draw_settings_menu(stdscr):
    """Displays the settings menu with dynamic custom domains."""
    curses.curs_set(0)  # Hide cursor
    stdscr.nodelay(0)
    stdscr.timeout(100)
    
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Highlighted option
    curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)  # Settings Header
    
    stdscr.keypad(True)
    current_row = 0

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        options = get_menu_options()  # Refresh menu options dynamically
        title = "PB-CLI Settings"
        stdscr.addstr(2, (width - len(title)) // 2, title, curses.color_pair(2) | curses.A_BOLD)
        
        start_y = 4
        for idx, option in enumerate(options):
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
        elif key == curses.KEY_DOWN and current_row < len(options) - 1:
            current_row += 1
        elif key in [curses.KEY_ENTER, 10, 13]:
            if handle_settings_selection(stdscr, current_row, options):
                return  # Exit settings menu

def handle_settings_selection(stdscr, current_row, options):
    """Handles the settings menu selection."""
    selection = options[current_row]
    
    if selection == "Configure GitHub":
        configure_service(stdscr, "GitHub")
    elif selection == "Configure GitLab":
        configure_service(stdscr, "GitLab")
    elif selection == "Add Custom Domain":
        add_custom_domain(stdscr)
    elif selection == "Back":
        return True
    else:
        modify_custom_domain(stdscr, selection)  # Handle existing domains
    
    return False

def configure_service(stdscr, service):
    """Prompts the user to configure GitHub or GitLab credentials."""
    stdscr.clear()
    height, width = stdscr.getmaxyx()
    
    stdscr.addstr(2, (width - len(f"Configure {service}")) // 2, f"Configure {service}", curses.A_BOLD)
    stdscr.addstr(4, 2, "Enter your username:")
    username = get_user_input(stdscr, 5, 2, width - 4)
    
    stdscr.addstr(7, 2, "Enter your token:")
    token = get_user_input(stdscr, 8, 2, width - 4, hidden=True)
    
    # Save credentials
    Config.set(service.lower(), "username", username)
    Config.set(service.lower(), "token", token)
    
    stdscr.addstr(10, 2, f"✅ {service} credentials saved!", curses.color_pair(2))
    stdscr.refresh()
    time.sleep(1)

def add_custom_domain(stdscr):
    """Prompts the user to add a new custom domain."""
    stdscr.clear()
    height, width = stdscr.getmaxyx()
    
    stdscr.addstr(2, (width - len("Add Custom Domain")) // 2, "Add Custom Domain", curses.A_BOLD)
    
    stdscr.addstr(4, 2, "Enter your custom domain:")
    domain = get_user_input(stdscr, 5, 2, width - 4)

    stdscr.addstr(7, 2, "Enter your username:")
    username = get_user_input(stdscr, 8, 2, width - 4)

    stdscr.addstr(10, 2, "Enter your password:")
    password = get_user_input(stdscr, 11, 2, width - 4, hidden=True)
    
    # Save domain credentials
    Config.set(domain, "username", username)
    Config.set(domain, "password", password)
    
    stdscr.addstr(13, 2, f"✅ Custom domain {domain} saved!", curses.color_pair(2))
    stdscr.refresh()
    time.sleep(1)

def modify_custom_domain(stdscr, domain):
    """Allows modifying the username and password for an existing custom domain."""
    stdscr.clear()
    height, width = stdscr.getmaxyx()
    
    stdscr.addstr(2, (width - len(f"Modify {domain}")) // 2, f"Modify {domain}", curses.A_BOLD)
    
    # Retrieve current credentials
    current_username = Config.get(domain, "username", "")
    current_password = Config.get(domain, "password", "")
    
    stdscr.addstr(4, 2, f"Current username: {current_username}")
    stdscr.addstr(6, 2, "Enter new username (leave empty to keep current):")
    new_username = get_user_input(stdscr, 7, 2, width - 4)
    
    stdscr.addstr(9, 2, "Enter new password (leave empty to keep current):")
    new_password = get_user_input(stdscr, 10, 2, width - 4, hidden=True)
    
    # Update credentials only if new values were entered
    if new_username:
        Config.set(domain, "username", new_username)
    if new_password:
        Config.set(domain, "password", new_password)
    
    stdscr.addstr(12, 2, f"✅ Credentials for {domain} updated!", curses.color_pair(2))
    stdscr.refresh()
    time.sleep(1)

def get_custom_domains():
    """Retrieves a list of all stored custom domains."""
    all_sections = Config.sections()
    return [key for key in all_sections if "." in key]  # Assuming domain keys contain a dot

def get_user_input(stdscr, y, x, max_width, hidden=False):
    """Handles user input in the terminal with optional hidden mode."""
    curses.echo()
    if hidden:
        curses.noecho()
    
    stdscr.move(y, x)
    stdscr.clrtoeol()
    
    input_str = ""
    while True:
        char = stdscr.getch()

        if char in [10, 13]:  # Enter key
            break
        elif char in [127, curses.KEY_BACKSPACE]:  # Backspace key
            if input_str:
                input_str = input_str[:-1]
                stdscr.move(y, x + len(input_str))
                stdscr.clrtoeol()
        elif 32 <= char <= 126:  # Printable characters
            if len(input_str) < max_width - x - 1:
                input_str += chr(char)
        
        if not hidden:
            stdscr.addstr(y, x, input_str)
        else:
            stdscr.addstr(y, x, "*" * len(input_str))
        stdscr.refresh()
    
    curses.noecho()
    return input_str.strip()

def pb_cli_settings():
    """Launches the settings menu."""
    curses.wrapper(draw_settings_menu)

if __name__ == "__main__":
    pb_cli_settings()
