import secrets
import bcrypt
import streamlit as st
from supabase import create_client, Client


def get_client() -> Client:
    """
    Inisialisasi Client Supabase Admin (Bypass RLS)
    Menggunakan SUPABASE_SERVICE_ROLE_KEY agar aman dari error RLS 42501.
    """
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_SERVICE_ROLE_KEY"]
    return create_client(url, key)


# ==========================================
# PASSWORD
# ==========================================
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    if not hashed:
        return False
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except ValueError:
        return False


# ==========================================
# FOLDER
# ==========================================
def normalize_folder(path: str) -> str:
    path = (path or "/").strip()
    if not path.startswith("/"):
        path = "/" + path
    if not path.endswith("/"):
        path += "/"
    return path


# ==========================================
# COMPANY & AUTH
# ==========================================
def register_company(company_name: str, admin_email: str, password: str) -> str:
    client = get_client()
    try:
        result = client.rpc(
            "register_company",
            {
                "p_company_name": company_name.strip(),
                "p_admin_email": admin_email.strip().lower(),
                "p_password_hash": hash_password(password),
            },
        ).execute()
        return result.data
    except Exception as e:
        if "EMAIL_TAKEN" in str(e):
            raise ValueError("Email ini sudah terdaftar. Silakan login.")
        raise


def get_user(email: str):
    client = get_client()
    response = (
        client.table("users")
        .select("*, companies(name)")
        .eq("email", email.strip().lower())
        .execute()
    )
    if not response.data:
        return None
    row = response.data[0]
    row["company_name"] = (row.get("companies") or {}).get("name")
    return row


def update_password(email: str, new_password: str):
    client = get_client()
    client.table("users").update(
        {"password": hash_password(new_password), "must_change_password": False}
    ).eq("email", email.strip().lower()).execute()


# ==========================================
# KARYAWAN
# ==========================================
def add_users_bulk(
    emails: list, folder_access: str, company_id: str, position_title: str = None
) -> dict:
    client = get_client()
    folder_access = normalize_folder(folder_access)

    create_folder(company_id, folder_access)

    records = []
    temp_passwords = {}
    for raw_email in emails:
        email = raw_email.strip().lower()
        if not email:
            continue
        temp_pw = secrets.token_urlsafe(6)
        temp_passwords[email] = temp_pw
        records.append(
            {
                "email": email,
                "role": "Karyawan",
                "folder_access": folder_access,
                "password": hash_password(temp_pw),
                "company_id": company_id,
                "must_change_password": True,
                "position_title": (position_title or "").strip() or None,
            }
        )

    if records:
        client.table("users").upsert(records, on_conflict="email").execute()

    return temp_passwords


def add_admin(
    email: str,
    folder_access: str,
    permission_level: str,
    company_id: str,
    position_title: str = None,
) -> str:
    """Tambah akun Admin baru (bukan Karyawan) -- khusus dipanggil SuperAdmin/Admin crud."""
    client = get_client()
    folder_access = normalize_folder(folder_access)
    create_folder(company_id, folder_access)

    temp_pw = secrets.token_urlsafe(6)
    client.table("users").upsert(
        {
            "email": email.strip().lower(),
            "role": "Admin",
            "folder_access": folder_access,
            "permission_level": permission_level,
            "password": hash_password(temp_pw),
            "company_id": company_id,
            "must_change_password": True,
            "position_title": (position_title or "").strip() or None,
        },
        on_conflict="email",
    ).execute()
    return temp_pw


def get_unique_folders(company_id: str) -> list:
    client = get_client()
    response = (
        client.table("documents")
        .select("folder_path")
        .eq("company_id", company_id)
        .execute()
    )
    folders = {"/"}
    for item in response.data:
        if item.get("folder_path"):
            folders.add(item["folder_path"])
    return sorted(folders)


