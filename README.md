# OOP-DataAnalysis-Project

YouTube Data API v3 kullanan, OOP mimarisiyle yazılmış Python veri analizi projesi.

## Proje Yapısı

```
OOP-DataAnalysis-Project/
├── src/
│   ├── api/
│   │   └── youtube_client.py       # YouTubeClient — API sarmalayıcı
│   ├── models/
│   │   ├── video.py                # Video dataclass
│   │   └── channel.py              # Channel dataclass
│   ├── services/
│   │   ├── data_cleaner.py         # DataCleaner — tekrar kaldırma, outlier tespiti, normalizasyon
│   │   ├── video_analyzer.py       # VideoAnalyzer — istatistik, etkileşim oranı
│   │   ├── channel_analyzer.py     # ChannelAnalyzer — kanal karşılaştırma
│   │   ├── text_analyzer.py        # TextAnalyzer — kelime/etiket frekansı, wordcloud
│   │   └── trend_analyzer.py       # TrendAnalyzer — trend listesi, kategori dağılımı
│   └── utils/
│       └── exceptions.py           # Özel exception sınıfları
├── app.py                          # Streamlit arayüzü (5 sekme)
├── .env                            # API anahtarı (git'e eklenmez)
├── .env.example                    # Şablon
└── requirements.txt
```

## Veri Temizleme (`src/services/data_cleaner.py`)

`DataCleaner` sınıfı ham API verisini aşağıdaki adımlarla işler:

1. **Tekrar kaldırma** — aynı video ID'sine sahip kayıtları temizler (`remove_duplicate_videos`)
2. **Eksik/negatif değer düzeltme** — boş başlık, negatif sayım ve `None` etiketleri varsayılan değerlerle doldurur (`clean_videos`)
3. **Outlier tespiti** — Z-score (eşik = 3.0) ile aşırı görüntüleme değerlerini tespit eder (`detect_view_outliers`)
4. **Min-Max normalizasyonu** — görüntüleme sayılarını 0–1 aralığına ölçekler (`normalize_view_counts`)

## Kurulum

```bash
pip install -r requirements.txt
cp .env.example .env
# .env içine YOUTUBE_API_KEY= değerini girin
streamlit run app.py
```

## Özellikler

| Sekme | İşlev |
|---|---|
| Video Analizi | ID veya URL ile video istatistikleri, etkileşim oranı |
| Kanal Analizi | Kanal ID/@handle/URL ile çoklu kanal karşılaştırma |
| Kelime & Etiket | Başlık kelime bulutu ve etiket bulutu |
| Trend Videoları | Ülke/kategori bazlı trend listesi ve görselleştirme |
| Global En Çok İzlenen | viewCount sıralamasına göre global video listesi |
