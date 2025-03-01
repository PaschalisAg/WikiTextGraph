import yaml
import re

def load_language_settings(yaml_file="LANG_SETTINGS.yml"):
    """
    Load language-specific settings from a YAML file.

    Args:
        yaml_file (str): Path to the YAML file containing language settings.

    Returns:
        dict: A dictionary of language settings with compiled regex patterns.
    """
    with open(yaml_file, "r", encoding="utf-8") as file:
        language_settings = yaml.safe_load(file)

    # compile regex patterns for section headers in each language
    for lang, settings in language_settings.items():
        settings["section_patt"] = re.compile(
            settings["section_patt"], flags=re.IGNORECASE
        )
    
    return language_settings

    
def get_language_settings(language_code, yaml_file="LANG_SETTINGS.yml"):
    """
    Retrieve settings for a specific language from the YAML configuration.

    Args:
        language_code (str): The language code (e.g., "EN", "ES", "GR", "PL", "IT", "NL", "EUS", "HI", "DE").
        yaml_file (str): Path to the YAML file containing language settings.

    Returns:
        dict: A dictionary containing the language-specific settings.
    """
    language_settings = load_language_settings(yaml_file)
    
    # return the requested language settings, defaulting to English if not found
    return language_settings.get(language_code, language_settings.get("EN", {}))