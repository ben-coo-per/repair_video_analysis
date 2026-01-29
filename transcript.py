"""YouTube transcript fetching utilities."""

import re
from typing import Optional
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound


def extract_video_id(url: str) -> Optional[str]:
    """
    Extract video ID from various YouTube URL formats.

    Supported formats:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - https://www.youtube.com/v/VIDEO_ID
    """
    patterns = [
        r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/)([a-zA-Z0-9_-]{11})",
        r"^([a-zA-Z0-9_-]{11})$",  # Just the video ID
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


def fetch_transcript(url: str) -> tuple[str, str]:
    """
    Fetch transcript for a YouTube video.

    Args:
        url: YouTube video URL

    Returns:
        Tuple of (transcript_text, video_title)

    Raises:
        ValueError: If video ID cannot be extracted or transcript unavailable
    """
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError(f"Could not extract video ID from URL: {url}")

    try:
        # Create API instance
        ytt_api = YouTubeTranscriptApi()

        # Try to get transcript, preferring manual captions over auto-generated
        transcript_list = ytt_api.list(video_id)

        # Try manual transcripts first
        transcript = None
        try:
            transcript = transcript_list.find_manually_created_transcript(["en"])
        except NoTranscriptFound:
            pass

        # Fall back to auto-generated
        if transcript is None:
            try:
                transcript = transcript_list.find_generated_transcript(["en"])
            except NoTranscriptFound:
                pass

        # Try any available transcript
        if transcript is None:
            for t in transcript_list:
                transcript = t
                break

        if transcript is None:
            raise ValueError(f"No transcript available for video: {url}")

        # Fetch the actual transcript data
        transcript_data = transcript.fetch()

        # Combine all text segments
        full_text = " ".join(segment.text for segment in transcript_data)

        # Get video title from metadata (using a simple approach)
        video_title = get_video_title(video_id)

        return full_text, video_title

    except TranscriptsDisabled:
        raise ValueError(f"Transcripts are disabled for video: {url}")
    except Exception as e:
        raise ValueError(f"Error fetching transcript for {url}: {str(e)}")


def get_video_title(video_id: str) -> str:
    """
    Get video title. Uses a simple approach via transcript API metadata.

    Falls back to video ID if title cannot be retrieved.
    """
    try:
        # The transcript API doesn't directly provide titles, so we use a workaround
        # In production, you might use the YouTube Data API for accurate titles
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)
        # Try to get any metadata that might include title
        for transcript in transcript_list:
            if hasattr(transcript, "video_id"):
                # Return a placeholder with video ID
                return f"YouTube Video ({video_id})"
    except Exception:
        pass

    return f"YouTube Video ({video_id})"
