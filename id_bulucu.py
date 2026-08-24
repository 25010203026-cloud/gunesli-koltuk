import requests
import json
import urllib3
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://sakus.sakarya.bel.tr/"
}

print("🔎 SAKUS Gizli ID Radarı Başlatıldı (7 MB'lık ana veriye dokunulmuyor)...")
id_haritasi = {}

for i in range(1, 150):
    url = f"https://sbbpublicapi.sakarya.bel.tr/api/v1/Ulasim/route-and-busstops/{i}"
    try:
        cevap = requests.get(url, headers=headers, verify=False, timeout=5)
        if cevap.status_code == 200:
            veri = cevap.json()
            if "lineNumber" in veri:
                hat_kodu = veri["lineNumber"]
                id_haritasi[hat_kodu] = i
                print(f"✅ {hat_kodu} hattının gizli ID'si bulundu: {i}")
    except:
        pass
    time.sleep(0.05)

with open("id_haritasi.json", "w", encoding="utf-8") as f:
    json.dump(id_haritasi, f, indent=4)
print("\n🚀 İŞLEM TAMAM! id_haritasi.json başarıyla oluşturuldu!")