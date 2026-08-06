from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import db
import ai

app = FastAPI()


class ChatRequest(BaseModel):
    message: str
    user_id: str


class TeamRequest(BaseModel):
    emails: str
    folder: str


class SettingsRequest(BaseModel):
    companyName: str

# Fungsi helper untuk mendapatkan company_id dan folder_access dari db.py


def get_user_context(email: str):
    user = db.get_user(email)
    if user:
        return user["company_id"], user["folder_access"]
    # Fallback aman agar Vercel tidak crash saat database belum ada user ini
    return "12345-dummy-company-id", "/"


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        company_id, folder_access = get_user_context(request.user_id)

        # 1. Ubah teks pertanyaan menjadi vector menggunakan Gemini (dari ai.py)
        query_embedding = ai.embed_text(request.message)

        # 2. Cari dokumen terkait di Supabase (dari db.py)
        matched_docs = db.search_documents(
            query_embedding=query_embedding,
            company_id=company_id,
            match_count=3,
            folder_prefix=folder_access
        )

        # 3. Filter dokumen jika user spesifik meminta video (dari ai.py)
        matched_docs = ai.filter_docs_by_intent(request.message, matched_docs)

        # 4. Generate jawaban akhir menggunakan Gemini (dari ai.py)
        if not matched_docs:
            jawaban = "Maaf, informasi tersebut belum tersedia di database dokumen kami."
            source_title = None
            source_type = None
        else:
            jawaban = ai.generate_answer(request.message, matched_docs)
            source_title = matched_docs[0].get("title")
            source_type = matched_docs[0].get(
                "metadata", {}).get("tipe_file", "Dokumen PDF")

        return {
            "reply": jawaban,
            "sourceTitle": source_title,
            "sourceType": source_type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/files")
async def files_endpoint(path: str = "/"):
    try:
        company_id, _ = get_user_context("admin@kopinusantara.com")

        # Tarik folder dan dokumen ASLI dari Supabase (dari db.py)
        folders_raw = db.list_child_folders(company_id, path)
        docs, count = db.list_documents_in_folder(
            company_id, path, page=1, page_size=50)

        # Format array folder untuk diterima oleh File Manager Next.js
        folders_formatted = []
        for f in folders_raw:
            name = [p for p in f.split("/") if p][-1]
            folders_formatted.append({"path": f, "name": name})

        return {
            "folders": folders_formatted,
            "files": docs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/team")
async def add_team(req: TeamRequest):
    try:
        company_id, _ = get_user_context("admin@kopinusantara.com")
        emails_list = [e.strip() for e in req.emails.split("\n") if e.strip()]

        # Simpan user baru ASLI ke Supabase (dari db.py)
        passwords = db.add_users_bulk(emails_list, req.folder, company_id)

        if passwords:
            return {"status": "success", "message": f"{len(passwords)} karyawan berhasil ditambahkan ke folder {req.folder}!"}
        return {"status": "error", "message": "Tidak ada email valid yang ditambahkan."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard")
async def dashboard_endpoint():
    try:
        company_id, _ = get_user_context("admin@kopinusantara.com")

        # Tarik perhitungan statistik ASLI dari Supabase
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
    except Exception as e:
        return {"stats": [{"label": "Total Dokumen", "value": 0}, {"label": "Total Karyawan", "value": 0}], "recent": []}
