# plubo/cli/commands/rename_plugin.py
import sys
from plubo.generators.plugin import rename_plugin

def rename_command(args):
    if len(args) != 2:
        print("Usage: plubo rename <old_name> <new_name>")
        sys.exit(1)
    
    old_name = args[0]
    new_name = args[1]
    try:
        rename_plugin(old_name, new_name)
        print(f"✅ Plugin renamed from '{old_name}' to '{new_name}'.")
        sys.exit(0)
    except Exception as error:
        print(f"❌ Rename failed: {error}")
        sys.exit(1)
