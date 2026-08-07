"use client";
import { useState, useRef, useEffect } from "react";
import { Plus, Send, MoreVertical, Sparkles, Bot, Loader2, Download, AlertTriangle, ExternalLink } from "lucide-react";
import { DocumentBadge } from "@/components/DocumentBadge";
import { cn } from "@/lib/utils";
import { apiJson, downloadBase64, getStoredUser } from "@/lib/api";

interface Source {
    id: string;
    title: string;
    file_url?: string;
    metadata?: { tipe_file?: string };
}

interface GeneratedFile {
    name: string;
    format: string;
    base64: string;
}

interface AnalysisTable {
    columns: string[];
    rows: Record<string, any>[];
}

interface Message {
    id: string;
    role: "user" | "assistant";
    content: string;
    sources?: Source[];
    generatedFiles?: GeneratedFile[];
    analysisTable?: AnalysisTable | null;
    analysisFile?: { name: string; base64: string } | null;
    warning?: string | null;
}

interface ChatSession {
    id: string;
    title: string | null;
}

/** Ubah URL YouTube apa pun (watch?v=, youtu.be/, embed/) jadi ID video
 * saja, supaya bisa dipasang ke src iframe embed. Balikin null kalau
 * polanya tidak dikenali (tetap fallback ke tombol "buka link" di bawah). */
function extractYoutubeId(url: string): string | null {
    try {
        const u = new URL(url);
        if (u.hostname.includes("youtu.be")) return u.pathname.slice(1) || null;
        if (u.hostname.includes("youtube.com")) {
            if (u.pathname === "/watch") return u.searchParams.get("v");
            if (u.pathname.startsWith("/embed/")) return u.pathname.split("/embed/")[1] || null;
            if (u.pathname.startsWith("/shorts/")) return u.pathname.split("/shorts/")[1] || null;
        }
        return null;
    } catch {
        return null;
    }
}

function SourceLink({ src }: { src: Source }) {
    const isYoutube = src.metadata?.tipe_file === "Video YouTube";
    if (isYoutube && src.file_url) {
        const videoId = extractYoutubeId(src.file_url);
        return (
            <div className="mt-2">
                <p className="mb-1 text-xs font-medium text-ink-muted">{src.title}</p>
                {videoId ? (
                    <iframe
                        src={`https://www.youtube.com/embed/${videoId}`}
                        title={src.title}
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                        allowFullScreen
                        className="aspect-video w-full max-w-xs rounded-[var(--radius-control)] border border-navy-100"
                    />
                ) : (
                    <a
                        href={src.file_url}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-2 rounded-[var(--radius-control)] border border-navy-100 bg-navy-50 px-2.5 py-2 text-xs font-medium text-navy-900 hover:bg-navy-100"
                    >
                        Buka video: {src.title}
                    </a>
                )}
            </div>
        );
    }
    if (!src.file_url) return null;
    return (
        <a
            href={src.file_url}
            target="_blank"
            rel="noreferrer"
            className="mt-2 flex items-center gap-2 rounded-[var(--radius-control)] border border-navy-100 bg-navy-50 px-2.5 py-2 text-xs font-medium text-navy-900 hover:bg-navy-100"
        >
            <DocumentBadge type={src.metadata?.tipe_file || "default"} size="sm" />
            <span className="truncate">Unduh: {src.title}</span>
            <ExternalLink className="h-3 w-3 shrink-0" />
        </a>
    );
}

