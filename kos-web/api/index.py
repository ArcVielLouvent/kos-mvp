from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class ChatRequest(BaseModel):
    message: str
    user_id: str

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    return {
        "reply": f"Terhubung dengan Backend Python! Kamu bertanya: {request.message}",
        "sourceTitle": "SOP Internal Kopi Nusantara",
        "sourceType": "Dokumen PDF"
    }

@app.get("/api/files")
async def files_endpoint(path: str = "/"):
    return {
        "folders": [
            {"path": "/SOP/", "name": "SOP & Operasional"},
            {"path": "/Keuangan/", "name": "Keuangan"}
        ],
        "files": [
            {"id": "1", "title": "SOP_Karyawan.pdf", "metadata": {"tipe_file": "Dokumen PDF"}, "created_at": "2026-08-06T00:00:00Z"},
            {"id": "2", "title": "Data_Absensi.xlsx", "metadata": {"tipe_file": "Spreadsheet"}, "created_at": "2026-08-06T00:00:00Z"}
        ]
    }
