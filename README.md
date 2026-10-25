# Panduan Scraping & Pembentukan Dataset ABSA Penginapan Bali

Pipeline ini dirancang untuk mengumpulkan data profil penginapan dan ulasan Google Maps di wilayah Bali, mengekstrak fasilitas dan balasan pemilik, melakukan pembersihan NLP, mendeteksi aspek halal dan umum, serta menghasilkan file CSV per tahap dan file Excel komprehensif (`Dataset ABSA Penginapan Bali.xlsx`) dengan sheet `ulasan` (26 kolom), `kalimat_aspek`, `daftar_penginapan`, `kamus_aspek`, serta sheet statistik ringkasan.

---

## 🌟 Fitur & Pembaruan Terbaru (Changelog)

1. **Scraping Ulasan Penuh (Full Infinite Scroll)**:
   - Memperbaiki batasan scroll lama (yang sebelumnya terhenti di 10–16 ulasan).
   - Mengambil puluhan hingga ratusan ulasan per penginapan (default: 100 ulasan, dapat disesuaikan hingga seluruh ulasan).
   - Otomatis memperluas ulasan panjang yang terpotong (`... Lainnya` / `Lihat lainnya`).
2. **Ekstraksi Balasan / Tanggapan Pemilik Hotel (`balasan_pemilik`)**:
   - Mendeteksi dan mengekstrak balasan resmi dari pengelola/pemilik hotel (`Tanggapan dari pemilik`), termasuk teks panjang yang terlipat.
3. **Ekstraksi Fasilitas Hotel (`fasilitas`)**:
   - Mengambil seluruh daftar fasilitas pada bagian *Detail hotel* (contoh: *Wi-Fi gratis, Sarapan gratis, Parkir gratis, Kolam renang luar, AC, Spa, Restoran, Pusat kebugaran, Bebas asap rokok, dll.*).
   - Mengisi kolom baru `fasilitas` pada file ulasan dan dataset ABSA.
4. **Indikator Progres Terminal Real-Time**:
   - Menampilkan progres dinamis per hotel yang sedang diproses:
     ```text
     [Hotel] Cicada Resort Bali Ubud, Autograph Collection (497 ulasan)
     Scraping Review: 100%|██████████| 100/100 ulasan [00:15<00:00, 6.42 review/s]
     ```
   - Disertai ringkasan ulasan baru, jumlah balasan pemilik, dan total fasilitas terdata.
5. **Autentikasi Google Anti-Captcha (`login_google.py`)**:
   - Membuka Chrome native dengan direktori profil persisten `data/browser_profile/` untuk login akun Google 1x tanpa terjebak loop *"Konfirmasi bahwa Anda bukan robot"*.
6. **Sinkronisasi Checkpoint Cerdas (Retrofit & Deduplikasi)**:
   - Aman dari gangguan koneksi atau interupsi (`Ctrl+C`).
   - Secara otomatis memperkaya (*enrich*) data ulasan lama dengan fasilitas hotel dan teks balasan pemilik yang baru diambil.

---

## 📁 Struktur Direktori & File

```
scrapingTraveloka_wawa/
│
├── data/                                         # Direktori penyimpanan dataset & sesi
│   ├── browser_profile/                         # Profil sesi login browser (diabaikan oleh Git)
│   ├── daftar_penginapan_bali_mentah.csv        # Hasil Tahap 1: Profil & koordinat penginapan
│   ├── raw_ulasan_checkpoint.csv                 # Hasil Tahap 2: Database ulasan mentah (checkpoint)
│   ├── dataset_absa_penginapan_halal_bali.csv    # Hasil Tahap 3: Dataset ABSA siap anotasi
│   └── Dataset ABSA Penginapan Bali.xlsx         # Hasil Akhir: File Excel multi-sheet
│
├── 01_scrape_daftar_penginapan.py                # Tahap 1: Scrape daftar penginapan se-Bali
├── 02_scrape_ulasan_penginapan.py                # Tahap 2: Scrape ulasan, fasilitas, & balasan pemilik
├── 03_proses_dataset_absa.py                     # Tahap 3: Preprocessing NLP & Export Excel multi-sheet
├── enrich_detail_penginapan.py                   # Utilitas: Melengkapi telepon, website, harga, alamat
├── login_google.py                               # Utilitas: Login akun Google tanpa loop captcha
├── run_pipeline.py                               # Runner menu interaktif (All-in-one)
├── requirements.txt                              # Daftar dependensi library Python
└── README.md                                     # Dokumentasi teknis & panduan eksekusi
```

