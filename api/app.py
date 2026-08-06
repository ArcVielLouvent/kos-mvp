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

        /* Cegah teks tombol melipat ke baris baru kalau kolomnya sempit */
        button { white-space: nowrap !important; }

        .st-key-kos-row-chathist button, .st-key-kos-row-chathist button p,
        .st-key-kos-row-folders button, .st-key-kos-row-folders button p,
        .st-key-kos-row-files button, .st-key-kos-row-files button p,
        .st-key-kos-row-directory-chat button, .st-key-kos-row-directory-chat button p,
        [class*="st-key-kos-row-picker"] button, [class*="st-key-kos-row-picker"] button p {
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
        .st-key-kos-row-files button:hover, [class*="st-key-kos-row-picker"] button:hover {
            background: var(--kos-hover) !important;
        }
        .st-key-kos-row-files button:disabled { color: #a1a1aa !important; opacity: 1 !important; }

        div[data-testid="stVerticalBlock"].st-key-kos-row-chathist,
        div[data-testid="stVerticalBlock"].st-key-kos-row-folders,
        div[data-testid="stVerticalBlock"].st-key-kos-row-files,
        div[data-testid="stVerticalBlock"][class*="st-key-kos-row-picker"] {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
        }

        [class*="st-key-kos-crumb"] button {
            background: transparent !important;
            border: 1px solid var(--kos-border) !important;
            box-shadow: none !important;
            padding: 4px var(--kos-3) !important;
            border-radius: 999px !important;
            font-size: 13px !important;
            color: var(--kos-muted) !important;
            width: auto !important;
        }
        [class*="st-key-kos-crumb"] button:hover {
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
    ("directory_selected_email", None),
    ("directory_chat_selected", None),
    ("last_draft", None),
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


def can_write(user: dict) -> bool:
    """SuperAdmin selalu bisa tulis. Admin cuma bisa kalau permission_level='crud'."""
    if user["role"] == "SuperAdmin":
        return True
    if user["role"] == "Admin":
        return user.get("permission_level", "crud") == "crud"
    return False


def is_admin_tier(user: dict) -> bool:
    """SuperAdmin atau Admin (untuk gating menu/halaman, bukan gating tulis)."""
    return user["role"] in ("SuperAdmin", "Admin")


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
                    "Daftar perusahaan baru (SuperAdmin)",
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
                for src in (m.get("sources") or []):
                    render_source_link(src)

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
                    docs = ai.filter_docs_by_intent(question, docs)
                    used_sources = []
                    seen = set()

                    if ai.is_generate_request(question):
                        # Niat: minta dokumen DIBUATKAN (bukan dicari)
                        if not can_write(user):
                            answer = "Membuat dokumen baru butuh akses tulis (CRUD). Hubungi Admin/SuperAdmin Anda."
                            st.write(answer)
                        else:
                            with st.spinner("AI sedang menyusun draf..."):
                                doc_type = ai.infer_doc_type(question)
                                draft_content = ai.generate_draft_document(question, doc_type)
                            answer = draft_content
                            st.warning(
                                "Draf berdasarkan pengetahuan umum AI -- BUKAN dokumen resmi. "
                                "Review dulu sebelum dipakai."
                            )
                            st.write(draft_content)
                            db.save_ai_draft(
                                user["company_id"], user["email"], question[:60], draft_content
                            )

                            branding = db.get_company_branding(user["company_id"])
                            logo_bytes = None
                            if branding.get("logo_url"):
                                try:
                                    logo_bytes = db.fetch_file_bytes(branding["logo_url"])
                                except Exception:
                                    logo_bytes = None

                            title_for_file = question[:50].strip() or "Dokumen"
                            col1, col2 = st.columns(2)
                            with col1:
                                if branding.get("docx_template_url"):
                                    try:
                                        template_bytes = db.fetch_file_bytes(branding["docx_template_url"])
                                        docx_bytes = ai.create_docx_from_template(
                                            template_bytes, title_for_file, draft_content
                                        )
                                    except Exception:
                                        docx_bytes = ai.create_docx_bytes(title_for_file, draft_content, logo_bytes)
                                else:
                                    docx_bytes = ai.create_docx_bytes(title_for_file, draft_content, logo_bytes)
                                st.download_button(
                                    "Download .docx", docx_bytes, file_name=f"{title_for_file}.docx",
                                    key=f"gen_docx_{st.session_state.current_session_id}_{len(question)}",
                                    icon=":material/download:",
                                )
                            with col2:
                                pdf_bytes = ai.create_pdf_bytes(title_for_file, draft_content, logo_bytes)
                                st.download_button(
                                    "Download .pdf", pdf_bytes, file_name=f"{title_for_file}.pdf",
                                    key=f"gen_pdf_{st.session_state.current_session_id}_{len(question)}",
                                    icon=":material/download:",
                                )

                    elif ai.is_analysis_request(question):
                        # Niat: analisis/rekomendasi dari data terstruktur (xlsx)
                        structured_docs = db.list_structured_documents(
                            user["company_id"], user["folder_access"]
                        )
                        if not structured_docs:
                            answer = "Tidak ada data terstruktur (XLSX) yang bisa dianalisis di folder akses Anda."
                            st.write(answer)
                        else:
                            q_lower = question.lower()
                            best_doc = next(
                                (d for d in structured_docs if any(
                                    w in q_lower for w in d["title"].lower().split() if len(w) > 3
                                )),
                                structured_docs[0],
                            )
                            sheets = best_doc.get("structured_data") or []
                            sheet = sheets[0] if sheets else None

                            if not sheet or not sheet.get("rows"):
                                answer = "Dataset ditemukan tapi tidak ada baris data untuk dianalisis."
                                st.write(answer)
                            else:
                                df = pd.DataFrame(sheet["rows"])
                                with st.spinner("AI menerjemahkan kriteria..."):
                                    criteria = ai.extract_analysis_criteria(question, list(df.columns))

                                if criteria.get("missing_info"):
                                    answer = f"Perlu klarifikasi: {criteria['missing_info']}"
                                    st.write(answer)
                                else:
                                    result_df = df.copy()
                                    for flt in criteria.get("filters", []):
                                        col, op, val = flt["column"], flt["operator"], flt["value"]
                                        if col not in result_df.columns:
                                            continue
                                        if op == ">=":
                                            result_df = result_df[pd.to_numeric(result_df[col], errors="coerce") >= float(val)]
                                        elif op == "<=":
                                            result_df = result_df[pd.to_numeric(result_df[col], errors="coerce") <= float(val)]
                                        elif op == "==":
                                            result_df = result_df[result_df[col].astype(str) == str(val)]
                                        elif op == "contains":
                                            result_df = result_df[result_df[col].astype(str).str.contains(str(val), case=False, na=False)]
                                    sort_by = criteria.get("sort_by")
                                    if sort_by and sort_by in result_df.columns:
                                        result_df = result_df.sort_values(
                                            sort_by, ascending=not criteria.get("sort_desc", False)
                                        )

                                    answer = (
                                        f"Berdasarkan data '{best_doc['title']}', ditemukan {len(result_df)} "
                                        f"baris cocok dari {len(df)} baris. (Bantuan awal, bukan analisis "
                                        f"profesional bersertifikat -- selalu verifikasi ulang.)"
                                    )
                                    st.write(answer)
                                    st.dataframe(result_df, use_container_width=True)
                                    xlsx_bytes = ai.create_xlsx_bytes(
                                        best_doc["title"][:31], result_df.to_dict("records")
                                    )
                                    st.download_button(
                                        "Download Hasil (.xlsx)", xlsx_bytes, file_name="Hasil Analisis.xlsx",
                                        key=f"analysis_xlsx_{st.session_state.current_session_id}_{len(question)}",
                                        icon=":material/download:",
                                    )

                    elif ai.is_file_request(question):
                        # Niat: minta file asli -- skip jawaban AI, langsung tombol download
                        if docs:
                            unique_docs = [
                                d for d in docs
                                if d.get("file_url") and not (d["id"] in seen or seen.add(d["id"]))
                            ]
                            if unique_docs:
                                answer = f"Ditemukan {len(unique_docs)} dokumen yang sesuai:"
                                st.write(answer)
                                for d in unique_docs:
                                    render_source_link(d)
                                used_sources = unique_docs
                            else:
                                answer = "Dokumen ditemukan, tapi file aslinya tidak tersedia untuk diunduh."
                                st.write(answer)
                        else:
                            answer = "Tidak ada dokumen yang cocok ditemukan di folder Anda."
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
                            for d in docs:
                                if d.get("file_url") and d["id"] not in seen:
                                    seen.add(d["id"])
                                    render_source_link(d)
                                    used_sources.append(d)

                    # Simpan sources minimal (bukan seluruh dict) supaya kolom jsonb ringkas
                    sources_to_save = [
                        {
                            "id": d["id"],
                            "title": d["title"],
                            "file_url": d.get("file_url"),
                            "metadata": d.get("metadata", {}),
                        }
                        for d in used_sources
                    ]

                    db.add_chat_message(
                        st.session_state.current_session_id, "assistant", answer,
                        sources=sources_to_save,
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
    user = st.session_state.user
    company_id = user["company_id"]
    user_role = user["role"]
    base_path = "/" if user_role == "SuperAdmin" else user["folder_access"]
    writable = can_write(user)

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
                disabled = (user_role != "SuperAdmin") and (
                    not accum.startswith(base_path)
                )
                if st.button(part, key=f"c_{i}", disabled=disabled):
                    st.session_state.fm_current_path = accum
                    st.rerun(scope="fragment")

    st.write("")

    if writable:
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
                "YouTube", use_container_width=True, icon=":material/smart_display:"
            ):
                yt_title = st.text_input("Judul video", key="yt_title")
                yt_url = st.text_input(
                    "Link YouTube (unlisted/publik)", key="yt_url",
                    placeholder="https://youtu.be/..."
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
                if "uploader_key_counter" not in st.session_state:
                    st.session_state.uploader_key_counter = 0

                uploaded_files = st.file_uploader(
                    "Pilih file (Dokumen, Gambar, Audio, Video, atau teks apa pun)",
                    accept_multiple_files=True,
                    label_visibility="collapsed",
                    key=f"file_uploader_{st.session_state.uploader_key_counter}",
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
                                structured_data = None

                                try:
                                    # ---------- CSV: 1 file = 1 chunk utuh ----------
                                    if ext == "csv":
                                        df = pd.read_csv(f)
                                        chunks = [
                                            ai.format_dataframe_as_text(df, sheet_name=f.name)
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
                                        try:
                                            structured_data = ai.extract_xlsx_structured(temp)
                                        except Exception:
                                            structured_data = None  # tetap lanjut, cuma tanpa fitur analisis
                                        tipe_file = "Spreadsheet"

                                    # ---------- Teks terstruktur: baca langsung ----------
                                    elif ext in [
                                        "txt", "md", "json", "xml",
                                        "html", "htm", "yaml", "yml", "log",
                                    ]:
                                        content = f.getvalue().decode("utf-8", errors="ignore")
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
                                        "jpg", "jpeg", "png", "webp",
                                        "gif", "bmp", "heic", "heif",
                                    ]:
                                        with open(temp, "wb") as file:
                                            file.write(f.getbuffer())
                                        image_mime = {
                                            "jpg": "image/jpeg", "jpeg": "image/jpeg",
                                            "png": "image/png", "webp": "image/webp",
                                            "gif": "image/gif", "bmp": "image/bmp",
                                            "heic": "image/heic", "heif": "image/heif",
                                        }
                                        content = ai.extract_multimodal(
                                            temp, image_mime[ext], f.name
                                        )
                                        chunks = ai.chunk_text(content)
                                        tipe_file = "Gambar"

                                    # ---------- Audio & Video ----------
                                    elif ext in [
                                        "mp4", "mov", "avi", "flv",
                                        "mpeg", "mpg", "webm", "wmv", "3gp",
                                        "mp3", "wav", "aiff", "aac", "ogg", "flac",
                                    ]:
                                        with open(temp, "wb") as file:
                                            file.write(f.getbuffer())
                                        video_mime = {
                                            "mp4": "video/mp4", "mov": "video/quicktime",
                                            "avi": "video/x-msvideo", "flv": "video/x-flv",
                                            "mpeg": "video/mpeg", "mpg": "video/mpeg",
                                            "webm": "video/webm", "wmv": "video/x-ms-wmv",
                                            "3gp": "video/3gpp",
                                        }
                                        audio_mime = {
                                            "mp3": "audio/mp3", "wav": "audio/wav",
                                            "aiff": "audio/aiff", "aac": "audio/aac",
                                            "ogg": "audio/ogg", "flac": "audio/flac",
                                        }
                                        mime = video_mime.get(ext) or audio_mime.get(ext)
                                        content = ai.extract_multimodal(temp, mime, f.name)
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
                                        structured_data=structured_data,
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
                                # Semua sukses -> reset uploader jadi kosong
                                st.session_state.uploader_key_counter += 1
                                st.rerun(scope="fragment")
                            # Ada yang gagal -> uploader TIDAK direset, file masih ada
                            # supaya bisa dihapus manual (file yang sukses) dan
                            # diproses ulang (file yang gagal) tanpa upload ulang semua.

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

    # --- State selection bulk, reset kalau pindah folder ---
    if st.session_state.get("fm_select_folder") != current:
        st.session_state.fm_selected_folders = set()
        st.session_state.fm_selected_docs = set()
        st.session_state.fm_select_folder = current

    selected_folders = st.session_state.fm_selected_folders
    selected_docs = st.session_state.fm_selected_docs
    total_selected = len(selected_folders) + len(selected_docs)

    if writable and total_selected > 0:
        sel_cols = st.columns([3, 2, 7])
        with sel_cols[0]:
            st.markdown(
                f"<p style='padding-top:8px; color:#a1a1aa;'>{total_selected} dipilih</p>",
                unsafe_allow_html=True,
            )
        with sel_cols[1]:
            if st.button(
                "Hapus terpilih", type="primary", icon=":material/delete_sweep:",
                key="btn_bulk_delete",
            ):
                for fpath in list(selected_folders):
                    db.delete_folder_and_contents(company_id, fpath)
                for did in list(selected_docs):
                    db.delete_document(did)
                st.session_state.fm_selected_folders = set()
                st.session_state.fm_selected_docs = set()
                flash(f"{total_selected} item berhasil dihapus.")
                st.rerun(scope="fragment")
        st.write("")

    if children:
        st.markdown("<p class='kos-label'>Folder</p>", unsafe_allow_html=True)
        with st.container(key="kos-row-folders"):
            for child in children:
                name = child.rstrip("/").split("/")[-1]
                if writable:
                    row = st.columns([0.6, 8.4, 1], vertical_alignment="center")
                    with row[0]:
                        checked = st.checkbox(
                            "", key=f"chk_folder_{child}",
                            value=(child in selected_folders),
                            label_visibility="collapsed",
                        )
                        if checked:
                            selected_folders.add(child)
                        else:
                            selected_folders.discard(child)
                    nav_col, opt_col = row[1], row[2]
                else:
                    row = st.columns([9, 1], vertical_alignment="center")
                    nav_col, opt_col = row[0], row[1]

                with nav_col:
                    if st.button(
                        name,
                        key=f"nav_{child}",
                        icon=":material/folder:",
                        use_container_width=True,
                    ):
                        st.session_state.fm_current_path = child
                        st.rerun(scope="fragment")
                with opt_col:
                    if writable:
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
                if writable:
                    row = st.columns([0.6, 5.4, 2, 2, 1], vertical_alignment="center")
                    with row[0]:
                        checked = st.checkbox(
                            "", key=f"chk_doc_{d['id']}",
                            value=(d["id"] in selected_docs),
                            label_visibility="collapsed",
                        )
                        if checked:
                            selected_docs.add(d["id"])
                        else:
                            selected_docs.discard(d["id"])
                    title_col, date_col, link_col, opt_col = row[1], row[2], row[3], row[4]
                else:
                    row = st.columns([6, 2, 2, 1], vertical_alignment="center")
                    title_col, date_col, link_col, opt_col = row[0], row[1], row[2], row[3]

                with title_col:
                    st.button(
                        title_short,
                        key=f"doc_{d['id']}",
                        icon=file_type_icon(d.get("metadata")),
                        use_container_width=True,
                        disabled=True,
                    )
                with date_col:
                    st.caption((d.get("created_at") or "")[:10])
                with link_col:
                    if d.get("file_url"):
                        is_youtube = (
                            d.get("metadata", {}).get("tipe_file") == "Video YouTube"
                        )
                        st.link_button(
                            "Buka YouTube" if is_youtube else "Unduh asli",
                            d["file_url"],
                            icon=":material/open_in_new:" if is_youtube else ":material/download:",
                            use_container_width=True,
                        )
                with opt_col:
                    if writable:
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
    with st.container(key=f"kos-crumb-{key_prefix}"):
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
        with st.container(key=f"kos-row-picker-{key_prefix}"):
            for child in children:
                name = child.rstrip("/").split("/")[-1]
                if st.button(
                    name, key=f"{key_prefix}_nav_{child}",
                    icon=":material/folder:", use_container_width=True,
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
    user = st.session_state.user
    company_id = user["company_id"]
    st.markdown("### Manajemen tim")

    if not can_write(user):
        st.info(
            "Akun Anda bertipe **read-only** -- tidak bisa menambah/mengubah tim. "
            "Hubungi SuperAdmin kalau perlu perubahan."
        )
        return

    tabs = ["Tambah Karyawan"]
    if user["role"] == "SuperAdmin":
        tabs.append("Tambah Admin")
    tabs.append("Branding")
    tab_objs = st.tabs(tabs)

    with tab_objs[0]:
        col1, col2 = st.columns([1, 1])
        with col1:
            emails_text = st.text_area(
                "Daftar email karyawan (pisahkan baris)", height=120, key="emp_emails"
            )
            position_title = st.text_input(
                "Jabatan (opsional, berlaku untuk semua email di atas)",
                key="emp_position",
                placeholder="mis. Barista, Staf Administrasi",
            )
        with col2:
            st.caption("Telusuri folder tujuan akses")
            final_folder = folder_picker(company_id, key_prefix="emp_picker")

        if st.button("Daftarkan sekarang", type="primary", icon=":material/person_add:"):
            email_list = re.findall(
                r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", emails_text
            )
            if email_list:
                temp = db.add_users_bulk(
                    email_list, final_folder, company_id, position_title=position_title
                )
                st.success(f"{len(temp)} karyawan ditambahkan ke {final_folder}.")
                st.dataframe(
                    pd.DataFrame(
                        [{"Email": e, "Password sementara": p} for e, p in temp.items()]
                    ),
                    use_container_width=True,
                )
            else:
                st.warning("Tidak ada email valid ditemukan.")

    if user["role"] == "SuperAdmin":
        with tab_objs[1]:
            st.caption("Admin baru akan mengelola folder yang dipilih di bawah dan turunannya.")
            col1, col2 = st.columns([1, 1])
            with col1:
                admin_email = st.text_input("Email Admin baru", key="new_admin_email")
                admin_position = st.text_input(
                    "Jabatan (opsional)", key="new_admin_position",
                    placeholder="mis. Manajer Keuangan",
                )
                admin_permission = st.radio(
                    "Level akses",
                    ["crud", "read_only"],
                    format_func=lambda x: "CRUD (bisa ubah/hapus)" if x == "crud" else "Read-only (lihat saja)",
                    key="new_admin_permission",
                )
            with col2:
                st.caption("Telusuri folder yang dikelola Admin ini")
                admin_folder = folder_picker(company_id, key_prefix="admin_picker")

            if st.button("Tambahkan Admin", type="primary", icon=":material/admin_panel_settings:"):
                if admin_email.strip():
                    temp_pw = db.add_admin(
                        admin_email, admin_folder, admin_permission, company_id,
                        position_title=admin_position,
                    )
                    st.success(f"Admin '{admin_email}' ditambahkan, mengelola folder {admin_folder}.")
                    st.info(f"Password sementara: `{temp_pw}`")
                else:
                    st.warning("Email wajib diisi.")

    with tab_objs[-1]:
        st.caption(
            "Logo & template dipakai otomatis saat AI membuatkan dokumen lewat Chat KOS "
            "(ketik mis. 'buatkan SOP...' di chat)."
        )
        branding = db.get_company_branding(company_id)
        col1, col2 = st.columns(2)
        with col1:
            st.caption("Logo perusahaan" + (" -- sudah ada" if branding.get("logo_url") else " -- belum diupload"))
            logo_file = st.file_uploader("Upload logo (PNG/JPG)", type=["png", "jpg", "jpeg"], key="logo_upload")
            if logo_file and st.button("Simpan Logo", key="save_logo"):
                db.upload_company_logo(company_id, bytes(logo_file.getbuffer()), logo_file.name)
                st.success("Logo tersimpan.")
                st.rerun()
        with col2:
            st.caption("Template surat .docx" + (" -- sudah ada" if branding.get("docx_template_url") else " -- belum diupload"))
            template_file = st.file_uploader("Upload template kosongan (.docx)", type=["docx"], key="template_upload")
            if template_file and st.button("Simpan Template", key="save_template"):
                db.upload_company_template(company_id, bytes(template_file.getbuffer()), template_file.name)
                st.success("Template tersimpan.")
                st.rerun()


# ==========================================
# DIREKTORI KARYAWAN + DETAIL RIWAYAT
# ==========================================
def employee_directory_page():
    user = st.session_state.user
    company_id = user["company_id"]

    if st.session_state.get("directory_selected_email"):
        employee_detail_page(st.session_state.directory_selected_email)
        return

    st.markdown("### Direktori Karyawan")
    st.caption(
        "Menampilkan akun dalam cakupan folder Anda."
        if user["role"] != "SuperAdmin"
        else "Menampilkan seluruh akun di perusahaan."
    )

    users_list = db.list_managed_users(company_id, user["folder_access"], user["role"])

    if not users_list:
        st.caption("Belum ada karyawan/admin di cakupan Anda.")
        return

    with st.container(key="kos-row-directory"):
        header = st.columns([3, 2, 2, 2, 2])
        for col, label in zip(header, ["Email", "Jabatan", "Posisi Web", "Kontrol", "Folder"]):
            col.caption(label.upper())

        for u in users_list:
            row = st.columns([3, 2, 2, 2, 2])
            with row[0]:
                if st.button(u["email"], key=f"dir_{u['email']}", use_container_width=True):
                    st.session_state.directory_selected_email = u["email"]
                    st.session_state.directory_chat_selected = None
                    st.rerun()
            with row[1]:
                st.write(u.get("position_title") or "-")
            with row[2]:
                # Dari POV Admin biasa, siapa pun di bawahnya cukup tampil "User"
                pov_role = u["role"] if user["role"] == "SuperAdmin" else (
                    "Admin" if u["role"] in ("SuperAdmin", "Admin") else "User"
                )
                st.write(pov_role)
            with row[3]:
                if u["role"] in ("SuperAdmin", "Admin"):
                    st.write("CRUD" if u.get("permission_level", "crud") == "crud" else "Read-only")
                else:
                    st.write("-")
            with row[4]:
                st.caption(u["folder_access"])


def employee_detail_page(email: str):
    if st.button("< Kembali ke Riwayat Tim", key="back_to_directory"):
        st.session_state.directory_selected_email = None
        st.session_state.directory_chat_selected = None
        st.rerun()

    st.markdown(f"### Riwayat: {email}")

    tab1, tab2, tab3 = st.tabs(["Riwayat Chat", "Laporan Kerjaan", "Skor Kuis"])

    with tab1:
        sessions = db.list_chat_sessions(email)
        if not sessions:
            st.caption("Belum ada riwayat chat.")
        else:
            col_list, col_view = st.columns([1, 2])
            with col_list:
                st.caption("Pilih percakapan")
                with st.container(key="kos-row-directory-chat", height=400):
                    for s in sessions:
                        active = s["id"] == st.session_state.get("directory_chat_selected")
                        label = ("• " if active else "") + (s["title"] or "Percakapan")
                        if st.button(label, key=f"dirchat_{s['id']}", use_container_width=True):
                            st.session_state.directory_chat_selected = s["id"]
                            st.rerun()
            with col_view:
                selected_session = st.session_state.get("directory_chat_selected")
                if not selected_session:
                    st.caption("Pilih percakapan di sebelah kiri untuk lihat isinya.")
                else:
                    with st.container(height=400):
                        for m in db.get_chat_messages(selected_session):
                            with st.chat_message(m["role"]):
                                st.write(m["content"])
                                for src in (m.get("sources") or []):
                                    render_source_link(src)

    with tab2:
        reports = db.get_user_reports(email)
        if not reports:
            st.caption("Belum ada laporan kerjaan.")
        for r in reports:
            with st.container(border=True):
                st.caption((r.get("created_at") or "")[:16].replace("T", " "))
                if r.get("content"):
                    st.write(r["content"])
                if r.get("media_url"):
                    if r.get("media_type") == "video":
                        st.video(r["media_url"])
                    elif r.get("media_type") == "audio":
                        st.audio(r["media_url"])

    with tab3:
        attempts = db.get_user_quiz_attempts(email)
        if not attempts:
            st.caption("Belum ada kuis yang dikerjakan.")
        for a in attempts:
            quiz_title = (a.get("quizzes") or {}).get("title", "Kuis")
            status = "✅ Lulus" if a["passed"] else "❌ Belum lulus"
            col1, col2, col3 = st.columns([3, 2, 2])
            with col1:
                st.write(f"**{quiz_title}**")
            with col2:
                st.write(f"{a['score']} ({status})")
            with col3:
                st.caption((a.get("created_at") or "")[:16].replace("T", " "))
            st.divider()


# ==========================================
# LAPOR KERJAAN (KARYAWAN)
# ==========================================
def lapor_kerjaan_page():
    user = st.session_state.user
    st.markdown("### Lapor Kerjaan")
    st.caption("Ceritakan pekerjaan hari ini -- lewat teks, atau rekam video/audio.")

    report_text = st.text_area("Tulis laporan (opsional kalau upload media)", height=120)
    media_file = st.file_uploader(
        "Atau upload video/audio (opsional)", type=["mp4", "mov", "mp3", "wav", "m4a"]
    )

    if st.button("Kirim Laporan", type="primary", icon=":material/send:"):
        if not report_text.strip() and not media_file:
            st.warning("Isi laporan teks atau upload media dulu.")
            return

        media_url = None
        media_type = "text"
        with st.spinner("Menyimpan laporan..."):
            if media_file:
                ext = media_file.name.split(".")[-1].lower()
                media_type = "video" if ext in ["mp4", "mov"] else "audio"
                temp = f"temp_report_{media_file.name}"
                try:
                    with open(temp, "wb") as f:
                        f.write(media_file.getbuffer())
                    media_url = db.upload_report_media(
                        user["company_id"], user["email"],
                        bytes(media_file.getbuffer()), media_file.name,
                    )
                except Exception as e:
                    st.error(f"Gagal upload media: {e}")
                finally:
                    if os.path.exists(temp):
                        os.remove(temp)

            db.add_report(
                user["email"], user["company_id"],
                content=report_text.strip() or None,
                media_url=media_url, media_type=media_type,
            )
        st.success("Laporan terkirim.")
        st.rerun()

    st.divider()
    st.markdown("#### Laporan Saya Sebelumnya")
    for r in db.get_user_reports(user["email"]):
        with st.container(border=True):
            st.caption((r.get("created_at") or "")[:16].replace("T", " "))
            if r.get("content"):
                st.write(r["content"])
            if r.get("media_url"):
                if r.get("media_type") == "video":
                    st.video(r["media_url"])
                elif r.get("media_type") == "audio":
                    st.audio(r["media_url"])


# ==========================================
# KUIS TRAINING (KARYAWAN mengerjakan)
# ==========================================
def kuis_page():
    user = st.session_state.user
    st.markdown("### Kuis Training")

    quizzes = db.list_quizzes_for_folder(user["company_id"], user["folder_access"])
    if not quizzes:
        st.caption("Belum ada kuis tersedia untuk folder Anda.")
        return

    my_attempts = db.get_user_quiz_attempts(user["email"])
    best_status = {}  # quiz_id -> True kalau pernah lulus
    for a in my_attempts:
        qid = a["quiz_id"]
        if a["passed"] or qid not in best_status:
            best_status[qid] = a["passed"]

    def label_with_status(qid):
        title = next(q["title"] for q in quizzes if q["id"] == qid)
        if qid not in best_status:
            return f"{title} (Belum dikerjakan)"
        return f"{title} ({'Sudah lulus' if best_status[qid] else 'Belum lulus'})"

    quiz_ids = [q["id"] for q in quizzes]
    selected_id = st.selectbox(
        "Pilih kuis", options=quiz_ids, format_func=label_with_status,
    )

    quiz = db.get_quiz(selected_id)
    if not quiz:
        return

    st.write(f"**{quiz['title']}** -- nilai minimal lulus: {quiz['passing_score']}")

    answers = {}
    with st.form(key=f"quiz_form_{selected_id}"):
        for i, q in enumerate(quiz["questions"]):
            answers[i] = st.radio(
                q["question"], options=list(range(4)),
                format_func=lambda idx, opts=q["options"]: opts[idx],
                key=f"quiz_{selected_id}_{i}",
            )
        submitted = st.form_submit_button("Kumpulkan Jawaban", type="primary")

    if submitted:
        total = len(quiz["questions"])
        correct = sum(
            1 for i, q in enumerate(quiz["questions"])
            if answers.get(i) == q["correct_index"]
        )
        score = round((correct / total) * 100) if total else 0
        passed = score >= quiz["passing_score"]

        db.save_quiz_attempt(
            selected_id, user["email"], user["company_id"],
            score, total, passed, answers,
        )

        if passed:
            st.success(f"Lulus! Skor: {score} ({correct}/{total} benar)")
        else:
            st.error(f"Belum lulus. Skor: {score} ({correct}/{total} benar) -- coba lagi.")
        st.caption("Refresh/pilih ulang kuis untuk lihat status terbaru di daftar riwayat.")

    st.divider()
    st.markdown("#### Riwayat Skor Saya")
    if not my_attempts:
        st.caption("Belum pernah mengerjakan kuis apa pun.")
    for a in my_attempts:
        quiz_title = next(
            (q["title"] for q in quizzes if q["id"] == a["quiz_id"]), "Kuis"
        )
        status = "✅ Lulus" if a["passed"] else "❌ Belum lulus"
        col1, col2, col3 = st.columns([3, 2, 2])
        with col1:
            st.write(f"**{quiz_title}**")
        with col2:
            st.write(f"{a['score']} ({status})")
        with col3:
            st.caption((a.get("created_at") or "")[:16].replace("T", " "))
        st.divider()


# ==========================================
# KELOLA KUIS (ADMIN/SUPERADMIN membuat kuis)
# ==========================================
def kelola_kuis_page():
    user = st.session_state.user
    company_id = user["company_id"]
    st.markdown("### Kelola Kuis")

    if not can_write(user):
        st.info("Akun read-only tidak bisa membuat kuis.")
        return

    st.caption("Telusuri ke folder tempat dokumen sumber berada")
    target_folder = folder_picker(company_id, key_prefix="quiz_picker")
    docs, _ = db.list_documents_in_folder(company_id, target_folder, page=1, page_size=100)

    if not docs:
        st.caption("Tidak ada dokumen di folder ini.")
        return

    doc_titles = {d["id"]: d["title"] for d in docs}
    selected_doc_id = st.selectbox(
        "Pilih dokumen sumber", options=list(doc_titles.keys()),
        format_func=lambda did: doc_titles[did],
    )
    quiz_title = st.text_input("Judul kuis", value=doc_titles.get(selected_doc_id, ""))
    num_questions = st.slider("Jumlah soal", 3, 10, 5)
    passing_score = st.slider("Nilai minimal lulus", 50, 100, 70, step=5)

    if st.button("Generate Kuis dari Dokumen", type="primary", icon=":material/auto_awesome:"):
        selected_doc = next((d for d in docs if d["id"] == selected_doc_id), None)
        content = (selected_doc or {}).get("content", "")
        if not content.strip():
            st.warning("Dokumen ini tidak punya cukup teks untuk dibuatkan soal.")
            return
        with st.spinner("AI sedang membuat soal..."):
            try:
                questions = ai.generate_quiz_questions(content, num_questions)
            except Exception as e:
                st.error(f"Gagal generate soal: {e}")
                return
        if not questions:
            st.error("AI tidak menghasilkan soal yang valid, coba lagi.")
            return
        db.create_quiz(
            company_id, target_folder, quiz_title.strip() or doc_titles[selected_doc_id],
            questions, source_document_id=selected_doc_id, passing_score=passing_score,
        )
        st.success(f"Kuis '{quiz_title}' dengan {len(questions)} soal berhasil dibuat.")
        with st.expander("Lihat soal yang dibuat"):
            for i, q in enumerate(questions, 1):
                st.write(f"**{i}. {q['question']}**")
                for j, opt in enumerate(q["options"]):
                    marker = "✓" if j == q["correct_index"] else "-"
                    st.write(f"{marker} {opt}")



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

    if role in ("SuperAdmin", "Admin"):
        menus = [
            "Chat KOS", "File Manager", "Manajemen Tim", "Riwayat Tim", "Kelola Kuis",
        ]
        icons = [
            "chat-square-text", "folder2", "people", "clock-history", "clipboard-check",
        ]
    else:
        menus = ["Chat KOS", "File Manager", "Lapor Kerjaan", "Kuis"]
        icons = ["chat-square-text", "folder2", "camera-video", "patch-question"]

    selected = sidebar_nav(menus, icons, st.session_state.current_menu)
    st.session_state.current_menu = selected

    if selected == "Chat KOS":
        chat_page()
    elif selected == "File Manager":
        file_manager_page()
    elif selected == "Manajemen Tim":
        admin_employee_management()
    elif selected == "Riwayat Tim":
        employee_directory_page()
    elif selected == "Kelola Kuis":
        kelola_kuis_page()
    elif selected == "Lapor Kerjaan":
        lapor_kerjaan_page()
    elif selected == "Kuis":
        kuis_page()