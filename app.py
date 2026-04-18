"""
YouTube Trend Video Analizi
Veri kaynagi: YouTube Data API v3
"""

import sys
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import matplotlib.pyplot as plt
from wordcloud import WordCloud

from src.api.youtube_client import YouTubeClient
from src.services.data_cleaner import DataCleaner
from src.utils.exceptions import InvalidInputError, QuotaExceededError

# ─────────────────────────────────────────────────────────────
#  Sayfa ayarlari
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="YouTube Trend Analizi",
    page_icon="▶",
    layout="wide",
)

CATEGORY_NAMES = {
    "1": "Film & Animasyon", "2": "Otomobil", "10": "Muzik",
    "15": "Evcil Hayvanlar", "17": "Spor", "20": "Oyun",
    "22": "Insanlar & Blog", "23": "Komedi", "24": "Eglence",
    "25": "Haberler & Politika", "26": "Nasil Yapilir",
    "27": "Egitim", "28": "Bilim & Teknoloji", "29": "Aktivizm",
}

ULKELER = {
    "Turkiye": "TR",
    "Amerika": "US",
    "Almanya": "DE",
    "Ingiltere": "GB",
    "Japonya": "JP",
}


# ─────────────────────────────────────────────────────────────
#  API baglantisi
# ─────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_client():
    # Streamlit Cloud secrets -> lokal .env sirasıyla dene
    api_key = None
    try:
        api_key = st.secrets["YOUTUBE_API_KEY"]
    except Exception:
        pass  # secrets.toml yoksa .env'den okunur
    try:
        return YouTubeClient(api_key=api_key)
    except InvalidInputError:
        return None

client = get_client()
cleaner = DataCleaner()

if client is None:
    st.error("API anahtari bulunamadi. Streamlit secrets veya .env dosyasini kontrol edin.")
    st.stop()


# ─────────────────────────────────────────────────────────────
#  Veri cekme
# ─────────────────────────────────────────────────────────────
def fetch_trends(region: str, n: int):
    videos, _ = client.get_trending_videos(region_code=region, max_results=n)
    return cleaner.clean_videos(videos)


def parse_duration(dur: str) -> float:
    """ISO 8601 sure stringini dakikaya cevirir. Ornek: PT4M13S -> 4.22"""
    if not dur:
        return 0.0
    pattern = r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?"
    m = re.match(pattern, dur)
    if not m:
        return 0.0
    hours = int(m.group(1) or 0)
    mins  = int(m.group(2) or 0)
    secs  = int(m.group(3) or 0)
    return round(hours * 60 + mins + secs / 60, 2)


def build_dataframe(videos) -> pd.DataFrame:
    rows = []
    for v in videos:
        rows.append({
            "video_id": v.id,
            "baslik": v.title[:55] + ("..." if len(v.title) > 55 else ""),
            "kanal": v.channel_title,
            "kategori": CATEGORY_NAMES.get(v.category_id, "Diger"),
            "goruntulenme": v.view_count,
            "begeni": v.like_count,
            "yorum": v.comment_count,
            "etkilesim_orani": v.engagement_rate,
            "begeni_orani": v.like_ratio,
            "sure_dk": parse_duration(v.duration),
            "yayın_tarihi": v.published_at.strftime("%Y-%m-%d") if v.published_at else "",
            "yayın_saati": v.published_at.hour if v.published_at else 0,
            "tag_sayisi": len(v.tags),
        })
    df = pd.DataFrame(rows)
    return df


# ─────────────────────────────────────────────────────────────
#  Sidebar — Veri secimi
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Veri Ayarlari")
    ulke_adi  = st.selectbox("Ulke", list(ULKELER.keys()), index=0)
    video_say = st.slider("Video sayisi", 10, 50, 50, step=10)
    getir_btn = st.button("Veriyi Getir", use_container_width=True, type="primary")
    st.divider()
    st.markdown("**Hakkinda**")
    st.caption("YouTube Data API v3 kullanilarak cekilen trend video verileri uzerinde istatistiksel analiz yapilmaktadir.")

region_code = ULKELER[ulke_adi]

# ─────────────────────────────────────────────────────────────
#  Veri yukleme — session_state ile kontrol
# ─────────────────────────────────────────────────────────────
state_key = f"{region_code}_{video_say}"

if getir_btn or "videos" not in st.session_state or st.session_state.get("state_key") != state_key:
    with st.spinner(f"{ulke_adi} trend videolari yukluyor..."):
        try:
            videos = fetch_trends(region_code, video_say)
        except QuotaExceededError:
            st.error("API gunluk kotasi doldu. Yarin tekrar deneyin.")
            st.stop()
        except Exception as e:
            st.error(f"Veri cekilemedi: {e}")
            st.stop()

    if not videos:
        st.warning("Bu bolge icin trend video bulunamadi.")
        st.stop()

    st.session_state["videos"]    = videos
    st.session_state["state_key"] = state_key

