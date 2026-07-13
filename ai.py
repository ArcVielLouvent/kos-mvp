import streamlit as st
import google.generativeai as genai
import time

def _configure():
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

def embed_text(text: str) -> list:
    _configure()
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=text,
    )
    return result["embedding"]

def generate_answer(question: str, context_documents: list) -> str:
    """
    RAG inti: AI HANYA menjawab dari dokumen/multimodal yang ditemukan di Supabase.
    """
    _configure()

    # Menggabungkan konteks yang kaya akan metadata (Folder dan Tipe File)
    context_parts = []
    for doc in context_documents:
        sumber = doc.get('metadata', {}).get('tipe_file', 'Dokumen KOS')
        folder = doc.get('folder_path', '/')
        context_parts.append(
            f"Judul: {doc['title']}\n"
            f"Lokasi Folder: {folder}\n"
            f"Tipe Data: {sumber}\n"
            f"Isi/Transkrip:\n{doc['content']}"
        )

    context = "\n\n====================\n\n".join(context_parts)

    prompt = f"""Kamu adalah KOS (Knowledge Operating System), asisten cerdas internal perusahaan.
Jawab pertanyaan pengguna HANYA berdasarkan Dokumen Referensi KOS di bawah ini.
Jika jawaban tidak ada di dalam dokumen referensi, katakan dengan jujur bahwa informasi tersebut belum tersedia di database perusahaan. Jangan pernah mengarang jawaban dari pengetahuan internetmu sendiri.
Gunakan bahasa Indonesia yang profesional namun luwes dan ramah.

=== DOKUMEN REFERENSI KOS ===
{context}
=== AKHIR DOKUMEN ===

Pertanyaan Pengguna: {question}
"""

    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return response.text


def extract_multimodal(file_path: str, mime_type: str, display_name: str) -> str:
    """
    Mengunggah file video/audio ke server Google Gemini, melakukan polling hingga siap 
    (menghindari status terpotong), mengekstrak isi, lalu menghapusnya.
    """
    _configure()
    
    # 1. Unggah file fisik ke server Google
    uploaded_file = genai.upload_file(path=file_path, mime_type=mime_type, display_name=display_name)
    
    # 2. Sistem Polling Anti-Halusinasi
    # Terus memeriksa setiap 5 detik sampai file berstatus ACTIVE (siap 100%)
    while uploaded_file.state.name == "PROCESSING":
        time.sleep(5)
        uploaded_file = genai.get_file(uploaded_file.name)
        
    if uploaded_file.state.name == "FAILED":
        genai.delete_file(uploaded_file.name)
        raise ValueError("Google Gemini gagal memproses file multimodal ini.")
        
    # 3. Proses Ekstraksi Teks (Memakai model 1.5 Pro karena unggul dalam analisa konteks panjang)
    model = genai.GenerativeModel("gemini-1.5-pro")
    
    prompt = """
    Tonton/Dengarkan file ini dengan saksama dari awal hingga akhir. 
    Buatkan transkrip yang sangat detail. Jika ini adalah video, jelaskan juga kejadian visualnya, 
    langkah-langkah teknis yang ditunjukkan, dan teks apa pun yang muncul di layar.
    """
    
    # Memberikan batas waktu tambahan (timeout) agar proses video yang panjang tidak digugurkan Streamlit
    response = model.generate_content(
        [uploaded_file, prompt],
        request_options={"timeout": 600} 
    )
    
    # 4. Hapus file dari server Google demi keamanan dan penghematan kuota
    genai.delete_file(uploaded_file.name)
    
    return response.text