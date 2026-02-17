import sys
from plubo.generators.dependencies import check_composer_dependencies, get_yarn_outdated

def check_dependencies_command(args):
    strict = "--strict" in args
    invalid_args = [arg for arg in args if arg != "--strict"]

    if invalid_args:
        print("Usage: plubo check-dep [--strict]")
        print("--strict: exit with code 1 if outdated dependencies are found")
        sys.exit(1)

    composer_outdated = check_composer_dependencies()
    yarn_outdated = get_yarn_outdated()

    if composer_outdated:
        print("Outdated Composer dependencies:")
        for package, versions in composer_outdated.items():
            print(f"- {package}: {versions['current']} -> {versions['latest']}")
    else:
        print("All Composer dependencies are up to date.")

    if yarn_outdated:
        print("Outdated Yarn dependencies:")
        for package, versions in yarn_outdated.items():
            print(f"- {package}: {versions['current']} -> {versions['latest']}")
    else:
        print("All Yarn dependencies are up to date.")

    outdated_count = len(composer_outdated) + len(yarn_outdated)
    if outdated_count == 0:
        print("✅ No outdated dependencies found.")
        sys.exit(0)

    print(f"⚠️ Found {outdated_count} outdated dependencies.")
    sys.exit(1 if strict else 0)
