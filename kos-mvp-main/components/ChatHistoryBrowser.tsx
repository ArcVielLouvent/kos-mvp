"use client";
import { useState, useEffect } from "react";
import { MessageSquare, User } from "lucide-react";
import { apiJson } from "@/lib/api";

const MONTHS = [
  "Januari", "Februari", "Maret", "April", "Mei", "Juni",
  "Juli", "Agustus", "September", "Oktober", "November", "Desember",
];

export function ChatHistoryBrowser() {
  const [sessions, setSessions] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [month, setMonth] = useState<string>("");
  const [year, setYear] = useState<string>("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [messages, setMessages] = useState<any[]>([]);

  const currentYear = new Date().getFullYear();
  const yearOptions = [currentYear, currentYear - 1, currentYear - 2];

  const load = async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams();
      if (month) params.set("month", month);
      if (year) params.set("year", year);
      const data = await apiJson(`/api/dashboard/chat-sessions?${params.toString()}`);
      setSessions(data.sessions || []);
    } catch {
      setSessions([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [month, year]);

  const openSession = async (id: string) => {
    setSelectedId(id);
    try {
      const data = await apiJson(`/api/chat/sessions/${id}/messages`);
      setMessages(data.messages || []);
    } catch {
      setMessages([]);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <select value={month} onChange={(e) => setMonth(e.target.value)} className="rounded border border-navy-100 px-3 py-2 text-xs focus:border-navy-500 focus:outline-none">
          <option value="">Semua Bulan</option>
          {MONTHS.map((m, i) => (
            <option key={m} value={i + 1}>{m}</option>
          ))}
        </select>
        <select value={year} onChange={(e) => setYear(e.target.value)} className="rounded border border-navy-100 px-3 py-2 text-xs focus:border-navy-500 focus:outline-none">
          <option value="">Semua Tahun</option>
          {yearOptions.map((y) => (
            <option key={y} value={y}>{y}</option>
          ))}
        </select>
        <span className="text-xs text-ink-faint">{sessions.length} percakapan ditemukan</span>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[320px_1fr]">
        <div className="max-h-[500px] space-y-1 overflow-y-auto rounded-[var(--radius-card)] border border-navy-100 bg-white p-2">
          {isLoading ? (
            <p className="p-4 text-xs text-ink-faint">Memuat...</p>
          ) : sessions.length === 0 ? (
            <p className="p-4 text-xs text-ink-faint">Tidak ada percakapan di periode ini.</p>
          ) : (
            sessions.map((s) => (
              <button
                key={s.id}
                onClick={() => openSession(s.id)}
                className={`flex w-full items-start gap-2 rounded-[var(--radius-control)] px-3 py-2 text-left text-xs ${
                  selectedId === s.id ? "bg-navy-50 font-medium text-navy-900" : "text-ink-muted hover:bg-navy-50"
                }`}
              >
                <MessageSquare className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                <div className="min-w-0 flex-1">
                  <p className="truncate">{s.title || "Percakapan baru"}</p>
                  <p className="flex items-center gap-1 text-2xs text-ink-faint">
                    <User className="h-2.5 w-2.5" /> {s.user_email} · {(s.created_at || "").slice(0, 10)}
                  </p>
                </div>
              </button>
            ))
          )}
        </div>

        <div className="max-h-[500px] overflow-y-auto rounded-[var(--radius-card)] border border-navy-100 bg-white p-4">
          {!selectedId ? (
            <p className="text-xs text-ink-faint">Pilih percakapan di sebelah kiri untuk lihat isinya.</p>
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
