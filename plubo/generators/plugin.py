import os
import json
import subprocess
import curses
import requests
from pathlib import Path
from plubo.utils import project
from plubo.settings.Config import Config

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

    # Return both namespace and its ID (None for personal)
    return options[selected]["full_path"], options[selected]["id"]

def get_custom_gitlab_domains():
    """Retrieve custom GitLab domains stored in Config."""
    all_sections = Config.sections()
    return [key for key in all_sections if "." in key]  # Domains usually contain a dot


def ask_for_repo_creation(stdscr, plugin_directory, plugin_name):
    """Ask the user if they want to create a repo on GitHub, GitLab, or a custom domain."""
    custom_domains = get_custom_gitlab_domains()
    options = ["GitHub", "GitLab"] + custom_domains + ["Skip"]
    
    selected = 0
    
    while True:
        stdscr.clear()
        stdscr.addstr(2, 2, "📂 Create Git Repository")
        
        for i, option in enumerate(options):
            if i == selected:
                stdscr.addstr(4 + i, 4, f"> {option} <", curses.A_BOLD)
            else:
                stdscr.addstr(4 + i, 4, option)
        
        key = stdscr.getch()
        if key == curses.KEY_UP and selected > 0:
            selected -= 1
        elif key == curses.KEY_DOWN and selected < len(options) - 1:
            selected += 1
        elif key in (curses.KEY_ENTER, 10, 13):
            break
    
    if selected == len(options) - 1:  # "Skip"
        return 
    
    platform = options[selected]
    stdscr.clear()
    
    # Retrieve credentials from Config
    username = Config.get(platform.lower(), "username")
    token = Config.get(platform.lower(), "token")

    # Ask for username only if missing
    if not username:
        curses.echo()
        stdscr.addstr(2, 2, f"👤 Enter your {platform} username:")
        stdscr.refresh()
        stdscr.move(4, 2)
        username = stdscr.getstr().decode("utf-8").strip()
        curses.noecho()
        Config.set(platform.lower(), "username", username)  # Save for future use

    # Ask for repo namespace (default to username)
    namespace_id = None
    if platform in ["GitLab"] + custom_domains:
        if platform == "GitLab":
            repo_namespace, namespace_id = ask_for_gitlab_namespace(stdscr, token, username)
        else:
            repo_namespace, namespace_id = ask_for_gitlab_namespace(stdscr, token, username, platform)
    else:
        repo_namespace = Config.get(platform.lower(), "repo_namespace", default=username)
    
        curses.echo()
        stdscr.addstr(6, 2, f"📂 Enter your repository namespace [{repo_namespace}]:")
        stdscr.refresh()
        stdscr.move(8, 2)
        namespace_input = stdscr.getstr().decode("utf-8").strip()
        curses.noecho()
        
        if namespace_input:
            repo_namespace = namespace_input
            Config.set(platform.lower(), "repo_namespace", repo_namespace)

    # Skip token prompt and use stored token
    if not token:
        stdscr.addstr(10, 2, f"❌ No {platform} token found in config. Please set it using pb-cli settings.")
        stdscr.refresh()
        stdscr.getch()
        return

    # Proceed with repo creation
    remote_url = setup_git_repository(stdscr, plugin_directory, plugin_name, platform, username, repo_namespace, namespace_id, token)

    if remote_url:
        stdscr.addstr(12, 2, f"✅ Repository created: {remote_url}")
    stdscr.addstr(14, 2, "Press any key to return to the main menu.")
    stdscr.refresh()
    stdscr.getch()


def create_github_repo(username, token, plugin_name, org_name=None):
    """Create a new GitHub repository under a user or organization."""
    if org_name:
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


