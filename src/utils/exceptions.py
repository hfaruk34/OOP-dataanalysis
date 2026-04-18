"""
Custom exception sınıfları - OOP-DataAnalysis-Project
"""


class YouTubeAPIError(Exception):
    """YouTube Data API ile ilgili hatalar için."""

    def __init__(self, message: str, status_code: int = None, reason: str = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.reason = reason

    def __str__(self) -> str:
        base = f"YouTube API Hatası: {self.message}"
        if self.status_code:
            base += f" (HTTP {self.status_code})"
        if self.reason:
            base += f" - Neden: {self.reason}"
        return base


class QuotaExceededError(YouTubeAPIError):
    """API kota limiti aşıldığında."""

    def __init__(self):
        super().__init__(
            message="Günlük API kota limiti aşıldı. Yarın tekrar deneyin.",
            status_code=403,
            reason="quotaExceeded",
        )


class VideoNotFoundError(YouTubeAPIError):
    """Video bulunamadığında."""

    def __init__(self, video_id: str):
        super().__init__(
            message=f"'{video_id}' ID'li video bulunamadı veya gizli.",
            status_code=404,
            reason="videoNotFound",
        )
        self.video_id = video_id


class ChannelNotFoundError(YouTubeAPIError):
    """Kanal bulunamadığında."""

    def __init__(self, channel_id: str):
        super().__init__(
            message=f"'{channel_id}' ID'li kanal bulunamadı.",
            status_code=404,
            reason="channelNotFound",
        )
        self.channel_id = channel_id


class DataCleaningError(Exception):
    """Veri temizleme işlemleri sırasında oluşan hatalar."""

    def __init__(self, message: str, field: str = None):
        super().__init__(message)
        self.message = message
        self.field = field

    def __str__(self) -> str:
        base = f"Veri Temizleme Hatası: {self.message}"
        if self.field:
            base += f" (Alan: {self.field})"
        return base


class InvalidInputError(Exception):
    """Geçersiz kullanıcı girdisi."""

    def __init__(self, message: str, field: str = None, value=None):
        super().__init__(message)
        self.message = message
        self.field = field
        self.value = value

    def __str__(self) -> str:
        base = f"Geçersiz Girdi: {self.message}"
        if self.field:
            base += f" (Alan: {self.field}"
            if self.value is not None:
                base += f", Değer: {self.value}"
            base += ")"
        return base
