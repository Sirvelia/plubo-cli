import os
import json
import subprocess
import curses
import requests
from pathlib import Path
from plubo.utils import project, interface
from plubo.settings.Config import Config
from plubo.git.github import ask_for_github_namespace, create_github_repo
from plubo.git.gitlab import ask_for_gitlab_namespace, create_gitlab_repo, get_custom_gitlab_domains
from plubo.git.git_utils import initialize_git_repository, set_remote_and_push

def handle_repo_selection(stdscr, current_row, menu_options, plugin_directory, plugin_name, custom_domains):
    """Handle the selection of a menu option"""
    if current_row < 0 or current_row >= len(menu_options):
        return False  # Invalid selection
    
    if current_row == len(menu_options) - 1:  # "Skip"
        return True

    # Retrieve credentials from Config
    platform = menu_options[current_row]
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
    if platform in ["GITLAB"] + custom_domains:
        if platform == "GITHUB":
            repo_namespace, namespace_id = ask_for_gitlab_namespace(stdscr, token, username)
        else:
            repo_namespace, namespace_id = ask_for_gitlab_namespace(stdscr, token, username, platform)
    else:
        repo_namespace = ask_for_github_namespace(stdscr, token, username)
    
        curses.echo()
        stdscr.addstr(6, 2, f"📂 Repository namespace [{repo_namespace}]:")
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
    
    
def ask_for_repo_creation(stdscr, plugin_directory, plugin_name):
    """Ask the user if they want to create a repo on GitHub, GitLab, or a custom domain."""
    custom_domains = get_custom_gitlab_domains()
    menu_options = ["GITHUB", "GITLAB"] + custom_domains + ["RETURN"]
    
    current_row = 0
    height, width = stdscr.getmaxyx()
    while True:
        selected_row, current_row = interface.render_menu(stdscr, menu_options, current_row, height, width)
        if selected_row is not None:
            if handle_repo_selection(stdscr, selected_row, menu_options, plugin_directory, plugin_name, custom_domains):
                return # Exit the CLI if handle_selection returns True
    

def setup_git_repository(stdscr, plugin_directory, plugin_name, platform, username, repo_namespace, namespace_id, access_token):
    """Initialize Git repository, create a remote repository via API, and push to the selected platform using SSH."""
    stdscr.clear()
    stdscr.addstr(2, 2, "🛠️ Setting up Git repository...")
    stdscr.refresh()
    
    try:
        initialize_git_repository(plugin_directory)
        
        if platform == "GITHUB":
            remote_url = create_github_repo(username, access_token, plugin_name, repo_namespace)
        elif platform == "GITLAB":
            remote_url = create_gitlab_repo(repo_namespace, namespace_id, access_token, plugin_name)
        else:
            remote_url = create_gitlab_repo(repo_namespace, namespace_id, access_token, plugin_name, platform)
        
        set_remote_and_push(remote_url, plugin_directory)
    except Exception as e:
        stdscr.addstr(6, 2, f"❌ Error creating repository: {e}")
        stdscr.refresh()
        stdscr.getch()
        return None
    
    return remote_url

def create_project(stdscr):
    """Main function to handle renaming within the curses menu."""
    stdscr.nodelay(0)
    interface.draw_background(stdscr, "➕ Create Plugin")
    
    wp_root = project.detect_wp_root()
    if not wp_root:
        interface.display_message(stdscr, "⚠️ No WordPress installation detected. Aborting.", "error", 4)
        stdscr.getch()
        return
    
    box_x = (stdscr.getmaxyx()[1] - 50) // 2  # Center box horizontally
    y_start = 8  # Position inputs inside the box
    
    new_name = interface.get_user_input(stdscr, y_start, box_x, "Plugin name (empty to cancel):", 40)
    
    if not new_name:
        interface.display_message(stdscr, "⚠️ Creation cancelled.", "error", 15)
    else:
        interface.display_message(stdscr, f"Creating plugin {new_name}... ⏳", "info", 15)
        create_plugin(new_name, wp_root)
        interface.display_message(stdscr, "✅ Plugin created successfully!", "success", 16)
    
    stdscr.getch()  # Wait for user input before returning

def rename_project(stdscr):
    """Main function to handle renaming within the curses menu."""
    stdscr.nodelay(0)
    interface.draw_background(stdscr, "🔄 Rename Plugin")
    
    box_x = (stdscr.getmaxyx()[1] - 50) // 2  # Center box horizontally
    y_start = 8  # Position inputs inside the box
    
    old_name = project.detect_plugin_name()
    new_name = interface.get_user_input(stdscr, y_start, box_x, "Plugin name (empty to cancel):", 40)
    
    if not new_name:
        interface.display_message(stdscr, "⚠️ Rename cancelled.", "error", 15)
    else:
        interface.display_message(stdscr, f"Renaming {old_name} to {new_name}... ⏳", "info", 15)
        rename_plugin(old_name, new_name)
        interface.display_message(stdscr, "✅ Plugin renamed successfully!", "success", 16)
    
    stdscr.getch()  # Wait for user input before returning

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
