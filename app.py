import re
import os
import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
from gtts import gTTS

import db
import ai

st.set_page_config(page_title="KOS Enterprise", layout="wide")

for key, default in [
    ("user", None),
    ("auth_view", "login"),
    ("force_pw_change", False),
    ("current_session_id", None),
    ("fm_current_path", "/"),
]:
    if key not in st.session_state:
        st.session_state[key] = default


def logout():
    st.session_state.user = None
    st.session_state.auth_view = "login"
    st.session_state.force_pw_change = False
    st.session_state.current_session_id = None
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
                "<h2 style='text-align: center;'>KOS</h2>", unsafe_allow_html=True
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
# NAVIGASI (sidebar ikon + akun)
# ==========================================
def account_popover():
    user = st.session_state.user
    with st.popover(f"👤 {user['email']}", use_container_width=True):
        st.write(f"**{user['email']}**")
        st.caption(user.get("role", ""))
        st.divider()
        st.button("Logout", on_click=logout, use_container_width=True)


def sidebar_nav(options: list, icons: list):
    with st.sidebar:
        st.markdown(f"### {st.session_state.user.get('company_name') or 'Perusahaan'}")
        st.divider()
        selected = option_menu(
            menu_title=None,
            options=options,
            icons=icons,
            default_index=0,
            styles={
                "container": {"padding": "0", "background-color": "transparent"},
                "icon": {"font-size": "16px"},
                "nav-link": {
                    "font-size": "14px",
                    "text-align": "left",
                    "margin": "2px",
                },
                "nav-link-selected": {"background-color": "#FF4B4B"},
            },
        )
        st.divider()
        account_popover()
    return selected


# ==========================================
# CHAT KOS (ala Claude: riwayat + delete/rename)
# ==========================================
def chat_page():
    user = st.session_state.user
    col_hist, col_chat = st.columns([1, 3])

    with col_hist:
        st.markdown("#### Riwayat")
        if st.button("+ Chat baru", use_container_width=True):
            st.session_state.current_session_id = None
            st.rerun()

        for s in db.list_chat_sessions(user["email"]):
            active = s["id"] == st.session_state.current_session_id
            label = ("🟢 " if active else "") + (s["title"] or "Percakapan baru")
            c1, c2 = st.columns([4, 1])
            with c1:
                if st.button(label, key=f"sess_{s['id']}", use_container_width=True):
                    st.session_state.current_session_id = s["id"]
                    st.rerun()
            with c2:
                with st.popover("⋮"):
                    new_title = st.text_input(
                        "Ganti nama", value=s["title"], key=f"rename_{s['id']}"
                    )
                    if st.button(
                        "Simpan", key=f"save_{s['id']}", use_container_width=True
                    ):
                        db.rename_chat_session(s["id"], new_title)
                        st.rerun()
                    if st.button(
                        "🗑️ Hapus", key=f"del_{s['id']}", use_container_width=True
                    ):
                        db.delete_chat_session(s["id"])
                        if st.session_state.current_session_id == s["id"]:
                            st.session_state.current_session_id = None
                        st.rerun()

    with col_chat:
        st.markdown(f"#### Chat KOS · Folder akses: `{user['folder_access']}`")

        if st.session_state.current_session_id:
            for m in db.get_chat_messages(st.session_state.current_session_id):
                with st.chat_message(m["role"]):
                    st.write(m["content"])

        question = st.chat_input(
            "Tanyakan sesuatu seputar operasional, SOP, atau resep..."
        )

        if question:
            if not st.session_state.current_session_id:
                st.session_state.current_session_id = db.create_chat_session(
                    user["email"], user["company_id"]
                )
                db.rename_chat_session(
                    st.session_state.current_session_id, question[:40]
                )

            db.add_chat_message(st.session_state.current_session_id, "user", question)
            with st.chat_message("user"):
                st.write(question)

            with st.chat_message("assistant"):
                with st.spinner("KOS sedang mencari di database..."):
                    q_emb = ai.embed_text(question)
                    docs = db.search_documents(
                        q_emb,
                        company_id=user["company_id"],
                        match_count=3,
                        folder_prefix=user["folder_access"],
                    )
                    answer = (
                        ai.generate_answer(question, docs)
                        if docs
                        else "Tidak ada dokumen referensi yang ditemukan di folder Anda."
                    )
                st.write(answer)
                if docs:
                    if st.button("🔊 Dengarkan", key=f"tts_{question[:20]}"):
                        tts = gTTS(text=answer, lang="id")
                        tts.save("response.mp3")
                        st.audio("response.mp3")

            db.add_chat_message(
                st.session_state.current_session_id, "assistant", answer
            )
            st.rerun()


# ==========================================
# FILE MANAGER (breadcrumb ala Drive)
# ==========================================
def file_manager_page():
    company_id = st.session_state.user["company_id"]
    current = st.session_state.fm_current_path

    parts = [p for p in current.strip("/").split("/") if p]
    crumb_cols = st.columns(len(parts) + 1)
    with crumb_cols[0]:
        if st.button("🏠 Root", key="crumb_root"):
            st.session_state.fm_current_path = "/"
            st.rerun()
    accum = "/"
    for i, part in enumerate(parts):
        accum += part + "/"
        with crumb_cols[i + 1]:
            if st.button(part, key=f"crumb_{i}"):
                st.session_state.fm_current_path = accum
                st.rerun()

    st.divider()

    if st.session_state.user["role"] == "Admin":
        with st.popover("+ Folder baru"):
            new_name = st.text_input("Nama folder", key="new_folder_name")
            if st.button("Buat", key="create_folder_btn"):
                if new_name.strip():
                    db.create_folder(company_id, current + new_name.strip() + "/")
                    st.rerun()
        st.write("")

    children = db.list_child_folders(company_id, current)
    docs = db.list_documents_in_folder(company_id, current)

    if not children and not docs:
        st.caption("Folder ini masih kosong.")

    if children:
        st.caption("Folder")
        cols = st.columns(4)
        for i, child in enumerate(children):
            name = child.rstrip("/").split("/")[-1]
            with cols[i % 4]:
                if st.button(
                    f"📁 {name}", key=f"folder_{child}", use_container_width=True
                ):
                    st.session_state.fm_current_path = child
                    st.rerun()

    if docs:
        st.caption("Dokumen")
        for d in docs:
            icon = (
                "🎥"
                if d.get("metadata", {}).get("tipe_file") == "Multimodal Transkrip"
                else "📄"
            )
            st.write(f"{icon} {d['title']}")


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
# ROUTING UTAMA
# ==========================================
if st.session_state.user is None:
    landing_page()
elif st.session_state.force_pw_change:
    force_password_change()
else:
    role = st.session_state.user["role"]

    if role == "Admin":
        selected = sidebar_nav(
            ["Chat KOS", "File Manager", "Upload Dokumen", "Karyawan"],
            ["chat-dots", "folder", "cloud-upload", "people"],
        )
        if selected == "Chat KOS":
            chat_page()
        elif selected == "File Manager":
            file_manager_page()
        elif selected == "Upload Dokumen":
            universal_uploader()
        else:
            admin_employee_management()

    else:
        selected = sidebar_nav(["Chat KOS", "File Manager"], ["chat-dots", "folder"])
        if selected == "Chat KOS":
            chat_page()
        else:
            file_manager_page()
