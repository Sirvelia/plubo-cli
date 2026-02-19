import os
import json
import re
from pathlib import Path
import fnmatch
from plubo.utils import project, interface, colors
from plubo.settings.Config import Config
from plubo.git.github import ask_for_github_namespace, create_github_repo, create_github_release
from plubo.git.gitlab import ask_for_gitlab_namespace, create_gitlab_repo, get_custom_gitlab_domains
from plubo.git.git_utils import initialize_git_repository, set_remote_and_push, get_git_remote_repo, clear_git_lock

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

    # Skip token prompt and use stored token
    if not token:
        stdscr.addstr(10, 2, f"❌ No {platform} token found in config. Please set it using pb-cli settings.")
        stdscr.refresh()
        stdscr.getch()
        return
    
    # Ask for username only if missing
    if not username:
        stdscr.addstr(10, 2, f"❌ No {platform} username found in config. Please set it using pb-cli settings.")
        stdscr.refresh()
        stdscr.getch()
        return

    # Ask for repo namespace (default to username)
    namespace_id = None
    if platform in ["GITLAB"] + custom_domains:
        if platform == "GITLAB":
            repo_namespace, namespace_id = ask_for_gitlab_namespace(stdscr, token, username)
        else:
            repo_namespace, namespace_id = ask_for_gitlab_namespace(stdscr, token, username, platform)
    else:
        repo_namespace = ask_for_github_namespace(stdscr, token, username)
    
    if not repo_namespace:
        return False


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
        create_plugin(stdscr, new_name, wp_root)
    
    stdscr.getch()  # Wait for user input before returning

def rename_project(stdscr):
    """Main function to handle renaming within the curses menu."""
    stdscr.nodelay(0)
    interface.draw_background(stdscr, "🔄 Rename Plugin")
    
    box_x = (stdscr.getmaxyx()[1] - 50) // 2  # Center box horizontally
    y_start = 8  # Position inputs inside the box
    
    wp_root = project.detect_wp_root()
    if not wp_root:
        interface.display_message(stdscr, "❌ No WordPress installation detected. Aborting.", "error", 15)
        stdscr.getch() 
        return
    
    old_name = project.detect_plugin_name()
    new_name = interface.get_user_input(stdscr, y_start, box_x, "Plugin name (empty to cancel):", 40)
    
    plugins_directory = wp_root / "wp-content/plugins"
    plugin_directory = plugins_directory / old_name
    
    if not new_name:
        interface.display_message(stdscr, "⚠️ Rename cancelled.", "error", 15)
    else:
        interface.display_message(stdscr, f"Renaming {old_name} to {new_name}... ⏳", "info", 15)
        rename_plugin(old_name, new_name, plugin_directory)
        interface.display_message(stdscr, "✅ Plugin renamed successfully!", "success", 16)
    
    stdscr.getch()  # Wait for user input before returning

def init_repo(stdscr):
    """Init repo for the plugin."""
    wp_root = project.detect_wp_root()
    if not wp_root:
        interface.display_message(stdscr, "❌ No WordPress installation detected. Aborting.", "error", 15)
        return
    
    plugin_name = project.detect_plugin_name()
    if not plugin_name:
        interface.display_message(stdscr, "❌ No plugin detected. Aborting.", "error", 15)
        return
    
    plugin_name = plugin_name.lower().replace(" ", "-")
    plugins_directory = wp_root / "wp-content/plugins"
    plugin_directory = plugins_directory / plugin_name
    
    ask_for_repo_creation(stdscr, plugin_directory, plugin_name)

