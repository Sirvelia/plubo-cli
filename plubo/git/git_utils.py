import os
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