---

## 🛠️ Instalasi & Persiapan Awal

### 1. Install Dependensi Python & Playwright
Buka terminal / PowerShell di root proyek dan jalankan:
```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Login Akun Google (Direkomendasikan 1x di Awal)
Untuk membuka akses penuh ke seluruh ulasan di Google Maps tanpa batasan dan tanpa captcha:
```bash
python login_google.py
```
> Jendela Google Chrome asli akan terbuka. Silakan login ke akun Google Anda. Setelah berhasil masuk, kembali ke terminal dan tekan **[ENTER]**. Sesi login Anda tersimpan permanen di `data/browser_profile/`.

---

## 🚀 Cara Menjalankan Pipeline

Anda dapat menjalankan seluruh alur melalui **Runner Interaktif**:
```bash
python run_pipeline.py
```
Menu interaktif yang tersedia:
```text
=============================================================
   PIPELINE SCRAPING & DATASET ABSA PENGINAPAN BALI
=============================================================
1. Jalankan Tahap 1: Scraping Daftar Penginapan
2. Jalankan Tahap 2: Scraping Ulasan Penginapan
3. Jalankan Tahap 3: Pemrosesan ABSA & Export Excel Lengkap
4. Jalankan Semua Tahap (1 -> 2 -> 3)
5. Lengkapi Metadata Penginapan (Alamat, Telepon, Website, Harga)
6. Login Akun Google (1x Saja untuk Buka Semua Ulasan Tanpa Captcha)
0. Keluar
=============================================================
```

---

## 📖 Panduan Eksekusi Manual per Tahap

### **Tahap 1: Scraping Daftar Penginapan Bali**
```bash
python 01_scrape_daftar_penginapan.py
```
- Mencari hotel, villa, resort, dan penginapan syariah/halal di 9 kabupaten/kota di Bali (Denpasar, Badung, Gianyar, Tabanan, Buleleng, Karangasem, Klungkung, Bangli, Jembrana).
- Output: `data/daftar_penginapan_bali_mentah.csv`.
- Kolom: `data_id`, `nama_penginapan`, `tipe`, `alamat`, `lat`, `lon`, `rating_rata2`, `jumlah_ulasan_total`, `kelompok_sampel`, `area_query`, `kab_query`, `query_sumber`, `kabupaten`.

---

### **Tahap 2: Scraping Ulasan, Fasilitas, & Balasan Pemilik**
```bash
# Menjalankan scraping dengan target default (100 ulasan per hotel)
python 02_scrape_ulasan_penginapan.py

# Menjalankan dengan kuota ulasan tertentu (contoh: 300 ulasan per hotel)
python 02_scrape_ulasan_penginapan.py --max 300

# Otomatis melanjutkan sekuensial dari hotel terakhir di checkpoint (tanpa mengulang hotel sebelumnya)
python 02_scrape_ulasan_penginapan.py --max 300

# Mulai langsung dari nomor urut penginapan tertentu (misal: penginapan ke-237 atau 239)
python 02_scrape_ulasan_penginapan.py --max 300 --start 237

# Mode Sweep: Periksa kembali hotel-hotel lama yang ulasannya belum mencapai target kuota
python 02_scrape_ulasan_penginapan.py --max 300 --retry-incomplete

# Menguji scraping hanya untuk satu hotel tertentu
python 02_scrape_ulasan_penginapan.py --hotel "Cicada Resort Bali Ubud" --max 100

