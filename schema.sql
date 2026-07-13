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