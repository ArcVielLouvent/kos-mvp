"use client";
import { useState, useEffect } from "react";
import {
  Mail, Briefcase, Shield, FolderOpen, MessageSquare, ArrowLeft,
  Search, FileText, Award, CheckCircle2, XCircle, Pencil, Check, X, Phone, IdCard, Users,
} from "lucide-react";
import { apiJson } from "@/lib/api";
import { cn } from "@/lib/utils";

type Tab = "chat" | "reports" | "quiz";

export function EmployeeDirectoryBody() {
  const [users, setUsers] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState("");

  const [selectedUser, setSelectedUser] = useState<any | null>(null);
  const [tab, setTab] = useState<Tab>("chat");

  const [isEditing, setIsEditing] = useState(false);
  const [editFullName, setEditFullName] = useState("");
  const [editPhone, setEditPhone] = useState("");
  const [editPosition, setEditPosition] = useState("");
  const [editPermission, setEditPermission] = useState("crud");
  const [editManagerEmail, setEditManagerEmail] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  const [sessions, setSessions] = useState<any[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<any[]>([]);

  const [reports, setReports] = useState<any[]>([]);
  const [attempts, setAttempts] = useState<any[]>([]);
  const [tabLoading, setTabLoading] = useState(false);

  useEffect(() => {
    apiJson("/api/team/users")
      .then((data) => setUsers(data.users || []))
      .catch(() => setUsers([]))
      .finally(() => setIsLoading(false));
  }, []);

  const filteredUsers = users.filter((u: any) => {
    const q = search.toLowerCase().trim();
    if (!q) return true;
    return (
      u.email?.toLowerCase().includes(q) ||
      u.full_name?.toLowerCase().includes(q) ||
      u.position_title?.toLowerCase().includes(q) ||
      u.role?.toLowerCase().includes(q)
    );
  });

  const openEmployee = async (u: any) => {
    setSelectedUser(u);
    setIsEditing(false);
    setEditFullName(u.full_name || "");
    setEditPhone(u.phone_number || "");
    setEditPosition(u.position_title || "");
    setEditPermission(u.permission_level || "crud");
    setEditManagerEmail(u.manager_email || "");
    setSelectedSessionId(null);
    setMessages([]);
    setSessions([]);
    setReports([]);
    setAttempts([]);
    loadTab(u.email, "chat");
  };

  const saveProfile = async () => {
    if (!selectedUser) return;
    setIsSaving(true);
    try {
      const body: any = {
        full_name: editFullName,
        phone_number: editPhone,
        position_title: editPosition,
        manager_email: editManagerEmail,
      };
      if (selectedUser.role === "Admin") body.permission_level = editPermission;

      await apiJson(`/api/team/users/${encodeURIComponent(selectedUser.email)}/profile`, {
        method: "PATCH",
        body: JSON.stringify(body),
      });

      const updated = {
        ...selectedUser,
        full_name: editFullName,
        phone_number: editPhone,
        position_title: editPosition,
        manager_email: editManagerEmail,
        permission_level: selectedUser.role === "Admin" ? editPermission : selectedUser.permission_level,
      };
      setSelectedUser(updated);
      setUsers((prev) => prev.map((u) => (u.email === updated.email ? updated : u)));
      setIsEditing(false);
    } catch {
      // gagal simpan -- diamkan, form tetap terbuka biar bisa dicoba lagi
    } finally {
      setIsSaving(false);
    }
  };

  const loadTab = async (email: string, t: Tab) => {
    setTab(t);
    setTabLoading(true);
    try {
      if (t === "chat") {
        const data = await apiJson(`/api/team/users/${encodeURIComponent(email)}/chat-sessions`);
        setSessions(data.sessions || []);
      } else if (t === "reports") {
        const data = await apiJson(`/api/team/users/${encodeURIComponent(email)}/reports`);
        setReports(data.reports || []);
      } else if (t === "quiz") {
        const data = await apiJson(`/api/team/users/${encodeURIComponent(email)}/quiz-attempts`);
        setAttempts(data.attempts || []);
      }
    } catch {
      // diamkan -- tab tetap kebuka, cuma kosong
    } finally {
      setTabLoading(false);
    }
  };

  const openSession = async (id: string) => {
    setSelectedSessionId(id);
    try {
      const data = await apiJson(`/api/chat/sessions/${id}/messages`);
      setMessages(data.messages || []);
    } catch {
      setMessages([]);
    }
  };

  // ---------- DETAIL KARYAWAN ----------
  if (selectedUser) {
    return (
      <div className="space-y-4">
        <button
          onClick={() => setSelectedUser(null)}
          className="flex items-center gap-1.5 text-xs font-medium text-navy-700 hover:underline"
        >
          <ArrowLeft className="h-3.5 w-3.5" /> Kembali ke daftar karyawan
        </button>

        {/* Data diri -- formal, bisa diedit Admin/SuperAdmin */}
        <div className="rounded-[var(--radius-card)] border border-navy-100 bg-white p-5">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-ink">Data Diri</h3>
            {!isEditing ? (
              <button
                onClick={() => setIsEditing(true)}
                className="flex items-center gap-1.5 text-xs font-medium text-navy-700 hover:underline"
              >
                <Pencil className="h-3.5 w-3.5" /> Edit
              </button>
            ) : (
              <div className="flex gap-2">
                <button
                  onClick={saveProfile}
                  disabled={isSaving}
                  className="flex items-center gap-1 rounded bg-navy-900 px-3 py-1.5 text-2xs font-semibold text-white hover:bg-navy-800 disabled:opacity-50"
                >
                  <Check className="h-3.5 w-3.5" /> {isSaving ? "Menyimpan..." : "Simpan"}
                </button>
                <button
                  onClick={() => setIsEditing(false)}
                  className="flex items-center gap-1 rounded border border-navy-100 px-3 py-1.5 text-2xs font-medium text-ink-muted hover:bg-navy-50"
                >
                  <X className="h-3.5 w-3.5" /> Batal
                </button>
              </div>
            )}
          </div>

          <div className="flex items-center gap-3 mb-4">
            <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-navy-900 text-sm font-semibold text-white">
              {selectedUser.email.slice(0, 2).toUpperCase()}
            </span>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-ink">{selectedUser.full_name || "(Nama belum diisi)"}</p>
              <p className="flex items-center gap-1.5 text-xs text-ink-muted">
                <Mail className="h-3 w-3" /> {selectedUser.email}
              </p>
            </div>
          </div>

          {!isEditing ? (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <div>
                <p className="text-2xs text-ink-faint">No. Telepon</p>
                <p className="text-xs font-medium text-ink">{selectedUser.phone_number || "-"}</p>
              </div>
              <div>
                <p className="text-2xs text-ink-faint">Jabatan</p>
                <p className="text-xs font-medium text-ink">{selectedUser.position_title || "-"}</p>
              </div>
              <div>
                <p className="text-2xs text-ink-faint">Role</p>
                <p className="text-xs font-medium text-ink">{selectedUser.role}</p>
              </div>
              <div>
                <p className="text-2xs text-ink-faint">Folder Akses</p>
                <p className="font-mono-data text-2xs text-ink">{selectedUser.folder_access}</p>
              </div>
              <div>
                <p className="text-2xs text-ink-faint">Atasan Langsung</p>
                <p className="text-xs font-medium text-ink">{selectedUser.manager_email || "-- (langsung ke Owner)"}</p>
              </div>
              {selectedUser.role === "Admin" && (
                <div>
                  <p className="text-2xs text-ink-faint">Level Akses</p>
                  <p className="text-xs font-medium text-ink">
                    {selectedUser.permission_level === "read_only" ? "Read-only" : "CRUD"}
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <label className="mb-1 flex items-center gap-1 text-2xs font-semibold text-ink-muted">
                  <IdCard className="h-3 w-3" /> Nama Lengkap
                </label>
                <input
                  value={editFullName}
                  onChange={(e) => setEditFullName(e.target.value)}
                  placeholder="mis. Arman Wijaya"
                  className="w-full rounded border border-navy-100 px-3 py-1.5 text-xs focus:border-navy-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="mb-1 flex items-center gap-1 text-2xs font-semibold text-ink-muted">
                  <Phone className="h-3 w-3" /> No. Telepon
                </label>
                <input
                  value={editPhone}
                  onChange={(e) => setEditPhone(e.target.value)}
                  placeholder="mis. 0812xxxxxxx"
                  className="w-full rounded border border-navy-100 px-3 py-1.5 text-xs focus:border-navy-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="mb-1 flex items-center gap-1 text-2xs font-semibold text-ink-muted">
                  <Briefcase className="h-3 w-3" /> Jabatan
                </label>
                <input
                  value={editPosition}
                  onChange={(e) => setEditPosition(e.target.value)}
                  placeholder="mis. Sales Lapangan"
                  className="w-full rounded border border-navy-100 px-3 py-1.5 text-xs focus:border-navy-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="mb-1 flex items-center gap-1 text-2xs font-semibold text-ink-muted">
                  <Users className="h-3 w-3" /> Atasan Langsung
                </label>
                <select
                  value={editManagerEmail}
                  onChange={(e) => setEditManagerEmail(e.target.value)}
                  className="w-full rounded border border-navy-100 px-3 py-1.5 text-xs focus:border-navy-500 focus:outline-none"
                >
                  <option value="">-- Tidak ada / langsung ke Owner --</option>
                  {users
                    .filter((u) => u.email !== selectedUser.email)
                    .map((u) => (
                      <option key={u.email} value={u.email}>
                        {u.full_name ? `${u.full_name} (${u.email})` : u.email}
                      </option>
                    ))}
                </select>
              </div>
              {selectedUser.role === "Admin" && (
                <div>
                  <label className="mb-1 flex items-center gap-1 text-2xs font-semibold text-ink-muted">
                    <Shield className="h-3 w-3" /> Level Akses
                  </label>
                  <select
                    value={editPermission}
                    onChange={(e) => setEditPermission(e.target.value)}
                    className="w-full rounded border border-navy-100 px-3 py-1.5 text-xs focus:border-navy-500 focus:outline-none"
                  >
                    <option value="crud">CRUD (bisa ubah/hapus)</option>
                    <option value="read_only">Read-only (lihat saja)</option>
                  </select>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Tabs */}
        <div className="flex gap-1 border-b border-navy-100">
          {[
            { id: "chat" as Tab, label: "Riwayat Chat", icon: MessageSquare },
            { id: "reports" as Tab, label: "Laporan Kerjaan", icon: FileText },
            { id: "quiz" as Tab, label: "Skor Kuis", icon: Award },
          ].map((t) => (
            <button
              key={t.id}
              onClick={() => loadTab(selectedUser.email, t.id)}
              className={cn(
                "flex items-center gap-1.5 border-b-2 px-3 py-2 text-xs font-medium",
                tab === t.id ? "border-navy-900 text-navy-900" : "border-transparent text-ink-muted hover:text-ink"
              )}
            >
              <t.icon className="h-3.5 w-3.5" /> {t.label}
            </button>
          ))}
        </div>

        {tabLoading ? (
          <p className="text-xs text-ink-faint">Memuat...</p>
        ) : tab === "chat" ? (
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-[300px_1fr]">
            <div className="max-h-[420px] space-y-1 overflow-y-auto rounded-[var(--radius-card)] border border-navy-100 bg-white p-2">
              {sessions.length === 0 ? (
                <p className="p-4 text-xs text-ink-faint">Belum ada riwayat chat.</p>
              ) : (
                sessions.map((s) => (
                  <button
                    key={s.id}
                    onClick={() => openSession(s.id)}
                    className={cn(
                      "flex w-full items-start gap-2 rounded-[var(--radius-control)] px-3 py-2 text-left text-xs",
                      selectedSessionId === s.id ? "bg-navy-50 font-medium text-navy-900" : "text-ink-muted hover:bg-navy-50"
                    )}
                  >
                    <MessageSquare className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                    <span className="truncate">{s.title || "Percakapan baru"}</span>
                  </button>
                ))
              )}
            </div>
            <div className="max-h-[420px] overflow-y-auto rounded-[var(--radius-card)] border border-navy-100 bg-white p-4">
              {!selectedSessionId ? (
                <p className="text-xs text-ink-faint">Pilih percakapan di sebelah kiri.</p>
              ) : (
                <div className="space-y-3">
                  {messages.map((m) => (
                    <div key={m.id} className={m.role === "user" ? "text-right" : ""}>
                      <p className="text-2xs font-semibold uppercase text-ink-faint">{m.role === "user" ? "User" : "AI"}</p>
                      <p className="whitespace-pre-wrap text-sm text-ink">{m.content}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ) : tab === "reports" ? (
          <div className="space-y-3">
            {reports.length === 0 ? (
              <p className="text-xs text-ink-faint">Belum ada laporan kerjaan.</p>
            ) : (
              reports.map((r: any) => (
                <div key={r.id} className="rounded-[var(--radius-card)] border border-navy-100 bg-white p-4">
                  <p className="mb-2 text-2xs text-ink-faint">{(r.created_at || "").slice(0, 16).replace("T", " ")}</p>
                  {r.content && <p className="mb-2 whitespace-pre-wrap text-sm text-ink">{r.content}</p>}
                  {r.media_url && r.media_type === "video" && (
                    <video src={r.media_url} controls className="max-w-md rounded-[var(--radius-control)]" />
                  )}
                  {r.media_url && r.media_type === "audio" && (
                    <audio src={r.media_url} controls className="w-full max-w-md" />
                  )}
                </div>
              ))
            )}
          </div>
        ) : (
          <div className="space-y-2">
            {attempts.length === 0 ? (
              <p className="text-xs text-ink-faint">Belum pernah mengerjakan kuis.</p>
            ) : (
              attempts.map((a: any) => (
                <div key={a.id} className="flex items-center justify-between rounded-[var(--radius-card)] border border-navy-100 bg-white px-4 py-3">
                  <div>
                    <p className="text-sm font-medium text-ink">{a.quizzes?.title || "Kuis"}</p>
                    <p className="text-2xs text-ink-faint">{(a.created_at || "").slice(0, 16).replace("T", " ")}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono-data text-sm text-ink">{a.score}</span>
                    {a.passed ? (
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                    ) : (
                      <XCircle className="h-4 w-4 text-red-500" />
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    );
  }

  // ---------- DAFTAR KARYAWAN ----------
  return (
    <div className="space-y-3">
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-ink-faint" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Cari email, jabatan, atau role..."
          className="w-full rounded-[var(--radius-control)] border border-navy-100 py-2 pl-9 pr-3 text-xs focus:border-navy-500 focus:outline-none"
        />
      </div>

      {isLoading ? (
        <p className="text-xs text-ink-faint">Memuat daftar karyawan...</p>
      ) : filteredUsers.length === 0 ? (
        <p className="text-xs text-ink-faint">{search ? "Tidak ada karyawan yang cocok." : "Belum ada karyawan."}</p>
      ) : (
        <div className="overflow-hidden rounded-[var(--radius-card)] border border-navy-100 bg-white">
          <div className="hidden border-b border-navy-100 bg-navy-50/50 px-4 py-2 text-2xs font-semibold uppercase tracking-wide text-ink-faint sm:grid sm:grid-cols-[1fr_140px_120px_160px]">
            <span>Email</span>
            <span>Jabatan</span>
            <span>Role</span>
            <span>Folder Akses</span>
          </div>
          {filteredUsers.map((u: any) => (
            <button
              key={u.email}
              onClick={() => openEmployee(u)}
              className="flex w-full flex-col gap-1 border-b border-navy-50 px-4 py-3 text-left last:border-0 hover:bg-navy-50/60 sm:grid sm:grid-cols-[1fr_140px_120px_160px] sm:items-center sm:gap-0"
            >
              <span className="flex min-w-0 items-center gap-2 text-sm font-medium text-ink">
                <Mail className="h-3.5 w-3.5 shrink-0 text-ink-faint" />
                <span className="truncate">{u.full_name ? `${u.full_name} · ${u.email}` : u.email}</span>
              </span>
              <span className="flex items-center gap-1.5 text-xs text-ink-muted">
                <Briefcase className="h-3 w-3" /> {u.position_title || "-"}
              </span>
              <span className="flex items-center gap-1.5 text-xs text-ink-muted">
                <Shield className="h-3 w-3" /> {u.role}
              </span>
              <span className="flex items-center gap-1.5 font-mono-data text-2xs text-ink-faint">
                <FolderOpen className="h-3 w-3" /> {u.folder_access}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
