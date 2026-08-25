"use client";
import { useState, useEffect, useMemo } from "react";
import { ArrowLeft, Search, AlertCircle, Send, Loader2, CheckCircle2, ChevronLeft, ChevronRight } from "lucide-react";
import Link from "next/link";
import { TopBar } from "@/components/TopBar";
import { apiJson } from "@/lib/api";
import { NOTIF_REFRESH_EVENT } from "@/components/NotificationBell";

const PAGE_SIZE = 20;

export default function BelumIsiKehadiranPage() {
  const [belum, setBelum] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [sentMsg, setSentMsg] = useState<string | null>(null);

  useEffect(() => {
    apiJson("/api/dashboard/submission-status")
      .then((data) => {
        setBelum(data.belum || []);
        setTotal(data.total || 0);
      })
      .finally(() => setIsLoading(false));
  }, []);

  const filtered = useMemo(() => {
    const q = search.toLowerCase().trim();
    if (!q) return belum;
    return belum.filter(
      (u) => u.email.toLowerCase().includes(q) || (u.position_title || "").toLowerCase().includes(q)
    );
  }, [belum, search]);

  // Reset ke halaman 1 tiap kali pencarian berubah -- supaya tidak nyangkut
  // di halaman 5 padahal hasil pencarian cuma 2 baris.
  useEffect(() => {
    setPage(1);
  }, [search]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const sendReminder = async () => {
    setIsSending(true);
    setSentMsg(null);
    try {
      const result = await apiJson("/api/notifications/run-check", { method: "POST" });
      window.dispatchEvent(new Event(NOTIF_REFRESH_EVENT));
      setSentMsg(`Pengingat terkirim ke ${result.reminded} karyawan${result.escalated ? `, eskalasi ke ${result.escalated} atasan` : ""}.`);
    } catch (e: any) {
      setSentMsg(e.message || "Gagal mengirim pengingat.");
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div>
      <TopBar
        title="Belum Isi Form Kehadiran"
        description={`${belum.length} dari ${total} karyawan belum mengisi form harian.`}
        action={
          <Link href="/dashboard" className="flex items-center gap-2 rounded-[var(--radius-control)] border border-navy-100 bg-white px-3 py-2 text-xs font-semibold text-ink-muted hover:bg-navy-50">
            <ArrowLeft className="h-3.5 w-3.5" /> Kembali ke Dashboard
          </Link>
        }
      />
      <div className="p-8">
        <div className="mx-auto max-w-2xl space-y-4">
          {isLoading ? (
            <div className="flex items-center justify-center rounded-[var(--radius-card)] border border-navy-100 bg-white p-12">
              <Loader2 className="h-5 w-5 animate-spin text-navy-700" />
            </div>
          ) : belum.length === 0 ? (
            <div className="space-y-2 rounded-[var(--radius-card)] border border-navy-100 bg-white p-8 text-center">
              <CheckCircle2 className="mx-auto h-8 w-8 text-green-600" />
              <p className="text-sm font-semibold text-ink">Semua karyawan sudah mengisi form hari ini.</p>
            </div>
          ) : (
            <>
              <div className="flex items-center gap-3">
                <div className="relative flex-1">
                  <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint" />
                  <input
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Cari nama, email, atau jabatan..."
                    className="w-full rounded-[var(--radius-control)] border border-navy-100 bg-white py-2 pl-9 pr-3 text-sm text-ink placeholder:text-ink-faint focus:border-navy-400"
                  />
                </div>
                <button
                  onClick={sendReminder}
                  disabled={isSending}
                  className="flex shrink-0 items-center gap-2 rounded-[var(--radius-control)] bg-navy-900 px-4 py-2 text-xs font-semibold text-white hover:bg-navy-800 disabled:opacity-50"
                >
                  {isSending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Send className="h-3.5 w-3.5" />}
                  Kirim Pengingat ke Semua
                </button>
              </div>

              {sentMsg && (
                <p className="rounded-[var(--radius-control)] bg-navy-50 px-3 py-2 text-xs font-medium text-navy-900">{sentMsg}</p>
              )}

              <div className="divide-y divide-navy-50 overflow-hidden rounded-[var(--radius-card)] border border-navy-100 bg-white">
                {filtered.length === 0 ? (
                  <p className="p-6 text-center text-xs text-ink-faint">Tidak ada yang cocok dengan pencarian.</p>
                ) : (
                  paginated.map((u) => (
                    <div key={u.email} className="flex items-center gap-3 px-4 py-3">
                      <AlertCircle className="h-4 w-4 shrink-0 text-amber-500" />
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm text-ink">{u.position_title || "-"}</p>
                        <p className="truncate text-xs text-ink-faint">{u.email}</p>
                      </div>
                    </div>
                  ))
                )}
              </div>

              {totalPages > 1 && (
                <div className="flex items-center justify-center gap-3">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="flex items-center gap-1 rounded border border-navy-100 bg-white px-3 py-1.5 text-xs font-medium text-ink-muted disabled:opacity-40"
                  >
                    <ChevronLeft className="h-3.5 w-3.5" /> Sebelumnya
                  </button>
                  <span className="text-xs text-ink-faint">Halaman {page} dari {totalPages} ({filtered.length} karyawan)</span>
                  <button
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                    className="flex items-center gap-1 rounded border border-navy-100 bg-white px-3 py-1.5 text-xs font-medium text-ink-muted disabled:opacity-40"
                  >
                    Selanjutnya <ChevronRight className="h-3.5 w-3.5" />
                  </button>
                </div>
              )}
              {search && totalPages <= 1 && (
                <p className="text-center text-2xs text-ink-faint">Menampilkan {filtered.length} dari {belum.length} karyawan.</p>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
