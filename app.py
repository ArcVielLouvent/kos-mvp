import streamlit as st
import pandas as pd
import os
from gtts import gTTS
import db
import ai

# ==========================================
# 1. KONFIGURASI HALAMAN & STATE
# ==========================================
st.set_page_config(page_title="KOS Enterprise", layout="wide")

if "user" not in st.session_state:
    st.session_state.user = None


# ==========================================
# 2. LOGIKA AUTENTIKASI (LOGIN & REGISTER)
# ==========================================
def logout():
    st.session_state.user = None
    st.rerun()


def landing_page():
    st.title("KOS (Knowledge Operating System)")
    st.markdown("Satu sistem terpusat untuk seluruh kecerdasan perusahaan Anda.")

    tab1, tab2 = st.tabs(["Login", "Register Perusahaan (Super Admin)"])

    with tab1:
        st.subheader("Masuk ke Workspace")
        login_email = st.text_input("Email", key="log_email")
        login_pass = st.text_input("Password", type="password", key="log_pass")

        if st.button("Login", type="primary"):
            user_data = db.get_user(login_email)
            if user_data and user_data.get("password") == login_pass:
                st.session_state.user = user_data
                st.success("Login Berhasil!")
                st.rerun()
            else:
                st.error("Email atau Password salah, atau akun belum terdaftar.")

    with tab2:
        st.subheader("Daftarkan Perusahaan Baru")
        st.info("Akun pertama ini akan otomatis menjadi Super Admin perusahaan.")
        reg_company = st.text_input("Nama Perusahaan")
        reg_email = st.text_input("Email Admin")
        reg_pass = st.text_input("Password", type="password")

        if st.button("Buat Perusahaan"):
            if reg_company and reg_email and reg_pass:
                client = db.get_client()
                # Daftarkan sebagai Super Admin dengan akses Root ('/')
                client.table("users").upsert(
                    {
                        "email": reg_email,
                        "password": reg_pass,
                        "role": "Admin",
                        "folder_access": "/",
                        "company_name": reg_company,
                    }
                ).execute()
                st.success(
                    f"Perusahaan {reg_company} berhasil didaftarkan! Silakan Login di tab sebelah."
                )
            else:
                st.warning("Mohon lengkapi semua data.")


# ==========================================
# 3. DASHBOARD SUPER ADMIN
# ==========================================
def admin_sidebar():
    st.sidebar.header(f"{st.session_state.user.get('company_name', 'Perusahaan')}")
    st.sidebar.write(f"Admin: {st.session_state.user['email']}")
    st.sidebar.button("Logout", on_click=logout)
    st.sidebar.divider()

    menu = st.sidebar.radio(
        "Navigasi",
        ["Manajemen Karyawan", "Universal Uploader", "File Manager & KOS AI"],
    )
    return menu


def admin_employee_management():
    st.header("Manajemen Karyawan (Paste & Pick)")
    st.write("Masukkan email karyawan dan tentukan direktori akses mereka.")

    col1, col2 = st.columns(2)
    with col1:
        emails_text = st.text_area(
            "Daftar Email (pisahkan dengan koma atau baris baru)",
            height=150,
            placeholder="karyawan1@kos.com\nkaryawan2@kos.com",
        )
    with col2:
        existing_folders = db.get_unique_folders()
        # Admin bisa mengetik folder baru jika belum ada di list
        selected_folder = st.selectbox("Pilih Folder Akses", existing_folders)
        new_folder = st.text_input("Atau ketik folder baru (contoh: /Dapur/SOP/ )")

        final_folder = new_folder if new_folder else selected_folder

    if st.button("Daftarkan Karyawan", type="primary"):
        import re

        # Ekstrak semua email dari teks
        email_list = re.findall(
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", emails_text
        )
        if email_list:
            db.add_users_bulk(email_list, final_folder)
            st.success(
                f"Berhasil mendaftarkan {len(email_list)} karyawan ke folder {final_folder}!"
            )
        else:
            st.warning("Tidak ada email valid yang ditemukan.")


