import os
import secrets
import bcrypt
from supabase import create_client, Client


def get_client() -> Client:
    """
    Inisialisasi Client Supabase Admin (Bypass RLS)
    Menggunakan SUPABASE_SERVICE_ROLE_KEY agar aman dari error RLS 42501.
    """
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise ValueError(
            "Environment variable SUPABASE_URL atau SUPABASE_SERVICE_ROLE_KEY belum di-set di Vercel!")
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


def get_fresh_file_url(stored_url: str, ttl_seconds: int = 3600 * 24 * 7) -> str:
    """PERBAIKAN BUG: signed URL Supabase Storage SELALU ada batas waktu
    (tidak bisa dibikin permanen) -- URL yang disimpan langsung di kolom
    file_url pas upload bakal kedaluwarsa cepat atau lambat, bikin error
    'File not found' / InvalidJWT 'exp claim timestamp check failed' saat
    dokumen dibuka lama setelah upload (dokumen upload awal cuma dikasih
    7 hari, sebagian lain 30-365 hari -- semua akan expired juga akhirnya).

    Fungsi ini AMBIL storage_path dari signed URL yang tersimpan (path-nya
    tetap valid walau TOKEN di URL itu sudah expired), lalu generate
    signed URL BARU yang fresh. Dipanggil setiap kali file_url mau
    dikirim ke frontend (bukan cuma sekali pas upload), jadi dokumen lama
    otomatis "sembuh" sendiri tanpa perlu migrasi/backfill data lama."""
    if not stored_url or "/object/sign/" not in stored_url:
        return stored_url  # bukan signed URL Supabase (mis. link YouTube) -- kembalikan apa adanya

    import re
    import urllib.parse

    match = re.search(r"/object/sign/([^/]+)/([^?]+)", stored_url)
    if not match:
        return stored_url
    bucket, encoded_path = match.group(1), match.group(2)
    storage_path = urllib.parse.unquote(encoded_path)

    try:
        client = get_client()
        signed = client.storage.from_(bucket).create_signed_url(storage_path, ttl_seconds)
        fresh_url = signed.get("signedURL") or signed.get("signed_url")
        return fresh_url or stored_url
    except Exception:
        return stored_url  # gagal re-sign (mis. file storage-nya memang sudah dihapus) -- kembalikan URL lama, biar error-nya jelas kelihatan di frontend daripada disembunyikan


def refresh_file_urls(items: list, key: str = "file_url") -> list:
    """Helper buat refresh file_url di banyak baris sekaligus (list dokumen,
    lampiran form, dst) -- item tanpa file_url dilewati begitu saja."""
    for item in items:
        if item.get(key):
            item[key] = get_fresh_file_url(item[key])
    return items


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
        {"password": hash_password(new_password),
         "must_change_password": False}
    ).eq("email", email.strip().lower()).execute()


