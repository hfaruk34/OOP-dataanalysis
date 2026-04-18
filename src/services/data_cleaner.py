"""
Veri temizleme servisi
"""

import statistics
from typing import Optional

from src.models.channel import Channel
from src.models.video import Video
from src.utils.exceptions import DataCleaningError


class DataCleaner:
    """
    Video ve kanal verilerini temizleyen, doğrulayan sınıf.

    Kullanım:
        cleaner = DataCleaner()
        clean_videos = cleaner.clean_videos(raw_videos)
    """

    def clean_videos(self, videos: list[Video]) -> list[Video]:
        """
        Video listesini temizler: tekrarları kaldırır, outlier'ları işaretler.

        Args:
            videos: Ham Video nesneleri listesi

        Returns:
            Temizlenmiş Video listesi

        Raises:
            DataCleaningError: Temizleme işlemi başarısız olursa
        """
        if not videos:
            return []

        try:
            unique = self.remove_duplicate_videos(videos)
            validated = [self._validate_video(v) for v in unique]
            return validated
        except DataCleaningError:
            raise
        except Exception as e:
            raise DataCleaningError(f"Video temizleme başarısız: {e}")

    def clean_channels(self, channels: list[Channel]) -> list[Channel]:
        """Kanal listesini temizler."""
        if not channels:
            return []
        try:
            unique = self.remove_duplicate_channels(channels)
            return [self._validate_channel(c) for c in unique]
        except DataCleaningError:
            raise
        except Exception as e:
            raise DataCleaningError(f"Kanal temizleme başarısız: {e}")

    @staticmethod
    def remove_duplicate_videos(videos: list[Video]) -> list[Video]:
        """ID'ye göre tekrar eden videoları kaldırır."""
        seen: set[str] = set()
        result = []
        for v in videos:
            if v.id not in seen:
                seen.add(v.id)
                result.append(v)
        return result

    @staticmethod
    def remove_duplicate_channels(channels: list[Channel]) -> list[Channel]:
        """ID'ye göre tekrar eden kanalları kaldırır."""
        seen: set[str] = set()
        result = []
        for c in channels:
            if c.id not in seen:
                seen.add(c.id)
                result.append(c)
        return result

    def detect_view_outliers(
        self, videos: list[Video], z_threshold: float = 3.0
    ) -> list[Video]:
        """
        Z-score yöntemi ile görüntüleme sayısında aşırı değer (outlier) tespiti.

        Args:
            videos: Video listesi
            z_threshold: Z-score eşiği (varsayılan 3.0)

        Returns:
            Outlier olan videoların listesi
        """
        if len(videos) < 3:
            return []

        counts = [v.view_count for v in videos]
        mean = statistics.mean(counts)
        stdev = statistics.stdev(counts)

        if stdev == 0:
            return []

        return [
            v for v in videos if abs((v.view_count - mean) / stdev) > z_threshold
        ]

    def normalize_view_counts(self, videos: list[Video]) -> list[float]:
        """
        Görüntüleme sayılarını 0-1 arasında normalize eder (Min-Max).

        Returns:
            Her videoya karşılık gelen normalize değerler listesi
        """
        if not videos:
            return []

        counts = [v.view_count for v in videos]
        min_v = min(counts)
        max_v = max(counts)

        if max_v == min_v:
            return [0.5] * len(videos)

        return [(c - min_v) / (max_v - min_v) for c in counts]

    @staticmethod
    def _validate_video(video: Video) -> Video:
        """Eksik/negatif sayısal değerleri düzeltir."""
        video.view_count = max(0, video.view_count)
        video.like_count = max(0, video.like_count)
        video.comment_count = max(0, video.comment_count)
        if not video.title:
            video.title = "(Başlık yok)"
        if video.tags is None:
            video.tags = []
        return video

    @staticmethod
    def _validate_channel(channel: Channel) -> Channel:
        """Eksik/negatif sayısal değerleri düzeltir."""
        channel.subscriber_count = max(0, channel.subscriber_count)
        channel.video_count = max(0, channel.video_count)
        channel.view_count = max(0, channel.view_count)
        if not channel.title:
            channel.title = "(Kanal adı yok)"
        return channel
