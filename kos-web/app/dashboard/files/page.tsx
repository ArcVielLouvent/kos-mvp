"use client";
import { useState, useMemo } from "react";
import {
    Folder,
    Home,
    ChevronRight,
    Plus,
    Upload,
    Search,
    LayoutGrid,
    List,
    MoreVertical,
    Download,
    Trash2,
    Pencil,
    Move,
} from "lucide-react";
import { TopBar } from "@/components/TopBar";
import { DocumentBadge } from "@/components/DocumentBadge";
import { cn } from "@/lib/utils";
import { getChildFolders, getDocumentsInFolder } from "@/lib/mock-data";

export default function FileManagerPage() {
    const [currentPath, setCurrentPath] = useState("/");
    const [view, setView] = useState<"grid" | "list">("grid");
    const [search, setSearch] = useState("");
    const [selected, setSelected] = useState<Set<string>>(new Set());
    const [newFolderOpen, setNewFolderOpen] = useState(false);
    const [newFolderName, setNewFolderName] = useState("");
    const [openMenuId, setOpenMenuId] = useState<string | null>(null);

    const segments = currentPath.split("/").filter(Boolean);
    const folders = useMemo(() => getChildFolders(currentPath), [currentPath]);
    const files = useMemo(() => {
        const all = getDocumentsInFolder(currentPath);
        if (!search.trim()) return all;
        return all.filter((f) => f.title.toLowerCase().includes(search.toLowerCase()));
    }, [currentPath, search]);

    function goTo(path: string) {
        setCurrentPath(path);
        setSelected(new Set());
        setOpenMenuId(null);
    }

    function toggleSelect(id: string) {
        setSelected((prev) => {
            const next = new Set(prev);
            next.has(id) ? next.delete(id) : next.add(id);
            return next;
        });
    }

    return (
        <div>
            <TopBar
                title="File Manager"
                description="Kelola dokumen, gambar, audio, dan video perusahaan."
            />
            <div className="p-8">
                <div className="mb-4 flex items-center gap-1 text-sm">
                    <button
                        onClick={() => goTo("/")}
                        className={cn(
                            "flex items-center gap-1.5 rounded-[var(--radius-control)] px-2.5 py-1.5 font-medium transition-colors",
                            currentPath === "/" ? "bg-navy-900 text-white" : "text-ink-muted hover:bg-navy-50"
                        )}
                    >
                        <Home className="h-3.5 w-3.5" />
                        Drive
                    </button>
                    {segments.map((seg, i) => {
                        const path = "/" + segments.slice(0, i + 1).join("/") + "/";
                        const active = path === currentPath;
                        return (
                            <span key={path} className="flex items-center gap-1">
                                <ChevronRight className="h-3.5 w-3.5 text-ink-faint" />
                                <button
                                    onClick={() => goTo(path)}
                                    className={cn(
                                        "rounded-[var(--radius-control)] px-2.5 py-1.5 font-medium transition-colors",
                                        active ? "bg-navy-900 text-white" : "text-ink-muted hover:bg-navy-50"
                                    )}
                                >
                                    {seg}
                                </button>
                            </span>
                        );
                    })}
                </div>

                <div className="mb-5 flex flex-wrap items-center gap-2">
                    <button
                        onClick={() => setNewFolderOpen(true)}
                        className="flex items-center gap-1.5 rounded-[var(--radius-control)] border border-navy-100 bg-white px-3 py-2 text-sm font-medium text-ink hover:bg-navy-50"
                    >
                        <Plus className="h-4 w-4" /> Folder Baru
                    </button>
                    <button className="flex items-center gap-1.5 rounded-[var(--radius-control)] bg-navy-900 px-3 py-2 text-sm font-medium text-white hover:bg-navy-800">
                        <Upload className="h-4 w-4" /> Upload File
                    </button>

                    <div className="ml-auto flex items-center gap-2">
                        <div className="relative">
                            <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint" />
                            <input
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                                placeholder="Cari file..."
                                className="w-56 rounded-[var(--radius-control)] border border-navy-100 py-2 pl-8 pr-3 text-sm placeholder:text-ink-faint focus:border-navy-500 focus:outline-none"
                            />
                        </div>
                        <div className="flex rounded-[var(--radius-control)] border border-navy-100 bg-white p-0.5">
                            <button
                                onClick={() => setView("grid")}
                                className={cn("rounded-[6px] p-1.5", view === "grid" ? "bg-navy-100 text-navy-900" : "text-ink-faint")}
                            >
                                <LayoutGrid className="h-4 w-4" />
                            </button>
                            <button
                                onClick={() => setView("list")}
                                className={cn("rounded-[6px] p-1.5", view === "list" ? "bg-navy-100 text-navy-900" : "text-ink-faint")}
                            >
                                <List className="h-4 w-4" />
                            </button>
                        </div>
                    </div>
                </div>

                {selected.size > 0 && (
                    <div className="mb-4 flex items-center justify-between rounded-[var(--radius-control)] bg-navy-900 px-4 py-2.5 text-sm text-white">
                        <span>{selected.size} item dipilih</span>
                        <button className="flex items-center gap-1.5 rounded-[var(--radius-control)] bg-red-600 px-3 py-1.5 font-medium hover:bg-red-700">
                            <Trash2 className="h-3.5 w-3.5" /> Hapus Terpilih
                        </button>
                    </div>
                )}

                {folders.length === 0 && files.length === 0 && (
                    <p className="py-12 text-center text-sm text-ink-faint">Direktori ini masih kosong.</p>
                )}

                {folders.length > 0 && (
                    <div className="mb-6">
                        <p className="mb-2.5 text-xs font-semibold uppercase tracking-wide text-ink-faint">Folder</p>
                        <div className={view === "grid" ? "grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4" : "space-y-1"}>
                            {folders.map((f) => (
                                <button
                                    key={f.path}
                                    onDoubleClick={() => goTo(f.path)}
                                    onClick={() => goTo(f.path)}
                                    className={cn(
                                        "group flex items-center gap-3 rounded-[var(--radius-card)] border border-navy-100 bg-white text-left transition-colors hover:border-navy-300 hover:bg-navy-50",
                                        view === "grid" ? "p-4" : "px-3 py-2.5"
                                    )}
                                >
                                    <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[var(--radius-control)] bg-navy-50">
                                        <Folder className="h-4.5 w-4.5 text-navy-700" fill="currentColor" fillOpacity={0.15} />
                                    </span>
                                    <span className="truncate text-sm font-medium text-ink">{f.name}</span>
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {files.length > 0 && (
                    <div>
                        <p className="mb-2.5 text-xs font-semibold uppercase tracking-wide text-ink-faint">File</p>
                        <div className="overflow-hidden rounded-[var(--radius-card)] border border-navy-100 bg-white">
                            {files.map((f, idx) => (
                                <div
                                    key={f.id}
                                    className={cn(
                                        "flex items-center gap-3 px-4 py-3",
                                        idx !== files.length - 1 && "border-b border-navy-100"
                                    )}
                                >
                                    <input
                                        type="checkbox"
                                        checked={selected.has(f.id)}
                                        onChange={() => toggleSelect(f.id)}
                                        className="h-4 w-4 rounded border-navy-300 text-navy-900 focus:ring-navy-500"
                                    />
                                    <DocumentBadge type={f.metadata.tipe_file} size="sm" />
                                    <span className="min-w-0 flex-1 truncate text-sm font-medium text-ink">{f.title}</span>
                                    <span className="hidden font-mono-data text-xs text-ink-faint sm:block">
                                        {new Date(f.created_at).toLocaleDateString("id-ID")}
                                    </span>
                                    <button className="flex items-center gap-1.5 rounded-[var(--radius-control)] border border-navy-100 px-2.5 py-1.5 text-xs font-medium text-ink-muted hover:bg-navy-50">
                                        <Download className="h-3.5 w-3.5" />
                                        Unduh
                                    </button>
                                    <div className="relative">
                                        <button
                                            onClick={() => setOpenMenuId(openMenuId === f.id ? null : f.id)}
                                            className="rounded-[var(--radius-control)] p-1.5 text-ink-faint hover:bg-navy-50"
                                        >
                                            <MoreVertical className="h-4 w-4" />
                                        </button>
                                        {openMenuId === f.id && (
                                            <div className="absolute right-0 top-full z-10 mt-1 w-40 overflow-hidden rounded-[var(--radius-control)] border border-navy-100 bg-white py-1 shadow-[var(--shadow-panel)]">
                                                <MenuItem icon={Pencil} label="Ganti nama" />
                                                <MenuItem icon={Move} label="Pindahkan" />
                                                <MenuItem icon={Trash2} label="Hapus" danger />
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {newFolderOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-navy-950/40 px-4">
                    <div className="w-full max-w-sm rounded-[var(--radius-card)] bg-white p-6 shadow-[var(--shadow-panel)]">
                        <h3 className="mb-4 text-base font-semibold text-ink">Buat Folder Baru</h3>
                        <input
                            autoFocus
                            value={newFolderName}
                            onChange={(e) => setNewFolderName(e.target.value)}
                            placeholder="Nama folder"
                            className="w-full rounded-[var(--radius-control)] border border-navy-100 px-3 py-2.5 text-sm focus:border-navy-500 focus:outline-none"
                        />
                        <div className="mt-5 flex justify-end gap-2">
                            <button
                                onClick={() => { setNewFolderOpen(false); setNewFolderName(""); }}
                                className="rounded-[var(--radius-control)] px-4 py-2 text-sm font-medium text-ink-muted hover:bg-navy-50"
                            >
                                Batal
                            </button>
                            <button
                                onClick={() => { setNewFolderOpen(false); setNewFolderName(""); }}
                                className="rounded-[var(--radius-control)] bg-navy-900 px-4 py-2 text-sm font-medium text-white hover:bg-navy-800"
                            >
                                Buat
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

function MenuItem({
    icon: Icon,
    label,
    danger,
}: {
    icon: typeof Pencil;
    label: string;
    danger?: boolean;
}) {
    return (
        <button
            className={cn(
                "flex w-full items-center gap-2.5 px-3 py-2 text-left text-sm hover:bg-navy-50",
                danger ? "text-red-600 hover:bg-red-50" : "text-ink-muted"
            )}
        >
            <Icon className="h-3.5 w-3.5" />
            {label}
        </button>
    );
}