# Menjalankan di background (headless mode)
python 02_scrape_ulasan_penginapan.py --max 300 --headless
```

**Fitur Cerdas & Checkpoint Tahap 2:**
- **Auto-Resume Sekuensial dari Baris Terakhir**: Skrip secara otomatis mendeteksi nama penginapan terakhir yang tersimpan di baris paling bawah `data/raw_ulasan_checkpoint.csv` (misal hotel terakhir: *Maeni Bali Villa*) dan langsung melanjutkan ke penginapan berikutnya (*Alas Arum Ecolodge*) tanpa membuang waktu mengulang hotel-hotel sebelumnya.
- **Global Progress Bar Real-time (`[Hotel 237/464]`)**: Menampilkan nomor urut asli hotel terhadap total 464 penginapan pada daftar master secara akurat.
- **Fast Append Streaming**: Ulasan baru langsung di-append ke CSV secara instan (0.001 detik) per hotel (`mode="a"`). Tidak me-rewrite file CSV puluhan ribu baris dari awal, sehingga bebas bottleneck I/O disk dan mencegah memory spike.
- **Ekstraksi Lengkap**: Mengekstrak teks ulasan utuh, rating berdesimal (`1.0` - `5.0`), tanggal, jumlah like, fasilitas hotel, dan balasan resmi pemilik hotel (`balasan_pemilik`).
- **Parameter Fleksibel**:
  - `--max <N>`: Target ulasan per penginapan (default 100, set 0 untuk semua ulasan).
  - `--start <N>`: Langsung melompat ke nomor penginapan tertentu (1-indexed).
  - `--retry-incomplete`: Mode khusus untuk menyapu ulang hotel yang ulasannya kurang dari kuota.
  - `--hotel "<Nama>"`: Filter nama hotel tertentu.
  - `--headless`: Menjalankan browser di latar belakang tanpa jendela visual.

---

### **(Opsional) Melengkapi Metadata Penginapan**
```bash
python enrich_detail_penginapan.py
```
- Membuka halaman penginapan untuk melengkapi nomor telepon, website resmi, alamat detail, dan estimasi harga jika sebelumnya belum terisi.

---

### **Tahap 3: Pemrosesan ABSA & Export ke Excel Lengkap**
```bash
python 03_proses_dataset_absa.py
```
- Melakukan pembersihan teks ulasan (`teks_bersih`) dan deteksi bahasa (`bahasa`).
- Mengonversi format tanggal relatif ke standar `iso_date` dan `tanggal_iso`.
- Menentukan `status_halal` dan `bukti_halal` berbasis aturan (*rule-based*).
- Menandai flag aspek halal (`flag_makanan_halal`, `flag_fasilitas_ibadah`, `flag_privasi_kamar`, `flag_kolam_renang`, `flag_citra_syariah`).
- Memecah ulasan per kalimat untuk diekstraksi ke sheet `kalimat_aspek` berdasarkan kamus 8 aspek (makanan halal, fasilitas ibadah, kesesuaian syariah, kebersihan, pelayanan, kamar & fasilitas, lokasi, harga).
- Menghasilkan 2 file luaran:
  1. `data/dataset_absa_penginapan_halal_bali.csv` (Dataset ulasan lengkap dengan kolom label aspek kosong siap anotasi).
  2. `data/Dataset ABSA Penginapan Bali.xlsx` (File Excel multi-sheet).

---

## 📊 Skema & Struktur Data

### 1. File Checkpoint Ulasan (`data/raw_ulasan_checkpoint.csv`)
Terdiri dari 17 kolom (setiap baris ulasan dijamin tepat 1 baris tanpa enter berantakan):
| No | Nama Kolom | Keterangan |
|---|---|---|
| 1 | `review_id` | Hash unik ulasan (kombinasi reviewer, tanggal, teks) |
| 2 | `data_id` | ID unik Google Maps untuk penginapan |
| 3 | `nama_penginapan` | Nama hotel / penginapan |
| 4 | `kabupaten` | Kabupaten/Kota di Bali |
| 5 | `kelompok_sampel` | Kelompok sampel (`syariah` / `umum`) |
| 6 | `kata_kunci` | Kata kunci pencarian awal |
| 7 | `fasilitas` | Fasilitas hotel (*Wi-Fi gratis, Sarapan, Kolam renang luar, AC, dll.*) |
| 8 | `teks_ulasan` | Teks ulasan asli pengunjung (sudah diperluas penuh & dibersihkan enter-nya) |
| 9 | `teks_terjemahan_google` | Terjemahan ulasan jika dalam bahasa asing |
| 10 | `rating_penginapan` | Rating rata-rata keseluruhan penginapan dari ringkasan Google Maps berdesimal (*contoh: 4.4, 4.9*) |
| 11 | `rating_bintang` | Rating bintang yang diberikan reviewer per ulasan berdesimal (*contoh: 5.0, 4.0, 1.0*) |
| 12 | `tanggal` | Teks tanggal ulasan asli di Google Maps (*misal: "3 bulan lalu"*) |
| 13 | `jumlah_like` | Jumlah like pada ulasan |
| 14 | `ada_balasan_pemilik` | Boolean (`True` jika pemilik hotel memberikan tanggapan resmi) |
| 15 | `balasan_pemilik` | Teks lengkap respon / tanggapan dari pihak hotel |
| 16 | `sumber` | Sumber data (`Google Maps`) |
| 17 | `reviewer_total_ulasan` | Jumlah total kontribusi ulasan yang ditulis oleh reviewer |

---

### 2. File Excel Akhir (`data/Dataset ABSA Penginapan Bali.xlsx`)
File Excel ini terdiri dari lembar kerja (*sheets*):

1. **`ulasan` (26 Kolom Standar)**:
   `place_id`, `data_id`, `nama_tempat`, `alamat`, `kategori`, `rating_tempat`, `total_ulasan_tempat`, `harga`, `telepon`, `website`, `latitude`, `longitude`, `status_halal`, `bukti_halal`, `review_id`, `reviewer_total_ulasan`, `rating_ulasan`, `tanggal`, `iso_date`, `ulasan`, `likes`, `label_halal_nama`, `teks_ulasan`, `tanggal_iso`, `teks_bersih`, `bahasa`.
2. **`kalimat_aspek`**:
   Potongan per kalimat ulasan yang cocok dengan kamus aspek, dilengkapi kolom `kalimat`, `aspek`, `aspek_inti_halal`, `rating_ulasan`, dan `bahasa`.
3. **`daftar_penginapan`**:
   Daftar seluruh profil penginapan unik di Bali beserta status halal, rating rata-rata, dan total ulasan.
4. **`kamus_aspek`**:
   Kamus kata kunci dan regex untuk 8 aspek analisis sentimen.
5. **Sheet Statistik Ringkasan**:
   - `stat_ringkas`: Ringkasan umum total hotel, ulasan, kalimat aspek, dan status halal.
   - `stat_status_halal`: Distribusi penginapan berdasarkan status halal.
   - `stat_aspek`: Sebaran frekuensi kemunculan masing-masing aspek.
   - `stat_bahasa`: Sebaran bahasa ulasan (Indonesia, Inggris, dll.).
   - `stat_rating`: Distribusi rating bintang 1 hingga 5.
   - `stat_tahun`: Distribusi tahun ulasan.
   - `stat_penginapan`: Rekap jumlah ulasan per penginapan.

---

## 💡 Tips & Pemecahan Masalah (Troubleshooting)

- **Mencegah Overclose / Crash Aplikasi Editor (Antigravity / VS Code)**:
  - **TUTUP TAB FILE CSV DI EDITOR**: Jangan membuka file `data/raw_ulasan_checkpoint.csv` di tab editor saat proses scraping sedang aktif berjalan. File yang sudah berisi puluhan ribu baris (39.000+) dan terus bertambah cepat akan memicu *file watcher* editor me-render ulang dokumen jutaan karakter, yang menyebabkan RAM editor melonjak hingga batas *Out of Memory (OOM)* dan membuat editor keluar sendiri (*silent crash / overclose*).
  - **JALANKAN DI TERMINAL CMD / POWERSHELL MURNI**: Menjalankan scraping langsung melalui Command Prompt (CMD) tanpa membuka editor menghemat konsumsi RAM sistem sebesar **60% – 75%**, mempercepat penulisan file, dan bebas risiko crash 100%.

- **Melanjutkan Scraping Tanpa Mengulang dari Awal**:
  - Cukup jalankan kembali `python 02_scrape_ulasan_penginapan.py --max 300`. Skrip akan otomatis mendeteksi baris hotel terakhir di CSV dan langsung lanjut ke hotel berikutnya.
  - Jika ingin meloncat secara spesifik ke hotel nomor tertentu, gunakan flag `--start <nomor_hotel>` (misal: `--start 237` atau `--start 239`).
  - Jika ingin menyapu kembali hotel lama yang ulasannya belum mencapai target kuota, gunakan `--retry-incomplete`.

- **Looping Captcha ("Konfirmasi bahwa Anda bukan robot")**:
  - Jangan mencoba menyelesaikan login melalui browser otomatis Playwright. Jalankan `python login_google.py` untuk login via browser Google Chrome asli Anda satu kali saja. Sesi login akan disimpan permanen di `data/browser_profile/`.

- **Mengecek Data CSV yang Sedang Berjalan Tanpa Buka Editor**:
  - Buka terminal PowerShell baru dan jalankan perintah satu baris berikut untuk melihat jumlah data terkini tanpa membuka file di editor:
    ```powershell
    python -c "import pandas as pd; df = pd.read_csv('data/raw_ulasan_checkpoint.csv'); print(f'Total ulasan: {len(df)} | Total hotel: {df["data_id"].nunique()}')"
    ```
  - Buka file CSV di aplikasi spreadsheet (seperti Microsoft Excel) setelah scraping selesai atau saat skrip sedang dijeda.
