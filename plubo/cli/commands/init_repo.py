import sys
from plubo.utils import project
from plubo.settings.Config import Config
from plubo.git.github import create_github_repo
from plubo.git.gitlab import create_gitlab_repo, fetch_gitlab_groups, get_custom_gitlab_domains
from plubo.git.git_utils import initialize_git_repository, set_remote_and_push


def _resolve_custom_domain(platform):
    for domain in get_custom_gitlab_domains():
        if platform.lower() == domain.lower():
            return domain
    return None


def _resolve_gitlab_namespace_id(namespace, username, token, gitlab_domain):
    if namespace == username:
        return None

    groups = fetch_gitlab_groups(token, gitlab_domain)
    for group in groups:
        if group.get("full_path") == namespace:
            return group.get("id")

    return None

def init_repo_command(args):
    if len(args) > 2:
        print("Usage: plubo init-repo [github|gitlab|<custom-gitlab-domain>] [namespace]")
        sys.exit(1)

    platform = args[0].lower() if args else "github"
    namespace_arg = args[1] if len(args) == 2 else None

    wp_root = project.detect_wp_root()
    if not wp_root:
        print("❌ No WordPress installation detected. Aborting.")
        sys.exit(1)

    plugin_name = project.detect_plugin_name()
    if not plugin_name:
        print("❌ No plugin detected. Aborting.")
        sys.exit(1)

    plugin_name = plugin_name.lower().replace(" ", "-")
    plugin_directory = wp_root / "wp-content/plugins" / plugin_name

    try:
        if platform == "github":
            username = Config.get("github", "username")
            token = Config.get("github", "token")

            if not username or not token:
                print("❌ Missing GitHub username/token. Configure them in pb-cli settings.")
                sys.exit(1)

            namespace = namespace_arg or username
            remote_url = create_github_repo(username, token, plugin_name, namespace)
        else:
            custom_domain = _resolve_custom_domain(platform)
            if platform == "gitlab":
                gitlab_domain = "gitlab.com"
                config_section = "gitlab"
            elif custom_domain:
                gitlab_domain = custom_domain
                config_section = custom_domain.lower()
            else:
                print("❌ Invalid platform. Use github, gitlab, or a configured custom GitLab domain.")
                sys.exit(1)

            username = Config.get(config_section, "username")
            token = Config.get(config_section, "token")

            if not username or not token:
                print(f"❌ Missing credentials in '{config_section}' settings.")
                sys.exit(1)

            namespace = namespace_arg or username
            namespace_id = _resolve_gitlab_namespace_id(namespace, username, token, gitlab_domain)

            if namespace != username and namespace_id is None:
                print(f"❌ Namespace '{namespace}' not found on {gitlab_domain}.")
                sys.exit(1)

            remote_url = create_gitlab_repo(namespace, namespace_id, token, plugin_name, gitlab_domain)

        initialize_git_repository(plugin_directory)
        set_remote_and_push(remote_url, plugin_directory)
        print(f"✅ Repository initialized and pushed: {remote_url}")

    except Exception as error:
        print(f"❌ Failed to initialize repository: {error}")
        sys.exit(1)
