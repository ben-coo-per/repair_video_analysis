#!/usr/bin/env python3
"""
YouTube Power Tool Repair Video Analyzer

Analyzes YouTube video transcripts to extract structured repair information.

Usage:
    python main.py <input_urls_file> <output_json_file>

Example:
    python main.py urls.txt output.json
"""

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env file from same directory as script
load_dotenv(Path(__file__).parent / ".env")

from transcript import fetch_transcript
from analyzer import analyze_transcript
from models import RepairRecord


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


def main():
    parser = argparse.ArgumentParser(
        description="Analyze YouTube power tool repair videos"
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Text file with YouTube URLs (one per line)",
    )
    parser.add_argument(
        "output_file",
        type=Path,
        help="Output JSON file for extracted repairs",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    # Validate input file exists
    if not args.input_file.exists():
        print(f"Error: Input file not found: {args.input_file}")
        sys.exit(1)

    # Read URLs from input file
    urls = args.input_file.read_text().strip().split("\n")
    urls = [url.strip() for url in urls if url.strip() and not url.strip().startswith("#")]

    if not urls:
        print("Error: No URLs found in input file")
        sys.exit(1)

    print(f"Found {len(urls)} URL(s) to process\n")

    # Process all videos
    all_repairs: list[dict] = []

    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] ", end="")
        repairs = process_video(url)
        all_repairs.extend(repairs)

    # Write output
    print(f"\n\nTotal repairs extracted: {len(all_repairs)}")
    print(f"Writing to: {args.output_file}")

    with open(args.output_file, "w") as f:
        json.dump(all_repairs, f, indent=2)

    print("Done!")


if __name__ == "__main__":
    main()
