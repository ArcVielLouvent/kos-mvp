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

## Catatan

- `api/app.py` (Streamlit) adalah versi lama, sudah tidak dipakai di produksi -- dibiarkan di repo cuma sebagai referensi, boleh dihapus kapan saja kalau sudah yakin tidak perlu rollback ke sana.
- File besar (upload dokumen/media) tetap masuk ke Supabase Storage lewat `db.py`, jalur ini tidak berubah.
