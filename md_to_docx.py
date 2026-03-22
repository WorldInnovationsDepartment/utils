import argparse
import os
import sys

import pypandoc

from _output import default_output


def md_to_docx(md_path, output_path=None):
    """
    Convert a Markdown file to DOCX format using pypandoc.

    Args:
        md_path (str): Path to the input Markdown file.
        output_path (str, optional): Desired path for the DOCX file.
                                     Defaults to ``output/md_to_docx/<stem>.docx``.

    Returns:
        str: Path to the generated DOCX file.

    Raises:
        FileNotFoundError: If the input Markdown file does not exist.
        RuntimeError: If the conversion process fails.
    """
    if not os.path.exists(md_path):
        raise FileNotFoundError(f'Input file not found: {md_path}')

    if output_path is None:
        stem = os.path.splitext(os.path.basename(md_path))[0]
        output_path = str(default_output(f'{stem}.docx'))

    try:
        pypandoc.convert_file(
            md_path,
            'docx',
            outputfile=output_path,
            extra_args=['--standalone']
        )
        print(f'Successfully converted to: {output_path}')
        return output_path

    except RuntimeError as e:
        raise RuntimeError(f'Conversion failed: {e}') from e


def main():
    """Parse command-line arguments and convert Markdown to DOCX."""
    parser = argparse.ArgumentParser(
        description='Convert Markdown files to DOCX format using pypandoc.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Example:\n  %(prog)s input.md\n  %(prog)s input.md -o output.docx'
    )

    parser.add_argument(
        'input',
        help='Path to the input Markdown file'
    )

    parser.add_argument(
        '-o', '--output',
        help='Path to the output DOCX file (default: input path with .docx extension)',
        default=None
    )

    args = parser.parse_args()

    try:
        md_to_docx(args.input, args.output)
    except FileNotFoundError as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()


