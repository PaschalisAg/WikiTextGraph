import re
import wikitextparser as wtp
import pandas as pd
from typing import Pattern, List


# regex for matching <ref> tags (references) in Wikipedia pages
refs_patt = re.compile(r'<\s*ref\b[^>]*\/\s*>|<\s*ref\b[^>]*>.*?<\s*\/\s*ref\s*>', flags=re.DOTALL)

# regex for matching HTML comments in Wikipedia pages (e.g., <!-- This is a comment -->)
comments_patt = re.compile(r'< !--[\s\S]*?-- >|<!--[\s\S]*?-->', flags=re.DOTALL)


# regex to find the beginning of the main text (e.g., bolded text)
beginning_of_main_text_patt = re.compile(r"'''(.*?)'''")


def remove_templates(parsed: wtp.WikiText, cleaned_text: str) -> str:
    """
    Removes templates from the parsed wikitext.

    Args:
        parsed (wtp.WikiText): The parsed Wikipedia text.
        cleaned_text (str): The original cleaned text.

    Returns:
        str: Text with templates removed.
    """
    for template in parsed.templates:
        cleaned_text = cleaned_text.replace(str(template), '')
    return cleaned_text


def extract_wiki_main_text(wiki_text: str, section_patt: Pattern) -> str:
    """
    Cleans and extracts the main text from the raw Wikipedia markup.

    Args:
        wiki_text (str): The raw Wikipedia text.
        section_patt (Pattern): A regex pattern used to detect section breaks.

    Returns:
        str: The cleaned main text.
    """
    parsed = wtp.parse(wiki_text)
    cleaned_text = wiki_text

    # remove templates
    cleaned_text = remove_templates(parsed, cleaned_text)

    # remove <ref> tags
    cleaned_text = re.sub(refs_patt, '', cleaned_text)

    # remove HTML comments
    cleaned_text = re.sub(comments_patt, '', cleaned_text)

    # trim text before the main bolded section
    beginning_of_main_text = beginning_of_main_text_patt.search(cleaned_text)
    if beginning_of_main_text:
        begin_index = beginning_of_main_text.start()
        cleaned_text = cleaned_text[begin_index:]

    # remove text after sections usually at the end (References, See also, etc.)
    end_main_text = section_patt.search(cleaned_text)
    if end_main_text:
        end_index = end_main_text.start()
        cleaned_text = cleaned_text[:end_index]
    
    cleaned_text = cleaned_text.replace('& nbsp;', '').replace('.  ', '. ').replace(',  ', ', ')
    
    return cleaned_text.strip()


def filter_non_content_pages(df: pd.DataFrame, filter_out_patterns: List[str], redirect_keywords: List[str]) -> pd.DataFrame:
    """
    Removes non-content pages by filtering out certain title patterns or redirect keywords.

    Args:
        df (pd.DataFrame): The DataFrame containing Wikipedia articles.
        filter_out_patterns (List[str]): List of regex patterns to filter out pages.
        redirect_keywords (List[str]): List of known redirect keywords.

    Returns:
        pd.DataFrame: A DataFrame with non-content pages removed.
    """
    if not filter_out_patterns:
        filter_out_patterns = []
    if not redirect_keywords:
        redirect_keywords = []

    # remove pages whose titles match any of the filter-out patterns (e.g., "^user:", "^talk:", etc.)
    if filter_out_patterns:
        df = df[~df['title'].str.contains("|".join(filter_out_patterns), flags=re.IGNORECASE, na=False)]

    return df


def extract_wikilinks(wiki_link_regex: Pattern, input_text: str) -> List[str]:
    """
    Extracts all Wikipedia-style links from the given text.

    Args:
        wiki_link_regex (Pattern): The regex pattern used to find wikilinks.
        input_text (str): The input Wikipedia text.

    Returns:
        List[str]: A list of extracted Wikipedia links.
    """
    matches = wiki_link_regex.findall(input_text)
    return matches


def fix_dubious_links(link: str) -> str:
    """
    Fixes dubious links by normalizing orthography.

    Args:
        link (str): The link to be normalized.

    Returns:
        str: The cleaned link with underscores replaced by spaces.
    """
    if pd.isna(link) or not isinstance(link, str):
        return link
    return link.replace('_', ' ')


def resolve_redirects(target_series: pd.Series, reverse_redirect_dict: dict) -> pd.Series:
    """
    Resolves redirects in the 'Target' column using a reverse redirect dictionary.

    Args:
        target_series (pd.Series): The Series containing Wikipedia article links.
        reverse_redirect_dict (dict): A dictionary mapping redirects to their final destinations.

    Returns:
        pd.Series: The updated Series with resolved redirects.
    """
    return target_series.apply(lambda target: reverse_redirect_dict.get(target, target))