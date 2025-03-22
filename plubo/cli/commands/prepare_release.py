import sys
from plubo.generators.plugin import rename_plugin

def prepare_release_command(args):
    if len(args) != 2:
        print("Usage: plubo rename <old_name> <new_name>")
        sys.exit(1)
    
    old_name = args[0]
    new_name = args[1]
    result = rename_plugin(old_name, new_name)
    print(result)