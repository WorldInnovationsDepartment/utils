#!/usr/bin/env python3
"""
Trim a video by removing a given number of seconds from the start or end.

Uses ffmpeg with stream-copy (no re-encoding) for near-instant operation.

Usage:
    python trim_video.py video.mp4 2              # remove last 2 seconds
    python trim_video.py video.mp4 2 --from-start # remove first 2 seconds
    python trim_video.py video.mp4 5 -o cut.mp4   # custom output name

Prerequisites:
    brew install ffmpeg  # or apt install ffmpeg
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from _output import default_output


def check_ffmpeg():
    """Verify ffmpeg and ffprobe are available."""
    for cmd in ("ffmpeg", "ffprobe"):
        if shutil.which(cmd) is None:
            print(
                f"ERROR: '{cmd}' not found. Install with: brew install ffmpeg (macOS) "
                f"or apt install ffmpeg (Linux)",
                file=sys.stderr,
            )
            sys.exit(1)


def get_duration(path: Path) -> float:
    """Return video duration in seconds via ffprobe."""
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"ERROR: ffprobe failed on {path}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(result.stdout)
    duration = float(data["format"]["duration"])
    return duration


def trim_video(
    input_path: Path,
    output_path: Path,
    seconds: float,
    from_start: bool,
):
    """Trim the video using ffmpeg stream-copy."""
    duration = get_duration(input_path)

    if seconds >= duration:
        print(
            f"ERROR: Cannot trim {seconds}s from a {duration:.1f}s video.",
            file=sys.stderr,
        )
        sys.exit(1)

    if from_start:
        # Skip the first N seconds
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(seconds),
            "-i", str(input_path),
            "-c", "copy",
            str(output_path),
        ]
        print(f"  Removing first {seconds}s (keeping {duration - seconds:.1f}s)")
    else:
        # Keep only up to (duration - N) seconds
        new_duration = duration - seconds
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-t", str(new_duration),
            "-c", "copy",
            str(output_path),
        ]
        print(f"  Removing last {seconds}s (keeping {new_duration:.1f}s)")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR: ffmpeg failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)

    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"  Output: {output_path} ({size_mb:.1f} MB)")


def main():
    parser = argparse.ArgumentParser(
        description="Trim a video by removing seconds from the start or end."
    )
    parser.add_argument("input", type=Path, help="Path to the input video file.")
    parser.add_argument(
        "seconds", type=float, help="Number of seconds to trim."
    )
    parser.add_argument(
        "--from-start",
        action="store_true",
        help="Remove from the beginning instead of the end (default: end).",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Output file path (default: <name>_trimmed.<ext>).",
    )
    args = parser.parse_args()

    input_path = args.input.resolve()
    if not input_path.is_file():
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    check_ffmpeg()

    output_path = args.output
    if output_path is None:
        output_path = default_output(
            input_path.stem + '_trimmed' + input_path.suffix,
        )

    print(f"\nTrimming: {input_path.name}")
    trim_video(input_path, output_path, args.seconds, args.from_start)
    print(f"\nDone. Saved to:\n  {output_path}\n")


if __name__ == "__main__":
    main()
