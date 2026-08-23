-- ============================================================
-- SCHEMA MASTER KOS -- SELURUH TABEL (lama & terbaru), digabung jadi
-- satu file referensi. Ini BUKAN untuk dijalankan urut dari atas ke
-- bawah di database baru (constraint FK antar tabel belum tentu valid
-- urutannya) -- fungsinya sebagai DOKUMENTASI/REFERENSI struktur
-- database yang SEDANG BERJALAN saat ini, supaya siapa pun (termasuk
-- developer baru) bisa lihat schema lengkap tanpa harus buka Supabase
-- dashboard atau baca satu-satu file migration_scope_*.sql.
--
-- BEDA dengan migration_scope_b1.sql / migration_scope_c.sql /
-- migration_scope_d.sql: file-file scope itu untuk DIJALANKAN di
-- Supabase SQL Editor secara berurutan sesuai kapan fitur itu dibuat
-- (dipakai pas deploy pertama kali / migrasi database yang masih
-- ketinggalan). File INI (schema.sql) di-update setiap kali ada
-- perubahan schema apa pun, terlepas dari scope mana asalnya, supaya
-- selalu jadi 1 sumber kebenaran (single source of truth) untuk
-- "seperti apa struktur DB kita sekarang". WAJIB di-update tiap ada
-- ALTER/CREATE TABLE baru, tidak peduli lewat scope mana perubahan
-- itu masuk.
-- ============================================================

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto; -- buat gen_random_uuid()

CREATE TABLE public.companies (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  name text NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  logo_url text,
  docx_template_url text,
  CONSTRAINT companies_pkey PRIMARY KEY (id)
);

CREATE TABLE public.users (
  email text NOT NULL,
  role text NOT NULL CHECK (role = ANY (ARRAY['SuperAdmin'::text, 'Admin'::text, 'Karyawan'::text])),
  folder_access text NOT NULL DEFAULT '/'::text,
  created_at timestamp with time zone DEFAULT now(),
  password text,
  company_id uuid,
  must_change_password boolean DEFAULT false,
  position_title text,
  permission_level text DEFAULT 'crud'::text CHECK (permission_level = ANY (ARRAY['crud'::text, 'read_only'::text])),
  full_name text,
  phone_number text,
  manager_email text,
  CONSTRAINT users_pkey PRIMARY KEY (email),
  CONSTRAINT users_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id)
);

CREATE TABLE public.folders (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  company_id uuid,
  path text NOT NULL,
  CONSTRAINT folders_pkey PRIMARY KEY (id),
  CONSTRAINT folders_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id)
);

CREATE TABLE public.documents (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  title text NOT NULL,
  content text NOT NULL,
  folder_path text DEFAULT '/'::text,
  metadata jsonb DEFAULT '{}'::jsonb,
  embedding vector(768),
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  company_id uuid,
  file_url text,
  structured_data jsonb,
  CONSTRAINT documents_pkey PRIMARY KEY (id),
  CONSTRAINT documents_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id)
);

CREATE INDEX IF NOT EXISTS documents_embedding_idx
  ON public.documents USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

CREATE TABLE public.document_chunks (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  document_id uuid,
  company_id uuid,
  chunk_index integer NOT NULL,
  content text NOT NULL,
  embedding vector(768),
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT document_chunks_pkey PRIMARY KEY (id),
  CONSTRAINT document_chunks_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id),
  CONSTRAINT document_chunks_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id)
);

CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx
  ON public.document_chunks USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

CREATE TABLE public.chat_sessions (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  company_id uuid,
  user_email text NOT NULL,
  title text DEFAULT 'Percakapan baru'::text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT chat_sessions_pkey PRIMARY KEY (id),
  CONSTRAINT chat_sessions_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id)
);

