import re
import wikitextparser as wtp
import pandas as pd
from typing import Pattern, List


# regex for matching <ref> tags (references) in Wikipedia pages
refs_patt = re.compile(r'<\s*ref\b[^>]*\/\s*>|<\s*ref\b[^>]*>.*?<\s*\/\s*ref\s*>', flags=re.DOTALL)

# regex for matching HTML comments in Wikipedia pages (e.g., <!-- This is a comment --> but < !-- This is also a comment -- >)
comments_patt = re.compile(r'< !--[\s\S]*?-- >|<!--[\s\S]*?-->', flags=re.DOTALL)


# regex to find the beginning of the main text (e.g., bolded text)
beginning_of_main_text_patt = re.compile(r"'''(.*?)'''")


def remove_templates(parsed: wtp.WikiText, cleaned_text: str) -> str:
    """
    Removes all template instances from the parsed wikitext string.

    A template in Wikipedia syntax is typically enclosed in double curly braces,
    e.g., `{{Infobox person}}`, `{{Citation needed}}`, etc. This function removes
    such templates from the given `cleaned_text` by iterating over the parsed
    `wtp.WikiText` object and removing any matching template content.

    Args:
        parsed (wtp.WikiText): A WikiTextParser-parsed object containing structured
            information about the wikitext, including its templates.
        cleaned_text (str): The original wikitext content in string form from which
            templates are to be removed.

    Returns:
        str: The `cleaned_text` with all templates found in `parsed.templates` removed.

    Example:
        >>> import wikitextparser as wtp
        >>> raw_text = "Barack Obama was the 44th president of the United States. {{Infobox person}}"
        >>> parsed = wtp.parse(raw_text)
        >>> result = remove_templates(parsed, raw_text)
        >>> print(result)
        'Barack Obama was the 44th president of the United States. '

    Notes:
        This function only removes exact string matches of the templates present in
        `parsed.templates`. If the `cleaned_text` was modified before this step (e.g.,
        whitespace normalized), template strings may not match exactly and remain.
    """
    for template in parsed.templates:
        cleaned_text = cleaned_text.replace(str(template), '')
    return cleaned_text