videos = st.session_state["videos"]
df = build_dataframe(videos)

# ─────────────────────────────────────────────────────────────
#  Baslik
# ─────────────────────────────────────────────────────────────
st.title("YouTube Trend Video Analizi")
st.markdown(
    f"**Bolge:** {ulke_adi} &nbsp;|&nbsp; "
    f"**Video sayisi:** {len(df)} &nbsp;|&nbsp; "
    f"**Veri kaynagi:** YouTube Data API v3"
)

# ─────────────────────────────────────────────────────────────
#  Veri Seti (en uste)
# ─────────────────────────────────────────────────────────────
st.divider()
st.subheader("Veri Seti")
st.caption("YouTube Data API v3 ile cekilen ham veri. Her satir bir trend videoyu temsil eder.")

df_display = df.drop(columns=["video_id"]).rename(columns={
    "baslik": "Baslik",
    "kanal": "Kanal",
    "kategori": "Kategori",
    "goruntulenme": "Goruntulenme",
    "begeni": "Begeni",
    "yorum": "Yorum",
    "etkilesim_orani": "Etkilesim %",
    "begeni_orani": "Begeni %",
    "sure_dk": "Sure (dk)",
    "yayın_tarihi": "Yayin Tarihi",
    "yayın_saati": "Saat",
    "tag_sayisi": "Tag",
})
df_display.index = range(1, len(df_display) + 1)
df_display.index.name = "No"
st.dataframe(df_display, use_container_width=True, hide_index=False, height=320)

csv_bytes = df_display.to_csv(index=True).encode("utf-8")
st.download_button(
    label="Veri setini CSV olarak indir",
    data=csv_bytes,
    file_name=f"youtube_trend_{ulke_adi.lower()}.csv",
    mime="text/csv",
)

# ─────────────────────────────────────────────────────────────
#  Hizli Istatistikler
# ─────────────────────────────────────────────────────────────
st.divider()
st.subheader("Genel Istatistikler")

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Toplam Video",           f"{len(df)}")
c2.metric("Toplam Goruntulenme",    f"{df['goruntulenme'].sum() / 1_000_000:.1f}M")
c3.metric("Ort. Goruntulenme",      f"{df['goruntulenme'].mean() / 1_000:.0f}B")
c4.metric("En Yuksek Goruntulenme", f"{df['goruntulenme'].max() / 1_000_000:.1f}M")
c5.metric("Ort. Etkilesim %",       f"{df['etkilesim_orani'].mean():.3f}%")
c6.metric("Ort. Sure",              f"{df['sure_dk'].mean():.1f} dk")

c7, c8, c9, c10, c11, c12 = st.columns(6)
c7.metric("Toplam Begeni",          f"{df['begeni'].sum() / 1_000_000:.1f}M")
c8.metric("Toplam Yorum",           f"{df['yorum'].sum() / 1_000:.0f}B")
c9.metric("Ort. Begeni",            f"{df['begeni'].mean() / 1_000:.0f}B")
c10.metric("Ort. Yorum",            f"{df['yorum'].mean():.0f}")
c11.metric("En Populer Kategori",   df['kategori'].value_counts().idxmax())
c12.metric("Benzersiz Kanal",       f"{df['kanal'].nunique()}")

c13, c14, c15, c16, c17, c18 = st.columns(6)
c13.metric("Min Goruntulenme",      f"{df['goruntulenme'].min():,}")
c14.metric("Medyan Goruntulenme",   f"{df['goruntulenme'].median() / 1_000:.0f}B")
c15.metric("Std Sapma (Gor.)",      f"{df['goruntulenme'].std() / 1_000_000:.1f}M")
c16.metric("Max Begeni",            f"{df['begeni'].max() / 1_000:.0f}B")
c17.metric("Max Yorum",             f"{df['yorum'].max():,}")
c18.metric("En Uzun Video",         f"{df['sure_dk'].max():.0f} dk")

st.divider()

# ─── Hizli Grafikler ───────────────────────────────────────
st.subheader("Hizli Grafikler")

