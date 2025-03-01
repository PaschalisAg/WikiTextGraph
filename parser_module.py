import os
import xml.sax
import gc
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import bz2
import yaml
import re
import multiprocessing as mp
from functools import partial
from pathlib import Path
from graph import generate_graph
from utils import extract_wiki_main_text, filter_non_content_pages

def _transform_batch(
    pages,
    section_patt,
    filter_out_patterns,
    redirect_keywords
):
    """
    Clean and transform a batch of Wikipedia pages into a Pandas DataFrame,
    suitable for writing to Parquet.
    """
    if not pages:
        return None

    df = pd.DataFrame(pages)
    df = filter_non_content_pages(df, filter_out_patterns, redirect_keywords)

    # Apply the main-text extraction based on the provided regex pattern
    df['text'] = df['text'].apply(lambda x: extract_wiki_main_text(x, section_patt))

    if df.empty:
        return None

    # Convert DataFrame to an Arrow Table for Parquet writing
    table = pa.Table.from_pandas(df)
    return table

class WikiXmlHandler(xml.sax.handler.ContentHandler):
    """
    SAX handler that accumulates Wikipedia pages and processes them in batches.
    """
    def __init__(
        self,
        batch_size,
        output_file,
        transform_func,
        pool=None
    ):
        """
        Args:
            batch_size (int): Number of pages to accumulate before processing a batch.
            output_file (Path or str): Parquet file to write the cleaned pages.
            transform_func (callable): A function that takes a list of pages and returns an Arrow Table.
            pool (multiprocessing.Pool): Optional pool for parallel transformation.
        """
        super().__init__()
        self._buffer = []
        self._current_tag = None
        self._pages = []
        self.batch_size = batch_size
        self.output_file = Path(output_file)
        self.transform_func = transform_func
        self.pool = pool
        self.parquet_writer = None

    def characters(self, content):
        if self._current_tag:
            self._buffer.append(content)

    def startElement(self, name, attrs):
        if name in ('title', 'text'):
            self._current_tag = name
            self._buffer = []

    def endElement(self, name):
        # If we are closing a <title> or <text>, save the content to self._pages
        if self._current_tag:
            content = ''.join(self._buffer)
            if self._current_tag == 'title':
                # Start a new page record
                self._pages.append({'title': content, 'text': ''})
            elif self._current_tag == 'text' and self._pages:
                # Assign text to the last page
                self._pages[-1]['text'] = content
            self._current_tag = None

        # If we closed a <page> element and we have enough pages, process them
        if name == 'page' and len(self._pages) >= self.batch_size:
            self.process_batch()

    def process_batch(self):
        """Send a batch for transformation and write the result to Parquet."""
        if not self._pages:
            return

        # We'll pass a copy of _pages to the transform function
        pages_batch = list(self._pages)
        self._pages.clear()  # Reset for the next batch

        if self.pool is not None:
            # Parallel approach: run _transform_batch in a worker process
            future = self.pool.apply_async(self.transform_func, (pages_batch,))
            table = future.get()
        else:
            # Fallback: run transformation sequentially
            table = self.transform_func(pages_batch)

        # Write the resulting table
        if table is not None:
            df = table.to_pandas().reset_index(drop=True)  # ✅ Ensure index consistency
            table = pa.Table.from_pandas(df)

            if self.parquet_writer is None:
                self.parquet_writer = pq.ParquetWriter(
                    str(self.output_file),
                    table.schema,
                    compression="gzip"
                )

            self.parquet_writer.write_table(table)

        # Encourage Python to free memory
        gc.collect()


    def close_writer(self):
        """Process any leftover pages and close the Parquet writer."""
        # Process remaining pages that didn't reach batch_size
        if self._pages:
            self.process_batch()

        if self.parquet_writer:
            self.parquet_writer.close()


def load_language_settings(yaml_file="LANG_SETTINGS.yml"):
    """
    Load language-specific settings from a YAML file.
    """
    with open(yaml_file, "r", encoding="utf-8") as file:
        language_settings = yaml.safe_load(file)
    for lang, settings in language_settings.items():
        settings["section_patt"] = re.compile(settings["section_patt"], flags=re.IGNORECASE)
    return language_settings


def get_language_settings(language_code, yaml_file="LANG_SETTINGS.yml"):
    """
    Retrieve settings for a specific language from the YAML configuration.
    """
    language_settings = load_language_settings(yaml_file)
    return language_settings.get(language_code, language_settings["EN"])


def parse_wikidump(
    dump_filepath,
    language_code="EN",
    base_dir=None,
    generate_graph_flag=False,
    num_cores=1 # by default use 1 CPU core in case it's not provided
):

    """
    Main workflow for parsing a Wikipedia dump.
    Optional parallelization: if num_cores > 1, we use multiprocessing for batch processing.
    """
    settings = get_language_settings(language_code)
    section_patt = settings["section_patt"]
    filter_out_patterns = settings.get('filter_out_patterns', [])
    redirect_keywords = settings.get('redirect_keywords', [])

    base_dir = Path(base_dir if base_dir else Path.cwd()).resolve()
    output_dir = base_dir / language_code / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    titles_texts_file = output_dir / f"{language_code}_WP_titles_texts.parquet"

    # Create a partial function for transforming each batch
    transform_func = partial(
        _transform_batch,
        section_patt=section_patt,
        filter_out_patterns=filter_out_patterns,
        redirect_keywords=redirect_keywords
    )

    # Optionally create a multiprocessing pool
    pool = mp.Pool(processes=num_cores) if num_cores > 1 else None

    handler = WikiXmlHandler(
        batch_size=10000,
        output_file=titles_texts_file,
        transform_func=transform_func,
        pool=pool
    )

    parser = xml.sax.make_parser()
    parser.setContentHandler(handler)

    dump_filepath = Path(dump_filepath)
    try:
        with bz2.open(dump_filepath, "rt", encoding="utf-8") as file:
            for line in file:
                parser.feed(line)
    except xml.sax.SAXException:
        pass
    finally:
        # Finish writing any partial batch and close writer
        handler.close_writer()

        # If a pool is being used, close/join it
        if pool is not None:
            pool.close()
            pool.join()

    print(f"Titles and texts saved to {titles_texts_file}")

    # Optionally generate the graph afterwards
    if generate_graph_flag:
        graph_output_dir = os.path.join(base_dir, language_code, "graph")
        os.makedirs(graph_output_dir, exist_ok=True)
        generate_graph(language_code, settings, titles_texts_file, graph_output_dir)