CREATE TABLE public.chat_messages (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  session_id uuid,
  role text CHECK (role = ANY (ARRAY['user'::text, 'assistant'::text])),
  content text NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  sources jsonb DEFAULT '[]'::jsonb,
  CONSTRAINT chat_messages_pkey PRIMARY KEY (id),
  CONSTRAINT chat_messages_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.chat_sessions(id)
);

CREATE TABLE public.reports (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  company_id uuid,
  user_email text NOT NULL,
  content text,
  media_url text,
  media_type text,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT reports_pkey PRIMARY KEY (id),
  CONSTRAINT reports_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id)
);
-- Catatan: tabel "reports" ini LEGACY (laporan flat, 1 teks + 1 media),
-- sudah digantikan work_reports + work_report_rows di bawah. Dibiarkan
-- ada demi kompatibilitas mundur endpoint /api/reports lama, belum
-- dihapus/dipensiunkan resmi.

CREATE TABLE public.quizzes (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  company_id uuid,
  source_document_id uuid,
  folder_path text NOT NULL DEFAULT '/'::text,
  title text NOT NULL,
  questions jsonb NOT NULL,
  passing_score integer NOT NULL DEFAULT 70,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT quizzes_pkey PRIMARY KEY (id),
  CONSTRAINT quizzes_source_document_id_fkey FOREIGN KEY (source_document_id) REFERENCES public.documents(id),
  CONSTRAINT quizzes_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id)
);

CREATE TABLE public.quiz_attempts (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  quiz_id uuid,
  user_email text NOT NULL,
  company_id uuid,
  score integer NOT NULL,
  total integer NOT NULL,
  passed boolean NOT NULL,
  answers jsonb,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT quiz_attempts_pkey PRIMARY KEY (id),
  CONSTRAINT quiz_attempts_quiz_id_fkey FOREIGN KEY (quiz_id) REFERENCES public.quizzes(id),
  CONSTRAINT quiz_attempts_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id)
);

CREATE TABLE public.ai_drafts (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  company_id uuid,
  requested_by text NOT NULL,
  title text NOT NULL,
  content text NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT ai_drafts_pkey PRIMARY KEY (id),
  CONSTRAINT ai_drafts_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id)
);

CREATE TABLE public.company_settings (
  company_id uuid NOT NULL,
  poin_pelanggaran_enabled boolean NOT NULL DEFAULT false,
  notify_atasan_enabled boolean NOT NULL DEFAULT false,
  attendance_deadline_hour integer NOT NULL DEFAULT 24,
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT company_settings_pkey PRIMARY KEY (company_id),
  CONSTRAINT company_settings_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id)
);

CREATE TABLE public.attendance (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_email text NOT NULL,
  company_id uuid NOT NULL,
  attendance_date date NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT attendance_pkey PRIMARY KEY (id),
  CONSTRAINT attendance_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id)
);
-- Catatan: tabel "attendance" ini LEGACY (check-in sederhana), sudah
-- digantikan form_submissions (Form Kehadiran dinamis) di bawah.

-- ---------- SCOPE C: Form Kehadiran (dinamis ala Google Forms) ----------
CREATE TABLE public.form_templates (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL,
  name text NOT NULL DEFAULT 'Form Kehadiran & Lapor Kerjaan'::text,
  description text,
  is_daily boolean NOT NULL DEFAULT true,
  is_active boolean NOT NULL DEFAULT true,
  created_by text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT form_templates_pkey PRIMARY KEY (id),
  CONSTRAINT form_templates_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id)
);

CREATE TABLE public.form_fields (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  template_id uuid NOT NULL,
  label text NOT NULL,
  field_type text NOT NULL DEFAULT 'short_text'::text CHECK (field_type = ANY (ARRAY['short_text'::text, 'long_text'::text, 'number'::text, 'date'::text, 'select'::text, 'checkbox'::text, 'file'::text])),
  options jsonb DEFAULT '[]'::jsonb,
  file_kind text DEFAULT 'any'::text CHECK (file_kind = ANY (ARRAY['video'::text, 'audio'::text, 'document'::text, 'any'::text])),
  is_required boolean NOT NULL DEFAULT false,
  sort_order integer NOT NULL DEFAULT 0,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT form_fields_pkey PRIMARY KEY (id),
  CONSTRAINT form_fields_template_id_fkey FOREIGN KEY (template_id) REFERENCES public.form_templates(id)
);

