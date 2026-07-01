import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Sayfa Ayarları
st.set_page_config(page_title="Ofis Proje Yönetimi", layout="wide")

# Google Sheets Bağlantısını Başlat
conn = st.connection("gsheets", type=GSheetsConnection)

# Verileri Çekme Fonksiyonu
@st.cache_data(ttl=5) # Verileri 5 saniyede bir güncel tutar
def load_data():
    kullanicilar = conn.read(worksheet="Kullanicilar")
    projeler = conn.read(worksheet="Projeler")
    gorevler = conn.read(worksheet="Gorevler")
    return kullanicilar, projeler, gorevler

kullanicilar_df, projeler_df, gorevler_df = load_data()

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
        # Kullanıcıyı veri tabanında arama
        user_match = kullanicilar_df[kullanicilar_df['Kullanici_Adi'] == kullanici_adi_input]
        
        if not user_match.empty:
            st.session_state.logged_in = True
            st.session_state.current_user = kullanici_adi_input
            st.session_state.current_role = user_match.iloc[0]['Rol']
            st.session_state.current_name = user_match.iloc[0]['Ad_Soyad']
            st.rerun()
        else:
            st.error("Kullanıcı bulunamadı. Lütfen tekrar deneyin.")

# --- ANA UYGULAMA EKRANI ---
else:
    # Üst Menü / Çıkış
    col1, col2 = st.columns([8, 2])
    with col1:
        st.write(f"Hoş geldin, **{st.session_state.current_name}** (Rol: {st.session_state.current_role})")
    with col2:
        if st.button("Çıkış Yap"):
            st.session_state.logged_in = False
            st.session_state.current_user = None
            st.rerun()

    st.divider()

    # ==========================================
    # ŞEF EKRANI
    # ==========================================
    if st.session_state.current_role == "Şef":
        st.header("👑 Şef Kontrol Paneli")
        
        tab1, tab2, tab3 = st.tabs(["Tüm Görevler", "Yeni Görev Ata", "Projeler"])
        
        with tab1:
            st.subheader("Ofisteki Tüm Görevler")
            st.dataframe(gorevler_df, use_container_width=True, hide_index=True)
            
        with tab2:
            st.subheader("Yeni Görev Oluştur")
            with st.form("yeni_gorev_formu"):
                yeni_proje_id = st.selectbox("Bağlı Olduğu Proje", projeler_df['Proje_ID'].tolist())
                yeni_etap = st.text_input("Etap Adı (Opsiyonel)")
                yeni_tanim = st.text_area("Görev Tanımı")
                
                # Atanan kişi listesine 'Herkes' seçeneğini ekle
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
                        "Gorev_Durumu": "Başlamadı"
                    }])
                    
                    guncel_gorevler = pd.concat([gorevler_df, yeni_satir], ignore_index=True)
                    conn.update(worksheet="Gorevler", data=guncel_gorevler)
                    st.success("Görev başarıyla atandı!")
                    st.cache_data.clear()
                    st.rerun()

        with tab3:
            st.subheader("Tüm Projeler")
            st.dataframe(projeler_df, use_container_width=True, hide_index=True)

    # ==========================================
    # PERSONEL EKRANI
    # ==========================================
    elif st.session_state.current_role == "Personel":
        st.header("📋 Görev Listem")
        
        # Sadece kendine atananları VEYA 'Herkes' yazanları filtrele
        benim_gorevlerim = gorevler_df[
            (gorevler_df['Atanan_Kişi'] == st.session_state.current_name) | 
            (gorevler_df['Atanan_Kişi'] == 'Herkes')
        ]
        
        if benim_gorevlerim.empty:
            st.info("Harika! Üzerinize atanmış bekleyen bir görev bulunmuyor.")
        else:
            # Görevleri listele ve durum güncelleme mekanizması sun
            for index, row in benim_gorevlerim.iterrows():
                with st.expander(f"📌 {row['Gorev_Tanimi']} (Son Tarih: {row['Son_Tarih']})"):
                    st.write(f"**Proje ID:** {row['Bagli_Oldugu_Proje_ID']} | **Etap:** {row['Etap_Adi']}")
                    st.write(f"**Atanan Kişi:** {row['Atanan_Kişi']}")
                    
                    mevcut_durum = row['Gorev_Durumu']
                    durum_secenekleri = ["Başlamadı", "Devam Ediyor", "Tamamlandı"]
                    
                    try:
                        varsayilan_index = durum_secenekleri.index(mevcut_durum)
                    except ValueError:
                        varsayilan_index = 0
                        
                    yeni_durum = st.selectbox(
                        "Görev Durumu:", 
                        durum_secenekleri, 
                        index=varsayilan_index,
                        key=f"durum_{row['Gorev_ID']}"
                    )
                    
                    if st.button("Durumu Güncelle", key=f"btn_{row['Gorev_ID']}"):
                        # Ana dataframe'de ilgili satırı bul ve güncelle
                        gorevler_df.loc[gorevler_df['Gorev_ID'] == row['Gorev_ID'], 'Gorev_Durumu'] = yeni_durum
                        conn.update(worksheet="Gorevler", data=gorevler_df)
                        st.success("Görev durumu güncellendi!")
                        st.cache_data.clear()
                        st.rerun()