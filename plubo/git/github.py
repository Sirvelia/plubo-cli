import requests
import curses

def validate_github_token(token):
    """Check if GitHub token is valid before storing it."""
    headers = {"Authorization": f"token {token}"}
    response = requests.get("https://api.github.com/user", headers=headers)
    return response.status_code == 200

def fetch_github_organizations(token):
    """Fetch the GitHub organizations the authenticated user belongs to."""
    url = "https://api.github.com/user/orgs"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()  # List of organizations
        else:
            return []
    except Exception as e:
        return []
    
def ask_for_github_namespace(stdscr, token, username):
    """Ask the user to select a GitHub namespace (personal or organization)."""
    orgs = fetch_github_organizations(token)

    # Create options list with personal namespace first
    options = [{"name": f"Personal ({username})", "full_path": username}]
    options.extend([{"name": org["login"], "full_path": org["login"]} for org in orgs])

    selected = 0

    while True:
        stdscr.clear()
        stdscr.addstr(2, 2, "📂 Select GitHub Namespace")
        
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

    return options[selected]["full_path"]

def create_github_repo(username, token, plugin_name, org_name=None):
    """Create a new GitHub repository under a user or organization."""
    if org_name and org_name != username:
        url = f"https://api.github.com/orgs/{org_name}/repos"  # Create repo in org
    else:
        url = "https://api.github.com/user/repos"  # Create repo in user namespace

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    data = {"name": plugin_name, "private": True}

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        repo_owner = org_name if org_name else username
        return f"git@github.com:{repo_owner}/{plugin_name}.git"
    else:
        raise Exception(f"GitHub repo creation failed: {response.json()}")