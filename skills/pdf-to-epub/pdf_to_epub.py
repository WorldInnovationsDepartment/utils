import argparse
import os
import sys

import pypandoc

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _output import default_output


def pdf_to_epub(pdf_path, output_path=None):
    """
    Convert a PDF file to EPUB format using pypandoc.

    Args:
        pdf_path (str): Path to the input PDF file.
        output_path (str, optional): Desired path for the EPUB file.
                                     Defaults to ``output/pdf_to_epub/<stem>.epub``.

    Returns:
        str: Path to the generated EPUB file.

    Raises:
        FileNotFoundError: If the input PDF file does not exist.
        RuntimeError: If the conversion process fails.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f'Input file not found: {pdf_path}')

    if output_path is None:
        stem = os.path.splitext(os.path.basename(pdf_path))[0]
        output_path = str(default_output(f'{stem}.epub'))

    try:
        pypandoc.convert_file(
            pdf_path,
            'epub',
            outputfile=output_path,
            extra_args=['--standalone']
        )
        print(f'Successfully converted to: {output_path}')
        return output_path

    except RuntimeError as e:
        raise RuntimeError(f'Conversion failed: {e}') from e


def main():
    """Parse command-line arguments and convert PDF to EPUB."""
    parser = argparse.ArgumentParser(
        description='Convert PDF files to EPUB format using pypandoc.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Example:\n  %(prog)s input.pdf\n  %(prog)s input.pdf -o output.epub'
    )

    parser.add_argument(
        'input',
        help='Path to the input PDF file'
    )

    parser.add_argument(
        '-o', '--output',
        help='Path to the output EPUB file (default: input path with .epub extension)',
        default=None
    )

    args = parser.parse_args()

    try:
        pdf_to_epub(args.input, args.output)
    except FileNotFoundError as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
