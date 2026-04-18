"""
YouTube Data API v3 istemci sınıfı
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs, urlparse

from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.models.channel import Channel
from src.models.video import Video
from src.utils.exceptions import (
    ChannelNotFoundError,
    InvalidInputError,
    QuotaExceededError,
    VideoNotFoundError,
    YouTubeAPIError,
)

# .env dosyasını bu dosyadan 3 üst dizinde ara (proje kökü)
_ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH)

YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"


class YouTubeClient:
    """
    YouTube Data API v3 ile iletişimi yöneten sınıf.

    Kullanım:
        client = YouTubeClient()
        video = client.get_video_details("dQw4w9WgXcQ")
    """

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or os.getenv("YOUTUBE_API_KEY")
        if not self._api_key:
            raise InvalidInputError(
                "YouTube API anahtarı bulunamadı. "
                "YOUTUBE_API_KEY ortam değişkenini ayarlayın.",
                field="api_key",
            )
        self._service = build(
            YOUTUBE_API_SERVICE_NAME,
            YOUTUBE_API_VERSION,
            developerKey=self._api_key,
        )

    def _handle_http_error(self, error: HttpError) -> None:
        """HttpError'u proje özel exception'larına dönüştürür."""
        status = error.resp.status
        reason = ""
        try:
            import json
            details = json.loads(error.content.decode())
            reason = details.get("error", {}).get("errors", [{}])[0].get("reason", "")
        except Exception:
            pass

        if status == 403 and reason == "quotaExceeded":
            raise QuotaExceededError()
        raise YouTubeAPIError(str(error), status_code=status, reason=reason)

    def get_video_details(self, video_id: str) -> Video:
        """
        Tek bir video için detaylı istatistikleri döndürür.

        Args:
            video_id: YouTube video ID (ör. 'dQw4w9WgXcQ')

        Returns:
            Video nesnesi

        Raises:
            InvalidInputError: video_id boş/None ise
            VideoNotFoundError: video bulunamazsa
            YouTubeAPIError: API hatası
        """
        if not video_id or not video_id.strip():
            raise InvalidInputError("Video ID boş olamaz.", field="video_id")

        try:
            response = (
                self._service.videos()
                .list(
                    part="snippet,statistics,contentDetails",
                    id=video_id.strip(),
                )
                .execute()
            )
        except HttpError as e:
            self._handle_http_error(e)

        items = response.get("items", [])
        if not items:
            raise VideoNotFoundError(video_id)

        return self._parse_video(items[0])

    def get_videos_by_ids(self, video_ids: list[str]) -> list[Video]:
        """
        Birden fazla video için detaylı istatistikleri döndürür (max 50).

        Args:
            video_ids: Video ID listesi

        Returns:
            Video nesneleri listesi
        """
        if not video_ids:
            raise InvalidInputError("Video ID listesi boş olamaz.", field="video_ids")

        ids = ",".join(v.strip() for v in video_ids[:50])
        try:
            response = (
                self._service.videos()
                .list(
                    part="snippet,statistics,contentDetails",
                    id=ids,
                )
                .execute()
            )
        except HttpError as e:
            self._handle_http_error(e)

        return [self._parse_video(item) for item in response.get("items", [])]

    def get_channel_info(self, channel_input: str) -> Channel:
        """
        Kanal bilgilerini döndürür. URL, handle veya ID kabul eder.

        Args:
            channel_input: Şunlardan biri:
                - Kanal ID:  UCxxxxxx
                - Handle:    @mkbhd  veya  mkbhd
                - URL:       https://youtube.com/@mkbhd
                             https://youtube.com/channel/UCxxxxxx

        Returns:
            Channel nesnesi

        Raises:
            ChannelNotFoundError: kanal bulunamazsa
        """
        if not channel_input or not channel_input.strip():
            raise InvalidInputError("Kanal girişi boş olamaz.", field="channel_input")

        raw = channel_input.strip()

        # URL'den ID veya handle çıkar
        channel_id, handle = self._parse_channel_input(raw)

        try:
            if channel_id:
                response = (
                    self._service.channels()
                    .list(part="snippet,statistics", id=channel_id)
                    .execute()
                )
            else:
                # forHandle parametresi ile ara (@ olmadan)
                response = (
                    self._service.channels()
                    .list(part="snippet,statistics", forHandle=handle)
                    .execute()
                )
        except HttpError as e:
            self._handle_http_error(e)

        items = response.get("items", [])
        if not items:
            raise ChannelNotFoundError(raw)

        return self._parse_channel(items[0])

    def get_trending_videos(
        self,
        region_code: str = "TR",
        category_id: str = "0",
        max_results: int = 25,
    ) -> tuple[list[Video], bool]:
        """
        Belirtilen ülke/kategorideki trend videoları döndürür.

        Args:
            region_code: ISO 3166-1 alpha-2 ülke kodu (ör. 'TR', 'US')
            category_id: YouTube kategori ID ('0' = tüm kategoriler)
            max_results: Döndürülecek maksimum video sayısı (1-50)

        Returns:
            (Video listesi, kategori_dusuruldu_mu) tuple.
            İkinci eleman True ise seçilen kategori o bölgede mevcut değildi
            ve kategori filtresi kaldırılarak tekrar denendi.
        """
        max_results = max(1, min(50, max_results))
        base_params = dict(
            part="snippet,statistics,contentDetails",
            chart="mostPopular",
            regionCode=region_code.upper(),
            maxResults=max_results,
        )

        use_category = category_id and category_id != "0"
        params = {**base_params, "videoCategoryId": category_id} if use_category else base_params

        try:
            response = self._service.videos().list(**params).execute()
            return [self._parse_video(item) for item in response.get("items", [])], False
        except HttpError as e:
            # Kategori bu bölgede desteklenmiyorsa kategorisiz tekrar dene
            if e.resp.status == 404 and use_category:
                try:
                    response = self._service.videos().list(**base_params).execute()
                    return [self._parse_video(item) for item in response.get("items", [])], True
                except HttpError as e2:
                    self._handle_http_error(e2)
            self._handle_http_error(e)

    def search_videos(
        self,
        query: str,
        max_results: int = 20,
        order: str = "relevance",
    ) -> list[Video]:
        """
        Anahtar kelime ile video arar ve detayları döndürür.

        Args:
            query: Arama terimi
            max_results: Maksimum sonuç sayısı (1-50)
            order: Sıralama ('relevance', 'viewCount', 'date', 'rating')

        Returns:
            Video nesneleri listesi
        """
        if not query or not query.strip():
            raise InvalidInputError("Arama terimi boş olamaz.", field="query")

        max_results = max(1, min(50, max_results))
        valid_orders = {"relevance", "viewCount", "date", "rating", "title"}
        if order not in valid_orders:
            raise InvalidInputError(
                f"Geçersiz sıralama. Seçenekler: {valid_orders}",
                field="order",
                value=order,
            )

        try:
            search_response = (
                self._service.search()
                .list(
                    part="id",
                    q=query.strip(),
                    type="video",
                    maxResults=max_results,
                    order=order,
                )
                .execute()
            )
        except HttpError as e:
            self._handle_http_error(e)

        video_ids = [
            item["id"]["videoId"]
            for item in search_response.get("items", [])
            if item.get("id", {}).get("videoId")
        ]

        if not video_ids:
            return []

        return self.get_videos_by_ids(video_ids)

    def search_channels(
        self,
        query: str,
        max_results: int = 20,
        region_code: str = "",
    ) -> list[Channel]:
        """
        Anahtar kelime ile kanal arar ve detaylarını döndürür.

        Args:
            query: Arama terimi
            max_results: Maksimum sonuç sayısı (1-50)
            region_code: Opsiyonel ülke filtresi (ör. 'TR')

        Returns:
            Channel nesneleri listesi
        """
        if not query or not query.strip():
            raise InvalidInputError("Arama terimi boş olamaz.", field="query")

        max_results = max(1, min(50, max_results))
        params = dict(
            part="id",
            q=query.strip(),
            type="channel",
            maxResults=max_results,
        )
        if region_code:
            params["regionCode"] = region_code.upper()

        try:
            search_resp = self._service.search().list(**params).execute()
        except HttpError as e:
            self._handle_http_error(e)

        channel_ids = [
            item["id"]["channelId"]
            for item in search_resp.get("items", [])
            if item.get("id", {}).get("channelId")
        ]
        if not channel_ids:
            return []

        try:
            ch_resp = (
                self._service.channels()
                .list(part="snippet,statistics", id=",".join(channel_ids))
                .execute()
            )
        except HttpError as e:
            self._handle_http_error(e)

        return [self._parse_channel(item) for item in ch_resp.get("items", [])]

    def get_top_channels_by_country(
        self, region_code: str = "TR", max_results: int = 50
    ) -> list[Channel]:
        """
        Belirtilen ülkenin en popüler kanallarını döndürür.
        YouTube'un trend videolarından kanalları çeker,
        o ülkeden olan kanalları filtreler ve abone sayısına göre sıralar.
        Ülke kanalları yetersizse ülke filtresi kaldırılır.

        Args:
            region_code: ISO 3166-1 alpha-2 ülke kodu (ör. 'TR')
            max_results: Döndürülecek maksimum kanal sayısı

        Returns:
            Abone sayısına göre sıralı Channel listesi
        """
        # Trend videoların kanallarını çek
        videos, _ = self.get_trending_videos(
            region_code=region_code, category_id="0", max_results=50
        )
        seen: dict[str, str] = {}
        for v in videos:
            if v.channel_id and v.channel_id not in seen:
                seen[v.channel_id] = v.channel_title

        if not seen:
            return []

        ids = list(seen.keys())[:50]
        try:
            ch_resp = (
                self._service.channels()
                .list(part="snippet,statistics", id=",".join(ids))
                .execute()
            )
        except HttpError as e:
            self._handle_http_error(e)

        all_channels = [self._parse_channel(item) for item in ch_resp.get("items", [])]

        # Sadece o ülkeye ait kanalları al
        local = [c for c in all_channels if c.country.upper() == region_code.upper()]

        # Eğer ülke kanalı 5'ten azsa filtreyi kaldır (bazı kanallar country doldurmaz)
        channels = local if len(local) >= 5 else all_channels

        # Abone sayısına göre büyükten küçüğe sırala
        channels.sort(key=lambda c: c.subscriber_count, reverse=True)

        return channels[:max_results]

    def get_most_viewed_global(
        self, query: str = "", max_results: int = 25
    ) -> list[Video]:
        """
        Global olarak en çok izlenen videoları döndürür.
        YouTube'da gerçek bir "global chart" endpoint olmadığından,
        viewCount sıralamasıyla geniş bir arama yapar.

        Args:
            query: Filtre için arama terimi (boş → tüm videolar)
            max_results: Döndürülecek video sayısı (1-50)

        Returns:
            Video nesneleri listesi (görüntülemeye göre sıralı)
        """
        q = query.strip() if query.strip() else "most viewed"
        return self.search_videos(q, max_results=max_results, order="viewCount")

    def get_video_category_names(self, region_code: str = "TR") -> dict[str, str]:
        """Kategori ID → isim eşlemesini döndürür."""
        try:
            response = (
                self._service.videoCategories()
                .list(part="snippet", regionCode=region_code)
                .execute()
            )
        except HttpError as e:
            self._handle_http_error(e)

        return {
            item["id"]: item["snippet"]["title"]
            for item in response.get("items", [])
        }

    # ------------------------------------------------------------------ #
    #  Özel yardımcı metodlar                                              #
    # ------------------------------------------------------------------ #

    @staticmethod
    def extract_video_id(raw: str) -> str:
        """
        YouTube video URL'sinden veya ham ID'sinden video ID çıkarır.

        Desteklenen formatlar:
            https://www.youtube.com/watch?v=dQw4w9WgXcQ
            https://youtu.be/dQw4w9WgXcQ
            dQw4w9WgXcQ
        """
        raw = raw.strip()
        # youtu.be/ID
        m = re.match(r"(?:https?://)?youtu\.be/([A-Za-z0-9_\-]{11})", raw)
        if m:
            return m.group(1)
        # youtube.com/watch?v=ID
        parsed = urlparse(raw)
        if parsed.netloc in ("www.youtube.com", "youtube.com", "m.youtube.com"):
            qs = parse_qs(parsed.query)
            if "v" in qs:
                return qs["v"][0]
        # Ham 11 karakterlik ID
        if re.match(r"^[A-Za-z0-9_\-]{11}$", raw):
            return raw
        return raw  # olduğu gibi döndür, API hata verir

    @staticmethod
    def _parse_channel_input(raw: str) -> tuple[str, str]:
        """
        Kanal girişinden (channel_id, handle) tuple döndürür.
        Biri dolu, diğeri boş olur.

        Desteklenen formatlar:
            UCxxxxxx               → channel_id
            @handle                → handle (@ olmadan)
            handle                 → handle
            youtube.com/@handle    → handle
            youtube.com/channel/UC → channel_id
        """
        # youtube.com/channel/UCxxxxxx
        m = re.search(r"youtube\.com/channel/([A-Za-z0-9_\-]+)", raw)
        if m:
            return m.group(1), ""

        # youtube.com/@handle
        m = re.search(r"youtube\.com/@([A-Za-z0-9_\.\-]+)", raw)
        if m:
            return "", m.group(1)

        # Doğrudan UCxxxxxx
        if re.match(r"^UC[A-Za-z0-9_\-]{22}$", raw):
            return raw, ""

        # @handle
        if raw.startswith("@"):
            return "", raw[1:]

        # Geri kalan → handle olarak dene
        return "", raw

    @staticmethod
    def _parse_video(item: dict) -> Video:
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})

        published_raw = snippet.get("publishedAt", "")
        try:
            published_at = datetime.fromisoformat(published_raw.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            published_at = datetime.utcnow()

        return Video(
            id=item["id"],
            title=snippet.get("title", ""),
            channel_id=snippet.get("channelId", ""),
            channel_title=snippet.get("channelTitle", ""),
            published_at=published_at,
            view_count=int(stats.get("viewCount", 0)),
            like_count=int(stats.get("likeCount", 0)),
            comment_count=int(stats.get("commentCount", 0)),
            description=snippet.get("description", ""),
            tags=snippet.get("tags", []),
            thumbnail_url=(
                snippet.get("thumbnails", {})
                .get("high", {})
                .get("url", "")
            ),
            duration=item.get("contentDetails", {}).get("duration", ""),
            category_id=snippet.get("categoryId", ""),
        )

    @staticmethod
    def _parse_channel(item: dict) -> Channel:
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})

        published_raw = snippet.get("publishedAt", "")
        try:
            published_at = datetime.fromisoformat(published_raw.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            published_at = None

        return Channel(
            id=item["id"],
            title=snippet.get("title", ""),
            description=snippet.get("description", ""),
            subscriber_count=int(stats.get("subscriberCount", 0)),
            video_count=int(stats.get("videoCount", 0)),
            view_count=int(stats.get("viewCount", 0)),
            country=snippet.get("country", ""),
            published_at=published_at,
            thumbnail_url=(
                snippet.get("thumbnails", {})
                .get("high", {})
                .get("url", "")
            ),
            custom_url=snippet.get("customUrl", ""),
        )
