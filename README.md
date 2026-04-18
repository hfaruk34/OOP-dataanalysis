# OOP-DataAnalysis-Project

YouTube Data API v3 kullanan, OOP mimarisiyle yazılmış Python veri analizi projesi.

## İstenen Kriterler (Markdown)

### 1) API Kullanımı Olan Kodlar

- `src/api/youtube_client.py` içindeki `YouTubeClient` sınıfı doğrudan YouTube Data API v3 ile haberleşir.
- Örnek metotlar:
  - `get_trending_videos(...)`
  - `search_videos(...)`
  - `get_video_details(...)`
  - `get_channel_info(...)`

### 2) Veri Temizleme İşlemleri

- `src/services/data_cleaner.py` içindeki `DataCleaner` sınıfı:
  - Tekrar eden video/kanal kayıtlarını kaldırır (`remove_duplicate_videos`, `remove_duplicate_channels`).
  - Eksik veya hatalı değerleri düzeltir (`clean_videos`, `clean_channels`).
  - Aykırı değer (outlier) tespiti yapar (`detect_view_outliers`).
  - Min-Max normalizasyon uygular (`normalize_view_counts`).

### 3) Veriyi CSV veya Excel Formatında Kaydetme

- `app.py` içinde:
  - **CSV** indirme: `df_display.to_csv(...)` + `st.download_button(...)`
  - **Excel (.xlsx)** indirme: `olustur_excel(...)` + `st.download_button(...)`

### 4) En Az 3 Farklı Veri Görselleştirme

- `app.py` içinde kullanılan görselleştirmelerden bazıları:
  - `px.bar(...)` (bar chart)
  - `px.histogram(...)` (histogram)
  - `px.scatter(..., trendline="ols")` (scatter)
  - `px.pie(...)` (pie chart)
  - `px.box(...)` (box plot)
  - `px.imshow(...)` (heatmap)
  - `px.violin(...)` (violin plot)

### 5) Hata Yönetimi

- `src/utils/exceptions.py` içinde özel exception sınıfları:
  - `YouTubeAPIError`
  - `QuotaExceededError`
  - `VideoNotFoundError`
  - `ChannelNotFoundError`
  - `DataCleaningError`
  - `InvalidInputError`
- `src/api/youtube_client.py` içinde `_handle_http_error(...)` ile API hataları proje exception'larına dönüştürülür.
- `app.py` içinde `try/except` blokları ile hatalar kullanıcıya `st.error(...)` ile gösterilir.

## Proje Yapısı

```text
OOP-DataAnalysis-Project/
├── src/
│   ├── api/
│   │   └── youtube_client.py
│   ├── models/
│   │   ├── video.py
│   │   └── channel.py
│   ├── services/
│   │   ├── data_cleaner.py
│   │   ├── video_analyzer.py
│   │   ├── channel_analyzer.py
│   │   ├── text_analyzer.py
│   │   └── trend_analyzer.py
│   └── utils/
│       └── exceptions.py
├── app.py
├── .env
├── .env.example
└── requirements.txt
```

## Kurulum

```bash
pip install -r requirements.txt
cp .env.example .env
# .env içine YOUTUBE_API_KEY değerini girin
streamlit run app.py
```

## Uygulama Özellikleri

| Sekme | İşlev |
|---|---|
| Video Analizi | ID veya URL ile video istatistikleri ve etkileşim oranı |
| Kanal Analizi | Kanal ID, @handle veya URL ile karşılaştırmalı analiz |
| Kelime ve Etiket | Başlık/etiket analizi ve wordcloud |
| Trend Videoları | Ülke/kategori bazlı trend listeleme ve görselleştirme |
| Global En Çok İzlenen | `viewCount` sıralamasına göre global liste |
