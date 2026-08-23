"use client";
import { useState, useEffect } from "react";
import { Bell, CalendarClock, Megaphone, TrendingUp, Trash2, Check, ChevronLeft, ChevronRight, Loader2 } from "lucide-react";
import { TopBar } from "@/components/TopBar";
import { apiJson } from "@/lib/api";
import { NOTIF_REFRESH_EVENT } from "@/components/NotificationBell";

const ICONS: Record<string, any> = {
  reminder: CalendarClock,
  escalation: TrendingUp,
  broadcast: Megaphone,
};

const TYPE_LABELS: Record<string, string> = {
  reminder: "Pengingat",
  escalation: "Eskalasi",
  broadcast: "Pengumuman",
};

const PAGE_SIZE = 20;

function formatFull(iso: string): string {
  return new Date(iso).toLocaleString("id-ID", { dateStyle: "long", timeStyle: "short" });
}

export default function NotificationsPage() {
  const [notifs, setNotifs] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);

  const load = (p: number) => {
    setIsLoading(true);
    apiJson(`/api/notifications/history?page=${p}&page_size=${PAGE_SIZE}`)
      .then((data) => {
        setNotifs(data.notifications || []);
        setTotal(data.total || 0);
      })
      .finally(() => setIsLoading(false));
  };

  useEffect(() => {
    load(page);
  }, [page]);

  const markRead = async (id: string) => {
    setNotifs((prev) => prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
    try {
      await apiJson(`/api/notifications/${id}/read`, { method: "PATCH" });
      window.dispatchEvent(new Event(NOTIF_REFRESH_EVENT));
    } catch {}
  };

  const deleteNotif = async (id: string) => {
    setNotifs((prev) => prev.filter((n) => n.id !== id));
    setTotal((t) => Math.max(0, t - 1));
    try {
      await apiJson(`/api/notifications/${id}`, { method: "DELETE" });
      window.dispatchEvent(new Event(NOTIF_REFRESH_EVENT));
    } catch {}
  };

  const markAllRead = async () => {
    setNotifs((prev) => prev.map((n) => ({ ...n, is_read: true })));
    try {
      await apiJson("/api/notifications/read-all", { method: "PATCH" });
      window.dispatchEvent(new Event(NOTIF_REFRESH_EVENT));
    } catch {}
  };

  const clearRead = async () => {
    try {
      await apiJson("/api/notifications/read", { method: "DELETE" });
      window.dispatchEvent(new Event(NOTIF_REFRESH_EVENT));
      load(page);
    } catch {}
  };

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div>
      <TopBar
        title="Notifikasi"
        description="Semua pengingat, eskalasi, dan pengumuman -- pesan ditampilkan utuh di sini."
        action={
          <div className="flex items-center gap-2">
            <button onClick={markAllRead} className="flex items-center gap-1.5 rounded-[var(--radius-control)] border border-navy-100 bg-white px-3 py-2 text-xs font-semibold text-ink-muted hover:bg-navy-50">
              <Check className="h-3.5 w-3.5" /> Tandai semua dibaca
            </button>
            <button onClick={clearRead} className="flex items-center gap-1.5 rounded-[var(--radius-control)] border border-navy-100 bg-white px-3 py-2 text-xs font-semibold text-ink-muted hover:bg-navy-50">
              <Trash2 className="h-3.5 w-3.5" /> Hapus yang sudah dibaca
            </button>
          </div>
        }
      />
      <div className="p-8">
        <div className="mx-auto max-w-2xl space-y-3">
          {isLoading ? (
            <div className="flex items-center justify-center rounded-[var(--radius-card)] border border-navy-100 bg-white p-12">
              <Loader2 className="h-5 w-5 animate-spin text-navy-700" />
            </div>
          ) : notifs.length === 0 ? (
            <p className="rounded-[var(--radius-card)] border border-navy-100 bg-white p-8 text-center text-sm text-ink-faint">
              Belum ada notifikasi.
            </p>
          ) : (
            notifs.map((n) => {
              const Icon = ICONS[n.type] || Bell;
              return (
                <div
                  key={n.id}
                  onClick={() => !n.is_read && markRead(n.id)}
                  className={`flex items-start gap-3 rounded-[var(--radius-card)] border border-navy-100 bg-white p-4 shadow-[var(--shadow-card)] ${n.is_read ? "" : "cursor-pointer ring-1 ring-navy-100"}`}
                >
                  <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-navy-50">
                    <Icon className="h-4 w-4 text-navy-700" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-semibold text-ink">{n.title}</p>
                      <span className="rounded-full bg-navy-50 px-2 py-0.5 text-2xs font-medium text-navy-700">{TYPE_LABELS[n.type] || n.type}</span>
                      {!n.is_read && <span className="h-1.5 w-1.5 rounded-full bg-navy-900" />}
                    </div>
                    {/* Pesan penuh, tidak dipotong -- ini alasan halaman ini ada */}
                    <p className="mt-1 whitespace-pre-wrap text-sm text-ink-muted">{n.message}</p>
                    <p className="mt-2 text-2xs text-ink-faint">{formatFull(n.created_at)}</p>
                  </div>
                  <button
                    onClick={(e) => { e.stopPropagation(); deleteNotif(n.id); }}
                    className="shrink-0 rounded p-1.5 text-ink-faint hover:bg-red-50 hover:text-red-600"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              );
            })
          )}

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-3 pt-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="flex items-center gap-1 rounded border border-navy-100 bg-white px-3 py-1.5 text-xs font-medium text-ink-muted disabled:opacity-40"
              >
                <ChevronLeft className="h-3.5 w-3.5" /> Sebelumnya
              </button>
              <span className="text-xs text-ink-faint">Halaman {page} dari {totalPages}</span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="flex items-center gap-1 rounded border border-navy-100 bg-white px-3 py-1.5 text-xs font-medium text-ink-muted disabled:opacity-40"
              >
                Selanjutnya <ChevronRight className="h-3.5 w-3.5" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
