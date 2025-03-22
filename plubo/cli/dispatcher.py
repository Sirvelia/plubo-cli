# plubo/cli/dispatcher.py
import sys
from plubo.cli.commands import add_component, add_entity, add_functionality, add_node_dependency, add_php_dependency, check_dependencies, create_plugin, init_repo, prepare_release, rename_plugin
import curses

COMMANDS = {
    'component': add_component.add_component_command,
    'entity': add_entity.add_entity_command,
    'functionality': add_functionality.add_functionality_command,
    'node-dep': add_node_dependency.add_node_dependency_command,
    'php-dep': add_php_dependency.add_php_dependency_command,
    'check-dep': check_dependencies.check_dependencies_command,
    'create': create_plugin.create_plugin_command,
    'init-repo': init_repo.init_repo_command,
    'release': prepare_release.prepare_release_command,
    'rename': rename_plugin.rename_command,
}

def dispatch(menu):
    if len(sys.argv) < 2:
        
        # If no direct command, launch the interactive menu
        curses.wrapper(menu)
        sys.exit(1)
    
    # if len(sys.argv) < 2:
    #     print("Usage: plubo <command> [args]")
    #     print("Available commands:", ", ".join(COMMANDS.keys()))
    #     sys.exit(1)

    command_name = sys.argv[1]
    command_func = COMMANDS.get(command_name)
    if not command_func:
        print(f"Unknown command: {command_name}")
        sys.exit(1)

    # Pass remaining arguments to the command function
    command_args = sys.argv[2:]
    command_func(command_args)

if __name__ == '__main__':
    dispatch()
