import math
import datetime
import streamlit as st
import folium
from streamlit_folium import st_folium
from folium import plugins
from astral import LocationInfo
from astral.sun import azimuth, elevation
from geopy.distance import geodesic
import streamlit.components.v1 as components
import json


# ==========================================
# 0. YÜKSEK KAPASİTELİ VERİTABANLARI
# ==========================================
@st.cache_data
def veritabani_yukle():
    with open("hat_verileri.json", "r", encoding="utf-8") as f:
        return json.load(f)


sakus_veritabanı = veritabani_yukle()


# ==========================================
# 1. PUSULA (COMPASS) VE GÜNEŞ MATEMATİĞİ
# ==========================================
def yon_hesapla(enlem1, boylam1, enlem2, boylam2):
    lat1, lat2 = math.radians(enlem1), math.radians(enlem2)
    fark = math.radians(boylam2 - boylam1)
    x = math.sin(fark) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(fark))
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def gunesi_hesapla_compass(coğrafi_rota, zaman_utc):
    if len(coğrafi_rota) < 2: return 0, 0, 0, -1, []

    gozlemci = LocationInfo("Sakarya", "Turkey", "Europe/Istanbul", coğrafi_rota[0][0], coğrafi_rota[0][1]).observer
    gunes_yuksekligi = elevation(gozlemci, zaman_utc)
    gok_cismi_acisi = azimuth(gozlemci, zaman_utc)

    sag_mesafe, sol_mesafe, toplam_mesafe = 0, 0, 0
    renkli_rota_segmentleri = []

    for i in range(len(coğrafi_rota) - 1):
        lat1, lon1 = coğrafi_rota[i]
        lat2, lon2 = coğrafi_rota[i + 1]
        mesafe = geodesic((lat1, lon1), (lat2, lon2)).meters
        if mesafe == 0: continue

        toplam_mesafe += mesafe
        otobus_yonu = yon_hesapla(lat1, lon1, lat2, lon2)
        fark = (gok_cismi_acisi - otobus_yonu) % 360

        # Güneş sağdaysa Kırmızı, soldaysa Mavi
        if 0 < fark < 180:
            sag_mesafe += mesafe
            renk = "#ef4444"
        else:
            sol_mesafe += mesafe
            renk = "#3b82f6"

        renkli_rota_segmentleri.append({
            "koordinatlar": [(lat1, lon1), (lat2, lon2)],
            "renk": renk
        })

    if toplam_mesafe == 0: toplam_mesafe = 1
    sag_oran = (sag_mesafe / toplam_mesafe) * 100
    sol_oran = (sol_mesafe / toplam_mesafe) * 100

    return sag_oran, sol_oran, toplam_mesafe, gunes_yuksekligi, renkli_rota_segmentleri


