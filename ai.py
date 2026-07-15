import os
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
    """Otomatis beralih ke lini Gemini Embedding terbaru"""
    return "gemini-embedding-2"


@st.cache_resource
def get_generation_model() -> str:
    """Menggunakan lini Gemini Flash paling mutakhir dan stabil"""
    return "gemini-3.5-flash"


def embed_text(text: str) -> list:
    """Sintaks ekstraksi array embedding dengan pembatasan dimensi ke 768"""
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


def extract_multimodal(file_path: str, mime_type: str, display_name: str) -> str:
    """
    MENGGUNAKAN NATIVE GEMINI FILE API (Ringan, Tanpa Memori Server Lokal).
    Menyerahkan tugas pembacaan PDF sepenuhnya ke server Google Cloud secara gratis.
    """
    if "pdf" not in mime_type:
        raise ValueError(
            "Ekstraksi non-PDF memerlukan metode penanganan biner yang berbeda."
        )

    try:
        client = get_client()

        # 1. Unggah file langsung ke staging area cloud Google Gemini (Mendukung hingga 2GB)
        uploaded_file = client.files.upload(file=file_path)

        # 2. Berikan instruksi pembacaan teks terstruktur
        prompt = "Baca seluruh dokumen PDF ini dengan saksama dan ekstrak seluruh teks serta tabel menjadi teks terstruktur murni."
        model_name = get_generation_model()

        # 3. Model Gemini melakukan OCR secara cloud dan mengembalikan hasilnya
        response = client.models.generate_content(
            model=model_name, contents=[uploaded_file, prompt]
        )

        # 4. Bersihkan file dari server Google demi privasi data
        try:
            client.files.delete(name=uploaded_file.name)
        except Exception:
            pass

        hasil_teks = response.text

        if not hasil_teks or not hasil_teks.strip():
            raise ValueError("Tidak ada teks yang bisa dibaca dari dokumen PDF ini.")

        return hasil_teks

    except Exception as e:
        raise RuntimeError(f"Gagal mengekstrak PDF via Google File API: {str(e)}")
