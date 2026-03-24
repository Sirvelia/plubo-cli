from importlib import metadata

PACKAGE_NAME = "plubo-cli"
__version__ = "0.1.0"


def get_version():
    """Return installed package version when available, otherwise local source version."""
    try:
        return metadata.version(PACKAGE_NAME)
    except metadata.PackageNotFoundError:
        return __version__
