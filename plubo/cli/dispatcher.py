# plubo/cli/dispatcher.py
import sys
from plubo.cli.commands import rename_plugin
import curses

COMMANDS = {
    'rename': rename_plugin.rename_command,
    # 'add-component': add_component.add_component_command,
    # Additional commands can be added here...
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