# Grafik 1: En cok izlenen 10 video
top10 = df.nlargest(10, "goruntulenme")[["baslik", "kanal", "goruntulenme"]].sort_values("goruntulenme")
fig_top10 = px.bar(
    top10, x="goruntulenme", y="baslik", orientation="h",
    title="En Cok Izlenen 10 Video",
    labels={"goruntulenme": "Goruntulenme", "baslik": "Video", "kanal": "Kanal"},
    color="goruntulenme", color_continuous_scale="Blues",
    hover_data={"kanal": True},
    text="goruntulenme",
)
fig_top10.update_traces(texttemplate="%{text:,}", textposition="outside")
fig_top10.update_layout(coloraxis_showscale=False, margin=dict(t=50, b=20, l=10, r=80), height=420)
st.plotly_chart(fig_top10, use_container_width=True)

# Grafik 2: En yuksek etkilesim oranlı 10 video
top10_eng = df.nlargest(10, "etkilesim_orani")[["baslik", "kanal", "etkilesim_orani"]].sort_values("etkilesim_orani")
fig_eng10 = px.bar(
    top10_eng, x="etkilesim_orani", y="baslik", orientation="h",
    title="En Yuksek Etkilesim Oranlı 10 Video",
    labels={"etkilesim_orani": "Etkilesim %", "baslik": "Video", "kanal": "Kanal"},
    color="etkilesim_orani", color_continuous_scale="Greens",
    hover_data={"kanal": True},
    text="etkilesim_orani",
)
fig_eng10.update_traces(texttemplate="%{text:.3f}%", textposition="outside")
fig_eng10.update_layout(coloraxis_showscale=False, margin=dict(t=50, b=20, l=10, r=80), height=420)
st.plotly_chart(fig_eng10, use_container_width=True)

# Grafik 3: Kategoriye gore ortalama goruntulenme
kat_ort = df.groupby("kategori")["goruntulenme"].mean().sort_values(ascending=False).reset_index()
kat_ort.columns = ["Kategori", "Ort. Goruntulenme"]
fig_kat_ort = px.bar(
    kat_ort, x="Kategori", y="Ort. Goruntulenme",
    title="Kategoriye Gore Ortalama Goruntulenme",
    labels={"Kategori": "Kategori", "Ort. Goruntulenme": "Ort. Goruntulenme"},
    color="Ort. Goruntulenme", color_continuous_scale="Oranges",
    text="Ort. Goruntulenme",
)
fig_kat_ort.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
fig_kat_ort.update_layout(
    coloraxis_showscale=False,
    xaxis_tickangle=-30,
    margin=dict(t=50, b=80, l=10, r=20),
    height=420,
)
st.plotly_chart(fig_kat_ort, use_container_width=True)

# Grafik 4: Begeni sayisi dagilimi
fig_begeni_hist = px.histogram(
    df, x="begeni", nbins=15,
    title="Begeni Sayisi Dagilimi",
    labels={"begeni": "Begeni Sayisi", "count": "Video Sayisi"},
    color_discrete_sequence=["#f783ac"],
)
fig_begeni_hist.update_layout(bargap=0.05, margin=dict(t=50, b=40), height=400)
st.plotly_chart(fig_begeni_hist, use_container_width=True)

# Grafik 5: Kategoriye gore yorum box plot
fig_yorum_box = px.box(
    df, x="kategori", y="yorum",
    title="Kategoriye Gore Yorum Sayisi Dagilimi",
    labels={"yorum": "Yorum Sayisi", "kategori": "Kategori"},
    color="kategori",
    color_discrete_sequence=px.colors.qualitative.Pastel,
    points="outliers",
)
fig_yorum_box.update_layout(
    showlegend=False,
    xaxis_tickangle=-30,
    margin=dict(t=50, b=80),
    height=420,
)
st.plotly_chart(fig_yorum_box, use_container_width=True)

# Grafik 6: Kanal bazli toplam goruntulenme (en cok izlenen 15 kanal)
kanal_hizli = (
    df.groupby("kanal")["goruntulenme"].sum()
    .sort_values(ascending=False)
    .head(15)
    .reset_index()
)
kanal_hizli.columns = ["Kanal", "Toplam Goruntulenme"]
fig_kanal_hizli = px.bar(
    kanal_hizli.sort_values("Toplam Goruntulenme"),
    x="Toplam Goruntulenme", y="Kanal", orientation="h",
    title="En Cok Izlenen 15 Kanal (Toplam Goruntulenme)",
    labels={"Toplam Goruntulenme": "Toplam Goruntulenme", "Kanal": ""},
    color="Toplam Goruntulenme", color_continuous_scale="Purples",
    text="Toplam Goruntulenme",
)
fig_kanal_hizli.update_traces(texttemplate="%{text:,}", textposition="outside")
fig_kanal_hizli.update_layout(coloraxis_showscale=False, margin=dict(t=50, b=20, l=10, r=80), height=500)
st.plotly_chart(fig_kanal_hizli, use_container_width=True)

