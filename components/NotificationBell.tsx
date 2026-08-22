"use client";
import { useEffect, useRef, useState } from "react";
import { Bell, CalendarClock, Megaphone, TrendingUp, Check } from "lucide-react";
import { apiJson } from "@/lib/api";

interface Notif {
  id: string;
  type: "reminder" | "escalation" | "broadcast";
  title: string;
  message: string;
  related_user_email?: string | null;
  is_read: boolean;
  created_at: string;
}

const ICONS: Record<string, any> = {
  reminder: CalendarClock,
  escalation: TrendingUp,
  broadcast: Megaphone,
};

function timeAgo(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return "Baru saja";
  if (mins < 60) return `${mins} menit lalu`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs} jam lalu`;
  return `${Math.floor(hrs / 24)} hari lalu`;
}

export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [notifs, setNotifs] = useState<Notif[]>([]);
  const [unread, setUnread] = useState(0);
  const ref = useRef<HTMLDivElement>(null);

  const load = () => {
    apiJson("/api/notifications")
      .then((data) => {
        setNotifs(data.notifications || []);
        setUnread(data.unread_count || 0);
      })
      .catch(() => {});
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 60_000); // polling tiap 1 menit
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const onClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  const markRead = async (id: string) => {
    setNotifs((prev) => prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
    setUnread((u) => Math.max(0, u - 1));
    try {
      await apiJson(`/api/notifications/${id}/read`, { method: "PATCH" });
    } catch {}
  };

  const markAllRead = async () => {
    setNotifs((prev) => prev.map((n) => ({ ...n, is_read: true })));
    setUnread(0);
    try {
      await apiJson("/api/notifications/read-all", { method: "PATCH" });
    } catch {}
  };

  return (
    <div ref={ref} className="fixed right-6 top-4 z-40">
      <button
        onClick={() => setOpen((o) => !o)}
        className="relative flex h-10 w-10 items-center justify-center rounded-full border border-navy-100 bg-white text-ink-muted shadow-sm hover:bg-navy-50 hover:text-ink"
      >
        <Bell className="h-4 w-4" />
        {unread > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-[16px] items-center justify-center rounded-full bg-red-600 px-1 text-[10px] font-bold text-white">
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-80 overflow-hidden rounded-[var(--radius-card)] border border-navy-100 bg-white shadow-xl">
          <div className="flex items-center justify-between border-b border-navy-100 px-4 py-3">
            <span className="text-sm font-semibold text-ink">Notifikasi</span>
            {unread > 0 && (
              <button onClick={markAllRead} className="flex items-center gap-1 text-2xs font-semibold text-navy-700 hover:underline">
                <Check className="h-3 w-3" /> Tandai semua dibaca
              </button>
            )}
          </div>
          <div className="max-h-96 overflow-y-auto">
            {notifs.length === 0 ? (
              <p className="px-4 py-8 text-center text-xs text-ink-faint">Belum ada notifikasi.</p>
            ) : (
              notifs.map((n) => {
                const Icon = ICONS[n.type] || Bell;
                return (
                  <button
                    key={n.id}
                    onClick={() => !n.is_read && markRead(n.id)}
                    className={`flex w-full items-start gap-2.5 border-b border-navy-50 px-4 py-3 text-left hover:bg-navy-50/60 ${n.is_read ? "" : "bg-navy-50/40"}`}
                  >
                    <Icon className="mt-0.5 h-4 w-4 shrink-0 text-navy-700" />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-xs font-semibold text-ink">{n.title}</p>
                      <p className="mt-0.5 line-clamp-2 text-2xs text-ink-muted">{n.message}</p>
                      <p className="mt-1 text-2xs text-ink-faint">{timeAgo(n.created_at)}</p>
                    </div>
                    {!n.is_read && <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-navy-900" />}
                  </button>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
