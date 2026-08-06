"use client";
import { useState, useEffect } from "react";
import { Folder, Home, Download } from "lucide-react";
import { TopBar } from "@/components/TopBar";
import { DocumentBadge } from "@/components/DocumentBadge";

export default function FileManagerPage() {
  const [currentPath, setCurrentPath] = useState("/");
  const [data, setData] = useState({ folders: [], files: [] });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setIsLoading(true);
    fetch(`/api/files?path=${currentPath}`)
      .then(res => res.json())
      .then(result => {
        setData(result);
        setIsLoading(false);
      });
  }, [currentPath]);

  return (
    <div>
      <TopBar title="File Manager" description="Kelola dokumen perusahaan." />
      <div className="p-8">
        <div className="mb-6 flex items-center gap-1 text-sm">
          <button onClick={() => setCurrentPath("/")} className="flex items-center gap-1.5 rounded-[var(--radius-control)] bg-navy-900 px-3 py-2 font-medium text-white">
            <Home className="h-4 w-4" /> Drive Akses
          </button>
        </div>
        
        {isLoading ? (
          <p className="animate-pulse text-sm text-ink-muted">Menyinkronkan dengan Backend Python...</p>
        ) : (
          <>
            <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
              {data.folders.map((f: any) => (
                <button key={f.path} onClick={() => setCurrentPath(f.path)} className="flex items-center gap-3 rounded-[var(--radius-card)] border border-navy-100 bg-white p-4 text-left hover:bg-navy-50">
                  <span className="flex h-9 w-9 items-center justify-center rounded-[var(--radius-control)] bg-navy-50">
                    <Folder className="h-4.5 w-4.5 text-navy-700" />
                  </span>
                  <span className="text-sm font-medium text-ink">{f.name}</span>
                </button>
              ))}
            </div>
            
            <div className="overflow-hidden rounded-[var(--radius-card)] border border-navy-100 bg-white">
              {data.files.map((f: any) => (
                <div key={f.id} className="flex items-center gap-3 border-b border-navy-100 px-4 py-3">
                  <DocumentBadge type={f.metadata.tipe_file} size="sm" />
                  <span className="flex-1 text-sm font-medium text-ink">{f.title}</span>
                  <button className="flex items-center gap-1.5 rounded-[var(--radius-control)] border border-navy-100 px-2.5 py-1.5 text-xs font-medium text-ink-muted hover:bg-navy-50">
                    <Download className="h-3.5 w-3.5" /> Unduh
                  </button>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
