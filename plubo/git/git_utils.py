import os
import re
import subprocess

def run_git_command(command, cwd=None):
    """Runs a Git command inside the given directory."""
    result = subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True)
    return result.stdout.strip()

def initialize_git_repository(plugin_directory):
    """Initialize a new Git repository."""
    os.chdir(plugin_directory)
    run_git_command(["git", "init"])
    run_git_command(["git", "add", "-A"])
    run_git_command(["git", "commit", "-m", "Initial commit"])

def set_remote_and_push(remote_url, plugin_directory):
    """Set Git remote and push initial commit."""
    os.chdir(plugin_directory)
    run_git_command(["git", "remote", "add", "origin", remote_url])
    run_git_command(["git", "branch", "-M", "main"])
    run_git_command(["git", "push", "-u", "origin", "main"])
    
def get_git_remote_repo(path):
    try:
        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=path,
            capture_output=True,
            text=True,
            check=True
        )
        url = result.stdout.strip()
        
        # Match GitHub-style URLs
        https_match = re.match(r"https://github\.com/(.*?)(\.git)?$", url)
        ssh_match = re.match(r"git@github\.com:(.*?)(\.git)?$", url)
        
        if https_match:
            return https_match.group(1)
        elif ssh_match:
            return ssh_match.group(1)
        else:
            return None
    except subprocess.CalledProcessError:
        return None

def clear_git_lock(repo_path):
    lock_path = os.path.join(repo_path, ".git", "index.lock")
    if os.path.exists(lock_path):
        os.remove(lock_path)
        print(f"Removed lock file: {lock_path}")