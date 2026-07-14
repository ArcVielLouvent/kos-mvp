import re
import os
import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
from gtts import gTTS

import db
import ai

# ==========================================
# KONFIGURASI & CSS HACK (UI MEMANJANG/HORIZONTAL BORDERLESS)
# ==========================================
st.set_page_config(
    page_title="KOS Enterprise", layout="wide", initial_sidebar_state="expanded"
)

st.markdown(
    """
    <style>
        .block-container { padding-top: 2rem !important; }

        /* HACK 1: Tombol Titik Tiga Transparan & Tanpa Panah Bawah */
        div[data-testid="stPopover"] > button {
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            color: #a1a1aa !important;
            display: flex;
            justify-content: center;
            width: 32px !important;
            min-width: 0 !important;
        }
        div[data-testid="stPopover"] > button:hover {
            color: white !important;
            background-color: rgba(255,255,255,0.1) !important;
            border-radius: 50% !important;
        }
        /* Membunuh ikon panah chevron bawaan */
        div[data-testid="stPopover"] > button svg {
            display: none !important;
        }
        div[data-testid="stPopover"] > button::after {
            display: none !important;
        }

        /* HACK 2: Tombol Folder (Stealth) Rata Kiri */
        .stealth-btn button {
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            display: flex !important;
            justify-content: flex-start !important; /* Memaksa teks rata kiri */
        }
        .stealth-btn button div p {
            text-align: left !important;
            font-size: 15px !important;
            margin: 0 !important;
            font-weight: 500 !important;
        }
        .stealth-btn button:hover div p {
            color: #3b82f6 !important;
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
]:
    if key not in st.session_state:
        st.session_state[key] = default


def logout():
    st.session_state.user = None
    st.session_state.auth_view = "login"
    st.session_state.force_pw_change = False
    st.session_state.current_session_id = None


# ==========================================
# NAVBAR GLOBAL
# ==========================================
def render_navbar():
    company_name = st.session_state.user.get("company_name", "KOS Enterprise")
    user_name = st.session_state.user["email"].split("@")[0].replace(".", " ").title()

    col1, col2 = st.columns([3, 1], vertical_alignment="center")
    with col1:
        st.markdown(
            f"<h3 style='margin:0; padding:0;'>Perusahaan {company_name}</h3>",
            unsafe_allow_html=True,
        )
    with col2:
        with st.popover(f" {user_name}", use_container_width=True):
            st.write(f"**{st.session_state.user['email']}**")
            st.caption(f"Role: {st.session_state.user.get('role', '')}")
            st.divider()
            st.button(
                "Logout", on_click=logout, use_container_width=True, type="primary"
            )
    st.divider()


# ==========================================
# GERBANG MASUK
# ==========================================
def landing_page():
    st.write("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])

    with col2:
        with st.container(border=True):
            st.markdown(
                "<h2 style='text-align: center;'>KOS Enterprise</h2>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<p style='text-align: center; color: gray;'>Sistem Terpusat AI Perusahaan</p>",
                unsafe_allow_html=True,
            )
            st.divider()

            if st.session_state.auth_view == "login":
                login_email = st.text_input("Email", key="log_email")
                login_pass = st.text_input("Password", type="password", key="log_pass")
                st.write("")
                if st.button(
                    "Login Workspace", type="primary", use_container_width=True
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
                            st.error("Email atau Password salah.")
                    except Exception:
                        st.error("Gagal terhubung ke database.")

                st.write("")
                if st.button(
                    "Daftar Perusahaan Baru (Admin)", use_container_width=True
                ):
                    st.session_state.auth_view = "register"
                    st.rerun()
            else:
                reg_company = st.text_input("Nama Perusahaan")
                reg_email = st.text_input("Email Admin")
                reg_pass = st.text_input("Password", type="password")
                st.write("")
                if st.button(
                    "Buat Perusahaan", type="primary", use_container_width=True
                ):
                    if reg_company and reg_email and reg_pass:
                        try:
                            db.register_company(reg_company, reg_email, reg_pass)
                            st.success("Berhasil didaftarkan! Silakan Login.")
                        except ValueError as e:
                            st.error(str(e))
                    else:
                        st.warning("Lengkapi semua data.")

                if st.button("Kembali ke Login", use_container_width=True):
                    st.session_state.auth_view = "login"
                    st.rerun()


def force_password_change():
    st.write("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.container(border=True):
            st.subheader("Buat Password Baru")
            new_pw = st.text_input("Password baru", type="password", key="new_pw")
            confirm = st.text_input(
                "Ulangi password", type="password", key="confirm_pw"
            )
            if st.button("Simpan", type="primary", use_container_width=True):
                if new_pw and new_pw == confirm:
                    db.update_password(st.session_state.user["email"], new_pw)
                    st.session_state.user["must_change_password"] = False
                    st.session_state.force_pw_change = False
                    st.rerun()
                else:
                    st.error("Password tidak cocok/kosong.")


# ==========================================
# SIDEBAR KOMPAK & RIWAYAT CHAT
# ==========================================
def sidebar_nav(options: list, icons: list, current_menu: str):
    with st.sidebar:
        selected = option_menu(
            menu_title=None,
            options=options,
            icons=icons,
            default_index=options.index(current_menu) if current_menu in options else 0,
            styles={
                "container": {"padding": "0"},
                "icon": {"font-size": "15px", "color": "gray"},
                "nav-link": {"font-size": "14px", "margin": "2px"},
                "nav-link-selected": {"background-color": "#27272a"},
            },
        )

        if selected == "Chat KOS":
            st.divider()
            st.caption("RIWAYAT PERCAKAPAN")
            if st.button("+ Chat Baru", use_container_width=True):
                st.session_state.current_session_id = None
                st.rerun()

            sessions = db.list_chat_sessions(st.session_state.user["email"])
            for s in sessions:
                title = s["title"] if s["title"] else "Chat..."
                c1, c2 = st.columns([5, 1], vertical_alignment="center")
                with c1:
                    if st.button(
                        title[:18], key=f"sess_{s['id']}", use_container_width=True
                    ):
                        st.session_state.current_session_id = s["id"]
                        st.rerun()
                with c2:
                    with st.popover("⋮"):
                        new_title = st.text_input(
                            "Rename", value=title, key=f"rn_{s['id']}"
                        )
                        if st.button("Simpan", key=f"sv_{s['id']}"):
                            db.rename_chat_session(s["id"], new_title)
                            st.rerun()
                        if st.button("Hapus", key=f"rm_{s['id']}", type="primary"):
                            db.delete_chat_session(s["id"])
                            st.rerun()
    return selected


# ==========================================
# CHAT KOS (DENGAN MIKROFON & DASHBOARD)
# ==========================================
def chat_page():
    user = st.session_state.user
    user_name = user["email"].split("@")[0].replace(".", " ").title()

    if not st.session_state.current_session_id:
        st.markdown(f"<h2>Selamat Datang, {user_name}</h2>", unsafe_allow_html=True)
        st.write(f"Ruang Kerja Aktif: **{user['folder_access']}**")
        st.caption(
            "Tanyakan SOP, resep, atau panduan operasional. AI hanya mencari dokumen di dalam folder Anda."
        )
        st.write("<br>", unsafe_allow_html=True)

    if st.session_state.current_session_id:
        for m in db.get_chat_messages(st.session_state.current_session_id):
            with st.chat_message(m["role"]):
                st.write(m["content"])

    question = st.chat_input("Ketik pertanyaan Anda di sini...")
    audio_val = st.audio_input("Gunakan Suara (Microphone)")

    final_query = None

    if question:
        final_query = question
    elif audio_val:
        with st.spinner("Menerjemahkan suara..."):
            with open("temp_audio.wav", "wb") as f:
                f.write(audio_val.getbuffer())
            final_query = ai.extract_multimodal(
                "temp_audio.wav", "audio/wav", "Voice Prompt"
            )
            os.remove("temp_audio.wav")

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
                    else "Tidak ada referensi dokumen ditemukan."
                )

            st.write(answer)
            if docs:
                if st.button("Putar Audio", key=f"tts_{final_query[:20]}"):
                    tts = gTTS(text=answer, lang="id")
                    tts.save("response.mp3")
                    st.audio("response.mp3")

        db.add_chat_message(st.session_state.current_session_id, "assistant", answer)
        st.rerun()


# ==========================================
# FILE MANAGER (DESAIN HORIZONTAL PILL BORDERLESS)
# ==========================================
def file_manager_page():
    company_id = st.session_state.user["company_id"]
    user_role = st.session_state.user["role"]
    base_path = (
        st.session_state.user["folder_access"] if user_role == "Karyawan" else "/"
    )

    if not st.session_state.fm_current_path.startswith(base_path):
        st.session_state.fm_current_path = base_path

    current = st.session_state.fm_current_path

    # Breadcrumb Navigasi
    parts = [p for p in current.strip("/").split("/") if p]
    crumb_cols = st.columns(len(parts) + 2)
    with crumb_cols[0]:
        if st.button("Drive", key="c_root"):
            st.session_state.fm_current_path = base_path
            st.rerun()
    accum = "/"
    for i, part in enumerate(parts):
        accum += part + "/"
        with crumb_cols[i + 1]:
            disabled = (user_role == "Karyawan") and (not accum.startswith(base_path))
            if st.button(f"› {part}", key=f"c_{i}", disabled=disabled):
                st.session_state.fm_current_path = accum
                st.rerun()

    # Toolbar Tambah / Upload
    if user_role == "Admin":
        col_a, col_b, _ = st.columns([2, 2, 8])
        with col_a:
            with st.popover("+ New Folder", use_container_width=True):
                new_name = st.text_input("Nama Folder Baru")
                if st.button("Buat Folder", type="primary"):
                    if new_name:
                        db.create_folder(company_id, current + new_name.strip() + "/")
                        st.rerun()
        with col_b:
            with st.popover("↑ Upload File", use_container_width=True):
                uploaded_files = st.file_uploader(
                    "Upload ke sini", accept_multiple_files=True
                )
                if st.button("Proses File", type="primary"):
                    if uploaded_files:
                        for f in uploaded_files:
                            ext = f.name.split(".")[-1].lower()
                            with st.spinner(f"Memproses {f.name}..."):
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
                                elif ext in ["mp4", "mp3", "mov", "wav"]:
                                    temp = f"temp_{f.name}"
                                    with open(temp, "wb") as file:
                                        file.write(f.getbuffer())
                                    mime = (
                                        "video/mp4"
                                        if ext in ["mp4", "mov"]
                                        else "audio/mp3"
                                    )
                                    content = ai.extract_multimodal(temp, mime, f.name)
                                    emb = ai.embed_text(content)
                                    db.insert_document(
                                        f.name,
                                        content,
                                        emb,
                                        company_id,
                                        current,
                                        {"tipe_file": "Media Transkrip"},
                                    )
                                    os.remove(temp)
                                else:
                                    st.warning(f"Format {ext} belum didukung.")
                        st.rerun()
    st.divider()

    children = db.list_child_folders(company_id, current)
    docs = db.list_documents_in_folder(company_id, current)

    if not children and not docs:
        st.info("Direktori kosong.")

    # ==========================================
    # RENDER BORDERLESS: Ikon, Teks, Titik Tiga (1 Baris)
    # ==========================================
    if children:
        st.markdown("##### Folders")
        f_cols = st.columns(3)
        for i, child in enumerate(children):
            name = child.rstrip("/").split("/")[-1]
            with f_cols[i % 3]:
                # st.container(border=True) dihilangkan
                c_main, c_opt = st.columns([8, 1], vertical_alignment="center")

                with c_main:
                    st.markdown("<div class='stealth-btn'>", unsafe_allow_html=True)
                    if st.button(
                        f"📁  {name}", key=f"nav_{child}", use_container_width=True
                    ):
                        st.session_state.fm_current_path = child
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

                with c_opt:
                    if user_role == "Admin":
                        with st.popover("⋮"):
                            rn_name = st.text_input(
                                "Rename", value=name, key=f"rn_{child}"
                            )
                            if st.button("Simpan", key=f"sv_{child}"):
                                db.rename_folder_cascade(company_id, child, rn_name)
                                st.rerun()
                            st.divider()
                            if st.button(
                                "Hapus", key=f"dl_{child}", type="primary"
                            ):
                                db.delete_folder_and_contents(company_id, child)
                                st.rerun()

    if docs:
        st.write("<br>", unsafe_allow_html=True)
        st.markdown("##### Files")
        d_cols = st.columns(3)
        for i, d in enumerate(docs):
            with d_cols[i % 3]:
                # st.container(border=True) dihilangkan
                c_main, c_opt = st.columns([8, 1], vertical_alignment="center")

                with c_main:
                    tipe = d.get("metadata", {}).get("tipe_file", "Dokumen")
                    icon = (
                        "🎥"
                        if "Media" in tipe
                        else ("📊" if "CSV" in tipe else "📄")
                    )
                    title_short = (
                        d["title"][:30] + "..."
                        if len(d["title"]) > 30
                        else d["title"]
                    )

                    st.markdown(
                        f"<p style='margin:0; font-size: 15px; font-weight: 500;' title='{d['title']}'>{icon}  {title_short}</p>",
                        unsafe_allow_html=True,
                    )

                with c_opt:
                    if user_role == "Admin":
                        with st.popover("⋮"):
                            mv_path = st.text_input(
                                "Pindah Path", value=current, key=f"mv_{d['id']}"
                            )
                            if st.button("Simpan", key=f"mv_btn_{d['id']}"):
                                db.move_document(d["id"], mv_path, company_id)
                                st.rerun()
                            st.divider()
                            if st.button(
                                "Hapus", key=f"dl_d_{d['id']}", type="primary"
                            ):
                                db.delete_document(d["id"])
                                st.rerun()


# ==========================================
# MANAJEMEN KARYAWAN
# ==========================================
def admin_employee_management():
    company_id = st.session_state.user["company_id"]
    st.markdown("### Manajemen Tim")

    col1, col2 = st.columns([1, 1])
    with col1:
        emails_text = st.text_area("Daftar Email Karyawan (pisahkan baris)", height=150)
    with col2:
        folders = db.get_unique_folders(company_id)
        selected_folder = st.selectbox("Pilih Akses Folder Utama", folders)
        new_folder = st.text_input("Atau ketik manual (cth: /Finance/)")
        final_folder = new_folder if new_folder else selected_folder

    if st.button("Daftarkan Sekarang", type="primary"):
        email_list = re.findall(
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", emails_text
        )
        if email_list:
            temp = db.add_users_bulk(email_list, final_folder, company_id)
            st.success(f"{len(temp)} karyawan ditambahkan ke {final_folder}!")
            st.dataframe(
                pd.DataFrame(
                    [{"Email": e, "Password Sementara": p} for e, p in temp.items()]
                ),
                use_container_width=True,
            )


# ==========================================
# ROUTING UTAMA
# ==========================================
if "current_menu" not in st.session_state:
    st.session_state.current_menu = "Chat KOS"

if st.session_state.user is None:
    landing_page()
elif st.session_state.force_pw_change:
    force_password_change()
else:
    render_navbar()

    role = st.session_state.user["role"]
    menus = (
        ["Chat KOS", "File Manager", "Manajemen Tim"]
        if role == "Admin"
        else ["Chat KOS", "File Manager"]
    )
    icons = (
        ["chat-square-text", "grid", "people"]
        if role == "Admin"
        else ["chat-square-text", "grid"]
    )

    selected = sidebar_nav(menus, icons, st.session_state.current_menu)
    st.session_state.current_menu = selected

    if selected == "Chat KOS":
        chat_page()
    elif selected == "File Manager":
        file_manager_page()
    elif role == "Admin":
        admin_employee_management()