import sys
from plubo.generators.entity import create_entity
from plubo.utils import project

def add_entity_command(args):
    if not args:
        print("Usage: plubo entity <entity_name>")
        sys.exit(1)

    if not project.detect_plugin_name():
        print("❌ No plugin detected. Run this command from a plugin root.")
        sys.exit(1)

    entity_name = " ".join(args).strip().replace(" ", "-")
    created, message = create_entity(entity_name)
    print(f"{'✅' if created else '❌'} {message}")
    sys.exit(0 if created else 1)
