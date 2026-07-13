# KOS — Prototipe minggu 1

Prototipe Knowledge Operating System: input resep + tanya jawab AI (RAG),
dibatasi hanya menjawab dari data yang sudah diinput sendiri.

## Struktur folder

```
kos-mvp/
├── app.py                          # UI Streamlit (tab input + tab chat)
├── db.py                           # Koneksi Supabase, simpan & cari resep
├── ai.py                           # Koneksi Gemini, bikin embedding & jawaban
├── schema.sql                      # Skema tabel + fungsi pencarian vector
├── requirements.txt                # Daftar library Python
├── .gitignore                      # Supaya secrets tidak ke-commit
├── .streamlit/
│   └── secrets.toml.example        # Contoh format secrets (bukan yang asli)
├── .devcontainer/
│   └── devcontainer.json           # Konfigurasi GitHub Codespaces
└── .github/workflows/
    └── sanity-check.yml            # Cek otomatis: kode bisa di-parse tanpa error
```

## Setup sekali di awal

1. **Supabase**: buat project baru di supabase.com, lalu buka SQL Editor
   dan jalankan isi `schema.sql`.
2. **Secrets lokal**: salin `.streamlit/secrets.toml.example` menjadi
   `.streamlit/secrets.toml`, isi dengan URL/key Supabase dan API key Gemini
   milikmu. File ini sudah otomatis diabaikan git (lihat `.gitignore`).
3. **Streamlit Community Cloud**: saat deploy, isi ulang tiga secrets yang
   sama di menu *App settings → Secrets* (tidak otomatis kebawa dari lokal).

## Menjalankan di Codespaces

Buka repo ini via tombol *Code → Codespaces → Create codespace*.
Environment otomatis ter-setup dari `.devcontainer/devcontainer.json`.
Setelah itu jalankan:

```
streamlit run app.py
```

## Alur branch

- `main` — versi stabil yang di-connect ke Streamlit Cloud
- `dev` — tempat kerja harian, merge ke `main` setelah dites jalan
