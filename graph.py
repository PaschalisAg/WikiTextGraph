from pathlib import Path
from typing import Union
import re
import gzip
import pickle
import pandas as pd
import pyarrow.parquet as pq
from utils import extract_wikilinks, resolve_redirects, fix_dubious_links

def generate_graph(
    language_code: str,
    settings: dict,
    input_file_path: Union[str, Path],
    graph_output_dir: Union[str, Path],
    use_string_labels: bool = False
):
    """
    Generates a Wikipedia graph representation from a Parquet file containing
    Wikipedia titles and texts.

    Args:
        language_code (str): The language code for the Wikipedia dump, e.g., "en".
        settings (dict): Language-specific settings, including filter patterns
                         and redirect keywords.
        input_file_path (str | Path): Path to the input Parquet file containing
                                      titles and texts.
        graph_output_dir (str | Path): Path to the directory where the processed
                                       graph data will be stored.
        use_string_labels (bool, optional): If True, the final graph edges use
                                            article titles as strings instead
                                            of numeric IDs. Defaults to False.
    """
    # ensure all paths are Path objects for consistency
    input_file_path = Path(input_file_path)
    graph_output_dir = Path(graph_output_dir)

    # ensure the output directory for graph data exists
    graph_output_dir.mkdir(parents=True, exist_ok=True)

    # extract filter patterns and redirect keywords from settings
    filter_out_patterns = settings['filter_out_patterns']
    redirect_keywords = [kw.lower() for kw in settings['redirect_keywords']]

    # regex pattern for extracting Wikipedia-style wikilinks
    wiki_link_regex = re.compile(
        r'\[\['
        r'([^\|\[\]#]+)'
        r'(?:\|[^\]]+)?'
        r'\]\]'
    )

    parquet_file = pq.ParquetFile(input_file_path)
    all_graph_data = []

    # iterate over the input file in batches
    for batch_index, batch in enumerate(parquet_file.iter_batches(batch_size=50_000)):
        df = batch.to_pandas()

        # normalize the titles and texts
        df['title'] = df['title'].str.lower()
        df['text'] = df['text'].str.lower()

        # check if the text starts with any redirect keyword, case-insensitive
        df['Redirect_Flag'] = df['text'].str.startswith(tuple(redirect_keywords)).astype(int)

        df['wikilinks'] = df['text'].apply(lambda x: extract_wikilinks(wiki_link_regex, x))

        # explode the DataFrame to create "Source" and "Target" columns
        graph_data = (
            df.explode('wikilinks')
              .rename(columns={'title': 'Source', 'wikilinks': 'Target'})
              .drop(columns=['text'], errors='ignore')
        )

        # normalize underscores in both Source and Target columns
        graph_data['Source'] = graph_data['Source'].apply(fix_dubious_links)
        graph_data['Target'] = graph_data['Target'].apply(fix_dubious_links)

        # apply filtering and normalization
        graph_data = graph_data[~graph_data['Source'].str.contains("|".join(filter_out_patterns), flags=re.IGNORECASE, na=False)]
        graph_data = graph_data[~graph_data['Target'].str.contains("|".join(filter_out_patterns), flags=re.IGNORECASE, na=False)]

        # replace NaN in the "Target" column with an empty string
        graph_data = graph_data.dropna(subset=['Target'])

        # detect and handle section links (# links)
        bool_mask = graph_data['Target'].str.startswith('#')
        graph_data.loc[bool_mask, 'Target'] = graph_data.loc[bool_mask, 'Source']

        # remove links to other Wikipedia languages
        pattern = r'^[a-zA-Z]{2,3}:'
        graph_data = graph_data[~graph_data['Target'].str.match(pattern)]

        # detect and handle self-edges
        graph_data = graph_data[graph_data['Source'] != graph_data['Target']]

        # collect the processed batch
        all_graph_data.append(graph_data)

    # concatenate all processed batches into a single DataFrame
    final_graph_data = pd.concat(all_graph_data, ignore_index=True)

    # create reverse redirect dictionary and save or load it
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

    # normalize the reverse redirect dictionary to lowercase
    normalised_rev_red_dict = {k.lower(): v.lower() for k, v in reverse_redirect_dict.items()}
    normalised_rev_red_dict = {fix_dubious_links(k.lower()): fix_dubious_links(v.lower()) for k, v in reverse_redirect_dict.items()}

    # resolve redirects in the 'Target' column
    final_graph_data['Target'] = resolve_redirects(final_graph_data['Target'], normalised_rev_red_dict)

    # remove rows where Source and Target are identical (self-loops) after redirect resolution
    final_graph_data = final_graph_data[final_graph_data['Source'] != final_graph_data['Target']]

    # drop duplicate rows but keep the first occurrence
    final_graph_data = final_graph_data.drop_duplicates(subset=['Source', 'Target'], keep='first')
    final_graph_data = final_graph_data[final_graph_data['Redirect_Flag'] != 1].drop('Redirect_Flag', axis=1, errors='ignore')

    # remove Target values that do not appear as Source values
    set_sources = set(final_graph_data['Source'])
    final_graph_data = final_graph_data[final_graph_data['Target'].isin(set_sources)]

    # remove rows with null values in either the 'Source' or 'Target' columns
    final_graph_data = final_graph_data.dropna(subset=['Source', 'Target'])
    # factorize the string labels into numeric IDs for more efficient representation
    combined = pd.concat([final_graph_data['Source'], final_graph_data['Target']], ignore_index=True)
    labels, uniques = pd.factorize(combined)
    assert len(labels) == 2 * len(final_graph_data), "Mismatch between factorized labels and graph size."
    final_graph_data['Source'] = labels[:len(final_graph_data)]  # first half are the source labels
    final_graph_data['Target'] = labels[len(final_graph_data):]  # second half are the target labels
    # create a mapping from numeric ID to string label for possible future use and for easier replacement
    mapping_df = pd.DataFrame({'id': range(len(uniques)), 'label': uniques})
    mapping_df_path = graph_output_dir / f"{language_code}_id_node_mapping.parquet"
    mapping_df.to_parquet(mapping_df_path, engine='fastparquet', compression='gzip')
    
    # save graph
    graph_output_path = graph_output_dir / f"{language_code}_wiki_graph.parquet"
    final_graph_data.to_parquet(graph_output_path, engine='fastparquet', compression='gzip')
    print(f"Graph data saved to {graph_output_path}")