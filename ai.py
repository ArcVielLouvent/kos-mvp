import os
from google import genai
from google.genai import types
import streamlit as st
from paddleocr import PaddleOCR
from pdf2image import convert_from_path


def get_client() -> genai.Client:
    """Inisialisasi Client menggunakan SDK google-genai yang mutakhir"""
    return genai.Client(api_key=st.secrets["GEMINI_API_KEY"])


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list:
    """Sistem pemotong teks (Chunking) untuk mencegah Limit Token"""
    if not text:
        return []
    chunks = []
    i = 0
    while i < len(text):
        end = i + chunk_size
        if end < len(text):
            space_index = text.rfind(" ", i, end)
            if space_index > i:
                end = space_index
        chunks.append(text[i:end].strip())
        i = end - overlap
    return [c for c in chunks if len(c) > 10]


@st.cache_resource
def get_embedding_model() -> str:
    """RADAR DINAMIS: Menemukan model Embedding dengan SDK baru"""
    client = get_client()
    try:
        for m in client.models.list():
            if "embedContent" in m.supported_generation_methods:
                return m.name.replace("models/", "")
    except Exception:
        pass
    return "text-embedding-004"


@st.cache_resource
def get_embedding_model() -> str:
    """Otomatis beralih ke lini Gemini Embedding terbaru (Anti-404)"""
    client = get_client()
    try:
        models = [m.name.replace("models/", "") for m in client.models.list()]
        for m in models:
            if "gemini-embedding" in m:
                return m
        for m in models:
            if "embedding" in m:
                return m
    except Exception:
        pass
    # Fallback ke lini terbaru Google API saat ini
    return "gemini-embedding-2"


@st.cache_resource
def get_generation_model() -> str:
    """
    Langsung dipasang ke Gemini generasi 3.5 / 3 Flash yang modern.
    Menghindari error pemutusan model lawas dari server Google.
    """
    client = get_client()
    try:
        models = [m.name.replace("models/", "") for m in client.models.list() if 'generateContent' in m.supported_generation_methods]
        
        for m in models:
            if "3.5-flash" in m: return m
        for m in models:
            if "3-flash" in m: return m
        for m in models:
            if "flash" in m: return m
            
        if models:
            return models[0]
    except Exception:
        pass
    
    return "gemini-3.5-flash"


def embed_text(text: str) -> list:
    """
    Sintaks ekstraksi array embedding dengan pembatasan dimensi
    agar cocok dengan kolom vector(768) di database Supabase Anda.
    """
    client = get_client()
    model_name = get_embedding_model()

    result = client.models.embed_content(
        model=model_name,
        contents=text,
        config=types.EmbedContentConfig(output_dimensionality=768),
    )

    [embedding_obj] = result.embeddings
    return embedding_obj.values


def generate_answer(question: str, context_documents: list) -> str:
    client = get_client()
    context_parts = []
    for doc in context_documents:
        sumber = doc.get("metadata", {}).get("tipe_file", "Dokumen KOS")
        folder = doc.get("folder_path", "/")
        context_parts.append(
            f"Judul: {doc['title']}\nLokasi: {folder}\nTipe: {sumber}\nIsi:\n{doc['content']}"
        )

    context = "\n\n====================\n\n".join(context_parts)

    prompt = f"""Kamu adalah Knowledge Operating System (KOS), asisten cerdas internal perusahaan.
Jawab pertanyaan pengguna HANYA berdasarkan Dokumen Referensi di bawah ini.
Jika jawaban tidak ada di dalam dokumen referensi, katakan jujur bahwa informasi tersebut belum tersedia di database. Jangan pernah mengarang.

=== DOKUMEN REFERENSI ===
{context}
=== AKHIR DOKUMEN ===

Pertanyaan: {question}
"""
    model_name = get_generation_model() 
    
    response = client.models.generate_content(
        model=model_name, 
        contents=prompt,
    )
    return response.text


@st.cache_resource
def init_paddle_ocr():
    """Inisialisasi PaddleOCR sekali saja dan simpan di cache Streamlit"""
    return PaddleOCR(use_angle_cls=True, lang="en")


def extract_multimodal(file_path: str, mime_type: str, display_name: str) -> str:
    """
    Menghapus argumen 'cls' yang tidak didukung pada method ocr() versi baru.
    """
    if "pdf" not in mime_type:
        return "Ekstraksi non-PDF memerlukan metode penanganan file biner yang berbeda."

    try:
        # 1. Mengambil objek PaddleOCR dari cache (cls=True sudah diset aman di sini)
        ocr = init_paddle_ocr()
        
        # 2. Konversi lembar halaman PDF menjadi gambar
        pages = convert_from_path(file_path, dpi=150)
        full_text = []
        
        for i, page in enumerate(pages):
            temp_img_path = f"temp_page_{i}.jpg"
            page.save(temp_img_path, 'JPEG')
            
            result = ocr.ocr(temp_img_path)
            
            page_text = []
            if result and result[0]:
                for line in result[0]:
                    text_detected = line[1][0]
                    page_text.append(text_detected)
            
            full_text.append(f"--- Halaman {i+1} ---\n" + "\n".join(page_text))
            
            # Bersihkan file temporary
            if os.path.exists(temp_img_path):
                os.remove(temp_img_path)
            
        return "\n\n".join(full_text)
        
    except Exception as e:
        return f"Gagal mengekstrak teks PDF melalui PaddleOCR lokal: {str(e)}"