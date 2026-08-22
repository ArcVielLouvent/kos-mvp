-- ============================================================
-- MIGRATION: Scope B - Fondasi (hierarki, settings, kehadiran)
-- Jalankan ini di Supabase SQL Editor SEBELUM deploy kode baru.
-- ============================================================

-- Atasan langsung (terpisah dari role sistem)
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS manager_email text;

-- Pengaturan fitur per perusahaan (toggle, diatur Owner di halaman Pengaturan)
CREATE TABLE IF NOT EXISTS public.company_settings (
  company_id uuid PRIMARY KEY REFERENCES public.companies(id) ON DELETE CASCADE,
  poin_pelanggaran_enabled boolean NOT NULL DEFAULT false,
  notify_atasan_enabled boolean NOT NULL DEFAULT false,
  attendance_deadline_hour integer NOT NULL DEFAULT 24,
  updated_at timestamp with time zone DEFAULT now()
);

-- Kehadiran harian (Form Kehadiran)
CREATE TABLE IF NOT EXISTS public.attendance (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_email text NOT NULL,
  company_id uuid NOT NULL REFERENCES public.companies(id) ON DELETE CASCADE,
  attendance_date date NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  UNIQUE (user_email, company_id, attendance_date)
);
