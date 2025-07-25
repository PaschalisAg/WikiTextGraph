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
    input_file_path = Path(input_file_path)
    graph_output_dir = Path(graph_output_dir)
    graph_output_dir.mkdir(parents=True, exist_ok=True)

    filter_out_patterns = settings["filter_out_patterns"]
    redirect_keywords = [kw.lower() for kw in settings["redirect_keywords"]]
    filter_re = re.compile("|".join(filter_out_patterns), flags=re.IGNORECASE)

    wiki_link_regex = re.compile(
        r"\[\["
        r"([^\|\[\]#]+)"
        r"(?:\|[^\]]+)?"
        r"\]\]"
    )

    parquet_file = pq.ParquetFile(input_file_path)
    all_graph_data = []

    for batch_index, batch in enumerate(parquet_file.iter_batches(batch_size=50_000)):
        df = batch.to_pandas()

        # Remove pages whose titles match filter-out patterns BEFORE exploding
        df = df[~df["title"].apply(lambda s: bool(
            isinstance(s, str) and filter_re.search(s)))]

        df["Redirect_Flag"] = df["text"].str.lower().str.startswith(
            tuple(redirect_keywords)).astype(int)
        df["wikilinks"] = df["text"].apply(
            lambda x: extract_wikilinks(wiki_link_regex, x))

        graph_data = (
            df.explode("wikilinks")
              .rename(columns={"title": "Source", "wikilinks": "Target"})
              .drop(columns=["text"], errors="ignore")
        )

        graph_data["Source"] = graph_data["Source"].apply(fix_dubious_links)
        graph_data["Target"] = graph_data["Target"].apply(fix_dubious_links)
        graph_data["Target"] = graph_data["Target"].apply(
            lambda word: word[0].upper(
            ) + word[1:] if isinstance(word, str) and word else word
        )

        graph_data = graph_data.dropna(subset=["Target"])

        # Normalize section links to self-links
        bool_mask = graph_data["Target"].str.startswith("#")
        graph_data.loc[bool_mask,
                       "Target"] = graph_data.loc[bool_mask, "Source"]

        # Remove links to other language wikis
        lang_link_pattern = r"^[a-zA-Z]{2,3}:"
        graph_data = graph_data[~graph_data["Target"].str.match(
            lang_link_pattern)]

        # Remove self-loops
        graph_data = graph_data[graph_data["Source"] != graph_data["Target"]]

        all_graph_data.append(graph_data)

    final_graph_data = pd.concat(all_graph_data, ignore_index=True)

    redirect_mapping_path = graph_output_dir / "redirects_rev_mapping.pkl.gzip"
    if not redirect_mapping_path.exists():
        reverse_redirect_dict = dict(zip(
            final_graph_data.loc[final_graph_data["Redirect_Flag"]
                                 == 1, "Source"],
            final_graph_data.loc[final_graph_data["Redirect_Flag"]
                                 == 1, "Target"]
        ))
        reverse_redirect_dict = {k: v for k,
                                 v in reverse_redirect_dict.items() if k != v}
        with gzip.open(redirect_mapping_path, "wb") as outp:
            pickle.dump(reverse_redirect_dict, outp,
                        protocol=pickle.HIGHEST_PROTOCOL)
    else:
        with gzip.open(redirect_mapping_path, "rb") as inp:
            reverse_redirect_dict = pickle.load(inp)

    normalised_rev_red_dict = {
        fix_dubious_links(k): fix_dubious_links(v)
        for k, v in reverse_redirect_dict.items()
    }

    final_graph_data["Target"] = resolve_redirects(
        final_graph_data["Target"], normalised_rev_red_dict)
    final_graph_data = final_graph_data[final_graph_data["Source"]
                                        != final_graph_data["Target"]]

    final_graph_data = final_graph_data.drop_duplicates(
        subset=["Source", "Target"], keep="first")
    final_graph_data = final_graph_data[final_graph_data["Redirect_Flag"] != 1].drop(
        "Redirect_Flag", axis=1, errors="ignore")

    set_sources = set(final_graph_data["Source"])
    final_graph_data = final_graph_data[final_graph_data["Target"].isin(
        set_sources)]
    final_graph_data = final_graph_data.dropna(subset=["Source", "Target"])

    combined = pd.concat(
        [final_graph_data["Source"], final_graph_data["Target"]], ignore_index=True)
    labels, uniques = pd.factorize(combined)
    assert len(labels) == 2 * \
        len(final_graph_data), "Mismatch between factorized labels and graph size."
    final_graph_data["Source"] = labels[:len(final_graph_data)]
    final_graph_data["Target"] = labels[len(final_graph_data):]

    mapping_df = pd.DataFrame({"id": range(len(uniques)), "label": uniques})
    mapping_df_path = graph_output_dir / \
        f"{language_code}_id_node_mapping.parquet"
    mapping_df.to_parquet(
        mapping_df_path, engine="fastparquet", compression="gzip")

    graph_output_path = graph_output_dir / \
        f"{language_code}_wiki_graph.parquet"
    final_graph_data.to_parquet(
        graph_output_path, engine="fastparquet", compression="gzip")
    print(f"Graph data saved to {graph_output_path}")