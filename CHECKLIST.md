# Utils Skills Checklist

Skill conversion status for all utility scripts.

| # | Skill Name | Source File | Claude Skill | Local Skill Dir | Status |
|---|-----------|-------------|--------------|-----------------|--------|
| 1 | pdf-to-epub | pdf_to_epub.py | ~/.hermes/skills/utils/pdf-to-epub/ | skills/pdf-to-epub/ | Done |
| 2 | epub-to-pdf | epub_to_pdf.py | ~/.hermes/skills/utils/epub-to-pdf/ | skills/epub-to-pdf/ | Done |
| 3 | md-to-docx | md_to_docx.py | ~/.hermes/skills/utils/md-to-docx/ | skills/md-to-docx/ | Done |
| 4 | webp-to-pdf | webp_to_pdf.py | ~/.hermes/skills/utils/webp-to-pdf/ | skills/webp-to-pdf/ | Done |
| 5 | trim-video | trim_video.py | ~/.hermes/skills/utils/trim-video/ | skills/trim-video/ | Done |
| 6 | upscale-video | upscale_video.py | ~/.hermes/skills/utils/upscale-video/ | skills/upscale-video/ | Done |
| 7 | yt-subs | yt_subs.py | ~/.hermes/skills/utils/yt-subs/ | skills/yt-subs/ | Done |

## Shared Files
- `_output.py` — Output path helper (shared across all skills)
- `cli.py` — Unified CLI entry point (`python cli.py <skill-name> [args]`)

## Notes
- All skills follow Claude skill format (SKILL.md + executable script)
- Each skill subdirectory under `skills/` is self-contained
- CLI dynamically loads and dispatches to the correct skill module
- Original scripts in repo root preserved for backward compatibility