export default function ChatPage() {
    const user = getStoredUser();
    const [sessions, setSessions] = useState<ChatSession[]>([]);
    const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const loadSessions = async () => {
        try {
            const data = await apiJson("/api/chat/sessions");
            setSessions(data.sessions || []);
        } catch {
            // diamkan -- riwayat opsional, tidak menghalangi chat baru
        }
    };

    useEffect(() => {
        loadSessions();
    }, []);

    const openSession = async (sessionId: string) => {
        setCurrentSessionId(sessionId);
        try {
            const data = await apiJson(`/api/chat/sessions/${sessionId}/messages`);
            setMessages(
                (data.messages || []).map((m: any) => ({
                    id: m.id,
                    role: m.role,
                    content: m.content,
                    sources: m.sources || [],
                }))
            );
        } catch {
            setMessages([]);
        }
    };

    const startNewChat = () => {
        setCurrentSessionId(null);
        setMessages([]);
    };

    const sendMessage = async () => {
        if (!input.trim() || isLoading) return;

        const userMessage: Message = { id: Date.now().toString(), role: "user", content: input };
        setMessages((prev) => [...prev, userMessage]);
        const question = input;
        setInput("");
        setIsLoading(true);

        try {
            const data = await apiJson("/api/chat", {
                method: "POST",
                body: JSON.stringify({ message: question, session_id: currentSessionId }),
            });

            if (!currentSessionId) {
                setCurrentSessionId(data.session_id);
                loadSessions();
            }

            const botMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: "assistant",
                content: data.reply,
                sources: data.sources || [],
                generatedFiles: data.generatedFiles || [],
                analysisTable: data.analysisTable,
                analysisFile: data.analysisFile,
                warning: data.warning,
            };
            setMessages((prev) => [...prev, botMessage]);
        } catch (error: any) {
            setMessages((prev) => [
                ...prev,
                { id: Date.now().toString(), role: "assistant", content: `Error: ${error.message}` },
            ]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex h-screen">
            {/* Riwayat Chat Kiri */}
            <div className="flex w-72 shrink-0 flex-col border-r border-navy-100 bg-white">
                <div className="border-b border-navy-100 p-4">
                    <button
                        onClick={startNewChat}
                        className="flex w-full items-center justify-center gap-2 rounded-[var(--radius-control)] bg-navy-900 py-2.5 text-sm font-medium text-white hover:bg-navy-800"
                    >
                        <Plus className="h-4 w-4" /> Chat Baru
                    </button>
                </div>
                <div className="flex-1 space-y-1 overflow-y-auto p-3">
                    <p className="px-2 pb-1 text-xs text-ink-faint">Riwayat</p>
                    {sessions.map((s) => (
                        <button
                            key={s.id}
                            onClick={() => openSession(s.id)}
                            className={cn(
                                "block w-full truncate rounded-[var(--radius-control)] px-3 py-2 text-left text-sm",
                                currentSessionId === s.id
                                    ? "bg-navy-50 font-medium text-navy-900"
                                    : "text-ink-muted hover:bg-navy-50"
                            )}
                        >
                            {s.title || "Percakapan baru"}
                        </button>
                    ))}
                </div>
            </div>

            {/* Area Chat Utama */}
            <div className="flex flex-1 flex-col">
                {messages.length === 0 ? (
                    <div className="flex flex-1 flex-col items-center justify-center gap-3 px-4 text-center">
                        <span className="flex h-14 w-14 items-center justify-center rounded-[var(--radius-card)] bg-navy-50">
                            <Sparkles className="h-6 w-6 text-navy-700" />
                        </span>
                        <h2 className="text-lg font-semibold text-ink">KOS Assistant</h2>
                        <p className="max-w-sm text-sm text-ink-muted">
                            Ruang kerja aktif: {user?.folder_access} -- AI hanya mencari dokumen di dalam folder Anda.
                        </p>
                    </div>
                ) : (
                    <div className="flex-1 space-y-6 overflow-y-auto px-8 py-6">
                        {messages.map((m) => (
                            <div key={m.id} className={cn("flex gap-3", m.role === "user" && "flex-row-reverse")}>
                                {m.role === "assistant" && (
                                    <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-navy-900">
                                        <Bot className="h-4 w-4 text-white" />
                                    </span>
                                )}
                                <div
                                    className={cn(
                                        "max-w-xl rounded-[var(--radius-card)] px-4 py-3 text-sm",
                                        m.role === "user"
                                            ? "bg-navy-900 text-white"
                                            : "border border-navy-100 bg-white text-ink shadow-[var(--shadow-card)]"
                                    )}
                                >
                                    {m.warning && (
                                        <div className="mb-2 flex items-start gap-2 rounded-[var(--radius-control)] border border-amber-200 bg-amber-50 px-2.5 py-2 text-xs text-amber-800">
                                            <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                                            <span>{m.warning}</span>
                                        </div>
                                    )}
                                    <p className="whitespace-pre-wrap">{m.content}</p>

                                    {m.generatedFiles && m.generatedFiles.length > 0 && (
                                        <div className="mt-3 flex gap-2">
                                            {m.generatedFiles.map((gf) => (
                                                <button
                                                    key={gf.name}
                                                    onClick={() =>
                                                        downloadBase64(
                                                            gf.name,
                                                            gf.base64,
                                                            gf.format === "pdf" ? "application/pdf" : "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                                                        )
                                                    }
                                                    className="flex items-center gap-1.5 rounded-[var(--radius-control)] border border-navy-100 px-3 py-1.5 text-xs font-medium text-navy-900 hover:bg-navy-50"
                                                >
                                                    <Download className="h-3.5 w-3.5" /> Download .{gf.format}
                                                </button>
                                            ))}
                                        </div>
                                    )}

                                    {m.analysisTable && (
                                        <div className="mt-3 max-w-full overflow-x-auto rounded-[var(--radius-control)] border border-navy-100">
                                            <table className="min-w-full text-xs">
                                                <thead className="bg-navy-50">
                                                    <tr>
                                                        {m.analysisTable.columns.map((c) => (
                                                            <th key={c} className="px-2 py-1.5 text-left font-medium text-ink-muted">
                                                                {c}
                                                            </th>
                                                        ))}
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {m.analysisTable.rows.map((row, i) => (
                                                        <tr key={i} className="border-t border-navy-100">
                                                            {m.analysisTable!.columns.map((c) => (
                                                                <td key={c} className="px-2 py-1.5">
                                                                    {String(row[c] ?? "")}
                                                                </td>
                                                            ))}
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    )}
                                    {m.analysisFile && (
                                        <button
                                            onClick={() =>
                                                downloadBase64(
                                                    m.analysisFile!.name,
                                                    m.analysisFile!.base64,
                                                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                                )
                                            }
                                            className="mt-2 flex items-center gap-1.5 rounded-[var(--radius-control)] border border-navy-100 px-3 py-1.5 text-xs font-medium text-navy-900 hover:bg-navy-50"
                                        >
                                            <Download className="h-3.5 w-3.5" /> Download Hasil (.xlsx)
                                        </button>
                                    )}

                                    {(m.sources || []).map((src) => (
                                        <SourceLink key={src.id} src={src} />
                                    ))}
                                </div>
                            </div>
                        ))}
                        {isLoading && (
                            <div className="flex gap-3">
                                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-navy-900">
                                    <Bot className="h-4 w-4 text-white" />
                                </span>
                                <div className="flex items-center gap-2 rounded-[var(--radius-card)] border border-navy-100 bg-white px-4 py-3 shadow-[var(--shadow-card)]">
                                    <Loader2 className="h-4 w-4 animate-spin text-navy-500" />{" "}
                                    <span className="text-sm text-ink-muted">AI sedang berpikir...</span>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>
                )}

                {/* Kotak Input */}
                <div className="border-t border-navy-100 bg-white p-4">
                    <div className="mx-auto flex max-w-3xl items-center gap-2 rounded-[var(--radius-card)] border border-navy-100 px-4 py-2.5 focus-within:border-navy-500">
                        <input
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                            placeholder="Tanya KOS..."
                            className="flex-1 text-sm text-ink placeholder:text-ink-faint focus:outline-none"
                            disabled={isLoading}
                        />
                        <button
                            onClick={sendMessage}
                            disabled={isLoading || !input.trim()}
                            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-navy-900 text-white disabled:opacity-40"
                        >
                            <Send className="h-4 w-4" />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
} 