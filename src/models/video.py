"""
Video veri modeli
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Video:
    """YouTube video verilerini temsil eden sınıf."""

    id: str
    title: str
    channel_id: str
    channel_title: str
    published_at: datetime
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    description: str = ""
    tags: list[str] = field(default_factory=list)
    thumbnail_url: str = ""
    duration: str = ""
    category_id: str = ""

    @property
    def engagement_rate(self) -> float:
        """Etkileşim oranı: (beğeni + yorum) / görüntüleme."""
        if self.view_count == 0:
            return 0.0
        return round((self.like_count + self.comment_count) / self.view_count * 100, 4)

    @property
    def like_ratio(self) -> float:
        """Beğeni / görüntüleme oranı (%)."""
        if self.view_count == 0:
            return 0.0
        return round(self.like_count / self.view_count * 100, 4)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "channel_id": self.channel_id,
            "channel_title": self.channel_title,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "view_count": self.view_count,
            "like_count": self.like_count,
            "comment_count": self.comment_count,
            "description": self.description,
            "tags": self.tags,
            "thumbnail_url": self.thumbnail_url,
            "duration": self.duration,
            "category_id": self.category_id,
            "engagement_rate": self.engagement_rate,
            "like_ratio": self.like_ratio,
        }

    def __repr__(self) -> str:
        return (
            f"Video(id='{self.id}', title='{self.title[:40]}...', "
            f"views={self.view_count:,})"
        )
