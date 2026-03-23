# Utils

A collection of command-line utilities written in Python, organized as a skill library.

## Quick Start

```bash
uv sync
uv run python cli.py --list              # see all available skills
uv run python cli.py <skill-name> --help  # see usage for a specific skill
```

## Available Skills

### Document Conversion

| Skill | Description | Backend |
|---|---|---|
| `pdf-to-epub` | Convert PDF to EPUB | [pypandoc](https://github.com/JessicaTegworthy/pypandoc) |
| `epub-to-pdf` | Convert EPUB to PDF | [Calibre](https://calibre-ebook.com/) (`ebook-convert`) |
| `md-to-docx` | Convert Markdown to DOCX | [pypandoc](https://github.com/JessicaTegworthy/pypandoc) |
| `webp-to-pdf` | Convert WebP image(s) to PDF | [Pillow](https://python-pillow.org/) |

### Video

| Skill | Description | Backend |
|---|---|---|
| `trim-video` | Trim seconds from start/end of a video (no re-encoding) | [FFmpeg](https://ffmpeg.org/) |
| `upscale-video` | Upscale video using Real-ESRGAN via Replicate API | [Replicate](https://replicate.com/) + FFmpeg |

### YouTube

| Skill | Description | Backend |
|---|---|---|
| `yt-subs` | Download YouTube subtitles (minified plain text by default, or with timestamps) | [yt-dlp](https://github.com/yt-dlp/yt-dlp) |

## Usage Examples

```bash
uv run python cli.py pdf-to-epub input.pdf
uv run python cli.py epub-to-pdf input.epub -o output.pdf
uv run python cli.py md-to-docx input.md
uv run python cli.py webp-to-pdf image.webp

uv run python cli.py trim-video video.mp4 2              # remove last 2 seconds
uv run python cli.py trim-video video.mp4 2 --from-start # remove first 2 seconds
uv run python cli.py upscale-video video.mp4 --scale 2

uv run python cli.py yt-subs https://youtu.be/VIDEO_ID
uv run python cli.py yt-subs https://youtu.be/VIDEO_ID -l uk -f vtt
```

## Structure

```
utils/
├── cli.py              # Unified CLI entry point
├── skills/
│   ├── _output.py      # Shared output-path helper
│   ├── pdf-to-epub/    # SKILL.md + pdf_to_epub.py
│   ├── epub-to-pdf/    # SKILL.md + epub_to_pdf.py
│   ├── md-to-docx/     # SKILL.md + md_to_docx.py
│   ├── webp-to-pdf/    # SKILL.md + webp_to_pdf.py
│   ├── trim-video/     # SKILL.md + trim_video.py
│   ├── upscale-video/  # SKILL.md + upscale_video.py
│   └── yt-subs/        # SKILL.md + yt_subs.py
├── CHECKLIST.md        # Skill conversion tracker
├── pyproject.toml
└── README.md
```

Each skill lives in its own subdirectory with a `SKILL.md` (description, prerequisites, usage) and an executable Python script.

## Requirements

- Python >= 3.12
- [Pandoc](https://pandoc.org/installing.html) (for `pdf-to-epub`, `md-to-docx`)
- [Calibre](https://calibre-ebook.com/download) (for `epub-to-pdf`)
- [FFmpeg](https://ffmpeg.org/) (for `trim-video`, `upscale-video`)
