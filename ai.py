from google import genai
import streamlit as st
import time
import os


def get_client() -> genai.Client:
    """Inisialisasi Client menggunakan SDK google-genai yang baru"""
    return genai.Client(api_key=st.secrets["GEMINI_API_KEY"])


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list:
    """Sistem pemotong teks (Chunking) agar tidak melebihi limit token Supabase/Embedding"""
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


def embed_text(text: str) -> list:
    client = get_client()
    # Pada SDK baru, text-embedding-004 didukung penuh tanpa error 404
    result = client.models.embed_content(
        model="text-embedding-004",
        contents=text,
    )
    # Cara baru mengambil array vektor dari response
    return result.embeddings[0].values


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
    # Menggunakan model flash terbaru untuk chat RAG
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text


def extract_multimodal(file_path: str, mime_type: str, display_name: str) -> str:
    """Sistem Upload & Ekstraksi File menggunakan syntax SDK google-genai terbaru"""
    client = get_client()

    # 1. Upload file fisik ke server Google
    uploaded_file = client.files.upload(
        file=file_path, config={"display_name": display_name}
    )

    # 2. Polling menunggu proses di server Google selesai
    while uploaded_file.state.name == "PROCESSING":
        time.sleep(3)
        uploaded_file = client.files.get(name=uploaded_file.name)

    if uploaded_file.state.name == "FAILED":
        client.files.delete(name=uploaded_file.name)
        raise ValueError(f"Google Gemini gagal memproses file {display_name}.")

    # 3. Penentuan Prompt
    if "pdf" in mime_type:
        prompt = "Baca seluruh dokumen PDF ini dengan saksama dan ekstrak seluruh teks serta tabel menjadi teks terstruktur. Abaikan gambar yang tidak penting."
    else:
        prompt = "Tonton/Dengarkan file ini dengan saksama. Buatkan transkrip yang sangat detail. Jika ada teks di layar, tuliskan juga."

    # 4. Ekstraksi konten dengan model Pro
    response = client.models.generate_content(
        model="gemini-2.5-pro", contents=[uploaded_file, prompt]
    )

    # 5. Pembersihan file di server Google agar kuota aman
    client.files.delete(name=uploaded_file.name)

    return response.text