# ==========================================
# DOKUMEN & RAG (dipisah: 1 dokumen utuh, banyak chunk untuk pencarian)
# ==========================================
def insert_document_with_chunks(
    title: str,
    chunks: list,
    embeddings: list,
    company_id: str,
    folder_path: str = "/",
    metadata: dict = None,
    file_bytes: bytes = None,
    original_filename: str = None,
    external_url: str = None,
    structured_data: list = None,
) -> str:
    """
    Simpan 1 baris di `documents` (file utuh, muncul 1x di File Manager, ada link
    download kalau file_bytes diisi), lalu simpan tiap chunk sebagai baris terpisah
    di `document_chunks` (khusus untuk pencarian vector, tidak pernah tampil sebagai
    "file" terpisah di File Manager).
    """
    client = get_client()
    folder_path = normalize_folder(folder_path)
    create_folder(company_id, folder_path)

    file_url = external_url
    if not file_url and file_bytes and original_filename:
        storage_path = f"{company_id}/{folder_path.strip('/')}/{original_filename}"
        try:
            client.storage.from_("company-files").upload(
                storage_path, file_bytes, {"upsert": "true"}
            )
            signed = client.storage.from_("company-files").create_signed_url(
                storage_path,
                3600 * 24 * 7,  # berlaku 7 hari, di-generate ulang tiap dibuka
            )
            file_url = signed.get("signedURL") or signed.get("signed_url")
        except Exception as e:
            # Sengaja TIDAK ditelan diam-diam -- tampilkan biar bisa didiagnosis.
            # Dokumen tetap tersimpan (bisa dicari & dijawab AI), cuma tanpa file
            # asli untuk didownload.
            st.warning(
                f"'{title}': gagal upload ke Storage, dokumen tetap tersimpan "
                f"tapi TANPA file asli untuk didownload. Penyebab: {e}"
            )
            file_url = None

    preview = chunks[0][:2000] if chunks else ""

    doc = (
        client.table("documents")
        .insert(
            {
                "title": title,
                "content": preview,
                "folder_path": folder_path,
                "metadata": metadata or {},
                "company_id": company_id,
                "file_url": file_url,
                "structured_data": structured_data,
            }
        )
        .execute()
    )
    document_id = doc.data[0]["id"]

    chunk_rows = [
        {
            "document_id": document_id,
            "company_id": company_id,
            "chunk_index": i,
            "content": chunk,
            "embedding": emb,
        }
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings))
    ]
    if chunk_rows:
        client.table("document_chunks").insert(chunk_rows).execute()

    return document_id


def search_documents(
    query_embedding: list,
    company_id: str,
    match_count: int = 3,
    folder_prefix: str = "/",
):
    client = get_client()
    response = client.rpc(
        "match_documents",
        {
            "query_embedding": query_embedding,
            "match_count": match_count,
            "folder_prefix": normalize_folder(folder_prefix),
            "p_company_id": company_id,
        },
    ).execute()
    return response.data


def delete_document(doc_id: str):
    client = get_client()
    client.table("documents").delete().eq("id", doc_id).execute()


def move_document(doc_id: str, new_path: str, company_id: str):
    client = get_client()
    new_path = normalize_folder(new_path)
    create_folder(company_id, new_path)
    client.table("documents").update({"folder_path": new_path}).eq(
        "id", doc_id
    ).execute()


# ---------- FILE MANAGER ----------
def create_folder(company_id: str, path: str):
    client = get_client()
    path = normalize_folder(path)
    client.table("folders").upsert(
        {"company_id": company_id, "path": path}, on_conflict="company_id,path"
    ).execute()


def delete_folder_and_contents(company_id: str, folder_path: str):
    client = get_client()
    folder_path = normalize_folder(folder_path)

    client.table("documents").delete().eq("company_id", company_id).ilike(
        "folder_path", f"{folder_path}%"
    ).execute()
    client.table("folders").delete().eq("company_id", company_id).ilike(
        "path", f"{folder_path}%"
    ).execute()


