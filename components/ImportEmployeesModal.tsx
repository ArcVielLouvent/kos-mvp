"use client";
import { useState } from "react";
import { Upload, Download, X, Loader2, CheckCircle2, AlertTriangle } from "lucide-react";
import { apiFetch, downloadBase64 } from "@/lib/api";

export function ImportEmployeesModal({ onClose, onDone }: { onClose: () => void; onDone: () => void }) {
  const [isUploading, setIsUploading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const downloadTemplate = async () => {
    try {
      const res = await apiFetch("/api/team/import-template");
      const data = await res.json();
      downloadBase64(data.filename, data.base64, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
    } catch {}
  };

  const handleFile = async (file: File | null) => {
    if (!file) return;
    setIsUploading(true);
    setError(null);
    setResult(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await apiFetch("/api/team/import-excel", { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Gagal import.");
      setResult(data);
      onDone();
    } catch (e: any) {
      setError(e.message || "Gagal memproses file.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={onClose}>
      <div className="w-full max-w-lg space-y-4 rounded-[var(--radius-card)] bg-white p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-ink">Import/Update Karyawan dari Excel</h3>
          <button onClick={onClose} className="rounded-full p-1 text-ink-muted hover:bg-navy-50">
            <X className="h-4 w-4" />
          </button>
        </div>

        <p className="text-xs text-ink-faint">
          Upload 1 file .xlsx berisi banyak karyawan sekaligus. Baris dengan email yang <b>sudah terdaftar</b> akan
          di-update datanya (nama/jabatan/folder/atasan) -- password login karyawan itu <b>tidak berubah</b>. Baris
          dengan email baru akan dibuatkan akun baru + password sementara, sama seperti tambah manual.
        </p>

        <button
          onClick={downloadTemplate}
          className="flex w-full items-center justify-center gap-2 rounded-[var(--radius-control)] border border-navy-100 bg-white py-2 text-xs font-semibold text-ink-muted hover:bg-navy-50"
        >
          <Download className="h-3.5 w-3.5" /> Unduh Template Excel
        </button>

        <label className="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-[var(--radius-card)] border-2 border-dashed border-navy-100 bg-navy-50/30 py-8 text-center hover:border-navy-300">
          {isUploading ? (
            <Loader2 className="h-6 w-6 animate-spin text-navy-700" />
          ) : (
            <Upload className="h-6 w-6 text-ink-faint" />
          )}
          <span className="text-xs font-medium text-ink-muted">
            {isUploading ? "Memproses..." : "Klik untuk pilih file .xlsx"}
          </span>
          <input type="file" accept=".xlsx,.xls" disabled={isUploading} className="hidden" onChange={(e) => handleFile(e.target.files?.[0] || null)} />
        </label>

        {error && (
          <p className="flex items-start gap-2 rounded-[var(--radius-control)] bg-red-50 px-3 py-2 text-xs font-medium text-red-700">
            <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" /> {error}
          </p>
        )}

        {result && (
          <div className="space-y-2 rounded-[var(--radius-control)] bg-navy-50 p-3">
            <p className="flex items-center gap-2 text-xs font-semibold text-navy-900">
              <CheckCircle2 className="h-4 w-4 text-green-600" /> {result.message}
            </p>
            {result.temporary_passwords && Object.keys(result.temporary_passwords).length > 0 && (
              <div className="max-h-32 overflow-y-auto rounded border border-navy-100 bg-white p-2 text-2xs">
                {Object.entries(result.temporary_passwords).map(([email, pw]) => (
                  <div key={email} className="flex justify-between gap-2 py-0.5">
                    <span className="truncate text-ink-muted">{email}</span>
                    <span className="font-mono-data font-semibold text-ink">{pw as string}</span>
                  </div>
                ))}
              </div>
            )}
            {result.errors && result.errors.length > 0 && (
              <div className="space-y-1">
                {result.errors.map((e: string, i: number) => (
                  <p key={i} className="text-2xs text-amber-700">{e}</p>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