# ==========================================
# KARYAWAN
# ==========================================
def add_users_bulk(
    emails: list, folder_access: str, company_id: str, position_title: str = None,
    manager_email: str = None,
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
                "manager_email": (manager_email or "").strip().lower() or None,
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
    manager_email: str = None,
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
            "manager_email": (manager_email or "").strip().lower() or None,
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
                3600 * 24 * 30,  # 30 hari -- di-refresh otomatis tiap dibaca lewat db.refresh_file_urls(), TTL ini cuma jaring pengaman tambahan
            )
            file_url = signed.get("signedURL") or signed.get("signed_url")
        except Exception as e:
            # Sengaja TIDAK ditelan diam-diam -- tampilkan biar bisa didiagnosis.
            # Dokumen tetap tersimpan (bisa dicari & dijawab AI), cuma tanpa file
            # asli untuk didownload.
            print(
                f"Peringatan: '{title}' gagal upload ke Storage, dokumen tetap tersimpan "
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


def delete_folder_and_contents(company_id: str, folder_path: str) -> dict:
    """Hapus folder + seluruh isinya (dokumen & subfolder) secara rekursif.

    SOAL KARYAWAN YANG AKSESNYA KE FOLDER INI: percobaan pertama saya
    auto-pindahkan mereka ke folder INDUK -- tapi itu ternyata keliru,
    karena folder induk SELALU lebih luas cakupannya daripada folder yang
    dihapus (dan kalau yang dihapus itu folder ROOT, induknya jadi "/" --
    akses PENUH ke SELURUH perusahaan). Auto-pindah seperti itu berarti
    menaikkan hak akses karyawan secara diam-diam tanpa persetujuan
    eksplisit Admin, yang justru lebih berbahaya daripada sekadar akses
    yang jadi kosong.

    Jadi SEKARANG: folder_access karyawan yang terdampak TIDAK diubah
    sama sekali (tetap menunjuk ke path yang sudah tidak ada -- secara
    de facto mereka jadi tidak lihat apa-apa di folder itu, TAPI tidak
    ada eskalasi izin yang tidak disengaja). Fungsi ini cuma MENDETEKSI
    dan MELAPORKAN siapa saja yang terdampak, supaya Admin sadar dan bisa
    assign ulang secara manual & sengaja lewat halaman Manajemen Tim.
    Daftar karyawan juga menandai folder yang sudah tidak ada (lihat
    list_all_folder_paths + endpoint /api/team/users)."""
    client = get_client()
    folder_path = normalize_folder(folder_path)

    affected_r = (
        client.table("users")
        .select("email")
        .eq("company_id", company_id)
        .ilike("folder_access", f"{folder_path}%")
        .execute()
    )
    affected_emails = [u["email"] for u in affected_r.data]

    client.table("documents").delete().eq("company_id", company_id).ilike(
        "folder_path", f"{folder_path}%"
    ).execute()
    client.table("folders").delete().eq("company_id", company_id).ilike(
        "path", f"{folder_path}%"
    ).execute()

    return {"affected_users": affected_emails}


def list_all_folder_paths(company_id: str) -> set:
    """Semua path folder yang BENAR-BENAR masih ada -- gabungan dari tabel
    folders (folder eksplisit, termasuk yang kosong) + folder_path yang
    kepakai dokumen (folder implisit). Dipakai buat nandain di Manajemen
    Tim kalau folder_access seorang karyawan sudah tidak ada lagi (mis.
    foldernya sudah dihapus admin lain, atau typo)."""
    client = get_client()
    paths = {"/"}
    folders_r = client.table("folders").select("path").eq("company_id", company_id).execute()
    for f in folders_r.data:
        paths.add(f["path"])
    docs_r = client.table("documents").select("folder_path").eq("company_id", company_id).execute()
    for d in docs_r.data:
        if d.get("folder_path"):
            paths.add(d["folder_path"])
    return paths


def list_child_folders(company_id: str, parent_path: str) -> list:
    parent_path = normalize_folder(parent_path)
    client = get_client()
    folders = (
        client.table("folders").select("path").eq(
            "company_id", company_id).execute()
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
            first_segment = path[len(parent_path):].split("/")[0]
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


def get_folder_tree_stats(company_id: str, folder_path: str) -> dict:
    """Total dokumen + subfolder di SELURUH pohon folder (rekursif ke bawah),
    BEDA dengan list_documents_in_folder yang cuma hitung isi langsung di
    1 folder itu saja. Dipakai kartu ringkasan folder di Dashboard supaya
    tidak menyesatkan (mis. folder dengan 0 dokumen langsung tapi punya
    5 subfolder isi 40 dokumen sebelumnya kelihatan 'kosong')."""
    client = get_client()
    folder_path = normalize_folder(folder_path)

    doc_r = (
        client.table("documents")
        .select("id", count="exact")
        .eq("company_id", company_id)
        .ilike("folder_path", f"{folder_path}%")
        .execute()
    )
    folder_r = (
        client.table("folders")
        .select("path", count="exact")
        .eq("company_id", company_id)
        .ilike("path", f"{folder_path}%")
        .neq("path", folder_path)  # jangan hitung folder itu sendiri sebagai "subfolder"
        .execute()
    )
    return {"doc_count": doc_r.count or 0, "subfolder_count": folder_r.count or 0}


def count_all_documents(company_id: str) -> int:
    """Total dokumen di SELURUH folder milik company -- dipakai Dashboard.
    Beda dengan list_documents_in_folder yang sengaja cuma hitung 1 folder
    spesifik (buat kebutuhan navigasi File Manager)."""
    client = get_client()
    r = (
        client.table("documents")
        .select("id", count="exact")
        .eq("company_id", company_id)
        .execute()
    )
    return r.count or 0

# ---------- CHAT HISTORY ----------


def create_chat_session(user_email: str, company_id: str) -> str:
    client = get_client()
    r = (
        client.table("chat_sessions")
        .insert({"user_email": user_email, "company_id": company_id})
        .execute()
    )
    return r.data[0]["id"]


def list_chat_sessions(user_email: str, page: int = 1, page_size: int = 30):
    """Dipaginasi -- tanpa ini, user yang sudah lama pakai KOS (ratusan
    percakapan) bakal me-load SEMUA riwayat chat sekaligus di sidebar."""
    client = get_client()
    offset = (page - 1) * page_size
    r = (
        client.table("chat_sessions")
        .select("*", count="exact")
        .eq("user_email", user_email)
        .order("updated_at", desc=True)
        .range(offset, offset + page_size - 1)
        .execute()
    )
    return r.data, (r.count or 0)


def get_chat_messages(session_id: str):
    client = get_client()
    r = (
        client.table("chat_messages")
        .select("*")
        .eq("session_id", session_id)
        .order("created_at")
        .execute()
    )
    messages = r.data
    # PERBAIKAN BUG "File not found": file_url di kolom "sources" (JSONB)
    # dibekukan sejak pesan itu dikirim -- kalau chat-nya dibuka lagi
    # berhari-hari/berbulan kemudian, URL itu sudah pasti kedaluwarsa.
    # Di-refresh di sini tiap riwayat chat dimuat, BUKAN pas disimpan
    # (supaya tidak perlu update kolom sources di DB tiap kali).
    for m in messages:
        if m.get("sources"):
            m["sources"] = refresh_file_urls(m["sources"])
    return messages


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


def count_all_folders(company_id: str) -> int:
    """Total folder company-wide dari tabel folders -- termasuk folder kosong,
    beda dengan get_unique_folders yang cuma ngitung folder yang punya dokumen."""
    client = get_client()
    r = (
        client.table("folders")
        .select("path", count="exact")
        .eq("company_id", company_id)
        .execute()
    )
    return r.count or 0


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


def move_folder_cascade(company_id: str, old_path: str, dest_parent_path: str):
    """Pindahkan folder (dan seluruh isinya secara kaskade) ke bawah folder
    tujuan lain -- beda dengan rename_folder_cascade yang cuma ganti nama
    di tempat, ini mengganti parent-nya juga. Dipakai oleh fitur
    'Pindahkan' ala Google Drive/OneDrive di File Manager."""
    client = get_client()
    old_path = normalize_folder(old_path)
    dest_parent_path = normalize_folder(dest_parent_path)

    parts = [p for p in old_path.split("/") if p]
    if not parts:
        return
    folder_name = parts[-1]
    new_path = dest_parent_path + folder_name + "/"

    if new_path == old_path or new_path.startswith(old_path):
        # Cegah memindahkan folder ke dalam dirinya sendiri (loop tak terhingga).
        raise ValueError("Tidak bisa memindahkan folder ke dalam dirinya sendiri.")

    create_folder(company_id, dest_parent_path)

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

    create_folder(company_id, new_path)


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
            "email, role, folder_access, position_title, permission_level, created_at, full_name, phone_number"
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


def update_user_profile(email: str, full_name: str = None, phone_number: str = None):
    """Data diri formal karyawan (nama lengkap, no. telepon) -- diisi/diedit
    Admin/SuperAdmin dari halaman Direktori Karyawan, terpisah dari data
    akses (role/folder/permission)."""
    client = get_client()
    updates = {}
    if full_name is not None:
        updates["full_name"] = full_name.strip() or None
    if phone_number is not None:
        updates["phone_number"] = phone_number.strip() or None
    if updates:
        client.table("users").update(updates).eq("email", email.strip().lower()).execute()


def update_user_manager(email: str, manager_email: str = None):
    """Atur/ubah atasan langsung (dipisah dari role sistem -- role ngatur
    akses fitur, manager_email ngatur siapa lihat laporan siapa)."""
    client = get_client()
    client.table("users").update(
        {"manager_email": (manager_email or "").strip().lower() or None}
    ).eq("email", email.strip().lower()).execute()


# ==========================================
# PENGATURAN PERUSAHAAN (toggle level company, diatur Owner)
# ==========================================
def get_company_settings(company_id: str) -> dict:
    client = get_client()
    r = (
        client.table("company_settings")
        .select("*")
        .eq("company_id", company_id)
        .execute()
    )
    if r.data:
        return r.data[0]
    # default kalau belum pernah disetting -- semua fitur opsional OFF dulu
    return {
        "company_id": company_id,
        "poin_pelanggaran_enabled": False,
        "notify_atasan_enabled": False,
        "attendance_deadline_hour": 24,
        "attendance_deadline_minute": 0,
    }


def update_company_settings(company_id: str, **fields) -> dict:
    client = get_client()
    payload = {"company_id": company_id, **{k: v for k, v in fields.items() if v is not None}}
    client.table("company_settings").upsert(payload, on_conflict="company_id").execute()
    return get_company_settings(company_id)


# ==========================================
# KEHADIRAN (Form Kehadiran harian)
# ==========================================
def check_in_attendance(user_email: str, company_id: str) -> dict:
    """Idempotent -- kalau hari ini sudah check-in, balikin record yang sudah
    ada (bukan bikin baris baru), supaya karyawan gak bisa check-in dobel."""
    client = get_client()
    today = _today_str()

    existing = (
        client.table("attendance")
        .select("*")
        .eq("user_email", user_email.strip().lower())
        .eq("company_id", company_id)
        .eq("attendance_date", today)
        .execute()
    )
    if existing.data:
        return existing.data[0]

    r = (
        client.table("attendance")
        .insert(
            {
                "user_email": user_email.strip().lower(),
                "company_id": company_id,
                "attendance_date": today,
            }
        )
        .execute()
    )
    return r.data[0]


def get_today_attendance(user_email: str, company_id: str):
    client = get_client()
    r = (
        client.table("attendance")
        .select("*")
        .eq("user_email", user_email.strip().lower())
        .eq("company_id", company_id)
        .eq("attendance_date", _today_str())
        .execute()
    )
    return r.data[0] if r.data else None


def get_attendance_status_today(company_id: str) -> dict:
    """Dipakai Dashboard Owner/atasan: siapa aja yang SUDAH dan BELUM
    check-in hari ini. SuperAdmin dikecualikan dari daftar 'belum' by
    default (Owner tidak wajib lapor), tapi tetap boleh check-in kalau mau."""
    client = get_client()
    today = _today_str()

    users_r = (
        client.table("users")
        .select("email, role, position_title, manager_email")
        .eq("company_id", company_id)
        .neq("role", "SuperAdmin")
        .execute()
    )
    attendance_r = (
        client.table("attendance")
        .select("user_email")
        .eq("company_id", company_id)
        .eq("attendance_date", today)
        .execute()
    )
    checked_in_emails = {a["user_email"] for a in attendance_r.data}

    sudah, belum = [], []
    for u in users_r.data:
        (sudah if u["email"] in checked_in_emails else belum).append(u)

    return {"sudah": sudah, "belum": belum, "total": len(users_r.data)}


def _today_str() -> str:
    """Tanggal 'hari ini' dalam WIB (UTC+7), BUKAN UTC -- kalau pakai
    tanggal UTC mentah, antara jam 00:00-06:59 WIB sistem masih mengira
    'hari ini' itu tanggal kemarin (karena UTC baru ganti tanggal jam
    07:00 WIB), bikin submission Form Kehadiran/Lapor Kerjaan dini hari
    bisa salah tercatat di tanggal yang salah."""
    return _now_wib().strftime("%Y-%m-%d")


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


def list_quizzes_for_folder(company_id: str, folder_access: str, page: int = 1, page_size: int = 20):
    """Kuis yang tersedia untuk karyawan sesuai cakupan folder aksesnya -- dipaginasi."""
    client = get_client()
    offset = (page - 1) * page_size
    r = (
        client.table("quizzes")
        .select("id, title, folder_path, passing_score, created_at", count="exact")
        .eq("company_id", company_id)
        .like("folder_path", f"{folder_access}%")
        .order("created_at", desc=True)
        .range(offset, offset + page_size - 1)
        .execute()
    )
    return r.data, (r.count or 0)


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
    """Dokumen yang punya structured_data (hasil upload XLSX) -- untuk halaman
    Insight & Grafik. folder_prefix di-normalize dulu (pastikan format
    '/path/' konsisten) sebelum dipakai LIKE prefix-match, supaya SEMUA
    subfolder di bawahnya ikut tersisir -- bukan cuma folder root."""
    client = get_client()
    folder_prefix = normalize_folder(folder_prefix)
    r = (
        client.table("documents")
        .select("id, title, folder_path, structured_data")
        .eq("company_id", company_id)
        .like("folder_path", f"{folder_prefix}%")
        .not_.is_("structured_data", "null")
        .execute()
    )
    return r.data


def get_document_by_id(doc_id: str):
    """Ambil 1 dokumen lengkap (termasuk structured_data) -- dipakai
    halaman Insight/Grafik buat eksplorasi 1 dataset secara interaktif."""
    client = get_client()
    r = client.table("documents").select("*").eq("id", doc_id).execute()
    return r.data[0] if r.data else None


def combine_structured_datasets(company_id: str, doc_ids: list = None, folder_path: str = None) -> dict:
    """Gabungkan BEBERAPA dataset XLSX jadi 1 tabel buat divisualisasikan
    bareng di Insight & Grafik -- entah dipilih manual (doc_ids) atau
    ambil semua isi 1 folder (folder_path).

    PENTING: penggabungan ini MEKANIS (nyambung baris, tanpa AI) dan
    CUMA berhasil kalau semua file yang dipilih punya struktur kolom yang
    SAMA PERSIS (mis. beberapa laporan bulanan dengan kolom identik).
    Kalau strukturnya beda-beda (mis. katalog KPI per departemen yang
    kolomnya beda-beda), fungsi ini SENGAJA menolak dengan pesan jelas --
    BUKAN maksa gabung jadi tabel yang tidak masuk akal. Untuk kasus itu,
    arahkan user ke fitur 'kompilasi data' di Chat KOS yang memang pakai
    AI buat ekstraksi lintas dokumen dengan struktur berbeda."""
    if folder_path:
        docs = list_structured_documents(company_id, folder_path)
    else:
        docs = [get_document_by_id(did) for did in (doc_ids or [])]
        docs = [d for d in docs if d and d.get("structured_data")]

    if not docs:
        raise ValueError("Tidak ada dataset terstruktur yang cocok di pilihan ini.")

    per_file = []  # (title, columns_set, rows)
    for doc in docs:
        sheets = doc.get("structured_data") or []
        if not sheets or not sheets[0].get("rows"):
            continue
        rows = sheets[0]["rows"]
        columns = list(rows[0].keys())
        per_file.append((doc["title"], columns, rows))

    if not per_file:
        raise ValueError("Dataset yang dipilih tidak punya baris data.")

    if len(per_file) == 1:
        title, columns, rows = per_file[0]
        return {"columns": columns, "rows": rows, "sources": [title], "merged": False}

    first_columns = set(per_file[0][1])
    mismatched = [title for title, cols, _ in per_file if set(cols) != first_columns]
    if mismatched:
        raise ValueError(
            f"Kolom di file-file ini TIDAK seragam (beda struktur), jadi tidak bisa digabung otomatis "
            f"jadi 1 tabel/chart. File yang strukturnya beda: {', '.join(mismatched[:3])}"
            f"{', dst' if len(mismatched) > 3 else ''}. "
            f"Kalau tetap mau menyatukan data dari file-file berbeda struktur, coba fitur "
            f"'kompilasi data' di Chat KOS (AI yang ekstraksi field-nya, bukan penggabungan mekanis)."
        )

    columns = per_file[0][1]
    merged_rows = []
    for title, _, rows in per_file:
        for r in rows:
            merged_rows.append({**r, "_sumber_file": title})
    return {
        "columns": columns + ["_sumber_file"],
        "rows": merged_rows,
        "sources": [title for title, _, _ in per_file],
        "merged": True,
    }


def list_documents_content_in_scope(company_id: str, folder_prefix: str = "/", limit: int = 25):
    """Ambil dokumen (id+title+content, TANPA structured_data) dalam cakupan
    folder tertentu -- dipakai fitur kompilasi lintas-dokumen di Chat KOS
    (mis. "buatkan daftar dari semua CV di folder ini"). BEDA dengan RAG
    biasa yang cuma ambil top-K hasil similarity search -- ini exhaustive
    (semua dokumen di scope, dibatasi `limit` demi biaya/waktu, urut
    terbaru dulu). Kalau folder berisi lebih dari `limit` dokumen, caller
    WAJIB kasih tahu user cuma sebagian yang diproses (penting untuk
    keputusan HR supaya tidak diam-diam kelewat data)."""
    client = get_client()
    r = (
        client.table("documents")
        .select("id, title, content, folder_path", count="exact")
        .eq("company_id", company_id)
        .like("folder_path", f"{normalize_folder(folder_prefix)}%")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return r.data, (r.count or 0)


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
    if not r.data:
        return {}
    branding = r.data[0]
    if branding.get("logo_url"):
        branding["logo_url"] = get_fresh_file_url(branding["logo_url"])
    if branding.get("docx_template_url"):
        branding["docx_template_url"] = get_fresh_file_url(branding["docx_template_url"])
    return branding


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
    client.table("companies").update(
        {"logo_url": url}).eq("id", company_id).execute()
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


def reprocess_missing_structured_data(company_id: str) -> dict:
    """Proses ulang dokumen .xlsx yang SUDAH terupload tapi structured_data-nya
    kosong (gagal diekstrak dulu, mis. karena bug parsing lama, atau file
    dengan baris judul di atas tabel) -- supaya dokumen lama ikut muncul di
    Insight & Grafik tanpa perlu upload ulang manual satu-satu. Dipanggil
    dari tombol 'Proses Ulang Dataset Lama' di halaman Insight."""
    try:
        from . import ai
    except ImportError:
        import ai
    import tempfile
    import os as _os

    client = get_client()
    r = (
        client.table("documents")
        .select("id, title, file_url")
        .eq("company_id", company_id)
        .ilike("title", "%.xlsx")
        .is_("structured_data", "null")
        .execute()
    )
    candidates = r.data
    fixed, still_failed = [], []

    for doc in candidates:
        if not doc.get("file_url"):
            still_failed.append(f"{doc['title']}: tidak ada file_url tersimpan")
            continue
        try:
            fresh_url = get_fresh_file_url(doc["file_url"])
            file_bytes = fetch_file_bytes(fresh_url)
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name
            try:
                structured = ai.extract_xlsx_structured(tmp_path)
            finally:
                _os.unlink(tmp_path)

            if structured:
                client.table("documents").update({"structured_data": structured}).eq("id", doc["id"]).execute()
                fixed.append(doc["title"])
            else:
                still_failed.append(f"{doc['title']}: tetap tidak ada tabel yang bisa dikenali (mungkin bukan data tabular, misalnya isinya narasi/katalog teks)")
        except Exception as e:
            still_failed.append(f"{doc['title']}: {str(e)}")

    return {"checked": len(candidates), "fixed": fixed, "still_failed": still_failed}
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


def count_all_chat_sessions(company_id: str) -> int:
    client = get_client()
    r = (
        client.table("chat_sessions")
        .select("id", count="exact")
        .eq("company_id", company_id)
        .execute()
    )
    return r.count or 0


def list_all_chat_sessions_for_company(company_id: str, month: int = None, year: int = None):
    """Riwayat percakapan company-wide (semua user, bukan cuma yang login),
    dipakai halaman Riwayat Percakapan di Dashboard. Bisa difilter bulan/tahun."""
    client = get_client()
    r = (
        client.table("chat_sessions")
        .select("*")
        .eq("company_id", company_id)
        .order("updated_at", desc=True)
        .execute()
    )
    rows = r.data
    if not month and not year:
        return rows
    filtered = []
    for row in rows:
        ts = row.get("created_at") or ""
        if len(ts) < 7:
            continue
        try:
            row_year, row_month = int(ts[0:4]), int(ts[5:7])
        except ValueError:
            continue
        if year and row_year != year:
            continue
        if month and row_month != month:
            continue
        filtered.append(row)
    return filtered


def get_recent_activity(company_id: str, limit: int = 8) -> list:
    """Gabungan aktivitas terbaru company-wide (dokumen diunggah, chat dimulai,
    karyawan ditambahkan) -- dibaca dari created_at yang sudah ada di masing-masing
    tabel, tanpa perlu tabel events terpisah."""
    client = get_client()
    activity = []

    docs = (
        client.table("documents")
        .select("title, created_at")
        .eq("company_id", company_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    for d in docs.data:
        activity.append({
            "type": "document",
            "title": f"Dokumen diunggah: {d['title']}",
            "who": "",
            "time": d.get("created_at", ""),
        })

    sessions = (
        client.table("chat_sessions")
        .select("title, user_email, created_at")
        .eq("company_id", company_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    for s in sessions.data:
        activity.append({
            "type": "chat",
            "title": f"Percakapan baru: {s['title'] or 'Tanpa judul'}",
            "who": s.get("user_email", ""),
            "time": s.get("created_at", ""),
        })

    users = (
        client.table("users")
        .select("email, created_at")
        .eq("company_id", company_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    for u in users.data:
        activity.append({
            "type": "employee",
            "title": f"Anggota baru: {u['email']}",
            "who": "",
            "time": u.get("created_at", ""),
        })

    activity.sort(key=lambda a: a["time"] or "", reverse=True)
    return activity[:limit]


# ============================================================
# FORM BUILDER -- Form Kehadiran & Lapor Kerjaan (digabung jadi satu,
# ala Google Forms: field bisa diatur bebas, upload video/audio/dokumen
# bisa wajib/opsional per field).
# ============================================================
def get_daily_template(company_id: str):
    """Ambil template form harian aktif (is_daily=true, is_active=true).
    Kalau belum pernah dibuat sama sekali, return None -- caller yang
    memutuskan mau bikinin default atau bilang 'Admin belum atur form'."""
    client = get_client()
    r = (
        client.table("form_templates")
        .select("*")
        .eq("company_id", company_id)
        .eq("is_daily", True)
        .eq("is_active", True)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return r.data[0] if r.data else None


def get_template_with_fields(template_id: str):
    client = get_client()
    tpl = client.table("form_templates").select("*").eq("id", template_id).execute()
    if not tpl.data:
        return None
    fields = (
        client.table("form_fields")
        .select("*")
        .eq("template_id", template_id)
        .order("sort_order")
        .execute()
    )
    return {**tpl.data[0], "fields": fields.data}


def save_daily_template(company_id: str, created_by: str, name: str, description: str, fields: list):
    """Simpan (buat/replace) template form harian + field-fieldnya sekaligus.
    Field lama ditimpa total supaya form-builder-nya sesederhana mungkin di
    sisi frontend (kirim seluruh daftar field final, bukan diff)."""
    client = get_client()

    existing = get_daily_template(company_id)
    if existing:
        template_id = existing["id"]
        client.table("form_templates").update({
            "name": name,
            "description": description,
            "updated_at": "now()",
        }).eq("id", template_id).execute()
        client.table("form_fields").delete().eq("template_id", template_id).execute()
    else:
        created = (
            client.table("form_templates")
            .insert({
                "company_id": company_id,
                "name": name,
                "description": description,
                "is_daily": True,
                "is_active": True,
                "created_by": created_by,
            })
            .execute()
        )
        template_id = created.data[0]["id"]

    rows = []
    for i, f in enumerate(fields):
        rows.append({
            "template_id": template_id,
            "label": f["label"],
            "field_type": f.get("field_type", "short_text"),
            "options": f.get("options") or [],
            "file_kind": f.get("file_kind") or "any",
            "is_required": bool(f.get("is_required", False)),
            "sort_order": i,
        })
    if rows:
        client.table("form_fields").insert(rows).execute()

    return get_template_with_fields(template_id)


def get_today_submission(template_id: str, user_email: str, company_id: str):
    client = get_client()
    r = (
        client.table("form_submissions")
        .select("*")
        .eq("template_id", template_id)
        .eq("user_email", user_email.strip().lower())
        .eq("company_id", company_id)
        .eq("submission_date", _today_str())
        .execute()
    )
    if not r.data:
        return None
    submission = r.data[0]
    answers = (
        client.table("form_submission_answers")
        .select("*")
        .eq("submission_id", submission["id"])
        .execute()
    )
    submission["answers"] = refresh_file_urls(answers.data, key="file_url")
    return submission


def _now_wib():
    """Jam sekarang di WIB (UTC+7) -- KOS dipakai perusahaan Indonesia, dan
    Admin mengisi 'Batas Waktu Lapor Harian' di Pengaturan dalam jam lokal
    (mis. 17 = jam 5 sore WIB), BUKAN UTC. Sebelumnya kode ini salah
    membandingkan jam UTC mentah terhadap deadline yang diisi dalam jam
    lokal -- akibatnya reminder nyaris tidak PERNAH terkirim di jam kerja
    (selisih 7 jam bikin kondisinya baru terpenuhi dini hari WIB, saat
    tidak ada yang buka dashboard), dan kalau deadline dibiarkan default
    24, kondisinya malah TIDAK PERNAH terpenuhi sama sekali sepanjang
    hari (jam cuma 0-23, tidak pernah >= 24). Ini penyebab persis laporan
    'klik tombol pengingat, tidak ada notif sama sekali'."""
    from datetime import datetime, timezone, timedelta
    return datetime.now(timezone.utc) + timedelta(hours=7)


def submit_daily_form(
    template_id: str, user_email: str, company_id: str, answers: list, deadline_hour: int = 24, deadline_minute: int = 0,
):
    """Idempotent per hari (unique constraint template+user+tanggal) --
    kalau sudah pernah isi hari ini, jawaban lama ditimpa (mengganti isian,
    bukan bikin submission dobel)."""
    client = get_client()
    now = _now_wib()
    status = "late" if (now.hour, now.minute) >= (deadline_hour, deadline_minute) else "on_time"

    existing = (
        client.table("form_submissions")
        .select("id")
        .eq("template_id", template_id)
        .eq("user_email", user_email.strip().lower())
        .eq("company_id", company_id)
        .eq("submission_date", _today_str())
        .execute()
    )
    if existing.data:
        submission_id = existing.data[0]["id"]
        client.table("form_submission_answers").delete().eq("submission_id", submission_id).execute()
        client.table("form_submissions").update({"status": status, "submitted_at": "now()"}).eq(
            "id", submission_id
        ).execute()
    else:
        created = (
            client.table("form_submissions")
            .insert({
                "template_id": template_id,
                "company_id": company_id,
                "user_email": user_email.strip().lower(),
                "submission_date": _today_str(),
                "status": status,
            })
            .execute()
        )
        submission_id = created.data[0]["id"]

    rows = []
    for a in answers:
        rows.append({
            "submission_id": submission_id,
            "field_id": a["field_id"],
            "value_text": a.get("value_text"),
            "file_url": a.get("file_url"),
            "file_kind": a.get("file_kind"),
        })
    if rows:
        client.table("form_submission_answers").insert(rows).execute()

    return get_today_submission(template_id, user_email, company_id)


def get_submission_status_today(company_id: str, template_id: str) -> dict:
    """Dipakai Dashboard Owner/atasan -- gabungan dari get_attendance_status_today
    lama: siapa SUDAH dan BELUM isi form hari ini. SuperAdmin dikecualikan
    dari daftar 'belum' (tidak wajib lapor), tetap boleh isi kalau mau.

    Ikut mengembalikan deadline_hour + is_past_deadline supaya frontend
    bisa membedakan 'belum isi (masih wajar, belum lewat jam batas)' vs
    'belum isi (SUDAH terlambat)' -- sebelumnya daftar 'belum' ini selalu
    tampil mengkhawatirkan (ikon jam oranye) sejak jam 00:00, padahal jam
    batas waktunya mungkin baru sore."""
    client = get_client()
    today = _today_str()
    settings = get_company_settings(company_id)
    deadline_hour = settings.get("attendance_deadline_hour", 24)
    deadline_minute = settings.get("attendance_deadline_minute", 0)
    now = _now_wib()
    is_past_deadline = (now.hour, now.minute) >= (deadline_hour, deadline_minute)

    users_r = (
        client.table("users")
        .select("email, role, position_title, manager_email")
        .eq("company_id", company_id)
        .neq("role", "SuperAdmin")
        .execute()
    )
    subs_r = (
        client.table("form_submissions")
        .select("user_email, status, submitted_at")
        .eq("company_id", company_id)
        .eq("template_id", template_id)
        .eq("submission_date", today)
        .execute()
    )
    by_email = {s["user_email"]: s for s in subs_r.data}

    sudah, belum = [], []
    for u in users_r.data:
        sub = by_email.get(u["email"])
        if sub:
            sudah.append({**u, "status": sub["status"], "submitted_at": sub["submitted_at"]})
        else:
            belum.append(u)

    return {
        "sudah": sudah,
        "belum": belum,
        "total": len(users_r.data),
        "deadline_hour": deadline_hour,
        "is_past_deadline": is_past_deadline,
    }


def get_user_submissions(user_email: str, limit: int = 50):
    """Riwayat isian form satu karyawan (menggantikan get_user_reports lama
    untuk halaman Direktori Karyawan / Riwayat)."""
    client = get_client()
    subs_r = (
        client.table("form_submissions")
        .select("*")
        .eq("user_email", user_email.strip().lower())
        .order("submission_date", desc=True)
        .limit(limit)
        .execute()
    )
    submissions = subs_r.data
    ids = [s["id"] for s in submissions]
    if ids:
        answers_r = (
            client.table("form_submission_answers")
            .select("*")
            .in_("submission_id", ids)
            .execute()
        )
        by_submission: dict = {}
        for a in answers_r.data:
            by_submission.setdefault(a["submission_id"], []).append(a)
        for s in submissions:
            s["answers"] = refresh_file_urls(by_submission.get(s["id"], []), key="file_url")
    return submissions


def upload_form_file(company_id: str, user_email: str, field_id: str, file_bytes: bytes, filename: str) -> str:
    client = get_client()
    storage_path = f"{company_id}/form-submissions/{user_email}/{_today_str()}/{field_id}_{filename}"
    client.storage.from_("company-files").upload(
        storage_path, file_bytes, {"upsert": "true"}
    )
    signed = client.storage.from_("company-files").create_signed_url(
        storage_path, 3600 * 24 * 30
    )
    return signed.get("signedURL") or signed.get("signed_url")


# ============================================================
# AKSES BERJENJANG -- rantai atasan (bukan cuma 1 level), dibangun dari
# manager_email yang sudah ada di tabel users. Dipakai untuk eskalasi
# notifikasi berantai: bawahan -> atasan langsung -> atasan dari atasan -> dst.
# ============================================================
def get_manager_chain(email: str, max_depth: int = 10) -> list:
    """Balikin daftar email atasan dari yang paling dekat sampai paling
    atas, berhenti kalau mentok (tidak ada manager_email lagi) atau kalau
    ketemu loop (data salah input) supaya tidak infinite loop."""
    client = get_client()
    chain = []
    seen = {email.strip().lower()}
    current = email.strip().lower()
    for _ in range(max_depth):
        r = client.table("users").select("manager_email").eq("email", current).execute()
        if not r.data:
            break
        manager = r.data[0].get("manager_email")
        if not manager or manager in seen:
            break
        chain.append(manager)
        seen.add(manager)
        current = manager
    return chain


# ============================================================
# NOTIFIKASI -- pengingat belum isi form + eskalasi berjenjang ke rantai
# atasan (mengikuti company_settings.notify_atasan_enabled).
# ============================================================
def create_notification(
    company_id: str, recipient_email: str, notif_type: str, title: str, message: str,
    related_user_email: str = None, related_date: str = None,
):
    """Idempotent (select-then-insert, sama gaya dengan check_in_attendance)
    -- 1 notifikasi per (recipient, tipe, related_user, tanggal), aman
    dipanggil berulang tanpa nge-spam kotak masuk kalau job pengingat
    jalan tiap beberapa jam."""
    client = get_client()
    recipient_email = recipient_email.strip().lower()
    related_user_email = (related_user_email or "").strip().lower() or None
    related_date = related_date or _today_str()

    q = (
        client.table("notifications")
        .select("id")
        .eq("company_id", company_id)
        .eq("recipient_email", recipient_email)
        .eq("type", notif_type)
        .eq("related_date", related_date)
    )
    q = q.eq("related_user_email", related_user_email) if related_user_email else q.is_("related_user_email", "null")
    if q.execute().data:
        return  # sudah ada notifikasi yang sama hari ini, jangan dobel

    client.table("notifications").insert({
        "company_id": company_id,
        "recipient_email": recipient_email,
        "type": notif_type,
        "title": title,
        "message": message,
        "related_user_email": related_user_email,
        "related_date": related_date,
    }).execute()


def list_notifications(recipient_email: str, unread_only: bool = False, limit: int = 30):
    client = get_client()
    q = (
        client.table("notifications")
        .select("*")
        .eq("recipient_email", recipient_email.strip().lower())
        .order("created_at", desc=True)
        .limit(limit)
    )
    if unread_only:
        q = q.eq("is_read", False)
    return q.execute().data


def list_notifications_paginated(recipient_email: str, page: int = 1, page_size: int = 20):
    """Dipakai halaman khusus /dashboard/notifications -- return
    (list, total_count) supaya bisa dipaginasi, beda dengan list_notifications
    yang cuma buat dropdown bell (flat, dibatasi limit kecil)."""
    client = get_client()
    offset = (page - 1) * page_size
    r = (
        client.table("notifications")
        .select("*", count="exact")
        .eq("recipient_email", recipient_email.strip().lower())
        .order("created_at", desc=True)
        .range(offset, offset + page_size - 1)
        .execute()
    )
    return r.data, (r.count or 0)


def delete_notification(notif_id: str, recipient_email: str):
    client = get_client()
    client.table("notifications").delete().eq("id", notif_id).eq(
        "recipient_email", recipient_email.strip().lower()
    ).execute()


def delete_read_notifications(recipient_email: str):
    """'Hapus yang sudah dibaca' -- bulk clear, tidak menyentuh yang belum dibaca."""
    client = get_client()
    client.table("notifications").delete().eq(
        "recipient_email", recipient_email.strip().lower()
    ).eq("is_read", True).execute()


def count_unread_notifications(recipient_email: str) -> int:
    client = get_client()
    r = (
        client.table("notifications")
        .select("id", count="exact")
        .eq("recipient_email", recipient_email.strip().lower())
        .eq("is_read", False)
        .execute()
    )
    return r.count or 0


def mark_notification_read(notif_id: str, recipient_email: str):
    client = get_client()
    client.table("notifications").update({"is_read": True}).eq("id", notif_id).eq(
        "recipient_email", recipient_email.strip().lower()
    ).execute()


def mark_all_notifications_read(recipient_email: str):
    client = get_client()
    client.table("notifications").update({"is_read": True}).eq(
        "recipient_email", recipient_email.strip().lower()
    ).eq("is_read", False).execute()


def run_late_submission_check(company_id: str) -> dict:
    """Job pengingat -- dipanggil berulang tiap beberapa jam (lewat cron
    Railway atau trigger manual Owner/Admin). Kirim reminder ke karyawan
    yang belum isi form hari ini SETELAH lewat attendance_deadline_hour,
    dan kalau notify_atasan_enabled aktif, eskalasi berantai ke SELURUH
    rantai atasannya (bukan cuma atasan langsung)."""
    settings = get_company_settings(company_id)
    template = get_daily_template(company_id)
    if not template:
        return {"checked": 0, "reminded": 0, "escalated": 0, "note": "Belum ada form harian yang diatur."}

    now = _now_wib()
    deadline_hour = settings.get("attendance_deadline_hour", 24)
    deadline_minute = settings.get("attendance_deadline_minute", 0)
    if (now.hour, now.minute) < (deadline_hour, deadline_minute):
        return {"checked": 0, "reminded": 0, "escalated": 0, "note": "Belum lewat batas waktu hari ini."}

    status = get_submission_status_today(company_id, template["id"])
    reminded, escalated, errors = 0, 0, []

    for u in status["belum"]:
        email = u["email"]
        nama = u.get("position_title") or email

        # PERBAIKAN BUG: sebelumnya loop ini tanpa try/except -- kalau 1
        # user gagal diproses (mis. create_notification error karena data
        # aneh), SELURUH fungsi crash dan tidak ada satupun reminder yang
        # terkirim, padahal 4 user lain seharusnya tetap bisa. Sekarang 1
        # user gagal cuma dicatat di errors, user lain tetap diproses.
        try:
            create_notification(
                company_id, email, "reminder",
                title="Belum isi Form Kehadiran/Lapor Kerjaan hari ini",
                message=f"Kamu belum mengisi form harian hari ini. Segera isi ya, {nama}.",
                related_user_email=email,
            )
            reminded += 1

            if settings.get("notify_atasan_enabled"):
                for manager_email in get_manager_chain(email):
                    create_notification(
                        company_id, manager_email, "escalation",
                        title="Bawahan belum isi form harian",
                        message=f"{email} belum mengisi Form Kehadiran/Lapor Kerjaan hari ini.",
                        related_user_email=email,
                    )
                    escalated += 1
        except Exception as e:
            errors.append(f"{email}: {str(e)}")

    result = {"checked": status["total"], "reminded": reminded, "escalated": escalated}
    if errors:
        result["errors"] = errors
    return result


def list_all_company_ids() -> list:
    """Dipakai job cron global (semua company sekaligus) -- bukan trigger
    manual 1 company oleh Admin."""
    client = get_client()
    r = client.table("companies").select("id").execute()
    return [c["id"] for c in r.data]


def run_late_submission_check_all_companies() -> dict:
    """Jalankan run_late_submission_check ke SEMUA company sekaligus --
    ini yang dipanggil scheduler otomatis (Railway Cron Job), BUKAN yang
    dipanggil tombol manual Admin (itu tetap per-company lewat
    run_late_submission_check biasa). 1 company gagal tidak menggagalkan
    company lain."""
    results = {}
    for company_id in list_all_company_ids():
        try:
            results[company_id] = run_late_submission_check(company_id)
        except Exception as e:
            results[company_id] = {"error": str(e)}
    return results


# ============================================================
# POIN PELANGGARAN -- SKEMA SAJA. Klien belum minta fitur ini diaktifkan
# (baru rencana), jadi belum ada endpoint/UI yang dipasang untuk ini.
# Fungsi di bawah disiapkan supaya nanti tinggal dicolokin, tanpa migrasi
# ulang, begitu dikonfirmasi ke klien.
# ============================================================
def add_violation_point(company_id: str, user_email: str, points: int, reason: str, given_by: str):
    client = get_client()
    client.table("violation_points").insert({
        "company_id": company_id,
        "user_email": user_email.strip().lower(),
        "points": points,
        "reason": reason,
        "given_by": given_by,
    }).execute()


def get_user_violation_points(user_email: str) -> int:
    client = get_client()
    r = (
        client.table("violation_points")
        .select("points")
        .eq("user_email", user_email.strip().lower())
        .execute()
    )
    return sum(row["points"] for row in r.data)


# ============================================================
# BROADCAST PENGUMUMAN VIA EMAIL
# ============================================================
def send_email(to_email: str, subject: str, body: str) -> bool:
    """Kirim 1 email lewat SMTP (env var SMTP_HOST/PORT/USER/PASS/FROM di
    Railway). Return False (bukan raise) kalau gagal supaya 1 email gagal
    tidak menggagalkan broadcast ke seluruh perusahaan."""
    import smtplib
    from email.mime.text import MIMEText

    host = os.environ.get("SMTP_HOST")
    port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")
    from_addr = os.environ.get("SMTP_FROM", smtp_user or "")

    if not host or not smtp_user or not smtp_pass:
        return False

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_email

    try:
        with smtplib.SMTP(host, port, timeout=15) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_addr, [to_email], msg.as_string())
        return True
    except Exception:
        return False


def send_broadcast_announcement(
    company_id: str, sender_email: str, subject: str, body: str, target_scope: str = "/",
) -> dict:
    client = get_client()
    q = client.table("users").select("email").eq("company_id", company_id)
    if target_scope and target_scope != "/":
        q = q.like("folder_access", f"{target_scope}%")
    recipients = [u["email"] for u in q.execute().data]

    sent_count = 0
    for email in recipients:
        if send_email(email, subject, body):
            sent_count += 1
        create_notification(
            company_id, email, "broadcast",
            title=subject, message=body,
            related_user_email=sender_email, related_date=_today_str(),
        )

    client.table("announcements").insert({
        "company_id": company_id,
        "sender_email": sender_email,
        "subject": subject,
        "body": body,
        "target_scope": target_scope,
        "recipient_count": sent_count,
    }).execute()

    return {"recipients": len(recipients), "emails_sent": sent_count}


def list_announcements(company_id: str, limit: int = 30):
    client = get_client()
    r = (
        client.table("announcements")
        .select("*")
        .eq("company_id", company_id)
        .order("sent_at", desc=True)
        .limit(limit)
        .execute()
    )
    return r.data


# ============================================================
# KLASIFIKASI JENIS FILE -- helper terpusat, dipakai di semua tempat yang
# perlu tahu jenis lampiran (Lapor Kerjaan, Form Kehadiran, dst).
#
# BUG LAMA yang diperbaiki di sini: logika sebelumnya cuma ngecek
# ext in ["mp4","mov"] -> "video", SELAIN itu langsung dianggap "audio"
# TANPA PENGECUALIAN -- jadi foto (.jpg/.png) dan dokumen (.pdf/.docx)
# ikut kelabelan "audio" dan tampilannya di frontend jadi rusak (coba
# di-render sebagai <audio>, gagal total). Sekarang eksplisit 4 kategori:
# image / video / audio / document, dengan fallback "document" (bukan
# "audio") untuk ekstensi yang tidak dikenal.
# ============================================================
def classify_file_kind(filename: str) -> str:
    ext = (filename or "").rsplit(".", 1)[-1].lower() if "." in (filename or "") else ""
    if ext in ("jpg", "jpeg", "png", "webp", "gif", "bmp", "heic", "heif"):
        return "image"
    if ext in ("mp4", "mov", "webm", "avi", "mkv", "3gp"):
        return "video"
    if ext in ("mp3", "wav", "aac", "ogg", "flac", "m4a", "aiff"):
        return "audio"
    return "document"  # fallback aman -- dokumen/PDF/lain-lain, BUKAN audio


# ============================================================
# FORM LAPOR KERJAAN -- BEDA dari Form Kehadiran. Ini laporan detail
# pekerjaan harian dengan BARIS DINAMIS ala Google Sheet (karyawan bebas
# nambah baris sendiri, 1 baris = 1 item pekerjaan), lampiran opsional
# per baris (foto/dokumen/video, boleh kosong), tanggal/jam/nama
# OTOMATIS terisi dari user_email + report_date + submitted_at (bukan
# field yang diketik manual).
# ============================================================
def get_today_work_report(user_email: str, company_id: str):
    client = get_client()
    r = (
        client.table("work_reports")
        .select("*")
        .eq("user_email", user_email.strip().lower())
        .eq("company_id", company_id)
        .eq("report_date", _today_str())
        .execute()
    )
    if not r.data:
        return None
    report = r.data[0]
    rows = (
        client.table("work_report_rows")
        .select("*")
        .eq("report_id", report["id"])
        .order("row_order")
        .execute()
    )
    report["rows"] = refresh_file_urls(rows.data, key="attachment_url")
    return report


def save_work_report(user_email: str, company_id: str, rows: list):
    """Idempotent per hari (1 report per user per tanggal, UNIQUE constraint)
    -- baris lama ditimpa total dengan baris final yang dikirim (konsisten
    dengan pola submit_daily_form: kirim seluruh daftar baris, bukan diff).
    Lampiran per baris OPSIONAL -- baris tanpa attachment_url tetap sah
    selama description-nya ada."""
    client = get_client()
    user_email = user_email.strip().lower()
    today = _today_str()

    existing = (
        client.table("work_reports")
        .select("id")
        .eq("user_email", user_email)
        .eq("company_id", company_id)
        .eq("report_date", today)
        .execute()
    )
    if existing.data:
        report_id = existing.data[0]["id"]
        client.table("work_report_rows").delete().eq("report_id", report_id).execute()
        client.table("work_reports").update({"updated_at": "now()"}).eq("id", report_id).execute()
    else:
        created = (
            client.table("work_reports")
            .insert({
                "company_id": company_id,
                "user_email": user_email,
                "report_date": today,
            })
            .execute()
        )
        report_id = created.data[0]["id"]

    row_payload = []
    for i, row in enumerate(rows):
        if not (row.get("description") or "").strip():
            continue  # baris kosong (belum diisi user) -- jangan disimpan
        row_payload.append({
            "report_id": report_id,
            "row_order": i,
            "description": row["description"].strip(),
            "time_note": (row.get("time_note") or "").strip() or None,
            "attachment_url": row.get("attachment_url"),
            "attachment_kind": row.get("attachment_kind"),
        })
    if row_payload:
        client.table("work_report_rows").insert(row_payload).execute()

    return get_today_work_report(user_email, company_id)


def get_user_work_reports(user_email: str, limit: int = 30):
    """Riwayat laporan kerjaan milik satu karyawan (dipakai untuk halaman
    'Riwayat Laporan Saya' karyawan itu sendiri, DAN halaman Direktori
    Karyawan buat Admin/SuperAdmin lihat laporan bawahannya)."""
    client = get_client()
    reports_r = (
        client.table("work_reports")
        .select("*")
        .eq("user_email", user_email.strip().lower())
        .order("report_date", desc=True)
        .limit(limit)
        .execute()
    )
    reports = reports_r.data
    ids = [r["id"] for r in reports]
    if ids:
        rows_r = (
            client.table("work_report_rows")
            .select("*")
            .in_("report_id", ids)
            .order("row_order")
            .execute()
        )
        by_report: dict = {}
        for row in rows_r.data:
            by_report.setdefault(row["report_id"], []).append(row)
        for r in reports:
            r["rows"] = refresh_file_urls(by_report.get(r["id"], []), key="attachment_url")
    return reports


def upload_work_report_attachment(
    company_id: str, user_email: str, row_key: str, file_bytes: bytes, filename: str
) -> dict:
    client = get_client()
    storage_path = f"{company_id}/work-reports/{user_email}/{_today_str()}/{row_key}_{filename}"
    client.storage.from_("company-files").upload(
        storage_path, file_bytes, {"upsert": "true"}
    )
    signed = client.storage.from_("company-files").create_signed_url(
        storage_path, 3600 * 24 * 30
    )
    url = signed.get("signedURL") or signed.get("signed_url")
    return {"url": url, "kind": classify_file_kind(filename)}


# ============================================================
# IMPORT/UPDATE KARYAWAN LEWAT EXCEL -- owner/admin upload 1 file .xlsx
# berisi banyak baris data karyawan sekaligus (email, nama, jabatan,
# folder akses, atasan, dst), TIDAK perlu isi form satu-satu di UI.
# Baris dengan email yang SUDAH ADA akan di-UPDATE (bukan bikin akun baru
# lagi), baris dengan email baru akan dibuatkan akun baru (password
# sementara, sama seperti alur tambah karyawan manual).
# ============================================================
ALLOWED_IMPORT_ROLES = {"Karyawan", "Admin"}  # SuperAdmin sengaja TIDAK boleh lewat import file (proteksi eskalasi privilege tidak sengaja)


def import_users_from_rows(rows: list, company_id: str) -> dict:
    client = get_client()

    existing_r = client.table("users").select("email").eq("company_id", company_id).execute()
    existing_emails = {u["email"] for u in existing_r.data}

    created, updated, errors = [], [], []
    new_records = []

    for i, row in enumerate(rows, start=2):  # baris 2 = baris pertama setelah header di Excel
        email = (row.get("email") or "").strip().lower()
        if not email or "@" not in email:
            errors.append(f"Baris {i}: kolom email kosong/tidak valid, dilewati.")
            continue

        role = (row.get("role") or "Karyawan").strip().title()
        if role not in ALLOWED_IMPORT_ROLES:
            errors.append(f"Baris {i} ({email}): role '{role}' tidak didukung lewat import (cuma Karyawan/Admin), dianggap Karyawan.")
            role = "Karyawan"

        folder_access = normalize_folder(row.get("folder_access") or "/")
        full_name = (row.get("full_name") or "").strip() or None
        position_title = (row.get("position_title") or "").strip() or None
        phone_number = (row.get("phone_number") or "").strip() or None
        manager_email = (row.get("manager_email") or "").strip().lower() or None
        permission_level = (row.get("permission_level") or "crud").strip().lower()
        if permission_level not in ("crud", "read_only"):
            permission_level = "crud"

        create_folder(company_id, folder_access)

        if email in existing_emails:
            # UPDATE -- SENGAJA tidak menyentuh kolom password/must_change_password
            # sama sekali, supaya login karyawan yang sudah ada tidak ke-reset.
            update_payload = {
                "role": role,
                "folder_access": folder_access,
                "full_name": full_name,
                "position_title": position_title,
                "phone_number": phone_number,
                "manager_email": manager_email,
            }
            if role == "Admin":
                update_payload["permission_level"] = permission_level
            try:
                client.table("users").update(update_payload).eq("email", email).eq("company_id", company_id).execute()
                updated.append(email)
            except Exception as e:
                errors.append(f"Baris {i} ({email}): gagal update -- {str(e)}")
        else:
            temp_pw = secrets.token_urlsafe(6)
            new_records.append({
                "email": email,
                "role": role,
                "folder_access": folder_access,
                "password": hash_password(temp_pw),
                "company_id": company_id,
                "must_change_password": True,
                "full_name": full_name,
                "position_title": position_title,
                "phone_number": phone_number,
                "manager_email": manager_email,
                "permission_level": permission_level if role == "Admin" else "crud",
                "_temp_password": temp_pw,  # dibuang sebelum insert, cuma buat dikembalikan ke caller
            })

    temp_passwords = {}
    if new_records:
        for r in new_records:
            temp_passwords[r["email"]] = r.pop("_temp_password")
        try:
            client.table("users").insert(new_records).execute()
            created.extend([r["email"] for r in new_records])
        except Exception as e:
            errors.append(f"Gagal membuat {len(new_records)} akun baru -- {str(e)}")

    return {
        "created": created,
        "updated": updated,
        "errors": errors,
        "temporary_passwords": temp_passwords,
    }
