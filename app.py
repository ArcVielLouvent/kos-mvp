import re
import os
import time  # <-- LIBRARY JEDA WAKTU ANTI SPAM
import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
from gtts import gTTS

import db
import ai

# ==========================================
# KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(
    page_title="Knowledge Operating System",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==========================================
# DESIGN SYSTEM -- CSS Modern & Borderless List View
# ==========================================
st.markdown(
    """
    <style>
        :root {
            --kos-1: 4px; --kos-2: 8px; --kos-3: 12px;
            --kos-4: 16px; --kos-5: 24px; --kos-6: 32px;
            --kos-border: rgba(255,255,255,0.08);
            --kos-hover: rgba(255,255,255,0.06);
            --kos-muted: #71717a;
            --kos-radius: 8px;
        }

        .block-container {
            padding-top: var(--kos-5) !important;
            padding-bottom: var(--kos-5) !important;
            max-width: 1180px;
        }

        div[data-testid="stHorizontalBlock"] { gap: var(--kos-2) !important; }
        hr { margin: var(--kos-3) 0 !important; opacity: 0.5; }

        .st-key-kos-row button, .st-key-kos-row button p {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            justify-content: flex-start !important;
            text-align: left !important;
            font-weight: 400 !important;
            color: #e4e4e7 !important;
            padding: var(--kos-2) var(--kos-3) !important;
            border-radius: var(--kos-radius) !important;
            width: 100% !important;
        }
        .st-key-kos-row button:hover { background: var(--kos-hover) !important; }
        .st-key-kos-row button:disabled { color: #a1a1aa !important; opacity: 1 !important; }

        div[data-testid="stVerticalBlock"].st-key-kos-row {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
        }

        .st-key-kos-crumb button {
            background: transparent !important;
            border: 1px solid var(--kos-border) !important;
            box-shadow: none !important;
            padding: 4px var(--kos-3) !important;
            border-radius: 999px !important;
            font-size: 13px !important;
            color: var(--kos-muted) !important;
            width: auto !important;
        }
        .st-key-kos-crumb button:hover {
            color: #fff !important;
            border-color: rgba(255,255,255,0.24) !important;
        }

        div[data-testid="stPopover"] > button {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            width: 30px !important;
            min-width: 30px !important;
            height: 30px !important;
            border-radius: 50% !important;
            color: var(--kos-muted) !important;
        }
        div[data-testid="stPopover"] > button:hover {
            background: var(--kos-hover) !important;
            color: #fff !important;
        }
        div[data-testid="stPopover"] button svg:last-child {
            display: none !important;
        }

        .kos-label {
            font-size: 11px;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            color: var(--kos-muted);
            margin: var(--kos-4) 0 var(--kos-1) 0;
        }

        .st-key-kos-navbar { padding-bottom: var(--kos-3); }
        div[data-testid="stSidebarUserContent"] { padding-top: var(--kos-2) !important; }
    </style>
""",
    unsafe_allow_html=True,
)

