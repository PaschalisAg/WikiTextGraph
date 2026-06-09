import xml.sax
import gc
import codecs
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import bz2
import yaml
import re
from pathlib import Path
from graph import generate_graph
from utils import extract_wiki_main_text, filter_non_content_pages


class WikiXmlHandler(xml.sax.handler.ContentHandler):
    """
    SAX handler that accumulates pages in memory and processes them in batches.

    Attributes:
        batch_size (int): Number of Wikipedia pages to process in each batch.
        output_file (Path): Path to the output Parquet file.
        section_patt (Pattern): Compiled regex pattern to locate section breaks.
        filter_out_patterns (list): Patterns to filter out unwanted pages.
        redirect_keywords (list): Keywords used to detect redirects.
    """

    def __init__(self, batch_size, output_file, section_patt, filter_out_patterns=None, redirect_keywords=None):
        """
        Initializes the SAX handler.

        Args:
            batch_size (int): Number of Wikipedia pages to process per batch.
            output_file (str | Path): Path to the output Parquet file.
            section_patt (Pattern): Compiled regex pattern for detecting section headers.
            filter_out_patterns (list, optional): Patterns to exclude pages. Defaults to None.
            redirect_keywords (list, optional): Keywords indicating redirects. Defaults to None.
        """
        super().__init__()
        self._buffer = []
        self._current_tag = None
        self._pages = []
        self.batch_size = batch_size
        self.output_file = Path(output_file)  # ensure correct path handling
        self.section_patt = section_patt

        self.filter_out_patterns = filter_out_patterns if filter_out_patterns else []
        self.redirect_keywords = [kw.lower() for kw in (redirect_keywords if redirect_keywords else [])]

        self.parquet_writer = None

    def characters(self, content):
        """Accumulates characters within an XML tag."""
        if self._current_tag:
            self._buffer.append(content)

    def startElement(self, name, attrs):
        """Detects the start of relevant XML elements (title, text)."""
        if name in ('title', 'text'):
            self._current_tag = name
            self._buffer = []

    def endElement(self, name):
        """Processes elements at the end of an XML tag and stores relevant data."""
        if self._current_tag:
            content = ''.join(self._buffer)
            if self._current_tag == 'title':
                self._pages.append({'title': content, 'text': ''})
            elif self._current_tag == 'text' and self._pages:
                self._pages[-1]['text'] = content
            self._current_tag = None

        if name == 'page':
            if len(self._pages) >= self.batch_size:
                self.process_batch()

    def process_batch(self):
        """
        Processes a batch of Wikipedia pages, filtering out non-content pages,
        extracting the main text, and saving the results in Parquet format.
        """
        if not self._pages:
            return

        df = pd.DataFrame(self._pages)
        df = filter_non_content_pages(df, self.filter_out_patterns, self.redirect_keywords)
        df['text'] = df['text'].apply(lambda x: extract_wiki_main_text(x, self.section_patt))

        if not df.empty:
            table = pa.Table.from_pandas(df, preserve_index=False)
            # table = pa.Table.from_pandas(df)
            if self.parquet_writer is None:
                self.parquet_writer = pq.ParquetWriter(str(self.output_file), table.schema, compression="gzip")
            self.parquet_writer.write_table(table)

        self._pages.clear()
        gc.collect()

    def close_writer(self):
        """Closes the Parquet writer to ensure data integrity."""
        if self.parquet_writer:
            self.parquet_writer.close()


def load_language_settings(yaml_file="LANG_SETTINGS.yml"):
    """
    Loads language-specific settings from a YAML file.

    Args:
        yaml_file (str | Path): Path to the YAML file containing language settings.

    Returns:
        dict: A dictionary with language-specific settings, including regex patterns.
    """
    yaml_file = Path(yaml_file)
    with yaml_file.open("r", encoding="utf-8") as f:
        language_settings = yaml.safe_load(f)
    for lang, settings in language_settings.items():
        settings["section_patt"] = re.compile(settings["section_patt"], flags=re.IGNORECASE)
    return language_settings


def get_language_settings(language_code, yaml_file="LANG_SETTINGS.yml"):
    """
    Retrieves settings for a specific language from the YAML configuration.

    Args:
        language_code (str): The language code (e.g., "en", "es", "el", "pl").
        yaml_file (str | Path): Path to the YAML file containing language settings.

    Returns:
        dict: A dictionary containing the language-specific settings.
    """
    language_settings = load_language_settings(yaml_file)
    return language_settings.get(language_code, language_settings["en"])