def setup_git_repository(stdscr, plugin_directory, plugin_name, platform, username, repo_namespace, namespace_id, access_token):
    """Initialize Git repository, create a remote repository via API, and push to the selected platform using SSH."""
    stdscr.clear()
    stdscr.addstr(2, 2, "🛠️ Setting up Git repository...")
    stdscr.refresh()
    os.chdir(plugin_directory)
    
    subprocess.run(["git", "init"], check=True)
    subprocess.run(["git", "add", "-A"], check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], check=True)
    
    try:
        if platform == "GitHub":
            # Determine if namespace is an organization
            if repo_namespace != username:
                remote_url = create_github_repo(username, access_token, plugin_name, repo_namespace)
            else:
                remote_url = create_github_repo(username, access_token, plugin_name)
        elif platform == "GitLab":
            remote_url = create_gitlab_repo(repo_namespace, namespace_id, access_token, plugin_name)
        else:
            remote_url = create_gitlab_repo(repo_namespace, namespace_id, access_token, plugin_name, "gitlab.sirvelia.com")
    except Exception as e:
        stdscr.addstr(6, 2, f"❌ Error creating repository: {e}")
        stdscr.refresh()
        stdscr.getch()
        return None
    
    subprocess.run(["git", "remote", "add", "origin", remote_url], check=True)
    subprocess.run(["git", "branch", "-M", "main"], check=True)
    subprocess.run(["git", "push", "-u", "origin", "main"], check=True)
    
    return remote_url

def create_project(stdscr):
    """Main function to handle renaming within the curses menu."""
    wp_root = project.detect_wp_root()
    if not wp_root:
        stdscr.addstr(4, 2, "❌ No WordPress installation detected. Aborting.")
        stdscr.refresh()
        stdscr.getch()
        return
    
    curses.curs_set(1)  # Show cursor for input
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Message color
    
    stdscr.nodelay(0)
    stdscr.clear()
    stdscr.addstr(2, 2, "➕ Create Plugin")
    stdscr.refresh()
    
    stdscr.addstr(6, 2, "Enter the new plugin name (leave empty to cancel):")
    stdscr.refresh()
    
    # Ensure proper user input handling
    curses.echo()
    stdscr.move(8, 2)
    curses.flushinp()
    new_name = stdscr.getstr().decode("utf-8").strip()
    curses.noecho()
    
    # If the user presses enter without input, do nothing
    if not new_name:
        stdscr.addstr(10, 2, "⚠️ Creation cancelled. Press any key to return.")
        stdscr.refresh()
        stdscr.getch()
        curses.curs_set(0)  # Hide cursor
        return
    
    stdscr.clear()
    stdscr.addstr(2, 2, f"Creating plugin {new_name}... ⏳")
    stdscr.refresh()
    create_plugin(new_name, wp_root)
    stdscr.clear()
    stdscr.refresh()
    
    stdscr.addstr(4, 2, "✅ Plugin created successfully!")
    stdscr.addstr(6, 2, "Press any key to return to the main menu.")
    stdscr.refresh()
    stdscr.getch()
    curses.curs_set(0)  # Hide cursor

def rename_project(stdscr):
    """Main function to handle renaming within the curses menu."""
    curses.curs_set(1)  # Show cursor for input
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Message color
    
    stdscr.nodelay(0)
    stdscr.clear()
    stdscr.addstr(2, 2, "🔄 Rename Plugin")
    stdscr.refresh()
    
    old_name = project.detect_plugin_name()
    stdscr.addstr(6, 2, f"Current plugin name detected: ")
    stdscr.addstr(old_name, curses.color_pair(3))
    stdscr.addstr(8, 2, "Enter a new plugin name (leave empty to cancel):")
    stdscr.refresh()
    
    # Ensure proper user input handling
    curses.echo()
    stdscr.move(10, 2)
    curses.flushinp()
    new_name = stdscr.getstr().decode("utf-8").strip()
    curses.noecho()
    
    # If the user presses enter without input, do nothing
    if not new_name:
        stdscr.addstr(12, 2, "⚠️ Rename cancelled. Press any key to return.")
        stdscr.refresh()
        stdscr.getch()
        curses.curs_set(0)  # Hide cursor
        return
    
    stdscr.clear()
    stdscr.addstr(2, 2, f"Renaming {old_name} to {new_name}... ⏳")
    stdscr.refresh()
    rename_plugin(old_name, new_name)
    
    stdscr.addstr(4, 2, "✅ Plugin renamed successfully!")
    stdscr.addstr(6, 2, "Press any key to return to the main menu.")
    stdscr.refresh()
    stdscr.getch()
    curses.curs_set(0)  # Hide cursor