for key, default in [
    ("user", None),
    ("auth_view", "login"),
    ("force_pw_change", False),
    ("current_session_id", None),
    ("fm_current_path", "/"),
    ("current_menu", "Chat KOS"),
    ("flash", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default


def logout():
    st.session_state.user = None
    st.session_state.auth_view = "login"
    st.session_state.force_pw_change = False
    st.session_state.current_session_id = None


def flash(message: str):
    st.session_state.flash = message


# ==========================================
# GERBANG MASUK
# ==========================================
def landing_page():
    st.write("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])

    with col2:
        with st.container(border=True):
            st.markdown(
                "<h2 style='text-align:center; margin-bottom:4px;'>Knowledge Operating System</h2>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<p style='text-align:center; color:#a1a1aa; margin-top:0;'>Sistem terpusat AI perusahaan</p>",
                unsafe_allow_html=True,
            )
            st.divider()

            if st.session_state.auth_view == "login":
                login_email = st.text_input("Email", key="log_email")
                login_pass = st.text_input("Password", type="password", key="log_pass")
                st.write("")
                if st.button(
                    "Login workspace",
                    type="primary",
                    use_container_width=True,
                    icon=":material/login:",
                ):
                    try:
                        user_data = db.get_user(login_email)
                        if user_data and db.verify_password(
                            login_pass, user_data.get("password", "")
                        ):
                            st.session_state.user = user_data
                            st.session_state.force_pw_change = user_data.get(
                                "must_change_password", False
                            )
                            st.session_state.fm_current_path = user_data[
                                "folder_access"
                            ]
                            st.rerun()
                        else:
                            st.error("Email atau password salah.")
                    except Exception:
                        st.error("Gagal terhubung ke database.")

                st.write("")
                if st.button(
                    "Daftar perusahaan baru (Admin)",
                    use_container_width=True,
                    icon=":material/domain_add:",
                ):
                    st.session_state.auth_view = "register"
                    st.rerun()
            else:
                reg_company = st.text_input("Nama perusahaan")
                reg_email = st.text_input("Email admin")
                reg_pass = st.text_input("Password", type="password")
                st.write("")
                if st.button(
                    "Buat perusahaan",
                    type="primary",
                    use_container_width=True,
                    icon=":material/domain_add:",
                ):
                    if reg_company and reg_email and reg_pass:
                        try:
                            db.register_company(reg_company, reg_email, reg_pass)
                            st.success("Berhasil didaftarkan. Silakan login.")
                        except ValueError as e:
                            st.error(str(e))
                    else:
                        st.warning("Lengkapi semua data.")

                if st.button("Kembali ke login", use_container_width=True):
                    st.session_state.auth_view = "login"
                    st.rerun()


def force_password_change():
    st.write("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.container(border=True):
            st.subheader("Buat password baru")
            new_pw = st.text_input("Password baru", type="password", key="new_pw")
            confirm = st.text_input(
                "Ulangi password", type="password", key="confirm_pw"
            )
            if st.button(
                "Simpan",
                type="primary",
                use_container_width=True,
                icon=":material/check:",
            ):
                if new_pw and new_pw == confirm:
                    db.update_password(st.session_state.user["email"], new_pw)
                    st.session_state.user["must_change_password"] = False
                    st.session_state.force_pw_change = False
                    st.rerun()
                else:
                    st.error("Password tidak cocok/kosong.")


# ==========================================
# NAVBAR GLOBAL
# ==========================================
def render_navbar():
    with st.container(key="kos-navbar"):
        company_name = st.session_state.user.get("company_name") or "Perusahaan"
        user_name = (
            st.session_state.user["email"].split("@")[0].replace(".", " ").title()
        )

        col1, col2 = st.columns([3, 1], vertical_alignment="center")
        with col1:
            st.markdown(
                f"<h4 style='margin:0;'>{company_name}</h4>", unsafe_allow_html=True
            )
        with col2:
            with st.popover(
                user_name, use_container_width=True, icon=":material/account_circle:"
            ):
                st.write(f"**{st.session_state.user['email']}**")
                st.caption(st.session_state.user.get("role", ""))
                st.divider()
                st.button(
                    "Logout",
                    on_click=logout,
                    use_container_width=True,
                    icon=":material/logout:",
                )
        st.divider()


# ==========================================
# SIDEBAR NAVIGASI + RIWAYAT CHAT
# ==========================================
def sidebar_nav(options: list, icons: list, current_menu: str):
    with st.sidebar:
        selected = option_menu(
            menu_title=None,
            options=options,
            icons=icons,
            default_index=options.index(current_menu) if current_menu in options else 0,
            styles={
                "container": {"padding": "0", "background-color": "transparent"},
                "icon": {"font-size": "15px", "color": "#71717a"},
                "nav-link": {"font-size": "14px", "margin": "2px 0"},
                "nav-link-selected": {"background-color": "#27272a"},
            },
        )

        if selected == "Chat KOS":
            st.divider()
            st.markdown("<p class='kos-label'>Riwayat</p>", unsafe_allow_html=True)
            if st.button("Chat baru", use_container_width=True, icon=":material/add:"):
                st.session_state.current_session_id = None
                st.rerun()

            with st.container(key="kos-row"):
                for s in db.list_chat_sessions(st.session_state.user["email"]):
                    title = s["title"] or "Percakapan baru"
                    c1, c2 = st.columns([5, 1], vertical_alignment="center")
                    with c1:
                        if st.button(
                            title[:22], key=f"sess_{s['id']}", use_container_width=True
                        ):
                            st.session_state.current_session_id = s["id"]
                            st.rerun()
                    with c2:
                        with st.popover(
                            "", icon=":material/more_vert:", key=f"opt_sess_{s['id']}"
                        ):
                            new_title = st.text_input(
                                "Ganti nama", value=title, key=f"rn_{s['id']}"
                            )
                            if st.button(
                                "Simpan", key=f"sv_{s['id']}", icon=":material/save:"
                            ):
                                db.rename_chat_session(s["id"], new_title)
                                st.rerun()
                            st.divider()
                            if st.button(
                                "Hapus",
                                key=f"rm_{s['id']}",
                                type="primary",
                                icon=":material/delete:",
                            ):
                                db.delete_chat_session(s["id"])
                                if st.session_state.current_session_id == s["id"]:
                                    st.session_state.current_session_id = None
                                st.rerun()
    return selected


# ==========================================
# CHAT KOS (STT/TTS Terintegrasi)
# ==========================================
def chat_page():
    user = st.session_state.user
    user_name = user["email"].split("@")[0].replace(".", " ").title()

    if not st.session_state.current_session_id:
        st.markdown(f"<h3>Selamat datang, {user_name}</h3>", unsafe_allow_html=True)
        st.caption(
            f"Ruang kerja aktif: {user['folder_access']} · AI hanya mencari dokumen di dalam folder Anda"
        )
        st.write("")

    if st.session_state.current_session_id:
        for m in db.get_chat_messages(st.session_state.current_session_id):
            with st.chat_message(m["role"]):
                st.write(m["content"])

    question = st.chat_input("Ketik pertanyaan Anda di sini...")
    audio_val = st.audio_input("Gunakan suara")

    final_query = question

    if not final_query and audio_val:
        with st.spinner("Menerjemahkan suara..."):
            with open("temp_audio_chat.wav", "wb") as f:
                f.write(audio_val.getbuffer())
            try:
                final_query = ai.extract_multimodal(
                    "temp_audio_chat.wav", "audio/wav", "Voice Prompt"
                )
            except Exception as e:
                st.error(f"Gagal memproses suara: {e}")
            finally:
                if os.path.exists("temp_audio_chat.wav"):
                    os.remove("temp_audio_chat.wav")

    if final_query:
        if not st.session_state.current_session_id:
            st.session_state.current_session_id = db.create_chat_session(
                user["email"], user["company_id"]
            )
            db.rename_chat_session(
                st.session_state.current_session_id, final_query[:30]
            )

        db.add_chat_message(st.session_state.current_session_id, "user", final_query)
        with st.chat_message("user"):
            st.write(final_query)

        with st.chat_message("assistant"):
            with st.spinner("Mencari referensi..."):
                try:
                    q_emb = ai.embed_text(final_query)
                    docs = db.search_documents(
                        q_emb,
                        company_id=user["company_id"],
                        match_count=3,
                        folder_prefix=user["folder_access"],
                    )
                    answer = (
                        ai.generate_answer(final_query, docs)
                        if docs
                        else "Tidak ada referensi dokumen ditemukan di folder Anda."
                    )
                    st.write(answer)

                    if docs and st.button(
                        "Dengarkan",
                        key=f"tts_{final_query[:20]}",
                        icon=":material/volume_up:",
                    ):
                        tts = gTTS(text=answer, lang="id")
                        tts.save("response.mp3")
                        st.audio("response.mp3")

                    db.add_chat_message(
                        st.session_state.current_session_id, "assistant", answer
                    )
                    st.rerun()

                except Exception as e:
                    st.error(f"Kesalahan pada mesin AI: {str(e)}")


# ==========================================
# FILE MANAGER (Universal Uploader Tahan Banting)
# ==========================================
def file_type_icon(metadata: dict) -> str:
    tipe = (metadata or {}).get("tipe_file", "")
    if tipe == "CSV Data":
        return ":material/bar_chart:"
    if tipe == "Media Transkrip":
        return ":material/videocam:"
    if tipe == "Dokumen PDF":
        return ":material/picture_as_pdf:"
    return ":material/description:"


@st.fragment
def file_manager_page():
    company_id = st.session_state.user["company_id"]
    user_role = st.session_state.user["role"]
    base_path = (
        st.session_state.user["folder_access"] if user_role == "Karyawan" else "/"
    )

    if not st.session_state.fm_current_path.startswith(base_path):
        st.session_state.fm_current_path = base_path

    current = st.session_state.fm_current_path

    parts = [p for p in current.strip("/").split("/") if p]
    with st.container(key="kos-crumb"):
        crumb_cols = st.columns(len(parts) + 1, gap="small")
        with crumb_cols[0]:
            if st.button("Drive", key="c_root", icon=":material/home:"):
                st.session_state.fm_current_path = base_path
                st.rerun(scope="fragment")
        accum = "/"
        for i, part in enumerate(parts):
            accum += part + "/"
            with crumb_cols[i + 1]:
                disabled = (user_role == "Karyawan") and (
                    not accum.startswith(base_path)
                )
                if st.button(part, key=f"c_{i}", disabled=disabled):
                    st.session_state.fm_current_path = accum
                    st.rerun(scope="fragment")

    st.write("")

    if user_role == "Admin":
        col_a, col_b, _ = st.columns([2, 2, 8])
        with col_a:
            with st.popover(
                "Folder baru",
                use_container_width=True,
                icon=":material/create_new_folder:",
            ):
                new_name = st.text_input("Nama folder")
                if st.button("Buat", type="primary", key="btn_create_folder"):
                    if new_name.strip():
                        db.create_folder(company_id, current + new_name.strip() + "/")
                        flash(f"Folder '{new_name.strip()}' dibuat.")
                        st.rerun(scope="fragment")
        with col_b:
            with st.popover(
                "Upload file", use_container_width=True, icon=":material/upload_file:"
            ):
                uploaded_files = st.file_uploader(
                    "Pilih file (PDF, TXT, MD, CSV, Audio, Video)",
                    accept_multiple_files=True,
                    label_visibility="collapsed",
                )
                if st.button("Proses file", type="primary", key="btn_process_upload"):
                    if not uploaded_files:
                        st.warning("Pilih minimal satu file dulu.")
                    else:
                        success_count = 0
                        error_logs = []

                        with st.spinner(
                            f"Memproses {len(uploaded_files)} file... (Mohon tunggu, ada jeda anti-spam)"
                        ):
                            for f in uploaded_files:
                                ext = f.name.split(".")[-1].lower()
                                try:
                                    if ext == "csv":
                                        df = pd.read_csv(f)
                                        for idx, row in df.iterrows():
                                            content = "\n".join(
                                                f"{c}: {v}" for c, v in row.items()
                                            )
                                            emb = ai.embed_text(content)
                                            db.insert_document(
                                                f"Baris {idx+1} - {f.name}",
                                                content,
                                                emb,
                                                company_id,
                                                current,
                                                {"tipe_file": "CSV Data"},
                                            )
                                            time.sleep(
                                                0.5
                                            )  # Jeda per baris (Anti-Spam)

                                    elif ext in ["txt", "md"]:
                                        content = f.getvalue().decode("utf-8")
                                        chunks = ai.chunk_text(content)
                                        for idx, chunk in enumerate(chunks):
                                            emb = ai.embed_text(chunk)
                                            title = (
                                                f.name
                                                if len(chunks) == 1
                                                else f"{f.name} (Part {idx+1})"
                                            )
                                            db.insert_document(
                                                title,
                                                chunk,
                                                emb,
                                                company_id,
                                                current,
                                                {"tipe_file": "Teks"},
                                            )
                                            time.sleep(
                                                0.5
                                            )  # Jeda per chunk (Anti-Spam)

                                    elif ext == "pdf":
                                        temp = f"temp_{f.name}"
                                        with open(temp, "wb") as file:
                                            file.write(f.getbuffer())
                                        content = ai.extract_multimodal(
                                            temp, "application/pdf", f.name
                                        )
                                        chunks = ai.chunk_text(content)
                                        for idx, chunk in enumerate(chunks):
                                            emb = ai.embed_text(chunk)
                                            title = (
                                                f.name
                                                if len(chunks) == 1
                                                else f"{f.name} (Part {idx+1})"
                                            )
                                            db.insert_document(
                                                title,
                                                chunk,
                                                emb,
                                                company_id,
                                                current,
                                                {"tipe_file": "Dokumen PDF"},
                                            )
                                            time.sleep(1)  # Jeda per chunk (Anti-Spam)
                                        if os.path.exists(temp):
                                            os.remove(temp)

                                    elif ext in ["mp4", "mp3", "mov", "wav"]:
                                        temp = f"temp_{f.name}"
                                        with open(temp, "wb") as file:
                                            file.write(f.getbuffer())
                                        mime = (
                                            "video/mp4"
                                            if ext in ["mp4", "mov"]
                                            else "audio/mp3"
                                        )
                                        content = ai.extract_multimodal(
                                            temp, mime, f.name
                                        )
                                        chunks = ai.chunk_text(content)
                                        for idx, chunk in enumerate(chunks):
                                            emb = ai.embed_text(chunk)
                                            title = (
                                                f.name
                                                if len(chunks) == 1
                                                else f"{f.name} (Part {idx+1})"
                                            )
                                            db.insert_document(
                                                title,
                                                chunk,
                                                emb,
                                                company_id,
                                                current,
                                                {"tipe_file": "Media Transkrip"},
                                            )
                                            time.sleep(1)  # Jeda per chunk (Anti-Spam)
                                        if os.path.exists(temp):
                                            os.remove(temp)

                                    else:
                                        error_logs.append(
                                            f"{f.name}: Format tidak didukung."
                                        )
                                        continue

                                    success_count += 1
                                    time.sleep(
                                        2
                                    )  # Jeda antar file penuh untuk mendinginkan mesin Google

                                except Exception as e:
                                    error_logs.append(f"{f.name}: {str(e)}")
                                    if "temp" in locals() and os.path.exists(temp):
                                        os.remove(temp)

                        if error_logs:
                            for msg in error_logs:
                                st.error(msg)

                        if success_count > 0:
                            flash(f"{success_count} file berhasil masuk ke {current}.")
                            if not error_logs:
                                st.rerun(scope="fragment")

    st.divider()

    children = db.list_child_folders(company_id, current)
    docs = db.list_documents_in_folder(company_id, current)

    if not children and not docs:
        st.caption("Direktori ini masih kosong.")
        return

    if children:
        st.markdown("<p class='kos-label'>Folder</p>", unsafe_allow_html=True)
        with st.container(key="kos-row"):
            for child in children:
                name = child.rstrip("/").split("/")[-1]
                row = st.columns([9, 1], vertical_alignment="center")
                with row[0]:
                    if st.button(
                        name,
                        key=f"nav_{child}",
                        icon=":material/folder:",
                        use_container_width=True,
                    ):
                        st.session_state.fm_current_path = child
                        st.rerun(scope="fragment")
                with row[1]:
                    if user_role == "Admin":
                        with st.popover(
                            "", icon=":material/more_vert:", key=f"opt_folder_{child}"
                        ):
                            rn_name = st.text_input(
                                "Ganti nama", value=name, key=f"rn_{child}"
                            )
                            if st.button(
                                "Simpan", key=f"sv_{child}", icon=":material/save:"
                            ):
                                db.rename_folder_cascade(company_id, child, rn_name)
                                st.rerun(scope="fragment")
                            st.divider()
                            if st.button(
                                "Hapus",
                                key=f"dl_{child}",
                                type="primary",
                                icon=":material/delete:",
                            ):
                                db.delete_folder_and_contents(company_id, child)
                                st.rerun(scope="fragment")

    if docs:
        st.markdown("<p class='kos-label'>File</p>", unsafe_allow_html=True)
        with st.container(key="kos-row"):
            for d in docs:
                title_short = (
                    d["title"] if len(d["title"]) <= 46 else d["title"][:46] + "..."
                )
                row = st.columns([7, 2, 1], vertical_alignment="center")
                with row[0]:
                    st.button(
                        title_short,
                        key=f"doc_{d['id']}",
                        icon=file_type_icon(d.get("metadata")),
                        use_container_width=True,
                        disabled=True,
                    )
                with row[1]:
                    st.caption((d.get("created_at") or "")[:10])
                with row[2]:
                    if user_role == "Admin":
                        with st.popover(
                            "", icon=":material/more_vert:", key=f"opt_doc_{d['id']}"
                        ):
                            mv_path = st.text_input(
                                "Pindah ke folder", value=current, key=f"mv_{d['id']}"
                            )
                            if st.button(
                                "Simpan",
                                key=f"mv_btn_{d['id']}",
                                icon=":material/drive_file_move:",
                            ):
                                db.move_document(d["id"], mv_path, company_id)
                                st.rerun(scope="fragment")
                            st.divider()
                            if st.button(
                                "Hapus",
                                key=f"dl_d_{d['id']}",
                                type="primary",
                                icon=":material/delete:",
                            ):
                                db.delete_document(d["id"])
                                st.rerun(scope="fragment")


# ==========================================
# MANAJEMEN TIM
# ==========================================
def admin_employee_management():
    company_id = st.session_state.user["company_id"]
    st.markdown("### Manajemen tim")

    col1, col2 = st.columns([1, 1])
    with col1:
        emails_text = st.text_area("Daftar email karyawan (pisahkan baris)", height=150)
    with col2:
        folders = db.get_unique_folders(company_id)
        selected_folder = st.selectbox("Pilih akses folder utama", folders)
        new_folder = st.text_input("Atau ketik manual (contoh: /Finance/)")
        final_folder = new_folder if new_folder else selected_folder

    if st.button("Daftarkan sekarang", type="primary", icon=":material/person_add:"):
        email_list = re.findall(
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", emails_text
        )
        if email_list:
            temp = db.add_users_bulk(email_list, final_folder, company_id)
            st.success(f"{len(temp)} karyawan ditambahkan ke {final_folder}.")
            st.dataframe(
                pd.DataFrame(
                    [{"Email": e, "Password sementara": p} for e, p in temp.items()]
                ),
                use_container_width=True,
            )
        else:
            st.warning("Tidak ada email valid ditemukan.")


# ==========================================
# ROUTING UTAMA
# ==========================================
if st.session_state.user is None:
    landing_page()
elif st.session_state.force_pw_change:
    force_password_change()
else:
    render_navbar()

    if st.session_state.flash:
        st.toast(st.session_state.flash, icon=":material/check_circle:")
        st.session_state.flash = None

    role = st.session_state.user["role"]
    menus = (
        ["Chat KOS", "File Manager", "Manajemen Tim"]
        if role == "Admin"
        else ["Chat KOS", "File Manager"]
    )
    icons = (
        ["chat-square-text", "folder2", "people"]
        if role == "Admin"
        else ["chat-square-text", "folder2"]
    )

    selected = sidebar_nav(menus, icons, st.session_state.current_menu)
    st.session_state.current_menu = selected

    if selected == "Chat KOS":
        chat_page()
    elif selected == "File Manager":
        file_manager_page()
    elif role == "Admin":
        admin_employee_management()
