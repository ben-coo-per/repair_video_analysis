"""LLM-based transcript analysis using Claude API."""

import json
import os
from typing import Optional

from anthropic import Anthropic

from models import RepairRecord, AnalysisResult


ANALYSIS_PROMPT = """You are an expert at analyzing power tool repair videos. Given a video transcript, extract detailed information about each repair discussed.

For EACH distinct repair in the video, extract:
- brand: Tool manufacturer (e.g., DeWalt, Milwaukee, Makita, Bosch, Ryobi, Craftsman, etc.)
- tool_type: Type of tool (e.g., circular saw, drill, angle grinder, jigsaw, router, sander, etc.)
- model: Model number if mentioned (otherwise null)
- problem: Detailed description of the problem/issue being repaired (be thorough)
- component: The specific component that failed or needed repair (e.g., motor brushes, switch, armature, bearing, cord, trigger, chuck, etc.)
- successful: true if the repair was successful, false otherwise
- failure_reason: If unsuccessful, explain why (otherwise null)

IMPORTANT:
- If multiple repairs are discussed, create a separate entry for each
- Extract as much detail as possible from the transcript
- If information is not clearly stated, use null
- Include power tools (corded or cordless electric tools), battery packs, and chargers
- Battery pack repairs should use tool_type "battery pack" with the appropriate brand
- Be accurate - only include information actually mentioned in the transcript

Respond with a JSON array of repair objects. If no power tool repairs are discussed, return an empty array.

Example response format:
[
  {{
    "brand": "DeWalt",
    "tool_type": "circular saw",
    "model": "DWE575",
    "problem": "The saw was making a grinding noise and the blade would not spin up to full speed. Smoke was visible coming from the motor housing during operation.",
    "component": "motor brushes",
    "successful": true,
    "failure_reason": null
  }}
]

Video Transcript:
{transcript}

Respond ONLY with the JSON array, no other text."""


def analyze_transcript(
    transcript: str,
    video_url: str,
    video_title: str,
    api_key: Optional[str] = None,
) -> AnalysisResult:
    """
    Analyze a transcript using Claude API to extract repair information.

    Args:
        transcript: The full transcript text
        video_url: Source video URL
        video_title: Video title for reference
        api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)

    Returns:
        AnalysisResult containing extracted repairs
    """
    if api_key is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return AnalysisResult(
                video_url=video_url,
                video_title=video_title,
                repairs=[],
                error="ANTHROPIC_API_KEY not set",
            )

    client = Anthropic(api_key=api_key)

    # Truncate transcript if too long (Claude has context limits)
    max_transcript_length = 100000
    if len(transcript) > max_transcript_length:
        transcript = transcript[:max_transcript_length] + "... [truncated]"

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": ANALYSIS_PROMPT.format(transcript=transcript),
                }
            ],
        )

        response_text = message.content[0].text.strip()

        # Strip markdown code blocks if present
        if response_text.startswith("```"):
            # Remove opening ```json or ```
            lines = response_text.split("\n")
            start_idx = 1 if lines[0].startswith("```") else 0
            # Find closing ```
            end_idx = len(lines)
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].strip() == "```":
                    end_idx = i
                    break
            response_text = "\n".join(lines[start_idx:end_idx])

        # Parse JSON response
        repairs_data = json.loads(response_text)

        repairs = []
        for repair_dict in repairs_data:
            repair = RepairRecord(
                brand=repair_dict.get("brand"),
                tool_type=repair_dict.get("tool_type"),
                model=repair_dict.get("model"),
                problem=repair_dict.get("problem", ""),
                component=repair_dict.get("component"),
                successful=repair_dict.get("successful", True),
                failure_reason=repair_dict.get("failure_reason"),
                video_url=video_url,
                video_title=video_title,
            )
            repairs.append(repair)

        return AnalysisResult(
            video_url=video_url,
            video_title=video_title,
            repairs=repairs,
        )

    except json.JSONDecodeError as e:
        return AnalysisResult(
            video_url=video_url,
            video_title=video_title,
            repairs=[],
            error=f"Failed to parse LLM response as JSON: {str(e)}",
        )
    except Exception as e:
        return AnalysisResult(
            video_url=video_url,
            video_title=video_title,
            repairs=[],
            error=f"Analysis error: {str(e)}",
        )
