from pathlib import Path
import curses
import os
import json
import re
from plubo.utils import project, interface
from plubo.generators.dependency_utils import DependencyScaffoldUtils

NODE_TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "node"


DEPENDENCY_OPTIONS = {
    "ALPINE.JS": {
        "packages": [
            {"name": "alpinejs", "dev": False},
            {"name": "@types/alpinejs", "dev": True},
        ],
        "post_install": ["scaffold_alpine_bootstrap"],
    },
    "TAILWIND CSS": {
        "packages": [
            {"name": "tailwindcss", "dev": True},
            {"name": "@tailwindcss/vite", "dev": True},
        ],
        "post_install": ["scaffold_tailwind_setup"],
    },
    "DAISY UI": {
        "packages": [
            {"name": "daisyui@latest", "dev": True},
        ],
    },
    "HIKEFLOW": {
        "packages": [
            {"name": "hikeflow", "dev": False},
        ],
    },
    "RETURN": None  # Special case, no package to install
}

def get_dependency_packages(dependency_option):
    """Return a normalized package list with explicit dev flags."""
    if not dependency_option:
        return []

    if isinstance(dependency_option, str):
        return [{"name": package_name, "dev": False} for package_name in dependency_option.split()]

    package_entries = dependency_option.get("packages", [])
    normalized_packages = []

    for entry in package_entries:
        if isinstance(entry, str):
            normalized_packages.append({"name": entry, "dev": bool(dependency_option.get("dev", False))})
            continue

        package_name = entry.get("name")
        if not package_name:
            continue

        normalized_packages.append(
            {"name": package_name, "dev": bool(entry.get("dev", dependency_option.get("dev", False)))}
        )

    return normalized_packages

def get_post_install_actions(dependency_option):
    if not isinstance(dependency_option, dict):
        return []
    actions = dependency_option.get("post_install", [])
    return [action for action in actions if isinstance(action, str)]

def resolve_dependency(value):
    """Resolve a preset from user input; fallback to custom package tokens."""
    normalized_value = DependencyScaffoldUtils.normalize_token(value)

    for option_name, dependency_option in DEPENDENCY_OPTIONS.items():
        packages = get_dependency_packages(dependency_option)
        if not packages:
            continue

        candidate_tokens = {DependencyScaffoldUtils.normalize_token(option_name)}
        candidate_tokens.update(DependencyScaffoldUtils.normalize_token(package["name"]) for package in packages)

        if normalized_value in candidate_tokens:
            return dependency_option, True

    return {"packages": [{"name": package_name, "dev": False} for package_name in value.split()]}, False

def _resolve_js_entrypoint(cwd):
    candidates = [
        cwd / "src/scripts/app.ts",
        cwd / "src/scripts/app.js",
        cwd / "src/js/app.js",
        cwd / "src/app.ts",
        cwd / "src/main.ts",
        cwd / "src/app.js",
        cwd / "src/main.js",
        cwd / "assets/js/app.js",
        cwd / "assets/src/app.js",
        cwd / "assets/src/js/app.js",
    ]

    for path in candidates:
        if path.exists():
            return path, False

    use_typescript = (cwd / "src/styles/app.scss").exists() or (cwd / "src/scripts").exists()
    fallback = cwd / "src/scripts/app.ts" if use_typescript else cwd / "src/js/app.js"
    created = not fallback.exists()
    DependencyScaffoldUtils.write_file_if_missing(fallback, "", cwd)
    return fallback, created

def _ensure_import(entrypoint_path, import_line):
    content = entrypoint_path.read_text(encoding="utf-8")
    normalized_import = import_line.strip()

    if normalized_import in content or "alpine-bootstrap" in content:
        return False

    if content.strip():
        entrypoint_path.write_text(f"{import_line}\n{content}", encoding="utf-8")
    else:
        entrypoint_path.write_text(f"{import_line}\n", encoding="utf-8")
    return True

def _ensure_scss_import(entrypoint_path, import_line):
    content = entrypoint_path.read_text(encoding="utf-8")
    normalized_import = import_line.strip()

    if normalized_import in content or "tailwind.css" in content:
        return False

    if content.strip():
        entrypoint_path.write_text(f"{import_line}\n{content}", encoding="utf-8")
    else:
        entrypoint_path.write_text(f"{import_line}\n", encoding="utf-8")
    return True

def _find_vite_config_path(cwd):
    for filename in (
        "vite.config.ts",
        "vite.config.js",
        "vite.config.mts",
        "vite.config.mjs",
        "vite.config.cts",
        "vite.config.cjs",
    ):
        path = cwd / filename
        if path.exists():
            return path
    return None

