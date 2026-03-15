import re
from pathlib import Path
from plubo.generators.functionality import create_functionality


def normalize_slug(value):
    normalized = re.sub(r"[^a-z0-9_-]+", "-", value.strip().lower())
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-_")
    return normalized


def slug_to_label(value):
    tokens = [part for part in re.split(r"[-_\s]+", value.strip()) if part]
    return " ".join(token.capitalize() for token in tokens)


def to_pascal_case(value):
    tokens = [part for part in re.split(r"[-_\s]+", value.strip()) if part]
    return "".join(token.capitalize() for token in tokens)


def default_plural(label):
    return label if label.endswith("s") else f"{label}s"


def find_method_bounds(content, method_signature):
    method_start = content.find(method_signature)
    if method_start < 0:
        return None

    opening_brace = content.find("{", method_start)
    if opening_brace < 0:
        return None

    depth = 1
    index = opening_brace + 1
    while index < len(content):
        char = content[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return opening_brace + 1, index
        index += 1

    return None


def ensure_functionality_file(class_name, template_filename):
    plugin_root = Path.cwd()
    resolved_class_name = to_pascal_case(class_name)
    file_path = plugin_root / "Functionality" / f"{resolved_class_name}.php"
    if file_path.exists():
        return True, file_path, ""

    created, message = create_functionality(class_name, template_filename)
    if not created:
        return False, None, message

    if not file_path.exists():
        return False, None, f"Expected file not found after creation: {file_path}"

    return True, file_path, message