def extract_wiki_main_text(wiki_text: str, section_patt: Pattern) -> str:
    """
    Cleans and extracts the main body text from raw Wikipedia markup.

    This function processes raw wikitext in four steps:
    1. Splits the article into an intro block (everything before the first ``==`` section
       heading) and the remaining body. This prevents template removal from creating
       orphaned bold-text fragments in later sections that would otherwise be mistaken
       for the article's opening line.
    2. Cleans the intro block by removing templates (e.g., ``{{Infobox}}``),
       ``<ref>...</ref>`` tags, and HTML comments (``<!-- ... -->``).
    3. Optionally trims any leading junk in the intro by seeking the first bolded phrase
       (``'''...'''``), but only if that match falls within the first 30% of the intro
       text. This preserves articles whose introductions do not open with a bolded title.
    4. Re-joins the cleaned intro with the remaining body, then cuts the combined text
       at the first non-main section matched by ``section_patt`` (e.g., "References",
       "See also"). Finally, cleans up ``& nbsp;`` entities and excess whitespace.

    Args:
        wiki_text (str): The full Wikipedia article source text in wikitext format.
        section_patt (Pattern): A compiled regular expression used to identify the start
            of non-main sections (such as ``== References ==``) to trim off extraneous
            content.

    Returns:
        str: A cleaned string containing the main article content, without templates,
        references, comments, or trailing non-main sections.

    Example:
        >>> import re
        >>> import wikitextparser as wtp
        >>> from my_module import extract_wiki_main_text
        >>> wiki_markup = '''
        {{Infobox person}}
        \'\'\'Barack Obama\'\'\' was the 44th president of the United States.
        <ref>Some citation</ref>
        == References ==
        <ref>Another citation</ref>
        '''
        >>> section_patt = re.compile(r'==\\s*(References|See also|External links)\\s*==', re.IGNORECASE)
        >>> cleaned = extract_wiki_main_text(wiki_markup, section_patt)
        >>> print(cleaned)
        "\'\'\'Barack Obama\'\'\' was the 44th president of the United States."

    Notes:
        - Template removal is applied only to the intro block, not to the full article,
          so that bold-text fragments inside section bodies do not affect intro detection.
        - The 30% threshold for bold-text trimming is a heuristic. Articles whose first
          bold phrase appears later than that (e.g., long preambles without a bolded
          subject) will have their intro preserved in full.
        - Assumes the `remove_templates` function is available and that the following
          global regex patterns exist in scope:
            - `refs_patt`: pattern for <ref> tags
            - `comments_patt`: pattern for HTML comments
            - `beginning_of_main_text_patt`: pattern to find the main bolded subject line.
        - The regex patterns must be compiled prior to calling this function.
    """
    # Step 1: Split article into intro (before first ==) and rest
    # This avoids detecting orphaned bold text from removed templates
    first_section_match = re.search(r'^==', wiki_text, flags=re.MULTILINE)
    
    if first_section_match:
        intro_text = wiki_text[:first_section_match.start()]
        rest_text = wiki_text[first_section_match.start():]
    else:
        # No sections found, entire article is intro
        intro_text = wiki_text
        rest_text = ""
    
    # Step 2: Clean the intro section
    parsed = wtp.parse(intro_text)
    cleaned_intro = intro_text
    
    # Remove templates (before other operations to avoid creating orphaned bold text)
    cleaned_intro = remove_templates(parsed, cleaned_intro)
    
    # Remove <ref> tags
    cleaned_intro = re.sub(refs_patt, '', cleaned_intro)
    
    # Remove HTML comments
    cleaned_intro = re.sub(comments_patt, '', cleaned_intro)
    
    # Step 3: Use bold-text detection only if intro has leading junk
    # (e.g., leftover metadata)
    beginning_of_main_text = beginning_of_main_text_patt.search(cleaned_intro)
    if beginning_of_main_text:
        # Only trim if the match is reasonably early (not the bulk of content)
        match_start = beginning_of_main_text.start()
        if match_start < len(cleaned_intro) * 0.3:  # Less than 30% into the text
            cleaned_intro = cleaned_intro[match_start:]
    
    # Step 4: Check if we need to cut off trailing non-main sections
    combined_text = cleaned_intro + rest_text
    end_main_text = section_patt.search(combined_text)
    if end_main_text:
        end_index = end_main_text.start()
        combined_text = combined_text[:end_index]
    
    combined_text = combined_text.replace('& nbsp;', '').replace('.  ', '. ').replace(',  ', ', ')
    
    return combined_text.strip()


def filter_non_content_pages(df: pd.DataFrame, filter_out_patterns: List[str], redirect_keywords: List[str]) -> pd.DataFrame:
    """
    Filters out non-content Wikipedia pages from a DataFrame based on title patterns 
    and known redirect keywords.

    This function is useful for cleaning a Wikipedia article dataset by removing entries
    such as user pages, talk pages, file/image pages, or redirects that are not part of
    encyclopedic content. It filters rows where the `title` column matches any of the 
    given regular expression patterns. Although `redirect_keywords` is currently unused,
    it is included for future extensibility (e.g., filtering based on content indicating redirects).

    Args:
        df (pd.DataFrame): A pandas DataFrame with at least a 'title' column representing article titles.
        filter_out_patterns (List[str]): A list of regular expression patterns to match titles 
            that should be excluded (e.g., ["^User:", "^Talk:", "^File:"]).
        redirect_keywords (List[str]): A list of known redirect keywords that might be used 
            for future filtering (currently not applied in the function).

    Returns:
        pd.DataFrame: A filtered DataFrame containing only valid content pages.

    Example:
        >>> import pandas as pd
        >>> data = {
        ...     "title": ["Barack Obama", "User:Example", "Talk:Climate Change", "Python (programming language)"],
        ...     "text": ["Obama content", "User page", "Talk page", "Python content"]
        ... }
        >>> df = pd.DataFrame(data)
        >>> filter_patterns = ["^User:", "^Talk:"]
        >>> redirect_keywords = []  # currently unused
        >>> filtered_df = filter_non_content_pages(df, filter_patterns, redirect_keywords)
        >>> print(filtered_df)
                               title              text
        0              Barack Obama     Obama content
        3  Python (programming language)  Python content

    Notes:
        - Only filters based on the `title` column.
        - This function does not yet use `redirect_keywords`; these may be used to
          exclude rows based on the article text or metadata in future updates.
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
    Extracts all Wikipedia-style internal links from the given wikitext using a provided regex pattern.

    Wikipedia internal links are typically formatted as:
    - [[Page Title]]
    - [[Page Title|Display Text]]
    - [[Page Title#Section]]
    
    This function returns the base page titles only, ignoring display text and section references.

    Args:
        wiki_link_regex (Pattern): A compiled regular expression used to match wikilinks.
            Example pattern:
                re.compile(
                    r'\[\['
                    r'([^\|\[\]#]+)'
                    r'(?:\|[^\]]+)?'
                    r'\]\]'
                )
            This captures the page title before a pipe `|` or hash `#`, if present.

        input_text (str): A string containing raw Wikipedia markup text.

    Returns:
        List[str]: A list of extracted Wikipedia page titles (without pipes, sections, or display overrides).

    Example:
        >>> import re
        >>> wiki_link_regex = re.compile(
        ...     r'\[\['
        ...     r'([^\|\[\]#]+)'
        ...     r'(?:\|[^\]]+)?'
        ...     r'\]\]'
        ... )
        >>> text = "This article links to [[Barack Obama]], [[Python (programming language)|Python]], and [[Climate change#Impacts]]."
        >>> extract_wikilinks(wiki_link_regex, text)
        ['Barack Obama', 'Python (programming language)', 'Climate change']

    Notes:
        - Only the page titles are returned; section links and alternative display texts are stripped.
        - If a link includes a hash (e.g., `[[Article#Section]]`), the function returns only `Article`.
    """
    matches = wiki_link_regex.findall(input_text)
    return matches


