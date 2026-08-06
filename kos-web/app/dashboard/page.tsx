import { TopBar } from "@/components/TopBar";
import { DocumentBadge } from "@/components/DocumentBadge";
import {
    FileText,
    Users,
    FolderTree,
    MessageSquare,
    ArrowUpRight,
} from "lucide-react";

// TODO: ganti dengan query Supabase asli (tabel documents/users/folders/chat_sessions) begitu backend final tersambung.
const STATS = [
    { label: "Total Dokumen", value: 50, icon: FileText, tint: "bg-navy-900" },
    { label: "Total Karyawan", value: 14, icon: Users, tint: "bg-navy-700" },
    { label: "Total Folder", value: 6, icon: FolderTree, tint: "bg-navy-500" },
    { label: "Percakapan Minggu Ini", value: 27, icon: MessageSquare, tint: "bg-navy-300" },
];

const FOLDER_BREAKDOWN = [
    { name: "SOP & Operasional", count: 18, color: "bg-navy-900" },
    { name: "HRD & Karyawan", count: 12, color: "bg-navy-700" },
    { name: "Keuangan", count: 8, color: "bg-navy-500" },
    { name: "Penilaian Karyawan / KPI", count: 7, color: "bg-navy-300" },
    { name: "Marketing", count: 3, color: "bg-navy-100 text-navy-900" },
    { name: "Lainnya", count: 2, color: "bg-navy-50 text-navy-900 border border-navy-100" },
];

const RECENT_ACTIVITY = [
    { title: "Kamus KPI Manajer Produksi.xlsx", type: "Spreadsheet" as const, who: "admin@kopinusantara.com", time: "10 menit lalu" },
    { title: "Teknik Pembuatan KPI", type: "Video YouTube" as const, who: "admin@kopinusantara.com", time: "1 jam lalu" },
    { title: "SOP Penerimaan Karyawan Baru.docx", type: "Dokumen Word" as const, who: "budi@kopinusantara.com", time: "3 jam lalu" },
];

export default function DashboardPage() {
    return (
        <div>
            <TopBar title="Dashboard" description="Ringkasan aktivitas dan pengetahuan perusahaan Anda." />
            <div className="space-y-6 p-8">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    {STATS.map((stat) => {
                        const Icon = stat.icon;
                        return (
                            <div key={stat.label} className="rounded-[var(--radius-card)] border border-navy-100 bg-white p-5 shadow-[var(--shadow-card)]">
                                <span className={`flex h-10 w-10 items-center justify-center rounded-[var(--radius-control)] ${stat.tint}`}>
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
                            <h3 className="text-sm font-semibold text-ink">Dokumen per Folder</h3>
                            <a href="/dashboard/files" className="flex items-center gap-1 text-xs font-medium text-navy-700 hover:underline">
                                Lihat semua <ArrowUpRight className="h-3 w-3" />
                            </a>
                        </div>
                        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                            {FOLDER_BREAKDOWN.map((f) => (
                                <div key={f.name} className={`rounded-[var(--radius-control)] p-4 ${f.color} ${f.color.includes("text-navy-900") ? "" : "text-white"}`}>
                                    <p className="font-mono-data text-xl font-semibold">{f.count}</p>
                                    <p className="mt-1 text-xs leading-snug opacity-90">{f.name}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                    <div className="rounded-[var(--radius-card)] border border-navy-100 bg-white p-6 shadow-[var(--shadow-card)]">
                        <h3 className="mb-4 text-sm font-semibold text-ink">Aktivitas Terbaru</h3>
                        <div className="space-y-4">
                            {RECENT_ACTIVITY.map((a, i) => (
                                <div key={i} className="flex items-start gap-3">
                                    <DocumentBadge type={a.type} size="sm" />
                                    <div className="min-w-0 flex-1">
                                        <p className="truncate text-sm font-medium text-ink">{a.title}</p>
                                        <p className="text-xs text-ink-faint">{a.who} · {a.time}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}