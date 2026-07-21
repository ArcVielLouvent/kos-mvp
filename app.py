import re
import os
import time  # <-- LIBRARY JEDA WAKTU ANTI SPAM
import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu

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

        /* Header bawaan Streamlit dibuat TRANSPARAN, bukan disembunyikan total --
           supaya tombol buka/tutup sidebar di HP tetap berfungsi. Cuma menu titik-tiga
           dan footer yang disembunyikan lewat selector resmi Streamlit. */
        header[data-testid="stHeader"] {
            background: transparent !important;
            box-shadow: none !important;
        }
        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }

        .block-container {
            padding-top: 3.75rem !important;
            padding-bottom: var(--kos-5) !important;
            max-width: 1180px;
        }

        div[data-testid="stHorizontalBlock"] { gap: var(--kos-2) !important; }
        hr { margin: var(--kos-3) 0 !important; opacity: 0.5; }

        .st-key-kos-row-chathist button, .st-key-kos-row-chathist button p,
        .st-key-kos-row-folders button, .st-key-kos-row-folders button p,
        .st-key-kos-row-files button, .st-key-kos-row-files button p,
        .st-key-kos-row-picker button, .st-key-kos-row-picker button p {
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
        .st-key-kos-row-chathist button:hover, .st-key-kos-row-folders button:hover,
        .st-key-kos-row-files button:hover, .st-key-kos-row-picker button:hover {
            background: var(--kos-hover) !important;
        }
        .st-key-kos-row-files button:disabled { color: #a1a1aa !important; opacity: 1 !important; }

        div[data-testid="stVerticalBlock"].st-key-kos-row-chathist,
        div[data-testid="stVerticalBlock"].st-key-kos-row-folders,
        div[data-testid="stVerticalBlock"].st-key-kos-row-files,
        div[data-testid="stVerticalBlock"].st-key-kos-row-picker {
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

        /* Navbar sederhana, cuma nama perusahaan */
        .st-key-kos-navbar { padding-bottom: var(--kos-3); }

        /* Sidebar: dorong panel akun ke paling bawah */
        div[data-testid="stSidebarUserContent"] {
            padding-top: var(--kos-2) !important;
            display: flex !important;
            flex-direction: column !important;
            min-height: calc(100vh - 2rem) !important;
        }
        .st-key-kos-sidebar-account {
            margin-top: auto !important;
            padding-top: var(--kos-4) !important;
            border-top: 1px solid var(--kos-border);
        }
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
# NAVBAR GLOBAL — cuma nama perusahaan
# ==========================================
def render_navbar():
    with st.container(key="kos-navbar"):
        company_name = st.session_state.user.get("company_name") or "Perusahaan"
        st.markdown(
            f"<h4 style='margin:0;'>{company_name}</h4>", unsafe_allow_html=True
        )
        st.divider()


# ==========================================
# SIDEBAR NAVIGASI + RIWAYAT CHAT + AKUN (di bawah)
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

            with st.container(key="kos-row-chathist"):
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

        # --- Panel akun, selalu di paling bawah sidebar ---
        with st.container(key="kos-sidebar-account"):
            user_name = (
                st.session_state.user["email"].split("@")[0].replace(".", " ").title()
            )
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
    return selected


# ==========================================
# CHAT KOS
# ==========================================
def render_source_link(d: dict):
    """Video YouTube -> tampilkan video player langsung. Lainnya -> tombol download."""
    if d.get("metadata", {}).get("tipe_file") == "Video YouTube":
        st.caption(d["title"])
        st.video(d["file_url"])
    else:
        st.link_button(
            f"Unduh: {d['title']}", d["file_url"], icon=":material/download:"
        )


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

    if question:
        if not st.session_state.current_session_id:
            st.session_state.current_session_id = db.create_chat_session(
                user["email"], user["company_id"]
            )
            db.rename_chat_session(st.session_state.current_session_id, question[:30])

        db.add_chat_message(st.session_state.current_session_id, "user", question)
        with st.chat_message("user"):
            st.write(question)

        with st.chat_message("assistant"):
            with st.spinner("Mencari referensi..."):
                try:
                    q_emb = ai.embed_text(question)
                    docs = db.search_documents(
                        q_emb,
                        company_id=user["company_id"],
                        match_count=3,
                        folder_prefix=user["folder_access"],
                    )
                    if ai.is_file_request(question):
                        # Niat: minta file asli -- skip jawaban AI, langsung tombol download
                        if docs:
                            seen = set()
                            unique_docs = [
                                d
                                for d in docs
                                if d.get("file_url")
                                and not (d["id"] in seen or seen.add(d["id"]))
                            ]
                            if unique_docs:
                                answer = (
                                    f"Ditemukan {len(unique_docs)} dokumen yang sesuai:"
                                )
                                st.write(answer)
                                for d in unique_docs:
                                    render_source_link(d)
                            else:
                                answer = "Dokumen ditemukan, tapi file aslinya tidak tersedia untuk diunduh."
                                st.write(answer)
                        else:
                            answer = (
                                "Tidak ada dokumen yang cocok ditemukan di folder Anda."
                            )
                            st.write(answer)
                    else:
                        answer = (
                            ai.generate_answer(question, docs)
                            if docs
                            else "Tidak ada referensi dokumen ditemukan di folder Anda."
                        )
                        st.write(answer)

                        # Tombol/video sumber -- dedup, 1 per dokumen unik
                        if docs:
                            seen = set()
                            for d in docs:
                                if d.get("file_url") and d["id"] not in seen:
                                    seen.add(d["id"])
                                    render_source_link(d)

                    db.add_chat_message(
                        st.session_state.current_session_id, "assistant", answer
                    )
                except Exception as e:
                    answer = None
                    st.error(f"Kesalahan pada mesin AI: {str(e)}")

        if answer is not None:
            st.rerun()


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
    if tipe == "Dokumen Word":
        return ":material/article:"
    if tipe == "Presentasi":
        return ":material/slideshow:"
    if tipe == "Spreadsheet":
        return ":material/table_chart:"
    if tipe == "Gambar":
        return ":material/image:"
    if tipe == "Dokumen RTF":
        return ":material/description:"
    if tipe == "Video YouTube":
        return ":material/smart_display:"
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
        col_a, col_b, col_c, _ = st.columns([2, 2, 2, 6])
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
        with col_c:
            with st.popover(
                "Video YouTube",
                use_container_width=True,
                icon=":material/smart_display:",
            ):
                yt_title = st.text_input("Judul video", key="yt_title")
                yt_url = st.text_input(
                    "Link YouTube (unlisted/publik)",
                    key="yt_url",
                    placeholder="https://youtu.be/...",
                )
                yt_desc = st.text_area(
                    "Deskripsi singkat (opsional)", key="yt_desc", height=80
                )
                if st.button("Tambahkan", type="primary", key="btn_add_youtube"):
                    if yt_title.strip() and yt_url.strip():
                        with st.spinner("Menganalisis video..."):
                            enriched = ai.describe_youtube_video(yt_url.strip())
                            content = f"{yt_title}\n{yt_desc}"
                            if enriched:
                                content += f"\n\n{enriched}"
                            chunks = ai.chunk_text(content) or [content]
                            embeddings = ai.embed_chunks_parallel(chunks)
                            db.insert_document_with_chunks(
                                title=yt_title.strip(),
                                chunks=chunks,
                                embeddings=embeddings,
                                company_id=company_id,
                                folder_path=current,
                                metadata={"tipe_file": "Video YouTube"},
                                external_url=yt_url.strip(),
                            )
                        flash(f"Video '{yt_title.strip()}' ditambahkan.")
                        st.rerun(scope="fragment")
                    else:
                        st.warning("Judul dan link YouTube wajib diisi.")
        with col_b:
            with st.popover(
                "Upload file", use_container_width=True, icon=":material/upload_file:"
            ):
                uploaded_files = st.file_uploader(
                    "Pilih file (Dokumen, Gambar, Audio, Video, atau teks apa pun)",
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
                                temp = f"temp_{f.name}"
                                chunks = []
                                tipe_file = "Dokumen"

                                try:
                                    # ---------- CSV: 1 file = 1 chunk utuh ----------
                                    if ext == "csv":
                                        df = pd.read_csv(f)
                                        chunks = [
                                            ai.format_dataframe_as_text(
                                                df, sheet_name=f.name
                                            )
                                        ]
                                        tipe_file = "CSV Data"

                                    # ---------- XLSX: 1 sheet = 1 chunk utuh ----------
                                    elif ext == "xlsx":
                                        with open(temp, "wb") as file:
                                            file.write(f.getbuffer())
                                        sheets = ai.extract_xlsx_text(temp)
                                        chunks = [
                                            f"Sheet: {name}\n{content}"
                                            for name, content in sheets
                                        ]
                                        tipe_file = "Spreadsheet"

                                    # ---------- Teks terstruktur: baca langsung ----------
                                    elif ext in [
                                        "txt",
                                        "md",
                                        "json",
                                        "xml",
                                        "html",
                                        "htm",
                                        "yaml",
                                        "yml",
                                        "log",
                                    ]:
                                        content = f.getvalue().decode(
                                            "utf-8", errors="ignore"
                                        )
                                        chunks = ai.chunk_text(content)
                                        tipe_file = "Teks"

                                    # ---------- RTF ----------
                                    elif ext == "rtf":
                                        with open(temp, "wb") as file:
                                            file.write(f.getbuffer())
                                        content = ai.extract_rtf_text(temp)
                                        chunks = ai.chunk_text(content)
                                        tipe_file = "Dokumen RTF"

                                    # ---------- PDF: 3 tingkat, Gemini opsi TERAKHIR ----------
                                    elif ext == "pdf":
                                        with open(temp, "wb") as file:
                                            file.write(f.getbuffer())
                                        content = ai.extract_pdf_text_local(temp)
                                        if len(content.strip()) < 50:
                                            # Kemungkinan hasil scan -> coba OCR lokal (gratis)
                                            try:
                                                content = ai.extract_pdf_ocr_local(temp)
                                            except Exception:
                                                content = ""
                                        if len(content.strip()) < 50:
                                            # OCR lokal pun gagal -> baru pakai Gemini (pakai kuota)
                                            content = ai.extract_multimodal(
                                                temp, "application/pdf", f.name
                                            )
                                        chunks = ai.chunk_text(content)
                                        tipe_file = "Dokumen PDF"

                                    # ---------- DOCX ----------
                                    elif ext == "docx":
                                        with open(temp, "wb") as file:
                                            file.write(f.getbuffer())
                                        content = ai.extract_docx_text(temp)
                                        chunks = ai.chunk_text(content)
                                        tipe_file = "Dokumen Word"

                                    # ---------- PPTX ----------
                                    elif ext == "pptx":
                                        with open(temp, "wb") as file:
                                            file.write(f.getbuffer())
                                        content = ai.extract_pptx_text(temp)
                                        chunks = ai.chunk_text(content)
                                        tipe_file = "Presentasi"

                                    # ---------- DOC lama: tidak didukung ----------
                                    elif ext == "doc":
                                        error_logs.append(
                                            f"{f.name}: Format .doc lama belum didukung, "
                                            "simpan ulang sebagai .docx terlebih dahulu."
                                        )
                                        continue

                                    # ---------- Gambar ----------
                                    elif ext in [
                                        "jpg",
                                        "jpeg",
                                        "png",
                                        "webp",
                                        "gif",
                                        "bmp",
                                        "heic",
                                        "heif",
                                    ]:
                                        with open(temp, "wb") as file:
                                            file.write(f.getbuffer())
                                        image_mime = {
                                            "jpg": "image/jpeg",
                                            "jpeg": "image/jpeg",
                                            "png": "image/png",
                                            "webp": "image/webp",
                                            "gif": "image/gif",
                                            "bmp": "image/bmp",
                                            "heic": "image/heic",
                                            "heif": "image/heif",
                                        }
                                        content = ai.extract_multimodal(
                                            temp, image_mime[ext], f.name
                                        )
                                        chunks = ai.chunk_text(content)
                                        tipe_file = "Gambar"

                                    # ---------- Audio & Video ----------
                                    elif ext in [
                                        "mp4",
                                        "mov",
                                        "avi",
                                        "flv",
                                        "mpeg",
                                        "mpg",
                                        "webm",
                                        "wmv",
                                        "3gp",
                                        "mp3",
                                        "wav",
                                        "aiff",
                                        "aac",
                                        "ogg",
                                        "flac",
                                    ]:
                                        with open(temp, "wb") as file:
                                            file.write(f.getbuffer())
                                        video_mime = {
                                            "mp4": "video/mp4",
                                            "mov": "video/quicktime",
                                            "avi": "video/x-msvideo",
                                            "flv": "video/x-flv",
                                            "mpeg": "video/mpeg",
                                            "mpg": "video/mpeg",
                                            "webm": "video/webm",
                                            "wmv": "video/x-ms-wmv",
                                            "3gp": "video/3gpp",
                                        }
                                        audio_mime = {
                                            "mp3": "audio/mp3",
                                            "wav": "audio/wav",
                                            "aiff": "audio/aiff",
                                            "aac": "audio/aac",
                                            "ogg": "audio/ogg",
                                            "flac": "audio/flac",
                                        }
                                        mime = video_mime.get(ext) or audio_mime.get(
                                            ext
                                        )
                                        content = ai.extract_multimodal(
                                            temp, mime, f.name
                                        )
                                        chunks = ai.chunk_text(content)
                                        tipe_file = "Media Transkrip"

                                    # ---------- Fallback universal ----------
                                    else:
                                        try:
                                            content = f.getvalue().decode("utf-8")
                                        except UnicodeDecodeError:
                                            content = ""
                                        if content.strip():
                                            chunks = ai.chunk_text(content)
                                            tipe_file = "Teks (format lain)"
                                        else:
                                            error_logs.append(
                                                f"{f.name}: Format .{ext} tidak dikenali "
                                                "dan bukan file teks -- tidak bisa diproses."
                                            )
                                            continue

                                    # ---------- Blok bersama: embed + simpan (1x per file) ----------
                                    if not chunks:
                                        error_logs.append(
                                            f"{f.name}: Tidak ada teks yang bisa diekstrak."
                                        )
                                        continue

                                    embeddings = []
                                    for chunk in chunks:
                                        embeddings.append(ai.embed_text(chunk))
                                        time.sleep(0.5)

                                    db.insert_document_with_chunks(
                                        title=f.name,
                                        chunks=chunks,
                                        embeddings=embeddings,
                                        company_id=company_id,
                                        folder_path=current,
                                        metadata={"tipe_file": tipe_file},
                                        file_bytes=bytes(f.getbuffer()),
                                        original_filename=f.name,
                                    )

                                    success_count += 1
                                    time.sleep(2)

                                except Exception as e:
                                    error_logs.append(f"{f.name}: {str(e)}")

                                finally:
                                    if os.path.exists(temp):
                                        os.remove(temp)

                        if error_logs:
                            for msg in error_logs:
                                st.error(msg)

                        if success_count > 0:
                            flash(f"{success_count} file berhasil masuk ke {current}.")
                            if not error_logs:
                                st.rerun(scope="fragment")

    st.divider()

    if "fm_doc_page" not in st.session_state:
        st.session_state.fm_doc_page = 1
    if st.session_state.get("fm_doc_page_folder") != current:
        st.session_state.fm_doc_page = 1
        st.session_state.fm_doc_page_folder = current

    PAGE_SIZE = 20
    children = db.list_child_folders(company_id, current)
    docs, total_docs = db.list_documents_in_folder(
        company_id, current, page=st.session_state.fm_doc_page, page_size=PAGE_SIZE
    )

    if not children and total_docs == 0:
        st.caption("Direktori ini masih kosong.")
        return

    if children:
        st.markdown("<p class='kos-label'>Folder</p>", unsafe_allow_html=True)
        with st.container(key="kos-row-folders"):
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
        with st.container(key="kos-row-files"):
            for d in docs:
                title_short = (
                    d["title"] if len(d["title"]) <= 46 else d["title"][:46] + "..."
                )
                row = st.columns([6, 2, 2, 1], vertical_alignment="center")
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
                    if d.get("file_url"):
                        is_youtube = (
                            d.get("metadata", {}).get("tipe_file") == "Video YouTube"
                        )
                        st.link_button(
                            "Buka YouTube" if is_youtube else "Unduh asli",
                            d["file_url"],
                            icon=(
                                ":material/open_in_new:"
                                if is_youtube
                                else ":material/download:"
                            ),
                            use_container_width=True,
                        )
                with row[3]:
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

        # --- Navigasi halaman (bukan infinite scroll) ---
        total_pages = max(1, (total_docs + PAGE_SIZE - 1) // PAGE_SIZE)
        if total_pages > 1:
            st.write("")
            nav_cols = st.columns([1, 2, 1])
            with nav_cols[0]:
                if st.button(
                    "Sebelumnya",
                    disabled=(st.session_state.fm_doc_page <= 1),
                    icon=":material/chevron_left:",
                    key="fm_page_prev",
                ):
                    st.session_state.fm_doc_page -= 1
                    st.rerun(scope="fragment")
            with nav_cols[1]:
                st.markdown(
                    f"<p style='text-align:center; color:#71717a; margin:0;'>"
                    f"Halaman {st.session_state.fm_doc_page} dari {total_pages} "
                    f"({total_docs} file)</p>",
                    unsafe_allow_html=True,
                )
            with nav_cols[2]:
                if st.button(
                    "Berikutnya",
                    disabled=(st.session_state.fm_doc_page >= total_pages),
                    icon=":material/chevron_right:",
                    key="fm_page_next",
                ):
                    st.session_state.fm_doc_page += 1
                    st.rerun(scope="fragment")


# ==========================================
# TREE PICKER FOLDER (dipakai untuk memilih akses karyawan)
# ==========================================
def folder_picker(company_id: str, key_prefix: str) -> str:
    """Navigasi klik-masuk folder (bukan dropdown datar) untuk memilih 1 folder tujuan."""
    state_key = f"{key_prefix}_browse_path"
    if state_key not in st.session_state:
        st.session_state[state_key] = "/"

    current = st.session_state[state_key]

    parts = [p for p in current.strip("/").split("/") if p]
    with st.container(key="kos-crumb"):
        cols = st.columns(len(parts) + 1, gap="small")
        with cols[0]:
            if st.button("Drive", key=f"{key_prefix}_root", icon=":material/home:"):
                st.session_state[state_key] = "/"
                st.rerun()
        accum = "/"
        for i, part in enumerate(parts):
            accum += part + "/"
            with cols[i + 1]:
                if st.button(part, key=f"{key_prefix}_crumb_{i}"):
                    st.session_state[state_key] = accum
                    st.rerun()

    children = db.list_child_folders(company_id, current)

    if children:
        with st.container(key="kos-row-picker"):
            for child in children:
                name = child.rstrip("/").split("/")[-1]
                if st.button(
                    name,
                    key=f"{key_prefix}_nav_{child}",
                    icon=":material/folder:",
                    use_container_width=True,
                ):
                    st.session_state[state_key] = child
                    st.rerun()
    else:
        st.caption("Tidak ada sub-folder di sini.")

    st.divider()
    st.caption(f"Folder terpilih: `{current}`")
    return current


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
        st.caption("Telusuri folder tujuan akses")
        final_folder = folder_picker(company_id, key_prefix="emp_picker")

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