def fix_dubious_links(link: str) -> str:
    """
    Normalizes Wikipedia-style links by replacing underscores with spaces.

    This function is useful for cleaning links that use underscores to represent spaces,
    which is common in Wikipedia page titles or internal link structures. If the input
    is not a string or is NaN (missing), it returns the input unchanged.

    Args:
        link (str): A Wikipedia link string (e.g., "Barack_Obama") to be normalized.

    Returns:
        str: The normalized link with underscores replaced by spaces. If input is not a
        string or is missing (NaN), the original input is returned.

    Example:
        >>> fix_dubious_links("Barack_Obama")
        'Barack Obama'

        >>> fix_dubious_links("Python_(programming_language)")
        'Python (programming language)'

        >>> fix_dubious_links(None)
        None

        >>> fix_dubious_links(42)
        42

    Notes:
        - This is a simple orthographic fix. It does not handle URL encoding,
          capitalization normalization, or other forms of text cleaning.
    """
    if pd.isna(link) or not isinstance(link, str):
        return link
    return link.replace('_', ' ')


def resolve_redirects(target_series: pd.Series, reverse_redirect_dict: dict) -> pd.Series:
    """
    Resolves redirects in a pandas Series of Wikipedia article titles using a 
    reverse redirect dictionary.

    Wikipedia pages often redirect to canonical or updated article titles. This 
    function replaces redirect titles in a Series with their final target titles 
    based on the provided mapping.

    Args:
        target_series (pd.Series): A pandas Series containing Wikipedia article links or titles.
        reverse_redirect_dict (dict): A dictionary where keys are redirect titles and 
            values are their canonical destination titles.

    Returns:
        pd.Series: A Series with the same shape as `target_series`, where each redirect 
        title has been replaced with its resolved target (if available).

    Example:
        >>> import pandas as pd
        >>> redirects = {
        ...     "USA": "United States",
        ...     "UK": "United Kingdom",
        ...     "COVID-19 pandemic": "Coronavirus pandemic"
        ... }
        >>> links = pd.Series(["USA", "Barack Obama", "UK", "COVID-19 pandemic"])
        >>> resolved = resolve_redirects(links, redirects)
        >>> print(resolved)
        0        United States
        1        Barack Obama
        2      United Kingdom
        3    Coronavirus pandemic
        dtype: object

    Notes:
        - Titles not present in the redirect dictionary remain unchanged.
        - Assumes exact case-sensitive matches for redirect keys.
    """
    return target_series.apply(lambda target: reverse_redirect_dict.get(target, target))