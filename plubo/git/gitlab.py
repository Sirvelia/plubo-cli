import requests
import curses
from plubo.settings.Config import Config
from plubo.utils import interface

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
            return response.json()  # List of groups
        else:
            return []
    except Exception as e:
        return []

def ask_for_gitlab_namespace(stdscr, token, username, gitlab_domain="gitlab.com"):
    """Ask the user to select a GitLab namespace (personal or group)."""
    groups = fetch_gitlab_groups(token, gitlab_domain)

    # Create options list with namespace name and ID (Personal account has no ID)
    options = [{"name": f"Personal ({username})", "full_path": username, "id": None}]
    options.extend([{"name": group["full_path"], "full_path": group["full_path"], "id": group["id"]} for group in groups])
    
    option_names = [opt["name"] for opt in options]  # Extract only names
    option_names.append("BACK")
    
    current_row = 0
    height, width = stdscr.getmaxyx()
    while True:
        selected_row, current_row = interface.render_menu(stdscr, option_names, current_row, height, width)
        if selected_row == len(options) - 1:  # "Skip"
            return False
    
        if selected_row is not None:
            return options[selected_row]["full_path"]

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
