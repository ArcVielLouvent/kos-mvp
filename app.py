import re
import os
import pandas as pd
import streamlit as st
from gtts import gTTS

import db
import ai

st.set_page_config(page_title="KOS Enterprise", layout="wide")

if "user" not in st.session_state:
    st.session_state.user = None
if "auth_view" not in st.session_state:
    st.session_state.auth_view = "login"
if "force_pw_change" not in st.session_state:
    st.session_state.force_pw_change = False


def logout():
    st.session_state.user = None
    st.session_state.auth_view = "login"
    st.session_state.force_pw_change = False
    st.rerun()


# ==========================================
# GERBANG MASUK
# ==========================================
def landing_page():
    st.write("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])

    with col2:
        with st.container(border=True):
            st.markdown(
                "<h2 style='text-align: center;'>KOS</h2>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<p style='text-align: center; color: gray;'>Satu sistem terpusat untuk seluruh kecerdasan perusahaan Anda.</p>",
                unsafe_allow_html=True,
            )
            st.divider()

            if st.session_state.auth_view == "login":
                st.subheader("Masuk ke Workspace")
                login_email = st.text_input("Email", key="log_email")
                login_pass = st.text_input("Password", type="password", key="log_pass")

                if st.button("Login", type="primary", use_container_width=True):
                    try:
                        user_data = db.get_user(login_email)
                        if user_data and db.verify_password(
                            login_pass, user_data.get("password", "")
                        ):
                            st.session_state.user = user_data
                            st.session_state.force_pw_change = user_data.get(
                                "must_change_password", False
                            )
                            st.rerun()
                        else:
                            st.error("Email atau Password salah.")
                    except Exception:
                        st.error("Terjadi gangguan saat menghubungi database.")

                st.write("")
                st.markdown(
                    "<p style='text-align: center; font-size: 14px;'>Belum mendaftarkan perusahaan?</p>",
                    unsafe_allow_html=True,
                )
                if st.button(
                    "Daftar Perusahaan Baru (Super Admin)", use_container_width=True
                ):
                    st.session_state.auth_view = "register"
                    st.rerun()

            else:
                st.subheader("Daftarkan Perusahaan")
                reg_company = st.text_input("Nama Perusahaan")
                reg_email = st.text_input("Email Admin")
                reg_pass = st.text_input("Password", type="password")

                if st.button(
                    "Buat Perusahaan", type="primary", use_container_width=True
                ):
                    if reg_company and reg_email and reg_pass:
                        try:
                            db.register_company(reg_company, reg_email, reg_pass)
                            st.success(
                                "Perusahaan berhasil didaftarkan! Silakan kembali ke Login."
                            )
                        except ValueError as e:
                            st.error(str(e))
                        except Exception:
                            st.error("Gagal mendaftar. Coba lagi beberapa saat.")
                    else:
                        st.warning("Mohon lengkapi semua data.")

                st.write("")
                st.markdown(
                    "<p style='text-align: center; font-size: 14px;'>Sudah punya akun?</p>",
                    unsafe_allow_html=True,
                )
                if st.button("Kembali ke Halaman Login", use_container_width=True):
                    st.session_state.auth_view = "login"
                    st.rerun()


def force_password_change():
    st.write("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.container(border=True):
            st.subheader("Login pertama — buat password baru")
            new_pw = st.text_input("Password baru", type="password", key="new_pw")
            confirm = st.text_input(
                "Ulangi password baru", type="password", key="confirm_pw"
            )
            if st.button("Simpan Password", type="primary", use_container_width=True):
                if not new_pw:
                    st.warning("Password tidak boleh kosong.")
                elif new_pw != confirm:
                    st.error("Password tidak cocok.")
                else:
                    db.update_password(st.session_state.user["email"], new_pw)
                    st.session_state.user["must_change_password"] = False
                    st.session_state.force_pw_change = False
                    st.success("Password diperbarui.")
                    st.rerun()


# ==========================================
# DASHBOARD ADMIN
# ==========================================
def admin_sidebar():
    st.sidebar.header(f"{st.session_state.user.get('company_name', 'Perusahaan')}")
    st.sidebar.write(f"Admin: {st.session_state.user['email']}")
    st.sidebar.button("Logout", on_click=logout)
    st.sidebar.divider()
    return st.sidebar.radio(
        "Navigasi",
        ["Manajemen Karyawan", "Universal Uploader", "File Manager & KOS AI"],
    )


def admin_employee_management():
    company_id = st.session_state.user["company_id"]
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
        existing_folders = db.get_unique_folders(company_id)
        selected_folder = st.selectbox("Pilih Folder Akses", existing_folders)
        new_folder = st.text_input("Atau ketik folder baru (contoh: /Dapur/SOP/ )")
        final_folder = new_folder if new_folder else selected_folder

    if st.button("Daftarkan Karyawan", type="primary"):
        email_list = re.findall(
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", emails_text
        )
        if email_list:
            temp_passwords = db.add_users_bulk(email_list, final_folder, company_id)
            st.success(f"Berhasil mendaftarkan {len(temp_passwords)} karyawan!")
            st.warning(
                "Salin dan kirim password sementara ini ke masing-masing karyawan (hanya tampil sekali):"
            )
            st.dataframe(
                pd.DataFrame(
                    [
                        {"email": e, "password_sementara": p}
                        for e, p in temp_passwords.items()
                    ]
                ),
                use_container_width=True,
            )
        else:
            st.warning("Tidak ada email valid yang ditemukan.")


def universal_uploader():
    company_id = st.session_state.user["company_id"]
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
        if not uploaded_files:
            st.error("Pilih minimal satu file!")
            return

        for file in uploaded_files:
            ext = file.name.split(".")[-1].lower()
            with st.spinner(f"Memproses {file.name}..."):

                if ext == "csv":
                    df = pd.read_csv(file)
                    for index, row in df.iterrows():
                        content = "\n".join(f"{col}: {val}" for col, val in row.items())
                        title = f"Baris {index+1} - {file.name}"
                        embedding = ai.embed_text(content)
                        db.insert_document(
                            title,
                            content,
                            embedding,
                            company_id,
                            folder_target,
                            {"tipe_file": "CSV Row", "sumber": file.name},
                        )
                    st.success(f"File {file.name} (CSV) dipecah & berhasil disimpan!")

                elif ext in ["mp4", "mp3", "mov", "wav"]:
                    temp_path = f"temp_{file.name}"
                    try:
                        with open(temp_path, "wb") as f:
                            f.write(file.getbuffer())
                        mime_type = (
                            "video/mp4" if ext in ["mp4", "mov"] else "audio/mp3"
                        )
                        content = ai.extract_multimodal(temp_path, mime_type, file.name)
                        embedding = ai.embed_text(content)
                        db.insert_document(
                            file.name,
                            content,
                            embedding,
                            company_id,
                            folder_target,
                            {"tipe_file": "Multimodal Transkrip"},
                        )
                        st.success(
                            f"Transkrip file {file.name} berhasil diekstrak dan disimpan!"
                        )
                    finally:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)

                else:
                    st.warning(
                        f"Format {ext} belum didukung secara penuh di prototipe ini."
                    )


# ==========================================
# KOS CHAT (UNTUK SEMUA ROLE)
# ==========================================
def kos_workspace():
    user = st.session_state.user
    st.header(f"Chat KOS (Folder Akses: {user['folder_access']})")

    question = st.text_input("Tanyakan sesuatu seputar operasional, SOP, atau resep...")

    if st.button("Tanya KOS", type="primary") and question:
        with st.spinner("KOS sedang mencari di database..."):
            query_embedding = ai.embed_text(question)
            docs = db.search_documents(
                query_embedding,
                company_id=user["company_id"],
                match_count=3,
                folder_prefix=user["folder_access"],
            )

            if not docs:
                st.warning("Tidak ada dokumen referensi yang ditemukan di folder Anda.")
            else:
                answer = ai.generate_answer(question, docs)
                st.markdown("### Jawaban AI")
                st.write(answer)

                tts = gTTS(text=answer, lang="id")
                tts.save("response.mp3")
                st.audio("response.mp3")

                with st.expander("Lihat Dokumen Referensi"):
                    for d in docs:
                        st.info(
                            f"**{d['title']}** (Similarity: {d['similarity']:.2f})\n\n{d['content'][:200]}..."
                        )


# ==========================================
# ROUTING UTAMA
# ==========================================
if st.session_state.user is None:
    landing_page()
elif st.session_state.force_pw_change:
    force_password_change()
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
        kos_workspace()
