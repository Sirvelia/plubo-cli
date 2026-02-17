import sys
import re
from plubo.generators.functionality import create_functionality, FUNCTIONALITY_OPTIONS
from plubo.utils import project


def _normalize_token(value):
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _resolve_functionality(value):
    normalized_value = _normalize_token(value)

    for option, template_filename in FUNCTIONALITY_OPTIONS.items():
        if not template_filename:
            continue
        if normalized_value == _normalize_token(option):
            return option, template_filename

    return None, "Functionality.php"

def add_functionality_command(args):
    if not args:
        print("Usage: plubo functionality <name|preset>")
        print("Example presets: admin-menus, ajax-actions, routes, users")
        print("Custom class: plubo functionality custom <name>")
        sys.exit(1)

    if not project.detect_plugin_name():
        print("❌ No plugin detected. Run this command from a plugin root.")
        sys.exit(1)

    if args[0].lower() == "custom":
        if len(args) < 2:
            print("Usage: plubo functionality custom <name>")
            sys.exit(1)
        functionality_name = " ".join(args[1:]).strip()
        template_filename = "Functionality.php"
    else:
        requested = " ".join(args).strip()
        resolved_name, template_filename = _resolve_functionality(requested)
        functionality_name = resolved_name if resolved_name else requested

    created, message = create_functionality(functionality_name, template_filename)
    print(f"{'✅' if created else '❌'} {message}")
    sys.exit(0 if created else 1)
