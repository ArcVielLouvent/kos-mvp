"use client";
import { useState, useEffect } from "react";
import { TopBar } from "@/components/TopBar";
import { DocumentBadge } from "@/components/DocumentBadge";
import { FileText, Users, FolderTree, MessageSquare, ArrowUpRight } from "lucide-react";
import { apiJson } from "@/lib/api";

const ICON_MAP: Record<string, any> = {
    "Total Dokumen": { icon: FileText, tint: "bg-navy-900" },
    "Total Karyawan": { icon: Users, tint: "bg-navy-700" },
    "Total Folder": { icon: FolderTree, tint: "bg-navy-500" },
    "Status Sistem": { icon: MessageSquare, tint: "bg-navy-300" },
};

export default function DashboardPage() {
    const [stats, setStats] = useState<any[]>([]);
    const [recentActivity, setRecentActivity] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        apiJson("/api/dashboard")
            .then((result) => {
                if (result.stats) setStats(result.stats);
                if (result.recent) setRecentActivity(result.recent);
                setIsLoading(false);
            })
            .catch((err) => {
                console.error("Dashboard Fetch Error:", err);
                setIsLoading(false);
            });
    }, []);

    return (
        <div>
            <TopBar title="Dashboard" description="Ringkasan aktivitas dan pengetahuan perusahaan Anda." />
            <div className="space-y-6 p-8">
                {isLoading ? (
                    <p className="animate-pulse text-sm text-ink-muted">Memuat statistik real-time...</p>
                ) : (
                    <>
                        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                            {stats.map((stat) => {
                                const config = ICON_MAP[stat.label] || { icon: FileText, tint: "bg-navy-900" };
                                const Icon = config.icon;
                                return (
                                    <div key={stat.label} className="rounded-[var(--radius-card)] border border-navy-100 bg-white p-5 shadow-[var(--shadow-card)]">
                                        <span className={`flex h-10 w-10 items-center justify-center rounded-[var(--radius-control)] ${config.tint}`}>
                                            <Icon className="h-5 w-5 text-white" strokeWidth={2} />
                                        </span>
                                        <p className="mt-4 font-mono-data text-2xl font-semibold text-ink">{stat.value}</p>
                                        <p className="text-sm text-ink-muted">{stat.label}</p>
                                    </div>
                                );
                            })}
                        </div>

                        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
                            <div className="rounded-[var(--radius-card)] border border-navy-100 bg-white p-6 shadow-[var(--shadow-card)] lg:col-span-2">
                                <div className="mb-4 flex items-center justify-between">
                                    <h3 className="text-sm font-semibold text-ink">Dokumen Sistem</h3>
                                    <a href="/dashboard/files" className="flex items-center gap-1 text-xs font-medium text-navy-700 hover:underline">
                                        Buka File Manager <ArrowUpRight className="h-3 w-3" />
                                    </a>
                                </div>
                                <p className="text-xs text-ink-faint">Semua folder dan berkas tersinkronisasi otomatis dengan hak akses cloud.</p>
                            </div>

                            <div className="rounded-[var(--radius-card)] border border-navy-100 bg-white p-6 shadow-[var(--shadow-card)]">
                                <h3 className="mb-4 text-sm font-semibold text-ink">Aktivitas Terbaru</h3>
                                <div className="space-y-4">
                                    {recentActivity.length === 0 ? (
                                        <p className="text-xs text-ink-muted">Belum ada log aktivitas terbaru.</p>
                                    ) : (
                                        recentActivity.map((a, i) => (
                                            <div key={i} className="flex items-start gap-3">
                                                <DocumentBadge type={a.type || "default"} size="sm" />
                                                <div className="min-w-0 flex-1">
                                                    <p className="truncate text-sm font-medium text-ink">{a.title}</p>
                                                    <p className="text-xs text-ink-faint">{a.who} · {a.time}</p>
                                                </div>
                                            </div>
                                        ))
                                    )}
                                </div>
                            </div>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}