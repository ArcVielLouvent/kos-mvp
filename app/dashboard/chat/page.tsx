"use client";
import { useState, useRef, useEffect } from "react";
import { Plus, Send, Sparkles, Bot, Loader2, Download, AlertTriangle, ExternalLink, Copy, Check, Pencil, Trash2, X, Eye } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { DocumentBadge } from "@/components/DocumentBadge";
import { FilePreviewModal } from "@/components/FilePreviewModal";
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

function SourceLink({ src, onPreview }: { src: Source; onPreview: (f: { title: string; file_url: string }) => void }) {
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
        <div className="mt-2 flex items-center gap-2 rounded-[var(--radius-control)] border border-navy-100 bg-navy-50 px-2.5 py-2 text-xs font-medium text-navy-900">
            <DocumentBadge type={src.metadata?.tipe_file || "default"} size="sm" />
            <span className="min-w-0 flex-1 truncate">{src.title}</span>
            <button
                type="button"
                onClick={() => onPreview({ title: src.title, file_url: src.file_url! })}
                className="flex shrink-0 items-center gap-1 rounded border border-navy-200 bg-white px-2 py-1 text-2xs font-semibold text-navy-900 hover:bg-navy-100"
            >
                <Eye className="h-3 w-3" /> Lihat
            </button>
            <a
                href={src.file_url}
                target="_blank"
                rel="noreferrer"
                className="flex shrink-0 items-center gap-1 rounded border border-navy-200 bg-white px-2 py-1 text-2xs font-semibold text-navy-900 hover:bg-navy-100"
            >
                <ExternalLink className="h-3 w-3" /> Buka
            </a>
        </div>
    );
}

