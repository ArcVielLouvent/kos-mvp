"use client";
import { useState, useEffect } from "react";
import { Folder, FileText, ArrowLeft, Home, Check, Square, CheckSquare, FolderCheck } from "lucide-react";
import { apiJson } from "@/lib/api";

/** Mode "single" (lama): pilih 1 dokumen, klik langsung terpilih.
 * Mode "multi" (baru): checkbox per dokumen (bisa pilih beberapa), PLUS
 * tombol "Pakai folder ini" per folder untuk ambil SEMUA dokumen di
 * dalamnya sekaligus tanpa perlu klik satu-satu -- dipakai fitur Buat
 * Kuis supaya sumbernya tidak dibatasi 1 file doang. */
export function DocumentPicker({
  selectedId, onSelect, mode = "single", selectedIds, onToggle, onUseFolder, currentFolderPath, onNavigate,
}: {
  selectedId?: string | null;
  onSelect?: (doc: { id: string; title: string }) => void;
  mode?: "single" | "multi";
  selectedIds?: Set<string>;
  onToggle?: (doc: { id: string; title: string }) => void;
  onUseFolder?: (folderPath: string) => void;
  currentFolderPath?: string;
  onNavigate?: (path: string) => void;
}) {
  const [internalPath, setInternalPath] = useState("/");
  const path = currentFolderPath ?? internalPath;
  const setPath = onNavigate ?? setInternalPath;
  const [folders, setFolders] = useState<any[]>([]);
  const [files, setFiles] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setIsLoading(true);
    apiJson(`/api/files?path=${encodeURIComponent(path)}`)
      .then((data) => {
        setFolders(data.folders || []);
        setFiles(data.files || []);
      })
      .finally(() => setIsLoading(false));
  }, [path]);

  return (
    <div className="rounded-[var(--radius-control)] border border-navy-100">
      <div className="flex items-center gap-2 border-b border-navy-50 bg-navy-50/50 px-3 py-2">
        <button onClick={() => setPath("/")} className="text-ink-faint hover:text-ink">
          <Home className="h-3.5 w-3.5" />
        </button>
        {path !== "/" && (
          <button
            onClick={() => setPath(path.replace(/\/[^/]+\/$/, "/") || "/")}
            className="flex items-center gap-1 text-2xs font-medium text-navy-700 hover:underline"
          >
            <ArrowLeft className="h-3 w-3" /> Kembali
          </button>
        )}
        <span className="truncate font-mono-data text-2xs text-ink-faint">{path}</span>
        {mode === "multi" && onUseFolder && (
          <button
            onClick={() => onUseFolder(path)}
            className="ml-auto flex shrink-0 items-center gap-1 rounded border border-navy-200 bg-white px-2 py-1 text-2xs font-semibold text-navy-900 hover:bg-navy-50"
          >
            <FolderCheck className="h-3 w-3" /> Pakai semua isi folder ini
          </button>
        )}
      </div>
      <div className="max-h-64 overflow-y-auto p-2">
        {isLoading ? (
          <p className="py-6 text-center text-2xs text-ink-faint">Memuat...</p>
        ) : folders.length === 0 && files.length === 0 ? (
          <p className="py-6 text-center text-2xs text-ink-faint">Folder ini kosong.</p>
        ) : (
          <div className="space-y-0.5">
            {folders.map((f: any) => (
              <button
                key={f.path}
                onClick={() => setPath(f.path)}
                className="flex w-full items-center gap-2 rounded px-2 py-1.5 text-left text-xs text-ink hover:bg-navy-50"
              >
                <Folder className="h-3.5 w-3.5 shrink-0 text-navy-700" /> {f.name}
              </button>
            ))}
            {files.map((doc: any) =>
              mode === "multi" ? (
                <button
                  key={doc.id}
                  onClick={() => onToggle?.({ id: doc.id, title: doc.title })}
                  className={`flex w-full items-center gap-2 rounded px-2 py-1.5 text-left text-xs hover:bg-navy-50 ${selectedIds?.has(doc.id) ? "bg-navy-50 font-semibold text-navy-900" : "text-ink"}`}
                >
                  {selectedIds?.has(doc.id) ? (
                    <CheckSquare className="h-3.5 w-3.5 shrink-0 text-navy-900" />
                  ) : (
                    <Square className="h-3.5 w-3.5 shrink-0 text-ink-faint" />
                  )}
                  <FileText className="h-3.5 w-3.5 shrink-0 text-ink-faint" />
                  <span className="truncate">{doc.title}</span>
                </button>
              ) : (
                <button
                  key={doc.id}
                  onClick={() => onSelect?.({ id: doc.id, title: doc.title })}
                  className={`flex w-full items-center justify-between gap-2 rounded px-2 py-1.5 text-left text-xs hover:bg-navy-50 ${selectedId === doc.id ? "bg-navy-50 font-semibold text-navy-900" : "text-ink"}`}
                >
                  <span className="flex min-w-0 items-center gap-2">
                    <FileText className="h-3.5 w-3.5 shrink-0 text-ink-faint" />
                    <span className="truncate">{doc.title}</span>
                  </span>
                  {selectedId === doc.id && <Check className="h-3.5 w-3.5 shrink-0 text-navy-900" />}
                </button>
              )
            )}
          </div>
        )}
      </div>
    </div>
  );
}

