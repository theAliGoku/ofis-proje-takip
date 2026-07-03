import streamlit as st
import pandas as pd
import datetime
from streamlit_gsheets import GSheetsConnection

# ─── SAYFA AYARLARI ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Egeşehir Ofis Yönetimi",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── GLOBAL CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── Genel arka plan ── */
.main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

/* ── Metric kartlar ── */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, #f8faff 0%, #eef2ff 100%);
    border: 1px solid #e0e7ff;
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 2px 8px rgba(99,102,241,0.07);
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 2rem;
    font-weight: 700;
    color: #3730a3;
}
[data-testid="metric-container"] [data-testid="stMetricLabel"] {
    font-size: 0.85rem;
    color: #6366f1;
    font-weight: 500;
}

/* ── Durum badge'leri ── */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    white-space: nowrap;
}
.badge-red    { background: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; }
.badge-yellow { background: #fef9c3; color: #a16207; border: 1px solid #fde047; }
.badge-green  { background: #dcfce7; color: #15803d; border: 1px solid #86efac; }
.badge-orange { background: #ffedd5; color: #c2410c; border: 1px solid #fb923c; }
.badge-blue   { background: #dbeafe; color: #1d4ed8; border: 1px solid #93c5fd; }

/* ── Görev kartı ── */
.task-card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 10px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    transition: box-shadow 0.2s ease;
}
.task-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.task-card-overdue {
    border-left: 4px solid #ef4444 !important;
    background: #fff8f8 !important;
}
.task-card-done {
    border-left: 4px solid #22c55e !important;
    background: #f0fdf4 !important;
    opacity: 0.85;
}
.task-card-inprogress {
    border-left: 4px solid #f59e0b !important;
    background: #fffbeb !important;
}

/* ── Login ekranı ── */
.login-card {
    background: white;
    border-radius: 20px;
    padding: 40px 48px;
    box-shadow: 0 8px 40px rgba(99,102,241,0.12);
    border: 1px solid #e0e7ff;
    text-align: center;
}
.login-logo {
    font-size: 3.5rem;
    margin-bottom: 10px;
}
.login-title {
    font-size: 1.6rem;
    font-weight: 700;
    color: #1e1b4b;
    margin-bottom: 4px;
}
.login-subtitle {
    font-size: 0.9rem;
    color: #6b7280;
    margin-bottom: 28px;
}

/* ── Sidebar ── */
.sidebar-user-card {
    background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
    border-radius: 14px;
    padding: 18px;
    color: white;
    margin-bottom: 16px;
    text-align: center;
}
.sidebar-user-card .name { font-weight: 700; font-size: 1.05rem; }
.sidebar-user-card .role { font-size: 0.8rem; opacity: 0.85; margin-top: 4px; }
.sidebar-stat {
    background: #f8faff;
    border: 1px solid #e0e7ff;
    border-radius: 10px;
    padding: 10px 14px;
    margin-bottom: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.88rem;
    color: #374151;
}
.sidebar-stat .val { font-weight: 700; color: #4f46e5; font-size: 1.1rem; }

/* ── Bölüm başlıkları ── */
.section-header {
    font-size: 1.3rem;
    font-weight: 700;
    color: #1e1b4b;
    padding-bottom: 6px;
    border-bottom: 2px solid #e0e7ff;
    margin-bottom: 16px;
}

/* ── Butonlar ── */
.stButton > button {
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.2s ease;
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(99,102,241,0.2);
}
.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] {
    height: 44px;
    padding: 0 20px;
    border-radius: 8px 8px 0 0;
    font-weight: 600;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    font-weight: 600 !important;
    color: #374151 !important;
}

/* ── Tablo başlık satırı ── */
.tablo-baslik {
    background: #f1f5f9;
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 0.8rem;
    font-weight: 700;
    color: #475569;
    margin-bottom: 4px;
}

/* ── Progress bar ── */
.progress-wrap {
    background: #e5e7eb;
    border-radius: 99px;
    height: 8px;
    width: 100%;
    overflow: hidden;
    margin: 4px 0 8px 0;
}
.progress-bar {
    height: 100%;
    border-radius: 99px;
    background: linear-gradient(90deg, #6366f1, #22c55e);
    transition: width 0.4s ease;
}

/* ── AI header ── */
.ai-header {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    border-radius: 16px;
    padding: 24px 28px;
    margin-bottom: 20px;
}
.ai-header h2 { color: #e2e8f0; margin: 0; font-size: 1.6rem; }
.ai-header p  { color: #94a3b8; margin: 6px 0 0 0; font-size: 0.95rem; }

/* ── Boş durum ── */
.empty-state {
    text-align: center;
    padding: 40px 20px;
    color: #9ca3af;
}
.empty-state .icon { font-size: 3rem; margin-bottom: 10px; }
.empty-state .msg  { font-size: 1rem; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

# ─── SABİTLER ────────────────────────────────────────────────────────────────
DURUM_SECENEKLERI = ["Başlamadı", "Devam Ediyor", "Tamamlandı"]
ALT_GOREV_KOLONLARI = [
    "Alt_Gorev_ID", "Ana_Gorev_ID", "Alt_Gorev_Tanimi",
    "Atanan_Kişi", "Son_Tarih", "Gorev_Durumu", "Aciklama"
]

# ─── YARDIMCI FONKSİYONLAR ──────────────────────────────────────────────────
def _id_esle(seri, deger):
    return seri.astype(str).str.strip() == str(deger).strip()


def durum_badge(durum):
    """Verilen duruma göre renkli HTML badge döndürür."""
    m = {
        "Başlamadı":   ("<span class='badge badge-red'>🔴 Başlamadı</span>"),
        "Devam Ediyor": ("<span class='badge badge-yellow'>🟡 Devam Ediyor</span>"),
        "Tamamlandı":  ("<span class='badge badge-green'>🟢 Tamamlandı</span>"),
    }
    return m.get(str(durum).strip(), f"<span class='badge badge-blue'>{durum}</span>")


def gecikme_var_mi(tarih_str):
    """Tarihi geçmiş mi? True/False döndürür."""
    try:
        t = pd.to_datetime(str(tarih_str)).date()
        return t < datetime.date.today()
    except Exception:
        return False


def ilerleme_yuzde(df, durum_kol="Gorev_Durumu"):
    """DataFrame'deki tamamlanma yüzdesini döndürür (0–100)."""
    if df.empty:
        return 0
    n = len(df[df[durum_kol] == "Tamamlandı"])
    return int(n / len(df) * 100)


def progress_bar_html(yuzde, renk="#6366f1"):
    return f"""
    <div class='progress-wrap'>
        <div class='progress-bar' style='width:{yuzde}%; background:{renk};'></div>
    </div>
    <small style='color:#6b7280;'>{yuzde}% tamamlandı</small>
    """


def gorev_sinif(row):
    """Görevin CSS sınıfını belirler."""
    if row.get("Gorev_Durumu") == "Tamamlandı":
        return "task-card task-card-done"
    if gecikme_var_mi(row.get("Son_Tarih", "")):
        return "task-card task-card-overdue"
    if row.get("Gorev_Durumu") == "Devam Ediyor":
        return "task-card task-card-inprogress"
    return "task-card"


def gorev_sirala(df):
    """Görevleri: gecikmiş → devam ediyor → başlamadı → tamamlandı sırasına koyar."""
    if df.empty:
        return df
    df = df.copy()
    df["_dt"] = pd.to_datetime(df.get("Son_Tarih", ""), errors="coerce")
    bugun = pd.Timestamp(datetime.date.today())
    df["_onc"] = 0
    df.loc[(df["Gorev_Durumu"] != "Tamamlandı") & (df["_dt"] < bugun), "_onc"] = 0
    df.loc[df["Gorev_Durumu"] == "Devam Ediyor", "_onc"] = 1
    df.loc[df["Gorev_Durumu"] == "Başlamadı", "_onc"] = 2
    df.loc[df["Gorev_Durumu"] == "Tamamlandı", "_onc"] = 3
    return df.sort_values("_onc").drop(columns=["_onc", "_dt"])


# ─── VERİTABANI FONKSİYONLARI ────────────────────────────────────────────────
def gorev_guncelle(gorevler_df, conn, gorev_id, yeni_durum, yeni_aciklama):
    mask = _id_esle(gorevler_df["Gorev_ID"], gorev_id)
    if not mask.any():
        st.error(f"Gorev_ID '{gorev_id}' bulunamadı.")
        return False
    gorevler_df.loc[mask, ["Gorev_Durumu", "Aciklama"]] = [yeni_durum, yeni_aciklama]
    try:
        conn.update(worksheet="Gorevler", data=gorevler_df)
    except Exception as e:
        st.error(f"Kaydedilemedi: {e}")
        return False
    return True


def alt_gorev_guncelle(alt_gorevler_df, conn, alt_gorev_id, yeni_durum, yeni_aciklama):
    mask = _id_esle(alt_gorevler_df["Alt_Gorev_ID"], alt_gorev_id)
    if not mask.any():
        st.error(f"Alt_Gorev_ID '{alt_gorev_id}' bulunamadı.")
        return False
    alt_gorevler_df.loc[mask, ["Gorev_Durumu", "Aciklama"]] = [yeni_durum, yeni_aciklama]
    try:
        conn.update(worksheet="AltGorevler", data=alt_gorevler_df)
    except Exception as e:
        st.error(f"Kaydedilemedi: {e}")
        return False
    return True


def gorev_sil(gorevler_df, alt_gorevler_df, conn, gorev_id):
    mask = _id_esle(gorevler_df["Gorev_ID"], gorev_id)
    if not mask.any():
        st.error(f"Gorev_ID '{gorev_id}' bulunamadı.")
        return False
    yeni_gorevler = gorevler_df[~mask].reset_index(drop=True)
    if not alt_gorevler_df.empty:
        alt_mask = _id_esle(alt_gorevler_df["Ana_Gorev_ID"], gorev_id)
        yeni_alt = alt_gorevler_df[~alt_mask].reset_index(drop=True)
    else:
        yeni_alt = alt_gorevler_df
    try:
        conn.update(worksheet="Gorevler", data=yeni_gorevler)
        conn.update(worksheet="AltGorevler", data=yeni_alt)
    except Exception as e:
        st.error(f"Görev silinemedi: {e}")
        return False
    return True


def proje_sil(projeler_df, conn, proje_id):
    mask = projeler_df["Proje_ID"].astype(str).str.strip() == str(proje_id).strip()
    if not mask.any():
        st.error(f"Proje_ID '{proje_id}' bulunamadı.")
        return False
    yeni = projeler_df[~mask].reset_index(drop=True)
    try:
        conn.update(worksheet="Projeler", data=yeni)
    except Exception as e:
        st.error(f"Proje silinemedi: {e}")
        return False
    return True


def alt_gorev_ekle(alt_gorevler_df, conn, ana_gorev_id, tanim, kisi, tarih):
    yeni_id = f"AG-{len(alt_gorevler_df) + 1:03d}"
    yeni = pd.DataFrame([{
        "Alt_Gorev_ID": yeni_id,
        "Ana_Gorev_ID": ana_gorev_id,
        "Alt_Gorev_Tanimi": tanim,
        "Atanan_Kişi": kisi,
        "Son_Tarih": tarih.strftime("%Y-%m-%d"),
        "Gorev_Durumu": "Başlamadı",
        "Aciklama": ""
    }])
    guncel = pd.concat([alt_gorevler_df, yeni], ignore_index=True)
    try:
        conn.update(worksheet="AltGorevler", data=guncel)
    except Exception as e:
        st.error(f"Alt görev kaydedilemedi: {e}")
        return False
    return True


# ─── METRIK KARTLAR ─────────────────────────────────────────────────────────
def metrik_satiri_ciz(df, gecikme_goster=True):
    """4 metrik: Toplam, Devam Eden, Tamamlanan, (Gecikmiş)."""
    toplam = len(df)
    devam  = len(df[df["Gorev_Durumu"] == "Devam Ediyor"])
    tamam  = len(df[df["Gorev_Durumu"] == "Tamamlandı"])

    if gecikme_goster:
        gecik = sum(
            1 for _, r in df.iterrows()
            if r["Gorev_Durumu"] != "Tamamlandı" and gecikme_var_mi(r.get("Son_Tarih", ""))
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📋 Toplam Görev", toplam)
        c2.metric("🟡 Devam Eden",   devam)
        c3.metric("✅ Tamamlanan",   tamam)
        c4.metric("🔴 Gecikmiş",     gecik)
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("📋 Toplam Görev", toplam)
        c2.metric("🟡 Devam Eden",   devam)
        c3.metric("✅ Tamamlanan",   tamam)

    yuzde = ilerleme_yuzde(df)
    st.markdown(progress_bar_html(yuzde), unsafe_allow_html=True)


# ─── DURUM/NOT KARTI ─────────────────────────────────────────────────────────
def durum_notu_karti(kayit_id, mevcut_durum, mevcut_aciklama,
                     salt_okunur, key_prefix, kaydet_fonksiyonu):
    try:
        idx = DURUM_SECENEKLERI.index(mevcut_durum)
    except (ValueError, TypeError):
        idx = 0

    yeni_durum = st.selectbox(
        "Durum:", DURUM_SECENEKLERI, index=idx,
        disabled=salt_okunur, key=f"{key_prefix}_durum"
    )

    aciklama = "" if pd.isna(mevcut_aciklama) else str(mevcut_aciklama)
    yeni_aciklama = st.text_area(
        "Açıklama / Not:", value=aciklama,
        disabled=salt_okunur, key=f"{key_prefix}_not",
        height=80
    )

    if salt_okunur:
        st.caption("🔒 Bu göreve ait değilsiniz — yalnızca Şef düzenleyebilir.")
    else:
        if st.button("💾 Güncelle", key=f"{key_prefix}_btn", type="primary"):
            if kaydet_fonksiyonu(kayit_id, yeni_durum, yeni_aciklama):
                st.success("✅ Güncellendi!")
                st.cache_data.clear()
                st.rerun()


# ─── GÖREV KARTI RENDER ─────────────────────────────────────────────────────
def gorev_karti_render(row, gorevler_df, alt_gorevler_df,
                        kullanicilar_df, conn, rol_normalize,
                        current_name, key_prefix):
    gorev_id = row["Gorev_ID"]

    # Üst bilgi satırı
    c_inf1, c_inf2, c_inf3 = st.columns([2, 2, 2])
    c_inf1.markdown(f"**Proje:** `{row.get('Bagli_Oldugu_Proje_ID','')}`")
    c_inf2.markdown(f"**Etap:** {row.get('Etap_Adi','—')}")
    c_inf3.markdown(durum_badge(row.get("Gorev_Durumu", "")), unsafe_allow_html=True)

    c_kisi, c_tarih = st.columns(2)
    c_kisi.markdown(f"👤 **Atanan:** {row.get('Atanan_Kişi','—')}")
    tarih_str = str(row.get("Son_Tarih",""))
    if gecikme_var_mi(tarih_str) and row.get("Gorev_Durumu") != "Tamamlandı":
        c_tarih.markdown(f"📅 **Son Tarih:** :red[{tarih_str} ⚠️ GECİKMİŞ]")
    else:
        c_tarih.markdown(f"📅 **Son Tarih:** {tarih_str}")

    salt_okunur = (rol_normalize != "şef") and (row["Atanan_Kişi"] != current_name)

    st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
    durum_notu_karti(
        kayit_id=gorev_id,
        mevcut_durum=row["Gorev_Durumu"],
        mevcut_aciklama=row.get("Aciklama", ""),
        salt_okunur=salt_okunur,
        key_prefix=f"{key_prefix}_ana_{gorev_id}",
        kaydet_fonksiyonu=lambda gid, d, a: gorev_guncelle(gorevler_df, conn, gid, d, a)
    )

    # Alt görevler
    if not alt_gorevler_df.empty:
        alt_liste = alt_gorevler_df[_id_esle(alt_gorevler_df["Ana_Gorev_ID"], gorev_id)]
    else:
        alt_liste = pd.DataFrame(columns=ALT_GOREV_KOLONLARI)

    if not alt_liste.empty:
        st.markdown("---")
        st.markdown(f"**🔹 Alt Görevler** ({len(alt_liste)})")
        for _, ar in alt_liste.iterrows():
            with st.container():
                ac1, ac2, ac3 = st.columns([3, 2, 2])
                ac1.markdown(f"📎 *{ar.get('Alt_Gorev_Tanimi','')}*")
                ac2.markdown(f"👤 {ar.get('Atanan_Kişi','')}")
                ac3.markdown(durum_badge(ar.get("Gorev_Durumu","")), unsafe_allow_html=True)

                a_salt = (rol_normalize != "şef") and (ar.get("Atanan_Kişi","") != current_name)
                durum_notu_karti(
                    kayit_id=ar["Alt_Gorev_ID"],
                    mevcut_durum=ar["Gorev_Durumu"],
                    mevcut_aciklama=ar.get("Aciklama",""),
                    salt_okunur=a_salt,
                    key_prefix=f"{key_prefix}_alt_{ar['Alt_Gorev_ID']}",
                    kaydet_fonksiyonu=lambda aid, d, a: alt_gorev_guncelle(alt_gorevler_df, conn, aid, d, a)
                )
            st.markdown("<div style='margin-bottom:6px;'></div>", unsafe_allow_html=True)

    # Şef: Alt görev ekleme
    if rol_normalize == "şef":
        st.markdown("---")
        with st.expander("➕ Bu Göreve Alt Görev Ekle", expanded=False):
            ag_tanim = st.text_input("Alt Görev Tanımı", key=f"ag_tanim_{gorev_id}")
            kisi_liste = ["Herkes"] + kullanicilar_df["Ad_Soyad"].tolist()
            ag_kisi  = st.selectbox("Atanan Personel", kisi_liste, key=f"ag_kisi_{gorev_id}")
            ag_tarih = st.date_input("Son Tarih", key=f"ag_tarih_{gorev_id}")
            if st.button("✅ Alt Görevi Kaydet", key=f"ag_btn_{gorev_id}", type="primary"):
                if not ag_tanim.strip():
                    st.warning("Lütfen alt görev tanımını girin.")
                else:
                    if alt_gorev_ekle(alt_gorevler_df, conn, gorev_id,
                                       ag_tanim.strip(), ag_kisi, ag_tarih):
                        st.success("✅ Alt görev eklendi!")
                        st.cache_data.clear()
                        st.rerun()

        with st.expander("🗑️ Bu Görevi Sil", expanded=False):
            st.warning("⚠️ Bu işlem geri alınamaz. Bağlı tüm alt görevler de silinir.")
            onay = st.checkbox("Silmek istediğimi onaylıyorum.", key=f"{key_prefix}_sil_onay_{gorev_id}")
            if st.button("🗑️ Kalıcı Olarak Sil", type="primary",
                         disabled=not onay, key=f"{key_prefix}_sil_btn_{gorev_id}"):
                if gorev_sil(gorevler_df, alt_gorevler_df, conn, gorev_id):
                    st.success("Görev silindi.")
                    st.cache_data.clear()
                    st.rerun()


# ─── VERİ YÜKLEME ────────────────────────────────────────────────────────────
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=5)
def load_data():
    kullanicilar = conn.read(worksheet="Kullanicilar")
    projeler     = conn.read(worksheet="Projeler")
    gorevler     = conn.read(worksheet="Gorevler")
    try:
        alt_gorevler = conn.read(worksheet="AltGorevler")
        if alt_gorevler is None or alt_gorevler.empty:
            alt_gorevler = pd.DataFrame(columns=ALT_GOREV_KOLONLARI)
    except Exception:
        alt_gorevler = pd.DataFrame(columns=ALT_GOREV_KOLONLARI)
    return kullanicilar, projeler, gorevler, alt_gorevler

kullanicilar_df, projeler_df, gorevler_df, alt_gorevler_df = load_data()

if alt_gorevler_df.empty and list(alt_gorevler_df.columns) != ALT_GOREV_KOLONLARI:
    alt_gorevler_df = pd.DataFrame(columns=ALT_GOREV_KOLONLARI)

# ─── SESSION STATE ────────────────────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in   = False
    st.session_state.current_user = None
    st.session_state.current_role = None
    st.session_state.current_name = None

# ─── LOGIN EKRANI ─────────────────────────────────────────────────────────────
if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col_center, _ = st.columns([1, 1.4, 1])
    with col_center:
        st.markdown("""
        <div class='login-card'>
            <div class='login-logo'>🏢</div>
            <div class='login-title'>Egeşehir Ofis Yönetimi</div>
            <div class='login-subtitle'>Sisteme erişmek için kullanıcı adınızı girin</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

        kullanici_adi_input = st.text_input(
            "Kullanıcı Adı", placeholder="kullanici_adi",
            label_visibility="collapsed"
        )
        if st.button("🚀 Giriş Yap", use_container_width=True, type="primary"):
            match = kullanicilar_df[kullanicilar_df["Kullanici_Adi"] == kullanici_adi_input]
            if not match.empty:
                st.session_state.logged_in    = True
                st.session_state.current_user = kullanici_adi_input
                st.session_state.current_role = str(match.iloc[0]["Rol"]).strip()
                st.session_state.current_name = str(match.iloc[0]["Ad_Soyad"]).strip()
                st.rerun()
            else:
                st.error("❌ Kullanıcı bulunamadı. Lütfen tekrar deneyin.")
    st.stop()

# ─── GİRİŞ SONRASI ──────────────────────────────────────────────────────────
rol_normalize = str(st.session_state.current_role).strip().casefold()
current_name  = st.session_state.current_name

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div class='sidebar-user-card'>
        <div style='font-size:2rem;'>{"👑" if rol_normalize == "şef" else "👤"}</div>
        <div class='name'>{current_name}</div>
        <div class='role'>{"Şef" if rol_normalize == "şef" else "Personel"}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"📅 **{datetime.date.today().strftime('%d %B %Y')}**")
    st.markdown("---")

    # Mini istatistikler
    if rol_normalize == "şef":
        hedef_df = gorevler_df
    else:
        hedef_df = gorevler_df[
            (gorevler_df["Atanan_Kişi"] == current_name) |
            (gorevler_df["Atanan_Kişi"] == "Herkes")
        ]

    devam_n = len(hedef_df[hedef_df["Gorev_Durumu"] == "Devam Ediyor"])
    tamam_n = len(hedef_df[hedef_df["Gorev_Durumu"] == "Tamamlandı"])
    gecik_n = sum(1 for _, r in hedef_df.iterrows()
                  if r["Gorev_Durumu"] != "Tamamlandı"
                  and gecikme_var_mi(r.get("Son_Tarih", "")))

    st.markdown(f"""
    <div class='sidebar-stat'><span>🟡 Devam Eden</span><span class='val'>{devam_n}</span></div>
    <div class='sidebar-stat'><span>✅ Tamamlanan</span><span class='val'>{tamam_n}</span></div>
    <div class='sidebar-stat'><span>🔴 Gecikmiş</span><span class='val'>{gecik_n}</span></div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🚪 Çıkış Yap", use_container_width=True):
        st.session_state.logged_in    = False
        st.session_state.current_user = None
        st.session_state.current_role = None
        st.session_state.current_name = None
        st.rerun()

# ─── ANA SEKMELER ────────────────────────────────────────────────────────────
tab_gorev, tab_ai = st.tabs(["📋 Görev Paneli", "🤖 AI Asistan"])

# ═══════════════════════════════════════════════════════════════════════════════
# GÖREV PANELİ
# ═══════════════════════════════════════════════════════════════════════════════
with tab_gorev:

    # ──────────────────────────────────────────────────────────────────────────
    # ŞEF EKRANI
    # ──────────────────────────────────────────────────────────────────────────
    if rol_normalize == "şef":
        st.markdown("<div class='section-header'>👑 Şef Kontrol Paneli</div>", unsafe_allow_html=True)

        tab_benim, tab_tum, tab_yeni, tab_projeler = st.tabs([
            "🙋 Benim İşlerim", "📊 Tüm İşlerin Durumu",
            "➕ Yeni Görev Ata", "📁 Projeler"
        ])

        # ── Benim İşlerim ────────────────────────────────────────────────────
        with tab_benim:
            ilgili_ana_id = []
            if not alt_gorevler_df.empty:
                ilgili_ana_id = alt_gorevler_df.loc[
                    alt_gorevler_df["Atanan_Kişi"] == current_name, "Ana_Gorev_ID"
                ].unique().tolist()

            sef_gorevlerim = gorevler_df[
                (gorevler_df["Atanan_Kişi"] == current_name) |
                (gorevler_df["Atanan_Kişi"] == "Herkes")     |
                (gorevler_df["Gorev_ID"].isin(ilgili_ana_id))
            ]

            metrik_satiri_ciz(sef_gorevlerim)
            st.divider()

            if sef_gorevlerim.empty:
                st.markdown("""
                <div class='empty-state'>
                    <div class='icon'>🎉</div>
                    <div class='msg'>Üzerinize atanmış bekleyen görev yok!</div>
                </div>""", unsafe_allow_html=True)
            else:
                for _, row in gorev_sirala(sef_gorevlerim).iterrows():
                    sinif = gorev_sinif(row)
                    gecik = gecikme_var_mi(row.get("Son_Tarih","")) and row["Gorev_Durumu"] != "Tamamlandı"
                    etiket = " 🔴 GECİKMİŞ" if gecik else ""
                    with st.expander(f"{'🔴' if gecik else '📌'} {row['Gorev_Tanimi']}{etiket}  ·  📅 {row.get('Son_Tarih','')}"):
                        gorev_karti_render(
                            row, gorevler_df, alt_gorevler_df, kullanicilar_df,
                            conn, rol_normalize, current_name, "sef_benim"
                        )

        # ── Tüm İşlerin Durumu ───────────────────────────────────────────────
        with tab_tum:
            metrik_satiri_ciz(gorevler_df)
            st.divider()

            # Filtreler
            fc1, fc2 = st.columns([2, 2])
            secilen_proje = fc1.selectbox(
                "🔍 Projeye Göre Filtrele",
                ["Tümü"] + projeler_df["Proje_ID"].dropna().unique().tolist(),
                key="tum_filtre_proje"
            )
            secilen_durum = fc2.selectbox(
                "📌 Duruma Göre Filtrele",
                ["Tümü"] + DURUM_SECENEKLERI,
                key="tum_filtre_durum"
            )

            filtrelenmis_df = gorevler_df.copy()
            if secilen_proje != "Tümü":
                filtrelenmis_df = filtrelenmis_df[filtrelenmis_df["Bagli_Oldugu_Proje_ID"] == secilen_proje]
            if secilen_durum != "Tümü":
                filtrelenmis_df = filtrelenmis_df[filtrelenmis_df["Gorev_Durumu"] == secilen_durum]

            st.markdown("---")

            # Başlık satırı
            st.markdown("""
            <div class='tablo-baslik' style='display:flex; gap:0;'>
                <span style='width:7%;'>ID</span>
                <span style='width:10%;'>Proje</span>
                <span style='width:12%;'>Etap</span>
                <span style='width:28%;'>Görev</span>
                <span style='width:13%;'>Atanan</span>
                <span style='width:10%;'>Son Tarih</span>
                <span style='width:14%;'>Durum</span>
                <span style='width:6%;'>İşlem</span>
            </div>
            """, unsafe_allow_html=True)

            for _, row in gorev_sirala(filtrelenmis_df).iterrows():
                gorev_id = row["Gorev_ID"]
                gecik = gecikme_var_mi(row.get("Son_Tarih","")) and row["Gorev_Durumu"] != "Tamamlandı"

                if not alt_gorevler_df.empty:
                    alt_liste = alt_gorevler_df[_id_esle(alt_gorevler_df["Ana_Gorev_ID"], gorev_id)]
                else:
                    alt_liste = pd.DataFrame(columns=ALT_GOREV_KOLONLARI)
                has_alts = not alt_liste.empty

                # Satır arka plan rengi
                bg = "#fff8f8" if gecik else ("#f0fdf4" if row["Gorev_Durumu"] == "Tamamlandı" else "white")
                border = "#ef4444" if gecik else ("#22c55e" if row["Gorev_Durumu"] == "Tamamlandı" else "#e5e7eb")

                c1,c2,c3,c4,c5,c6,c7,c8,c9 = st.columns([0.6,1.0,1.2,2.8,1.4,1.1,1.5,0.5,0.5])
                c1.caption(str(gorev_id))
                c2.caption(str(row.get("Bagli_Oldugu_Proje_ID","")))
                c3.caption(str(row.get("Etap_Adi","")))
                c4.write(f"{'🔹 ' if has_alts else ''}{str(row.get('Gorev_Tanimi',''))}")
                c5.caption(str(row.get("Atanan_Kişi","")))
                c6.caption(f"{'⚠️ ' if gecik else ''}{str(row.get('Son_Tarih',''))}")

                try:
                    d_idx = DURUM_SECENEKLERI.index(row["Gorev_Durumu"])
                except (ValueError, TypeError):
                    d_idx = 0
                yeni_durum_tum = c7.selectbox(
                    "durum", DURUM_SECENEKLERI, index=d_idx,
                    key=f"tum_durum_{gorev_id}", label_visibility="collapsed"
                )

                if c8.button("💾", key=f"tum_kaydet_{gorev_id}", help="Kaydet"):
                    if gorev_guncelle(gorevler_df, conn, gorev_id,
                                      yeni_durum_tum, row.get("Aciklama","")):
                        st.success(f"✅ '{row['Gorev_Tanimi']}' güncellendi!")
                        st.cache_data.clear()
                        st.rerun()

                if c9.button("🗑️", key=f"tum_sil_{gorev_id}", help="Sil"):
                    st.session_state[f"tum_sil_onay_{gorev_id}"] = True

                if st.session_state.get(f"tum_sil_onay_{gorev_id}", False):
                    st.warning(f"⚠️ **'{row['Gorev_Tanimi']}'** ve bağlı alt görevler silinecek. Emin misiniz?")
                    e1, e2, _ = st.columns([1, 1, 5])
                    if e1.button("✅ Evet, Sil", key=f"tum_sil_evet_{gorev_id}", type="primary"):
                        if gorev_sil(gorevler_df, alt_gorevler_df, conn, gorev_id):
                            st.session_state.pop(f"tum_sil_onay_{gorev_id}", None)
                            st.cache_data.clear()
                            st.rerun()
                    if e2.button("❌ İptal", key=f"tum_sil_iptal_{gorev_id}"):
                        st.session_state.pop(f"tum_sil_onay_{gorev_id}", None)
                        st.rerun()

                if has_alts:
                    with st.expander(f"🔽 {len(alt_liste)} alt görev"):
                        ah = st.columns([0.7, 2.8, 1.4, 1.1, 1.5, 0.6])
                        for c_ah, lbl in zip(ah, ["Alt ID","Alt Görev","Atanan","Son Tarih","Durum","💾"]):
                            c_ah.markdown(f"<small><b>{lbl}</b></small>", unsafe_allow_html=True)
                        st.markdown("<hr style='margin:2px 0 4px 0;'>", unsafe_allow_html=True)

                        for _, ar in alt_liste.iterrows():
                            alt_id = ar["Alt_Gorev_ID"]
                            a1,a2,a3,a4,a5,a6 = st.columns([0.7,2.8,1.4,1.1,1.5,0.6])
                            a1.caption(str(alt_id))
                            a2.write(str(ar.get("Alt_Gorev_Tanimi","")))
                            a3.caption(str(ar.get("Atanan_Kişi","")))
                            a4.caption(str(ar.get("Son_Tarih","")))
                            try:
                                ai = DURUM_SECENEKLERI.index(ar["Gorev_Durumu"])
                            except (ValueError, TypeError):
                                ai = 0
                            yad = a5.selectbox(
                                "d", DURUM_SECENEKLERI, index=ai,
                                key=f"tum_alt_durum_{alt_id}", label_visibility="collapsed"
                            )
                            if a6.button("💾", key=f"tum_alt_kaydet_{alt_id}"):
                                if alt_gorev_guncelle(alt_gorevler_df, conn, alt_id,
                                                       yad, ar.get("Aciklama","")):
                                    st.success("✅ Alt görev güncellendi!")
                                    st.cache_data.clear()
                                    st.rerun()

                st.markdown("<hr style='margin:4px 0; border-color:#f0f0f0;'>", unsafe_allow_html=True)

        # ── Yeni Görev Ata ────────────────────────────────────────────────────
        with tab_yeni:
            st.markdown("<div class='section-header'>➕ Yeni Görev Oluştur</div>", unsafe_allow_html=True)

            with st.form("yeni_gorev_formu", clear_on_submit=True):
                c_sol, c_sag = st.columns(2)
                with c_sol:
                    yeni_proje_id = st.selectbox("📁 Bağlı Proje", projeler_df["Proje_ID"].tolist())
                    yeni_etap     = st.text_input("🏷️ Etap Adı (opsiyonel)")
                    yeni_tanim    = st.text_area("📝 Görev Tanımı", height=120)
                with c_sag:
                    kisi_listesi = ["Herkes"] + kullanicilar_df["Ad_Soyad"].tolist()
                    yeni_kisi    = st.selectbox("👤 Atanan Kişi", kisi_listesi)
                    yeni_tarih   = st.date_input("📅 Son Tarih")
                    st.markdown("<br>", unsafe_allow_html=True)

                ekle_btn = st.form_submit_button("✅ Görevi Oluştur", use_container_width=True, type="primary")

                if ekle_btn:
                    if not yeni_tanim.strip():
                        st.warning("Lütfen görev tanımı girin.")
                    else:
                        yeni_id = f"G-{len(gorevler_df) + 1:03d}"
                        yeni_satir = pd.DataFrame([{
                            "Gorev_ID": yeni_id,
                            "Bagli_Oldugu_Proje_ID": yeni_proje_id,
                            "Etap_Adi": yeni_etap,
                            "Gorev_Tanimi": yeni_tanim,
                            "Atanan_Kişi": yeni_kisi,
                            "Son_Tarih": yeni_tarih.strftime("%Y-%m-%d"),
                            "Gorev_Durumu": "Başlamadı",
                            "Aciklama": ""
                        }])
                        try:
                            conn.update(worksheet="Gorevler",
                                        data=pd.concat([gorevler_df, yeni_satir], ignore_index=True))
                            st.success(f"✅ Görev oluşturuldu! (ID: {yeni_id})")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Kaydedilemedi: {e}")

        # ── Projeler ─────────────────────────────────────────────────────────
        with tab_projeler:
            st.markdown("<div class='section-header'>📁 Proje Yönetimi</div>", unsafe_allow_html=True)

            # Proje kartları özet
            if not projeler_df.empty:
                st.markdown("#### Proje Genel Görünümü")
                cols = st.columns(min(len(projeler_df), 3))
                for i, (_, prj) in enumerate(projeler_df.iterrows()):
                    pid = prj.get("Proje_ID","")
                    prj_gorevler = gorevler_df[gorevler_df["Bagli_Oldugu_Proje_ID"] == pid]
                    yuzde = ilerleme_yuzde(prj_gorevler)
                    acik  = len(prj_gorevler[prj_gorevler["Gorev_Durumu"] != "Tamamlandı"])

                    with cols[i % 3]:
                        prj_ad = prj.get("Proje_Adi", pid)
                        # Fallback: ilk ad içeren sütun
                        if not prj_ad or str(prj_ad) == "nan":
                            for c in projeler_df.columns:
                                if "ad" in c.lower() and c != "Proje_ID":
                                    prj_ad = prj.get(c, pid)
                                    break
                        st.markdown(f"""
                        <div class='task-card' style='border-left:4px solid #6366f1;'>
                            <b style='color:#1e1b4b;'>{pid}</b><br>
                            <span style='color:#374151;font-size:0.95rem;'>{prj_ad}</span><br>
                            <small style='color:#6b7280;'>Açık görev: {acik}</small>
                        </div>
                        """, unsafe_allow_html=True)
                        st.markdown(progress_bar_html(yuzde), unsafe_allow_html=True)

                st.markdown("---")

            # Yeni Proje Ekle
            with st.expander("➕ Yeni Proje Ekle", expanded=False):
                np_ad   = st.text_input("Proje Adı",  key="np_ad")
                np_acik = st.text_input("Açıklama",   key="np_acik")
                np_dur  = st.selectbox("Durum", ["Aktif","Tamamlandı","Beklemede"], key="np_dur")
                if st.button("✅ Projeyi Ekle", key="np_ekle_btn", type="primary"):
                    if not np_ad.strip():
                        st.warning("Lütfen proje adı girin.")
                    else:
                        yeni_pid = f"P-{len(projeler_df)+1:03d}"
                        yeni_proje = pd.DataFrame([{c:"" for c in projeler_df.columns}])
                        cols_list = projeler_df.columns.tolist()
                        if "Proje_ID"  in cols_list: yeni_proje["Proje_ID"]  = yeni_pid
                        if "Proje_Adi" in cols_list: yeni_proje["Proje_Adi"] = np_ad.strip()
                        if "Aciklama"  in cols_list: yeni_proje["Aciklama"]  = np_acik.strip()
                        if "Durum"     in cols_list: yeni_proje["Durum"]     = np_dur
                        for c in cols_list:
                            if "ad" in c.lower() and c != "Proje_ID":
                                yeni_proje[c] = np_ad.strip()
                                break
                        try:
                            conn.update(worksheet="Projeler",
                                        data=pd.concat([projeler_df, yeni_proje], ignore_index=True))
                            st.success(f"✅ '{np_ad}' eklendi! (ID: {yeni_pid})")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Kaydedilemedi: {e}")

            # Düzenleme tablosu
            st.markdown("#### Mevcut Projeleri Düzenle")
            st.info("💡 Hücrelere çift tıklayarak düzeltebilirsiniz.")
            duz_projeler = st.data_editor(
                projeler_df, use_container_width=True,
                hide_index=True, num_rows="fixed", key="sef_projeler_editor"
            )
            if st.button("💾 Değişiklikleri Kaydet", key="proje_kaydet_btn"):
                try:
                    conn.update(worksheet="Projeler", data=duz_projeler)
                    st.success("✅ Güncellendi!")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Hata: {e}")

            st.markdown("---")

            # Proje Sil
            st.markdown("#### 🗑️ Proje Sil")
            proje_id_listesi = projeler_df["Proje_ID"].dropna().unique().tolist()
            if proje_id_listesi:
                silinecek = st.selectbox("Silinecek Proje:", proje_id_listesi, key="silinecek_proje_sec")
                onay_cb   = st.checkbox(f"'{silinecek}' projesini silmek istediğimi onaylıyorum.", key="proje_sil_onay")
                if st.button("🗑️ Seçili Projeyi Sil", type="primary",
                             disabled=not onay_cb, key="proje_sil_btn"):
                    if proje_sil(projeler_df, conn, silinecek):
                        st.success(f"'{silinecek}' silindi!")
                        st.cache_data.clear()
                        st.rerun()
            else:
                st.info("Silinecek proje bulunmuyor.")

    # ──────────────────────────────────────────────────────────────────────────
    # PERSONEL EKRANI
    # ──────────────────────────────────────────────────────────────────────────
    elif rol_normalize == "personel":
        st.markdown("<div class='section-header'>📋 Görev Listem</div>", unsafe_allow_html=True)

        ilgili_ana_id = []
        if not alt_gorevler_df.empty:
            ilgili_ana_id = alt_gorevler_df.loc[
                alt_gorevler_df["Atanan_Kişi"] == current_name, "Ana_Gorev_ID"
            ].unique().tolist()

        benim_gorevlerim = gorevler_df[
            (gorevler_df["Atanan_Kişi"] == current_name) |
            (gorevler_df["Atanan_Kişi"] == "Herkes")     |
            (gorevler_df["Gorev_ID"].isin(ilgili_ana_id))
        ]

        if benim_gorevlerim.empty:
            st.markdown("""
            <div class='empty-state'>
                <div class='icon'>🎉</div>
                <div class='msg'>Harika! Üzerinize atanmış bekleyen görev yok.</div>
            </div>""", unsafe_allow_html=True)
        else:
            metrik_satiri_ciz(benim_gorevlerim)
            st.divider()

            for _, row in gorev_sirala(benim_gorevlerim).iterrows():
                gecik = gecikme_var_mi(row.get("Son_Tarih","")) and row["Gorev_Durumu"] != "Tamamlandı"
                etiket = " 🔴 GECİKMİŞ" if gecik else ""
                ikon = "🔴" if gecik else ("✅" if row["Gorev_Durumu"] == "Tamamlandı" else "📌")
                with st.expander(f"{ikon} {row['Gorev_Tanimi']}{etiket}  ·  📅 {row.get('Son_Tarih','')}"):
                    gorev_karti_render(
                        row, gorevler_df, alt_gorevler_df, kullanicilar_df,
                        conn, rol_normalize, current_name, "personel"
                    )

    else:
        st.warning(f"'{st.session_state.current_role}' rolü tanınmıyor. Yönetici ile iletişime geçin.")

# ═══════════════════════════════════════════════════════════════════════════════
# AI ASİSTAN SEKMESİ
# ═══════════════════════════════════════════════════════════════════════════════
with tab_ai:

    st.markdown("""
    <div class='ai-header'>
      <h2>🤖 Ofis AI Asistanı</h2>
      <p>Proje analiz botu — projelerinize dair her soruyu sorabilirsiniz.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Sağlayıcı kontrol ────────────────────────────────────────────────────
    try:
        from groq import Groq as GroqClient
        GROQ_AVAILABLE = True
    except ImportError:
        GROQ_AVAILABLE = False

    try:
        from google import genai as google_genai
        GENAI_AVAILABLE = True
    except ImportError:
        GENAI_AVAILABLE = False

    # ── API Key'leri secrets veya session'dan oku ─────────────────────────────
    if "groq_api_key" not in st.session_state:
        st.session_state.groq_api_key = ""
        try:
            st.session_state.groq_api_key = st.secrets.get("GROQ_API_KEY", "")
        except Exception:
            pass

    if "gemini_api_key" not in st.session_state:
        st.session_state.gemini_api_key = ""
        try:
            st.session_state.gemini_api_key = st.secrets.get("GEMINI_API_KEY", "")
        except Exception:
            pass

    groq_key   = st.session_state.groq_api_key
    gemini_key = st.session_state.gemini_api_key

    # Aktif sağlayıcıyı belirle
    if GROQ_AVAILABLE and groq_key:
        aktif_saglayici = "groq"
    elif GENAI_AVAILABLE and gemini_key:
        aktif_saglayici = "gemini"
    else:
        aktif_saglayici = None

    # ── API Key Kurulum Arayüzü ───────────────────────────────────────────────
    if aktif_saglayici is None:
        st.info("🔑 AI asistanı kullanmak için aşağıdaki adımları izleyin.")
        with st.expander("📘 Nasıl API Key Alırım? (Ücretsiz — 2 dk)", expanded=True):
            st.markdown("""
**🚀 Önerilen: Groq API (tamamen ücretsiz, kota sorunu yok)**

1. **[console.groq.com](https://console.groq.com)** adresine gidin
2. Google hesabınızla kayıt olun (ücretsiz)
3. Sol menüden **"API Keys"** → **"Create API Key"** tıklayın
4. Oluşan key'i (`gsk_...`) aşağıya yapıştırın
5. ✅ Bitti! Artık AI asistanı kullanabilirsiniz.

---

**Alternatif: Google Gemini API**
1. [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) adresine gidin
2. **"Create API key in new project"** seçin (yeni proje = taze kota)
3. Key'i aşağıya yapıştırın
""")

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("#### 🟢 Groq API Key (Önerilen)")
            girilen_groq = st.text_input(
                "Groq API Key:", type="password", key="groq_key_input",
                placeholder="gsk_..."
            )
            if st.button("✅ Groq Key'i Kaydet", key="groq_kaydet"):
                if girilen_groq.strip():
                    st.session_state.groq_api_key = girilen_groq.strip()
                    st.rerun()
                else:
                    st.warning("Lütfen bir key girin.")

        with col_g2:
            st.markdown("#### 🔵 Google Gemini API Key")
            girilen_gemini = st.text_input(
                "Gemini API Key:", type="password", key="gemini_key_input",
                placeholder="AQ... veya AIzaSy..."
            )
            if st.button("✅ Gemini Key'i Kaydet", key="gemini_kaydet"):
                if girilen_gemini.strip():
                    st.session_state.gemini_api_key = girilen_gemini.strip()
                    st.rerun()
                else:
                    st.warning("Lütfen bir key girin.")

        st.stop()

    # ── Sağlayıcı bilgisi ─────────────────────────────────────────────────────
    if aktif_saglayici == "groq":
        st.success("✅ **Groq API** aktif — llama-3.3-70b modeli kullanılıyor")
    else:
        st.info("🔵 **Google Gemini API** aktif")

    with st.sidebar:
        st.markdown("---")
        st.markdown("**🤖 AI Asistan**")
        if aktif_saglayici == "groq":
            st.caption("✅ Groq API bağlı")
        else:
            st.caption("🔵 Gemini API bağlı")
        if st.button("🔑 API Key Değiştir", key="api_key_degistir"):
            st.session_state.groq_api_key   = ""
            st.session_state.gemini_api_key = ""
            st.rerun()

    # ── Veri bağlamı ──────────────────────────────────────────────────────────
    def veri_baglamini_olustur():
        bugun = datetime.date.today()
        s = [f"Bugünün tarihi: {bugun.strftime('%d %B %Y')}"]
        s.append("\n=== PROJELER ===")
        s.append(projeler_df.to_string(index=False) if not projeler_df.empty else "(Yok)")
        s.append("\n=== GÖREVLER ===")
        s.append(gorevler_df.to_string(index=False) if not gorevler_df.empty else "(Yok)")
        s.append("\n=== ALT GÖREVLER ===")
        s.append(alt_gorevler_df.to_string(index=False) if not alt_gorevler_df.empty else "(Yok)")
        s.append("\n=== PERSONEL ===")
        s.append(kullanicilar_df.to_string(index=False) if not kullanicilar_df.empty else "(Yok)")

        if not gorevler_df.empty:
            s.append("\n=== PERSONEL İŞ YÜKÜ ===")
            for kisi in kullanicilar_df["Ad_Soyad"].tolist():
                kg = gorevler_df[
                    (gorevler_df["Atanan_Kişi"] == kisi) |
                    (gorevler_df["Atanan_Kişi"] == "Herkes")
                ]
                s.append(f"  {kisi}: Başlamadı={len(kg[kg['Gorev_Durumu']=='Başlamadı'])}, "
                         f"Devam={len(kg[kg['Gorev_Durumu']=='Devam Ediyor'])}, "
                         f"Tamamlandı={len(kg[kg['Gorev_Durumu']=='Tamamlandı'])}")

        if not gorevler_df.empty and "Son_Tarih" in gorevler_df.columns:
            try:
                hb = bugun - datetime.timedelta(days=bugun.weekday())
                hs = hb + datetime.timedelta(days=6)
                gt = gorevler_df.copy()
                gt["_dt"] = pd.to_datetime(gt["Son_Tarih"], errors="coerce")
                bu_hafta = gt[(gt["_dt"].dt.date >= hb) & (gt["_dt"].dt.date <= hs)]
                gecikmus  = gt[(gt["_dt"].dt.date < bugun) & (gt["Gorev_Durumu"] != "Tamamlandı")]
                s.append(f"\n=== BU HAFTA TERMİNİ DOLAN ({hb} – {hs}) ===")
                s.append(bu_hafta[["Gorev_ID","Gorev_Tanimi","Atanan_Kişi","Son_Tarih","Gorev_Durumu"]].to_string(index=False) if not bu_hafta.empty else "(Yok)")
                s.append("\n=== GECİKMİŞ GÖREVLER ===")
                s.append(gecikmus[["Gorev_ID","Gorev_Tanimi","Atanan_Kişi","Son_Tarih","Gorev_Durumu"]].to_string(index=False) if not gecikmus.empty else "(Yok)")
            except Exception:
                pass
        return "\n".join(s)

    SISTEM_PROMPT = (
        "Sen 'Ofis Asistanı' adında, Türkçe konuşan bir proje yönetimi AI asistanısın. "
        "Görevin: proje/görev durumu analizi, haftalık raporlar, personel iş yükü analizi, "
        "kritik görevleri vurgulama. Her zaman yapılandırılmış, okunması kolay Markdown "
        "formatında yanıt ver. Günümüz tarihi sana verilmiştir."
    )

    # ── AI çağrısı fonksiyonu ─────────────────────────────────────────────────
    def ai_yanit_uret(sorgu: str) -> str:
        """Groq veya Gemini ile yanıt üretir. Yanıt metnini döndürür."""
        veri = veri_baglamini_olustur()
        tam_sorgu = f"{SISTEM_PROMPT}\n\nGüncel ofis verileri:\n{veri}\n\nKullanıcı sorusu: {sorgu}"

        if aktif_saglayici == "groq":
            client = GroqClient(api_key=groq_key)
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": tam_sorgu}],
                max_tokens=2048,
                temperature=0.4,
            )
            return resp.choices[0].message.content

        else:  # gemini
            gc = google_genai.Client(api_key=gemini_key)
            for model_adi in ["gemini-2.0-flash", "gemini-2.0-flash-lite"]:
                try:
                    yanit = gc.models.generate_content(model=model_adi, contents=tam_sorgu)
                    return yanit.text
                except Exception:
                    continue
            raise RuntimeError("Gemini modelleri yanıt üretemedi. Kota dolmuş olabilir, 1-2 dakika bekleyip tekrar deneyin.")

    # ── Chat geçmişi ──────────────────────────────────────────────────────────
    if "ai_chat_history" not in st.session_state:
        st.session_state.ai_chat_history = []

    # ── Hızlı Analizler ───────────────────────────────────────────────────────
    st.markdown("**⚡ Hızlı Analizler:**")
    b1, b2, b3, b4, b5 = st.columns(5)
    hizli_sorgu = None
    if b1.button("📅 Haftalık Rapor",    use_container_width=True, key="ai_btn_haftalik"):
        hizli_sorgu = "Bu haftanın detaylı proje raporunu çıkar. Tamamlanan, devam eden, geciken ve bu hafta termini dolan görevleri listele."
    if b2.button("👥 Personel Analizi",  use_container_width=True, key="ai_btn_personel"):
        hizli_sorgu = "Her personelin şu anki görevlerini, iş yükünü ve müsaitlik durumunu analiz et. Kimin fazla yüklü, kimin boş olduğunu söyle."
    if b3.button("🚨 Kritik Görevler",   use_container_width=True, key="ai_btn_kritik"):
        hizli_sorgu = "Gecikmiş görevleri ve bu hafta bitmesi gereken tamamlanmamış görevleri kritiklik sırasına göre listele."
    if b4.button("📊 Proje Özeti",        use_container_width=True, key="ai_btn_proje"):
        hizli_sorgu = "Tüm projelerin genel durumunu özetle. Her proje için tamamlanma yüzdesi ve açık görev sayısı hakkında bilgi ver."
    if b5.button("🗑️ Sohbeti Sıfırla",  use_container_width=True, key="ai_btn_temizle"):
        st.session_state.ai_chat_history = []
        st.rerun()

    st.markdown("---")

    # ── Geçmiş mesajlar ───────────────────────────────────────────────────────
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.ai_chat_history:
            with st.chat_message("user" if msg["role"] == "user" else "assistant"):
                st.markdown(msg["content"])

    # ── Yeni mesaj ────────────────────────────────────────────────────────────
    kullanici_mesaji = st.chat_input("Projelere dair bir soru sorun veya rapor isteyin...")
    aktif_sorgu = hizli_sorgu or kullanici_mesaji

    if aktif_sorgu:
        st.session_state.ai_chat_history.append({"role": "user", "content": aktif_sorgu})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(aktif_sorgu)

        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner("Analiz ediliyor..."):
                    try:
                        yanit_metni = ai_yanit_uret(aktif_sorgu)
                        st.markdown(yanit_metni)
                        st.session_state.ai_chat_history.append(
                            {"role": "assistant", "content": yanit_metni}
                        )
                    except Exception as e:
                        hata = f"⚠️ Yanıt üretilemedi: {str(e)}"
                        st.error(hata)
                        st.session_state.ai_chat_history.append(
                            {"role": "assistant", "content": hata}
                        )
        st.rerun()

