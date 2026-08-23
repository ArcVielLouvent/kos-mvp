"use client";
import { useState, useEffect } from "react";
import { Folder, FileText, ArrowLeft, Home, Check } from "lucide-react";
import { apiJson } from "@/lib/api";

export function DocumentPicker({
  selectedId, onSelect,
}: {
  selectedId: string | null;
  onSelect: (doc: { id: string; title: string }) => void;
}) {
  const [path, setPath] = useState("/");
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
            {files.map((doc: any) => (
              <button
                key={doc.id}
                onClick={() => onSelect({ id: doc.id, title: doc.title })}
                className={`flex w-full items-center justify-between gap-2 rounded px-2 py-1.5 text-left text-xs hover:bg-navy-50 ${selectedId === doc.id ? "bg-navy-50 font-semibold text-navy-900" : "text-ink"}`}
              >
                <span className="flex min-w-0 items-center gap-2">
                  <FileText className="h-3.5 w-3.5 shrink-0 text-ink-faint" />
                  <span className="truncate">{doc.title}</span>
                </span>
                {selectedId === doc.id && <Check className="h-3.5 w-3.5 shrink-0 text-navy-900" />}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