def list_child_folders(company_id: str, parent_path: str) -> list:
    parent_path = normalize_folder(parent_path)
    client = get_client()
    folders = (
        client.table("folders").select("path").eq("company_id", company_id).execute()
    )
    docs = (
        client.table("documents")
        .select("folder_path")
        .eq("company_id", company_id)
        .execute()
    )

    all_paths = {r["path"] for r in folders.data}
    all_paths |= {r["folder_path"] for r in docs.data if r.get("folder_path")}

    children = set()
    for path in all_paths:
        if path.startswith(parent_path) and path != parent_path:
            first_segment = path[len(parent_path) :].split("/")[0]
            if first_segment:
                children.add(parent_path + first_segment + "/")
    return sorted(children)


def list_documents_in_folder(
    company_id: str, folder_path: str, page: int = 1, page_size: int = 20
):
    """Return (list_dokumen, total_count) -- dipaginasi supaya tidak jadi 1 daftar panjang."""
    client = get_client()
    offset = (page - 1) * page_size
    r = (
        client.table("documents")
        .select("id, title, metadata, created_at, file_url", count="exact")
        .eq("company_id", company_id)
        .eq("folder_path", normalize_folder(folder_path))
        .order("created_at", desc=True)
        .range(offset, offset + page_size - 1)
        .execute()
    )
    return r.data, (r.count or 0)


# ---------- CHAT HISTORY ----------
def create_chat_session(user_email: str, company_id: str) -> str:
    client = get_client()
    r = (
        client.table("chat_sessions")
        .insert({"user_email": user_email, "company_id": company_id})
        .execute()
    )
    return r.data[0]["id"]


def list_chat_sessions(user_email: str):
    client = get_client()
    r = (
        client.table("chat_sessions")
        .select("*")
        .eq("user_email", user_email)
        .order("updated_at", desc=True)
        .execute()
    )
    return r.data


def get_chat_messages(session_id: str):
    client = get_client()
    r = (
        client.table("chat_messages")
        .select("*")
        .eq("session_id", session_id)
        .order("created_at")
        .execute()
    )
    return r.data


def add_chat_message(session_id: str, role: str, content: str, sources: list = None):
    client = get_client()
    client.table("chat_messages").insert(
        {
            "session_id": session_id,
            "role": role,
            "content": content,
            "sources": sources or [],
        }
    ).execute()
    client.table("chat_sessions").update({"updated_at": "now()"}).eq(
        "id", session_id
    ).execute()


def rename_chat_session(session_id: str, new_title: str):
    client = get_client()
    client.table("chat_sessions").update({"title": new_title}).eq(
        "id", session_id
    ).execute()


def delete_chat_session(session_id: str):
    client = get_client()
    client.table("chat_sessions").delete().eq("id", session_id).execute()


def rename_folder_cascade(company_id: str, old_path: str, new_name: str):
    client = get_client()
    old_path = normalize_folder(old_path)

    parts = [p for p in old_path.split("/") if p]
    if not parts:
        return

    parent_path = "/" + "/".join(parts[:-1]) + "/" if len(parts) > 1 else "/"
    new_path = parent_path + new_name.strip() + "/"

    folders = (
        client.table("folders")
        .select("path")
        .eq("company_id", company_id)
        .ilike("path", f"{old_path}%")
        .execute()
    )
    for f in folders.data:
        updated_path = f["path"].replace(old_path, new_path, 1)
        client.table("folders").update({"path": updated_path}).eq("path", f["path"]).eq(
            "company_id", company_id
        ).execute()

    docs = (
        client.table("documents")
        .select("id, folder_path")
        .eq("company_id", company_id)
        .ilike("folder_path", f"{old_path}%")
        .execute()
    )
    for d in docs.data:
        updated_path = d["folder_path"].replace(old_path, new_path, 1)
        client.table("documents").update({"folder_path": updated_path}).eq(
            "id", d["id"]
        ).execute()

    users = (
        client.table("users")
        .select("email, folder_access")
        .eq("company_id", company_id)
        .ilike("folder_access", f"{old_path}%")
        .execute()
    )
    for u in users.data:
        updated_path = u["folder_access"].replace(old_path, new_path, 1)
        client.table("users").update({"folder_access": updated_path}).eq(
            "email", u["email"]
        ).execute()


