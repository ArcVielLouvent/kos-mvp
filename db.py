import streamlit as st
from supabase import create_client, Client


def get_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def insert_document(
    title: str,
    content: str,
    embedding: list,
    folder_path: str = "/",
    metadata: dict = None,
):
    """Simpan satu dokumen universal (teks, video, audio, dll) beserta metadatanya."""
    client = get_client()

    if metadata is None:
        metadata = {}

    return (
        client.table("documents")
        .insert(
            {
                "title": title,
                "content": content,
                "folder_path": folder_path,
                "embedding": embedding,
                "metadata": metadata,
            }
        )
        .execute()
    )


def search_documents(
    query_embedding: list, match_count: int = 3, folder_prefix: str = "/"
):
    """Cari dokumen paling relevan menggunakan pgvector, difilter berdasarkan folder."""
    client = get_client()
    response = client.rpc(
        "match_documents",
        {
            "query_embedding": query_embedding,
            "match_count": match_count,
            "folder_prefix": folder_prefix,
        },
    ).execute()
    return response.data


def get_user(email: str):
    """Mengambil data pengguna saat login (Role dan Izin Folder)."""
    client = get_client()
    response = client.table("users").select("*").eq("email", email).execute()

    if response.data:
        # Mengembalikan dict berisi email, role, folder_access
        return response.data[0]
    return None


def add_users_bulk(emails: list, folder_access: str):
    """Menambahkan banyak karyawan sekaligus (Metode Paste & Pick)."""
    client = get_client()

    # Membersihkan spasi dan memastikan email tidak kosong
    records = [
        {"email": email.strip(), "role": "Karyawan", "folder_access": folder_access}
        for email in emails
        if email.strip()
    ]

    if not records:
        return None

    # Menggunakan upsert agar sistem menimpa data jika email sudah pernah didaftarkan
    return client.table("users").upsert(records, on_conflict="email").execute()


def get_unique_folders():
    """Mengambil daftar folder unik yang sudah ada di database untuk menu Dropdown."""
    client = get_client()
    response = client.table("documents").select("folder_path").execute()

    # Mengumpulkan folder unik, dan memastikan Root ('/') selalu ada di pilihan
    folders = {"/"}
    if response.data:
        for item in response.data:
            if item.get("folder_path"):
                folders.add(item["folder_path"])

    return sorted(list(folders))