def create_plugin(stdscr, new_name, wp_root):
    """Install a specific Composer dependency, handling Lando projects."""
    if not new_name or not wp_root:
        return  # Do nothing

    plugin_name = new_name.lower().replace(" ", "-")
    plugins_directory = wp_root / "wp-content/plugins"
    plugin_directory = plugins_directory / plugin_name

    stdscr.clear()
    interface.draw_background(stdscr, f"⏳ Creating plugin {plugin_name}...")
    
    height, width = stdscr.getmaxyx()

    try:       
        command = ["lando", "composer", "create-project", "joanrodas/plubo", plugin_name] if project.is_lando_project() else ["composer", "create-project", "joanrodas/plubo", plugin_name]
        
        if project.run_command(command, plugins_directory, stdscr):
            interface.display_message(stdscr, f"✅ Successfully created {plugin_name}", "success", height - 3)
            rename_plugin("plugin-placeholder", new_name, plugin_directory)
            # os.chdir(plugin_directory)  # Change directory to the newly created plugin folder
            stdscr.clear()
            activate_plugin(stdscr, plugin_name, plugin_directory)
            ask_for_repo_creation(stdscr, plugin_directory, plugin_name)
        else:
            interface.display_message(stdscr, f"❌ Creation failed for {plugin_name}", "error", height - 3)
        
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    
    stdscr.refresh()

    # **Wait for user input before returning**
    stdscr.getch()  # Wait user input
            

def rename_plugin(old_name, new_name, plugin_root= Path(os.getcwd())):
    """Replaces the plugin name in all relevant files with correct casing."""
    parent_directory = plugin_root.parent  # The directory containing the plugin folder
    
    casing_variants = {
        old_name.lower().replace("_", "-"): new_name.lower().replace("_", "-"),
        old_name.upper().replace("-", "_"): new_name.upper().replace("-", "_"),
        old_name.title().replace("-", ""): new_name.title().replace("-", ""),
        old_name.upper().replace("-", "").replace("_", ""): new_name.upper().replace("-", "").replace("_", "-")
    }
    
    # Update PHP files
    for file in iter_files(plugin_root, "*.php"):
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
        
def iter_files(root, pattern):
    for dirpath, dirnames, filenames in os.walk(root):
        # Remove vendor and node_modules directories from the search
        dirnames[:] = [d for d in dirnames if d not in ("vendor", "node_modules")]
        for filename in filenames:
            if fnmatch.fnmatch(filename, pattern):
                yield Path(dirpath) / filename
                
