"""
Dispatcher provider AI -- KOS bisa jalan pakai Google Gemini ATAU OpenAI,
diatur lewat 1 env var: AI_PROVIDER=gemini (default) atau AI_PROVIDER=openai.

Kenapa begini: klien produksi (Pak Dianata) pakai OpenAI API, tapi selama
pengembangan sering dites pakai Gemini karena kuota gratisnya lebih
longgar. Daripada 2 kode berbeda yang harus disinkronkan manual tiap ada
perubahan, modul ini cuma nge-load SATU implementasi (ai_gemini.py atau
ai_openai.py) dan expose semua fungsi publiknya dengan nama yang SAMA --
jadi index.py tetap manggil `ai.generate_answer(...)`, `ai.embed_text(...)`,
dst tanpa peduli provider mana yang lagi aktif di belakangnya.

PENTING -- HAL YANG HARUS DIPERHATIKAN SEBELUM GANTI PROVIDER DI PRODUKSI:
1. Kedua provider dikunci ke 768 dimensi embedding (lihat EMBEDDING_DIMENSIONS
   di ai_openai.py, dan model embedding Gemini yang dipakai) supaya kolom
   `vector(768)` di database TIDAK perlu migrasi ulang skema.
   TAPI -- 768 angka yang sama BUKAN BERARTI ruang vektornya sama.
   Vector embedding dari Gemini dan OpenAI TIDAK bisa dibandingkan
   silang (apple-to-apple), karena model yang menghasilkannya beda total.
   Kalau dokumen-dokumen yang SUDAH ADA di database di-embed pakai Gemini,
   lalu kamu pindah ke AI_PROVIDER=openai, pencarian semantik (RAG di
   Chat KOS) untuk dokumen LAMA itu akan jadi tidak relevan/acak --
   BUKAN error, tapi hasilnya diam-diam jelek. Dokumen yang diupload
   SETELAH pindah provider akan ter-embed pakai provider baru dan aman.
   Solusi kalau mau pindah provider dengan dokumen lama yang sudah banyak:
   re-embed ulang semua dokumen (re-upload, atau bikin script migrasi
   yang re-generate embedding tiap dokumen pakai provider baru).
2. Fitur video/YouTube native (Gemini bisa "menonton" video & URL YouTube
   langsung) TIDAK ada padanan persis di OpenAI -- versi OpenAI cuma
   transkrip audio (Whisper) untuk file video, dan transkrip caption
   (kalau ada) untuk YouTube. Ini keterbatasan asli OpenAI, bukan bug.
   Lihat docstring di ai_openai.py:extract_multimodal & describe_youtube_video.
3. Set API key yang sesuai provider aktif: GEMINI_API_KEY untuk Gemini,
   OPENAI_API_KEY untuk OpenAI. Cuma perlu isi salah satu (yang aktif).
"""
import os

try:
    from . import ai_gemini, ai_openai
except ImportError:  # dijalankan langsung dari dalam folder api/
    import ai_gemini
    import ai_openai

_PROVIDER = os.environ.get("AI_PROVIDER", "gemini").strip().lower()
_impl = ai_openai if _PROVIDER == "openai" else ai_gemini

# Re-export semua fungsi publik dari provider yang aktif ke namespace modul
# ini -- supaya kode pemanggil (index.py, dst) tetap pakai `ai.nama_fungsi(...)`
# apa adanya, tidak perlu tahu provider mana yang lagi jalan.
for _name in dir(_impl):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_impl, _name)

ACTIVE_PROVIDER = _PROVIDER  # buat debugging/health-check, lihat index.py /api/health kalau ada