# ==========================================
# 2. GERÇEKÇİ 3D ANİMASYON MOTORU
# ==========================================
def uc_boyutlu_motor(sag, sol, yukseklik, mesaj_ek=""):
    is_night = yukseklik < 0
    y_pos = max(3.0, 25.0 * math.sin(math.radians(max(1.0, abs(yukseklik)))))
    x_pos = ((sag - sol) / 100.0) * 15.0

    if is_night:
        sky_color, light_color, ambient_intensity, dir_intensity, cisim = "#0B0C10", "#e2e8f0", "0.15", "0.5", "🌙 Ay"
    elif abs(yukseklik) < 15:
        sky_color, light_color, ambient_intensity, dir_intensity, cisim = "#fdba74", "#f97316", "0.3", "0.8", "🌅 Güneş"
    else:
        sky_color, light_color, ambient_intensity, dir_intensity, cisim = "#87CEEB", "#FDFBD3", "0.5", "1.2", "☀️ Güneş"

    mesaj = f"{cisim} SAĞDAN Vuruyor 👉 SOLA OTUR! (%{sag:.0f} Sağ)" if sag > sol else f"{cisim} SOLDAN Vuruyor 👉 SAĞA OTUR! (%{sol:.0f} Sol)"
    if mesaj_ek: mesaj += f" | {mesaj_ek}"

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://aframe.io/releases/1.4.0/aframe.min.js"></script>
        <script src="https://unpkg.com/aframe-orbit-controls@1.3.0/dist/aframe-orbit-controls.min.js"></script>
        <style>body {{ margin: 0; border-radius: 15px; overflow: hidden; }} .panel {{ position: absolute; top: 15px; left: 50%; transform: translateX(-50%); background: rgba(255,255,255,0.95); padding: 12px 24px; border-radius: 25px; font-family: sans-serif; font-weight: bold; z-index: 10; box-shadow: 0 4px 10px rgba(0,0,0,0.3); text-align: center; color: #111; font-size: 14px;}}</style>
    </head>
    <body>
        <div class="panel">{mesaj}</div>
        <a-scene embedded shadow="type: pcfsoft" style="height: 450px; width: 100%;" vr-mode-ui="enabled: false">
            <a-sky color="{sky_color}"></a-sky>
            <a-entity light="type: ambient; color: #fff; intensity: {ambient_intensity}"></a-entity>
            <a-entity light="type: directional; castShadow: true; color: {light_color}; intensity: {dir_intensity}; shadowMapHeight: 2048; shadowMapWidth: 2048;" position="{x_pos} {y_pos} 5"></a-entity>
            <a-sphere position="{x_pos} {y_pos + 2} -10" radius="1.8" color="{light_color}" material="emissive: {light_color}; emissiveIntensity: 1"></a-sphere>
            <a-entity position="0 0.8 -2" animation="property: position; to: 0 0.85 -2; dir: alternate; dur: 350; loop: true; easing: easeInOutSine">
                <a-box position="0 0.7 0" width="1.8" height="1.6" depth="4.5" color="#1d4ed8" shadow="cast: true; receive: true"></a-box>
                <a-box position="0 0.3 0" width="1.82" height="0.1" depth="4.52" color="#fbbf24"></a-box>
                <a-box position="0 1.05 0" width="1.85" height="0.6" depth="4.3" color="#bae6fd" material="opacity: 0.8"></a-box>
                <a-cylinder position="-0.9 -0.2 1.2" radius="0.35" height="0.25" rotation="0 0 90" color="#111" shadow="cast: true"></a-cylinder>
                <a-cylinder position="0.9 -0.2 1.2" radius="0.35" height="0.25" rotation="0 0 90" color="#111" shadow="cast: true"></a-cylinder>
                <a-cylinder position="-0.9 -0.2 -1.2" radius="0.35" height="0.25" rotation="0 0 90" color="#111" shadow="cast: true"></a-cylinder>
                <a-cylinder position="0.9 -0.2 -1.2" radius="0.35" height="0.25" rotation="0 0 90" color="#111" shadow="cast: true"></a-cylinder>
            </a-entity>
            <a-plane position="0 0 -10" rotation="-90 0 0" width="20" height="60" color="#334155" shadow="receive: true"></a-plane>
            <a-entity animation="property: position; from: 0 0 -10; to: 0 0 0; dur: 800; loop: true; easing: linear">
                <a-plane position="0 0.02 0" rotation="-90 0 0" width="0.2" height="5" color="#fff"></a-plane>
            </a-entity>
            <a-entity camera look-controls orbit-controls="target: 0 0.8 -2; minDistance: 3; maxDistance: 12; initialPosition: -6 4 6"></a-entity>
        </a-scene>
    </body>
    </html>
    """
    components.html(html_code, height=470)


# ==========================================
# 3. KULLANICI ARAYÜZÜ (UI) VE ISI HARİTASI
# ==========================================
st.set_page_config(page_title="Güneşli Koltuk", page_icon="🚌", layout="wide")

if 'sonuc_goster' not in st.session_state: st.session_state.sonuc_goster = False
if 'sag_oran' not in st.session_state: st.session_state.sag_oran = 0
if 'sol_oran' not in st.session_state: st.session_state.sol_oran = 0
if 'mesafe_km' not in st.session_state: st.session_state.mesafe_km = 0
if 'yukseklik' not in st.session_state: st.session_state.yukseklik = 0
if 'zaman_etiketi' not in st.session_state: st.session_state.zaman_etiketi = ""
if 'renkli_segmentler' not in st.session_state: st.session_state.renkli_segmentler = []

with st.sidebar:
    st.markdown("## ⏳ Zaman Makinesi")
    zaman_modu = st.radio("Hesaplama Zamanı:", ["🕒 Şu Anki Zaman", "📅 Farklı Bir Zaman Planla"])
    hesaplanacak_zaman = datetime.datetime.now(datetime.timezone.utc)
    zaman_etiketi = "Şu anki zamana göre hesaplandı"

    if zaman_modu == "📅 Farklı Bir Zaman Planla":
        st.markdown("---")
        trip_date = st.date_input("Yolculuk Tarihi:", datetime.date.today())
        trip_time = st.time_input("Tahmini Saat:", datetime.time(8, 30))
        naive_datetime = datetime.datetime.combine(trip_date, trip_time)
        trip_utc_time = naive_datetime - datetime.timedelta(hours=3)
        hesaplanacak_zaman = trip_utc_time.replace(tzinfo=datetime.timezone.utc)
        zaman_etiketi = f"{trip_date.strftime('%d.%m.%Y')} - {trip_time.strftime('%H:%M')} Tahmini"
        if st.button("🔍 Bu Saate Göre Ara", use_container_width=True):
            st.session_state.tetikleyici = "sidebar_ara"

    st.markdown("---")
    st.markdown("### 🗺️ Harita Lejantı")
    st.markdown("🔴 **Kırmızı Yollar:** Güneş otobüsün **SAĞINDAN** vurur.")
    st.markdown("🔵 **Mavi Yollar:** Güneş otobüsün **SOLUNDAN** vurur.")

st.title("🚌 Güneşli Koltuk: SAKUS")

tum_hatlar = list(sakus_veritabanı.keys())

if not tum_hatlar:
    st.error("Veritabanı bulunamadı!")
else:
    col1, col2 = st.columns([1, 2])

    with col1:
        secilen_hat = st.selectbox("🚍 Otobüs Hattını Seçin:", tum_hatlar)
        hat_verisi = sakus_veritabanı[secilen_hat]
        duraklar = hat_verisi["duraklar"]
        tam_coğrafi_rota = hat_verisi.get("coğrafi_akış_geometrisi", [])
        durak_isimleri_numarali = [d[0] for d in duraklar]
        hat_kisa = secilen_hat.split(' (')[0] if ' (' in secilen_hat else secilen_hat
        yon = st.radio("Güzergahınız (Hızlı Tavsiye):", [f"{hat_kisa} (Gidiş)", f"{hat_kisa} (Dönüş)"])

        if st.button("Koltuk Bul 🚀", use_container_width=True) or st.session_state.get("tetikleyici") == "sidebar_ara":
            with st.spinner(f"Analiz yapılıyor... ({zaman_etiketi})"):
                if tam_coğrafi_rota:
                    orta_coor = len(tam_coğrafi_rota) // 2
                    secilen_coğrafi_rota = tam_coğrafi_rota[:orta_coor] if "Gidiş" in yon else tam_coğrafi_rota[
                        orta_coor:]
                else:
                    orta = len(duraklar) // 2
                    secilen_coğrafi_rota = [d[1] for d in duraklar[:orta]] if "Gidiş" in yon else [d[1] for d in
                                                                                                   duraklar[orta:]]

                if len(secilen_coğrafi_rota) > 1:
                    sag, sol, mesafe, yukseklik, segmentler = gunesi_hesapla_compass(secilen_coğrafi_rota,
                                                                                     hesaplanacak_zaman)
                    st.session_state.sonuc_goster = True
                    st.session_state.sag_oran, st.session_state.sol_oran = sag, sol
                    st.session_state.mesafe_km = mesafe / 1000
                    st.session_state.yukseklik = yukseklik
                    st.session_state.zaman_etiketi = zaman_etiketi
                    st.session_state.renkli_segmentler = segmentler
            if st.session_state.get("tetikleyici") == "sidebar_ara": st.session_state.tetikleyici = ""

        st.markdown("---")
        st.markdown("### 📍 Detaylı Ara Durak Seçimi")
        binis = st.selectbox("Biniş Durağı:", durak_isimleri_numarali)
        inis = st.selectbox("İniş Durağı:", durak_isimleri_numarali, index=len(durak_isimleri_numarali) - 1)

        if st.button("Detaylı Koltuk Bul 🔍", use_container_width=True):
            b_idx, i_idx = durak_isimleri_numarali.index(binis), durak_isimleri_numarali.index(inis)
            if b_idx >= i_idx:
                st.error("Lütfen gidiş yönündeki ilerideki durakları seçin.")
            else:
                with st.spinner("Seçili duraklar hesaplanıyor..."):
                    secilen_hassas_rota = [d[1] for d in duraklar[b_idx:i_idx + 1]]
                    sag, sol, mesafe, yukseklik, segmentler = gunesi_hesapla_compass(secilen_hassas_rota,
                                                                                     hesaplanacak_zaman)
                    st.session_state.sonuc_goster, st.session_state.sag_oran, st.session_state.sol_oran = True, sag, sol
                    st.session_state.mesafe_km, st.session_state.yukseklik, st.session_state.zaman_etiketi = mesafe / 1000, yukseklik, zaman_etiketi
                    st.session_state.renkli_segmentler = segmentler

    with col2:
        if st.session_state.sonuc_goster:
            uc_boyutlu_motor(st.session_state.sag_oran, st.session_state.sol_oran, st.session_state.yukseklik,
                             f"{st.session_state.zaman_etiketi}")

        with st.expander("🗺️ Güneş Analiz Haritası (Isı Haritası)",
                         expanded=True if not st.session_state.sonuc_goster else False):
            if len(duraklar) > 0:
                merkez_lat = sum(d[1][0] for d in duraklar) / len(duraklar)
                merkez_lon = sum(d[1][1] for d in duraklar) / len(duraklar)
                m = folium.Map(location=[merkez_lat, merkez_lon], zoom_start=13)
                plugins.LocateControl(position="topleft").add_to(m)

                if st.session_state.sonuc_goster and st.session_state.renkli_segmentler:
                    for segment in st.session_state.renkli_segmentler:
                        folium.PolyLine(
                            segment["koordinatlar"],
                            color=segment["renk"],
                            weight=5,
                            opacity=0.9
                        ).add_to(m)
                elif tam_coğrafi_rota:
                    folium.PolyLine(tam_coğrafi_rota, color="gray", weight=3, opacity=0.5).add_to(m)

                # İkonlar Eski Haline Döndü! Kocaman Mavi Otobüs İkonları.
                for i, durak in enumerate(duraklar):
                    folium.Marker(
                        location=[durak[1][0], durak[1][1]],
                        tooltip=f"{i + 1}. {durak[0]}",
                        icon=folium.Icon(color="blue", icon="bus", prefix="fa")
                    ).add_to(m)

                st_folium(m, height=450, width="100%")