def _ensure_vite_tailwind_plugin(cwd):
    vite_config_path = _find_vite_config_path(cwd)
    if not vite_config_path:
        return "Skipped Vite config update: no `vite.config.*` file found"

    content = vite_config_path.read_text(encoding="utf-8")
    updated_content = content

    if "@tailwindcss/vite" not in updated_content:
        import_line = 'import tailwindcss from "@tailwindcss/vite";'
        require_line = 'const tailwindcss = require("@tailwindcss/vite");'

        import_matches = list(re.finditer(r"^import\s.+$", updated_content, flags=re.MULTILINE))
        if import_matches:
            last_import = import_matches[-1]
            insertion_point = last_import.end()
            updated_content = (
                updated_content[:insertion_point]
                + f"\n{import_line}"
                + updated_content[insertion_point:]
            )
        elif "export default" in updated_content:
            updated_content = f"{import_line}\n{updated_content}"
        elif "module.exports" in updated_content:
            updated_content = updated_content.replace(
                "module.exports",
                f"{require_line}\n\nmodule.exports",
                1,
            )
        else:
            return (
                f"Skipped `{DependencyScaffoldUtils.display_path(vite_config_path, cwd)}`: "
                "unable to add `@tailwindcss/vite` import"
            )

    if "tailwindcss()" not in updated_content:
        updated_content, plugin_count = re.subn(
            r"plugins\s*:\s*\[",
            "plugins: [\n    tailwindcss(),",
            updated_content,
            count=1,
        )
        if plugin_count == 0:
            return (
                f"Skipped `{DependencyScaffoldUtils.display_path(vite_config_path, cwd)}`: "
                "unable to find `plugins` array for Vite"
            )

    if updated_content == content:
        return f"Kept existing `{DependencyScaffoldUtils.display_path(vite_config_path, cwd)}`"

    vite_config_path.write_text(updated_content, encoding="utf-8")
    return f"Updated `{DependencyScaffoldUtils.display_path(vite_config_path, cwd)}` with Tailwind Vite plugin"

def _scaffold_tailwind_setup(cwd):
    messages = []
    has_plubo_layout = (cwd / "src/styles/app.scss").exists()
    messages.append(_ensure_vite_tailwind_plugin(cwd))

    if has_plubo_layout:
        messages.append(
            DependencyScaffoldUtils.copy_template_if_missing(
                NODE_TEMPLATES_DIR / "app.css",
                cwd / "src/styles/tailwind.css",
                cwd,
            )
        )

        app_scss_path = cwd / "src/styles/app.scss"
        if _ensure_scss_import(app_scss_path, '@import "tailwind.css";'):
            messages.append(
                f"Added Tailwind import to `{DependencyScaffoldUtils.display_path(app_scss_path, cwd)}`"
            )
        else:
            messages.append(
                f"Kept existing Tailwind import in `{DependencyScaffoldUtils.display_path(app_scss_path, cwd)}`"
            )
        return messages

    messages.append(
        DependencyScaffoldUtils.copy_template_if_missing(
            NODE_TEMPLATES_DIR / "app.css",
            cwd / "src/css/app.css",
            cwd,
        )
    )
    return messages

def _scaffold_alpine_bootstrap(cwd):
    messages = []
    entrypoint_path, created = _resolve_js_entrypoint(cwd)
    bootstrap_extension = ".ts" if entrypoint_path.suffix in {".ts", ".tsx"} else ".js"
    bootstrap_template_name = "alpine-bootstrap.ts" if bootstrap_extension == ".ts" else "alpine-bootstrap.js"
    bootstrap_path = entrypoint_path.parent / f"alpine-bootstrap{bootstrap_extension}"
    messages.append(
        DependencyScaffoldUtils.copy_template_if_missing(
            NODE_TEMPLATES_DIR / bootstrap_template_name,
            bootstrap_path,
            cwd,
        )
    )

    if created:
        messages.append(f"Created `{DependencyScaffoldUtils.display_path(entrypoint_path, cwd)}`")

    relative_bootstrap = os.path.relpath(bootstrap_path, entrypoint_path.parent).replace(os.sep, "/")
    if not relative_bootstrap.startswith("."):
        relative_bootstrap = f"./{relative_bootstrap}"
    import_line = f'import "{relative_bootstrap}";'

    if _ensure_import(entrypoint_path, import_line):
        messages.append(
            f"Added Alpine bootstrap import to `{DependencyScaffoldUtils.display_path(entrypoint_path, cwd)}`"
        )
    else:
        messages.append(
            f"Kept existing Alpine bootstrap import in `{DependencyScaffoldUtils.display_path(entrypoint_path, cwd)}`"
        )

    return messages

