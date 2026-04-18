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

## Uygulama İçeriği (Gerçek `app.py`)

Bu proje, Streamlit ile yazılmış tek sayfalık bir **YouTube trend video analizi** uygulamasıdır.

### Veri Kaynağı ve Seçim

- **Veri kaynağı**: YouTube Data API v3
- **Filtreler**: Ülke (region) ve video sayısı

### Analiz Bölümleri

`app.py` içinde yer alan başlıca analiz ve görselleştirme bölümleri:

- **Veri Seti**: Çekilen veriyi tabloda gösterme + CSV indirme
- **Genel İstatistikler**: Toplam/ortalama metrik kartları
- **Hızlı Grafikler**: Top 10 izlenme, top 10 etkileşim, kategori ortalamaları vb.
- **1. Betimsel İstatistikler**
- **2. Kategori Dağılımı**
- **3. Görüntülenme Dağılımı** (histogram/box + log ölçekli histogram)
- **4. Beğeni ile Görüntülenme Arasındaki İlişki** (scatter + OLS trendline)
- **5. Etkileşim Oranı Analizi** (bar + violin)
- **6. Değişkenler Arası Korelasyon Matrisi** (heatmap)
- **7. Video Süresi ve Performans**
- **8. Kanal Bazlı Performans**
- **9. Yayın Saati ve Görüntülenme İlişkisi**
- **10. Genel Değerlendirme**
- **PDF Raporu** ve **Excel Raporu (.xlsx)** indirme
