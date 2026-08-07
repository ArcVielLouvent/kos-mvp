from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from . import db
from . import ai
from . import auth
# Impor modul untuk mendekode JWT dari auth atau gunakan helper bawaan Anda
# Di sini kita asumsikan auth.py memiliki fungsi get_email_from_token

app = FastAPI()

app.include_router(auth.router)


class ChatRequest(BaseModel):
    message: str


class TeamRequest(BaseModel):
    emails: str
    folder: str


class SettingsRequest(BaseModel):
    companyName: str

# ====================================================================
# HELPER: MENDAPATKAN EMAIL & KONTEKS DARI HEADER SECARA OTOMATIS
# ====================================================================


def get_current_user_context(authorization: str = Header(None)):
    """
    Membaca token JWT dari header secara dinamis untuk mengidentifikasi user.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Akses ditolak. Token autentikasi tidak valid atau tidak ditemukan."
        )

    token = authorization.split(" ")[1]

    try:
        # Panggil fungsi decoder dari auth.py milik Anda untuk mengambil email dari JWT
        email = auth.get_email_from_token(token)
    except Exception:
        raise HTTPException(
            status_code=401, detail="Token kedaluwarsa atau tidak sah.")

    user = db.get_user(email)
    if user:
        return user["company_id"], user["folder_access"], email

    raise HTTPException(
        status_code=404,
        detail="Profil akun Anda tidak ditemukan di dalam database sistem."
    )

# ====================================================================
# ENDPOINTS (SEMUA SUDAH DINAMIS TANPA HARDCODED EMAIL)
# ====================================================================


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest, context: tuple = Depends(get_current_user_context)):
    try:
        company_id, folder_access, _ = context
        query_embedding = ai.embed_text(request.message)

        matched_docs = db.search_documents(
            query_embedding=query_embedding,
            company_id=company_id,
            match_count=3,
            folder_prefix=folder_access
        )

        matched_docs = ai.filter_docs_by_intent(request.message, matched_docs)

        if not matched_docs:
            jawaban = "Maaf, informasi tersebut belum tersedia di database dokumen kami."
            source_title = None
            source_type = None
        else:
            jawaban = ai.generate_answer(request.message, matched_docs)
            source_title = matched_docs[0].get("title")
            source_type = matched_docs[0].get(
                "metadata", {}).get("tipe_file", "Dokumen PDF")

        return {"reply": jawaban, "sourceTitle": source_title, "sourceType": source_type}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/files")
async def files_endpoint(path: str = "/", context: tuple = Depends(get_current_user_context)):
    try:
        company_id, _, _ = context
        folders_raw = db.list_child_folders(company_id, path)
        docs, _ = db.list_documents_in_folder(
            company_id, path, page=1, page_size=50)

        folders_formatted = [{"path": f, "name": [
            p for p in f.split("/") if p][-1]} for f in folders_raw]
        return {"folders": folders_formatted, "files": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/team")
async def add_team(req: TeamRequest, context: tuple = Depends(get_current_user_context)):
    try:
        company_id, _, _ = context
        emails_list = [e.strip() for e in req.emails.split("\n") if e.strip()]
        passwords = db.add_users_bulk(emails_list, req.folder, company_id)

        if passwords:
            return {"status": "success", "message": f"{len(passwords)} karyawan berhasil ditambahkan!"}
        return {"status": "error", "message": "Tidak ada email valid yang ditambahkan."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard")
async def dashboard_endpoint(context: tuple = Depends(get_current_user_context)):
    try:
        company_id, _, _ = context
        _, doc_count = db.list_documents_in_folder(
            company_id, "/", page_size=1)
        users = db.list_managed_users(company_id, "/", "SuperAdmin")
        folders = db.get_unique_folders(company_id)

        return {
            "stats": [
                {"label": "Total Dokumen", "value": doc_count},
                {"label": "Total Karyawan", "value": len(
                    users) if users else 0},
                {"label": "Total Folder", "value": len(
                    folders) if folders else 0},
                {"label": "Status Sistem", "value": "Aktif"}
            ],
            "recent": []
        }
    except Exception:
        return {"stats": [{"label": "Total Dokumen", "value": 0}, {"label": "Total Karyawan", "value": 0}], "recent": []}
