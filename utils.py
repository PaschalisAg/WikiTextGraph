import re
import wikitextparser as wtp
import pandas as pd
from typing import List

# Regex for matching <ref> tags (references) in Wikipedia pages
refs_patt = re.compile(r'<\s*ref\b[^>]*\/\s*>|<\s*ref\b[^>]*>.*?<\s*\/\s*ref\s*>', flags=re.DOTALL)
# Regex for matching HTML comments in Wikipedia pages
comments_patt = re.compile(r'<!--.*?-->', flags=re.DOTALL)
# Regex to find the beginning of the main text (e.g., bolded text)
beginning_of_main_text_patt = re.compile(r"'''(.*?)'''")


def remove_templates(parsed: wtp.WikiText, cleaned_text: str) -> str:
    """
    Remove all templates from Wikipedia text.
    
    Args:
        parsed (wtp.WikiText): Parsed wiki text.
        cleaned_text (str): Original text before removal.
    
    Returns:
        str: Cleaned text with templates removed.
    """
    for template in parsed.templates:
        cleaned_text = cleaned_text.replace(str(template), '')
    return cleaned_text


def extract_wiki_main_text(wiki_text: str, section_patt: re.Pattern) -> str:
    """
    Clean and extract the main text from the raw wiki markup.
    
    Args:
        wiki_text (str): Raw Wikipedia markup text.
        section_patt (re.Pattern): Regex pattern to find end sections.
    
    Returns:
        str: Cleaned main Wikipedia text.
    """
    parsed = wtp.parse(wiki_text)
    cleaned_text = wiki_text
    
    # Remove templates
    cleaned_text = remove_templates(parsed, cleaned_text)
    # Remove <ref> tags
    cleaned_text = re.sub(refs_patt, '', cleaned_text)
    # Remove HTML comments
    cleaned_text = re.sub(comments_patt, '', cleaned_text)
    
    # Trim text before the main bolded section
    beginning_of_main_text = beginning_of_main_text_patt.search(cleaned_text)
    if beginning_of_main_text:
        begin_index = beginning_of_main_text.start()
        cleaned_text = cleaned_text[begin_index:]
    
    # Remove text after sections usually at the end (References, See also, etc.)
    end_main_text = section_patt.search(cleaned_text)
    if end_main_text:
        end_index = end_main_text.start()
        cleaned_text = cleaned_text[:end_index]
    
    return cleaned_text.strip()


def filter_non_content_pages(df: pd.DataFrame, filter_out_patterns: List[str], redirect_keywords: List[str]) -> pd.DataFrame:
    """
    Remove non-content pages based on title patterns or known redirects.
    
    Args:
        df (pd.DataFrame): Dataframe containing Wikipedia page titles and text.
        filter_out_patterns (List[str]): List of patterns to exclude pages.
        redirect_keywords (List[str]): List of redirect keywords.
    
    Returns:
        pd.DataFrame: Filtered dataframe with only content pages.
    """
    if not filter_out_patterns:
        filter_out_patterns = []
    if not redirect_keywords:
        redirect_keywords = []
    
    if filter_out_patterns:
        df = df[~df['title'].str.contains("|".join(filter_out_patterns), flags=re.IGNORECASE, na=False)]
    
    return df


def extract_wikilinks(wiki_link_regex: re.Pattern, input_text: str) -> List[str]:
    """
    Extract Wikipedia links from the text while ensuring multiple links are captured.
    
    Args:
        wiki_link_regex (re.Pattern): Compiled regex for extracting links.
        input_text (str): Text to extract links from.
    
    Returns:
        List[str]: Extracted Wikipedia links.
    """
    return wiki_link_regex.findall(input_text)


def fix_dubious_links(link: str) -> str:
    """
    Normalize dubious links by replacing underscores with spaces.
    
    Args:
        link (str): Wikipedia link.
    
    Returns:
        str: Normalized link.
    """
    if pd.isna(link) or not isinstance(link, str):
        return link
    return link.replace('_', ' ')


def resolve_redirects(target_series: pd.Series, reverse_redirect_dict: dict) -> pd.Series:
    """
    Resolve redirects in the 'Target' column using a reverse redirect dictionary.
    
    Args:
        target_series (pd.Series): Pandas series containing Wikipedia targets.
        reverse_redirect_dict (dict): Dictionary mapping redirects to their final target.
    
    Returns:
        pd.Series: Series with resolved redirects.
    """
    return target_series.apply(lambda target: reverse_redirect_dict.get(target, target))