st.divider()


# ─────────────────────────────────────────────────────────────
#  BOLUM 1 — Betimsel Istatistikler
# ─────────────────────────────────────────────────────────────
st.header("1. Betimsel Istatistikler")

st.markdown(
    """
    Betimsel istatistikler, veri setinin genel yapisini anlamak icin kullanilan temel olcutlerdir.
    Ortalama, medyan, standart sapma ve ceyrekler arasi aralik gibi degerler;
    verideki merkezi egilimi, yayilimi ve olagandisiliklari ortaya koyar.
    Asagida sayisal degiskenlere ait ozet istatistikler yer almaktadir.
    """
)

num_cols = ["goruntulenme", "begeni", "yorum", "etkilesim_orani", "sure_dk", "tag_sayisi"]
desc = df[num_cols].describe().round(2)
desc.index = ["Gozlem", "Ortalama", "Std Sapma", "Min", "Q1 (%25)", "Medyan (%50)", "Q3 (%75)", "Max"]
desc.columns = ["Goruntulenme", "Begeni", "Yorum", "Etkilesim %", "Sure (dk)", "Tag Sayisi"]

st.dataframe(desc, use_container_width=True)

col_s1, col_s2, col_s3, col_s4 = st.columns(4)
col_s1.metric("Ort. Goruntulenme", f"{df['goruntulenme'].mean():,.0f}")
col_s2.metric("Medyan Goruntulenme", f"{df['goruntulenme'].median():,.0f}")
col_s3.metric("Ort. Etkilesim %", f"{df['etkilesim_orani'].mean():.3f}%")
col_s4.metric("Ort. Video Suresi", f"{df['sure_dk'].mean():.1f} dk")

st.divider()


# ─────────────────────────────────────────────────────────────
#  BOLUM 3 — Kategori Dagilimi
# ─────────────────────────────────────────────────────────────
st.header("2. Kategori Dagilimi")

st.markdown(
    """
    Trend videolarin kategori dagilimi incelendiginde platfrom uzerinde hangi icerik turlerinin
    on plana ciktigi gorulabilmektedir. Ornegin muzik veya eglence kategorilerinin agirlikli olmasi,
    kullanicilarin kisa sureli, pasif tuketim iceriklere yoneldigine isaret eder.
    Egitim veya bilim-teknoloji gibi kategorilerin payi ise izleyici kitlesinin bilgi odakli
    taleplerine dair fikir vermektedir.
    """
)

kat_say = df["kategori"].value_counts().reset_index()
kat_say.columns = ["Kategori", "Video Sayisi"]

col_k1, col_k2 = st.columns(2)
with col_k1:
    fig_pie = px.pie(
        kat_say, values="Video Sayisi", names="Kategori",
        title="Kategorilere Gore Video Orani",
        color_discrete_sequence=px.colors.qualitative.Set2,
        hole=0.35,
    )
    fig_pie.update_traces(textposition="inside", textinfo="percent+label")
    fig_pie.update_layout(showlegend=False, margin=dict(t=50, b=10, l=10, r=10))
    st.plotly_chart(fig_pie, use_container_width=True)

with col_k2:
    fig_kat = px.bar(
        kat_say.sort_values("Video Sayisi"),
        x="Video Sayisi", y="Kategori", orientation="h",
        title="Kategori Bazi Video Sayisi",
        color="Video Sayisi",
        color_continuous_scale="Blues",
        text="Video Sayisi",
    )
    fig_kat.update_traces(textposition="outside")
    fig_kat.update_layout(coloraxis_showscale=False, margin=dict(t=50, b=10, l=10, r=30))
    st.plotly_chart(fig_kat, use_container_width=True)

st.divider()


# ─────────────────────────────────────────────────────────────
#  BOLUM 4 — Goruntulenme Dagilimi (Histogram + Box Plot)
# ─────────────────────────────────────────────────────────────
st.header("3. Goruntulenme Dagilimi")

st.markdown(
    """
    Goruntulenme sayisinin dagilimi incelendiginde sagdan carpik (pozitif carpiklik) bir yapi
    sergiledigi gorulmektedir. Baska bir deyisle buyuk cogunluk gorece dusukt izlenme sayisina
    sahipken az sayida video cok yuksek goruntulenme degerlerine ulasabilmektedir.
    Bu durum YouTube gibi platformlarda icerik tuketimininin "long-tail" ozelligi tasidiginini
    gostermektedir. Histogram araligi 10 gruba bolunmustir; kutu grafigi ise ceyrekler arasi
    aralik (IQR) ve aykiri deger konumlarini gostermektedir.
    """
)

