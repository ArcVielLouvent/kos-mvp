-- ============================================================
-- MIGRATION: Scope C - Form Kehadiran/Lapor Kerjaan dinamis,
--            notifikasi + eskalasi berjenjang, poin pelanggaran
--            (skema saja, belum diaktifkan di UI), broadcast email.
-- Jalankan ini di Supabase SQL Editor SEBELUM deploy kode baru.
-- Aman dijalankan ulang (semua pakai IF NOT EXISTS).
-- ============================================================

-- ------------------------------------------------------------
-- 1. FORM BUILDER (ala Google Forms)
--    Form Kehadiran & Form Lapor Kerjaan digabung jadi SATU
--    template per company ("form harian"), isinya diatur bebas
--    lewat form_fields (tipe field termasuk upload video/audio/
--    dokumen, dan wajib/opsional per field bisa diatur sendiri).
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.form_templates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL REFERENCES public.companies(id) ON DELETE CASCADE,
  name text NOT NULL DEFAULT 'Form Kehadiran & Lapor Kerjaan',
  description text,
  -- true = ini form harian aktif (dipakai attendance-check). Cuma boleh
  -- ada 1 yang is_daily=true per company (dijaga di layer aplikasi, bukan
  -- constraint DB, supaya gampang ganti-ganti template tanpa migrasi).
  is_daily boolean NOT NULL DEFAULT true,
  is_active boolean NOT NULL DEFAULT true,
  created_by text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS form_templates_company_idx ON public.form_templates(company_id);

-- field_type: 'short_text' | 'long_text' | 'number' | 'date' | 'select' | 'checkbox' | 'file'
-- file_kind (cuma dipakai kalau field_type='file'): 'video' | 'audio' | 'document' | 'any'
CREATE TABLE IF NOT EXISTS public.form_fields (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  template_id uuid NOT NULL REFERENCES public.form_templates(id) ON DELETE CASCADE,
  label text NOT NULL,
  field_type text NOT NULL DEFAULT 'short_text'
    CHECK (field_type IN ('short_text','long_text','number','date','select','checkbox','file')),
  options jsonb DEFAULT '[]'::jsonb,       -- daftar pilihan untuk select/checkbox
  file_kind text DEFAULT 'any'
    CHECK (file_kind IN ('video','audio','document','any')),
  is_required boolean NOT NULL DEFAULT false,
  sort_order integer NOT NULL DEFAULT 0,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS form_fields_template_idx ON public.form_fields(template_id);

-- Satu submission = satu isian form dari satu karyawan di satu tanggal
-- (menggantikan konsep attendance check-in yang lama -- isi form ini
-- OTOMATIS berarti "hadir & lapor" hari itu).
CREATE TABLE IF NOT EXISTS public.form_submissions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  template_id uuid NOT NULL REFERENCES public.form_templates(id) ON DELETE CASCADE,
  company_id uuid NOT NULL REFERENCES public.companies(id) ON DELETE CASCADE,
  user_email text NOT NULL,
  submission_date date NOT NULL,
  status text NOT NULL DEFAULT 'on_time' CHECK (status IN ('on_time','late')),
  submitted_at timestamptz DEFAULT now(),
  UNIQUE (template_id, user_email, submission_date)
);

CREATE INDEX IF NOT EXISTS form_submissions_company_date_idx
  ON public.form_submissions(company_id, submission_date);
CREATE INDEX IF NOT EXISTS form_submissions_user_idx
  ON public.form_submissions(user_email);

CREATE TABLE IF NOT EXISTS public.form_submission_answers (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  submission_id uuid NOT NULL REFERENCES public.form_submissions(id) ON DELETE CASCADE,
  field_id uuid NOT NULL REFERENCES public.form_fields(id) ON DELETE CASCADE,
  value_text text,
  file_url text,
  file_kind text,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS form_submission_answers_submission_idx
  ON public.form_submission_answers(submission_id);

-- ------------------------------------------------------------
-- 2. NOTIFIKASI (pengingat belum isi form + eskalasi berjenjang
--    ke rantai atasan, bukan cuma 1 level -- mengikuti manager_email
--    yang sudah ada di tabel users).
-- ------------------------------------------------------------
-- type: 'reminder' (ke karyawan yang telat) | 'escalation' (ke atasan)
--       | 'broadcast' (pengumuman)
CREATE TABLE IF NOT EXISTS public.notifications (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL REFERENCES public.companies(id) ON DELETE CASCADE,
  recipient_email text NOT NULL,
  type text NOT NULL CHECK (type IN ('reminder','escalation','broadcast')),
  title text NOT NULL,
  message text NOT NULL,
  related_user_email text,      -- untuk escalation: siapa bawahan yang telat
  related_date date,            -- untuk reminder/escalation: tanggal form yang belum diisi
  is_read boolean NOT NULL DEFAULT false,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS notifications_recipient_idx
  ON public.notifications(recipient_email, is_read);

-- Catatan: dedupe notifikasi (1 reminder/escalation per hari per orang)
-- ditangani di kode aplikasi (cek-lalu-insert, sama gaya dengan
-- check_in_attendance), bukan lewat unique constraint DB -- supaya
-- related_user_email/related_date yang boleh NULL tidak butuh index
-- ekspresi yang rewel di sisi Postgres/PostgREST.

-- ------------------------------------------------------------
-- 3. POIN PELANGGARAN
--    Klien BELUM minta fitur ini aktif sekarang (baru rencana),
--    jadi cuma disiapkan skemanya. Tidak ada endpoint/UI yang
--    dipasang untuk ini sampai dikonfirmasi ke klien.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.violation_points (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL REFERENCES public.companies(id) ON DELETE CASCADE,
  user_email text NOT NULL,
  points integer NOT NULL DEFAULT 1,
  reason text,
  given_by text,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS violation_points_user_idx ON public.violation_points(user_email);

-- ------------------------------------------------------------
-- 4. BROADCAST PENGUMUMAN VIA EMAIL
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.announcements (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL REFERENCES public.companies(id) ON DELETE CASCADE,
  sender_email text NOT NULL,
  subject text NOT NULL,
  body text NOT NULL,
  target_scope text NOT NULL DEFAULT '/',   -- folder_access prefix, '/' = semua orang
  recipient_count integer NOT NULL DEFAULT 0,
  sent_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS announcements_company_idx ON public.announcements(company_id);
