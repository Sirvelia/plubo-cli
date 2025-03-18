import curses
import time
from plubo.settings.Config import Config
from plubo.git.github import validate_github_token
from plubo.git.gitlab import validate_gitlab_token
from plubo.utils import interface

def get_menu_options():
    """Dynamically retrieves menu options, including custom domains."""
    custom_domains = get_custom_domains()
    return [
        "Configure GitHub",
        "Configure GitLab",
        "Add Custom Domain",
        *custom_domains,  # Dynamically append custom domains
        "BACK"
    ]

def draw_settings_menu(stdscr):
    """Displays the settings menu with dynamic custom domains."""
    curses.curs_set(0)  # Hide cursor   
    stdscr.keypad(True)
    
    current_row = 0
    height, width = stdscr.getmaxyx()

    while True:        
        menu_options = get_menu_options()  # Refresh options dynamically
        selected_row, current_row = interface.render_menu(stdscr, menu_options, current_row, height, width)
        
        if selected_row is not None:
            if handle_settings_selection(stdscr, selected_row, menu_options):
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
    elif selection == "BACK":
        return True
    else:
        modify_custom_domain(stdscr, selection)  # Handle existing domains
    
    return False

def configure_service(stdscr, service):
    """Prompts the user to configure GitHub or GitLab credentials."""
    stdscr.erase()
    interface.draw_background(stdscr, f"Configure {service}")
        
    box_x = (stdscr.getmaxyx()[1] - 50) // 2  # Center box horizontally
    y_start = 10  # Position inputs inside the box
    
    username = interface.get_user_input(stdscr, y_start, box_x, "Enter your username:", 40)
    token = interface.get_user_input(stdscr, y_start, box_x, "Enter your token:", 40, hidden=True)
    
    # Validate Credentials
    service_key = service.lower()
    is_valid = validate_github_token(token) if service_key == 'github' else validate_gitlab_token(token)
    
    if is_valid:
        Config.set(service_key, "username", username)
        Config.set(service_key, "token", token)
        interface.display_message(stdscr, f"✅ {service} credentials saved!", "success")
    else:
        interface.display_message(stdscr, f"❌ {service} credentials not saved! Invalid token.", "error")

    stdscr.getch()  # Waits for a key press before returning

def add_custom_domain(stdscr):
    """Prompts the user to add a new custom domain."""
    stdscr.erase()
    interface.draw_background(stdscr, "Add Custom Domain")

    box_x = (stdscr.getmaxyx()[1] - 50) // 2
    y_start = 10

    domain = interface.get_user_input(stdscr, y_start, box_x, "Enter your custom domain:", 40)
    username = interface.get_user_input(stdscr, y_start + 4, box_x, "Enter your username:", 40)
    token = interface.get_user_input(stdscr, y_start + 8, box_x, "Enter your token:", 40, hidden=True)

    try:
        if token and validate_gitlab_token(token, domain):
            Config.set(domain, "username", username)
            Config.set(domain, "token", token)
            interface.display_message(stdscr, f"✅ Custom domain {domain} saved!", "success")
        else:
            interface.display_message(stdscr, f"❌ Custom domain {domain} not saved! Invalid token.", "error")
    except curses.error:
        interface.display_message(stdscr, f"❌ Custom domain not saved! Invalid token.", "error")
        pass
    
    stdscr.getch()  # Waits for a key press before returning

def modify_custom_domain(stdscr, domain):
    """Allows modifying the username and token for an existing custom domain."""
    stdscr.erase()
    interface.draw_background(stdscr, f"Modify domain {domain}")
    
    # Retrieve current credentials
    current_username = Config.get(domain, "username", "")
    
    box_x = (stdscr.getmaxyx()[1] - 50) // 2
    y_start = 10

    new_username = interface.get_user_input(stdscr, y_start, box_x, f"New username ({current_username}):", 40)
    new_token = interface.get_user_input(stdscr, y_start + 4, box_x, "Enter your token:", 40, hidden=True)    
        
    if new_token and validate_gitlab_token(new_token, domain):
        if new_username:
            Config.set(domain, "username", new_username)
        
        Config.set(domain, "token", new_token)
        interface.display_message(stdscr, f"✅ Credentials for {domain} updated!", "success")
    else:
        interface.display_message(stdscr, f"❌ Credentials for {domain} not updated! Token is not valid.", "error")
    
    stdscr.getch()  # Waits for a key press before returning

def get_custom_domains():
    """Retrieves a list of all stored custom domains."""
    all_sections = Config.sections()
    return [key for key in all_sections if "." in key]  # Assuming domain keys contain a dot

def pb_cli_settings():
    """Launches the settings menu."""
    curses.wrapper(draw_settings_menu)

if __name__ == "__main__":
    pb_cli_settings()
