-- 1. Aktifkan ekstensi pgvector (jika belum)
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Buat tabel dokumen universal (Global KOS)
CREATE TABLE IF NOT EXISTS documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  folder_path TEXT DEFAULT '/',
  metadata JSONB DEFAULT '{}'::jsonb,
  embedding VECTOR(768),
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- 3. Index untuk mempercepat pencarian similarity
CREATE INDEX IF NOT EXISTS documents_embedding_idx
  ON documents USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

-- 4. Fungsi pencarian (RAG) dengan dukungan filter folder
CREATE OR REPLACE FUNCTION match_documents (
  query_embedding VECTOR(768),
  match_count INT,
  folder_prefix TEXT DEFAULT '/' -- Default mencari di semua folder ('/')
)
RETURNS TABLE (
  id UUID,
  title TEXT,
  content TEXT,
  folder_path TEXT,
  metadata JSONB,
  similarity FLOAT
)
LANGUAGE sql STABLE
AS $$
  SELECT
    id, title, content, folder_path, metadata,
    1 - (embedding <=> query_embedding) AS similarity
  FROM documents
  -- Logika cerdas: Jika user mencari di '/SOP/', sistem akan mencari di folder itu dan sub-foldernya
  WHERE folder_path LIKE folder_prefix || '%' 
  ORDER BY embedding <=> query_embedding
  LIMIT match_count;
$$;

-- 6. Buat tabel pengguna (Single-Table, tanpa relasi rumit)
CREATE TABLE IF NOT EXISTS users (
  email TEXT PRIMARY KEY,
  role TEXT NOT NULL CHECK (role IN ('Admin', 'Karyawan')),
  folder_access TEXT NOT NULL DEFAULT '/',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 7. Suntikkan akun Super Admin default (agar kamu tidak terkunci dari sistem)
-- Password akan diurus di Streamlit menggunakan form login sederhana
INSERT INTO users (email, role, folder_access) 
VALUES ('admin@kos.com', 'Admin', '/')
ON CONFLICT (email) DO NOTHING;

create table if not exists companies (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  created_at timestamptz default now()
);

alter table users add column if not exists company_id uuid references companies(id);
alter table documents add column if not exists company_id uuid references companies(id);
alter table users add column if not exists must_change_password boolean default false;

create index if not exists documents_company_idx on documents(company_id);
create index if not exists users_company_idx on users(company_id);

-- match_documents sekarang WAJIB filter company_id, bukan cuma folder
create or replace function match_documents (
  query_embedding vector(768),
  match_count int,
  folder_prefix text default '/',
  p_company_id uuid default null
)
returns table (id uuid, title text, content text, folder_path text, metadata jsonb, similarity float)
language sql stable
as $$
  select id, title, content, folder_path, metadata,
    1 - (embedding <=> query_embedding) as similarity
  from documents
  where company_id = p_company_id
    and folder_path like folder_prefix || '%'
  order by embedding <=> query_embedding
  limit match_count;
$$;

-- Register company + admin pertama, atomik (gagal semua kalau email dobel)
create or replace function register_company(
  p_company_name text, p_admin_email text, p_password_hash text
) returns uuid language plpgsql as $$
declare new_company_id uuid;
begin
  if exists (select 1 from users where email = p_admin_email) then
    raise exception 'EMAIL_TAKEN';
  end if;
  insert into companies (name) values (p_company_name) returning id into new_company_id;
  insert into users (email, password, role, folder_access, company_id, company_name)
  values (p_admin_email, p_password_hash, 'Admin', '/', new_company_id, p_company_name);
  return new_company_id;
end; $$;