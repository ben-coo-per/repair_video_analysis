#!/usr/bin/env python3
"""
YouTube Power Tool Repair Video Analyzer

Analyzes YouTube video transcripts to extract structured repair information.

Usage:
    python main.py [--delay SECONDS]

Reads URLs from urls_to_add.txt, processes each one:
  1. Fetch transcript & analyze with Claude
  2. Append results to output.json immediately
  3. Move the URL from urls_to_add.txt to urls.txt
"""

import json
import sys
import time
import argparse
from pathlib import Path

from dotenv import load_dotenv

# Load .env file from same directory as script
SCRIPT_DIR = Path(__file__).parent
load_dotenv(SCRIPT_DIR / ".env")

from transcript import fetch_transcript
from analyzer import analyze_transcript

INPUT_FILE = SCRIPT_DIR / "urls_to_add.txt"
ARCHIVE_FILE = SCRIPT_DIR / "urls.txt"
OUTPUT_FILE = SCRIPT_DIR / "output.json"


def process_video(url: str) -> list[dict]:
    """
    Process a single video URL and return extracted repairs.

    Args:
        url: YouTube video URL

    Returns:
        List of repair dictionaries
    """
    url = url.strip()
    if not url or url.startswith("#"):
        return []

    print(f"Processing: {url}")

    try:
        # Fetch transcript
        print("  Fetching transcript...")
        transcript, video_title = fetch_transcript(url)
        print(f"  Title: {video_title}")
        print(f"  Transcript length: {len(transcript)} characters")

        # Analyze with LLM
        print("  Analyzing with Claude...")
        result = analyze_transcript(transcript, url, video_title)

        if result.error:
            print(f"  Error: {result.error}")
            return []

        print(f"  Found {len(result.repairs)} repair(s)")

        return [repair.to_dict() for repair in result.repairs]

    except ValueError as e:
        print(f"  Error: {str(e)}")
        return []
    except Exception as e:
        print(f"  Unexpected error: {str(e)}")
        return []


def load_output() -> list[dict]:
    """Load existing repairs from output.json, or return empty list."""
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, "r") as f:
            return json.load(f)
    return []


def save_output(data: list[dict]) -> None:
    """Write repairs list to output.json."""
    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)


def read_urls(path: Path) -> list[str]:
    """Read non-empty, non-comment lines from a URL file."""
    if not path.exists():
        return []
    lines = path.read_text().strip().split("\n")
    return [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]


def remove_url_from_input(url: str) -> None:
    """Remove a URL from urls_to_add.txt, preserving other lines."""
    if not INPUT_FILE.exists():
        return
    lines = INPUT_FILE.read_text().split("\n")
    remaining = [line for line in lines if line.strip() != url.strip()]
    INPUT_FILE.write_text("\n".join(remaining))


def append_url_to_archive(url: str) -> None:
    """Append a URL to urls.txt."""
    with open(ARCHIVE_FILE, "a") as f:
        f.write(f"{url.strip()}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze YouTube power tool repair videos"
    )
    parser.add_argument(
        "--delay",
        "-d",
        type=float,
        default=5.0,
        help="Delay in seconds between requests to avoid IP bans (default: 5)",
    )

    args = parser.parse_args()

    urls = read_urls(INPUT_FILE)

    if not urls:
        print(f"No URLs found in {INPUT_FILE}")
        sys.exit(0)

    print(f"Found {len(urls)} URL(s) to process\n")

    total_new = 0

    for i, url in enumerate(urls, 1):
        if i > 1 and args.delay > 0:
            print(f"  Waiting {args.delay}s before next request...")
            time.sleep(args.delay)

        print(f"\n[{i}/{len(urls)}] ", end="")
        repairs = process_video(url)

        if repairs:
            # Append to output.json immediately
            all_repairs = load_output()
            all_repairs.extend(repairs)
            save_output(all_repairs)
            total_new += len(repairs)
            print(f"  Saved {len(repairs)} repair(s) to {OUTPUT_FILE}")

        # Move URL from urls_to_add.txt -> urls.txt regardless of success
        remove_url_from_input(url)
        append_url_to_archive(url)
        print(f"  Moved URL to {ARCHIVE_FILE}")

    print(f"\n\nDone! Added {total_new} new repair(s) to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
