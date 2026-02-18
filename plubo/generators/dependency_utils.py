import json
import re
from pathlib import Path


class DependencyScaffoldUtils:
    @staticmethod
    def normalize_token(value):
        return re.sub(r"[^a-z0-9]+", "", value.lower())

    @staticmethod
    def display_path(path, cwd):
        try:
            return str(path.relative_to(cwd))
        except ValueError:
            return str(path)

    @classmethod
    def write_file_if_missing(cls, path, content, cwd):
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            return f"Kept existing `{cls.display_path(path, cwd)}`"
        path.write_text(content, encoding="utf-8")
        return f"Created `{cls.display_path(path, cwd)}`"

    @classmethod
    def copy_template_if_missing(cls, template_path, destination_path, cwd):
        if not template_path.exists():
            return f"Skipped `{cls.display_path(destination_path, cwd)}`: missing template `{template_path}`"
        template_content = template_path.read_text(encoding="utf-8")
        return cls.write_file_if_missing(destination_path, template_content, cwd)

    @classmethod
    def ensure_package_json_scripts(cls, cwd, scripts_to_add, conditional_scripts=None):
        package_json_path = cwd / "package.json"
        if not package_json_path.exists():
            return [f"Skipped package.json script updates: `{cls.display_path(package_json_path, cwd)}` not found"]

        try:
            package_data = json.loads(package_json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return [f"Skipped package.json script updates: invalid JSON in `{cls.display_path(package_json_path, cwd)}`"]

        scripts = package_data.setdefault("scripts", {})
        added = []

        for script_name, script_cmd in scripts_to_add.items():
            if script_name not in scripts:
                scripts[script_name] = script_cmd
                added.append(script_name)

        for script_name, script_cmd in (conditional_scripts or {}).items():
            if script_name not in scripts:
                scripts[script_name] = script_cmd
                added.append(script_name)

        if not added:
            return ["Kept existing package.json scripts"]

        package_json_path.write_text(json.dumps(package_data, indent=2) + "\n", encoding="utf-8")
        added_display = ", ".join(f"`{name}`" for name in added)
        return [f"Added package.json scripts: {added_display}"]
