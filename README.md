# Utils

A collection of command-line document conversion utilities written in Python.

## Scripts

### Document Conversion

| Script | Description | Backend |
|---|---|---|
| `pdf_to_epub.py` | Convert PDF to EPUB | [pypandoc](https://github.com/JessicaTegworthy/pypandoc) |
| `epub_to_pdf.py` | Convert EPUB to PDF | [Calibre](https://calibre-ebook.com/) (`ebook-convert`) |
| `md_to_docx.py` | Convert Markdown to DOCX | [pypandoc](https://github.com/JessicaTegworthy/pypandoc) |
| `webp_to_pdf.py` | Convert WebP image(s) to PDF | [Pillow](https://python-pillow.org/) |

### Video

| Script | Description | Backend |
|---|---|---|
| `trim_video.py` | Trim seconds from start/end of a video (no re-encoding) | [FFmpeg](https://ffmpeg.org/) |
| `upscale_video.py` | Upscale video using Real-ESRGAN via Replicate API | [Replicate](https://replicate.com/) + FFmpeg |

### YouTube

| Script | Description | Backend |
|---|---|---|
| `yt_subs.py` | Download YouTube subtitles (minified plain text by default, or with timestamps) | [yt-dlp](https://github.com/yt-dlp/yt-dlp) |

## Requirements

- Python >= 3.12
- [Pandoc](https://pandoc.org/installing.html) (required by `pypandoc`)
- [Calibre](https://calibre-ebook.com/download) (required by `epub_to_pdf.py`)
- [FFmpeg](https://ffmpeg.org/) (required by `trim_video.py`, `upscale_video.py`)

## Setup

```bash
uv sync
```

## Usage

### Document Conversion

Each script accepts an input file and an optional `-o` / `--output` flag for the output path. When omitted, the output file is placed next to the input with the appropriate extension.

```bash
python pdf_to_epub.py input.pdf
python epub_to_pdf.py input.epub
python md_to_docx.py input.md
python webp_to_pdf.py image.webp
```

### Video

```bash
python trim_video.py video.mp4 2              # remove last 2 seconds
python trim_video.py video.mp4 2 --from-start # remove first 2 seconds
python upscale_video.py video.mp4 --scale 2
```

### YouTube

```bash
python yt_subs.py https://youtu.be/VIDEO_ID                # plain text (default)
python yt_subs.py https://youtu.be/VIDEO_ID -m timestamps   # keep SRT timestamps
python yt_subs.py https://youtu.be/VIDEO_ID -l uk -f vtt    # Ukrainian, VTT format
```
