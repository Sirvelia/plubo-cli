import sys
from .add_cpt import add_cpt_command
from .add_taxonomy import add_taxonomy_command

SUBCOMMANDS = {
    "cpt": add_cpt_command,
    "post-type": add_cpt_command,
    "taxonomy": add_taxonomy_command,
    "tax": add_taxonomy_command,
}

USAGE = (
    "Usage: pb-cli functionalities <subcommand> [args]\n"
    "Subcommands:\n"
    "  cpt <slug> [--singular <label>] [--plural <label>]\n"
    "  taxonomy <taxonomy_slug> <post_type_slug> "
    "[--singular <label>] [--plural <label>] [--hierarchical]"
)


def functionalities_command(args):
    if not args or args[0] in {"help", "--help", "-h"}:
        print(USAGE)
        sys.exit(0 if args else 1)

    subcommand = args[0].lower()
    handler = SUBCOMMANDS.get(subcommand)
    if not handler:
        print(f"❌ Unknown functionalities subcommand: {subcommand}")
        print(USAGE)
        sys.exit(1)

    handler(args[1:])

