from setuptools import setup, find_packages
from pathlib import Path


def parse_requirements(filename='requirements.txt'):
    """
    Loads dependencies from a pip requirements file.

    Args:
        filename (str | Path, optional): Path to the requirements file. Defaults to 'requirements.txt'.

    Returns:
        list: A list of required packages as strings.
    """
    filename = Path(filename)  # ensure cross-platform path handling
    if not filename.exists():
        return []  # return an empty list if file does not exist

    with filename.open('r', encoding='utf-8') as file:
        lines = file.readlines()

    # filter out comments and empty lines
    reqs = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
    return reqs


setup(
    name='MultiLGraphWiki',
    version='0.1.0',
    packages=find_packages(),
    install_requires=parse_requirements(),
    entry_points={
        'console_scripts': [
            # this creates a command-line tool named 'MultiLGraphWiki'
            'MultiLGraphWiki=main:main',
        ],
    },
    author="Paschalis Agapitos",
    author_email="pasxalisag9@gmail.com",
    description=(
        "MultiLGraphWiki is a tool that parses Wikipedia dumps, cleans the texts, and saves the "
        "title and the cleaned text of each article present in a given Wikipedia dump. Moreover, "
        "if prompted, it will create a graph by resolving the redirects and maximizing the "
        "total number of valid links in the final version. Currently, it supports 9 languages "
        "but it can be extended by tweaking the `LANG_SETTINGS.yml` file. The supported "
        "languages are: English (en), Spanish (es), Greek (el), Polish (pl), German (de), "
        "Basque (eu), Dutch (nl), Hindi (hi), and Italian (it)."
    ),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)