def replace_in_file(file_path, replacements):
    """Replaces occurrences of old names with new ones in a file."""
    # Skip if the path is not a file
    if not file_path.is_file():
        return

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
    
    def replace_string(text):
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text

    def recursive_replace(obj):
        if isinstance(obj, str):
            return replace_string(obj)
        elif isinstance(obj, dict):
            return {replace_string(key): recursive_replace(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [recursive_replace(item) for item in obj]
        return obj
    
    updated_data = recursive_replace(data)
    
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(updated_data, f, indent=4)


def activate_plugin(stdscr, plugin_name, plugin_directory):
    """Runs composer update, yarn build, and activates the plugin."""
    
    stdscr.clear()
    interface.draw_background(stdscr, f"🚀 Activating Plugin: {plugin_name}")
    
    height, width = stdscr.getmaxyx()
    
    commands = [
        (["lando", "composer", "update"] if project.is_lando_project() else ["composer", "update"], "Updating Composer dependencies"),
        (["yarn"], "Installing Node.js dependencies"),
        (["yarn", "build"], "Building assets")
    ]

    for cmd, description in commands:
        interface.display_message(stdscr, f"🔄 {description}...", "info", 2)
        if not project.run_command(cmd, plugin_directory, stdscr):
            interface.display_message(stdscr, f"❌ Failed: {description}", "error", height - 3)
            stdscr.getch()
            return

    if project.is_wp_cli_available():
        activation_command = ["wp", "plugin", "activate", plugin_name]
    elif project.is_lando_project():
        activation_command = ["lando", "wp", "plugin", "activate", plugin_name]
    else:
        interface.display_message(stdscr, "❌ No WP-CLI available. Plugin not activated.", "error", height - 3)
        stdscr.getch()
        return

    interface.display_message(stdscr, "🔄 Activating Plugin...", "info", 2)
    if project.run_command(activation_command, plugin_directory, stdscr):
        interface.display_message(stdscr, f"✅ Plugin '{plugin_name}' activated successfully!", "success", height - 3)
    else:
        interface.display_message(stdscr, f"❌ Plugin activation failed!", "error", height - 3)

    stdscr.getch()

def prepare_release(stdscr):
    """
    Prepares a release by:
     - Asking for the release version.
     - Updating the plugin header and version variable in the main plugin file.
     - Committing the changes and tagging the release.
     - Executing the distribution archive command (with or without lando).
     - Adding the generated ZIP archive to Git.
    """
    stdscr.clear()
    interface.draw_background(stdscr, "🚀 Prepare Release")
    height, width = stdscr.getmaxyx()
    
    wp_root = project.detect_wp_root()
    if not wp_root:
        interface.display_message(stdscr, "❌ No WordPress installation detected. Aborting.", "error", 15)
        stdscr.getch()
        return
    
    plugin_name = project.detect_plugin_name()
    if not plugin_name:
        interface.display_message(stdscr, "❌ No plugin detected. Aborting.", "error", 15)
        stdscr.getch()
        return
    
    plugin_name = plugin_name.lower().replace(" ", "-")
    plugins_directory = wp_root / "wp-content/plugins"
    plugin_root = plugins_directory / plugin_name

    # Ask for the release number/version
    box_x = (width - 50) // 2
    release = interface.get_user_input(stdscr, 8, box_x, "Enter release version:", 20)
    if not release:
        interface.display_message(stdscr, "Release cancelled.", "error", 4)
        stdscr.getch()
        return

    # Detect plugin name and main plugin file (assumes plugin name equals main file name)
    main_plugin_file = os.path.join(plugin_root, f"{plugin_name}.php")
    if not os.path.exists(main_plugin_file):
        interface.display_message(stdscr, "Main plugin file not found.", "error", 4)
        stdscr.getch()
        return
    
    plugin_constant = plugin_name.upper().replace("-", "_") + "_VERSION"

    # Update version in plugin header and version variable using regex substitutions.
    with open(main_plugin_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 1. Update header version
    new_content = re.sub(
        r"(Version:\s*)([\d\.]+)",
        lambda m: m.group(1) + release,
        content,
        flags=re.IGNORECASE
    )

    # 2. Update version constant
    pattern = rf"(define\(\s*['\"]{re.escape(plugin_constant)}['\"]\s*,\s*['\"])([\d\.]+)(['\"]\s*\))"

    new_content = re.sub(
        pattern,
        lambda m: m.group(1) + release + m.group(3),
        new_content
    )

    with open(main_plugin_file, "w", encoding="utf-8") as f:
        f.write(new_content)

    interface.display_message(stdscr, f"Updated version in {main_plugin_file}", "success", 4)
    stdscr.refresh()
    
    clear_git_lock(plugin_root)

    # Commit the version change and create a tag.
    if not project.run_command(["git", "add", main_plugin_file], plugin_root, stdscr):
        interface.display_message(stdscr, "Failed to stage changes.", "error", 4)
        stdscr.getch()
        return
    
    interface.display_message(stdscr, f"Added file", "success", 5)
    stdscr.refresh()

    commit_msg = f"Release version {release}"
    if not project.run_command(["git", "commit", "-m", commit_msg], plugin_root, stdscr):
        interface.display_message(stdscr, "Git commit failed.", "error", 4)
        stdscr.getch()
        return
    
    interface.display_message(stdscr, f"Commited file", "success", 5)
    stdscr.refresh()

    if not project.run_command(["git", "tag", release], plugin_root, stdscr):
        interface.display_message(stdscr, "Git tag creation failed.", "error", 4)
        stdscr.getch()
        return
    
    interface.display_message(stdscr, f"Tag created", "success", 5)
    stdscr.refresh()
    
    if not project.run_command(["git", "push", "origin", "main"], plugin_root, stdscr):
        interface.display_message(stdscr, "Git push failed.", "error", 4)
        stdscr.getch()
        return
    
    interface.display_message(stdscr, f"Pushed to repo", "success", 5)
    stdscr.refresh()
    
    token = Config.get("github", "token")
    repo = get_git_remote_repo(plugin_root)
    create_github_release(release, repo, token)

    # Execute the WP distribution archive command.
    # if project.is_lando_project():
    #     archive_cmd = ["lando", "wp", "dist", "archive", "."]
    # else:
    #     archive_cmd = ["wp", "dist", "archive", "."]

    # if not project.run_command(archive_cmd, plugin_root, stdscr):
    #     interface.display_message(stdscr, "Failed to create distribution archive.", "error", 4)
    #     stdscr.getch()
    #     return

    stdscr.addstr(height - 2, 4, "Press any key to return to the main menu.")
    stdscr.getch()
