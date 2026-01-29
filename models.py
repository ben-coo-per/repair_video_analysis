"""Data models for repair video analysis."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class RepairRecord:
    """Single repair entry extracted from a video."""

    brand: Optional[str]
    tool_type: Optional[str]
    model: Optional[str]
    problem: str
    component: Optional[str]
    successful: bool
    failure_reason: Optional[str]
    video_url: str
    video_title: str

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "brand": self.brand,
            "tool_type": self.tool_type,
            "model": self.model,
            "problem": self.problem,
            "component": self.component,
            "successful": self.successful,
            "failure_reason": self.failure_reason,
            "video_url": self.video_url,
            "video_title": self.video_title,
        }


@dataclass
class AnalysisResult:
    """Collection of repairs from a video."""

    video_url: str
    video_title: str
    repairs: list[RepairRecord]
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "video_url": self.video_url,
            "video_title": self.video_title,
            "repairs": [r.to_dict() for r in self.repairs],
            "error": self.error,
        }
