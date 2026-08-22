"use client";
import { useState, useEffect } from "react";
import { Megaphone, Send, Loader2, Users, Clock } from "lucide-react";
import { TopBar } from "@/components/TopBar";
import { apiJson } from "@/lib/api";

export default function AnnouncementsPage() {
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [targetScope, setTargetScope] = useState("/");
  const [isSending, setIsSending] = useState(false);
  const [resultMsg, setResultMsg] = useState<string | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);

  const loadHistory = () => {
    setIsLoadingHistory(true);
    apiJson("/api/announcements")
      .then((data) => setHistory(data.announcements || []))
      .finally(() => setIsLoadingHistory(false));
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const handleSend = async () => {
    if (!subject.trim() || !body.trim()) {
      setResultMsg("Judul dan isi pengumuman wajib diisi.");
      return;
    }
    setIsSending(true);
    setResultMsg(null);
    try {
      const result = await apiJson("/api/announcements/broadcast", {
        method: "POST",
        body: JSON.stringify({ subject: subject.trim(), body: body.trim(), target_scope: targetScope }),
      });
      setResultMsg(result.message);
      setSubject("");
      setBody("");
      loadHistory();
    } catch (e: any) {
      setResultMsg(e.message || "Gagal mengirim pengumuman.");
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div>
      <TopBar title="Broadcast Pengumuman" description="Kirim pengumuman ke seluruh karyawan (atau sebagian folder) lewat email + notifikasi dalam aplikasi." />
      <div className="p-8">
        <div className="mx-auto grid max-w-4xl gap-6 lg:grid-cols-[1.3fr_1fr]">
          <div className="space-y-4 rounded-[var(--radius-card)] border border-navy-100 bg-white p-6 shadow-[var(--shadow-card)]">
            <div className="flex items-center gap-2 text-sm font-semibold text-ink">
              <Megaphone className="h-4 w-4 text-navy-700" /> Buat Pengumuman
            </div>

            <div>
              <label className="mb-1 block text-xs font-semibold text-ink-muted">Judul</label>
              <input
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="Mis. Libur Nasional 17 Agustus"
                className="w-full rounded-[var(--radius-control)] border border-navy-100 bg-white px-3 py-2 text-sm text-ink placeholder:text-ink-faint focus:border-navy-400"
              />
            </div>

            <div>
              <label className="mb-1 block text-xs font-semibold text-ink-muted">Isi Pengumuman</label>
              <textarea
                value={body}
                onChange={(e) => setBody(e.target.value)}
                rows={7}
                placeholder="Tulis isi pengumuman di sini..."
                className="w-full rounded-[var(--radius-control)] border border-navy-100 bg-white px-3 py-2 text-sm text-ink placeholder:text-ink-faint focus:border-navy-400"
              />
            </div>

            <div>
              <label className="mb-1 block text-xs font-semibold text-ink-muted">Target Penerima</label>
              <select
                value={targetScope}
                onChange={(e) => setTargetScope(e.target.value)}
                className="w-full rounded-[var(--radius-control)] border border-navy-100 bg-white px-3 py-2 text-sm text-ink"
              >
                <option value="/">Semua karyawan</option>
              </select>
              <p className="mt-1 text-2xs text-ink-faint">
                Saat ini bisa ke semua karyawan. Kirim ke folder/divisi tertentu bisa ditambahkan belakangan kalau dibutuhkan.
              </p>
            </div>

            {resultMsg && (
              <p className="rounded-[var(--radius-control)] bg-navy-50 px-3 py-2 text-xs font-medium text-navy-900">{resultMsg}</p>
            )}

            <button
              onClick={handleSend}
              disabled={isSending}
              className="flex w-full items-center justify-center gap-2 rounded-[var(--radius-control)] bg-navy-900 py-2.5 text-sm font-semibold text-white hover:bg-navy-800 disabled:opacity-50"
            >
              {isSending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              {isSending ? "Mengirim..." : "Kirim Pengumuman"}
            </button>
            <p className="text-center text-2xs text-ink-faint">
              Email terkirim lewat SMTP yang dikonfigurasi di server -- kalau belum diatur, pengumuman tetap masuk sebagai notifikasi dalam aplikasi.
            </p>
          </div>

          <div className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-ink-faint">Riwayat Pengumuman</p>
            {isLoadingHistory ? (
              <div className="flex justify-center rounded-[var(--radius-card)] border border-navy-100 bg-white p-8">
                <Loader2 className="h-4 w-4 animate-spin text-navy-700" />
              </div>
            ) : history.length === 0 ? (
              <p className="rounded-[var(--radius-card)] border border-navy-100 bg-white p-6 text-center text-xs text-ink-faint">
                Belum ada pengumuman yang dikirim.
              </p>
            ) : (
              history.map((a) => (
                <div key={a.id} className="rounded-[var(--radius-card)] border border-navy-100 bg-white p-4">
                  <p className="text-sm font-semibold text-ink">{a.subject}</p>
                  <p className="mt-1 line-clamp-2 text-xs text-ink-muted">{a.body}</p>
                  <div className="mt-2 flex items-center gap-3 text-2xs text-ink-faint">
                    <span className="flex items-center gap-1"><Users className="h-3 w-3" /> {a.recipient_count} email terkirim</span>
                    <span className="flex items-center gap-1"><Clock className="h-3 w-3" /> {a.sent_at?.slice(0, 16).replace("T", " ")}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
