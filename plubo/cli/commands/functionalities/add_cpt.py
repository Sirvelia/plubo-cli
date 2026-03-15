import sys
from plubo.utils import project
from ._shared import (
    default_plural,
    ensure_functionality_file,
    find_method_bounds,
    normalize_slug,
    slug_to_label,
)

USAGE = (
    "Usage: pb-cli functionalities cpt <slug> "
    "[--singular <label>] [--plural <label>]"
)


def _parse_args(args):
    if not args:
        print(USAGE)
        sys.exit(1)

    slug = None
    singular = None
    plural = None
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--singular":
            if index + 1 >= len(args):
                print("❌ Missing value for --singular")
                print(USAGE)
                sys.exit(1)
            singular = args[index + 1].strip()
            index += 2
            continue
        if arg == "--plural":
            if index + 1 >= len(args):
                print("❌ Missing value for --plural")
                print(USAGE)
                sys.exit(1)
            plural = args[index + 1].strip()
            index += 2
            continue
        if arg.startswith("--"):
            print(f"❌ Unknown option: {arg}")
            print(USAGE)
            sys.exit(1)
        if slug is not None:
            print("❌ Only one CPT slug is allowed.")
            print(USAGE)
            sys.exit(1)
        slug = arg
        index += 1

    if not slug:
        print(USAGE)
        sys.exit(1)

    normalized_slug = normalize_slug(slug)
    if not normalized_slug:
        print("❌ Invalid CPT slug.")
        sys.exit(1)

    singular_label = singular.strip() if singular else slug_to_label(normalized_slug)
    if not singular_label:
        singular_label = slug_to_label(normalized_slug)
    plural_label = plural.strip() if plural else default_plural(singular_label)
    if not plural_label:
        plural_label = default_plural(singular_label)

    return normalized_slug, singular_label, plural_label


def _build_cpt_block(slug, singular_label, plural_label, text_domain):
    return (
        f"        register_post_type('{slug}', [\n"
        "            'labels' => [\n"
        f"                'name' => __('{plural_label}', '{text_domain}'),\n"
        f"                'singular_name' => __('{singular_label}', '{text_domain}'),\n"
        "            ],\n"
        "            'public' => true,\n"
        "            'show_in_rest' => true,\n"
        "            'has_archive' => true,\n"
        "            'supports' => ['title', 'editor', 'thumbnail'],\n"
        "        ]);\n"
    )


def add_cpt_command(args):
    if not project.detect_plugin_name():
        print("❌ No plugin detected. Run this command from a plugin root.")
        sys.exit(1)

    slug, singular_label, plural_label = _parse_args(args)
    ok, file_path, message = ensure_functionality_file("Custom Post Types", "CustomPostTypes.php")
    if not ok:
        print(f"❌ {message}")
        sys.exit(1)

    content = file_path.read_text(encoding="utf-8")
    if (
        f"register_post_type('{slug}'" in content
        or f'register_post_type("{slug}"' in content
    ):
        print(f"❌ CPT '{slug}' is already registered in {file_path}")
        sys.exit(1)

    bounds = find_method_bounds(content, "public function register_post_types()")
    if not bounds:
        print(f"❌ Could not find method register_post_types() in {file_path}")
        sys.exit(1)

    text_domain = project.detect_plugin_name()
    _, body_end = bounds
    cpt_block = _build_cpt_block(slug, singular_label, plural_label, text_domain)
    closing_line_start = content.rfind("\n", 0, body_end) + 1
    closing_indent = content[closing_line_start:body_end]
    before_closing = content[:closing_line_start]
    if not before_closing.endswith("\n"):
        before_closing += "\n"
    updated_content = before_closing + cpt_block + closing_indent + content[body_end:]
    file_path.write_text(updated_content, encoding="utf-8")

    if message:
        print(f"ℹ️ {message}")
    print(f"✅ CPT '{slug}' added in {file_path}")
    sys.exit(0)
