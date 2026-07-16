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
    # CARA 1: Mengubah target kunci ke Service Role Key untuk hak akses admin internal
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
def add_users_bulk(emails: list, folder_access: str, company_id: str) -> dict:
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
            }
        )

    if records:
        client.table("users").upsert(records, on_conflict="email").execute()

    return temp_passwords


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
# DOKUMEN & RAG
# ==========================================
def insert_document(
    title: str,
    content: str,
    embedding: list,
    company_id: str,
    folder_path: str = "/",
    metadata: dict = None,
):
    client = get_client()

    create_folder(company_id, folder_path)

    # Berhasil mengeksekusi insert tanpa gangguan RLS
    return (
        client.table("documents")
        .insert(
            {
                "title": title,
                "content": content,
                "folder_path": normalize_folder(folder_path),
                "embedding": embedding,
                "metadata": metadata or {},
                "company_id": company_id,
            }
        )
        .execute()
    )


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


def list_documents_in_folder(company_id: str, folder_path: str):
    client = get_client()
    r = (
        client.table("documents")
        .select("id, title, metadata, created_at")
        .eq("company_id", company_id)
        .eq("folder_path", normalize_folder(folder_path))
        .order("created_at", desc=True)
        .execute()
    )
    return r.data


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


def add_chat_message(session_id: str, role: str, content: str):
    """Menambahkan pesan chat baru dan memperbarui timestamp sesi aktif."""
    client = get_client()
    client.table("chat_messages").insert(
        {"session_id": session_id, "role": role, "content": content}
    ).execute()

    # Bypass RLS saat memperbarui waktu aktivitas chat terakhir
    client.table("chat_sessions").update({"updated_at": "now()"}).eq(
        "id", session_id
    ).execute()


def rename_chat_session(session_id: str, new_title: str):
    """Mengubah nama/judul sesi percakapan."""
    client = get_client()
    client.table("chat_sessions").update({"title": new_title}).eq(
        "id", session_id
    ).execute()


def delete_chat_session(session_id: str):
    """Menghapus sesi percakapan (otomatis menghapus pesan terkait jika cascade aktif di DB)."""
    client = get_client()
    client.table("chat_sessions").delete().eq("id", session_id).execute()


def rename_folder_cascade(company_id: str, old_path: str, new_name: str):
    """
    Mengubah nama folder beserta seluruh sub-folder, dokumen di dalamnya,
    hingga memperbarui hak akses folder (folder_access) milik karyawan secara berantai.
    """
    client = get_client()
    old_path = normalize_folder(old_path)

    parts = [p for p in old_path.split("/") if p]
    if not parts:
        return

    parent_path = "/" + "/".join(parts[:-1]) + "/" if len(parts) > 1 else "/"
    new_path = parent_path + new_name.strip() + "/"

    # 1. Perbarui semua path di tabel folders yang berada di bawah folder tersebut
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

    # 2. Perbarui lokasi folder_path untuk semua dokumen yang terdampak
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

    # 3. Sinkronisasi hak akses folder (folder_access) karyawan agar tidak kehilangan akses
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
