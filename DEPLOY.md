# Deploy: Vercel (frontend) + Railway (backend)

Arsitektur baru: **Next.js di Vercel** (murni frontend, tanpa Python function
lagi) dan **FastAPI di Railway** (backend, karena butuh proses lama untuk
upload/OCR/embedding yang kena limit 10 detik di Vercel serverless
function). Database tetap Supabase (Postgres terkelola) -- tidak pindah.

## 1. Backend -- Railway

1. Buat project baru di Railway, pilih "Deploy from GitHub repo", pilih repo ini.
2. Railway otomatis pakai `railway.json` + `Dockerfile.api` di root repo (builder Docker, bukan Nixpacks) -- jangan ubah root directory, biarkan default (root repo), karena `api/index.py` butuh diimpor sebagai package `api`.
3. Set environment variables di tab **Variables**:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `GEMINI_API_KEY`
   - `ALLOWED_ORIGINS` -- isi domain Vercel produksi (boleh lebih dari satu, pisah koma). Bisa diisi belakangan setelah tahu domain Vercel final, tapi isi secepatnya -- kalau kosong, CORS fallback ke `*` (longgar, cuma buat sementara).
4. Deploy. Setelah jalan, catat domain publiknya, contoh: `https://kos-backend-production.up.railway.app`.
5. Cek health: buka `https://<domain-railway>/docs` -- harus muncul Swagger UI FastAPI.

## 2. Frontend -- Vercel

1. Import repo yang sama ke Vercel, framework otomatis kedetek Next.js.
2. Set environment variable di **Project Settings > Environment Variables**:
   - `NEXT_PUBLIC_API_URL` = domain Railway dari langkah di atas (**tanpa** trailing slash), mis. `https://kos-backend-production.up.railway.app`
3. Deploy. `vercel.json` sekarang cuma bilang `{"framework": "nextjs"}` -- tidak ada lagi rewrite ke `api/index.py`.
4. Setelah tahu domain Vercel final, balik ke Railway dan lengkapi `ALLOWED_ORIGINS` dengan domain ini, lalu redeploy backend supaya CORS ketat (bukan `*` lagi).

## 3. Lokal (dev)

Tidak berubah -- tetap jalankan FastAPI lokal (`uvicorn api.index:app --reload` dari root repo) di `:8000`, dan `npm run dev` untuk Next.js. `lib/api.ts` otomatis pakai `http://localhost:8000` saat hostname `localhost`.

## 4. Migrasi database (Scope C -- form dinamis, notifikasi, broadcast)

Sebelum deploy kode baru ini, jalankan `api/migration_scope_c.sql` di
Supabase SQL Editor (aman dijalankan ulang, semua pakai `IF NOT EXISTS`).
Isinya: tabel form builder (`form_templates`, `form_fields`,
`form_submissions`, `form_submission_answers`), notifikasi
(`notifications`), poin pelanggaran -- skema saja, belum aktif di UI
(`violation_points`), dan broadcast pengumuman (`announcements`).

## 4b. Migrasi database (Scope D -- Form Lapor Kerjaan, beda dari Kehadiran)

Jalankan juga `api/migration_scope_d.sql` -- tabel `work_reports` +
`work_report_rows` untuk laporan kerjaan detail dengan baris dinamis ala
Google Sheet (terpisah dari Form Kehadiran di Scope C).

## 5. Email broadcast (opsional, tapi disarankan diisi)

Tambahkan di Railway Variables kalau mau broadcast pengumuman benar-benar
terkirim lewat email (kalau kosong, pengumuman tetap masuk sebagai
notifikasi dalam aplikasi, cuma email-nya nggak jalan):
- `SMTP_HOST`, `SMTP_PORT` (default 587), `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`

## 6. Job pengingat otomatis (belum di-otomatisasi penuh)

Endpoint `POST /api/notifications/run-check` aman dipanggil berkali-kali
(idempotent) dan mengecek siapa yang belum isi form hari ini setelah lewat
jam batas waktu di Pengaturan, lalu eskalasi ke rantai atasan kalau
`notify_atasan_enabled` aktif. Saat ini dipicu manual lewat tombol
"Kirim pengingat sekarang" di Dashboard -- kalau mau benar-benar otomatis
tiap beberapa jam, tambahkan Railway Cron Job yang hit endpoint ini
(butuh service account/token khusus dulu, karena endpoint ini pakai auth
header X-User-Email biasa -- ini bagian yang perlu didiskusikan lagi kalau
mau full-otomatis).


## 7. Pilih provider AI: Gemini atau OpenAI

Set di Railway Variables:
- `AI_PROVIDER=openai` (atau `gemini`, default kalau tidak diisi)
- Isi API key sesuai provider aktif: `OPENAI_API_KEY` atau `GEMINI_API_KEY` (yang tidak aktif boleh kosong)

**PENTING sebelum pindah provider di produksi yang sudah ada isinya:**
Dokumen yang SUDAH di-embed pakai Gemini tidak "nyambung" secara semantik
kalau dicari pakai model embedding OpenAI (meski sama-sama 768 dimensi
angka, ruang vektornya beda total) -- pencarian RAG buat dokumen lama
akan jadi kurang relevan (bukan error, cuma diam-diam kurang akurat).
Dokumen yang diupload SETELAH pindah provider aman, ter-embed pakai
provider baru. Kalau company sudah punya banyak dokumen lama, sebaiknya
upload ulang / re-embed dulu setelah pindah provider. Detail lengkap ada
di komentar `api/ai.py`.

Fitur video/YouTube native (Gemini bisa "menonton" langsung) tidak ada
padanan persis di OpenAI -- versi OpenAI cuma transkrip audio (Whisper)
untuk file video, dan transkrip caption untuk YouTube (kalau videonya
punya caption). Ini keterbatasan asli provider, bukan bug.

## 8. Schema database: mana yang harus dijalankan?

- `api/migration_scope_*.sql` -- jalankan BERURUTAN sesuai nomor scope-nya
  kalau ini setup database BARU dari nol, atau kalau database lama belum
  ketinggalan migrasi tertentu.
- `api/schema.sql` -- BUKAN untuk dijalankan langsung, ini referensi
  lengkap "seperti apa struktur DB seharusnya sekarang" (semua tabel,
  lama+baru, digabung). Dipakai untuk cek/bandingkan, bukan dieksekusi
  urut dari atas ke bawah.

## Catatan

- `api/app.py` (Streamlit) adalah versi lama, sudah tidak dipakai di produksi -- dibiarkan di repo cuma sebagai referensi, boleh dihapus kapan saja kalau sudah yakin tidak perlu rollback ke sana.
- File besar (upload dokumen/media/form) tetap masuk ke Supabase Storage lewat `db.py`, jalur ini tidak berubah.
