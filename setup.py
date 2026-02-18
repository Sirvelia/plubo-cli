from setuptools import setup, find_packages

setup(
    name="plubo-cli",
    version="0.1.0",
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
