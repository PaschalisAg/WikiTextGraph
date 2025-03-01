import os
import argparse
from pathlib import Path
from gui import gui_prompt_for_inputs
from config import get_language_settings
from parser_module import parse_wikidump
from graph import generate_graph


def parse_args():
    """
    Parse command-line arguments for processing a Wikipedia XML dump.

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
        choices=['EN', 'ES', 'GR', 'PL', 'IT', 'NL', 'EUS', 'HI', 'DE'],
        help='Language code (EN, ES, GR, PL, IT, NL, EUS, HI, DE).'
    )
    parser.add_argument(
        '--base_dir', type=str, default=os.getcwd(),
        help='Base directory for output files.'
    )
    parser.add_argument(
        '--generate_graph', action='store_true',
        help='Flag to generate the graph.'
    )
    
    return parser.parse_args()


def main():
    """
    Main function to process Wikipedia XML dump and optionally generate a graph.
    """
    args = parse_args()
    
    # If required arguments are missing, prompt user via GUI
    if not args.dump_filepath or not args.language_code:
        dump_filepath, language_code, base_dir, generate_graph_flag, num_cores = gui_prompt_for_inputs()

    else:
        dump_filepath = Path(args.dump_filepath).resolve()
        language_code = args.language_code
        base_dir = Path(args.base_dir).resolve()
        generate_graph_flag = args.generate_graph

    # Process Wikipedia XML dump
    parse_wikidump(
        dump_filepath=dump_filepath,
        language_code=language_code,
        base_dir=base_dir,
        generate_graph_flag=generate_graph_flag,
        num_cores=num_cores
    )


if __name__ == "__main__":
    main()