import sys
from plubo.generators.component import create_component
from plubo.utils import project

def add_component_command(args):
    if not args:
        print("Usage: plubo component <component_name>")
        sys.exit(1)

    if not project.detect_plugin_name():
        print("❌ No plugin detected. Run this command from a plugin root.")
        sys.exit(1)

    component_name = " ".join(args).strip().replace(" ", "-")
    created, message = create_component(component_name)
    print(f"{'✅' if created else '❌'} {message}")
    sys.exit(0 if created else 1)
