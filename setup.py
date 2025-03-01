from setuptools import setup, find_packages
from pathlib import Path


def parse_requirements(filename='requirements.txt'):
    """
    Load requirements from a pip requirements file.

    Args:
        filename (str): Path to the requirements file.

    Returns:
        list: A list of required packages.
    """
    with open(filename, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    # Filter out comments and empty lines.
    reqs = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
    return reqs


setup(
    name='wikidump_processor',
    version='0.1.0',
    packages=find_packages(),
    install_requires=parse_requirements(),
    entry_points={
        'console_scripts': [
            # This creates a command-line tool named 'wikidump_processor'
            'wikidump_processor=main:main',
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
        "languages are: English (EN), Spanish (ES), Greek (GR), Polish (PL), German (DE), "
        "Basque (EUS), Dutch (NL), Hindi (HI), and Italian (IT)."
    ),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)