def init_repo(stdscr):
    """Init repo for the plugin."""
    wp_root = project.detect_wp_root()
    if not wp_root:
        stdscr.addstr(4, 2, "❌ No WordPress installation detected. Aborting.")
        stdscr.refresh()
        stdscr.getch()
        curses.curs_set(0)  # Hide cursor
        return
    
    plugin_name = project.detect_plugin_name()
    if not plugin_name:
        stdscr.addstr(4, 2, "❌ No plugin detected. Aborting.")
        stdscr.refresh()
        stdscr.getch()
        curses.curs_set(0)  # Hide cursor
        return
    
    plugin_name = plugin_name.lower().replace(" ", "-")
    plugins_directory = wp_root / "wp-content/plugins"
    plugin_directory = plugins_directory / plugin_name
    
    ask_for_repo_creation(stdscr, plugin_directory, plugin_name)
    curses.curs_set(0)  # Hide cursor
        
def create_plugin(new_name, wp_root):
    """Create the new plugin using Plubo Boilerplate."""
    plugin_name = new_name.lower().replace(" ", "-")
    plugins_directory = wp_root / "wp-content/plugins"
    plugin_directory = plugins_directory / plugin_name
    
    curses.endwin()  # Exit curses mode so the user can interact normally
    print(f"\n⏳ Creating plugin {new_name} in {plugin_directory}...\n")  # Inform user
    
    try:       
        command = ["lando", "composer", "create-project", "joanrodas/plubo", plugin_name] if project.is_lando_project() else ["composer", "create-project", "joanrodas/plubo", plugin_name]
        subprocess.run(command, check=True, cwd=str(plugins_directory))
        
        os.chdir(plugin_directory)  # Change directory to the newly created plugin folder
        rename_plugin("plugin-placeholder", new_name)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during plugin creation: {e}")
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    finally:
        stdscr = curses.initscr()
        ask_for_repo_creation(stdscr, plugin_directory, plugin_name)

def rename_plugin(old_name, new_name):
    """Replaces the plugin name in all relevant files with correct casing."""
    plugin_root = Path(os.getcwd())  # Get current plugin directory
    parent_directory = plugin_root.parent  # The directory containing the plugin folder
    
    casing_variants = {
        old_name.lower().replace("_", "-"): new_name.lower().replace("_", "-"),
        old_name.upper().replace("-", "_"): new_name.upper().replace("-", "_"),
        old_name.title().replace("-", ""): new_name.title().replace("-", ""),
        old_name.upper().replace("-", "").replace("_", ""): new_name.upper().replace("-", "").replace("_", "-")
    }
    
    # Update PHP files
    for file in plugin_root.rglob("*.php"):
        replace_in_file(file, casing_variants)
    
    # Update JSON files (composer.json, package.json)
    for json_file in ["composer.json", "package.json"]:
        json_path = plugin_root / json_file
        if json_path.exists():
            replace_in_json(json_path, casing_variants)
    
    # Update .pot file
    pot_file = plugin_root / "languages" / f"{old_name.lower()}.pot"
    if pot_file.exists():
        new_pot_file = plugin_root / "languages" / f"{new_name.lower()}.pot"
        replace_in_file(pot_file, casing_variants)
        pot_file.rename(new_pot_file)
    
    # Rename main plugin file
    old_plugin_file = plugin_root / f"{old_name.lower()}.php"
    new_plugin_file = plugin_root / f"{new_name.lower()}.php"
    if old_plugin_file.exists():
        old_plugin_file.rename(new_plugin_file)
    
    # Rename plugin folder
    new_plugin_folder = parent_directory / new_name.lower().replace(" ", "-")  # Normalize new folder name
    if plugin_root.exists():
        plugin_root.rename(new_plugin_folder)
    
    #TODO: MAYBE COMPILE assets AND activate plugin if lando is present
    
    return new_plugin_folder

def replace_in_file(file_path, replacements):
    """Replaces occurrences of old names with new ones in a file."""
    with file_path.open("r", encoding="utf-8") as f:
        content = f.read()
    
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    with file_path.open("w", encoding="utf-8") as f:
        f.write(content)

def replace_in_json(file_path, replacements):
    """Updates JSON values containing the old name."""
    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    
    def recursive_replace(obj):
        if isinstance(obj, str):
            for old, new in replacements.items():
                obj = obj.replace(old, new)
            return obj
        elif isinstance(obj, dict):
            return {key: recursive_replace(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [recursive_replace(item) for item in obj]
        return obj
    
    updated_data = recursive_replace(data)
    
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(updated_data, f, indent=4)
