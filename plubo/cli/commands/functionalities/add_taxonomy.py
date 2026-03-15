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
    "Usage: pb-cli functionalities taxonomy <taxonomy_slug> <post_type_slug> "
    "[--singular <label>] [--plural <label>] [--hierarchical]"
)


def _parse_args(args):
    if len(args) < 2:
        print(USAGE)
        sys.exit(1)

    taxonomy_slug = None
    post_type_slug = None
    singular = None
    plural = None
    hierarchical = False
    positional = []
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
        if arg == "--hierarchical":
            hierarchical = True
            index += 1
            continue
        if arg.startswith("--"):
            print(f"❌ Unknown option: {arg}")
            print(USAGE)
            sys.exit(1)
        positional.append(arg)
        index += 1

    if len(positional) != 2:
        print(USAGE)
        sys.exit(1)

    taxonomy_slug = normalize_slug(positional[0])
    post_type_slug = normalize_slug(positional[1])
    if not taxonomy_slug or not post_type_slug:
        print("❌ Invalid taxonomy slug or post type slug.")
        sys.exit(1)

    singular_label = singular.strip() if singular else slug_to_label(taxonomy_slug)
    if not singular_label:
        singular_label = slug_to_label(taxonomy_slug)
    plural_label = plural.strip() if plural else default_plural(singular_label)
    if not plural_label:
        plural_label = default_plural(singular_label)

    return taxonomy_slug, post_type_slug, singular_label, plural_label, hierarchical


def _build_taxonomy_block(taxonomy_slug, post_type_slug, singular_label, plural_label, text_domain, hierarchical):
    hierarchical_value = "true" if hierarchical else "false"
    return (
        f"        register_taxonomy('{taxonomy_slug}', ['{post_type_slug}'], [\n"
        "            'labels' => [\n"
        f"                'name' => __('{plural_label}', '{text_domain}'),\n"
        f"                'singular_name' => __('{singular_label}', '{text_domain}'),\n"
        "            ],\n"
        "            'public' => true,\n"
        "            'show_in_rest' => true,\n"
        f"            'hierarchical' => {hierarchical_value},\n"
        "        ]);\n"
    )


def add_taxonomy_command(args):
    if not project.detect_plugin_name():
        print("❌ No plugin detected. Run this command from a plugin root.")
        sys.exit(1)

    taxonomy_slug, post_type_slug, singular_label, plural_label, hierarchical = _parse_args(args)
    ok, file_path, message = ensure_functionality_file("Taxonomies", "Taxonomies.php")
    if not ok:
        print(f"❌ {message}")
        sys.exit(1)

    content = file_path.read_text(encoding="utf-8")
    if (
        f"register_taxonomy('{taxonomy_slug}'" in content
        or f'register_taxonomy("{taxonomy_slug}"' in content
    ):
        print(f"❌ Taxonomy '{taxonomy_slug}' is already registered in {file_path}")
        sys.exit(1)

    bounds = find_method_bounds(content, "public function register_taxonomies()")
    if not bounds:
        print(f"❌ Could not find method register_taxonomies() in {file_path}")
        sys.exit(1)

    text_domain = project.detect_plugin_name()
    _, body_end = bounds
    taxonomy_block = _build_taxonomy_block(
        taxonomy_slug,
        post_type_slug,
        singular_label,
        plural_label,
        text_domain,
        hierarchical,
    )
    closing_line_start = content.rfind("\n", 0, body_end) + 1
    closing_indent = content[closing_line_start:body_end]
    before_closing = content[:closing_line_start]
    if not before_closing.endswith("\n"):
        before_closing += "\n"
    updated_content = before_closing + taxonomy_block + closing_indent + content[body_end:]
    file_path.write_text(updated_content, encoding="utf-8")

    if message:
        print(f"ℹ️ {message}")
    print(f"✅ Taxonomy '{taxonomy_slug}' added in {file_path}")
    sys.exit(0)