def _find_next_bz2_header(data, raw_file, read_size):
    """
    Scan forward through *data* (and then the raw file) to locate the next
    bz2 stream header (magic bytes ``BZh`` followed by a block-size digit 1-9).

    Returns the data starting at the header, or an empty bytes object if
    no further header is found.
    """
    while True:
        pos = 1  # skip position 0 to avoid re-matching the broken header
        while True:
            idx = data.find(b'BZh', pos)
            if idx < 0:
                break
            if idx + 3 < len(data) and 49 <= data[idx + 3] <= 57:  # '1'..'9'
                return data[idx:]
            pos = idx + 1
        data = raw_file.read(read_size)
        if not data:
            return b''


def _iter_multistream_bz2(filepath, read_size=65536):
    """
    Decompress a multistream bz2 file, yielding chunks of raw bytes.

    Wikipedia's ``-pages-articles-multistream.xml.bz2`` dumps consist of many
    independent bz2 streams concatenated together.  Python's ``bz2.BZ2File``
    relies on the platform ``libbz2`` to handle stream boundaries, and some
    builds (notably the one shipped with macOS) choke at those boundaries.

    This function drives ``bz2.BZ2Decompressor`` directly, creating a fresh
    decompressor for each stream.  If a stream is corrupted it scans forward
    for the next valid ``BZh`` header and resumes, so a single bad block does
    not abort the entire dump.
    """
    with open(filepath, 'rb') as raw:
        buf = b''

        while True:
            decompressor = bz2.BZ2Decompressor()

            try:
                while not decompressor.eof:
                    if not buf:
                        buf = raw.read(read_size)
                        if not buf:
                            return
                    decompressed = decompressor.decompress(buf)
                    buf = b''  # input fully consumed by the decompressor
                    if decompressed:
                        yield decompressed

                # Stream finished normally; carry over unconsumed bytes
                buf = decompressor.unused_data

                # If nothing is left, try reading more from the file
                if not buf:
                    buf = raw.read(read_size)
                    if not buf:
                        return

            except OSError:
                # Current stream is corrupted — try to recover
                remaining = decompressor.unused_data + buf
                buf = _find_next_bz2_header(remaining, raw, read_size)
                if not buf:
                    return


def _feed_parser_from_chunks(chunk_iter, parser):
    """
    Feed decompressed byte chunks into a SAX parser with incremental UTF-8
    decoding.
    """
    decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
    for chunk in chunk_iter:
        parser.feed(decoder.decode(chunk))
    tail = decoder.decode(b"", final=True)
    if tail:
        parser.feed(tail)


def parse_wikidump(dump_filepath, language_code="en", base_dir=None, generate_graph_flag=False, use_string_labels=False):
    """
    Parses a Wikipedia XML dump, extracts relevant content, and optionally generates a graph.

    Args:
        dump_filepath (str | Path): Path to the Wikipedia XML dump file.
        language_code (str, optional): The language code for processing. Defaults to "en".
        base_dir (str | Path, optional): Base directory for storing output files. Defaults to None.
        generate_graph_flag (bool, optional): Whether to generate a graph after parsing. Defaults to False.
    """
    # print statement to show that the processing has started
    print(f"Processing the dump: {dump_filepath}.")
    settings = get_language_settings(language_code)
    section_patt = settings["section_patt"]
    filter_out_patterns = settings.get('filter_out_patterns', [])
    redirect_keywords = settings.get('redirect_keywords', [])

    # set base directory, defaulting to the current working directory
    base_dir = Path(base_dir) if base_dir else Path.cwd()
    output_dir = base_dir / language_code / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    titles_texts_file = output_dir / f"{language_code}_WP_titles_texts.parquet"

    handler = WikiXmlHandler(
        batch_size=10000,
        output_file=titles_texts_file,
        section_patt=section_patt,
        filter_out_patterns=filter_out_patterns,
        redirect_keywords=redirect_keywords
    )

    # initialize XML parser
    parser = xml.sax.make_parser()
    parser.setContentHandler(handler)

    # process the Wikipedia XML dump
    try:
        _feed_parser_from_chunks(_iter_multistream_bz2(dump_filepath), parser)
    except xml.sax.SAXException:
        pass
    finally:
        handler.process_batch()
        handler.close_writer()

    print(f"Titles and texts saved to {titles_texts_file}")

    # generate graph if the flag is set
    if generate_graph_flag:
        print("Creating the graph...")
        graph_output_dir = base_dir / language_code / "graph"
        graph_output_dir.mkdir(parents=True, exist_ok=True)
        generate_graph(language_code, settings, str(titles_texts_file), str(graph_output_dir), use_string_labels=use_string_labels)
