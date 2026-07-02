import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Sayfa Ayarları
st.set_page_config(page_title="Ofis Proje Yönetimi", layout="wide")

st.markdown("""
    <style>
    .stButton>button {
        border-radius: 8px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { height: 50px; padding-top: 10px; padding-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

st.title("🏢 Egeşehir Ofis Yönetim Paneli")

DURUM_SECENEKLERI = ["Başlamadı", "Devam Ediyor", "Tamamlandı"]

# Alt görevler için gereken sütunlar - Google Sheets'te "AltGorevler" adında
# bir sayfa (worksheet) oluşturup bu başlıkları eklemeniz gerekir:
ALT_GOREV_KOLONLARI = [
    "Alt_Gorev_ID", "Ana_Gorev_ID", "Alt_Gorev_Tanimi",
    "Atanan_Kişi", "Son_Tarih", "Gorev_Durumu", "Aciklama"
]


def _id_esle(seri, deger):
    """Gorev_ID / Alt_Gorev_ID karşılaştırmasını baştaki-sondaki boşluklara
    ve tip farklarına (metin/sayı) karşı dayanıklı hale getirir."""
    return seri.astype(str).str.strip() == str(deger).strip()


def gorev_guncelle(gorevler_df, conn, gorev_id, yeni_durum, yeni_aciklama):
    mask = _id_esle(gorevler_df['Gorev_ID'], gorev_id)
    if not mask.any():
        st.error(f"⚠️ Gorev_ID '{gorev_id}' tabloda bulunamadı, kaydedilemedi.")
        return False
    gorevler_df.loc[mask, ['Gorev_Durumu', 'Aciklama']] = [yeni_durum, yeni_aciklama]
    try:
        conn.update(worksheet="Gorevler", data=gorevler_df)
    except Exception as e:
        st.error(f"⚠️ Google Sheets'e kaydedilirken hata oluştu: {e}")
        return False
    return True


def alt_gorev_guncelle(alt_gorevler_df, conn, alt_gorev_id, yeni_durum, yeni_aciklama):
    mask = _id_esle(alt_gorevler_df['Alt_Gorev_ID'], alt_gorev_id)
    if not mask.any():
        st.error(f"⚠️ Alt_Gorev_ID '{alt_gorev_id}' tabloda bulunamadı, kaydedilemedi.")
        return False
    alt_gorevler_df.loc[mask, ['Gorev_Durumu', 'Aciklama']] = [yeni_durum, yeni_aciklama]
    try:
        conn.update(worksheet="AltGorevler", data=alt_gorevler_df)
    except Exception as e:
        st.error(f"⚠️ Google Sheets'e kaydedilirken hata oluştu: {e}")
        return False
    return True


def gorev_sil(gorevler_df, alt_gorevler_df, conn, gorev_id):
    """Ana görevi ve bağlı tüm alt görevleri siler."""
    mask = _id_esle(gorevler_df['Gorev_ID'], gorev_id)
    if not mask.any():
        st.error(f"⚠️ Gorev_ID '{gorev_id}' tabloda bulunamadı.")
        return False
    yeni_gorevler = gorevler_df[~mask].reset_index(drop=True)
    # Bağlı alt görevleri de sil
    if not alt_gorevler_df.empty:
        alt_mask = _id_esle(alt_gorevler_df['Ana_Gorev_ID'], gorev_id)
        yeni_alt_gorevler = alt_gorevler_df[~alt_mask].reset_index(drop=True)
    else:
        yeni_alt_gorevler = alt_gorevler_df
    try:
        conn.update(worksheet="Gorevler", data=yeni_gorevler)
        conn.update(worksheet="AltGorevler", data=yeni_alt_gorevler)
    except Exception as e:
        st.error(f"⚠️ Görev silinirken hata oluştu: {e}")
        return False
    return True


def proje_sil(projeler_df, conn, proje_id):
    """Projeyi listeden siler."""
    mask = projeler_df['Proje_ID'].astype(str).str.strip() == str(proje_id).strip()
    if not mask.any():
        st.error(f"⚠️ Proje_ID '{proje_id}' tabloda bulunamadı.")
        return False
    yeni_projeler = projeler_df[~mask].reset_index(drop=True)
    try:
        conn.update(worksheet="Projeler", data=yeni_projeler)
    except Exception as e:
        st.error(f"⚠️ Proje silinirken hata oluştu: {e}")
        return False
    return True


def alt_gorev_ekle(alt_gorevler_df, conn, ana_gorev_id, tanim, kisi, tarih):
    yeni_id = f"AG-{len(alt_gorevler_df) + 1:03d}"
    yeni_satir = pd.DataFrame([{
        "Alt_Gorev_ID": yeni_id,
        "Ana_Gorev_ID": ana_gorev_id,
        "Alt_Gorev_Tanimi": tanim,
        "Atanan_Kişi": kisi,
        "Son_Tarih": tarih.strftime("%Y-%m-%d"),
        "Gorev_Durumu": "Başlamadı",
        "Aciklama": ""
    }])
    guncel = pd.concat([alt_gorevler_df, yeni_satir], ignore_index=True)
    try:
        conn.update(worksheet="AltGorevler", data=guncel)
    except Exception as e:
        st.error(f"⚠️ Alt görev kaydedilirken hata oluştu: {e}")
        return False
    return True


def durum_notu_karti(kayit_id, mevcut_durum, mevcut_aciklama, salt_okunur, key_prefix, kaydet_fonksiyonu):
    """Tek bir görev/alt görev için durum + not düzenleme arayüzü çizer."""
    try:
        varsayilan_index = DURUM_SECENEKLERI.index(mevcut_durum)
    except (ValueError, TypeError):
        varsayilan_index = 0

    yeni_durum = st.selectbox(
        "Durum:", DURUM_SECENEKLERI, index=varsayilan_index,
        disabled=salt_okunur, key=f"{key_prefix}_durum"
    )

    if pd.isna(mevcut_aciklama):
        mevcut_aciklama = ""

    yeni_aciklama = st.text_area(
        "Açıklama / Notlar:", value=mevcut_aciklama,
        disabled=salt_okunur, key=f"{key_prefix}_not"
    )

    if salt_okunur:
        st.caption("🔒 Bu görev 'Herkes'e atanmıştır veya size ait değildir; durumunu yalnızca Şef değiştirebilir.")
    else:
        if st.button("Durumu ve Notu Güncelle", key=f"{key_prefix}_btn"):
            if kaydet_fonksiyonu(kayit_id, yeni_durum, yeni_aciklama):
                st.success("Güncellendi!")
                st.cache_data.clear()
                st.rerun()


def gorev_karti_render(row, gorevler_df, alt_gorevler_df, kullanicilar_df, conn,
                        rol_normalize, current_name, key_prefix):
    """Bir ana görevi; durum/not editörü + alt görevler listesi + (Şef ise)
    alt görev ekleme formuyla birlikte çizer."""
    gorev_id = row['Gorev_ID']

    st.write(f"**Proje ID:** {row['Bagli_Oldugu_Proje_ID']} | **Etap:** {row['Etap_Adi']}")
    st.write(f"**Atanan Kişi:** {row['Atanan_Kişi']}")

    # Kural: görev "Herkes"e atanmışsa veya bu kişiye ait değilse (örn. sadece
    # bir alt görevi yüzünden listede görünüyorsa), durumu yalnızca Şef değiştirebilir.
    salt_okunur = (rol_normalize != "şef") and (row['Atanan_Kişi'] != current_name)

    durum_notu_karti(
        kayit_id=gorev_id,
        mevcut_durum=row['Gorev_Durumu'],
        mevcut_aciklama=row.get('Aciklama', ""),
        salt_okunur=salt_okunur,
        key_prefix=f"{key_prefix}_ana_{gorev_id}",
        kaydet_fonksiyonu=lambda gid, durum, aciklama: gorev_guncelle(gorevler_df, conn, gid, durum, aciklama)
    )

    # --- ALT GÖREVLER ---
    if not alt_gorevler_df.empty:
        alt_liste = alt_gorevler_df[_id_esle(alt_gorevler_df['Ana_Gorev_ID'], gorev_id)]
    else:
        alt_liste = alt_gorevler_df

    if not alt_liste.empty:
        st.markdown("---")
        st.markdown("**🔹 Alt Görevler**")
        for _, alt_row in alt_liste.iterrows():
            st.markdown(f"*{alt_row['Alt_Gorev_Tanimi']}* — 👤 {alt_row['Atanan_Kişi']} — 📅 {alt_row['Son_Tarih']}")
            alt_salt_okunur = (rol_normalize != "şef") and (alt_row['Atanan_Kişi'] != current_name)
            durum_notu_karti(
                kayit_id=alt_row['Alt_Gorev_ID'],
                mevcut_durum=alt_row['Gorev_Durumu'],
                mevcut_aciklama=alt_row.get('Aciklama', ""),
                salt_okunur=alt_salt_okunur,
                key_prefix=f"{key_prefix}_alt_{alt_row['Alt_Gorev_ID']}",
                kaydet_fonksiyonu=lambda aid, durum, aciklama: alt_gorev_guncelle(alt_gorevler_df, conn, aid, durum, aciklama)
            )
            st.markdown("&nbsp;", unsafe_allow_html=True)

    # --- ŞEF İÇİN: ALT GÖREV EKLEME + GÖREV SİLME ---
    if rol_normalize == "şef":
        st.markdown("---")
        with st.expander("➕ Bu Göreve Alt Görev Ekle"):
            with st.form(f"{key_prefix}_alt_ekle_form_{gorev_id}"):
                alt_tanim = st.text_input("Alt Görev Tanımı")
                alt_kisi = st.selectbox("Atanan Personel", kullanicilar_df['Ad_Soyad'].tolist())
                alt_tarih = st.date_input("Son Tarih")
                alt_ekle_btn = st.form_submit_button("Alt Görevi Ekle")

                if alt_ekle_btn:
                    if not alt_tanim.strip():
                        st.warning("Lütfen alt görev tanımını girin.")
                    else:
                        if alt_gorev_ekle(alt_gorevler_df, conn, gorev_id, alt_tanim.strip(), alt_kisi, alt_tarih):
                            st.success("Alt görev eklendi!")
                            st.cache_data.clear()
                            st.rerun()

        with st.expander("🗑️ Bu Görevi Sil"):
            st.warning("⚠️ Bu işlem geri alınamaz! Göreve bağlı tüm alt görevler de silinecektir.")
            onay = st.checkbox("Silmek istediğimi onaylıyorum.", key=f"{key_prefix}_sil_onay_{gorev_id}")
            if st.button("🗑️ Görevi Kalıcı Olarak Sil", type="primary", disabled=not onay,
                         key=f"{key_prefix}_sil_btn_{gorev_id}"):
                if gorev_sil(gorevler_df, alt_gorevler_df, conn, gorev_id):
                    st.success("Görev silindi!")
                    st.cache_data.clear()
                    st.rerun()


# ── VERİ KATMANI (her iki sekme de kullanır) ──────────────────────────────
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=5)
def load_data():
    kullanicilar = conn.read(worksheet="Kullanicilar")
    projeler = conn.read(worksheet="Projeler")
    gorevler = conn.read(worksheet="Gorevler")
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

# SEKMELERİ (TABS) OLUŞTURUYORUZ
tab_gorev, tab_ai = st.tabs(["📋 Görev Paneli", "🤖 AI Asistan"])

with tab_gorev:

    # Session State (Giriş Yapmış Kullanıcıyı Hatırlama)
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.session_state.current_role = None
        st.session_state.current_name = None

    # --- GİRİŞ (LOGIN) EKRANI ---
    if not st.session_state.logged_in:
        st.title("🔐 Sisteme Giriş")
        kullanici_adi_input = st.text_input("Kullanıcı Adı")

        if st.button("Giriş Yap"):
            user_match = kullanicilar_df[kullanicilar_df['Kullanici_Adi'] == kullanici_adi_input]

            if not user_match.empty:
                st.session_state.logged_in = True
                st.session_state.current_user = kullanici_adi_input
                st.session_state.current_role = str(user_match.iloc[0]['Rol']).strip()
                st.session_state.current_name = str(user_match.iloc[0]['Ad_Soyad']).strip()
                st.rerun()
            else:
                st.error("Kullanıcı bulunamadı. Lütfen tekrar deneyin.")

    # --- ANA UYGULAMA EKRANI ---
    else:
        col1, col2 = st.columns([8, 2])
        with col1:
            st.write(f"Hoş geldin, **{st.session_state.current_name}** (Rol: {st.session_state.current_role})")
        with col2:
            if st.button("Çıkış Yap"):
                st.session_state.logged_in = False
                st.session_state.current_user = None
                st.session_state.current_role = None
                st.session_state.current_name = None
                st.rerun()

        st.divider()

        rol_normalize = str(st.session_state.current_role).strip().casefold()
        current_name = st.session_state.current_name

        # ==========================================
        # ŞEF EKRANI
        # ==========================================
        if rol_normalize == "şef":
            st.header("👑 Şef Kontrol Paneli")

            tab_benim, tab_tum, tab_yeni, tab_projeler = st.tabs(
                ["Benim İşlerim", "Tüm İşlerin Durumu", "Yeni Görev Ata", "Projeler"]
            )

            with tab_benim:
                st.subheader("Bana Atanan Görevler")

                # Kendine / Herkes'e atanan görevler + kendisine atanmış bir alt
                # görevi olan görevler (böylece o alt görev de burada görünür)
                ilgili_ana_id = []
                if not alt_gorevler_df.empty:
                    ilgili_ana_id = alt_gorevler_df.loc[
                        alt_gorevler_df['Atanan_Kişi'] == current_name, 'Ana_Gorev_ID'
                    ].unique().tolist()

                sef_gorevlerim = gorevler_df[
                    (gorevler_df['Atanan_Kişi'] == current_name) |
                    (gorevler_df['Atanan_Kişi'] == 'Herkes') |
                    (gorevler_df['Gorev_ID'].isin(ilgili_ana_id))
                ]

                st.markdown("### 📊 Anlık Durum Özeti (Benim İşlerim)")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Toplam İş", len(sef_gorevlerim))
                with col2:
                    st.metric("Devam Eden", len(sef_gorevlerim[sef_gorevlerim['Gorev_Durumu'] == 'Devam Ediyor']))
                with col3:
                    st.metric("Tamamlanan", len(sef_gorevlerim[sef_gorevlerim['Gorev_Durumu'] == 'Tamamlandı']))

                st.divider()

                if sef_gorevlerim.empty:
                    st.info("Üzerinize atanmış bekleyen bir görev bulunmuyor.")
                else:
                    for _, row in sef_gorevlerim.iterrows():
                        with st.expander(f"📌 {row['Gorev_Tanimi']} (Son Tarih: {row['Son_Tarih']})"):
                            gorev_karti_render(
                                row, gorevler_df, alt_gorevler_df, kullanicilar_df, conn,
                                rol_normalize, current_name, key_prefix="sef_benim"
                            )

            with tab_tum:
                st.subheader("Ofisteki Tüm Görevler")

                st.markdown("### 📊 Anlık Durum Özeti (Tüm Ofis)")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Toplam Kayıtlı Görev", len(gorevler_df))
                with col2:
                    st.metric("Devam Eden", len(gorevler_df[gorevler_df['Gorev_Durumu'] == 'Devam Ediyor']))
                with col3:
                    st.metric("Tamamlanan", len(gorevler_df[gorevler_df['Gorev_Durumu'] == 'Tamamlandı']))

                st.divider()

                secilen_proje = st.selectbox(
                    "🔍 Projeye Göre Filtrele",
                    ["Tümü"] + projeler_df['Proje_ID'].dropna().unique().tolist()
                )

                if secilen_proje == "Tümü":
                    filtrelenmis_df = gorevler_df.copy()
                else:
                    filtrelenmis_df = gorevler_df[gorevler_df['Bagli_Oldugu_Proje_ID'] == secilen_proje].copy()

                st.markdown("---")

                # ── Başlık Satırı ──────────────────────────────────────────
                hdr = st.columns([0.6, 1.0, 1.2, 2.8, 1.4, 1.1, 1.5, 0.5, 0.5])
                for col_h, label in zip(hdr, ["ID", "Proje", "Etap", "Görev Tanımı", "Atanan", "Son Tarih", "Durum", "💾", "🗑️"]):
                    col_h.markdown(f"<small><b>{label}</b></small>", unsafe_allow_html=True)
                st.markdown("<hr style='margin:2px 0 6px 0;'>", unsafe_allow_html=True)

                for _, row in filtrelenmis_df.iterrows():
                    gorev_id = row['Gorev_ID']

                    # Alt görev kontrolü
                    if not alt_gorevler_df.empty:
                        alt_liste = alt_gorevler_df[_id_esle(alt_gorevler_df['Ana_Gorev_ID'], gorev_id)]
                    else:
                        alt_liste = pd.DataFrame(columns=ALT_GOREV_KOLONLARI)
                    has_alts = not alt_liste.empty

                    # ── Ana Görev Satırı ───────────────────────────────────
                    c1, c2, c3, c4, c5, c6, c7, c8, c9 = st.columns([0.6, 1.0, 1.2, 2.8, 1.4, 1.1, 1.5, 0.5, 0.5])
                    c1.caption(str(gorev_id))
                    c2.caption(str(row.get('Bagli_Oldugu_Proje_ID', '')))
                    c3.caption(str(row.get('Etap_Adi', '')))
                    c4.write(f"{'🔹 ' if has_alts else ''}{str(row.get('Gorev_Tanimi', ''))}")
                    c5.caption(str(row.get('Atanan_Kişi', '')))
                    c6.caption(str(row.get('Son_Tarih', '')))

                    try:
                        durum_idx = DURUM_SECENEKLERI.index(row['Gorev_Durumu'])
                    except (ValueError, TypeError):
                        durum_idx = 0

                    yeni_durum_tum = c7.selectbox(
                        "durum", DURUM_SECENEKLERI, index=durum_idx,
                        key=f"tum_durum_{gorev_id}",
                        label_visibility="collapsed"
                    )

                    if c8.button("💾", key=f"tum_kaydet_{gorev_id}", help="Durumu kaydet"):
                        if gorev_guncelle(gorevler_df, conn, gorev_id, yeni_durum_tum, row.get('Aciklama', '')):
                            st.success(f"✅ '{row['Gorev_Tanimi']}' güncellendi!")
                            st.cache_data.clear()
                            st.rerun()

                    if c9.button("🗑️", key=f"tum_sil_{gorev_id}", help="Görevi sil"):
                        st.session_state[f"tum_sil_onay_{gorev_id}"] = True

                    # ── Silme Onayı ────────────────────────────────────────
                    if st.session_state.get(f"tum_sil_onay_{gorev_id}", False):
                        with st.container():
                            st.warning(f"⚠️ **'{row['Gorev_Tanimi']}'** görevi ve bağlı tüm alt görevleri silinecek. Emin misiniz?")
                            evet_col, iptal_col, _ = st.columns([1, 1, 5])
                            if evet_col.button("✅ Evet, Sil", key=f"tum_sil_evet_{gorev_id}", type="primary"):
                                if gorev_sil(gorevler_df, alt_gorevler_df, conn, gorev_id):
                                    st.session_state.pop(f"tum_sil_onay_{gorev_id}", None)
                                    st.cache_data.clear()
                                    st.rerun()
                            if iptal_col.button("❌ İptal", key=f"tum_sil_iptal_{gorev_id}"):
                                st.session_state.pop(f"tum_sil_onay_{gorev_id}", None)
                                st.rerun()

                    # ── Alt Görevler (Açılır-Kapanır) ─────────────────────
                    if has_alts:
                        with st.expander(f"🔽 {len(alt_liste)} alt görev — genişletmek için tıklayın"):
                            # Alt görev başlık satırı
                            ah = st.columns([0.7, 2.8, 1.4, 1.1, 1.5, 0.6])
                            for col_ah, lbl in zip(ah, ["Alt ID", "Alt Görev Tanımı", "Atanan", "Son Tarih", "Durum", "💾"]):
                                col_ah.markdown(f"<small><b>{lbl}</b></small>", unsafe_allow_html=True)
                            st.markdown("<hr style='margin:2px 0 4px 0;'>", unsafe_allow_html=True)

                            for _, alt_row in alt_liste.iterrows():
                                alt_id = alt_row['Alt_Gorev_ID']
                                a1, a2, a3, a4, a5, a6 = st.columns([0.7, 2.8, 1.4, 1.1, 1.5, 0.6])
                                a1.caption(str(alt_id))
                                a2.write(str(alt_row.get('Alt_Gorev_Tanimi', '')))
                                a3.caption(str(alt_row.get('Atanan_Kişi', '')))
                                a4.caption(str(alt_row.get('Son_Tarih', '')))

                                try:
                                    alt_durum_idx = DURUM_SECENEKLERI.index(alt_row['Gorev_Durumu'])
                                except (ValueError, TypeError):
                                    alt_durum_idx = 0

                                yeni_alt_durum = a5.selectbox(
                                    "alt_durum", DURUM_SECENEKLERI, index=alt_durum_idx,
                                    key=f"tum_alt_durum_{alt_id}",
                                    label_visibility="collapsed"
                                )
                                if a6.button("💾", key=f"tum_alt_kaydet_{alt_id}", help="Alt görevi kaydet"):
                                    if alt_gorev_guncelle(alt_gorevler_df, conn, alt_id, yeni_alt_durum, alt_row.get('Aciklama', '')):
                                        st.success(f"✅ Alt görev güncellendi!")
                                        st.cache_data.clear()
                                        st.rerun()

                    st.markdown("<hr style='margin:4px 0; border-color:#e8e8e8;'>", unsafe_allow_html=True)

            with tab_yeni:
                st.subheader("Yeni Görev Oluştur")
                with st.form("yeni_gorev_formu"):
                    yeni_proje_id = st.selectbox("Bağlı Olduğu Proje", projeler_df['Proje_ID'].tolist())
                    yeni_etap = st.text_input("Etap Adı (Opsiyonel)")
                    yeni_tanim = st.text_area("Görev Tanımı")

                    kisi_listesi = kullanicilar_df['Ad_Soyad'].tolist()
                    kisi_listesi.insert(0, "Herkes")
                    yeni_kisi = st.selectbox("Atanan Kişi", kisi_listesi)

                    yeni_tarih = st.date_input("Son Tarih")

                    ekle_btn = st.form_submit_button("Görevi Ata")

                    if ekle_btn:
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

                        guncel_gorevler = pd.concat([gorevler_df, yeni_satir], ignore_index=True)
                        try:
                            conn.update(worksheet="Gorevler", data=guncel_gorevler)
                            st.success("Görev başarıyla atandı!")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"⚠️ Kaydedilirken hata oluştu: {e}")

            with tab_projeler:
                st.subheader("Tüm Projeler (Düzenlenebilir)")
                st.info("💡 Proje durumlarını veya detaylarını değiştirmek için hücrelere çift tıklayın. Silmek için 🗑️ butonunu kullanın.")

                duzenlenmis_projeler = st.data_editor(
                    projeler_df, use_container_width=True, hide_index=True, key="sef_projeler_editor"
                )

                if st.button("💾 Proje Değişikliklerini Kaydet"):
                    try:
                        conn.update(worksheet="Projeler", data=duzenlenmis_projeler)
                        st.success("Proje listesi güncellendi!")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"⚠️ Kaydedilirken hata oluştu: {e}")

                st.markdown("---")
                st.markdown("#### 🗑️ Proje Sil")
                st.caption("Silmek istediğiniz projeyi seçin. Bu işlem geri alınamaz.")

                proje_id_listesi = projeler_df['Proje_ID'].dropna().unique().tolist()
                if proje_id_listesi:
                    silinecek_proje = st.selectbox(
                        "Silinecek Proje:", proje_id_listesi, key="silinecek_proje_sec"
                    )
                    proje_sil_onay = st.checkbox(
                        f"'{silinecek_proje}' projesini silmek istediğimi onaylıyorum.",
                        key="proje_sil_onay"
                    )
                    if st.button("🗑️ Seçili Projeyi Sil", type="primary",
                                 disabled=not proje_sil_onay, key="proje_sil_btn"):
                        if proje_sil(projeler_df, conn, silinecek_proje):
                            st.success(f"'{silinecek_proje}' projesi silindi!")
                            st.cache_data.clear()
                            st.rerun()
                else:
                    st.info("Silinecek proje bulunmuyor.")

        # ==========================================
        # PERSONEL EKRANI
        # ==========================================
        elif rol_normalize == "personel":
            st.header("📋 Görev Listem")

            ilgili_ana_id = []
            if not alt_gorevler_df.empty:
                ilgili_ana_id = alt_gorevler_df.loc[
                    alt_gorevler_df['Atanan_Kişi'] == current_name, 'Ana_Gorev_ID'
                ].unique().tolist()

            benim_gorevlerim = gorevler_df[
                (gorevler_df['Atanan_Kişi'] == current_name) |
                (gorevler_df['Atanan_Kişi'] == 'Herkes') |
                (gorevler_df['Gorev_ID'].isin(ilgili_ana_id))
            ]

            if benim_gorevlerim.empty:
                st.info("Harika! Üzerinize atanmış bekleyen bir görev bulunmuyor.")
            else:
                st.markdown("### 📊 Durum Özeti")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Toplam İş", len(benim_gorevlerim))
                with col2:
                    st.metric("Devam Eden", len(benim_gorevlerim[benim_gorevlerim['Gorev_Durumu'] == 'Devam Ediyor']))
                with col3:
                    st.metric("Tamamlanan", len(benim_gorevlerim[benim_gorevlerim['Gorev_Durumu'] == 'Tamamlandı']))

                st.divider()

                for _, row in benim_gorevlerim.iterrows():
                    with st.expander(f"📌 {row['Gorev_Tanimi']} (Son Tarih: {row['Son_Tarih']})"):
                        gorev_karti_render(
                            row, gorevler_df, alt_gorevler_df, kullanicilar_df, conn,
                            rol_normalize, current_name, key_prefix="personel"
                        )

        # ==========================================
        # TANIMSIZ ROL (savunma amaçlı)
        # ==========================================
        else:
            st.warning(
                f"'{st.session_state.current_role}' rolü tanınmıyor. "
                "Lütfen yönetici ile iletişime geçin."
            )

# ---------------------------------------------------------
# AI ASISTAN SEKMESI
# ---------------------------------------------------------
with tab_ai:
    import datetime
    try:
        from google import genai as google_genai
        GENAI_AVAILABLE = True
    except ImportError:
        GENAI_AVAILABLE = False

    st.markdown("""
    <style>
    .ai-header { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
                 border-radius: 16px; padding: 24px 28px; margin-bottom: 20px; }
    .ai-header h2 { color: #e2e8f0; margin: 0; font-size: 1.6rem; }
    .ai-header p  { color: #94a3b8; margin: 6px 0 0 0; font-size: 0.95rem; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="ai-header">
      <h2>Robot Yuz Ofis AI Asistani</h2>
      <p>Google Gemini destekli proje analiz botu - projenize dair her soruyu sorabilirsiniz.</p>
    </div>
    """, unsafe_allow_html=True)

    if not GENAI_AVAILABLE:
        st.error("google-genai paketi yuklu degil. Terminal: pip install google-genai")
        st.stop()

    if "gemini_api_key" not in st.session_state:
        st.session_state.gemini_api_key = ""
        try:
            st.session_state.gemini_api_key = st.secrets["GEMINI_API_KEY"]
        except Exception:
            pass

    if not st.session_state.gemini_api_key:
        with st.expander("API Anahtari Gir", expanded=True):
            girilen_key = st.text_input("Google AI Studio API anahtarinizi girin:", type="password", key="gemini_api_key_input")
            if girilen_key:
                st.session_state.gemini_api_key = girilen_key
                st.rerun()

    gemini_key = st.session_state.gemini_api_key
    if not gemini_key:
        st.info("Devam etmek icin Gemini API anahtarinizi girin.")
        st.stop()

    def veri_baglamini_olustur():
        bugun = datetime.date.today()
        s = [f"Bugunun tarihi: {bugun}"]
        s.append("\n=== PROJELER ===")
        s.append(projeler_df.to_string(index=False) if not projeler_df.empty else "(Yok)")
        s.append("\n=== GOREVLER ===")
        s.append(gorevler_df.to_string(index=False) if not gorevler_df.empty else "(Yok)")
        s.append("\n=== ALT GOREVLER ===")
        s.append(alt_gorevler_df.to_string(index=False) if not alt_gorevler_df.empty else "(Yok)")
        s.append("\n=== PERSONEL ===")
        s.append(kullanicilar_df.to_string(index=False) if not kullanicilar_df.empty else "(Yok)")
        if not gorevler_df.empty:
            s.append("\n=== PERSONEL IS YUKU ===")
            for kisi in kullanicilar_df["Ad_Soyad"].tolist():
                kg = gorevler_df[(gorevler_df["Atanan_Kisi"] == kisi) | (gorevler_df["Atanan_Kisi"] == "Herkes")]
                s.append(f"  {kisi}: Baslamadi={len(kg[kg['Gorev_Durumu']=='Baslamadi'])}, Devam={len(kg[kg['Gorev_Durumu']=='Devam Ediyor'])}, Tamam={len(kg[kg['Gorev_Durumu']=='Tamamlandi'])}")
        if not gorevler_df.empty and "Son_Tarih" in gorevler_df.columns:
            try:
                hb = bugun - datetime.timedelta(days=bugun.weekday())
                hs = hb + datetime.timedelta(days=6)
                gt = gorevler_df.copy()
                gt["_dt"] = pd.to_datetime(gt["Son_Tarih"], errors="coerce")
                bu_hafta = gt[(gt["_dt"].dt.date >= hb) & (gt["_dt"].dt.date <= hs)]
                gecikmus = gt[(gt["_dt"].dt.date < bugun) & (gt["Gorev_Durumu"] != "Tamamlandi")]
                s.append(f"\n=== BU HAFTA TERMINI DOLAN ({hb} - {hs}) ===")
                s.append(bu_hafta[["Gorev_ID","Gorev_Tanimi","Atanan_Kisi","Son_Tarih","Gorev_Durumu"]].to_string(index=False) if not bu_hafta.empty else "(Yok)")
                s.append("\n=== GECIKMIS GOREVLER ===")
                s.append(gecikmus[["Gorev_ID","Gorev_Tanimi","Atanan_Kisi","Son_Tarih","Gorev_Durumu"]].to_string(index=False) if not gecikmus.empty else "(Yok)")
            except Exception:
                pass
        return "\n".join(s)

    SISTEM_PROMPT = """Sen Turkce konusan bir proje yonetimi AI asistanisin. Gorev: proje/gorev durumu analizi, haftalik raporlar, personel is yuku analizi, kritik gorevleri vurgulama. Her zaman yapilandirilmis Markdown formatinda yanit ver."""

    if "ai_chat_history" not in st.session_state:
        st.session_state.ai_chat_history = []

    st.markdown("**Hizli Analizler:**")
    b1, b2, b3, b4, b5 = st.columns(5)
    hizli_sorgu = None
    if b1.button("Haftalik Rapor", use_container_width=True, key="ai_btn_haftalik"):
        hizli_sorgu = "Bu haftanin detayli proje raporunu cikar. Tamamlanan, devam eden, geciken ve bu hafta termini dolan gorevleri listele."
    if b2.button("Personel Analizi", use_container_width=True, key="ai_btn_personel"):
        hizli_sorgu = "Her personelin su anki gorevlerini, is yukunu ve musaitlik durumunu analiz et. Kimin fazla yuklu, kimin bos oldugunu soyle."
    if b3.button("Kritik Gorevler", use_container_width=True, key="ai_btn_kritik"):
        hizli_sorgu = "Gecikmis gorevleri ve bu hafta bitmesi gereken tamamlanmamis gorevleri kritiklik sirasina gore listele."
    if b4.button("Proje Ozeti", use_container_width=True, key="ai_btn_proje"):
        hizli_sorgu = "Tum projelerin genel durumunu ozetle. Her proje icin tamamlanma yuzdesi ve acik gorev sayisi hakkinda bilgi ver."
    if b5.button("Sohbeti Temizle", use_container_width=True, key="ai_btn_temizle"):
        st.session_state.ai_chat_history = []
        st.rerun()

    st.markdown("---")

    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.ai_chat_history:
            role = "user" if msg["role"] == "user" else "assistant"
            avatar = "Person" if msg["role"] == "user" else "Robot"
            with st.chat_message(role):
                st.markdown(msg["content"])

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
                        client = google_genai.Client(api_key=gemini_key)
                        veri_baglami = veri_baglamini_olustur()
                        tam_sorgu = f"{SISTEM_PROMPT}\n\nGuncel ofis verileri:\n{veri_baglami}\n\nKullanici sorusu: {aktif_sorgu}"

                        MODEL_ADAYLARI = ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-flash", "gemini-1.5-flash-8b"]
                        yanit_metni = None
                        son_hata = None
                        for model_adi in MODEL_ADAYLARI:
                            try:
                                yanit = client.models.generate_content(model=model_adi, contents=tam_sorgu)
                                yanit_metni = yanit.text
                                break
                            except Exception as e:
                                son_hata = str(e)
                                continue

                        if yanit_metni:
                            st.markdown(yanit_metni)
                            st.session_state.ai_chat_history.append({"role": "assistant", "content": yanit_metni})
                        else:
                            hata = f"Tum modeller basarisiz oldu. Son hata: {son_hata}"
                            st.error(hata)
                            st.session_state.ai_chat_history.append({"role": "assistant", "content": hata})
                    except Exception as e:
                        hata = f"AI yanit uretemedi: {str(e)}"
                        st.error(hata)
                        st.session_state.ai_chat_history.append({"role": "assistant", "content": hata})
        st.rerun()