CREATE TABLE public.form_submissions (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  template_id uuid NOT NULL,
  company_id uuid NOT NULL,
  user_email text NOT NULL,
  submission_date date NOT NULL,
  status text NOT NULL DEFAULT 'on_time'::text CHECK (status = ANY (ARRAY['on_time'::text, 'late'::text])),
  submitted_at timestamp with time zone DEFAULT now(),
  CONSTRAINT form_submissions_pkey PRIMARY KEY (id),
  CONSTRAINT form_submissions_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id),
  CONSTRAINT form_submissions_template_id_fkey FOREIGN KEY (template_id) REFERENCES public.form_templates(id)
);

CREATE TABLE public.form_submission_answers (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  submission_id uuid NOT NULL,
  field_id uuid NOT NULL,
  value_text text,
  file_url text,
  file_kind text,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT form_submission_answers_pkey PRIMARY KEY (id),
  CONSTRAINT form_submission_answers_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES public.form_submissions(id),
  CONSTRAINT form_submission_answers_field_id_fkey FOREIGN KEY (field_id) REFERENCES public.form_fields(id)
);

-- ---------- SCOPE C: Notifikasi, poin pelanggaran (skema saja), broadcast ----------
CREATE TABLE public.notifications (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL,
  recipient_email text NOT NULL,
  type text NOT NULL CHECK (type = ANY (ARRAY['reminder'::text, 'escalation'::text, 'broadcast'::text])),
  title text NOT NULL,
  message text NOT NULL,
  related_user_email text,
  related_date date,
  is_read boolean NOT NULL DEFAULT false,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT notifications_pkey PRIMARY KEY (id),
  CONSTRAINT notifications_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id)
);

CREATE TABLE public.violation_points (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL,
  user_email text NOT NULL,
  points integer NOT NULL DEFAULT 1,
  reason text,
  given_by text,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT violation_points_pkey PRIMARY KEY (id),
  CONSTRAINT violation_points_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id)
);
-- Catatan: SKEMA SAJA -- belum ada endpoint/UI yang memakai tabel ini,
-- klien belum konfirmasi fitur poin pelanggaran diaktifkan.

CREATE TABLE public.announcements (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL,
  sender_email text NOT NULL,
  subject text NOT NULL,
  body text NOT NULL,
  target_scope text NOT NULL DEFAULT '/'::text,
  recipient_count integer NOT NULL DEFAULT 0,
  sent_at timestamp with time zone DEFAULT now(),
  CONSTRAINT announcements_pkey PRIMARY KEY (id),
  CONSTRAINT announcements_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id)
);

-- ---------- SCOPE D: Form Lapor Kerjaan (baris dinamis ala Google Sheet) ----------
CREATE TABLE public.work_reports (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL,
  user_email text NOT NULL,
  report_date date NOT NULL,
  submitted_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT work_reports_pkey PRIMARY KEY (id),
  CONSTRAINT work_reports_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id),
  CONSTRAINT work_reports_unique_per_day UNIQUE (company_id, user_email, report_date)
);

CREATE TABLE public.work_report_rows (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  report_id uuid NOT NULL,
  row_order integer NOT NULL DEFAULT 0,
  description text NOT NULL,
  time_note text,
  attachment_url text,
  attachment_kind text CHECK ((attachment_kind = ANY (ARRAY['image'::text, 'video'::text, 'audio'::text, 'document'::text])) OR attachment_kind IS NULL),
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT work_report_rows_pkey PRIMARY KEY (id),
  CONSTRAINT work_report_rows_report_id_fkey FOREIGN KEY (report_id) REFERENCES public.work_reports(id)
);
