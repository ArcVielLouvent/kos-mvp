"use client";
import { useState, useEffect } from "react";
import { Home, Folder } from "lucide-react";
import { apiJson } from "@/lib/api";

interface FolderChild {
    path: string;
    name: string;
}

/** Folder picker gaya "telusuri" (breadcrumb + klik masuk folder), bukan
 * dropdown datar -- supaya tetap enak dipakai walau folder-nya banyak di
 * masa depan. Samain logic dengan folder_picker() di app.py (Streamlit). */
export function FolderTreePicker({
    value,
    onChange,
}: {
    value: string;
    onChange: (path: string) => void;
}) {
    const [browsePath, setBrowsePath] = useState("/");
    const [children, setChildren] = useState<FolderChild[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        setIsLoading(true);
        setError("");
        apiJson(`/api/folders/children?path=${encodeURIComponent(browsePath)}`)
            .then((res) => setChildren(res.children || []))
            .catch((e: any) => {
                setChildren([]);
                setError(e.message || "Gagal memuat folder.");
            })
            .finally(() => setIsLoading(false));
    }, [browsePath]);

    const parts = browsePath.split("/").filter(Boolean);

    return (
        <div className="space-y-2 rounded border border-navy-100 bg-white p-3">
            <div className="flex flex-wrap items-center gap-1">
                <button
                    type="button"
                    onClick={() => setBrowsePath("/")}
                    className="flex items-center gap-1 rounded-full border border-navy-100 px-2.5 py-1 text-xs text-ink-muted hover:border-navy-300 hover:text-ink"
                >
                    <Home className="h-3 w-3" /> Drive
                </button>
                {parts.map((part, i) => {
                    const accum = "/" + parts.slice(0, i + 1).join("/") + "/";
                    return (
                        <button
                            type="button"
                            key={accum}
                            onClick={() => setBrowsePath(accum)}
                            className="rounded-full border border-navy-100 px-2.5 py-1 text-xs text-ink-muted hover:border-navy-300 hover:text-ink"
                        >
                            {part}
                        </button>
                    );
                })}
            </div>

            <div className="max-h-48 space-y-1 overflow-y-auto">
                {isLoading ? (
                    <p className="text-xs text-ink-faint">Memuat folder...</p>
                ) : error ? (
                    <p className="text-xs text-red-600">{error}</p>
                ) : children.length === 0 ? (
                    <p className="text-xs text-ink-faint">Tidak ada sub-folder di sini.</p>
                ) : (
                    children.map((c) => (
                        <button
                            type="button"
                            key={c.path}
                            onClick={() => setBrowsePath(c.path)}
                            className="flex w-full items-center gap-2 rounded px-2 py-1.5 text-left text-xs text-ink hover:bg-navy-50"
                        >
                            <Folder className="h-3.5 w-3.5 text-navy-700" /> {c.name}
                        </button>
                    ))
                )}
            </div>

            <div className="flex items-center justify-between border-t border-navy-100 pt-2">
                <span className="text-2xs text-ink-faint">
                    Sedang menelusuri: <code className="font-mono-data">{browsePath}</code>
                </span>
                <button
                    type="button"
                    onClick={() => onChange(browsePath)}
                    className="rounded bg-navy-900 px-3 py-1.5 text-2xs font-semibold text-white hover:bg-navy-800"
                >
                    Pilih folder ini
                </button>
            </div>

            {value && (
                <p className="text-2xs text-ink-muted">
                    Folder terpilih: <code className="font-mono-data">{value}</code>
                </p>
            )}
        </div>
    );
}