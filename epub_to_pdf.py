import argparse
import os
import shutil
import subprocess
import sys

from _output import default_output


def epub_to_pdf(epub_path, output_path=None):
    """
    Convert an EPUB file to PDF format using Calibre's ebook-convert.

    Args:
        epub_path (str): Path to the input EPUB file.
        output_path (str, optional): Desired path for the PDF file.
                                     Defaults to ``output/epub_to_pdf/<stem>.pdf``.

    Returns:
        str: Path to the generated PDF file.

    Raises:
        FileNotFoundError: If the input EPUB file does not exist or ebook-convert is not installed.
        RuntimeError: If the conversion process fails.
    """
    if not os.path.exists(epub_path):
        raise FileNotFoundError(f'Input file not found: {epub_path}')

    if not shutil.which('ebook-convert'):
        raise FileNotFoundError(
            'ebook-convert not found. Please install Calibre: '
            'https://calibre-ebook.com/download'
        )

    if output_path is None:
        stem = os.path.splitext(os.path.basename(epub_path))[0]
        output_path = str(default_output(f'{stem}.pdf'))

    try:
        # Use ebook-convert from Calibre for better EPUB handling
        result = subprocess.run(
            ['ebook-convert', epub_path, output_path, '--enable-heuristics'],
            check=True,
            capture_output=True,
            text=True
        )
        print(f'Successfully converted to: {output_path}')
        return output_path

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        raise RuntimeError(f'Conversion failed: {error_msg}') from e


def main():
    """Parse command-line arguments and convert EPUB to PDF."""
    parser = argparse.ArgumentParser(
        description='Convert EPUB files to PDF format using Calibre\'s ebook-convert.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Example:\n  %(prog)s input.epub\n  %(prog)s input.epub -o output.pdf'
    )

    parser.add_argument(
        'input',
        help='Path to the input EPUB file'
    )

    parser.add_argument(
        '-o', '--output',
        help='Path to the output PDF file (default: input path with .pdf extension)',
        default=None
    )

    args = parser.parse_args()

    try:
        epub_to_pdf(args.input, args.output)
    except FileNotFoundError as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

