import yaml
import re
from pathlib import Path


def load_language_settings(yaml_file="LANG_SETTINGS.yml"):
    """
    Loads language-specific settings from a YAML file and compiles regex patterns.

    Args:
        yaml_file (str, optional): Path to the YAML file containing language settings.
            Defaults to "LANG_SETTINGS.yml".

    Returns:
        dict: A dictionary containing language settings with compiled regex patterns.
              Example structure:
              {
                  "en": {
                      "section_patt": <compiled regex>,
                      "filter_out_patterns": [...],
                      "redirect_keywords": [...]
                  },
                  "es": {...},
                  ...
              }
    """
    # convert to a Path object for cross-platform compatibility
    yaml_file = Path(yaml_file).resolve()

    with yaml_file.open("r", encoding="utf-8") as file:
        language_settings = yaml.safe_load(file)

    # compile regex patterns for section headers in each language
    for lang, settings in language_settings.items():
        settings["section_patt"] = re.compile(
            settings["section_patt"], flags=re.IGNORECASE
        )

    return language_settings


def get_language_settings(language_code, yaml_file="LANG_SETTINGS.yml"):
    """
    Retrieves settings for a specific language from the YAML configuration.

    Args:
        language_code (str): The language code (e.g., "en" for English, "es" for Spanish,
                             "el" for Greek, "pl" for Polish, "it" for Italian,
                             "nl" for Dutch, "eu" for Basque, "hi" for Hindi,
                             "de" for German, etc.).
        yaml_file (str, optional): Path to the YAML file containing language settings.
                                   Defaults to "LANG_SETTINGS.yml".

    Returns:
        dict: A dictionary containing the language-specific settings. If the specified
              language is not found, defaults to English ("en").
    """
    language_settings = load_language_settings(yaml_file)

    # return the requested language settings, defaulting to English if not found
    return language_settings.get(language_code, language_settings.get("en", {}))