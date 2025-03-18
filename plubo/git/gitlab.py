import requests
import curses
from plubo.settings.Config import Config

def validate_gitlab_token(token, gitlab_domain="gitlab.com"):
    """Check if GitLab token is valid before storing it."""
    headers = {"PRIVATE-TOKEN": token}
    url = f"https://{gitlab_domain}/api/v4/user"
    
    try:
        response = requests.get(url, headers=headers, timeout=5)  # Add a timeout to avoid long waits
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        return False
    
def fetch_gitlab_groups(token, gitlab_domain="gitlab.com"):
    """Fetch the GitLab groups of the authenticated user."""
    url = f"https://{gitlab_domain}/api/v4/groups"
    headers = {"PRIVATE-TOKEN": token}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            print(response.json())
            return response.json()  # List of groups
        else:
            print("ERROR")
            return []
    except Exception as e:
        return []

def ask_for_gitlab_namespace(stdscr, token, username, gitlab_domain="gitlab.com"):
    """Ask the user to select a GitLab namespace (personal or group)."""
    groups = fetch_gitlab_groups(token, gitlab_domain)

    # Create options list with namespace name and ID (Personal account has no ID)
    options = [{"name": f"Personal ({username})", "full_path": username, "id": None}]
    options.extend([{"name": group["full_path"], "full_path": group["full_path"], "id": group["id"]} for group in groups])
    
    selected = 0

    while True:
        stdscr.clear()
        stdscr.addstr(2, 2, "📂 Select GitLab Namespace")
        
        for i, option in enumerate(options):
            if i == selected:
                stdscr.addstr(4 + i, 4, f"> {option['name']} <", curses.A_BOLD)
            else:
                stdscr.addstr(4 + i, 4, option['name'])
        
        key = stdscr.getch()
        if key == curses.KEY_UP and selected > 0:
            selected -= 1
        elif key == curses.KEY_DOWN and selected < len(options) - 1:
            selected += 1
        elif key in (curses.KEY_ENTER, 10, 13):
            break
    
    # if selected == len(options) - 1:  # "Skip"
    #     return 

    # Return both namespace and its ID (None for personal)
    return options[selected]["full_path"], options[selected]["id"]

def get_custom_gitlab_domains():
    """Retrieve custom GitLab domains stored in Config."""
    all_sections = Config.sections()
    return [key for key in all_sections if "." in key]  # Subomains contain a dot

def create_gitlab_repo(namespace, namespace_id, token, plugin_name, gitlab_domain="gitlab.com"):
    """Create a new GitLab repository under the selected namespace (group or personal)."""
    url = f"https://{gitlab_domain}/api/v4/projects"
    headers = {"PRIVATE-TOKEN": token}
    
    data = {"name": plugin_name, "visibility": "public"}
    
    if namespace_id:  # Only send if it's a group
        data["namespace_id"] = namespace_id

    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 201:
        return f"git@{gitlab_domain}:{namespace}/{plugin_name}.git"
    else:
        raise Exception(f"GitLab repo creation failed: {response.json()}")