# ==========================================
# DIREKTORI KARYAWAN (folder-scoped: admin lihat yang di bawah cakupannya)
# ==========================================
def list_managed_users(company_id: str, viewer_folder_access: str, viewer_role: str):
    """
    SuperAdmin -> lihat semua user di perusahaan.
    Admin/Karyawan (kalau dipanggil) -> cuma user yang folder_access-nya
    berada DI DALAM cakupan folder viewer.
    """
    client = get_client()
    query = (
        client.table("users")
        .select(
            "email, role, folder_access, position_title, permission_level, created_at"
        )
        .eq("company_id", company_id)
        .order("created_at", desc=True)
    )
    if viewer_role != "SuperAdmin":
        query = query.like("folder_access", f"{viewer_folder_access}%")
    r = query.execute()
    return r.data


def update_user_position(email: str, position_title: str):
    client = get_client()
    client.table("users").update(
        {"position_title": (position_title or "").strip() or None}
    ).eq("email", email.strip().lower()).execute()


def update_admin_permission(email: str, permission_level: str):
    client = get_client()
    client.table("users").update({"permission_level": permission_level}).eq(
        "email", email.strip().lower()
    ).execute()


# ==========================================
# LAPOR KERJAAN KARYAWAN
# ==========================================
def add_report(
    user_email: str,
    company_id: str,
    content: str = None,
    media_url: str = None,
    media_type: str = "text",
):
    client = get_client()
    client.table("reports").insert(
        {
            "user_email": user_email.strip().lower(),
            "company_id": company_id,
            "content": content,
            "media_url": media_url,
            "media_type": media_type,
        }
    ).execute()


def get_user_reports(user_email: str):
    client = get_client()
    r = (
        client.table("reports")
        .select("*")
        .eq("user_email", user_email.strip().lower())
        .order("created_at", desc=True)
        .execute()
    )
    return r.data


# ==========================================
# SISTEM KUIS TRAINING ONBOARDING
# ==========================================
def create_quiz(
    company_id: str,
    folder_path: str,
    title: str,
    questions: list,
    source_document_id: str = None,
    passing_score: int = 70,
) -> str:
    client = get_client()
    r = (
        client.table("quizzes")
        .insert(
            {
                "company_id": company_id,
                "folder_path": normalize_folder(folder_path),
                "title": title,
                "questions": questions,
                "source_document_id": source_document_id,
                "passing_score": passing_score,
            }
        )
        .execute()
    )
    return r.data[0]["id"]


def list_quizzes_for_folder(company_id: str, folder_access: str):
    """Kuis yang tersedia untuk karyawan sesuai cakupan folder aksesnya."""
    client = get_client()
    r = (
        client.table("quizzes")
        .select("id, title, folder_path, passing_score, created_at")
        .eq("company_id", company_id)
        .like("folder_path", f"{folder_access}%")
        .order("created_at", desc=True)
        .execute()
    )
    return r.data


def get_quiz(quiz_id: str):
    client = get_client()
    r = client.table("quizzes").select("*").eq("id", quiz_id).execute()
    return r.data[0] if r.data else None


def save_quiz_attempt(
    quiz_id: str,
    user_email: str,
    company_id: str,
    score: int,
    total: int,
    passed: bool,
    answers: list,
):
    client = get_client()
    client.table("quiz_attempts").insert(
        {
            "quiz_id": quiz_id,
            "user_email": user_email.strip().lower(),
            "company_id": company_id,
            "score": score,
            "total": total,
            "passed": passed,
            "answers": answers,
        }
    ).execute()


def get_user_quiz_attempts(user_email: str):
    client = get_client()
    r = (
        client.table("quiz_attempts")
        .select("*, quizzes(title)")
        .eq("user_email", user_email.strip().lower())
        .order("created_at", desc=True)
        .execute()
    )
    return r.data