col_h1, col_h2 = st.columns(2)
with col_h1:
    fig_hist = px.histogram(
        df, x="goruntulenme", nbins=15,
        title="Goruntulenme Sayisi Histogrami",
        labels={"goruntulenme": "Goruntulenme", "count": "Video Sayisi"},
        color_discrete_sequence=["#4dabf7"],
    )
    fig_hist.update_layout(bargap=0.05, margin=dict(t=50, b=30))
    st.plotly_chart(fig_hist, use_container_width=True)

with col_h2:
    fig_box = px.box(
        df, y="goruntulenme",
        title="Goruntulenme Kutu Grafigi (Box Plot)",
        labels={"goruntulenme": "Goruntulenme"},
        color_discrete_sequence=["#74c0fc"],
        points="all",
    )
    fig_box.update_layout(margin=dict(t=50, b=30))
    st.plotly_chart(fig_box, use_container_width=True)

# Log olcekli histogram
st.markdown(
    """
    **Log olcekli dagilim:** Goruntulenme degerleri normal dagilimdan uzak oldugu icin
    logaritmik olcek uygulandiginda dagilim daha simetrik bir goruntu kazanmaktadir.
    Bu durum, verinin log-normal bir dagilim sergiledigine isaret etmektedir.
    """
)
df["log_goruntulenme"] = np.log1p(df["goruntulenme"])
fig_loghist = px.histogram(
    df, x="log_goruntulenme", nbins=20,
    title="Goruntulenme Sayisi (Log Olcekli) Histogrami",
    labels={"log_goruntulenme": "ln(Goruntulenme + 1)", "count": "Video Sayisi"},
    color_discrete_sequence=["#69db7c"],
)
fig_loghist.update_layout(bargap=0.04, margin=dict(t=50, b=30))
st.plotly_chart(fig_loghist, use_container_width=True)

st.divider()


# ─────────────────────────────────────────────────────────────
#  BOLUM 5 — Begeni - Goruntulenme Iliskisi
# ─────────────────────────────────────────────────────────────
st.header("4. Begeni ile Goruntulenme Arasindaki Iliski")

st.markdown(
    """
    Begeni sayisi ile goruntulenme sayisi arasinda guclu ve pozitif bir dogrusal iliski
    beklenmektedir. Bununla birlikte bazi videolarin goruntulenme sayisina oranla anormal
    derecede yuksek ya da dusuk begeni aldigi gorulmektedir. Yuksek goruntulenme-dusuk begeni
    durumu genellikle algoritma kaynakli zorunlu izlenmelerde gozlemlenmekte;
    yuksek begeni-gorece dusuk goruntulenme ise baglantili topluluklarin yogun ilgisini
    yansitmaktadir. Scatter grafiginin renk kodlamasi kategorileri, boyut ise yorum sayisini
    temsil etmektedir.
    """
)

df["yorum_scaled"] = np.sqrt(df["yorum"]).clip(upper=500) + 5
fig_scatter = px.scatter(
    df, x="goruntulenme", y="begeni",
    color="kategori",
    size="yorum_scaled",
    hover_name="baslik",
    hover_data={"kanal": True, "etkilesim_orani": ":.3f", "yorum_scaled": False},
    title="Goruntulenme vs Begeni (renk=kategori, boyut=yorum)",
    labels={
        "goruntulenme": "Goruntulenme",
        "begeni": "Begeni",
        "kategori": "Kategori",
    },
    trendline="ols",
    trendline_scope="overall",
    opacity=0.8,
)
fig_scatter.update_layout(margin=dict(t=50, b=30))
st.plotly_chart(fig_scatter, use_container_width=True)

# Pearson korelasyon
corr_val = df["goruntulenme"].corr(df["begeni"])
st.info(
    f"Pearson korelasyon katsayisi (goruntulenme ~ begeni): **r = {corr_val:.4f}**  "
    f"— {'guclu pozitif iliski' if corr_val > 0.7 else 'orta duzey iliski' if corr_val > 0.4 else 'zayif iliski'}"
)

st.divider()


# ─────────────────────────────────────────────────────────────
#  BOLUM 6 — Etkilesim Orani Analizi
# ─────────────────────────────────────────────────────────────
st.header("5. Etkilesim Orani Analizi")

