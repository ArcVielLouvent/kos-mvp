-- ============================================================
-- MIGRATION: Scope E - Presisi menit untuk Batas Waktu Lapor Harian
-- (sebelumnya cuma jam bulat 1-24, sekarang bisa HH:MM)
-- Jalankan ini di Supabase SQL Editor. Aman dijalankan ulang.
-- ============================================================

ALTER TABLE public.company_settings
  ADD COLUMN IF NOT EXISTS attendance_deadline_minute integer NOT NULL DEFAULT 0
  CHECK (attendance_deadline_minute >= 0 AND attendance_deadline_minute <= 59);
