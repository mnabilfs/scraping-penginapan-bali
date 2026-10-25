"""
Enricher Metadata Penginapan Google Maps:
Mengisi kolom `alamat`, `telepon`, `website`, dan `harga` yang masih kosong di `data/daftar_penginapan_bali_mentah.csv`.
"""

import re
import time
from pathlib import Path
import pandas as pd
from tqdm import tqdm
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
HOTEL_FILE = DATA_DIR / "daftar_penginapan_bali_mentah.csv"

def clean_icon_text(txt: str) -> str:
    """Membersihkan karakter ikon font Google Maps."""
    if not txt:
        return ""
    # Hapus karakter private use area Unicode (ikon Material)
    cleaned = re.sub(r"[\ue000-\uf8ff]", "", txt).strip()
    return cleaned

def enrich_hotels(headless: bool = True):
    if not HOTEL_FILE.exists():
        print(f"File {HOTEL_FILE} tidak ditemukan!")
        return

    df = pd.read_csv(HOTEL_FILE)
    print(f"📋 Total penginapan: {len(df)}")

    # Cari baris yang telepon atau websitenya masih kosong
    mask_empty = df["telepon"].isnull() | (df["telepon"] == "") | df["website"].isnull() | (df["website"] == "")
    hotels_to_enrich = df[mask_empty].copy()
    print(f"🎯 Penginapan yang perlu dilengkapi (telepon/web): {len(hotels_to_enrich)}")

    if len(hotels_to_enrich) == 0:
        print("🎉 Semua detail penginapan sudah lengkap 100%!")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, args=["--lang=id-ID,id"])
        page = browser.new_page()

        # Blokir gambar untuk loading cepat
        page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "media", "font"] else route.continue_())

        count = 0
        for idx, row in tqdm(hotels_to_enrich.iterrows(), total=len(hotels_to_enrich), desc="Melengkapi Detail Hotel"):
            url = row.get("url", "")
            if not url or pd.isnull(url):
                continue

            try:
                page.goto(url, timeout=20000, wait_until="domcontentloaded")
                time.sleep(1.0)

                details = page.evaluate("""() => {
                    const addrEl = document.querySelector('button[data-item-id="address"]');
                    const phoneEl = document.querySelector('button[data-item-id*="phone"]');
                    const webEl = document.querySelector('a[data-item-id="authority"]');
                    const priceEl = document.querySelector('span[aria-label*="per malam"], div.drwW4b, span.fontTitleLarge, div[aria-label*="IDR"], div[aria-label*="Rp"]');
                    return {
                        alamat: addrEl ? addrEl.innerText.trim() : '',
                        telepon: phoneEl ? phoneEl.innerText.trim() : '',
                        website: webEl ? webEl.getAttribute('href') : '',
                        harga: priceEl ? priceEl.innerText.trim() : ''
                    };
                }""")

                # Update jika ditemukan
                if details["alamat"] and (pd.isnull(df.at[idx, "alamat"]) or df.at[idx, "alamat"] == ""):
                    df.at[idx, "alamat"] = clean_icon_text(details["alamat"])
                if details["telepon"] and (pd.isnull(df.at[idx, "telepon"]) or df.at[idx, "telepon"] == ""):
                    df.at[idx, "telepon"] = clean_icon_text(details["telepon"])
                if details["website"] and (pd.isnull(df.at[idx, "website"]) or df.at[idx, "website"] == ""):
                    df.at[idx, "website"] = details["website"]
                if details["harga"] and (pd.isnull(df.at[idx, "harga"]) or df.at[idx, "harga"] == ""):
                    df.at[idx, "harga"] = clean_icon_text(details["harga"])

                count += 1
                # Simpan berkala setiap 10 hotel
                if count % 10 == 0:
                    df.to_csv(HOTEL_FILE, index=False, encoding="utf-8")

            except Exception:
                continue

        browser.close()

    df.to_csv(HOTEL_FILE, index=False, encoding="utf-8")
    print("\n" + "=" * 60)
    print("✅ Berhasil melengkapi metadata penginapan!")
    print(f"📁 Disimpan di: {HOTEL_FILE}")
    print("=" * 60)

if __name__ == "__main__":
    enrich_hotels(headless=True)
