import sys
import re
import subprocess
from plubo.utils import project
from plubo.settings.Config import Config
from plubo.git.github import create_github_release
from plubo.git.git_utils import get_git_remote_repo, clear_git_lock


def _run_git(command, cwd):
    subprocess.run(command, cwd=str(cwd), check=True)

def prepare_release_command(args):
    if not args:
        print("Usage: plubo release <version> [--no-github-release]")
        sys.exit(1)

    release = args[0]
    options = set(args[1:])
    invalid_options = [option for option in options if option != "--no-github-release"]

    if invalid_options:
        print("Usage: plubo release <version> [--no-github-release]")
        sys.exit(1)

    wp_root = project.detect_wp_root()
    if not wp_root:
        print("❌ No WordPress installation detected. Aborting.")
        sys.exit(1)

    plugin_name = project.detect_plugin_name()
    if not plugin_name:
        print("❌ No plugin detected. Aborting.")
        sys.exit(1)

    plugin_name = plugin_name.lower().replace(" ", "-")
    plugin_root = wp_root / "wp-content/plugins" / plugin_name
    main_plugin_file = plugin_root / f"{plugin_name}.php"

    if not main_plugin_file.exists():
        print(f"❌ Main plugin file not found: {main_plugin_file}")
        sys.exit(1)

    plugin_constant = plugin_name.upper().replace("-", "_") + "_VERSION"

    content = main_plugin_file.read_text(encoding="utf-8")
    new_content, header_count = re.subn(
        r"(Version:\s*)([\d\.]+)",
        lambda match: match.group(1) + release,
        content,
        flags=re.IGNORECASE
    )

    constant_pattern = rf"(define\(\s*['\"]{re.escape(plugin_constant)}['\"]\s*,\s*['\"])([\d\.]+)(['\"]\s*\))"
    new_content, constant_count = re.subn(
        constant_pattern,
        lambda match: match.group(1) + release + match.group(3),
        new_content
    )

    if header_count == 0:
        print("⚠️ Plugin header version not found; no header update made.")
    if constant_count == 0:
        print(f"⚠️ Version constant '{plugin_constant}' not found; no constant update made.")

    main_plugin_file.write_text(new_content, encoding="utf-8")
    print(f"✅ Updated version references in {main_plugin_file}")

    clear_git_lock(plugin_root)

    try:
        relative_main_file = str(main_plugin_file.relative_to(plugin_root))
        _run_git(["git", "add", relative_main_file], plugin_root)
        _run_git(["git", "commit", "-m", f"Release version {release}"], plugin_root)
        _run_git(["git", "tag", release], plugin_root)

        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(plugin_root),
            capture_output=True,
            text=True,
            check=True
        ).stdout.strip()
        _run_git(["git", "push", "origin", branch], plugin_root)
        _run_git(["git", "push", "origin", release], plugin_root)
        print(f"✅ Release commit, tag, and push completed on branch '{branch}'.")
    except subprocess.CalledProcessError as error:
        print(f"❌ Git operation failed with exit code {error.returncode}.")
        sys.exit(error.returncode)

    if "--no-github-release" in options:
        print("ℹ️ Skipped GitHub release creation.")
        return

    token = Config.get("github", "token")
    repo = get_git_remote_repo(plugin_root)
    if not token or not repo:
        print("ℹ️ Skipped GitHub release: missing GitHub token or non-GitHub remote.")
        return

    try:
        success, payload = create_github_release(release, repo, token)
        if success:
            print(f"✅ GitHub release created for tag {release}.")
        else:
            message = payload.get("message", "unknown error") if isinstance(payload, dict) else str(payload)
            print(f"❌ GitHub release failed: {message}")
            sys.exit(1)
    except Exception as error:
        print(f"❌ GitHub release failed: {error}")
        sys.exit(1)
