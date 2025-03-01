import re
import gzip
import pickle
import pandas as pd
import pyarrow.parquet as pq
import multiprocessing as mp
from pathlib import Path
from functools import partial

from utils import extract_wikilinks, resolve_redirects

def _process_chunk(
    df,
    wiki_link_regex,
    filter_out_patterns,
    redirect_keywords
):
    """
    Process a single Pandas DataFrame chunk, returning the cleaned
    graph edges (Source/Target) for that chunk.
    """
    # Convert titles/text to lowercase
    df['title'] = df['title'].str.lower()
    df['text'] = df['text'].str.lower()

    # Check if the text starts with any redirect keyword, case-insensitive
    df['Redirect_Flag'] = df['text'].str.startswith(tuple(redirect_keywords)).astype(int)

    # Extract wikilinks
    df['wikilinks'] = df['text'].apply(lambda x: extract_wikilinks(wiki_link_regex, x))

    # Explode to create "Source" and "Target"
    graph_data = (
        df.explode('wikilinks')
          .rename(columns={'title': 'Source', 'wikilinks': 'Target'})
          .drop(columns=['text'], errors='ignore')
    )

    # Filter out patterns from Source/Target
    pattern_union = "|".join(filter_out_patterns)
    graph_data = graph_data[
        ~graph_data['Source'].str.contains(pattern_union, flags=re.IGNORECASE, na=False)
        & ~graph_data['Target'].str.contains(pattern_union, flags=re.IGNORECASE, na=False)
    ]

    # Drop NaN in the Target column
    graph_data = graph_data.dropna(subset=['Target'])

    # If Target is a section-only link (starts with '#'), treat it as a self-link to Source
    bool_mask = graph_data['Target'].str.startswith('#')
    graph_data.loc[bool_mask, 'Target'] = graph_data.loc[bool_mask, 'Source']

    # Remove links to other language wikis (e.g. "en:", "fr:", etc.)
    pattern_lang = r'^[a-zA-Z]{2,3}:'
    graph_data = graph_data[~graph_data['Target'].str.match(pattern_lang)]

    # Remove trivial self-edges (where Source == Target)
    graph_data = graph_data[graph_data['Source'] != graph_data['Target']]

    # Return the processed chunk
    return graph_data


def generate_graph(language_code, 
                   settings, 
                   input_file_path, 
                   graph_output_dir, 
                   num_cores=1):
    """
    Generate a graph representation from a single file containing Wikipedia
    titles and texts, using parallel chunk processing if num_cores > 1.

    Args:
        language_code (str): The language code for the Wikipedia dump.
        settings (dict): Language-specific settings, including filter patterns and redirect keywords.
        input_file_path (str): Path to the input file containing titles and texts.
        graph_output_dir (str): Path to the directory where graph data should be stored.
        num_cores (int): Number of CPU cores to use for parallel processing; by default 1 unless other provided.
    """
    # Convert paths to pathlib.Path objects
    graph_output_dir = Path(graph_output_dir)
    input_file_path = Path(input_file_path)
    graph_output_dir.mkdir(parents=True, exist_ok=True)

    # Extract filter out patterns and redirect keywords
    filter_out_patterns = settings['filter_out_patterns']
    redirect_keywords = [kw.lower() for kw in settings['redirect_keywords']]

    # Compile regex for wikilinks
    wiki_link_regex = re.compile(
        r'\[\['
        r'([^\|\[\]#]+)'     # Capture the Wikipedia page title
        r'(?:\|[^\]]+)?'     # Ignore display text or sections if present
        r'\]\]'
    )

    # Read Parquet file in chunks
    parquet_file = pq.ParquetFile(input_file_path)

    # Collect DataFrames (or process them on the fly). 
    # For large dumps, you may want a streaming approach; 
    # here we gather them to demonstrate parallel map usage.
    dataframes = []
    for batch_index, batch in enumerate(parquet_file.iter_batches(batch_size=100_000)):
        df_batch = batch.to_pandas()
        dataframes.append(df_batch)

    # Prepare the partial function for parallel processing
    process_func = partial(
        _process_chunk,
        wiki_link_regex=wiki_link_regex,
        filter_out_patterns=filter_out_patterns,
        redirect_keywords=redirect_keywords
    )

    if num_cores > 1:
        # Use multiprocessing to speed up chunk processing
        with mp.Pool(processes=num_cores) as pool:
            all_graph_data = pool.map(process_func, dataframes)
    else:
        # Fallback to sequential processing if only one core is requested
        all_graph_data = [process_func(df) for df in dataframes]

    # Concatenate all processed batches
    final_graph_data = pd.concat(all_graph_data, ignore_index=True)

    # --------------------- Global Steps Follow --------------------- #
    # 1) Build or load reverse redirect dictionary
    redirect_mapping_path = graph_output_dir / 'redirects_rev_mapping.pkl.gzip'
    if not redirect_mapping_path.exists():
        reverse_redirect_dict = dict(zip(
            final_graph_data.loc[final_graph_data['Redirect_Flag'] == 1, 'Source'],
            final_graph_data.loc[final_graph_data['Redirect_Flag'] == 1, 'Target']
        ))
        reverse_redirect_dict = {k: v for k, v in reverse_redirect_dict.items() if k != v}
        with gzip.open(redirect_mapping_path, 'wb') as outp:
            pickle.dump(reverse_redirect_dict, outp, protocol=pickle.HIGHEST_PROTOCOL)
    else:
        with gzip.open(redirect_mapping_path, 'rb') as inp:
            reverse_redirect_dict = pickle.load(inp)

    # Normalize the reverse redirect dictionary
    normalised_rev_red_dict = {k.lower(): v.lower() for k, v in reverse_redirect_dict.items()}

    # 2) Resolve redirects
    final_graph_data['Target'] = resolve_redirects(final_graph_data['Target'], normalised_rev_red_dict)

    # 3) Remove new self-loops (where Source == Target after redirect resolution)
    final_graph_data = final_graph_data[final_graph_data['Source'] != final_graph_data['Target']]

    # 4) Drop duplicates
    final_graph_data = final_graph_data.drop_duplicates(subset=['Source', 'Target'], keep='first')

    # 5) Remove entries where Redirect_Flag == 1 and remove the flag column
    final_graph_data = final_graph_data[final_graph_data['Redirect_Flag'] != 1].drop('Redirect_Flag', axis=1, errors='ignore')

    # 6) Remove Target values that do not appear as Source values (global check)
    set_sources = set(final_graph_data['Source'])
    final_graph_data = final_graph_data[final_graph_data['Target'].isin(set_sources)]

    # 7) Remove null values in Source/Target columns
    final_graph_data = final_graph_data.dropna(subset=['Source', 'Target'])

    # 8) Save to disk
    graph_parquet_path = graph_output_dir / f"{language_code}_graph_wiki_cleaned.parquet"
    final_graph_data.to_parquet(graph_parquet_path, engine='fastparquet', compression='gzip')

    print(f"Graph data saved to {graph_parquet_path}")