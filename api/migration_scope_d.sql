-- ============================================================
-- MIGRATION: Scope D - Form Lapor Kerjaan (BEDA dari Kehadiran)
--            Baris dinamis ala Google Sheet, lampiran opsional per
--            baris, tanggal/jam/nama auto-isi (bukan field yang
--            diisi manual).
-- Jalankan ini di Supabase SQL Editor SEBELUM deploy kode baru.
-- Aman dijalankan ulang (semua pakai IF NOT EXISTS).
-- ============================================================

-- Satu "amplop" laporan per karyawan per hari -- tanggal & siapa yang
-- lapor otomatis dari user_email + report_date (bukan field yang diisi
-- manual di form, makanya nggak ada kolom itu di form_fields).
CREATE TABLE IF NOT EXISTS public.work_reports (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL REFERENCES public.companies(id) ON DELETE CASCADE,
  user_email text NOT NULL,
  report_date date NOT NULL,
  submitted_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  UNIQUE (company_id, user_email, report_date)
);

CREATE INDEX IF NOT EXISTS work_reports_company_date_idx
  ON public.work_reports(company_id, report_date);
CREATE INDEX IF NOT EXISTS work_reports_user_idx
  ON public.work_reports(user_email);

-- Baris-baris pekerjaan (ala Google Sheet) -- karyawan bebas nambah baris
-- sendiri, 1 baris = 1 item pekerjaan. Lampiran per baris OPSIONAL
-- (foto/dokumen/video), boleh kosong.
-- attachment_kind: 'image' | 'video' | 'audio' | 'document' | NULL
CREATE TABLE IF NOT EXISTS public.work_report_rows (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  report_id uuid NOT NULL REFERENCES public.work_reports(id) ON DELETE CASCADE,
  row_order integer NOT NULL DEFAULT 0,
  description text NOT NULL,
  time_note text,                 -- opsional, mis. "09:00-11:00" -- teks bebas, bukan wajib
  attachment_url text,
  attachment_kind text CHECK (attachment_kind IN ('image','video','audio','document') OR attachment_kind IS NULL),
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS work_report_rows_report_idx
  ON public.work_report_rows(report_id);
