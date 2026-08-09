"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { TopBar } from "@/components/TopBar";
import { FileText, Users, FolderTree, MessageSquare, ArrowUpRight, Folder, UserPlus } from "lucide-react";
import { apiJson } from "@/lib/api";
import { cn } from "@/lib/utils";

const ICON_MAP: Record<string, any> = {
    "Total Dokumen": { icon: FileText, tint: "bg-navy-900" },
    "Total Karyawan": { icon: Users, tint: "bg-success" },
    "Total Folder": { icon: FolderTree, tint: "bg-warning" },
    "Total Percakapan": { icon: MessageSquare, tint: "bg-danger" },
};

const ACTIVITY_ICON: Record<string, any> = {
    document: { icon: FileText, tint: "bg-navy-50 text-navy-700" },
    chat: { icon: MessageSquare, tint: "bg-navy-50 text-navy-700" },
    employee: { icon: UserPlus, tint: "bg-navy-50 text-navy-700" },
};

const FOLDER_COLORS = ["bg-navy-900", "bg-success", "bg-warning", "bg-danger", "bg-navy-700"];

function formatTime(iso: string) {
    if (!iso) return "";
    return iso.slice(0, 16).replace("T", " ");
}

export default function DashboardPage() {
    const router = useRouter();
    const [stats, setStats] = useState<any[]>([]);
    const [folderBreakdown, setFolderBreakdown] = useState<any[]>([]);
    const [recentActivity, setRecentActivity] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        apiJson("/api/dashboard")
            .then((result) => {
                if (result.stats) setStats(result.stats);
                if (result.folderBreakdown) setFolderBreakdown(result.folderBreakdown);
                if (result.recent) setRecentActivity(result.recent);
                setIsLoading(false);
            })
            .catch((err) => {
                console.error("Dashboard Fetch Error:", err);
                setStats([{ label: `Gagal memuat: ${err.message || "error tidak diketahui"}`, value: "-" }]);
                setIsLoading(false);
            });
    }, []);

    const goToFolder = (path: string) => {
        router.push(`/dashboard/files?path=${encodeURIComponent(path)}`);
    };

    return (
        <div>
            <TopBar title="Dashboard" description="Ringkasan aktivitas dan pengetahuan perusahaan Anda." />
            <div className="space-y-6 p-8">
                {isLoading ? (
                    <p className="animate-pulse text-sm text-ink-muted">Memuat statistik real-time...</p>
                ) : (
                    <>
                        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
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

                        <div>
                            <div className="mb-3 flex items-center justify-between">
                                <h3 className="text-sm font-semibold text-ink">Dokumen per Folder</h3>
                                <a href="/dashboard/files" className="flex items-center gap-1 text-xs font-medium text-navy-700 hover:underline">
                                    Buka File Manager <ArrowUpRight className="h-3 w-3" />
                                </a>
                            </div>

                            {folderBreakdown.length === 0 ? (
                                <div className="rounded-[var(--radius-card)] border border-navy-100 bg-white p-8 text-center">
                                    <Folder className="mx-auto mb-2 h-8 w-8 text-ink-faint" />
                                    <p className="text-xs text-ink-faint">Belum ada folder. Buat folder pertama di File Manager.</p>
                                </div>
                            ) : (
                                <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
                                    {folderBreakdown.map((f, i) => (
                                        <button
                                            key={f.path}
                                            onClick={() => goToFolder(f.path)}
                                            className={cn(
                                                "flex flex-col items-start gap-3 rounded-[var(--radius-card)] p-4 text-left text-white shadow-[var(--shadow-card)] transition-transform hover:-translate-y-0.5",
                                                FOLDER_COLORS[i % FOLDER_COLORS.length]
                                            )}
                                        >
                                            <Folder className="h-5 w-5 opacity-90" />
                                            <div>
                                                <p className="font-mono-data text-xl font-semibold">{f.count}</p>
                                                <p className="truncate text-xs opacity-90">{f.name}</p>
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>

                        <div className="rounded-[var(--radius-card)] border border-navy-100 bg-white p-6 shadow-[var(--shadow-card)]">
                            <h3 className="mb-4 text-sm font-semibold text-ink">Aktivitas Terbaru</h3>
                            <div className="space-y-3">
                                {recentActivity.length === 0 ? (
                                    <p className="text-xs text-ink-muted">Belum ada aktivitas.</p>
                                ) : (
                                    recentActivity.map((a, i) => {
                                        const config = ACTIVITY_ICON[a.type] || ACTIVITY_ICON.document;
                                        const Icon = config.icon;
                                        return (
                                            <div key={i} className="flex items-start gap-3">
                                                <span className={cn("flex h-8 w-8 shrink-0 items-center justify-center rounded-[var(--radius-control)]", config.tint)}>
                                                    <Icon className="h-4 w-4" />
                                                </span>
                                                <div className="min-w-0 flex-1">
                                                    <p className="truncate text-sm font-medium text-ink">{a.title}</p>
                                                    <p className="text-xs text-ink-faint">
                                                        {a.who ? `${a.who} · ` : ""}{formatTime(a.time)}
                                                    </p>
                                                </div>
                                            </div>
                                        );
                                    })
                                )}
                            </div>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}