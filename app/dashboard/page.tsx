"use client";
import { useState, useEffect } from "react";
import { TopBar } from "@/components/TopBar";
import { FileManagerBody } from "@/components/FileManagerBody";
import { EmployeeDirectoryBody } from "@/components/EmployeeDirectoryBody";
import { ChatHistoryBrowser } from "@/components/ChatHistoryBrowser";
import { FileText, Users, MessageSquare, ArrowLeft, Folder } from "lucide-react";
import { apiJson } from "@/lib/api";
import { cn } from "@/lib/utils";

type ViewMode = "overview" | "files" | "employees" | "chats";

const ACTIVITY_ICON: Record<string, any> = {
    document: { icon: FileText, tint: "bg-navy-50 text-navy-700" },
    chat: { icon: MessageSquare, tint: "bg-navy-50 text-navy-700" },
    employee: { icon: Users, tint: "bg-navy-50 text-navy-700" },
};

const FOLDER_COLORS = ["bg-navy-900", "bg-success", "bg-warning", "bg-danger", "bg-navy-700"];

function formatTime(iso: string) {
    if (!iso) return "";
    return iso.slice(0, 16).replace("T", " ");
}

export default function DashboardPage() {
    const [view, setView] = useState<ViewMode>("overview");
    const [filesInitialPath, setFilesInitialPath] = useState("/");
    const [docCount, setDocCount] = useState<number | string>("-");
    const [folderCount, setFolderCount] = useState<number | string>("-");
    const [employeeCount, setEmployeeCount] = useState<number | string>("-");
    const [chatCount, setChatCount] = useState<number | string>("-");
    const [folderBreakdown, setFolderBreakdown] = useState<any[]>([]);
    const [recentActivity, setRecentActivity] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        apiJson("/api/dashboard")
            .then((result) => {
                const stats = result.stats || [];
                const find = (label: string) => stats.find((s: any) => s.label === label)?.value ?? "-";
                setDocCount(find("Total Dokumen"));
                setFolderCount(find("Total Folder"));
                setEmployeeCount(find("Total Karyawan"));
                setChatCount(find("Total Percakapan"));
                setFolderBreakdown(result.folderBreakdown || []);
                setRecentActivity(result.recent || []);
                setIsLoading(false);
            })
            .catch(() => setIsLoading(false));
    }, []);

    const openFiles = (path: string = "/") => {
        setFilesInitialPath(path);
        setView("files");
    };

    const titles: Record<ViewMode, string> = {
        overview: "Dashboard",
        files: "Dokumen & Folder",
        employees: "Karyawan",
        chats: "Riwayat Percakapan",
    };

    return (
        <div>
            <TopBar
                title={titles[view]}
                description={view === "overview" ? "Ringkasan aktivitas dan pengetahuan perusahaan Anda." : undefined}
                action={
                    view !== "overview" ? (
                        <button
                            onClick={() => setView("overview")}
                            className="flex items-center gap-1.5 rounded-[var(--radius-control)] border border-navy-100 px-3 py-1.5 text-xs font-medium text-ink hover:bg-navy-50"
                        >
                            <ArrowLeft className="h-3.5 w-3.5" /> Kembali ke Dashboard
                        </button>
                    ) : undefined
                }
            />

            <div className="p-8">
                {view === "files" && <FileManagerBody initialPath={filesInitialPath} />}
                {view === "employees" && <EmployeeDirectoryBody />}
                {view === "chats" && <ChatHistoryBrowser />}

                {view === "overview" && (
                    isLoading ? (
                        <p className="animate-pulse text-sm text-ink-muted">Memuat statistik real-time...</p>
                    ) : (
                        <div className="space-y-6">
                            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                                {/* Kartu gabungan: Dokumen + Folder dalam 1 kotak, klik buka File Manager di root */}
                                <button
                                    onClick={() => openFiles("/")}
                                    className="rounded-[var(--radius-card)] border border-navy-100 bg-white p-5 text-left shadow-[var(--shadow-card)] transition-transform hover:-translate-y-0.5"
                                >
                                    <span className="flex h-10 w-10 items-center justify-center rounded-[var(--radius-control)] bg-navy-900">
                                        <FileText className="h-5 w-5 text-white" strokeWidth={2} />
                                    </span>
                                    <div className="mt-4 flex items-baseline gap-2">
                                        <p className="font-mono-data text-2xl font-semibold text-ink">{docCount}</p>
                                        <span className="text-xs text-ink-faint">dokumen</span>
                                    </div>
                                    <div className="mt-1 flex items-center gap-1.5 text-xs text-ink-muted">
                                        <Folder className="h-3 w-3" /> {folderCount} folder
                                    </div>
                                </button>

                                {/* Kartu Karyawan, klik buka direktori karyawan */}
                                <button
                                    onClick={() => setView("employees")}
                                    className="rounded-[var(--radius-card)] border border-navy-100 bg-white p-5 text-left shadow-[var(--shadow-card)] transition-transform hover:-translate-y-0.5"
                                >
                                    <span className="flex h-10 w-10 items-center justify-center rounded-[var(--radius-control)] bg-success">
                                        <Users className="h-5 w-5 text-white" strokeWidth={2} />
                                    </span>
                                    <p className="mt-4 font-mono-data text-2xl font-semibold text-ink">{employeeCount}</p>
                                    <p className="text-sm text-ink-muted">Karyawan</p>
                                </button>

                                {/* Kartu Riwayat Percakapan, klik buka browser riwayat + filter bulan/tahun */}
                                <button
                                    onClick={() => setView("chats")}
                                    className="rounded-[var(--radius-card)] border border-navy-100 bg-white p-5 text-left shadow-[var(--shadow-card)] transition-transform hover:-translate-y-0.5"
                                >
                                    <span className="flex h-10 w-10 items-center justify-center rounded-[var(--radius-control)] bg-danger">
                                        <MessageSquare className="h-5 w-5 text-white" strokeWidth={2} />
                                    </span>
                                    <p className="mt-4 font-mono-data text-2xl font-semibold text-ink">{chatCount}</p>
                                    <p className="text-sm text-ink-muted">Riwayat Percakapan</p>
                                </button>
                            </div>

                            {/* Preview root folder -- klik langsung ke folder itu di File Manager */}
                            {folderBreakdown.length > 0 && (
                                <div>
                                    <div className="mb-3 flex items-center justify-between">
                                        <h3 className="text-sm font-semibold text-ink">Folder</h3>
                                        <button onClick={() => openFiles("/")} className="text-xs font-medium text-navy-700 hover:underline">
                                            Lihat semua
                                        </button>
                                    </div>
                                    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
                                        {folderBreakdown.map((f: any, i: number) => (
                                            <button
                                                key={f.path}
                                                onClick={() => openFiles(f.path)}
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
                                </div>
                            )}

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
                        </div>
                    )
                )}
            </div>
        </div>
    );
}
