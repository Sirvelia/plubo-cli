import re
from pathlib import Path

HEADER_OPTION_TO_LABEL = {
    "--plugin-name": "Plugin Name",
    "--plugin-uri": "Plugin URI",
    "--author": "Author",
    "--author-uri": "Author URI",
    "--description": "Description",
    "--requires-plugins": "Requires Plugins",
    "--version": "Version",
}


def find_main_plugin_file(plugin_directory, plugin_slug=None):
    plugin_directory = Path(plugin_directory)

    if plugin_slug:
        expected_file = plugin_directory / f"{plugin_slug}.php"
        if expected_file.exists():
            return expected_file

    for php_file in plugin_directory.glob("*.php"):
        try:
            content = php_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        if "Plugin Name:" in content and "Text Domain:" in content:
            return php_file

    return None


def apply_plugin_header_updates(plugin_file, header_updates):
    if not header_updates:
        return False, []

    content = plugin_file.read_text(encoding="utf-8")
    header_match = re.search(r"/\*[\s\S]*?Plugin Name:[\s\S]*?\*/", content)
    if not header_match:
        return False, [f"No plugin header found in `{plugin_file.name}`"]

    header_block = header_match.group(0)
    updated_header = header_block

    for field, value in header_updates.items():
        pattern = re.compile(rf"(^\s*\*?\s*{re.escape(field)}\s*:\s*).*$", re.MULTILINE)
        if pattern.search(updated_header):
            updated_header = pattern.sub(lambda match: f"{match.group(1)}{value}", updated_header, count=1)
            continue

        updated_header = updated_header.replace("*/", f" * {field}: {value}\n */", 1)

    updated_content = content[:header_match.start()] + updated_header + content[header_match.end():]
    plugin_file.write_text(updated_content, encoding="utf-8")
    return True, [f"Updated plugin headers in `{plugin_file.name}`"]
