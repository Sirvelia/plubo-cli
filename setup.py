from pathlib import Path
import re

from setuptools import setup, find_packages


def read_version():
    version_file = Path(__file__).resolve().parent / "plubo" / "version.py"
    match = re.search(
        r"^__version__\s*=\s*[\"']([^\"']+)[\"']",
        version_file.read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    if not match:
        raise RuntimeError("Unable to find __version__ in plubo/version.py")
    return match.group(1)

setup(
    name="plubo-cli",
    version=read_version(),
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "plubo": [
            "templates/*.php",
            "templates/Admin/*.php",
            "templates/node/*",
        ],
    },
    install_requires=[
        "packaging",
        "requests",
    ],
    entry_points={
        "console_scripts": [
            "pb-cli=plubo.main:main",
        ],
    },
)