function CopyButton({ text }: { text: string }) {
    const [copied, setCopied] = useState(false);
    const handleCopy = async () => {
        try {
            await navigator.clipboard.writeText(text);
            setCopied(true);
            setTimeout(() => setCopied(false), 1500);
        } catch {
            // clipboard API gagal -- diamkan, tombol tetap tampil
        }
    };
    return (
        <button
            onClick={handleCopy}
            title="Salin pesan"
            className="flex items-center gap-1 rounded-[var(--radius-control)] px-2 py-1 text-xs text-ink-faint opacity-0 transition-opacity hover:bg-navy-50 hover:text-ink-muted group-hover:opacity-100"
        >
            {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
            {copied ? "Disalin" : "Salin"}
        </button>
    );
}

/** Tabel hasil markdown AI dibungkus komponen ini supaya ada tombol
 * "Salin Tabel" -- baca langsung dari DOM <table> yang sudah dirender,
 * jadi hasil salinnya tab-separated dan rapi kalau ditempel ke Excel/Sheets. */
function CopyableTable(props: React.TableHTMLAttributes<HTMLTableElement>) {
    const tableRef = useRef<HTMLTableElement>(null);
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
        const table = tableRef.current;
        if (!table) return;
        const rows = Array.from(table.rows).map((row) =>
            Array.from(row.cells).map((cell) => (cell as HTMLElement).innerText.trim()).join("\t")
        );
        navigator.clipboard.writeText(rows.join("\n")).then(() => {
            setCopied(true);
            setTimeout(() => setCopied(false), 1500);
        });
    };

    return (
        <div className="group/table relative my-2 max-w-full overflow-x-auto rounded-[var(--radius-control)] border border-navy-100">
            <button
                onClick={handleCopy}
                className="absolute right-2 top-2 z-10 flex items-center gap-1 rounded border border-navy-100 bg-white px-2 py-1 text-2xs font-medium text-ink-muted opacity-0 shadow-sm transition-opacity hover:bg-navy-50 group-hover/table:opacity-100"
            >
                {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                {copied ? "Disalin" : "Salin Tabel"}
            </button>
            <table ref={tableRef} className="min-w-full text-xs" {...props} />
        </div>
    );
}

const markdownComponents = {
    table: CopyableTable,
    thead: (props: any) => <thead className="bg-navy-50" {...props} />,
    th: (props: any) => <th className="border-b border-navy-100 px-2 py-1.5 text-left font-medium text-ink-muted" {...props} />,
    td: (props: any) => <td className="border-b border-navy-50 px-2 py-1.5" {...props} />,
    h1: (props: any) => <h3 className="mt-3 mb-1.5 text-base font-semibold text-ink" {...props} />,
    h2: (props: any) => <h3 className="mt-3 mb-1.5 text-sm font-semibold text-ink" {...props} />,
    h3: (props: any) => <h4 className="mt-2 mb-1 text-sm font-semibold text-ink" {...props} />,
    p: (props: any) => <p className="mb-2 last:mb-0" {...props} />,
    ul: (props: any) => <ul className="mb-2 list-disc space-y-0.5 pl-5" {...props} />,
    ol: (props: any) => <ol className="mb-2 list-decimal space-y-0.5 pl-5" {...props} />,
    strong: (props: any) => <strong className="font-semibold text-ink" {...props} />,
    code: (props: any) => <code className="rounded bg-navy-50 px-1 py-0.5 font-mono-data text-2xs" {...props} />,
};

export default function ChatPage() {
    const user = getStoredUser();
    const [sessions, setSessions] = useState<ChatSession[]>([]);
    const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [renamingId, setRenamingId] = useState<string | null>(null);
    const [renameValue, setRenameValue] = useState("");
    const [previewFile, setPreviewFile] = useState<{ title: string; file_url: string } | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    useEffect(() => {
        const el = textareaRef.current;
        if (!el) return;
        el.style.height = "auto";
        el.style.height = Math.min(el.scrollHeight, 200) + "px";
    }, [input]);

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
        if (renamingId) return;
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

    const startRename = (s: ChatSession) => {
        setRenamingId(s.id);
        setRenameValue(s.title || "");
    };

    const confirmRename = async () => {
        if (!renamingId) return;
        const title = renameValue.trim() || "Percakapan baru";
        try {
            await apiJson(`/api/chat/sessions/${renamingId}`, {
                method: "PATCH",
                body: JSON.stringify({ title }),
            });
            setSessions((prev) => prev.map((s) => (s.id === renamingId ? { ...s, title } : s)));
        } catch {
            // gagal rename -- diamkan
        } finally {
            setRenamingId(null);
        }
    };

    const deleteSession = async (id: string) => {
        if (!confirm("Hapus percakapan ini secara permanen?")) return;
        try {
            await apiJson(`/api/chat/sessions/${id}`, { method: "DELETE" });
            setSessions((prev) => prev.filter((s) => s.id !== id));
            if (currentSessionId === id) startNewChat();
        } catch {
            // gagal hapus -- diamkan
        }
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

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    return (
        <div className="flex h-screen">
            <div className="flex w-64 shrink-0 flex-col border-r border-navy-100 bg-navy-50/50">
                <div className="p-3">
                    <button
                        onClick={startNewChat}
                        className="flex w-full items-center justify-center gap-2 rounded-[var(--radius-control)] bg-navy-900 py-2.5 text-sm font-medium text-white hover:bg-navy-800"
                    >
                        <Plus className="h-4 w-4" /> Chat Baru
                    </button>
                </div>
                <p className="px-4 pb-1 text-2xs font-semibold uppercase tracking-wide text-ink-faint">Riwayat</p>
                <div className="flex-1 space-y-0.5 overflow-y-auto px-2 pb-3">
                    {sessions.map((s) => (
                        <div
                            key={s.id}
                            className={cn(
                                "group flex items-center gap-1 rounded-[var(--radius-control)] px-2 py-1",
                                currentSessionId === s.id ? "bg-white shadow-2xs" : "hover:bg-white/60"
                            )}
                        >
                            {renamingId === s.id ? (
                                <div className="flex flex-1 items-center gap-1">
                                    <input
                                        autoFocus
                                        value={renameValue}
                                        onChange={(e) => setRenameValue(e.target.value)}
                                        onKeyDown={(e) => {
                                            if (e.key === "Enter") confirmRename();
                                            if (e.key === "Escape") setRenamingId(null);
                                        }}
                                        className="min-w-0 flex-1 rounded border border-navy-200 px-1.5 py-1 text-xs focus:border-navy-500"
                                    />
                                    <button onClick={confirmRename} className="p-1 text-navy-700 hover:text-navy-900">
                                        <Check className="h-3.5 w-3.5" />
                                    </button>
                                    <button onClick={() => setRenamingId(null)} className="p-1 text-ink-faint hover:text-ink">
                                        <X className="h-3.5 w-3.5" />
                                    </button>
                                </div>
                            ) : (
                                <>
                                    <button
                                        onClick={() => openSession(s.id)}
                                        className={cn(
                                            "min-w-0 flex-1 truncate rounded px-1 py-1.5 text-left text-sm",
                                            currentSessionId === s.id ? "font-medium text-navy-900" : "text-ink-muted"
                                        )}
                                    >
                                        {s.title || "Percakapan baru"}
                                    </button>
                                    <div className="flex shrink-0 gap-0.5 opacity-0 transition-opacity group-hover:opacity-100">
                                        <button onClick={() => startRename(s)} className="p-1 text-ink-faint hover:text-navy-900" title="Ganti nama">
                                            <Pencil className="h-3.5 w-3.5" />
                                        </button>
                                        <button onClick={() => deleteSession(s.id)} className="p-1 text-ink-faint hover:text-red-600" title="Hapus">
                                            <Trash2 className="h-3.5 w-3.5" />
                                        </button>
                                    </div>
                                </>
                            )}
                        </div>
                    ))}
                </div>
            </div>

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
                    <div className="flex-1 overflow-y-auto">
                        <div className="mx-auto max-w-3xl space-y-8 px-6 py-8">
                            {messages.map((m) => (
                                <div key={m.id} className="group flex gap-3">
                                    <span
                                        className={cn(
                                            "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
                                            m.role === "assistant" ? "bg-navy-900" : "bg-navy-100"
                                        )}
                                    >
                                        {m.role === "assistant" ? (
                                            <Bot className="h-4 w-4 text-white" />
                                        ) : (
                                            <span className="text-xs font-semibold text-navy-900">
                                                {(user?.email || "U").slice(0, 1).toUpperCase()}
                                            </span>
                                        )}
                                    </span>

                                    <div className="min-w-0 flex-1 pt-0.5">
                                        {m.warning && (
                                            <div className="mb-2 flex items-start gap-2 rounded-[var(--radius-control)] border border-amber-200 bg-amber-50 px-2.5 py-2 text-xs text-amber-800">
                                                <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                                                <span>{m.warning}</span>
                                            </div>
                                        )}

                                        {m.role === "assistant" ? (
                                            <div className="text-sm leading-relaxed text-ink">
                                                <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                                                    {m.content}
                                                </ReactMarkdown>
                                            </div>
                                        ) : (
                                            <p className="whitespace-pre-wrap text-sm leading-relaxed text-ink">{m.content}</p>
                                        )}

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
                                            <div className="mt-3">
                                                <CopyableTable>
                                                    <thead>
                                                        <tr>
                                                            {m.analysisTable.columns.map((c) => (
                                                                <th key={c}>{c}</th>
                                                            ))}
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        {m.analysisTable.rows.map((row, i) => (
                                                            <tr key={i}>
                                                                {m.analysisTable!.columns.map((c) => (
                                                                    <td key={c}>{String(row[c] ?? "")}</td>
                                                                ))}
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </CopyableTable>
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
                                            <SourceLink key={src.id} src={src} onPreview={setPreviewFile} />
                                        ))}

                                        <div className="mt-1">
                                            <CopyButton text={m.content} />
                                        </div>
                                    </div>
                                </div>
                            ))}
                            {isLoading && (
                                <div className="flex gap-3">
                                    <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-navy-900">
                                        <Bot className="h-4 w-4 text-white" />
                                    </span>
                                    <div className="flex items-center gap-2 pt-1.5">
                                        <Loader2 className="h-4 w-4 animate-spin text-navy-500" />
                                        <span className="text-sm text-ink-muted">AI sedang berpikir...</span>
                                    </div>
                                </div>
                            )}
                            <div ref={messagesEndRef} />
                        </div>
                    </div>
                )}

                <div className="border-t border-navy-100 bg-white p-4">
                    <div className="mx-auto flex max-w-3xl items-end gap-2 rounded-[var(--radius-card)] border border-navy-100 px-4 py-3.5 focus-within:border-navy-500">
                        <textarea
                            ref={textareaRef}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Tanya KOS... (Enter kirim, Shift+Enter baris baru)"
                            rows={1}
                            className="max-h-[200px] flex-1 resize-none text-sm text-ink placeholder:text-ink-faint focus:outline-none"
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
            {previewFile && <FilePreviewModal file={previewFile} onClose={() => setPreviewFile(null)} />}
        </div>
    );
}