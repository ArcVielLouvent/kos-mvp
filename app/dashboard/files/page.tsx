"use client";
import { useState, useEffect } from "react";
import { Folder, Home, Download } from "lucide-react";
import { TopBar } from "@/components/TopBar";
import { DocumentBadge } from "@/components/DocumentBadge";

// API URL dinamis (Vercel otomatis pakai domain produksi kosong, lokal pakai localhost)
const API_URL = typeof window !== "undefined" && window.location.hostname === "localhost"
  ? "http://localhost:8000"
  : "";

export default function FileManagerPage() {
  const [currentPath, setCurrentPath] = useState("/");
  const [data, setData] = useState({ folders: [], files: [] });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setIsLoading(true);

    // Ambil token JWT session user yang tersimpan dari localStorage atau cookies saat login
    const token = typeof window !== "undefined" ? localStorage.getItem("sb-access-token") || localStorage.getItem("supabase_token") : null;

    // Menggunakan API_URL dinamis dan menyuntikkan Authorization Header berbasis Bearer Token JWT
    fetch(`${API_URL}/api/files?path=${currentPath}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}` // Identitas perusahaan otomatis terdeteksi dari sini
      }
    })
      .then(res => {
        if (!res.ok) {
          throw new Error("Gagal mengambil data berkas dari server.");
        }
        return res.json();
      })
      .then(result => {
        setData(result);
        setIsLoading(false);
      })
      .catch(err => {
        console.error("FileManager Error:", err);
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
            {data.folders.length === 0 && data.files.length === 0 ? (
              <p className="text-center text-sm text-ink-muted py-8">Tidak ada berkas atau folder di direktori ini.</p>
            ) : (
              <>
                <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
                  {data.folders?.map((f: any) => (
                    <button key={f.path} onClick={() => setCurrentPath(f.path)} className="flex items-center gap-3 rounded-[var(--radius-card)] border border-navy-100 bg-white p-4 text-left hover:bg-navy-50">
                      <span className="flex h-9 w-9 items-center justify-center rounded-[var(--radius-control)] bg-navy-50">
                        <Folder className="h-4.5 w-4.5 text-navy-700" />
                      </span>
                      <span className="text-sm font-medium text-ink">{f.name}</span>
                    </button>
                  ))}
                </div>

                <div className="overflow-hidden rounded-[var(--radius-card)] border border-navy-100 bg-white">
                  {data.files?.map((f: any) => (
                    <div key={f.id} className="flex items-center gap-3 border-b border-navy-100 px-4 py-3">
                      <DocumentBadge type={f.metadata?.tipe_file || "pdf"} size="sm" />
                      <span className="flex-1 text-sm font-medium text-ink">{f.title}</span>
                      <button className="flex items-center gap-1.5 rounded-[var(--radius-control)] border border-navy-100 px-2.5 py-1.5 text-xs font-medium text-ink-muted hover:bg-navy-50">
                        <Download className="h-3.5 w-3.5" /> Unduh
                      </button>
                    </div>
                  ))}
                </div>
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}