st.markdown(
    """
    Etkilesim orani (engagement rate), bir videonun izleyicileri ne kadar harekete gecirdigini
    gosteren onemli bir performans metrikidir. Bu calismada etkilesim orani
    (begeni + yorum) / goruntulenme formulu ile hesaplanmistir.
    Yuksek etkilesim orani genellikle niş topluluklara hitap eden, izleyicinin aktif katilimini
    tesvik eden iceriklerle iliskilendirilmektedir.
    Violin grafigi, her kategorinin etkilesim dagilimini ve yogunlugunu ayni anda gostermektedir.
    """
)

# Violin plot — etkilesim oranlari kategoriye gore
kat_engag = df.groupby("kategori")["etkilesim_orani"].mean().sort_values(ascending=False).reset_index()
fig_eng_bar = px.bar(
    kat_engag, x="etkilesim_orani", y="kategori", orientation="h",
    title="Kategoriye Gore Ortalama Etkilesim Orani",
    labels={"etkilesim_orani": "Ort. Etkilesim %", "kategori": "Kategori"},
    color="etkilesim_orani",
    color_continuous_scale="Greens",
    text="etkilesim_orani",
)
fig_eng_bar.update_traces(texttemplate="%{text:.3f}%", textposition="outside")
fig_eng_bar.update_layout(coloraxis_showscale=False, margin=dict(t=50, b=10, l=10, r=60))
st.plotly_chart(fig_eng_bar, use_container_width=True)

# Violin grafiğini yalnizca birden fazla kategori varsa goster
kat_groups = df["kategori"].value_counts()
kat_violin_filter = kat_groups[kat_groups >= 2].index.tolist()
df_violin = df[df["kategori"].isin(kat_violin_filter)]

if len(df_violin["kategori"].unique()) >= 2:
    st.markdown(
        """
        Asagidaki violin grafigi, kategorilerin etkilesim orani dagilimlari icin
        yogunluk kestirimini gostermektedir. Simetrik ve dar bir violin dusuk
        degiskenlige; genis ve asimetrik bir violin ise heterojen bir dagilima isaret eder.
        """
    )
    fig_violin = px.violin(
        df_violin, x="kategori", y="etkilesim_orani",
        box=True, points="all",
        title="Kategoriye Gore Etkilesim Orani Dagilimi (Violin + Box)",
        labels={"etkilesim_orani": "Etkilesim %", "kategori": "Kategori"},
        color="kategori",
        color_discrete_sequence=px.colors.qualitative.Set3,
    )
    fig_violin.update_layout(showlegend=False, margin=dict(t=50, b=30))
    st.plotly_chart(fig_violin, use_container_width=True)

st.divider()


# ─────────────────────────────────────────────────────────────
#  BOLUM 7 — Korelasyon Matrisi (Isil Harita)
# ─────────────────────────────────────────────────────────────
st.header("6. Degiskenler Arasi Korelasyon Matrisi")

st.markdown(
    """
    Korelasyon matrisi, sayisal degiskenler arasindaki ikili dogrusal iliskilerin bir arada
    goruntulenebilmesini saglamaktadir. Deger 1'e yaklastikca guclu pozitif, -1'e yaklastikca
    guclu negatif iliski; 0 civarinda ise iliski zayiflamaktadir.
    Isil harita (heatmap) uzerindeki her hucre, ilgili iki degisken arasindaki Pearson
    korelasyon katsayisini gostermektedir. Bu analiz, hangi degiskenlerin birlikte hareket
    ettigini ve hangi iliskilerin istatistiksel olarak anlamli oldugunu belirlemek acisindan
    kritik oneme sahiptir.
    """
)

corr_cols = {
    "goruntulenme": "Goruntulenme",
    "begeni": "Begeni",
    "yorum": "Yorum",
    "etkilesim_orani": "Etkilesim %",
    "sure_dk": "Sure (dk)",
    "tag_sayisi": "Tag Sayisi",
}
corr_df = df[list(corr_cols.keys())].rename(columns=corr_cols)
corr_matrix = corr_df.corr().round(3)

fig_heat = px.imshow(
    corr_matrix,
    text_auto=True,
    color_continuous_scale="RdBu_r",
    zmin=-1, zmax=1,
    title="Pearson Korelasyon Matrisi",
    aspect="auto",
)
fig_heat.update_layout(margin=dict(t=60, b=40, l=40, r=40))
st.plotly_chart(fig_heat, use_container_width=True)

st.divider()


# ─────────────────────────────────────────────────────────────
#  BOLUM 8 — Video Suresi Analizi
# ─────────────────────────────────────────────────────────────
st.header("7. Video Suresi ve Performans")

