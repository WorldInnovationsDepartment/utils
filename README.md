# Utils

A collection of command-line document conversion utilities written in Python.

## Scripts

| Script | Description | Backend |
|---|---|---|
| `pdf_to_epub.py` | Convert PDF files to EPUB format | [pypandoc](https://github.com/JessicaTegworthy/pypandoc) |
| `epub_to_pdf.py` | Convert EPUB files to PDF format | [Calibre](https://calibre-ebook.com/) (`ebook-convert`) |
| `md_to_docx.py` | Convert Markdown files to DOCX format | [pypandoc](https://github.com/JessicaTegworthy/pypandoc) |

## Requirements

- Python >= 3.12
- [Pandoc](https://pandoc.org/installing.html) (required by `pypandoc`)
- [Calibre](https://calibre-ebook.com/download) (required by `epub_to_pdf.py`)

## Setup

```bash
uv sync
```

## Usage

Each script accepts an input file and an optional `-o` / `--output` flag for the output path. When omitted, the output file is placed next to the input with the appropriate extension.

```bash
python pdf_to_epub.py input.pdf
python pdf_to_epub.py input.pdf -o output.epub

python epub_to_pdf.py input.epub
python epub_to_pdf.py input.epub -o output.pdf

python md_to_docx.py input.md
python md_to_docx.py input.md -o output.docx
```
