"use client";
import { useState } from "react";
import { Plus, Send, MoreVertical, Sparkles, Bot } from "lucide-react";
import { DocumentBadge } from "@/components/DocumentBadge";
import { cn } from "@/lib/utils";
import { MOCK_SESSIONS, type MockSession } from "@/lib/mock-chat";

export default function ChatPage() {
    const [sessions] = useState<MockSession[]>(MOCK_SESSIONS);
    const [activeId, setActiveId] = useState<string | null>(sessions[0]?.id ?? null);
    const [input, setInput] = useState("");

    const active = sessions.find((s) => s.id === activeId);

    return (
        <div className="flex h-screen">
            {/* Riwayat percakapan */}
            <div className="flex w-72 shrink-0 flex-col border-r border-navy-100 bg-white">
                <div className="border-b border-navy-100 p-4">
                    <button
                        onClick={() => setActiveId(null)}
                        className="flex w-full items-center justify-center gap-2 rounded-[var(--radius-control)] bg-navy-900 py-2.5 text-sm font-medium text-white hover:bg-navy-800"
                    >
                        <Plus className="h-4 w-4" /> Chat Baru
                    </button>
                </div>
                <div className="flex-1 space-y-1 overflow-y-auto p-3">
                    <p className="px-2 pb-2 text-xs font-semibold uppercase tracking-wide text-ink-faint">
                        Riwayat
                    </p>
                    {sessions.map((s) => (
                        <button
                            key={s.id}
                            onClick={() => setActiveId(s.id)}
                            className={cn(
                                "group flex w-full items-center justify-between rounded-[var(--radius-control)] px-3 py-2.5 text-left text-sm transition-colors",
                                s.id === activeId
                                    ? "bg-navy-100 font-medium text-navy-900"
                                    : "text-ink-muted hover:bg-navy-50"
                            )}
                        >
                            <span className="truncate">{s.title}</span>
                            <MoreVertical className="h-3.5 w-3.5 shrink-0 text-ink-faint opacity-0 group-hover:opacity-100" />
                        </button>
                    ))}
                </div>
            </div>

            {/* Percakapan aktif */}
            <div className="flex flex-1 flex-col">
                {!active ? (
                    <div className="flex flex-1 flex-col items-center justify-center gap-3 px-4 text-center">
                        <span className="flex h-14 w-14 items-center justify-center rounded-[var(--radius-card)] bg-navy-50">
                            <Sparkles className="h-6 w-6 text-navy-700" />
                        </span>
                        <h2 className="text-lg font-semibold text-ink">Mulai percakapan baru</h2>
                        <p className="max-w-sm text-sm text-ink-muted">
                            Tanyakan apa saja seputar SOP, kebijakan, atau data perusahaan Anda —
                            KOS akan menjawab berdasarkan dokumen yang tersedia di folder Anda.
                        </p>
                    </div>
                ) : (
                    <div className="flex-1 space-y-6 overflow-y-auto px-8 py-6">
                        {active.messages.map((m) => (
                            <div
                                key={m.id}
                                className={cn("flex gap-3", m.role === "user" && "flex-row-reverse")}
                            >
                                {m.role === "assistant" && (
                                    <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-navy-900">
                                        <Bot className="h-4 w-4 text-white" />
                                    </span>
                                )}
                                <div
                                    className={cn(
                                        "max-w-xl rounded-[var(--radius-card)] px-4 py-3 text-sm leading-relaxed",
                                        m.role === "user"
                                            ? "bg-navy-900 text-white"
                                            : "border border-navy-100 bg-white text-ink shadow-[var(--shadow-card)]"
                                    )}
                                >
                                    <p>{m.content}</p>
                                    {m.sourceTitle && (
                                        <div className="mt-3 flex items-center gap-2 rounded-[var(--radius-control)] border border-navy-100 bg-navy-50 px-2.5 py-2">
                                            <DocumentBadge type={m.sourceType} size="sm" />
                                            <span className="truncate text-xs font-medium text-navy-900">
                                                {m.sourceTitle}
                                            </span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {/* Input */}
                <div className="border-t border-navy-100 bg-white p-4">
                    <div className="mx-auto flex max-w-3xl items-center gap-2 rounded-[var(--radius-card)] border border-navy-100 px-4 py-2.5 focus-within:border-navy-500">
                        <input
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Ketik pertanyaan Anda di sini..."
                            className="flex-1 text-sm text-ink placeholder:text-ink-faint focus:outline-none"
                        />
                        <button className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-navy-900 text-white hover:bg-navy-800 disabled:opacity-40">
                            <Send className="h-4 w-4" />
                        </button>
                    </div>
                    <p className="mx-auto mt-2 max-w-3xl text-center text-xs text-ink-faint">
                        KOS hanya menjawab berdasarkan dokumen di folder akses Anda — bukan pengetahuan umum di luar itu.
                    </p>
                </div>
            </div>
        </div>
    );
}