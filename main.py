import argparse
from pathlib import Path
from gui import gui_prompt_for_inputs
from config import get_language_settings
from parser_module import parse_wikidump
from graph import generate_graph


def parse_args():
    """
    Parses command-line arguments for processing a Wikipedia XML dump.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Parse Wikipedia XML dump and generate graph."
    )
    parser.add_argument(
        '--dump_filepath', type=str,
        help='Path to the compressed XML dump file.'
    )
    parser.add_argument(
        '--language_code', type=str,
        choices=['en', 'es', 'el', 'pl', 'it', 'nl', 'eu', 'hi', 'de'],
        help='Language code (en, es, el, pl, it, nl, eu, hi, de).'
    )
    parser.add_argument(
        '--base_dir', type=str, default=str(Path.cwd()),
        help='Base directory for output files. Defaults to the current working directory.'
    )
    parser.add_argument(
        '--generate_graph', action='store_true',
        help='Flag to indicate whether to generate the graph.'
    )

    return parser.parse_args()


def main():
    """
    Main function to process a Wikipedia XML dump and optionally generate a graph.

    This function:
    1. Parses command-line arguments.
    2. Uses the GUI if required arguments are missing.
    3. Ensures the base directory exists.
    4. Processes the Wikipedia dump file.
    5. Generates a graph if the option is enabled.
    """
    args = parse_args()

    # if required arguments are missing, prompt user via GUI
    if not args.dump_filepath or not args.language_code:
        dump_filepath, language_code, base_dir, generate_graph_flag = gui_prompt_for_inputs()
    else:
        dump_filepath = Path(args.dump_filepath)  # convert to Path object
        language_code = args.language_code
        base_dir = Path(args.base_dir) if args.base_dir else Path.cwd()
        generate_graph_flag = args.generate_graph

    # ensure base directory exists
    base_dir.mkdir(parents=True, exist_ok=True)

    # parse Wikipedia XML dump
    parse_wikidump(
        dump_filepath=str(dump_filepath),  # convert Path to string for compatibility
        language_code=language_code,
        base_dir=str(base_dir),  # convert Path to string for compatibility
        generate_graph_flag=generate_graph_flag
    )

    # generate graph if the flag is set
    if generate_graph_flag:
        settings = get_language_settings(language_code)
        graph_output_dir = base_dir / language_code / "graph"
        graph_output_dir.mkdir(parents=True, exist_ok=True)  # ensure directory exists
        titles_texts_file = base_dir / language_code / "output" / f"{language_code}_WP_titles_texts.parquet"
        generate_graph(language_code, settings, str(titles_texts_file), str(graph_output_dir))


if __name__ == "__main__":
    main()