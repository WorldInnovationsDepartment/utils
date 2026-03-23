#!/usr/bin/env python3
"""
Video upscaler using Replicate's Real-ESRGAN API.

Extracts frames from a video, upscales each via the Real-ESRGAN model on
Replicate, then reassembles them at the original framerate with the original
audio track copied verbatim.

Model choice: Real-ESRGAN (nightmareai/real-esrgan) — GAN-based, deterministic
output means no inter-frame flickering (unlike diffusion models such as SUPIR).
86M+ runs on Replicate, battle-tested for video upscaling.

Usage:
    python upscale_video.py /path/to/video.mp4
    python upscale_video.py /path/to/video.mp4 --scale 2 --workers 8
    python upscale_video.py /path/to/video.mp4 --seconds 5  # upscale first 5s only
    python upscale_video.py /path/to/video.mp4 --cleanup  # remove temp files after

Prerequisites:
    pip install replicate tqdm python-dotenv requests
    brew install ffmpeg  # or apt install ffmpeg

    Set REPLICATE_API_TOKEN in your environment or in a .env file.
    Get a token at https://replicate.com/account/api-tokens
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)
from fractions import Fraction
from pathlib import Path

import replicate
import requests
from dotenv import load_dotenv
from tqdm import tqdm

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _output import default_output

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPLICATE_MODEL = "nightmareai/real-esrgan"
MAX_RETRIES = 10
DEFAULT_RPM = 6  # Replicate's rate limit for accounts with < $5 credit
DEFAULT_WORKERS = 10
COST_PER_FRAME_ESTIMATE = 0.0005  # USD, rough estimate for Real-ESRGAN on T4


# ---------------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------------


class RateLimiter:
    """Thread-safe token-bucket rate limiter."""

    def __init__(self, rpm: int):
        self._min_interval = 60.0 / rpm
        self._lock = threading.Lock()
        self._last_call = 0.0

    def wait(self):
        """Block until the next request is allowed."""
        with self._lock:
            now = time.monotonic()
            wait_for = self._min_interval - (now - self._last_call)
            if wait_for > 0:
                time.sleep(wait_for)
            self._last_call = time.monotonic()


def parse_retry_after(error_msg: str) -> float:
    """Extract wait time from a Replicate 429 error message.

    Looks for patterns like "resets in ~8s" or "resets in ~1s".
    Returns seconds to wait, or 12.0 as a safe default.
    """
    match = re.search(r"resets in ~(\d+)s", error_msg)
    if match:
        return float(match.group(1)) + 2.0  # add 2s buffer
    return 12.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def check_prerequisites():
    """Verify ffmpeg, ffprobe, and API token are available."""
    errors = []

    for cmd in ("ffmpeg", "ffprobe"):
        if shutil.which(cmd) is None:
            errors.append(
                f"'{cmd}' not found. Install with: brew install ffmpeg (macOS) "
                f"or apt install ffmpeg (Linux)"
            )

    load_dotenv()
    if not os.environ.get("REPLICATE_API_TOKEN"):
        errors.append(
            "REPLICATE_API_TOKEN not set. Export it or add to a .env file.\n"
            "  Get a token at https://replicate.com/account/api-tokens"
        )

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


def probe_video(path: Path) -> dict:
    """Return video metadata via ffprobe."""
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_streams",
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
    video_stream = next(
        (s for s in data["streams"] if s["codec_type"] == "video"), None
    )
    audio_stream = next(
        (s for s in data["streams"] if s["codec_type"] == "audio"), None
    )

    if video_stream is None:
        print("ERROR: No video stream found in input file.", file=sys.stderr)
        sys.exit(1)

    width = int(video_stream["width"])
    height = int(video_stream["height"])
    r_fps = video_stream.get("r_frame_rate", "30/1")
    nb_frames = int(video_stream.get("nb_frames", 0))
    duration = float(video_stream.get("duration", 0))

    # If nb_frames is missing/zero, estimate from duration × fps
    fps_frac = Fraction(r_fps)
    if nb_frames == 0 and duration > 0:
        nb_frames = int(float(fps_frac) * duration)

    return {
        "width": width,
        "height": height,
        "fps": r_fps,
        "fps_float": float(fps_frac),
        "nb_frames": nb_frames,
        "duration": duration,
        "has_audio": audio_stream is not None,
    }


def determine_scale(width: int, height: int, forced_scale: int | None) -> int:
    """Pick upscale factor. 4× for sub-1080p sources, 2× otherwise."""
    if forced_scale:
        return forced_scale
    longer = max(width, height)
    if longer <= 1080:
        return 4
    elif longer <= 2160:
        return 2
    else:
        return 2


def extract_frames(
    video_path: Path, frames_dir: Path, fps: str, seconds: float | None = None
) -> int:
    """Extract video frames as PNGs. Returns the number of extracted frames."""
    frames_dir.mkdir(parents=True, exist_ok=True)

    # Check if frames already extracted (resume support)
    existing = sorted(frames_dir.glob("*.png"))
    if existing:
        print(f"  Found {len(existing)} previously extracted frames, reusing.")
        return len(existing)

    print("  Extracting frames with ffmpeg...")
    cmd = ["ffmpeg", "-i", str(video_path)]
    if seconds is not None:
        cmd += ["-t", str(seconds)]
    cmd += [
        "-vsync", "cfr",
        "-r", fps,
        "-qmin", "1",
        "-q:v", "1",
        str(frames_dir / "%06d.png"),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR: Frame extraction failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)

    count = len(list(frames_dir.glob("*.png")))
    print(f"  Extracted {count} frames.")
    return count


def upscale_single_frame(
    frame_path: Path, output_path: Path, scale: int, limiter: RateLimiter
) -> tuple[bool, str]:
    """Upscale one frame via Replicate. Returns (success, message)."""
    if output_path.exists() and output_path.stat().st_size > 0:
        return True, "skipped (already exists)"

    last_error = ""
    for attempt in range(1, MAX_RETRIES + 1):
        # Wait for the rate limiter before every API call
        limiter.wait()

        try:
            with open(frame_path, "rb") as f:
                output = replicate.run(
                    REPLICATE_MODEL,
                    input={
                        "image": f,
                        "scale": scale,
                        "face_enhance": False,
                    },
                )

            # Handle various output types from the replicate client
            if hasattr(output, "read"):
                img_data = output.read()
            elif isinstance(output, str):
                img_data = requests.get(output, timeout=60).content
            elif isinstance(output, list) and len(output) > 0:
                item = output[0]
                if hasattr(item, "read"):
                    img_data = item.read()
                else:
                    img_data = requests.get(str(item), timeout=60).content
            else:
                img_data = requests.get(str(output), timeout=60).content

            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as out:
                out.write(img_data)

            return True, "ok"

        except Exception as exc:
            last_error = str(exc)
            is_rate_limit = "429" in last_error or "throttled" in last_error.lower()
            if attempt < MAX_RETRIES:
                if is_rate_limit:
                    delay = parse_retry_after(last_error)
                    tqdm.write(
                        f"  Rate-limited on {frame_path.name}, "
                        f"waiting {delay:.0f}s (attempt {attempt}/{MAX_RETRIES})"
                    )
                else:
                    delay = min(2 ** attempt, 30)
                time.sleep(delay)

    return False, f"failed after {MAX_RETRIES} retries: {last_error}"


def upscale_frames(
    frames_dir: Path,
    upscaled_dir: Path,
    scale: int,
    max_workers: int,
    rpm: int,
) -> int:
    """Upscale all frames with rate-limited concurrency. Returns count of failures."""
    upscaled_dir.mkdir(parents=True, exist_ok=True)
    limiter = RateLimiter(rpm)

    frame_files = sorted(frames_dir.glob("*.png"))
    if not frame_files:
        print("ERROR: No frames found to upscale.", file=sys.stderr)
        sys.exit(1)

    # Figure out how many are already done
    already_done = sum(
        1
        for f in frame_files
        if (upscaled_dir / f.name).exists()
        and (upscaled_dir / f.name).stat().st_size > 0
    )
    remaining = len(frame_files) - already_done

    est_cost = len(frame_files) * COST_PER_FRAME_ESTIMATE
    est_minutes = remaining / rpm if rpm > 0 else 0
    print(f"  Total frames: {len(frame_files)}")
    print(f"  Already upscaled: {already_done}")
    print(f"  Remaining: {remaining}")
    print(f"  Rate limit: {rpm} req/min → ~{est_minutes:.1f} min for remaining")
    print(f"  Estimated API cost: ~${est_cost:.2f}")
    print(f"  Concurrent workers: {max_workers}")
    print()

    if remaining == 0:
        print("  All frames already upscaled.")
        return 0

    failures = 0

    with tqdm(
        total=len(frame_files),
        initial=already_done,
        desc="Upscaling",
        unit="frame",
        bar_format=(
            "{l_bar}{bar}| {n_fmt}/{total_fmt} "
            "[{elapsed}<{remaining}, {rate_fmt}] "
        ),
    ) as pbar:
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {}
            for frame_path in frame_files:
                out_path = upscaled_dir / frame_path.name
                if out_path.exists() and out_path.stat().st_size > 0:
                    continue
                fut = pool.submit(
                    upscale_single_frame, frame_path, out_path, scale, limiter
                )
                futures[fut] = frame_path

            for fut in as_completed(futures):
                success, msg = fut.result()
                if not success:
                    failures += 1
                    fname = futures[fut].name
                    tqdm.write(f"  WARN: {fname} — {msg}")
                pbar.update(1)

    return failures


def reassemble_video(
    upscaled_dir: Path,
    output_path: Path,
    fps: str,
    original_video: Path,
    has_audio: bool,
    seconds: float | None = None,
):
    """Reassemble upscaled frames into final video with original audio."""
    print("  Encoding video with H.265 (CRF 18, slow preset)...")

    cmd = [
        "ffmpeg",
        "-y",
        "-framerate", fps,
        "-i", str(upscaled_dir / "%06d.png"),
    ]

    if has_audio:
        cmd += ["-i", str(original_video)]
        cmd += ["-map", "0:v", "-map", "1:a"]
        cmd += ["-c:a", "copy"]
        if seconds is not None:
            cmd += ["-t", str(seconds)]
    else:
        cmd += ["-map", "0:v"]

    cmd += [
        "-c:v", "libx265",
        "-crf", "18",
        "-preset", "slow",
        "-pix_fmt", "yuv420p",
        "-tag:v", "hvc1",  # Apple compatibility
        str(output_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR: Video encoding failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)

    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"  Output: {output_path} ({size_mb:.1f} MB)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Upscale a video using Real-ESRGAN via Replicate API."
    )
    parser.add_argument("input", type=Path, help="Path to the input video file.")
    parser.add_argument(
        "--scale",
        type=int,
        choices=[2, 4],
        default=None,
        help="Upscale factor (default: auto — 4× for ≤1080p, 2× otherwise).",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help=f"Max concurrent API requests (default: {DEFAULT_WORKERS}).",
    )
    parser.add_argument(
        "--rpm",
        type=int,
        default=DEFAULT_RPM,
        help=(
            f"API rate limit in requests per minute (default: {DEFAULT_RPM}). "
            "Replicate enforces 6 RPM for accounts with < $5 credit."
        ),
    )
    parser.add_argument(
        "--seconds",
        type=float,
        default=None,
        help="Only upscale the first N seconds of the video.",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Remove temporary frame directories after completion.",
    )
    args = parser.parse_args()

    # --- Validate input ---
    input_path = args.input.resolve()
    if not input_path.is_file():
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    check_prerequisites()

    # --- Probe video ---
    print(f"\n[1/4] Probing video: {input_path.name}")
    info = probe_video(input_path)
    scale = determine_scale(info["width"], info["height"], args.scale)
    out_w, out_h = info["width"] * scale, info["height"] * scale

    # Apply --seconds limit
    effective_duration = info["duration"]
    if args.seconds is not None:
        effective_duration = min(args.seconds, info["duration"])
    effective_frames = int(info["fps_float"] * effective_duration)

    print(f"  Source:  {info['width']}×{info['height']} @ {info['fps_float']:.2f} fps")
    print(f"  Duration: {info['duration']:.1f}s" + (
        f" (trimmed to {effective_duration:.1f}s)" if args.seconds else ""
    ))
    print(f"  Frames:  ~{effective_frames}")
    print(f"  Scale:   {scale}× → {out_w}×{out_h}")
    print(f"  Audio:   {'yes' if info['has_audio'] else 'no'}")

    # --- Working directories (under output/upscale_video/) ---
    output_path = default_output(
        input_path.stem + '_upscaled' + input_path.suffix,
    )
    work_dir = output_path.parent / f'.upscale_{input_path.stem}'
    frames_dir = work_dir / 'frames'
    upscaled_dir = work_dir / 'upscaled'

    # --- Extract frames ---
    print('\n[2/4] Extracting frames')
    extract_frames(input_path, frames_dir, info['fps'], args.seconds)

    # --- Upscale frames ---
    print(f'\n[3/4] Upscaling frames via Replicate ({REPLICATE_MODEL})')
    failures = upscale_frames(
        frames_dir, upscaled_dir, scale, args.workers, args.rpm
    )
    if failures > 0:
        print(
            f'\n  WARNING: {failures} frame(s) failed to upscale. '
            f'Re-run the script to retry only the missing frames.',
            file=sys.stderr,
        )
        sys.exit(1)

    # --- Reassemble ---
    print('\n[4/4] Reassembling video')
