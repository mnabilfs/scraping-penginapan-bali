"""
TAHAP 1: Scraping Daftar Penginapan di Bali dari Google Maps
Output: data/daftar_penginapan_bali_mentah.csv
Kolom:
  - data_id
  - nama_penginapan
  - tipe
  - alamat
  - lat, lon
  - rating_rata2
  - jumlah_ulasan_total
  - kelompok_sampel ('halal' atau 'umum')
  - area_query, kab_query, query_sumber
  - kabupaten (hasil infer_kabupaten)
  - place_id, telepon, website, harga (metadata tambahan untuk sheet ulasan)
"""

import os
import re
import time
import urllib.parse
from pathlib import Path
import pandas as pd
from tqdm import tqdm
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = DATA_DIR / "daftar_penginapan_bali_mentah.csv"

# Daftar Kabupaten di Bali untuk fungsi infer_kabupaten
DAFTAR_KABUPATEN = [
    "Badung", "Bangli", "Buleleng", "Denpasar", "Gianyar",
    "Jembrana", "Karangasem", "Klungkung", "Tabanan"
]

def infer_kabupaten(alamat: str, fallback_kab: str = "") -> str:
    """Mendeteksi kabupaten di Bali berdasarkan teks alamat."""
    if not isinstance(alamat, str):
        return fallback_kab
    alamat_lower = alamat.lower()
    for kab in DAFTAR_KABUPATEN:
        if kab.lower() in alamat_lower:
            return kab
    return fallback_kab or "Bali (Lainnya)"

# Daftar Kueri Pencarian Google Maps
QUERIES = [
    # 1. Kelompok Halal / Syariah
    {"query": "hotel syariah di bali", "kelompok": "halal", "area": "Bali", "kab": "Denpasar"},
    {"query": "penginapan syariah bali", "kelompok": "halal", "area": "Bali", "kab": "Badung"},
    {"query": "hotel muslim friendly bali", "kelompok": "halal", "area": "Bali", "kab": "Badung"},
    {"query": "villa syariah bali", "kelompok": "halal", "area": "Bali", "kab": "Gianyar"},
    
    # 2. Kelompok Umum (per kabupaten untuk sebaran representatif)
    {"query": "hotel di denpasar bali", "kelompok": "umum", "area": "Denpasar", "kab": "Denpasar"},
    {"query": "hotel di kuta badung bali", "kelompok": "umum", "area": "Kuta", "kab": "Badung"},
    {"query": "hotel di seminyak badung bali", "kelompok": "umum", "area": "Seminyak", "kab": "Badung"},
    {"query": "hotel di ubud gianyar bali", "kelompok": "umum", "area": "Ubud", "kab": "Gianyar"},
    {"query": "hotel di tabanan bali", "kelompok": "umum", "area": "Tabanan", "kab": "Tabanan"},
    {"query": "hotel di singaraja buleleng bali", "kelompok": "umum", "area": "Singaraja", "kab": "Buleleng"},
    {"query": "hotel di karangasem amlapura bali", "kelompok": "umum", "area": "Amlapura", "kab": "Karangasem"},
    {"query": "hotel di klungkung nusa penida bali", "kelompok": "umum", "area": "Nusa Penida", "kab": "Klungkung"},
    {"query": "hotel di jembrana negara bali", "kelompok": "umum", "area": "Negara", "kab": "Jembrana"},
    {"query": "hotel di bangli kintamani bali", "kelompok": "umum", "area": "Kintamani", "kab": "Bangli"}
]

