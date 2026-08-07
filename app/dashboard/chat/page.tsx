"use client";
import { useState, useRef, useEffect } from "react";
import { Plus, Send, MoreVertical, Sparkles, Bot, Loader2 } from "lucide-react";
import { DocumentBadge } from "@/components/DocumentBadge";
import { cn } from "@/lib/utils";

// API URL dinamis (Vercel otomatis pakai domain produksi kosong, lokal pakai localhost)
const API_URL = typeof window !== "undefined" && window.location.hostname === "localhost"
    ? "http://localhost:8000"
    : "";

interface Message {
    id: string;
    role: "user" | "assistant";
    content: string;
    sourceTitle?: string;
    sourceType?: any;
}

export default function ChatPage() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Auto-scroll ke bawah saat ada pesan baru
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const sendMessage = async () => {
        if (!input.trim() || isLoading) return;

        // Ambil token JWT session user yang tersimpan dari localStorage atau cookies saat login
        const token = typeof window !== "undefined" ? localStorage.getItem("sb-access-token") || localStorage.getItem("supabase_token") : null;

        const userMessage: Message = {
            id: Date.now().toString(),
            role: "user",
            content: input,
        };

        setMessages((prev) => [...prev, userMessage]);
        setInput("");
        setIsLoading(true);

        try {
            // MENGGUNAKAN API_URL DINAMIS DAN MENYUNTIKKAN AUTHORIZATION HEADER
            const response = await fetch(`${API_URL}/api/chat`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}` // Identitas user otomatis dibaca backend dari sini
                },
                body: JSON.stringify({ message: userMessage.content }), // Bersih tanpa parameter user_id manual
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Gagal mendapatkan respons dari server.");
            }

            const data = await response.json();

            const botMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: "assistant",
                content: data.reply || "Maaf, terjadi kesalahan pada sistem AI.",
                sourceTitle: data.sourceTitle,
                sourceType: data.sourceType,
            };

            setMessages((prev) => [...prev, botMessage]);
        } catch (error: any) {
            setMessages((prev) => [
                ...prev,
                { id: Date.now().toString(), role: "assistant", content: `Error: ${error.message || "Tidak dapat terhubung ke Backend Python."}` }
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
                        onClick={() => setMessages([])}
                        className="flex w-full items-center justify-center gap-2 rounded-[var(--radius-control)] bg-navy-900 py-2.5 text-sm font-medium text-white hover:bg-navy-800"
                    >
                        <Plus className="h-4 w-4" /> Chat Baru
                    </button>
                </div>
                <div className="flex-1 p-3">
                    <p className="px-2 text-xs text-ink-faint">Sesi saat ini (Tersambung via Token JWT)</p>
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
                        <p className="max-w-sm text-sm text-ink-muted">Tanyakan seputar SOP atau dokumen perusahaan.</p>
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
                                <div className={cn("max-w-xl rounded-[var(--radius-card)] px-4 py-3 text-sm", m.role === "user" ? "bg-navy-900 text-white" : "border border-navy-100 bg-white text-ink shadow-[var(--shadow-card)]")}>
                                    <p>{m.content}</p>
                                    {m.sourceTitle && (
                                        <div className="mt-3 flex items-center gap-2 rounded-[var(--radius-control)] border border-navy-100 bg-navy-50 px-2.5 py-2">
                                            <DocumentBadge type={m.sourceType} size="sm" />
                                            <span className="truncate text-xs font-medium text-navy-900">{m.sourceTitle}</span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                        {isLoading && (
                            <div className="flex gap-3">
                                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-navy-900"><Bot className="h-4 w-4 text-white" /></span>
                                <div className="flex items-center gap-2 rounded-[var(--radius-card)] border border-navy-100 bg-white px-4 py-3 shadow-[var(--shadow-card)]">
                                    <Loader2 className="h-4 w-4 animate-spin text-navy-500" /> <span className="text-sm text-ink-muted">AI sedang berpikir...</span>
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
                        <button onClick={sendMessage} disabled={isLoading || !input.trim()} className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-navy-900 text-white disabled:opacity-40">
                            <Send className="h-4 w-4" />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
