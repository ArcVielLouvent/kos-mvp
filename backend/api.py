from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
# Nanti kamu tinggal import fungsionalitas dari ai.py milikmu di sini
# import ai 

app = FastAPI()

# Mengizinkan Next.js (port 3000) untuk berkomunikasi dengan Python (port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# Format data yang akan diterima dari Next.js
class ChatRequest(BaseModel):
    message: str
    user_id: str

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    user_message = request.message
    
    # DI SINI KAMU PANGGIL GEMINI / ai.py
    # Contoh: bot_reply = ai.generate_response(user_message)
    bot_reply = f"Ini adalah respons dari Python Backend. Kamu tadi bilang: '{user_message}'"
    
    return {
        "reply": bot_reply,
        "sourceTitle": "SOP Internal (Contoh)",
        "sourceType": "Dokumen PDF"
    }