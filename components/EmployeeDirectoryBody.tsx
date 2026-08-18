"use client";
import { useState, useEffect } from "react";
import {
  Mail, Briefcase, Shield, FolderOpen, MessageSquare, ArrowLeft,
  Search, FileText, Award, CheckCircle2, XCircle,
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
      u.position_title?.toLowerCase().includes(q) ||
      u.role?.toLowerCase().includes(q)
    );
  });

  const openEmployee = async (u: any) => {
    setSelectedUser(u);
    setSelectedSessionId(null);
    setMessages([]);
    setSessions([]);
    setReports([]);
    setAttempts([]);
    loadTab(u.email, "chat");
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

        {/* Data diri */}
        <div className="flex flex-wrap items-center gap-x-6 gap-y-2 rounded-[var(--radius-card)] border border-navy-100 bg-white p-4">
          <span className="flex h-10 w-10 items-center justify-center rounded-full bg-navy-900 text-sm font-semibold text-white">
            {selectedUser.email.slice(0, 2).toUpperCase()}
          </span>
          <div className="flex items-center gap-1.5 text-sm font-medium text-ink">
            <Mail className="h-3.5 w-3.5 text-ink-faint" /> {selectedUser.email}
          </div>
          <div className="flex items-center gap-1.5 text-xs text-ink-muted">
            <Briefcase className="h-3 w-3" /> {selectedUser.position_title || "-"}
          </div>
          <div className="flex items-center gap-1.5 text-xs text-ink-muted">
            <Shield className="h-3 w-3" /> {selectedUser.role}
          </div>
          <div className="flex items-center gap-1.5 font-mono-data text-2xs text-ink-faint">
            <FolderOpen className="h-3 w-3" /> {selectedUser.folder_access}
          </div>
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
              <span className="flex items-center gap-2 text-sm font-medium text-ink">
                <Mail className="h-3.5 w-3.5 text-ink-faint" /> {u.email}
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