def parse_url_coords_and_id(url: str):
    """Mengekstrak lat, lon, dan data_id (hex CID) dari URL Google Maps."""
    lat, lon, data_id, place_id = None, None, None, None
    if not url:
        return lat, lon, data_id, place_id

    # 1. Ekstrak Lat, Lon (format !3d/!4d atau @lat,lon)
    coord_match = re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", url) or re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", url)
    if coord_match:
        lat = float(coord_match.group(1))
        lon = float(coord_match.group(2))

    # 2. Ekstrak place_id (!19sChIJ...)
    pid_match = re.search(r"!19s(ChIJ[0-9a-zA-Z_-]+)", url)
    if pid_match:
        place_id = pid_match.group(1)

    # 3. Ekstrak data_id hex (!1s0x...:0x...)
    data_id_match = re.search(r"!1s(0x[0-9a-fA-F]+:0x[0-9a-fA-F]+)", url)
    if data_id_match:
        data_id = data_id_match.group(1)
    else:
        # Fallback cari sembarang format hex 0x...:0x...
        alt_match = re.search(r"(0x[0-9a-fA-F]+:0x[0-9a-fA-F]+)", url)
        if alt_match:
            data_id = alt_match.group(1)

    return lat, lon, data_id, place_id

def scrape_daftar_penginapan(headless: bool = False, max_scroll: int = 15):
    """
    Menjalankan Playwright untuk mencari hotel dan mengumpulkan profil penginapan.
    headless=False direkomendasikan agar Anda bisa melihat proses dan menangani consent popup.
    """
    print("=" * 60)
    print("🚀 MEMULAI TAHAP 1: SCRAPING DAFTAR PENGINAPAN BALI")
    print("=" * 60)

    # Muat data yang sudah ada jika ingin resume
    existing_places = {}
    if OUTPUT_FILE.exists():
        try:
            df_old = pd.read_csv(OUTPUT_FILE)
            for _, r in df_old.iterrows():
                if pd.notnull(r.get("data_id")):
                    existing_places[r["data_id"]] = r.to_dict()
            print(f"📦 Ditemukan checkpoint lama: {len(existing_places)} penginapan.")
        except Exception as e:
            print(f"⚠️ Gagal membaca checkpoint lama ({e}), memulai dari awal.")

    with sync_playwright() as p:
        # Gunakan Chromium dengan parameter user-agent & locale Indonesia
        browser = p.chromium.launch(headless=headless, args=["--lang=id-ID,id"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="id-ID",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()

        for q_item in QUERIES:
            query = q_item["query"]
            kelompok = q_item["kelompok"]
            area = q_item["area"]
            kab = q_item["kab"]

            encoded_q = urllib.parse.quote(query)
            target_url = f"https://www.google.com/maps/search/{encoded_q}?hl=id"
            print(f"\n🔍 Menjalankan kueri: '{query}' ({kelompok})")

            try:
                page.goto(target_url, timeout=45000, wait_until="domcontentloaded")
                time.sleep(3)

                # Tangani dialog persetujuan Google jika muncul
                try:
                    btn_accept = page.locator("button:has-text('Setujui semua'), button:has-text('Terima semua'), form:has(button) button:visible").first
                    if btn_accept.is_visible(timeout=2000):
                        btn_accept.click()
                        time.sleep(2)
                except Exception:
                    pass

                # Tunggu feed container hasil pencarian
                feed_selector = "div[role='feed']"
                try:
                    page.wait_for_selector(feed_selector, timeout=10000)
                except Exception:
                    print(f"   ⚠️ Feed hasil tidak ditemukan untuk kueri ini.")
                    continue

                # Scroll feed untuk memuat lebih banyak item
                print(f"   ⏳ Melakukan scroll hasil pencarian...")
                for scroll_idx in range(max_scroll):
                    page.evaluate(
                        """(selector) => {
                            const el = document.querySelector(selector);
                            if (el) el.scrollBy(0, 1000);
                        }""",
                        feed_selector
                    )
                    time.sleep(1.5)
                    # Cek jika sudah mencapai batas akhir ("Anda telah mencapai akhir daftar")
                    if page.locator("text='Anda telah mencapai akhir daftar'").is_visible():
                        break

                # Ekstrak semua kartu tempat dari feed
                card_locator = page.locator("div[role='feed'] > div:has(a[href*='/maps/place/'])")
                total_cards = card_locator.count()
                print(f"   📋 Ditemukan {total_cards} tempat pada kueri ini.")

                for i in range(total_cards):
                    card = card_locator.nth(i)
                    try:
                        link_el = card.locator("a[href*='/maps/place/']").first
                        if not link_el.is_visible():
                            continue
                        place_url = link_el.get_attribute("href") or ""
                        
                        lat, lon, data_id, place_id = parse_url_coords_and_id(place_url)
                        if not data_id:
                            # Jika data_id tidak di URL, buat hash fallback dari URL
                            data_id = f"fallback_{hash(place_url)}"

                        if data_id in existing_places:
                            continue

                        # Ambil Nama Penginapan
                        nama = link_el.get_attribute("aria-label") or link_el.inner_text().split("\n")[0].strip()

                        # Ambil Tipe / Kategori & Rating dari kartu
                        text_content = card.inner_text()
                        lines = [l.strip() for l in text_content.split("\n") if l.strip()]

                        rating_rata2 = None
                        jumlah_ulasan_total = 0
                        tipe = "Hotel"
                        alamat = ""

                        # Regex rating & total ulasan (misal: "4,3 (1.200)" atau "4.1 (36)")
                        rating_match = re.search(r"(\d[,\.]\d)\s*\(([\d\.]+)\)", text_content)
                        if rating_match:
                            rating_rata2 = float(rating_match.group(1).replace(",", "."))
                            jumlah_ulasan_total = int(rating_match.group(2).replace(".", ""))

                        # Deteksi tipe dari baris teks
                        for line in lines:
                            for t in ["Hotel", "Hostel", "Resor", "Resort", "Villa", "Vila", "Wisma", "Homestay", "Pondok", "Guest house"]:
                                if t.lower() in line.lower() and len(line) < 35:
                                    tipe = line
                                    break

                        # Ambil perkiraan alamat dari baris
                        alamat_candidates = [l for l in lines if any(k in l.lower() for k in ["jl.", "jalan", "bali", "kec.", "kab.", "gang", "gg."])]
                        if alamat_candidates:
                            alamat = alamat_candidates[0]

                        kabupaten_hasil = infer_kabupaten(alamat, fallback_kab=kab)

                        item_data = {
                            "data_id": data_id,
                            "place_id": place_id or "",
                            "nama_penginapan": nama,
                            "tipe": tipe,
                            "alamat": alamat,
                            "lat": lat,
                            "lon": lon,
                            "rating_rata2": rating_rata2,
                            "jumlah_ulasan_total": jumlah_ulasan_total,
                            "kelompok_sampel": kelompok,
                            "area_query": area,
                            "kab_query": kab,
                            "query_sumber": query,
                            "kabupaten": kabupaten_hasil,
                            "url": place_url,
                            "harga": "",
                            "telepon": "",
                            "website": ""
                        }

                        existing_places[data_id] = item_data

                    except Exception as err:
                        continue

                # Simpan checkpoint sementara setiap kueri selesai
                df_temp = pd.DataFrame(list(existing_places.values()))
                df_temp.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
                print(f"   💾 Checkpoint tersimpan: {len(existing_places)} penginapan.")

            except Exception as e:
                print(f"   ❌ Kesalahan pada kueri '{query}': {e}")
                continue

        browser.close()

    print("\n" + "=" * 60)
    print(f"✅ TAHAP 1 SELESAI: {len(existing_places)} penginapan berhasil dikumpulkan!")
    print(f"📁 Disimpan di: {OUTPUT_FILE}")
    print("=" * 60)

if __name__ == "__main__":
    # max_scroll=15 dapat ditingkatkan (misal 30) jika ingin menarik lebih banyak hotel
    scrape_daftar_penginapan(headless=False, max_scroll=12)
