#!/usr/bin/env python3
"""
Utils CLI — unified command-line interface for all utility skills.

Usage:
    python cli.py <skill-name> [args...]
    python cli.py --list

Examples:
    python cli.py pdf-to-epub input.pdf -o output.epub
    python cli.py trim-video video.mp4 2 --from-start
    python cli.py yt-subs "https://youtu.be/VIDEO_ID" -l uk
    python cli.py --list
"""

import importlib.util
import sys
from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parent / "skills"

# Mapping: CLI skill name -> (subdirectory, module filename, entry function)
SKILLS = {
    "pdf-to-epub":    ("pdf-to-epub",    "pdf_to_epub.py",    "main"),
    "epub-to-pdf":    ("epub-to-pdf",    "epub_to_pdf.py",    "main"),
    "md-to-docx":     ("md-to-docx",     "md_to_docx.py",    "main"),
    "webp-to-pdf":    ("webp-to-pdf",    "webp_to_pdf.py",   "main"),
    "trim-video":     ("trim-video",     "trim_video.py",     "main"),
    "upscale-video":  ("upscale-video",  "upscale_video.py",  "main"),
    "yt-subs":        ("yt-subs",        "yt_subs.py",        "main"),
}

DESCRIPTIONS = {
    "pdf-to-epub":    "Convert PDF to EPUB (pypandoc)",
    "epub-to-pdf":    "Convert EPUB to PDF (Calibre)",
    "md-to-docx":     "Convert Markdown to DOCX (pypandoc)",
    "webp-to-pdf":    "Convert WebP image to PDF (Pillow)",
    "trim-video":     "Trim seconds from video start/end (FFmpeg, no re-encode)",
    "upscale-video":  "Upscale video via Real-ESRGAN on Replicate",
    "yt-subs":        "Download YouTube subtitles (yt-dlp)",
}


def list_skills():
    """Print all available skills."""
    print("\nAvailable skills:\n")
    max_name = max(len(n) for n in SKILLS)
    for name in sorted(SKILLS):
        desc = DESCRIPTIONS.get(name, "")
        print(f"  {name:<{max_name + 2}} {desc}")
    print(f"\nUsage: python {Path(__file__).name} <skill-name> [args...]\n")


def load_and_run(skill_name: str, args: list[str]):
    """Dynamically load a skill module and run its main()."""
    if skill_name not in SKILLS:
        print(f"Error: Unknown skill '{skill_name}'", file=sys.stderr)
        print(f"Run 'python {Path(__file__).name} --list' to see available skills.", file=sys.stderr)
        sys.exit(1)

    subdir, module_file, entry = SKILLS[skill_name]
    module_path = SKILLS_DIR / subdir / module_file

    if not module_path.exists():
        print(f"Error: Script not found: {module_path}", file=sys.stderr)
        sys.exit(1)

    # Override sys.argv so argparse inside the skill sees the right args
    sys.argv = [str(module_path)] + args

    # Load the module dynamically
    spec = importlib.util.spec_from_file_location(module_file.replace(".py", ""), module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Call the entry function
    fn = getattr(module, entry, None)
    if fn is None:
        print(f"Error: No '{entry}' function in {module_path}", file=sys.stderr)
        sys.exit(1)

    fn()


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("--help", "-h"):
        print(__doc__)
        list_skills()
        sys.exit(0)

    if sys.argv[1] == "--list":
        list_skills()
        sys.exit(0)

    skill_name = sys.argv[1]
    skill_args = sys.argv[2:]
    load_and_run(skill_name, skill_args)


if __name__ == "__main__":
    main()
