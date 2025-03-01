# MultilGraphWiki

MultiLGraphWiki is a powerful tool for parsing Wikipedia dumps, cleaning article texts, and generating graph representations of Wikipedia's link structure. 
It supports multiple languages and provides both command-line and graphical interfaces for ease of use.

## Features

- Parse Wikipedia XML dumps and extract article titles and cleaned text
- Generate graph representations of Wikipedia's link structure
- Resolve redirects to maximize valid links in the final graph
- Support for 9 languages: English (en), Spanish (es), Greek (el), Polish (pl), German (de), Basque (eu), Dutch (nl), Hindi (hi), and Italian (it)
- Extensible language support through configuration
- User-friendly GUI for non-technical users

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/MultiLGraphWiki.git
   cd MultiLGraphWiki
   ```

2. Install the package and its dependencies:
   ```bash
   pip install -e .
   ```

   This will install all the required dependencies listed in `requirements.txt`:
   - cramjam==2.9.1
   - fastparquet==2024.2.0
   - fsspec==2025.2.0
   - numpy==1.24.4
   - packaging==24.2
   - pandas==2.0.3
   - pyarrow==17.0.0
   - PySide6==6.6.3.1
   - PySide6_Addons==6.6.3.1
   - PySide6_Essentials==6.6.3.1
   - python-dateutil==2.9.0.post0
   - pytz==2025.1
   - PyYAML==6.0.2
   - regex==2024.11.6
   - shiboken6==6.6.3.1
   - six==1.17.0
   - tzdata==2025.1
   - wcwidth==0.2.13
   - wikitextparser==0.56.3

## Usage

### For Non-Technical Users (GUI)

1. Launch the application:
   ```bash
   python main.py
   ```

2. Follow the steps in the GUI:
   - Step 1: Select the compressed XML dump file (*.bz2)
   - Step 2: Select a base directory for output files
   - Step 3: Select your language from the dropdown
   - Step 4: Choose whether to generate a graph
   - Click "Confirm Selection" to start processing

### For Technical Users (Command Line)

Use the command-line interface for automation or batch processing:

```bash
python main.py --dump_filepath /path/to/dump.bz2 --language_code EN --base_dir /path/to/output --generate_graph
```

Options:
- `--dump_filepath`: Path to the compressed Wikipedia XML dump file
- `--language_code`: Language code (EN, ES, GR, PL, IT, NL, EUS, HI, DE)
- `--base_dir`: Base directory for output files (defaults to current directory)
- `--generate_graph`: Flag to generate the graph (optional)

You can also use the installed command-line tool:

```bash
wikidump_processor --dump_filepath /path/to/dump.bz2 --language_code EN --generate_graph
```

## Output

The tool creates the following directory structure:

```
base_dir/
└── language_code/
    ├── output/
    │   └── language_code_WP_titles_texts.parquet
    └── graph/
        ├── redirects_rev_mapping.pkl.gzip
        └── language_code_graph_wiki_cleaned.parquet
```

- `language_code_WP_titles_texts.parquet`: Contains the titles and cleaned text of each Wikipedia article
- `redirects_rev_mapping.pkl.gzip`: Mappings for redirect resolution
- `language_code_graph_wiki_cleaned.parquet`: The final graph representation with Source/Target pairs

## Language Support

MultiLGraphWiki currently supports 9 languages. The language-specific settings are stored in `LANG_SETTINGS.yml`. Each language configuration includes:

- Regular expressions for identifying sections like "References" and "See also"
- Patterns for filtering out non-content pages
- Redirect keywords for identifying redirect pages

To add support for a new language, update the YAML file with the appropriate settings.

## Extending Language Support

To add a new language:

1. Edit `LANG_SETTINGS.yml` and add a new entry with:
   - `section_patt`: Regular expression for identifying reference sections
   - `filter_out_patterns`: Patterns for non-content pages to filter out
   - `redirect_keywords`: Keywords indicating redirect pages

2. Update the language choices in the code (in `main.py` and `gui.py`)

## Technical Details

The processing pipeline consists of:

1. Parsing the XML dump using SAX parsing for memory efficiency
2. Cleaning the text by removing templates, references, and non-content sections
3. Extracting wikilinks from the cleaned text
4. Building a graph representation with articles as nodes and links as edges
5. Resolving redirects to ensure valid connections
6. Removing duplicate edges and self-loops
7. Saving the final graph data in Parquet format

## License

MultiLGraphWiki is licensed under the **Apache License 2.0**.

Under this license, you are free to:

- **Use** the software for any purpose.
- **Modify** and distribute the software.
- **Integrate** it into your own projects.
- **Commercialize** derived works.

However, the following conditions apply:

- **Attribution**: You must provide appropriate credit to the original authors, include the license notice, and indicate if changes were made.
- **No Warranty**: The software is provided "as is," without any express or implied warranties.
- **Patent Grant**: If you contribute to the project, you grant a license to use any of your patents related to the contributed code.

For full details, see the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0).

## Author
Paschalis Agapitos - pasxalisag9@gmail.com

## Acknowledgments
Special thanks to Gustavo Ariel Schwartz, my PhD supervisor, for his valuable insights during the development of the algorithm.