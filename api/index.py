import base64
import io
import os
import re
import time
import uuid
from typing import List, Optional
import urllib.parse

import pandas as pd
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Dukung dua cara jalan: sebagai package "api" (mis. `uvicorn api.index:app`
# dari root repo) ATAU sebagai modul biasa saat root directory Railway
# diarahkan langsung ke folder api/ (mis. `uvicorn index:app`).
try:
    from . import ai, auth, db
except ImportError:  # dijalankan langsung dari dalam folder api/
    import ai
    import auth
    import db

app = FastAPI()

# ====================================================================
# CORS -- WAJIB karena frontend (Vercel) dan backend (Railway) sekarang
# berbeda domain. Set ALLOWED_ORIGINS di Railway, contoh:
# "https://kos-mvp.vercel.app,https://app.kuroteklab.com"
# Kalau env var kosong, fallback "*" (longgar, cuma untuk dev/awal setup --
# SEGERA diisi origin asli begitu domain Vercel final sudah ada).
_allowed_origins_env = os.environ.get("ALLOWED_ORIGINS", "").strip()
_allowed_origins = (
    [o.strip() for o in _allowed_origins_env.split(",") if o.strip()]
    if _allowed_origins_env
    else ["*"]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)

PAGE_SIZE_DEFAULT = 20


# ====================================================================
# MODELS
# ====================================================================
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class SessionRenameRequest(BaseModel):
    title: str


class FolderCreateRequest(BaseModel):
    folder_name: str
    current_path: str = "/"


class FolderRenameRequest(BaseModel):
    old_path: str
    new_name: str


class BulkDeleteRequest(BaseModel):
    folders: List[str] = []
    docs: List[str] = []


class MoveDocumentRequest(BaseModel):
    doc_id: str
    new_path: str


class BulkMoveRequest(BaseModel):
    folders: List[str] = []
    docs: List[str] = []
    destination: str


class YouTubeRequest(BaseModel):
    title: str
    url: str
    description: str = ""
    current_path: str = "/"


class EmployeeBulkRequest(BaseModel):
    emails: str  # teks bebas, email diekstrak via regex (sama seperti app.py)
    folder: str
    position_title: Optional[str] = None
    manager_email: Optional[str] = None  # atasan langsung -- opsional, terpisah dari role


class AdminAddRequest(BaseModel):
    email: str
    folder: str
    permission_level: str = "crud"  # "crud" | "read_only"
    position_title: Optional[str] = None
    manager_email: Optional[str] = None


class QuizAttemptRequest(BaseModel):
    answers: dict  # {"0": 2, "1": 0, ...}


class QuizGenerateRequest(BaseModel):
    folder_path: str
    source_document_id: str
    title: str
    num_questions: int = 5
    passing_score: int = 70


# ====================================================================
# HELPER AUTH -- auth.py TIDAK menerbitkan token (login cuma balikin data
# user apa adanya, disimpan penuh di localStorage "kos_user" di frontend,
# identik dengan pola st.session_state.user di app.py). Jadi identitas
# request cukup dikirim lewat header "X-User-Email", lalu kita SELALU
# ambil ulang data terbaru dari DB (bukan percaya field dari client) --
# supaya role/permission_level/folder_access yang dipakai untuk keputusan
# akses selalu yang terbaru, bukan basi dari localStorage lama.
# ====================================================================
def get_current_user_context(x_user_email: str = Header(None, alias="X-User-Email")) -> dict:
    if not x_user_email:
        raise HTTPException(
            status_code=401, detail="Akses ditolak. Sesi tidak ditemukan.")
    user = db.get_user(x_user_email)
    if not user:
        raise HTTPException(
            status_code=404, detail="Profil akun tidak ditemukan.")
    return user


# ====================================================================
# HELPER PERMISSION (identik dengan logika app.py)
# ====================================================================
def can_write(user: dict) -> bool:
    """SuperAdmin selalu bisa tulis. Admin cuma bisa kalau permission_level='crud'."""
    if user["role"] == "SuperAdmin":
        return True
    if user["role"] == "Admin":
        return user.get("permission_level", "crud") == "crud"
    return False


def is_admin_tier(user: dict) -> bool:
    return user["role"] in ("SuperAdmin", "Admin")


def require_write(user: dict):
    if not can_write(user):
        raise HTTPException(
            status_code=403,
            detail="Akun Anda bertipe read-only -- tidak bisa melakukan perubahan ini.",
        )


def require_superadmin(user: dict):
    if user["role"] != "SuperAdmin":
        raise HTTPException(status_code=403, detail="Khusus SuperAdmin.")


def base_path_for(user: dict) -> str:
    return "/" if user["role"] == "SuperAdmin" else user["folder_access"]


def to_b64(data: bytes) -> str:
    return base64.b64encode(data).decode("utf-8")


# ====================================================================
# CHAT KOS -- SESI
# ====================================================================
@app.get("/api/chat/sessions")
async def list_sessions_endpoint(user: dict = Depends(get_current_user_context)):
    return {"sessions": db.list_chat_sessions(user["email"])}


@app.post("/api/chat/sessions")
async def create_session_endpoint(user: dict = Depends(get_current_user_context)):
    session_id = db.create_chat_session(user["email"], user["company_id"])
    return {"id": session_id}


@app.get("/api/chat/sessions/{session_id}/messages")
async def get_session_messages_endpoint(
    session_id: str, user: dict = Depends(get_current_user_context)
):
    return {"messages": db.get_chat_messages(session_id)}


@app.patch("/api/chat/sessions/{session_id}")
async def rename_session_endpoint(
    session_id: str,
    req: SessionRenameRequest,
    user: dict = Depends(get_current_user_context),
):
    db.rename_chat_session(session_id, req.title)
    return {"status": "success"}


@app.delete("/api/chat/sessions/{session_id}")
async def delete_session_endpoint(
    session_id: str, user: dict = Depends(get_current_user_context)
):
    db.delete_chat_session(session_id)
    return {"status": "success"}


# ====================================================================
# CHAT KOS -- MENGIRIM PESAN (RAG + generate dokumen + analisis data)
# ====================================================================
@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest, user: dict = Depends(get_current_user_context)):
    company_id = user["company_id"]
    folder_access = user["folder_access"]
    question = req.message

    session_id = req.session_id
    if not session_id:
        session_id = db.create_chat_session(user["email"], company_id)
        db.rename_chat_session(session_id, question[:30])

    db.add_chat_message(session_id, "user", question)

    try:
        q_emb = ai.embed_text(question)
        docs = db.search_documents(
            q_emb, company_id=company_id, match_count=2, folder_prefix=folder_access
        )
        docs = ai.filter_docs_by_intent(question, docs)

        used_sources = []
        seen = set()
        mode = "chat"
        generated_files = []
        analysis_table = None
        analysis_file = None
        warning = None

        # ---------- NIAT: KOMPILASI DATA DARI BANYAK DOKUMEN ----------
        # Dicek PALING AWAL (sebelum is_generate_request) karena frasa
        # seperti "buatkan daftar/tabel" bisa tabrakan dengan kata kunci
        # "buatkan" di is_generate_request -- kompilasi harus menang di
        # kasus itu, bukan malah dianggap "buatkan dokumen karangan AI".
        if ai.is_compile_request(question):
            mode = "compile"
            scope_folder = folder_access
            docs_in_scope, total_in_scope = db.list_documents_content_in_scope(
                company_id, scope_folder, limit=25
            )
            if not docs_in_scope:
                answer = f"Tidak ada dokumen ditemukan di folder {scope_folder} untuk dikompilasi."
            else:
                columns = ai.determine_extraction_columns(question)
                compiled_rows, extract_errors = ai.extract_fields_from_documents_parallel(
                    docs_in_scope, columns
                )
                if not compiled_rows:
                    answer = "Gagal mengekstrak data dari dokumen-dokumen di folder ini. Coba lagi atau periksa apakah dokumennya berisi teks yang cukup."
                else:
                    synthesis = ai.synthesize_compiled_answer(question, columns, compiled_rows)
                    scope_note = (
                        f"(Diproses dari {len(compiled_rows)} dari total {total_in_scope} dokumen di {scope_folder}"
                        + (f", {len(extract_errors)} dokumen gagal diekstrak" if extract_errors else "")
                        + (" -- HANYA sebagian, ada lebih banyak dokumen di folder ini yang belum ikut diproses, persempit ke sub-folder untuk cakupan lebih spesifik" if total_in_scope > len(docs_in_scope) else "")
                        + ".)"
                    )
                    answer = f"{synthesis}\n\n{scope_note}"

                    display_columns = [c for c in columns]
                    analysis_table = {
                        "columns": display_columns,
                        "rows": [{c: row.get(c, "-") for c in display_columns} for row in compiled_rows],
                    }
                    xlsx_rows = [{c: row.get(c, "-") for c in display_columns} for row in compiled_rows]
                    xlsx_bytes = ai.create_xlsx_bytes("Hasil Kompilasi", xlsx_rows)
                    analysis_file = {
                        "name": "Hasil Kompilasi.xlsx",
                        "base64": to_b64(xlsx_bytes),
                    }

        # ---------- NIAT: MINTA DOKUMEN DIBUATKAN ----------
        elif ai.is_generate_request(question):
            mode = "generate"
            if not can_write(user):
                answer = "Membuat dokumen baru butuh akses tulis (CRUD). Hubungi Admin/SuperAdmin Anda."
            else:
                doc_type = ai.infer_doc_type(question)
                draft_content = ai.generate_draft_document(question, doc_type)
                answer = draft_content
                warning = (
                    "Draf berdasarkan pengetahuan umum AI -- BUKAN dokumen resmi. "
                    "Review dulu sebelum dipakai."
                )
                db.save_ai_draft(
                    company_id, user["email"], question[:60], draft_content)

                branding = db.get_company_branding(company_id)
                logo_bytes = None
                if branding.get("logo_url"):
                    try:
                        logo_bytes = db.fetch_file_bytes(branding["logo_url"])
                    except Exception:
                        logo_bytes = None

                title_for_file = question[:50].strip() or "Dokumen"

                if branding.get("docx_template_url"):
                    try:
                        template_bytes = db.fetch_file_bytes(
                            branding["docx_template_url"])
                        docx_bytes = ai.create_docx_from_template(
                            template_bytes, title_for_file, draft_content
                        )
                    except Exception:
                        docx_bytes = ai.create_docx_bytes(
                            title_for_file, draft_content, logo_bytes)
                else:
                    docx_bytes = ai.create_docx_bytes(
                        title_for_file, draft_content, logo_bytes)

                pdf_bytes = ai.create_pdf_bytes(
                    title_for_file, draft_content, logo_bytes)

                generated_files = [
                    {
                        "name": f"{title_for_file}.docx",
                        "format": "docx",
                        "base64": to_b64(docx_bytes),
                    },
                    {
                        "name": f"{title_for_file}.pdf",
                        "format": "pdf",
                        "base64": to_b64(pdf_bytes),
                    },
                ]

        # ---------- NIAT: ANALISIS DATA TERSTRUKTUR (XLSX) ----------
        elif ai.is_analysis_request(question):
            mode = "analysis"
            structured_docs = db.list_structured_documents(
                company_id, folder_access)
            if not structured_docs:
                answer = "Tidak ada data terstruktur (XLSX) yang bisa dianalisis di folder akses Anda."
            else:
                q_lower = question.lower()
                best_doc = next(
                    (
                        d
                        for d in structured_docs
                        if any(w in q_lower for w in d["title"].lower().split() if len(w) > 3)
                    ),
                    structured_docs[0],
                )
                sheets = best_doc.get("structured_data") or []
                sheet = sheets[0] if sheets else None

                if not sheet or not sheet.get("rows"):
                    answer = "Dataset ditemukan tapi tidak ada baris data untuk dianalisis."
                else:
                    df = pd.DataFrame(sheet["rows"])
                    criteria = ai.extract_analysis_criteria(
                        question, list(df.columns))

                    if criteria.get("missing_info"):
                        answer = f"Perlu klarifikasi: {criteria['missing_info']}"
                    else:
                        result_df = df.copy()
                        for flt in criteria.get("filters", []):
                            col, op, val = flt["column"], flt["operator"], flt["value"]
                            if col not in result_df.columns:
                                continue
                            if op == ">=":
                                result_df = result_df[
                                    pd.to_numeric(
                                        result_df[col], errors="coerce") >= float(val)
                                ]
                            elif op == "<=":
                                result_df = result_df[
                                    pd.to_numeric(
                                        result_df[col], errors="coerce") <= float(val)
                                ]
                            elif op == "==":
                                result_df = result_df[result_df[col].astype(
                                    str) == str(val)]
                            elif op == "contains":
                                result_df = result_df[
                                    result_df[col]
                                    .astype(str)
                                    .str.contains(str(val), case=False, na=False)
                                ]
                        sort_by = criteria.get("sort_by")
                        if sort_by and sort_by in result_df.columns:
                            result_df = result_df.sort_values(
                                sort_by, ascending=not criteria.get(
                                    "sort_desc", False)
                            )

                        answer = (
                            f"Berdasarkan data '{best_doc['title']}', ditemukan {len(result_df)} "
                            f"baris cocok dari {len(df)} baris. (Bantuan awal, bukan analisis "
                            f"profesional bersertifikat -- selalu verifikasi ulang.)"
                        )
                        records = result_df.to_dict("records")
                        analysis_table = {
                            "columns": list(result_df.columns),
                            "rows": records,
                        }
                        xlsx_bytes = ai.create_xlsx_bytes(
                            best_doc["title"][:31], records)
                        analysis_file = {
                            "name": "Hasil Analisis.xlsx",
                            "base64": to_b64(xlsx_bytes),
                        }

        # ---------- NIAT: MINTA FILE ASLI ----------
        elif ai.is_file_request(question):
            mode = "file_request"
            if docs:
                unique_docs = [
                    d
                    for d in docs
                    if d.get("file_url") and not (d["id"] in seen or seen.add(d["id"]))
                ]
                if unique_docs:
                    answer = f"Ditemukan {len(unique_docs)} dokumen yang sesuai:"
                    used_sources = unique_docs
                else:
                    answer = "Dokumen ditemukan, tapi file aslinya tidak tersedia untuk diunduh."
            else:
                answer = "Tidak ada dokumen yang cocok ditemukan di folder Anda."

        # ---------- DEFAULT: JAWAB DARI RAG ----------
        else:
            answer = ai.generate_answer(
                question, docs) if docs else "Tidak ada referensi dokumen ditemukan di folder Anda."
            if docs:
                for d in docs:
                    if d.get("file_url") and d["id"] not in seen:
                        seen.add(d["id"])
                        used_sources.append(d)

        sources_to_save = [
            {
                "id": d["id"],
                "title": d["title"],
                "file_url": d.get("file_url"),
                "metadata": d.get("metadata", {}),
            }
            for d in used_sources
        ]

        db.add_chat_message(session_id, "assistant",
                            answer, sources=sources_to_save)

        return {
            "session_id": session_id,
            "reply": answer,
            "mode": mode,
            "sources": sources_to_save,
            "generatedFiles": generated_files,
            "analysisTable": analysis_table,
            "analysisFile": analysis_file,
            "warning": warning,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Kesalahan pada mesin AI: {str(e)}")


def normalize_folder(path: str) -> str:
    """Defensif: apa pun inputnya (None, '', 'files', '/files', '/files/'),
    selalu hasilkan format konsisten dengan leading+trailing slash."""
    if not path or path.strip() in ("", "files", "root", "undefined", "null"):
        return "/"
    p = path.strip()
    if not p.startswith("/"):
        p = "/" + p
    if not p.endswith("/"):
        p += "/"
    return p

# ====================================================================
# FILE MANAGER (VERSI PENYELARASAN FINAL - AMAN & BERSIH)
# ====================================================================


@app.get("/api/files")
async def files_endpoint(
    path: str = "/",
    page: int = 1,
    page_size: int = PAGE_SIZE_DEFAULT,
    user: dict = Depends(get_current_user_context),
):
    company_id = user["company_id"]
    base_path = base_path_for(user)

    try:
        # 1. Decode karakter %20 internet menjadi spasi asli
        path = urllib.parse.unquote(path)

        # 2. Eksekusi pengaman defensif (VERSI FIX DENGAN DEBUG LOG)
        path = normalize_folder(path)
        
        # LOG DEBUG: Mengintip parameter yang masuk ke server
        print(f"[DEBUG-API] USER ROLE: {user.get('role')} | COMPANY ID: {company_id}")
        print(f"[DEBUG-API] PATH AWAL: '{path}' | BASE PATH USER: '{base_path}'")

        # Pengaman: Hanya cek startswith jika base_path user dibatasi (bukan "/")
        if base_path != "/" and not path.startswith(base_path):
            print(f"[DEBUG-API] !PERINGATAN! Path '{path}' melanggar hak akses. Reset ke '{base_path}'")
            path = base_path
        else:
            print(f"[DEBUG-API] AKURAT: Path '{path}' lolos validasi hak akses.")


        # 3. Panggil kueri asli utama Anda (BLOK TOLERANSI LEMAH SUDAH DIHAPUS TOTAL)
        folders_raw = db.list_child_folders(company_id, path)
        docs, total = db.list_documents_in_folder(
            company_id, path, page=page, page_size=page_size)

        # 4. Format data folder untuk Next.js
        folders_formatted = []
        if folders_raw:
            for f in folders_raw:
                cleaned_path = normalize_folder(f)
                name = [p for p in cleaned_path.split(
                    "/") if p][-1] if [p for p in cleaned_path.split("/") if p] else cleaned_path

                folders_formatted.append({
                    "path": cleaned_path,
                    "name": name
                })

        return {
            "folders": folders_formatted,
            "files": docs if docs is not None else [],
            "total": total if total is not None else 0,
            "page": page,
            "pageSize": page_size,
            "writable": can_write(user),
            "basePath": base_path,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/debug-user")
async def debug_user_endpoint(user: dict = Depends(get_current_user_context)):
    """Endpoint sementara untuk melihat profil user asli yang dibaca oleh Vercel dari token JWT"""
    return {
        "email_terbaca": user.get("email"),
        "role_terbaca": user.get("role"),
        "company_id_terbaca": user.get("company_id"),
        "folder_access_terbaca": user.get("folder_access")
    }


@app.get("/api/folders/children")
async def folder_children_endpoint(
    path: str = "/", user: dict = Depends(get_current_user_context)
):
    """Dipakai oleh folder-tree-picker (mis. saat memilih folder akses karyawan/admin/kuis)."""
    children = db.list_child_folders(user["company_id"], path)
    return {
        "children": [
            {"path": c, "name": c.rstrip("/").split("/")[-1]} for c in children
        ]
    }


@app.post("/api/folders")
async def create_folder_endpoint(
    req: FolderCreateRequest, user: dict = Depends(get_current_user_context)
):
    require_write(user)
    try:
        full_path = req.current_path + req.folder_name.strip() + "/"
        db.create_folder(user["company_id"], full_path)
        return {"status": "success", "message": f"Folder '{req.folder_name}' berhasil dibuat."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/folders/rename")
async def rename_folder_endpoint(
    req: FolderRenameRequest, user: dict = Depends(get_current_user_context)
):
    require_write(user)
    try:
        db.rename_folder_cascade(
            user["company_id"], req.old_path, req.new_name)
        return {"status": "success", "message": "Folder berhasil diganti nama."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/folders")
async def delete_folder_endpoint(
    path: str, user: dict = Depends(get_current_user_context)
):
    require_write(user)
    try:
        db.delete_folder_and_contents(user["company_id"], path)
        return {"status": "success", "message": "Folder berhasil dihapus secara permanen."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/documents")
async def delete_document_endpoint(
    doc_id: str, user: dict = Depends(get_current_user_context)
):
    require_write(user)
    try:
        db.delete_document(doc_id)
        return {"status": "success", "message": "Dokumen berhasil dihapus secara permanen."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/documents/bulk-delete")
async def bulk_delete_endpoint(
    req: BulkDeleteRequest, user: dict = Depends(get_current_user_context)
):
    require_write(user)
    try:
        for fpath in req.folders:
            db.delete_folder_and_contents(user["company_id"], fpath)
        for did in req.docs:
            db.delete_document(did)
        total = len(req.folders) + len(req.docs)
        return {"status": "success", "message": f"{total} item berhasil dihapus."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/documents/move")
async def move_document_endpoint(
    req: MoveDocumentRequest, user: dict = Depends(get_current_user_context)
):
    require_write(user)
    try:
        db.move_document(req.doc_id, req.new_path, user["company_id"])
        return {"status": "success", "message": "Dokumen berhasil dipindahkan."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/documents/bulk-move")
async def bulk_move_endpoint(
    req: BulkMoveRequest, user: dict = Depends(get_current_user_context)
):
    """Pindahkan banyak folder & dokumen sekaligus ke satu folder tujuan --
    ala 'Move to' di Google Drive/OneDrive. Dipakai oleh tombol 'Pindahkan
    Terpilih' di File Manager setelah pilih beberapa item (termasuk Pilih
    Semua)."""
    require_write(user)
    try:
        dest = normalize_folder(req.destination)
        for fpath in req.folders:
            db.move_folder_cascade(user["company_id"], fpath, dest)
        for did in req.docs:
            db.move_document(did, dest, user["company_id"])
        total = len(req.folders) + len(req.docs)
        return {"status": "success", "message": f"{total} item berhasil dipindahkan ke {dest}."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/youtube")
async def add_youtube_endpoint(
    req: YouTubeRequest, user: dict = Depends(get_current_user_context)
):
    require_write(user)
    try:
        company_id = user["company_id"]
        enriched = ai.describe_youtube_video(req.url.strip())
        content = f"{req.title}\n{req.description}"
        if enriched:
            content += f"\n\n{enriched}"

        chunks = ai.chunk_text(content) or [content]
        embeddings = ai.embed_chunks_parallel(chunks)

        db.insert_document_with_chunks(
            title=req.title.strip(),
            chunks=chunks,
            embeddings=embeddings,
            company_id=company_id,
            folder_path=req.current_path,
            metadata={"tipe_file": "Video YouTube"},
            external_url=req.url.strip(),
        )
        return {"status": "success", "message": f"Video '{req.title}' berhasil ditambahkan ke AI knowledge base!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------- helper: proses 1 file upload sesuai jenis (identik app.py) ----------
IMAGE_MIME = {
    "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp",
    "gif": "image/gif", "bmp": "image/bmp", "heic": "image/heic", "heif": "image/heif",
}
VIDEO_MIME = {
    "mp4": "video/mp4", "mov": "video/quicktime", "avi": "video/x-msvideo",
    "flv": "video/x-flv", "mpeg": "video/mpeg", "mpg": "video/mpeg",
    "webm": "video/webm", "wmv": "video/x-ms-wmv", "3gp": "video/3gpp",
}
AUDIO_MIME = {
    "mp3": "audio/mp3", "wav": "audio/wav", "aiff": "audio/aiff",
    "aac": "audio/aac", "ogg": "audio/ogg", "flac": "audio/flac",
}
TEXT_EXTS = {"txt", "md", "json", "xml", "html", "htm", "yaml", "yml", "log"}


def _process_single_upload(filename: str, file_bytes: bytes) -> dict:
    """Return {"chunks": [...], "tipe_file": str, "structured_data": list|None} atau raise ValueError."""
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    temp = f"/tmp/upload_{uuid.uuid4().hex}_{filename}"
    chunks = []
    tipe_file = "Dokumen"
    structured_data = None

    try:
        if ext == "csv":
            df = pd.read_csv(io.BytesIO(file_bytes))
            chunks = [ai.format_dataframe_as_text(df, sheet_name=filename)]
            tipe_file = "CSV Data"

        elif ext == "xlsx":
            with open(temp, "wb") as f:
                f.write(file_bytes)
            sheets = ai.extract_xlsx_text(temp)
            chunks = [f"Sheet: {name}\n{content}" for name, content in sheets]
            try:
                structured_data = ai.extract_xlsx_structured(temp)
            except Exception:
                structured_data = None
            tipe_file = "Spreadsheet"

        elif ext in TEXT_EXTS:
            content = file_bytes.decode("utf-8", errors="ignore")
            chunks = ai.chunk_text(content)
            tipe_file = "Teks"

        elif ext == "rtf":
            with open(temp, "wb") as f:
                f.write(file_bytes)
            content = ai.extract_rtf_text(temp)
            chunks = ai.chunk_text(content)
            tipe_file = "Dokumen RTF"

        elif ext == "pdf":
            with open(temp, "wb") as f:
                f.write(file_bytes)
            content = ai.extract_pdf_text_local(temp)
            if len(content.strip()) < 50:
                try:
                    content = ai.extract_pdf_ocr_local(temp)
                except Exception:
                    content = ""
            if len(content.strip()) < 50:
                content = ai.extract_multimodal(
                    temp, "application/pdf", filename)
            chunks = ai.chunk_text(content)
            tipe_file = "Dokumen PDF"

        elif ext == "docx":
            with open(temp, "wb") as f:
                f.write(file_bytes)
            content = ai.extract_docx_text(temp)
            chunks = ai.chunk_text(content)
            tipe_file = "Dokumen Word"

        elif ext == "pptx":
            with open(temp, "wb") as f:
                f.write(file_bytes)
            content = ai.extract_pptx_text(temp)
            chunks = ai.chunk_text(content)
            tipe_file = "Presentasi"

        elif ext == "doc":
            raise ValueError(
                "Format .doc lama belum didukung, simpan ulang sebagai .docx terlebih dahulu."
            )

        elif ext in IMAGE_MIME:
            with open(temp, "wb") as f:
                f.write(file_bytes)
            content = ai.extract_multimodal(temp, IMAGE_MIME[ext], filename)
            chunks = ai.chunk_text(content)
            tipe_file = "Gambar"

        elif ext in VIDEO_MIME or ext in AUDIO_MIME:
            with open(temp, "wb") as f:
                f.write(file_bytes)
            mime = VIDEO_MIME.get(ext) or AUDIO_MIME.get(ext)
            content = ai.extract_multimodal(temp, mime, filename)
            chunks = ai.chunk_text(content)
            tipe_file = "Media Transkrip"

        else:
            try:
                content = file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                content = ""
            if content.strip():
                chunks = ai.chunk_text(content)
                tipe_file = "Teks (format lain)"
            else:
                raise ValueError(
                    f"Format .{ext} tidak dikenali dan bukan file teks -- tidak bisa diproses."
                )

        if not chunks:
            raise ValueError("Tidak ada teks yang bisa diekstrak.")

        return {"chunks": chunks, "tipe_file": tipe_file, "structured_data": structured_data}
    finally:
        if os.path.exists(temp):
            os.remove(temp)


@app.post("/api/upload")
async def upload_files_endpoint(
    files: List[UploadFile] = File(...),
    folder_path: str = Form("/"),
    user: dict = Depends(get_current_user_context),
):
    # Karyawan (role dasar) BOLEH upload, tapi TIDAK boleh pilih folder --
    # semua otomatis masuk "Kotak Masuk" (analog inbox email), baru
    # Admin/SuperAdmin yang menyortir lewat File Manager (fitur Pindahkan
    # dokumen sudah ada). Admin/SuperAdmin tetap bebas pilih folder tujuan.
    if user["role"] == "Karyawan":
        folder_path = "/Kotak Masuk/"
    else:
        require_write(user)

    company_id = user["company_id"]

    success_count = 0
    error_logs = []

    for f in files:
        file_bytes = await f.read()
        try:
            result = _process_single_upload(f.filename, file_bytes)
            embeddings = ai.embed_chunks_parallel(result["chunks"])
            db.insert_document_with_chunks(
                title=f.filename,
                chunks=result["chunks"],
                embeddings=embeddings,
                company_id=company_id,
                folder_path=folder_path,
                metadata={"tipe_file": result["tipe_file"]},
                file_bytes=file_bytes,
                original_filename=f.filename,
                structured_data=result["structured_data"],
            )
            success_count += 1
        except ValueError as e:
            error_logs.append(f"{f.filename}: {str(e)}")
        except Exception as e:
            error_logs.append(f"{f.filename}: {str(e)}")

    if success_count and not error_logs:
        message = f"{success_count} file berhasil masuk ke {folder_path}."
    elif success_count:
        message = f"{success_count} file berhasil masuk ke {folder_path}, sebagian gagal."
    else:
        message = "Semua file gagal diproses."

    return {
        "status": "success" if success_count else "error",
        "message": message,
        "successCount": success_count,
        "errors": error_logs,
    }


# ====================================================================
# MANAJEMEN TIM
# ====================================================================
@app.post("/api/team/employees")
async def add_employees_endpoint(
    req: EmployeeBulkRequest, user: dict = Depends(get_current_user_context)
):
    require_write(user)
    email_list = re.findall(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", req.emails)
    if not email_list:
        raise HTTPException(
            status_code=400, detail="Tidak ada email valid ditemukan.")
    temp_passwords = db.add_users_bulk(
        email_list, req.folder, user["company_id"], position_title=req.position_title,
        manager_email=req.manager_email,
    )
    return {
        "status": "success",
        "message": f"{len(temp_passwords)} karyawan ditambahkan ke {req.folder}.",
        "temporaryPasswords": temp_passwords,
    }


@app.post("/api/team/admins")
async def add_admin_endpoint(
    req: AdminAddRequest, user: dict = Depends(get_current_user_context)
):
    require_superadmin(user)
    if not req.email.strip():
        raise HTTPException(status_code=400, detail="Email wajib diisi.")
    temp_pw = db.add_admin(
        req.email, req.folder, req.permission_level, user["company_id"],
        position_title=req.position_title, manager_email=req.manager_email,
    )
    return {
        "status": "success",
        "message": f"Admin '{req.email}' ditambahkan, mengelola folder {req.folder}.",
        "temporaryPassword": temp_pw,
    }


@app.get("/api/team/import-template")
async def download_import_template_endpoint(user: dict = Depends(get_current_user_context)):
    """Template .xlsx buat diisi Owner/Admin -- kolom sudah sesuai yang
    dibaca /api/team/import-excel, plus 1 baris contoh."""
    require_write(user)
    rows = [{
        "email": "contoh@perusahaan.com",
        "full_name": "Nama Lengkap",
        "position_title": "Staff Operasional",
        "phone_number": "081234567890",
        "role": "Karyawan",  # Karyawan atau Admin -- SuperAdmin tidak bisa lewat import
        "folder_access": "/Operasional/",
        "manager_email": "atasan@perusahaan.com",
        "permission_level": "crud",  # cuma dipakai kalau role=Admin -- crud atau read_only
    }]
    xlsx_bytes = ai.create_xlsx_bytes("Template Karyawan", rows)
    return {"filename": "template_import_karyawan.xlsx", "base64": to_b64(xlsx_bytes)}


@app.post("/api/team/import-excel")
async def import_users_excel_endpoint(
    file: UploadFile = File(...), user: dict = Depends(get_current_user_context)
):
    """Import/update karyawan massal dari 1 file Excel -- baris dengan email
    yang sudah ada di-UPDATE datanya (bukan dibuat akun baru), baris baru
    dibuatkan akun + password sementara (sama seperti alur tambah manual)."""
    require_write(user)
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in ("xlsx", "xls"):
        raise HTTPException(status_code=400, detail="File harus .xlsx atau .xls.")

    file_bytes = await file.read()
    try:
        df = pd.read_excel(io.BytesIO(file_bytes), dtype=str).fillna("")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Gagal membaca file Excel: {str(e)}")

    # Normalisasi nama kolom -- huruf kecil, trim spasi, spasi jadi underscore
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    if "email" not in df.columns:
        raise HTTPException(status_code=400, detail="Kolom 'email' wajib ada di file Excel.")

    rows = df.to_dict(orient="records")
    if not rows:
        raise HTTPException(status_code=400, detail="File Excel kosong, tidak ada baris data.")

    result = db.import_users_from_rows(rows, user["company_id"])
    total = len(result["created"]) + len(result["updated"])
    message = f"{len(result['created'])} akun baru dibuat, {len(result['updated'])} akun diupdate."
    if result["errors"]:
        message += f" {len(result['errors'])} baris bermasalah."
    return {"status": "success" if total else "error", "message": message, **result}


@app.get("/api/team/branding")
async def get_branding_endpoint(user: dict = Depends(get_current_user_context)):
    return db.get_company_branding(user["company_id"])


@app.post("/api/team/branding/logo")
async def upload_logo_endpoint(
    file: UploadFile = File(...), user: dict = Depends(get_current_user_context)
):
    require_write(user)
    file_bytes = await file.read()
    url = db.upload_company_logo(user["company_id"], file_bytes, file.filename)
    return {"status": "success", "logo_url": url}


@app.post("/api/team/branding/template")
async def upload_template_endpoint(
    file: UploadFile = File(...), user: dict = Depends(get_current_user_context)
):
    require_write(user)
    file_bytes = await file.read()
    url = db.upload_company_template(
        user["company_id"], file_bytes, file.filename)
    return {"status": "success", "docx_template_url": url}


# ====================================================================
# DIREKTORI KARYAWAN
# ====================================================================
@app.get("/api/team/users")
async def list_users_endpoint(user: dict = Depends(get_current_user_context)):
    users_list = db.list_managed_users(
        user["company_id"], user["folder_access"], user["role"])
    return {"users": users_list}


class UserProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    position_title: Optional[str] = None
    permission_level: Optional[str] = None  # "crud" | "read_only" -- cuma berlaku untuk role Admin
    manager_email: Optional[str] = None  # atasan langsung -- kirim "" untuk hapus atasan


@app.patch("/api/team/users/{email}/profile")
async def update_user_profile_endpoint(
    email: str, req: UserProfileUpdateRequest, user: dict = Depends(get_current_user_context)
):
    require_write(user)
    if req.full_name is not None or req.phone_number is not None:
        db.update_user_profile(email, full_name=req.full_name, phone_number=req.phone_number)
    if req.position_title is not None:
        db.update_user_position(email, req.position_title)
    if req.permission_level is not None:
        db.update_admin_permission(email, req.permission_level)
    if req.manager_email is not None:
        db.update_user_manager(email, req.manager_email)
    return {"status": "success", "message": "Data karyawan diperbarui."}


# ====================================================================
# PENGATURAN PERUSAHAAN (toggle fitur, khusus Owner/Admin)
# ====================================================================
class CompanySettingsUpdateRequest(BaseModel):
    poin_pelanggaran_enabled: Optional[bool] = None
    notify_atasan_enabled: Optional[bool] = None
    attendance_deadline_hour: Optional[int] = None


@app.get("/api/settings/company")
async def get_company_settings_endpoint(user: dict = Depends(get_current_user_context)):
    return db.get_company_settings(user["company_id"])


@app.patch("/api/settings/company")
async def update_company_settings_endpoint(
    req: CompanySettingsUpdateRequest, user: dict = Depends(get_current_user_context)
):
    if not is_admin_tier(user):
        raise HTTPException(status_code=403, detail="Khusus Admin/SuperAdmin.")
    updated = db.update_company_settings(
        user["company_id"],
        poin_pelanggaran_enabled=req.poin_pelanggaran_enabled,
        notify_atasan_enabled=req.notify_atasan_enabled,
        attendance_deadline_hour=req.attendance_deadline_hour,
    )
    return {"status": "success", "settings": updated}


# ====================================================================
# KEHADIRAN (Form Kehadiran harian)
# ====================================================================
@app.post("/api/attendance/check-in")
async def check_in_attendance_endpoint(user: dict = Depends(get_current_user_context)):
    record = db.check_in_attendance(user["email"], user["company_id"])
    return {"status": "success", "message": "Kehadiran tercatat.", "attendance": record}


@app.get("/api/attendance/today")
async def get_today_attendance_endpoint(user: dict = Depends(get_current_user_context)):
    record = db.get_today_attendance(user["email"], user["company_id"])
    return {"checkedIn": record is not None, "attendance": record}


@app.get("/api/dashboard/attendance-status")
async def dashboard_attendance_status_endpoint(user: dict = Depends(get_current_user_context)):
    if not is_admin_tier(user):
        raise HTTPException(status_code=403, detail="Khusus Admin/SuperAdmin.")
    return db.get_attendance_status_today(user["company_id"])


def require_team_view(viewer: dict, target_email: str):
    if not is_admin_tier(viewer):
        raise HTTPException(status_code=403, detail="Khusus Admin/SuperAdmin.")
    if viewer["role"] != "SuperAdmin":
        target = db.get_user(target_email)
        if not target or not target.get("folder_access", "").startswith(viewer["folder_access"]):
            raise HTTPException(
                status_code=403, detail="Di luar cakupan folder Anda.")


@app.get("/api/team/users/{email}/chat-sessions")
async def user_chat_sessions_endpoint(
    email: str, user: dict = Depends(get_current_user_context)
):
    require_team_view(user, email)
    return {"sessions": db.list_chat_sessions(email)}


@app.get("/api/team/users/{email}/reports")
async def user_reports_endpoint(email: str, user: dict = Depends(get_current_user_context)):
    require_team_view(user, email)
    return {"reports": db.get_user_reports(email)}


@app.get("/api/team/users/{email}/quiz-attempts")
async def user_quiz_attempts_endpoint(
    email: str, user: dict = Depends(get_current_user_context)
):
    require_team_view(user, email)
    return {"attempts": db.get_user_quiz_attempts(email)}


# ====================================================================
# LAPOR KERJAAN (KARYAWAN)
# ====================================================================
@app.post("/api/reports")
async def add_report_endpoint(
    content: Optional[str] = Form(None),
    media: Optional[UploadFile] = File(None),
    user: dict = Depends(get_current_user_context),
):
    if not (content and content.strip()) and not media:
        raise HTTPException(
            status_code=400, detail="Isi laporan teks atau upload media dulu.")

    media_url = None
    media_type = "text"
    if media:
        file_bytes = await media.read()
        media_type = db.classify_file_kind(media.filename)  # bug lama: cuma kenal mp4/mov, selain itu dianggap "audio" -- sekarang eksplisit image/video/audio/document
        media_url = db.upload_report_media(
            user["company_id"], user["email"], file_bytes, media.filename
        )

    db.add_report(
        user["email"], user["company_id"],
        content=(content.strip() if content else None),
        media_url=media_url, media_type=media_type,
    )
    return {"status": "success", "message": "Laporan terkirim."}


@app.get("/api/reports")
async def get_my_reports_endpoint(user: dict = Depends(get_current_user_context)):
    return {"reports": db.get_user_reports(user["email"])}


# ====================================================================
# KUIS TRAINING (KARYAWAN)
# ====================================================================
@app.get("/api/quizzes")
async def list_quizzes_endpoint(user: dict = Depends(get_current_user_context)):
    quizzes = db.list_quizzes_for_folder(
        user["company_id"], user["folder_access"])
    return {"quizzes": quizzes}


@app.get("/api/quizzes/{quiz_id}")
async def get_quiz_endpoint(quiz_id: str, user: dict = Depends(get_current_user_context)):
    quiz = db.get_quiz(quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Kuis tidak ditemukan.")
    if not is_admin_tier(user):
        # Karyawan TIDAK BOLEH lihat correct_index sebelum submit -- kalau
        # tidak disaring, jawaban benar bocor lewat network tab browser.
        # Penilaian tetap dihitung server-side di endpoint /attempts pakai
        # db.get_quiz yang lengkap (tanpa disaring), bukan dari sini.
        quiz = {
            **quiz,
            "questions": [
                {k: v for k, v in q.items() if k != "correct_index"}
                for q in quiz["questions"]
            ],
        }
    return quiz


@app.post("/api/quizzes/{quiz_id}/attempts")
async def submit_quiz_attempt_endpoint(
    quiz_id: str, req: QuizAttemptRequest, user: dict = Depends(get_current_user_context)
):
    quiz = db.get_quiz(quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Kuis tidak ditemukan.")

    total = len(quiz["questions"])
    correct = sum(
        1
        for i, q in enumerate(quiz["questions"])
        if req.answers.get(str(i)) == q["correct_index"]
    )
    score = round((correct / total) * 100) if total else 0
    passed = score >= quiz["passing_score"]

    db.save_quiz_attempt(
        quiz_id, user["email"], user["company_id"], score, total, passed, req.answers
    )
    return {"score": score, "total": total, "correct": correct, "passed": passed}


@app.get("/api/quizzes/attempts/me")
async def my_quiz_attempts_endpoint(user: dict = Depends(get_current_user_context)):
    return {"attempts": db.get_user_quiz_attempts(user["email"])}


# ====================================================================
# KELOLA KUIS (ADMIN/SUPERADMIN)
# ====================================================================
@app.post("/api/quizzes/generate")
async def generate_quiz_endpoint(
    req: QuizGenerateRequest, user: dict = Depends(get_current_user_context)
):
    require_write(user)

    # Catatan: list_documents_in_folder tidak menyertakan kolom "content" (cuma preview
    # tidak tersedia di sana), jadi kita ambil isi lengkap dokumen lewat
    # db.get_full_document_content -- inilah fungsi yang memang dibuat khusus untuk ini.
    content = db.get_full_document_content(req.source_document_id)
    if not content or not content.strip():
        raise HTTPException(
            status_code=400, detail="Dokumen ini tidak punya cukup teks untuk dibuatkan soal."
        )

    try:
        questions = ai.generate_quiz_questions(content, req.num_questions)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Gagal generate soal: {str(e)}")

    if not questions:
        raise HTTPException(
            status_code=500, detail="AI tidak menghasilkan soal yang valid, coba lagi.")

    quiz_id = db.create_quiz(
        user["company_id"], req.folder_path, req.title or "Kuis",
        questions, source_document_id=req.source_document_id,
        passing_score=req.passing_score,
    )
    return {"status": "success", "quiz_id": quiz_id, "questions": questions}


class PasswordChangeRequest(BaseModel):
    new_password: str


@app.post("/api/profile/password")
async def change_password_endpoint(
    req: PasswordChangeRequest, user: dict = Depends(get_current_user_context)
):
    if not req.new_password or len(req.new_password) < 6:
        raise HTTPException(
            status_code=400, detail="Password minimal 6 karakter.")
    db.update_password(user["email"], req.new_password)
    return {"status": "success", "message": "Password berhasil diperbarui."}

# ====================================================================
# DASHBOARD
# ====================================================================


@app.get("/api/dashboard/chat-sessions")
async def dashboard_chat_sessions_endpoint(
    month: int = None,
    year: int = None,
    user: dict = Depends(get_current_user_context),
):
    if not is_admin_tier(user):
        raise HTTPException(status_code=403, detail="Khusus Admin/SuperAdmin.")
    sessions = db.list_all_chat_sessions_for_company(user["company_id"], month=month, year=year)
    return {"sessions": sessions}


@app.get("/api/dashboard")
async def dashboard_endpoint(user: dict = Depends(get_current_user_context)):
    if not is_admin_tier(user):
        raise HTTPException(status_code=403, detail="Khusus Admin/SuperAdmin.")
    try:
        company_id = user["company_id"]
        doc_count = db.count_all_documents(company_id)
        users = db.list_managed_users(company_id, "/", "SuperAdmin")
        folder_count = db.count_all_folders(company_id)
        chat_count = db.count_all_chat_sessions(company_id)

        root_folders = db.list_child_folders(company_id, "/")
        folder_breakdown = []
        inbox = {"path": "/Kotak Masuk/", "count": 0}
        for fpath in root_folders:
            _, fdoc_count = db.list_documents_in_folder(company_id, fpath, page=1, page_size=1)
            if fpath.strip("/").lower() == "kotak masuk":
                inbox["count"] = fdoc_count
                continue  # jangan dobel -- Kotak Masuk ditampilkan terpisah di dashboard, bukan ikut grid folder biasa
            folder_breakdown.append({
                "path": fpath,
                "name": fpath.rstrip("/").split("/")[-1],
                "count": fdoc_count,
            })

        recent = db.get_recent_activity(company_id, limit=8)

        return {
            "stats": [
                {"label": "Total Dokumen", "value": doc_count},
                {"label": "Total Karyawan", "value": len(users) if users else 0},
                {"label": "Total Folder", "value": folder_count},
                {"label": "Total Percakapan", "value": chat_count},
            ],
            "folderBreakdown": folder_breakdown,
            "inbox": inbox,
            "recent": recent,
        }
    except Exception:
        return {
            "stats": [
                {"label": "Total Dokumen", "value": 0},
                {"label": "Total Karyawan", "value": 0},
            ],
            "recent": [],
        }


# ====================================================================
# FORM BUILDER -- Form Kehadiran & Lapor Kerjaan (digabung jadi satu,
# ala Google Forms). Mengganti /api/attendance/* dan /api/reports lama
# sebagai jalur utama, tapi endpoint lama TETAP dibiarkan aktif supaya
# histori lama tidak hilang / tidak ada breaking change mendadak.
# ====================================================================
class FormFieldInput(BaseModel):
    label: str
    field_type: str = "short_text"  # short_text | long_text | number | date | select | checkbox | file
    options: List[str] = []
    file_kind: Optional[str] = "any"  # video | audio | document | any
    is_required: bool = False


class SaveFormTemplateRequest(BaseModel):
    name: str = "Form Kehadiran & Lapor Kerjaan"
    description: Optional[str] = None
    fields: List[FormFieldInput] = []


class FormAnswerInput(BaseModel):
    field_id: str
    value_text: Optional[str] = None
    file_url: Optional[str] = None
    file_kind: Optional[str] = None


class SubmitFormRequest(BaseModel):
    answers: List[FormAnswerInput] = []


@app.get("/api/forms/template")
async def get_daily_template_endpoint(user: dict = Depends(get_current_user_context)):
    """Dipakai form-builder (Admin/SuperAdmin lihat/edit) DAN halaman isi
    form karyawan (semua role, read-only)."""
    template = db.get_daily_template(user["company_id"])
    if not template:
        return {"template": None}
    return {"template": db.get_template_with_fields(template["id"])}


@app.put("/api/forms/template")
async def save_daily_template_endpoint(
    req: SaveFormTemplateRequest, user: dict = Depends(get_current_user_context)
):
    if not is_admin_tier(user):
        raise HTTPException(status_code=403, detail="Khusus Admin/SuperAdmin.")
    if not req.fields:
        raise HTTPException(status_code=400, detail="Form minimal punya 1 field.")
    template = db.save_daily_template(
        user["company_id"], user["email"], req.name, req.description,
        [f.model_dump() for f in req.fields],
    )
    return {"status": "success", "message": "Form harian disimpan.", "template": template}


@app.get("/api/forms/submission/today")
async def get_today_submission_endpoint(user: dict = Depends(get_current_user_context)):
    template = db.get_daily_template(user["company_id"])
    if not template:
        return {"template": None, "submission": None}
    submission = db.get_today_submission(template["id"], user["email"], user["company_id"])
    return {
        "template": db.get_template_with_fields(template["id"]),
        "submission": submission,
    }


@app.post("/api/forms/submit")
async def submit_daily_form_endpoint(
    req: SubmitFormRequest,
    user: dict = Depends(get_current_user_context),
):
    """Terima jawaban non-file (dan file_url hasil upload sebelumnya lewat
    /api/forms/upload-answer) untuk semua field form harian sekaligus --
    jumlah field dinamis, makanya dikirim sebagai list `answers`."""
    template = db.get_daily_template(user["company_id"])
    if not template:
        raise HTTPException(status_code=400, detail="Admin belum mengatur Form Kehadiran/Lapor Kerjaan.")

    fields_by_id = {f["id"]: f for f in db.get_template_with_fields(template["id"])["fields"]}
    answers = [a.model_dump() for a in req.answers]

    submitted_ids = {a["field_id"] for a in answers if (a.get("value_text") or a.get("file_url"))}
    missing_required = [
        f["label"] for fid, f in fields_by_id.items()
        if f["is_required"] and fid not in submitted_ids
    ]
    if missing_required:
        raise HTTPException(
            status_code=400,
            detail=f"Field wajib belum diisi: {', '.join(missing_required)}",
        )

    settings = db.get_company_settings(user["company_id"])
    submission = db.submit_daily_form(
        template["id"], user["email"], user["company_id"], answers,
        deadline_hour=settings.get("attendance_deadline_hour", 24),
    )
    return {"status": "success", "message": "Form terkirim.", "submission": submission}


@app.post("/api/forms/upload-answer")
async def upload_form_answer_endpoint(
    field_id: str = Form(...),
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user_context),
):
    """Upload 1 file jawaban (video/audio/dokumen) untuk 1 field -- dipanggil
    dulu sebelum /api/forms/submit, hasil file_url-nya diselipkan ke body
    submit sebagai jawaban field itu."""
    file_bytes = await file.read()
    url = db.upload_form_file(user["company_id"], user["email"], field_id, file_bytes, file.filename)
    kind = db.classify_file_kind(file.filename)
    return {"status": "success", "file_url": url, "file_kind": kind}


@app.get("/api/dashboard/submission-status")
async def dashboard_submission_status_endpoint(user: dict = Depends(get_current_user_context)):
    if not is_admin_tier(user):
        raise HTTPException(status_code=403, detail="Khusus Admin/SuperAdmin.")
    template = db.get_daily_template(user["company_id"])
    if not template:
        return {"sudah": [], "belum": [], "total": 0}
    return db.get_submission_status_today(user["company_id"], template["id"])


@app.get("/api/team/users/{email}/submissions")
async def user_submissions_endpoint(email: str, user: dict = Depends(get_current_user_context)):
    require_team_view(user, email)
    return {"submissions": db.get_user_submissions(email)}


# ====================================================================
# NOTIFIKASI -- pengingat belum isi form + eskalasi berjenjang ke rantai
# atasan (mengikuti company_settings.notify_atasan_enabled).
# ====================================================================
@app.get("/api/notifications")
async def list_notifications_endpoint(
    unread_only: bool = False, user: dict = Depends(get_current_user_context)
):
    """Dipakai dropdown bell -- dibatasi (default 8) supaya ringkas, isi
    penuh + pagination ada di /api/notifications/history."""
    return {
        "notifications": db.list_notifications(user["email"], unread_only=unread_only, limit=8),
        "unread_count": db.count_unread_notifications(user["email"]),
    }


@app.get("/api/notifications/history")
async def notifications_history_endpoint(
    page: int = 1, page_size: int = 20, user: dict = Depends(get_current_user_context)
):
    """Halaman khusus /dashboard/notifications -- daftar penuh + pagination,
    beda dengan /api/notifications yang cuma buat dropdown bell."""
    items, total = db.list_notifications_paginated(user["email"], page=page, page_size=page_size)
    return {"notifications": items, "total": total, "page": page, "page_size": page_size}


@app.delete("/api/notifications/read")
async def delete_read_notifications_endpoint(user: dict = Depends(get_current_user_context)):
    """WAJIB didefinisikan SEBELUM /api/notifications/{notif_id} -- kalau
    kebalik, request ke sini malah ketangkep rute dinamis itu duluan
    (notif_id="read"), FastAPI cocokkan path sesuai urutan definisi."""
    db.delete_read_notifications(user["email"])
    return {"status": "success"}


@app.delete("/api/notifications/{notif_id}")
async def delete_notification_endpoint(notif_id: str, user: dict = Depends(get_current_user_context)):
    db.delete_notification(notif_id, user["email"])
    return {"status": "success"}


@app.patch("/api/notifications/{notif_id}/read")
async def mark_notification_read_endpoint(notif_id: str, user: dict = Depends(get_current_user_context)):
    db.mark_notification_read(notif_id, user["email"])
    return {"status": "success"}


@app.patch("/api/notifications/read-all")
async def mark_all_notifications_read_endpoint(user: dict = Depends(get_current_user_context)):
    db.mark_all_notifications_read(user["email"])
    return {"status": "success"}


@app.post("/api/notifications/run-check")
async def run_notification_check_endpoint(user: dict = Depends(get_current_user_context)):
    """Jalankan pengecekan telat + eskalasi sekarang juga. Dipanggil manual
    oleh Admin/SuperAdmin dari UI, ATAU dipanggil otomatis berulang tiap
    beberapa jam lewat Railway Cron Job / scheduler eksternal yang hit
    endpoint ini (aman dipanggil berkali-kali, sudah idempotent)."""
    if not is_admin_tier(user):
        raise HTTPException(status_code=403, detail="Khusus Admin/SuperAdmin.")
    result = db.run_late_submission_check(user["company_id"])
    return {"status": "success", **result}


# ====================================================================
# BROADCAST PENGUMUMAN VIA EMAIL
# ====================================================================
class BroadcastRequest(BaseModel):
    subject: str
    body: str
    target_scope: str = "/"


@app.post("/api/announcements/broadcast")
async def broadcast_announcement_endpoint(
    req: BroadcastRequest, user: dict = Depends(get_current_user_context)
):
    if not is_admin_tier(user):
        raise HTTPException(status_code=403, detail="Khusus Admin/SuperAdmin.")
    if not req.subject.strip() or not req.body.strip():
        raise HTTPException(status_code=400, detail="Judul dan isi pengumuman wajib diisi.")
    result = db.send_broadcast_announcement(
        user["company_id"], user["email"], req.subject.strip(), req.body.strip(), req.target_scope,
    )
    return {"status": "success", "message": f"Terkirim ke {result['emails_sent']}/{result['recipients']} email.", **result}


@app.get("/api/announcements")
async def list_announcements_endpoint(user: dict = Depends(get_current_user_context)):
    if not is_admin_tier(user):
        raise HTTPException(status_code=403, detail="Khusus Admin/SuperAdmin.")
    return {"announcements": db.list_announcements(user["company_id"])}


# ====================================================================
# FORM LAPOR KERJAAN -- BEDA dari Form Kehadiran. Laporan detail
# pekerjaan harian dengan baris dinamis ala Google Sheet (karyawan bebas
# nambah baris sendiri), lampiran opsional per baris (foto/dokumen/video,
# boleh kosong), tanggal/jam/nama OTOMATIS (bukan diketik manual).
# ====================================================================
class WorkReportRowInput(BaseModel):
    description: str
    time_note: Optional[str] = None
    attachment_url: Optional[str] = None
    attachment_kind: Optional[str] = None


class SaveWorkReportRequest(BaseModel):
    rows: List[WorkReportRowInput] = []


@app.get("/api/work-reports/today")
async def get_today_work_report_endpoint(user: dict = Depends(get_current_user_context)):
    report = db.get_today_work_report(user["email"], user["company_id"])
    return {"report": report}


@app.post("/api/work-reports/submit")
async def submit_work_report_endpoint(
    req: SaveWorkReportRequest, user: dict = Depends(get_current_user_context)
):
    rows = [r.model_dump() for r in req.rows if r.description.strip()]
    if not rows:
        raise HTTPException(status_code=400, detail="Isi minimal 1 baris pekerjaan.")
    report = db.save_work_report(user["email"], user["company_id"], rows)
    return {"status": "success", "message": "Laporan kerjaan tersimpan.", "report": report}


@app.post("/api/work-reports/upload-attachment")
async def upload_work_report_attachment_endpoint(
    row_key: str = Form(...),
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user_context),
):
    """Lampiran per baris OPSIONAL -- endpoint ini cuma dipanggil kalau
    karyawan memang melampirkan file di baris itu, tidak wajib."""
    file_bytes = await file.read()
    result = db.upload_work_report_attachment(
        user["company_id"], user["email"], row_key, file_bytes, file.filename
    )
    return {"status": "success", "file_url": result["url"], "file_kind": result["kind"]}


@app.get("/api/work-reports/history")
async def get_my_work_reports_endpoint(user: dict = Depends(get_current_user_context)):
    """Riwayat laporan kerjaan MILIK SENDIRI -- karyawan bisa lihat semua
    laporan yang pernah dia kirim sebelumnya."""
    return {"reports": db.get_user_work_reports(user["email"])}


@app.get("/api/team/users/{email}/work-reports")
async def user_work_reports_endpoint(email: str, user: dict = Depends(get_current_user_context)):
    """Dipakai Admin/SuperAdmin di Direktori Karyawan untuk lihat riwayat
    laporan kerjaan bawahannya."""
    require_team_view(user, email)
    return {"reports": db.get_user_work_reports(email)}