def universal_uploader():
    st.header("Universal KOS Uploader")
    st.write(
        "Unggah dokumen, file resep (CSV), atau video panduan (MP4/MP3). AI akan mengekstraknya otomatis."
    )

    folder_target = st.text_input(
        "Target Folder Penyimpanan", value="/", help="Contoh: /Dapur/Resep/"
    )
    uploaded_files = st.file_uploader(
        "Pilih File (PDF, CSV, MP4, MP3)", accept_multiple_files=True
    )

    if st.button("Mulai Proses & Ekstrak Data"):
        if uploaded_files:
            for file in uploaded_files:
                ext = file.name.split(".")[-1].lower()
                with st.spinner(f"Memproses {file.name}..."):

                    if ext == "csv":
                        df = pd.read_csv(file)
                        for index, row in df.iterrows():
                            # Gabungkan semua kolom jadi satu teks konten
                            content = "\n".join(
                                [f"{col}: {val}" for col, val in row.items()]
                            )
                            title = f"Baris {index+1} - {file.name}"
                            embedding = ai.embed_text(content)
                            db.insert_document(
                                title,
                                content,
                                embedding,
                                folder_target,
                                {"tipe_file": "CSV Row", "sumber": file.name},
                            )
                        st.success(
                            f"File {file.name} (CSV) dipecah & berhasil disimpan!"
                        )

                    elif ext in ["mp4", "mp3", "mov", "wav"]:
                        # Simpan file fisik sementara untuk diupload ke server Google
                        temp_path = f"temp_{file.name}"
                        with open(temp_path, "wb") as f:
                            f.write(file.getbuffer())

                        mime_type = (
                            "video/mp4" if ext in ["mp4", "mov"] else "audio/mp3"
                        )
                        # Ekstrak menggunakan Gemini 1.5 Pro
                        content = ai.extract_multimodal(temp_path, mime_type, file.name)
                        embedding = ai.embed_text(content)
                        db.insert_document(
                            file.name,
                            content,
                            embedding,
                            folder_target,
                            {"tipe_file": "Multimodal Transkrip"},
                        )

                        os.remove(temp_path)  # Hapus file fisik
                        st.success(
                            f"Transkrip file {file.name} berhasil diekstrak dan disimpan!"
                        )

                    # Logika 3: Fallback ke teks PDF/TXT biasa
                    else:
                        st.warning(
                            f"Format {ext} belum didukung secara penuh di prototipe ini."
                        )

        else:
            st.error("Pilih minimal satu file!")


# ==========================================
# 4. KOS CHAT & FILE MANAGER (UNTUK SEMUA)
# ==========================================
def kos_workspace():
    user = st.session_state.user
    st.header(f"Chat KOS (Folder Akses: {user['folder_access']})")

    question = st.text_input("Tanyakan sesuatu seputar operasional, SOP, atau resep...")

    if st.button("Tanya KOS", type="primary") and question:
        with st.spinner("KOS sedang mencari di database..."):
            # 1. Cari dokumen, dikunci HANYA di folder akses pengguna
            query_embedding = ai.embed_text(question)
            docs = db.search_documents(
                query_embedding, match_count=3, folder_prefix=user["folder_access"]
            )

            if not docs:
                st.warning("Tidak ada dokumen referensi yang ditemukan di folder Anda.")
            else:
                # 2. Hasilkan jawaban
                answer = ai.generate_answer(question, docs)
                st.markdown("### Jawaban AI")
                st.write(answer)

                # 3. Fitur Text to Speech
                tts = gTTS(text=answer, lang="id")
                tts.save("response.mp3")
                st.audio("response.mp3")

                # Tampilkan Referensi
                with st.expander("Lihat Dokumen Referensi"):
                    for d in docs:
                        st.info(
                            f"**{d['title']}** (Similiarity: {d['similarity']:.2f})\n\n{d['content'][:200]}..."
                        )


# ==========================================
# 5. KONTROL UTAMA (ROUTING)
# ==========================================
if st.session_state.user is None:
    landing_page()
else:
    role = st.session_state.user["role"]

    if role == "Admin":
        menu = admin_sidebar()
        if menu == "Manajemen Karyawan":
            admin_employee_management()
        elif menu == "Universal Uploader":
            universal_uploader()
        else:
            kos_workspace()

    elif role == "Karyawan":
        st.sidebar.header("KOS Workspace")
        st.sidebar.write(f"Email: {st.session_state.user['email']}")
        st.sidebar.write(f"Hak Akses: **{st.session_state.user['folder_access']}**")
        st.sidebar.button("Logout", on_click=logout)

        # Karyawan hanya bisa melihat workspace
        kos_workspace()
