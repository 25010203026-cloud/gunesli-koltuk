# BOT.PY (Kritik Düzeltme: Step 1 Geometrisini Silmez, Pre-Save Yapar)
import requests
import time
import urllib3
import json

# SSL Uyarılarını kapatıyoruz
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Sunucuyu kandıran sihirli anahtarlar
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://sakus.sakarya.bel.tr/"
}


def coğrafi_rota_çek_detailed(duraklar):
    """
    Step 1 Fix'ten hatırla: Duraklar arasındaki en hassas
    yol geometrisini (OSRM) pre-save yapmalıyız.
    """
    if len(duraklar) < 2: return []

    rota_geometrisi = []
    for i in range(len(duraklar) - 1):
        lat1, lon1 = duraklar[i][1]
        lat2, lon2 = duraklar[i + 1][1]

        url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
        try:
            cevap = requests.get(url, timeout=5)
            if cevap.status_code == 200:
                osrm_veri = cevap.json()
                if "routes" in osrm_veri:
                    geometri_noktaları = osrm_veri["routes"][0]["geometry"]["coordinates"]
                    for nokta in geometri_noktaları:
                        rota_geometrisi.append((nokta[1], nokta[0]))  # (lat, lon)
        except:
            pass  # OSRM hata verirse atla

    return rota_geometrisi


print("🕷️ SAKUS Yüksek Kapasiteli Örümcek Botu Başlatılıyor...")

bulunan_hat_sayisi = 0
sakus_veritabanı = {}

for i in range(1, 150):
    url = f"https://sbbpublicapi.sakarya.bel.tr/api/v1/Ulasim/route-and-busstops/{i}"
    try:
        cevap = requests.get(url, headers=headers, verify=False, timeout=10)

        if cevap.status_code == 200 and cevap.text.strip():
            veri = cevap.json()

            if isinstance(veri, dict) and "lineNumber" in veri:
                hat_kodu = veri["lineNumber"]
                hat_adi = veri["lineName"].strip()

                if "routes" in veri and len(veri["routes"]) > 0:
                    api_durakları = veri["routes"][0].get("busStops", [])

                    if len(api_durakları) > 0:
                        bulunan_hat_sayisi += 1
                        print(
                            f"🔄 ID {i}: {hat_kodu} ({len(api_durakları)} durak) çekiliyor. Detaylı coğrafi akış kaydediliyor...")

                        temiz_duraklar = []
                        for i_dur, durak in enumerate(api_durakları):
                            durak_adi = f"{i_dur + 1} - {durak['name'].replace('\"', '\'')}"
                            lon = durak["busStopGeometry"]["coordinates"][0]
                            lat = durak["busStopGeometry"]["coordinates"][1]
                            temiz_duraklar.append((durak_adi, (lat, lon)))

                        # Step 1 Fix'ten hatırla: Detaylı Geometriyi çekip pre-save yap
                        coğrafi_akış_geometrisi = coğrafi_rota_çek_detailed(temiz_duraklar)

                        # KRİTİK VERİ KORUMA: Durakları silmiyoruz!
                        # Hem durakları hem de hassas akışı kaydediyoruz.
                        sakus_veritabanı[f"{hat_kodu} ({hat_adi})"] = {
                            "duraklar": temiz_duraklar,
                            "coğrafi_akış_geometrisi": coğrafi_akış_geometrisi
                        }
    except Exception as e:
        pass

    time.sleep(0.05)  # Çok hızlı istek atıyoruz ki belediye ban atmasın

with open("hat_verileri.json", "w", encoding="utf-8") as dosya:
    json.dump(sakus_veritabanı, dosya, ensure_ascii=False, indent=4)

print(
    f"\n🎉 İŞLEM TAMAM! Toplam {bulunan_hat_sayisi} farklı otobüs hattının durak listeleri VE detaylı coğrafi akış geometrileri hat_verileri.json dosyasına yazıldı! (403/401 Reddedildi hataları sessizce atlandı) 🚀")