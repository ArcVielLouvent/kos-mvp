import secrets
import bcrypt
import streamlit as st
from supabase import create_client, Client


def get_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
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
    """Buat entitas perusahaan baru + akun Admin pertamanya, atomik di 1 transaksi."""
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
# KARYAWAN (Paste & Pick, per perusahaan)
# ==========================================
def add_users_bulk(emails: list, folder_access: str, company_id: str) -> dict:
    """
    Tambah banyak karyawan sekaligus.
    Return: dict {email: temp_password} untuk ditampilkan admin sekali saja.
    """
    client = get_client()
    folder_access = normalize_folder(folder_access)

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


# ---------- FILE MANAGER ----------
def create_folder(company_id: str, path: str):
    client = get_client()
    path = normalize_folder(path)
    client.table("folders").upsert(
        {"company_id": company_id, "path": path}, on_conflict="company_id,path"
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
    client = get_client()
    client.table("chat_messages").insert(
        {"session_id": session_id, "role": role, "content": content}
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
