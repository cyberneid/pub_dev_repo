from setuptools import setup, find_packages

setup(
    name = "pub_repo",
    version = "0.1.3",
    url = "https://codeberg.org/PapaTutuWawa/pub_repo",
    author = "Alexander \"PapaTutuWawa\"",
    author_email = "papatutuwawa <at> polynom.me",
    license = "GPLv3",
    packages = find_packages(),
    install_requires = [
        "falcon",
        "pyyaml",
        "jinja2"
    ],
    zip_safe = True
)
