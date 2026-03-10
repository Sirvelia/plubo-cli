import sys
from pathlib import Path
from plubo.cli.commands.plugin_headers import HEADER_OPTION_TO_LABEL, apply_plugin_header_updates, find_main_plugin_file
from plubo.utils import project

USAGE = (
    "Usage: pb-cli set-headers "
    "[--plugin-name <name>] [--plugin-uri <url>] [--author <name>] "
    "[--author-uri <url>] [--description <text>] "
    "[--requires-plugins <plugins>] [--version <version>]"
)


def _parse_set_header_args(args):
    header_updates = {}
    index = 0

    while index < len(args):
        arg = args[index]
        if arg in HEADER_OPTION_TO_LABEL:
            if index + 1 >= len(args):
                print(f"❌ Missing value for option: {arg}")
                print(USAGE)
                sys.exit(1)

            value = args[index + 1].strip()
            if not value:
                print(f"❌ Empty value is not allowed for option: {arg}")
                print(USAGE)
                sys.exit(1)

            header_updates[HEADER_OPTION_TO_LABEL[arg]] = value
            index += 2
            continue

        matched_inline_option = False
        for option, header_label in HEADER_OPTION_TO_LABEL.items():
            prefix = f"{option}="
            if arg.startswith(prefix):
                value = arg[len(prefix):].strip()
                if not value:
                    print(f"❌ Empty value is not allowed for option: {option}")
                    print(USAGE)
                    sys.exit(1)

                header_updates[header_label] = value
                matched_inline_option = True
                break

        if matched_inline_option:
            index += 1
            continue

        print(f"❌ Unknown option: {arg}")
        print(USAGE)
        sys.exit(1)

    if not header_updates:
        print("❌ At least one header option is required.")
        print(USAGE)
        sys.exit(1)

    return header_updates


def set_plugin_headers_command(args):
    header_updates = _parse_set_header_args(args)
    plugin_directory = Path.cwd()
    plugin_slug = project.detect_plugin_name()
    main_plugin_file = find_main_plugin_file(plugin_directory, plugin_slug)

    if not main_plugin_file:
        print("❌ No plugin header file found. Run this command from your plugin root.")
        sys.exit(1)

    updated, messages = apply_plugin_header_updates(main_plugin_file, header_updates)
    if not updated:
        error_message = messages[0] if messages else "Unable to update plugin headers."
        print(f"❌ {error_message}")
        sys.exit(1)

    print(f"✅ Plugin headers updated in `{main_plugin_file.name}`.")
    for message in messages:
        print(f"ℹ️ {message}")
