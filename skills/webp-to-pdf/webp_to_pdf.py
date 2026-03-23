import argparse
import os
import sys

from PIL import Image

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _output import default_output


def webp_to_pdf(webp_path, output_path=None):
    """
    Convert a WebP image (or multiple images) to PDF format using Pillow.

    Args:
        webp_path (str): Path to the input WebP file.
        output_path (str, optional): Desired path for the PDF file.
                                     Defaults to ``output/webp_to_pdf/<stem>.pdf``.

    Returns:
        str: Path to the generated PDF file.

    Raises:
        FileNotFoundError: If the input WebP file does not exist.
        RuntimeError: If the conversion process fails.
    """
    if not os.path.exists(webp_path):
        raise FileNotFoundError(f'Input file not found: {webp_path}')

    if output_path is None:
        stem = os.path.splitext(os.path.basename(webp_path))[0]
        output_path = str(default_output(f'{stem}.pdf'))

    try:
        img = Image.open(webp_path)
        # Convert to RGB since PDF doesn't support RGBA
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        img.save(output_path, 'PDF')
        print(f'Successfully converted to: {output_path}')
        return output_path

    except Exception as e:
        raise RuntimeError(f'Conversion failed: {e}') from e


def main():
    """Parse command-line arguments and convert WebP to PDF."""
    parser = argparse.ArgumentParser(
        description='Convert WebP images to PDF format using Pillow.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Example:\n  %(prog)s input.webp\n  %(prog)s input.webp -o output.pdf'
    )

    parser.add_argument(
        'input',
        help='Path to the input WebP file'
    )

    parser.add_argument(
        '-o', '--output',
        help='Path to the output PDF file (default: input path with .pdf extension)',
        default=None
    )

    args = parser.parse_args()

    try:
        webp_to_pdf(args.input, args.output)
    except FileNotFoundError as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
