"use client";
import { useState, useEffect } from "react";
import { Mail, Briefcase, Shield, FolderOpen, MessageSquare, ArrowLeft } from "lucide-react";
import { apiJson } from "@/lib/api";

export function EmployeeDirectoryBody() {
    const [users, setUsers] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [selectedEmail, setSelectedEmail] = useState<string | null>(null);
    const [sessions, setSessions] = useState<any[]>([]);
    const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
    const [messages, setMessages] = useState<any[]>([]);

    useEffect(() => {
        apiJson("/api/team/users")
            .then((data) => setUsers(data.users || []))
            .catch(() => setUsers([]))
            .finally(() => setIsLoading(false));
    }, []);

    const openEmployee = async (email: string) => {
        setSelectedEmail(email);
        setSelectedSessionId(null);
        setMessages([]);
        try {
            const data = await apiJson(`/api/team/users/${encodeURIComponent(email)}/chat-sessions`);
            setSessions(data.sessions || []);
        } catch {
            setSessions([]);
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

    if (selectedEmail) {
        return (
            <div className="space-y-4">
                <button
                    onClick={() => setSelectedEmail(null)}
                    className="flex items-center gap-1.5 text-xs font-medium text-navy-700 hover:underline"
                >
                    <ArrowLeft className="h-3.5 w-3.5" /> Kembali ke daftar karyawan
                </button>
                <h3 className="text-sm font-semibold text-ink">Riwayat Chat: {selectedEmail}</h3>

                <div className="grid grid-cols-1 gap-4 lg:grid-cols-[300px_1fr]">
                    <div className="max-h-[420px] space-y-1 overflow-y-auto rounded-[var(--radius-card)] border border-navy-100 bg-white p-2">
                        {sessions.length === 0 ? (
                            <p className="p-4 text-xs text-ink-faint">Belum ada riwayat chat.</p>
                        ) : (
                            sessions.map((s) => (
                                <button
                                    key={s.id}
                                    onClick={() => openSession(s.id)}
                                    className={`flex w-full items-start gap-2 rounded-[var(--radius-control)] px-3 py-2 text-left text-xs ${
                                        selectedSessionId === s.id ? "bg-navy-50 font-medium text-navy-900" : "text-ink-muted hover:bg-navy-50"
                                    }`}
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
            </div>
        );
    }

    return (
        <div className="space-y-3">
            {isLoading ? (
                <p className="text-xs text-ink-faint">Memuat daftar karyawan...</p>
            ) : users.length === 0 ? (
                <p className="text-xs text-ink-faint">Belum ada karyawan.</p>
            ) : (
                <div className="overflow-hidden rounded-[var(--radius-card)] border border-navy-100 bg-white">
                    <div className="hidden border-b border-navy-100 bg-navy-50/50 px-4 py-2 text-2xs font-semibold uppercase tracking-wide text-ink-faint sm:grid sm:grid-cols-[1fr_140px_120px_160px]">
                        <span>Email</span>
                        <span>Jabatan</span>
                        <span>Role</span>
                        <span>Folder Akses</span>
                    </div>
                    {users.map((u: any) => (
                        <button
                            key={u.email}
                            onClick={() => openEmployee(u.email)}
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
