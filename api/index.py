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
from pydantic import BaseModel

from . import ai
from . import auth
from . import db

app = FastAPI()
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


class YouTubeRequest(BaseModel):
    title: str
    url: str
    description: str = ""
    current_path: str = "/"


class EmployeeBulkRequest(BaseModel):
    emails: str  # teks bebas, email diekstrak via regex (sama seperti app.py)
    folder: str
    position_title: Optional[str] = None


class AdminAddRequest(BaseModel):
    email: str
    folder: str
    permission_level: str = "crud"  # "crud" | "read_only"
    position_title: Optional[str] = None


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
            q_emb, company_id=company_id, match_count=3, folder_prefix=folder_access
        )
        docs = ai.filter_docs_by_intent(question, docs)

        used_sources = []
        seen = set()
        mode = "chat"
        generated_files = []
        analysis_table = None
        analysis_file = None
        warning = None

        # ---------- NIAT: MINTA DOKUMEN DIBUATKAN ----------
        if ai.is_generate_request(question):
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

        # 2. Eksekusi pengaman defensif Claude
        path = normalize_folder(path)

        if not path.startswith(base_path):
            path = base_path

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
        email_list, req.folder, user["company_id"], position_title=req.position_title
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
        position_title=req.position_title,
    )
    return {
        "status": "success",
        "message": f"Admin '{req.email}' ditambahkan, mengelola folder {req.folder}.",
        "temporaryPassword": temp_pw,
    }


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

def require_team_view(viewer: dict, target_email: str):
    if not is_admin_tier(viewer):
        raise HTTPException(status_code=403, detail="Khusus Admin/SuperAdmin.")
    if viewer["role"] != "SuperAdmin":
        target = db.get_user(target_email)
        if not target or not target.get("folder_access", "").startswith(viewer["folder_access"]):
            raise HTTPException(status_code=403, detail="Di luar cakupan folder Anda.")

@app.get("/api/team/users/{email}/chat-sessions")
async def user_chat_sessions_endpoint(
    email: str, user: dict = Depends(get_current_user_context)
):
    require_team_view(user, email) 
    return {"sessions": db.list_chat_sessions(email)}


@app.get("/api/team/users/{email}/reports")
async def user_reports_endpoint(email: str, user: dict = Depends(get_current_user_context)):
    require_team_view(user, email
    return {"reports": db.get_user_reports(email)}


@app.get("/api/team/users/{email}/quiz-attempts")
async def user_quiz_attempts_endpoint(
    email: str, user: dict = Depends(get_current_user_context)
):
    require_team_view(user, email
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
        ext = media.filename.split(".")[-1].lower()
        media_type = "video" if ext in ["mp4", "mov"] else "audio"
        file_bytes = await media.read()
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


# ====================================================================
# DASHBOARD
# ====================================================================
@app.get("/api/dashboard")
async def dashboard_endpoint(user: dict = Depends(get_current_user_context)):
    if not is_admin_tier(user):             # <-- tambahkan baris ini
        raise HTTPException(status_code=403, detail="Khusus Admin/SuperAdmin.")
    try:
        company_id = user["company_id"]
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
                {"label": "Status Sistem", "value": "Aktif"},
            ],
            "recent": [],
        }
    except Exception:
        return {
            "stats": [
                {"label": "Total Dokumen", "value": 0},
                {"label": "Total Karyawan", "value": 0},
            ],
            "recent": [],
        }
