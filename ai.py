from google import genai
from google.genai import types
import streamlit as st

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
            if 'embedContent' in m.supported_generation_methods:
                # SDK baru lebih stabil tanpa prefix 'models/'
                return m.name.replace("models/", "")
    except Exception:
        pass
    return "text-embedding-004"

@st.cache_resource
def get_generation_model() -> str:
    """RADAR DINAMIS: Menemukan model Generate yang anti-404"""
    client = get_client()
    try:
        models = [m.name.replace("models/", "") for m in client.models.list() if 'generateContent' in m.supported_generation_methods]
        for m in models:
            if "gemini-1.5-flash" in m: return m
        for m in models:
            if "flash" in m: return m
        if models:
            return models[0]
    except Exception:
        pass
    return "gemini-1.5-flash"

def embed_text(text: str) -> list:
    client = get_client()
    model_name = get_embedding_model()
    
    result = client.models.embed_content(
        model=model_name,
        contents=text,
    )
    # Sintaks pengambilan array pada SDK baru
    return result.embeddings[0].values

def generate_answer(question: str, context_documents: list) -> str:
    client = get_client()
    context_parts = []
    for doc in context_documents:
        sumber = doc.get('metadata', {}).get('tipe_file', 'Dokumen KOS')
        folder = doc.get('folder_path', '/')
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

def extract_multimodal(file_path: str, mime_type: str, display_name: str) -> str:
    """
    Menggunakan API Key yang SAMA dari st.secrets['GEMINI_API_KEY'].
    Tidak perlu login tambahan, aman untuk file PDF besar (Anti 404).
    """
    # 1. Mengambil client yang sudah dikonfigurasi dengan API Key Anda
    client = get_client() 
    
    # 2. Upload file menggunakan client tersebut
    uploaded_file = client.files.upload(file=file_path)
    
    if "pdf" in mime_type:
        prompt = "Baca seluruh dokumen PDF ini dengan saksama dan ekstrak seluruh teks serta tabel menjadi teks terstruktur. Abaikan gambar yang tidak penting."
    else:
        prompt = "Tonton/Dengarkan file ini dengan saksama. Buatkan transkrip yang sangat detail."
        
    model_name = get_generation_model()
    
    # 3. Kirim referensi berkas hasil unggahan ke Gemini
    response = client.models.generate_content(
        model=model_name,
        contents=[
            uploaded_file,
            prompt
        ]
    )
    
    # 4. Hapus berkas dari server setelah teks berhasil diekstrak
    try:
        client.files.delete(name=uploaded_file.name)
    except Exception:
        pass
        
    return response.text