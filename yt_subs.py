import argparse
import os
import re
import sys

import yt_dlp

from _output import default_output


def clean_url(url):
    """Strip shell-escape backslashes and playlist/tracking params from a URL."""
    url = url.replace('\\', '')
    url = re.sub(r'[&?](list|index|si)=[^&]*', '', url)
    return url


def minify_srt(text):
    """Strip SRT sequence numbers, timestamps, and blank lines — return plain text."""
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if re.match(r'^\d+$', line):
            continue
        if re.match(r'\d{2}:\d{2}:\d{2}', line):
            continue
        lines.append(line)
    return '\n'.join(lines)


def minify_vtt(text):
    """Strip VTT header, timestamps, and blank lines — return plain text."""
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith('WEBVTT') or line.startswith('Kind:') or line.startswith('Language:'):
            continue
        if re.match(r'\d{2}:\d{2}', line):
            continue
        lines.append(line)
    return '\n'.join(lines)


def download_subtitles(url, lang='en', output_path=None, sub_format='srt', auto=True, mode='minify'):
    """
    Download subtitles from a YouTube video.

    Tries manual (human-written) subtitles first, then falls back to
    auto-generated subtitles if allowed.

    Args:
        url (str): YouTube video URL.
        lang (str): Subtitle language code (default: 'en').
        output_path (str, optional): Output file path. Defaults to
                                      '<video_title>.<lang>.<format>' in the current directory.
        sub_format (str): Subtitle format — 'srt', 'vtt', or 'ass' (default: 'srt').
        auto (bool): Whether to fall back to auto-generated subtitles (default: True).
        mode (str): 'minify' strips timestamps leaving plain text (default),
                    'timestamps' keeps original subtitle format.

    Returns:
        str: Path to the downloaded subtitle file.

    Raises:
        RuntimeError: If subtitles cannot be downloaded.
    """
    url = clean_url(url)

    # Build subtitle language list — include <lang>-orig variant that YouTube
    # sometimes uses for the original audio language's auto-generated subs.
    sub_langs = [lang, f'{lang}-orig']

    # Determine output template via a quick info extraction
    info_opts = {
        'quiet': True,
        'writesubtitles': True,
        'writeautomaticsub': auto,
        'subtitleslangs': sub_langs,
    }
    with yt_dlp.YoutubeDL(info_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
        except yt_dlp.utils.DownloadError as e:
            raise RuntimeError(f'Failed to fetch video info: {e}') from e

    title = info.get('title', 'subtitles')
    manual_subs = info.get('subtitles') or {}
    auto_subs = info.get('automatic_captions') or {}

    # Pick the best single language key: prefer manual subs, then auto-generated.
    chosen_lang = None
    use_auto = False
    for k in sub_langs:
        if k in manual_subs:
            chosen_lang = k
            break
    if not chosen_lang and auto:
        for k in sub_langs:
            if k in auto_subs:
                chosen_lang = k
                use_auto = True
                break

    if not chosen_lang:
        if not auto:
            raise RuntimeError(
                f"No manual subtitles for language '{lang}' and auto-generated subs are disabled"
            )
        raise RuntimeError(f"No subtitles available for language '{lang}'")

    if output_path:
        base, _ = os.path.splitext(output_path)
        outtmpl = base
    else:
        safe_title = yt_dlp.utils.sanitize_filename(title)
        outtmpl = str(default_output(safe_title))

    ydl_opts = {
        'skip_download': True,
        'writesubtitles': not use_auto,
        'writeautomaticsub': use_auto,
        'subtitleslangs': [chosen_lang],
        'subtitlesformat': sub_format,
        'convertsubtitles': sub_format,
        'outtmpl': outtmpl,
        'quiet': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
        except yt_dlp.utils.DownloadError as e:
            raise RuntimeError(f'Failed to download subtitles: {e}') from e

    expected = f'{outtmpl}.{chosen_lang}.{sub_format}'
    if not os.path.exists(expected):
        raise RuntimeError(f'Subtitle file not found at expected path: {expected}')

    if mode == 'minify':
        with open(expected, 'r', encoding='utf-8') as f:
            text = f.read()

        minifiers = {'srt': minify_srt, 'vtt': minify_vtt}
        minify_fn = minifiers.get(sub_format)
        if minify_fn:
            text = minify_fn(text)

        txt_path = re.sub(r'\.[^.]+$', '.txt', expected)
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text)
        os.remove(expected)
        print(f'Successfully downloaded subtitles (minified): {txt_path}')
        return txt_path

    print(f'Successfully downloaded subtitles: {expected}')
    return expected


def main():
    """Parse command-line arguments and download YouTube subtitles."""
    parser = argparse.ArgumentParser(
        description='Download subtitles from a YouTube video.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Example:\n'
               '  %(prog)s https://www.youtube.com/watch?v=VIDEO_ID\n'
               '  %(prog)s https://youtu.be/VIDEO_ID -l uk -f vtt\n'
               '  %(prog)s https://youtu.be/VIDEO_ID --no-auto -o subs.srt'
    )

    parser.add_argument(
        'url',
        help='YouTube video URL'
    )

    parser.add_argument(
        '-l', '--lang',
        help='Subtitle language code (default: en)',
        default='en'
    )

    parser.add_argument(
        '-o', '--output',
        help='Output file path (default: <video_title>.<lang>.<format>)',
        default=None
    )

    parser.add_argument(
        '-f', '--format',
        help='Subtitle format: srt, vtt, ass (default: srt)',
        choices=['srt', 'vtt', 'ass'],
        default='srt'
    )

    parser.add_argument(
        '-m', '--mode',
        help='Output mode: minify (plain text, no timestamps — default) or timestamps (original format)',
        choices=['minify', 'timestamps'],
        default='minify'
    )

    parser.add_argument(
        '--auto',
        help='Fall back to auto-generated subtitles (default)',
        action='store_true',
        default=True
    )

    parser.add_argument(
        '--no-auto',
        help='Do not use auto-generated subtitles',
        action='store_false',
        dest='auto'
    )

    args = parser.parse_args()

    try:
        download_subtitles(args.url, args.lang, args.output, args.format, args.auto, args.mode)
    except RuntimeError as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
