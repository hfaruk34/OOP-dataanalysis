"""
Channel (Kanal) veri modeli
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Channel:
    """YouTube kanal verilerini temsil eden sınıf."""

    id: str
    title: str
    description: str = ""
    subscriber_count: int = 0
    video_count: int = 0
    view_count: int = 0
    country: str = ""
    published_at: Optional[datetime] = None
    thumbnail_url: str = ""
    custom_url: str = ""

    @property
    def views_per_video(self) -> float:
        """Video başına ortalama görüntüleme."""
        if self.video_count == 0:
            return 0.0
        return round(self.view_count / self.video_count, 2)

    @property
    def subscribers_per_video(self) -> float:
        """Video başına abone oranı."""
        if self.video_count == 0:
            return 0.0
        return round(self.subscriber_count / self.video_count, 2)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "subscriber_count": self.subscriber_count,
            "video_count": self.video_count,
            "view_count": self.view_count,
            "country": self.country,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "thumbnail_url": self.thumbnail_url,
            "custom_url": self.custom_url,
            "views_per_video": self.views_per_video,
            "subscribers_per_video": self.subscribers_per_video,
        }

    def __repr__(self) -> str:
        return (
            f"Channel(id='{self.id}', title='{self.title}', "
            f"subscribers={self.subscriber_count:,})"
        )