def apply_post_install_actions(dependency_option, cwd=None):
    cwd = Path(cwd) if cwd else Path(os.getcwd())
    messages = []
    action_handlers = {
        "scaffold_tailwind_setup": _scaffold_tailwind_setup,
        "scaffold_alpine_bootstrap": _scaffold_alpine_bootstrap,
    }

    for action in get_post_install_actions(dependency_option):
        handler = action_handlers.get(action)
        if not handler:
            messages.append(f"Skipped unknown post-install action `{action}`")
            continue
        try:
            messages.extend(handler(cwd))
        except Exception as error:
            messages.append(f"Failed post-install action `{action}`: {error}")

    return messages

def get_installed_dependencies():
    """Read package.json and return a dictionary of installed dependencies and versions."""
    package_json_path = "package.json"

    if not os.path.exists(package_json_path):
        return {}

    try:
        with open(package_json_path, "r", encoding="utf-8") as file:
            deps_data = json.load(file)
            
            # Merge dependencies and devDependencies
            dependencies = deps_data.get("dependencies", {})
            dev_dependencies = deps_data.get("devDependencies", {})

            return {**dependencies, **dev_dependencies}  # Merge both dictionaries
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def install_dependency(stdscr, dependency_option):
    """Install a specific Composer dependency, handling Lando projects."""
    packages = get_dependency_packages(dependency_option)
    if not packages:
        return  # Do nothing if the user selects "Back to Main Menu"

    package_names = [package["name"] for package in packages]
    stdscr.clear()
    interface.draw_background(stdscr, f"⏳ Installing {' '.join(package_names)}...")

    height, width = stdscr.getmaxyx()

    commands = []
    regular_packages = [package["name"] for package in packages if not package["dev"]]
    dev_packages = [package["name"] for package in packages if package["dev"]]

    if regular_packages:
        commands.append(["yarn", "add"] + regular_packages)
    if dev_packages:
        commands.append(["yarn", "add", "--dev"] + dev_packages)

    success = True
    for command in commands:
        success = project.run_command(command, Path(os.getcwd()), stdscr)
        if not success:
            break

    post_install_messages = []
    if success:
        post_install_messages = apply_post_install_actions(dependency_option, cwd=Path(os.getcwd()))

    package_display = ", ".join(package_names)
    message = (
        f"✅ Successfully installed {package_display}"
        if success
        else f"❌ Installation failed for {package_display}"
    )

    stdscr.addstr(height - 3, 4, message, curses.color_pair(3))
    if post_install_messages:
        stdscr.addstr(height - 2, 4, f"ℹ️ {post_install_messages[-1][: max(0, width - 8)]}", curses.color_pair(3))
    stdscr.refresh()

    # **Wait for user input before returning**
    stdscr.getch()  # Wait user input

def dependency_menu(stdscr):
    """Display the dependency installation submenu with a background title."""
    curses.curs_set(0)  # Hide cursor   
    stdscr.keypad(True)
        
    current_row = 0
    height, width = stdscr.getmaxyx()

    while True:
        installed_dependencies = get_installed_dependencies()
        menu_options = []
        original_names = []  # To map displayed names back to actual options

        for option, dependency_option in DEPENDENCY_OPTIONS.items():
            checkmark = ""
            version_info = ""
            packages = get_dependency_packages(dependency_option)

            all_packages_installed = bool(packages) and all(
                package["name"] in installed_dependencies for package in packages
            )
            if all_packages_installed:
                checkmark = "✅"

            installed_versions = [
                f'{package["name"]} {installed_dependencies[package["name"]]}'
                for package in packages
                if package["name"] in installed_dependencies
            ]
            if installed_versions:
                version_info = f" ({', '.join(installed_versions)})"

            display_text = f"{checkmark} {option} {version_info}".strip()
            menu_options.append(display_text)
            original_names.append(option)  # Keep track of original option names
            
        selected_row, current_row = interface.render_menu(stdscr, menu_options, current_row, height, width)
        
        if selected_row is not None:
            selected_option = original_names[selected_row]
            dependency_option = DEPENDENCY_OPTIONS[selected_option]
            if dependency_option is not None:
                install_dependency(stdscr, dependency_option)
            return