st.markdown(
    """
    Video suresi, izleyici davranisi uzerinde dogrudan etkisi olan bir degiskendir.
    Kisa iceriklerin (< 5 dakika) hizli tuketimi kolaylastirdigi ve goruntulenme sayisini
    artirdigi bilinmektedir. Buna karsin uzun iceriklerin yorum ve begeni alinmasi acisindan
    daha avantajli oldugu literaturde bircok calismada belgelenmistir.
    Asagida sure ile goruntulenme arasindaki iliski scatter grafigi ile gosterilmis,
    ek olarak sure araligina gore ortalama goruntulenme bar grafiginde karsilastirilmistir.
    """
)

col_d1, col_d2 = st.columns(2)
with col_d1:
    fig_dur_scat = px.scatter(
        df[df["sure_dk"] > 0], x="sure_dk", y="goruntulenme",
        title="Video Suresi vs Goruntulenme",
        labels={"sure_dk": "Sure (dakika)", "goruntulenme": "Goruntulenme"},
        trendline="lowess",
        color="kategori",
        opacity=0.75,
        hover_name="baslik",
    )
    fig_dur_scat.update_layout(showlegend=False, margin=dict(t=50, b=30))
    st.plotly_chart(fig_dur_scat, use_container_width=True)

with col_d2:
    bins = [0, 2, 5, 10, 20, 60, 300]
    labels_bin = ["0-2 dk", "2-5 dk", "5-10 dk", "10-20 dk", "20-60 dk", "60+ dk"]
    df["sure_araligi"] = pd.cut(
        df["sure_dk"], bins=bins, labels=labels_bin, right=True
    )
    sure_group = (
        df.groupby("sure_araligi", observed=False)["goruntulenme"]
        .mean()
        .reset_index()
    )
    sure_group.columns = ["Sure Araligi", "Ort. Goruntulenme"]
    fig_dur_bar = px.bar(
        sure_group, x="Sure Araligi", y="Ort. Goruntulenme",
        title="Sure Araligina Gore Ort. Goruntulenme",
        labels={"Sure Araligi": "Sure Araligi", "Ort. Goruntulenme": "Ort. Goruntulenme"},
        color="Ort. Goruntulenme",
        color_continuous_scale="Oranges",
        text="Ort. Goruntulenme",
    )
    fig_dur_bar.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig_dur_bar.update_layout(coloraxis_showscale=False, margin=dict(t=50, b=30, r=20))
    st.plotly_chart(fig_dur_bar, use_container_width=True)

st.divider()


# ─────────────────────────────────────────────────────────────
#  BOLUM 9 — Kanal Performansi
# ─────────────────────────────────────────────────────────────
st.header("8. Kanal Bazli Performans")

st.markdown(
    """
    Ayni analizin kanal boyutundan ele alinmasi, birden fazla video ile yer alan kanallarin
    platform uzerindeki etkisini ortaya koyar. Eger belirli kanallar trend listesinde
    birden fazla videoyla gorunuyorsa bu kanallarin algoritma tarafindan tercih edildigi
    ve guvenilir bulundugu seklinde yorumlanabilir. Asagida birden fazla trend videosu
    bulunan kanallar goruntulenme toplamina gore sirali olarak sunulmaktadir.
    """
)

kanal_df = (
    df.groupby("kanal")
    .agg(
        video_sayisi=("baslik", "count"),
        toplam_goruntulenme=("goruntulenme", "sum"),
        ort_etkilesim=("etkilesim_orani", "mean"),
    )
    .reset_index()
    .sort_values("toplam_goruntulenme", ascending=False)
)

multi_kanal = kanal_df[kanal_df["video_sayisi"] > 1]
goster_df = multi_kanal if len(multi_kanal) >= 3 else kanal_df.head(15)

fig_kanal = px.bar(
    goster_df.sort_values("toplam_goruntulenme").tail(15),
    x="toplam_goruntulenme", y="kanal", orientation="h",
    color="video_sayisi",
    title="Kanallara Gore Toplam Goruntulenme",
    labels={
        "toplam_goruntulenme": "Toplam Goruntulenme",
        "kanal": "Kanal",
        "video_sayisi": "Video Sayisi",
    },
    color_continuous_scale="Purples",
    text="video_sayisi",
)
fig_kanal.update_traces(texttemplate="%{text} video", textposition="inside")
fig_kanal.update_layout(margin=dict(t=50, b=10, l=10, r=20))
st.plotly_chart(fig_kanal, use_container_width=True)

st.divider()


# ─────────────────────────────────────────────────────────────
#  BOLUM 10 — Yayin Saati Analizi
# ─────────────────────────────────────────────────────────────
st.header("9. Yayin Saati ve Goruntulenme Iliskisi")

