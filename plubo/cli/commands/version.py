import sys

from plubo.version import get_version


def version_command(args):
    if args:
        print("Usage: pb-cli version")
        sys.exit(1)

    print(get_version())