# ==========================================
# DRAF DOKUMEN AI (audit trail, TIDAK masuk RAG)
# ==========================================
def save_ai_draft(company_id: str, requested_by: str, title: str, content: str) -> str:
    client = get_client()
    r = (
        client.table("ai_drafts")
        .insert(
            {
                "company_id": company_id,
                "requested_by": requested_by,
                "title": title,
                "content": content,
            }
        )
        .execute()
    )
    return r.data[0]["id"]


# ==========================================
# ANALISIS DATA -- dokumen dengan data terstruktur (XLSX)
# ==========================================
def list_structured_documents(company_id: str, folder_prefix: str = "/"):
    """Dokumen yang punya structured_data (hasil upload XLSX) -- untuk halaman Analisis Data."""
    client = get_client()
    r = (
        client.table("documents")
        .select("id, title, folder_path, structured_data")
        .eq("company_id", company_id)
        .like("folder_path", f"{folder_prefix}%")
        .not_.is_("structured_data", "null")
        .execute()
    )
    return r.data


# ==========================================
# BRANDING PERUSAHAAN (logo, template surat)
# ==========================================
def get_company_branding(company_id: str) -> dict:
    client = get_client()
    r = (
        client.table("companies")
        .select("logo_url, docx_template_url")
        .eq("id", company_id)
        .execute()
    )
    return r.data[0] if r.data else {}


def upload_company_logo(company_id: str, file_bytes: bytes, filename: str) -> str:
    client = get_client()
    storage_path = f"{company_id}/branding/logo_{filename}"
    client.storage.from_("company-files").upload(
        storage_path, file_bytes, {"upsert": "true"}
    )
    signed = client.storage.from_("company-files").create_signed_url(
        storage_path, 3600 * 24 * 365
    )
    url = signed.get("signedURL") or signed.get("signed_url")
    client.table("companies").update({"logo_url": url}).eq("id", company_id).execute()
    return url


def upload_company_template(company_id: str, file_bytes: bytes, filename: str) -> str:
    client = get_client()
    storage_path = f"{company_id}/branding/template_{filename}"
    client.storage.from_("company-files").upload(
        storage_path, file_bytes, {"upsert": "true"}
    )
    signed = client.storage.from_("company-files").create_signed_url(
        storage_path, 3600 * 24 * 365
    )
    url = signed.get("signedURL") or signed.get("signed_url")
    client.table("companies").update({"docx_template_url": url}).eq(
        "id", company_id
    ).execute()
    return url


def fetch_file_bytes(url: str) -> bytes:
    """Ambil isi file dari URL (Supabase signed URL) sebagai bytes -- dipakai untuk baca logo/template kembali."""
    import requests

    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.content


# ==========================================
# UPLOAD MEDIA LAPORAN KERJAAN (dipindah dari app.py -> jaga app.py tidak bicara ke Supabase langsung)
# ==========================================
def upload_report_media(
    company_id: str, user_email: str, file_bytes: bytes, filename: str
) -> str:
    client = get_client()
    storage_path = f"{company_id}/reports/{user_email}/{filename}"
    client.storage.from_("company-files").upload(
        storage_path, file_bytes, {"upsert": "true"}
    )
    signed = client.storage.from_("company-files").create_signed_url(
        storage_path, 3600 * 24 * 30
    )
    return signed.get("signedURL") or signed.get("signed_url")


def get_full_document_content(document_id: str) -> str:
    """Gabungkan SEMUA chunk milik 1 dokumen (urut) -- untuk kebutuhan ekstraksi
    data yang butuh isi lengkap, bukan cuma chunk paling mirip dari vector search."""
    client = get_client()
    r = (
        client.table("document_chunks")
        .select("content, chunk_index")
        .eq("document_id", document_id)
        .order("chunk_index")
        .execute()
    )
    return "\n".join(c["content"] for c in r.data)