st.markdown(
    """
    Videolarin hangi saatte yayinlandiginin performans uzerine etkisi, icerik uretici stratejileri
    acisindan sikca tartisilan bir konudur. Bu analizde, trend videolarin yayinlandigi saatler
    ile aldiklari goruntulenme ortalamasi karsilastirilmistir. Yoğun izleyici kitlesinin aktif
    oldugu saatlerde yapilan paylasimlarin ilk 24 saatteki momentum nedeniyle daha yuksek
    goruntulenme elde ettigine dair bulgular literaturde mevcuttur.
    """
)

saat_df = (
    df.groupby("yayın_saati")
    .agg(
        video_sayisi=("baslik", "count"),
        ort_goruntulenme=("goruntulenme", "mean"),
    )
    .reset_index()
    .sort_values("yayın_saati")
)
saat_df.columns = ["Saat", "Video Sayisi", "Ort. Goruntulenme"]

fig_saat = make_subplots(specs=[[{"secondary_y": True}]])
fig_saat.add_trace(
    go.Bar(x=saat_df["Saat"], y=saat_df["Video Sayisi"],
           name="Video Sayisi", marker_color="#74c0fc", opacity=0.65),
    secondary_y=False,
)
fig_saat.add_trace(
    go.Scatter(x=saat_df["Saat"], y=saat_df["Ort. Goruntulenme"],
               name="Ort. Goruntulenme", mode="lines+markers",
               line=dict(color="#ff6b6b", width=2.5),
               marker=dict(size=7)),
    secondary_y=True,
)
fig_saat.update_layout(
    title_text="Yayin Saatine Gore Video Sayisi ve Ort. Goruntulenme",
    xaxis_title="Saat (UTC)",
    legend=dict(orientation="h", y=1.1),
    margin=dict(t=70, b=40),
)
fig_saat.update_yaxes(title_text="Video Sayisi", secondary_y=False)
fig_saat.update_yaxes(title_text="Ort. Goruntulenme", secondary_y=True)
st.plotly_chart(fig_saat, use_container_width=True)

st.divider()


# ─────────────────────────────────────────────────────────────
#  BOLUM 11 — Genel Degerlendirme
# ─────────────────────────────────────────────────────────────
st.header("10. Genel Degerlendirme")

top3 = df.nlargest(3, "goruntulenme")[["baslik", "kanal", "goruntulenme", "etkilesim_orani"]]
en_etkilesim = df.nlargest(3, "etkilesim_orani")[["baslik", "kanal", "etkilesim_orani"]]

col_e1, col_e2 = st.columns(2)
with col_e1:
    st.markdown("**En Cok Izlenen 3 Video**")
    st.dataframe(
        top3.rename(columns={"baslik": "Baslik", "kanal": "Kanal",
                              "goruntulenme": "Goruntulenme", "etkilesim_orani": "Etkilesim %"}),
        use_container_width=True, hide_index=True,
    )
with col_e2:
    st.markdown("**En Yuksek Etkilesim Oranlı 3 Video**")
    st.dataframe(
        en_etkilesim.rename(columns={"baslik": "Baslik", "kanal": "Kanal",
                                      "etkilesim_orani": "Etkilesim %"}),
        use_container_width=True, hide_index=True,
    )

st.markdown(
    f"""
    ---
    Bu calisma kapsaminda YouTube Data API v3 kullanilarak {ulke_adi} bolgesine ait
    **{len(df)} trend video** uzerinde istatistiksel analiz gerceklestirilmistir.
    Elde edilen bulgular asagidaki sekilde ozetlenebilir:

    - Goruntulenme sayisinin dagilimi **sagdan carpik** bir yapi sergilemekte olup buyuk
      cogunluk gorece dusuk izlenme degerlerine sahipken az sayida video cok yuksek
      goruntulenme rakamlaına ulasabilmektedir.
    - Begeni ve goruntulenme arasindaki Pearson korelasyonu **r = {corr_val:.3f}** olarak
      hesaplanmis; bu iki degisken arasinda {'guclu' if corr_val > 0.7 else 'orta duzey'}
      bir pozitif iliski tespit edilmistir.
    - En yuksek ortalama etkilesim orani **{kat_engag.iloc[0]['kategori']}** kategorisinde
      gozlemlenirken en fazla trend video **{df['kategori'].value_counts().idxmax()}**
      kategorisinde yer almaktadir.
    - Video suresi ile goruntulenme arasindaki iliski dogrusal bir gidis izlememekte;
      orta uzunluktaki videolarin (5-20 dakika) goruntulenme acisindan en verimli aralik
      oldugu gozlemlenmektedir.
    """
)
