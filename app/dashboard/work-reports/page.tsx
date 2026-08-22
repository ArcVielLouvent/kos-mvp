"use client";
import { useState, useEffect } from "react";
import { Plus, Trash2, Paperclip, Loader2, Send, Pencil, History, X } from "lucide-react";
import Link from "next/link";
import { TopBar } from "@/components/TopBar";
import { apiJson, apiFetch, getStoredUser } from "@/lib/api";

interface Row {
  _key: string;
  description: string;
  time_note: string;
  attachment_url?: string;
  attachment_kind?: string;
  attachment_name?: string;
  uploading?: boolean;
}

function newRow(): Row {
  return { _key: Math.random().toString(36).slice(2), description: "", time_note: "" };
}

export default function WorkReportPage() {
  const user = getStoredUser();
  const [isLoading, setIsLoading] = useState(true);
  const [report, setReport] = useState<any>(null);
  const [editing, setEditing] = useState(false);
  const [rows, setRows] = useState<Row[]>([newRow()]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const load = () => {
    setIsLoading(true);
    apiJson("/api/work-reports/today")
      .then((data) => {
        setReport(data.report);
        if (data.report) {
          setRows(
            (data.report.rows || []).map((r: any) => ({
              _key: r.id,
              description: r.description,
              time_note: r.time_note || "",
              attachment_url: r.attachment_url,
              attachment_kind: r.attachment_kind,
              attachment_name: r.attachment_url ? r.attachment_url.split("/").pop()?.split("?")[0] : undefined,
            }))
          );
          setEditing(false);
        } else {
          setRows([newRow()]);
          setEditing(true);
        }
      })
      .finally(() => setIsLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const updateRow = (key: string, patch: Partial<Row>) => {
    setRows((prev) => prev.map((r) => (r._key === key ? { ...r, ...patch } : r)));
  };

  const addRow = () => setRows((prev) => [...prev, newRow()]);

  const removeRow = (key: string) => setRows((prev) => (prev.length > 1 ? prev.filter((r) => r._key !== key) : prev));

  const handleAttachmentChange = async (row: Row, file: File | null) => {
    if (!file) return;
    updateRow(row._key, { uploading: true });
    setErrorMsg(null);
    try {
      const formData = new FormData();
      formData.append("row_key", row._key);
      formData.append("file", file);
      const res = await apiFetch("/api/work-reports/upload-attachment", { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Upload lampiran gagal.");
      updateRow(row._key, {
        attachment_url: data.file_url,
        attachment_kind: data.file_kind,
        attachment_name: file.name,
        uploading: false,
      });
    } catch (e: any) {
      setErrorMsg(e.message || "Upload lampiran gagal.");
      updateRow(row._key, { uploading: false });
    }
  };

  const handleSubmit = async () => {
    setErrorMsg(null);
    const filled = rows.filter((r) => r.description.trim());
    if (filled.length === 0) {
      setErrorMsg("Isi minimal 1 baris pekerjaan.");
      return;
    }
    setIsSubmitting(true);
    try {
      await apiJson("/api/work-reports/submit", {
        method: "POST",
        body: JSON.stringify({
          rows: filled.map((r) => ({
            description: r.description.trim(),
            time_note: r.time_note.trim() || null,
            attachment_url: r.attachment_url || null,
            attachment_kind: r.attachment_kind || null,
          })),
        }),
      });
      load();
    } catch (e: any) {
      setErrorMsg(e.message || "Gagal mengirim laporan.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const today = new Date().toLocaleDateString("id-ID", { weekday: "long", day: "numeric", month: "long", year: "numeric" });
  const now = new Date().toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" });

  return (
    <div>
      <TopBar
        title="Lapor Kerjaan"
        description="Rincian pekerjaan hari ini, baris bebas ditambah sendiri seperti spreadsheet."
        action={
          <Link href="/dashboard/work-reports/history" className="flex items-center gap-2 rounded-[var(--radius-control)] border border-navy-100 bg-white px-3 py-2 text-xs font-semibold text-ink-muted hover:bg-navy-50">
            <History className="h-3.5 w-3.5" /> Riwayat Laporan Saya
          </Link>
        }
      />
      <div className="p-8">
        <div className="mx-auto max-w-3xl">
          {/* Header auto-isi -- tanggal/jam/nama TIDAK diketik manual */}
          <div className="mb-4 grid grid-cols-3 gap-3 rounded-[var(--radius-card)] border border-navy-100 bg-white p-4 text-xs">
            <div>
              <p className="text-2xs font-semibold uppercase tracking-wide text-ink-faint">Tanggal</p>
              <p className="mt-0.5 font-medium text-ink">{today}</p>
            </div>
            <div>
              <p className="text-2xs font-semibold uppercase tracking-wide text-ink-faint">Jam</p>
              <p className="mt-0.5 font-medium text-ink">{now}</p>
            </div>
            <div>
              <p className="text-2xs font-semibold uppercase tracking-wide text-ink-faint">Nama</p>
              <p className="mt-0.5 truncate font-medium text-ink">{user?.email}</p>
            </div>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center rounded-[var(--radius-card)] border border-navy-100 bg-white p-12">
              <Loader2 className="h-5 w-5 animate-spin text-navy-700" />
            </div>
          ) : !editing && report ? (
            <div className="space-y-4 rounded-[var(--radius-card)] border border-navy-100 bg-white p-6 shadow-[var(--shadow-card)]">
              <div className="flex items-center justify-between">
                <p className="text-sm font-semibold text-ink">Laporan hari ini sudah terkirim</p>
                <button
                  onClick={() => setEditing(true)}
                  className="flex items-center gap-1.5 rounded border border-navy-100 bg-white px-2.5 py-1.5 text-2xs font-semibold text-ink-muted hover:bg-navy-50"
                >
                  <Pencil className="h-3 w-3" /> Edit
                </button>
              </div>
              <div className="overflow-hidden rounded-[var(--radius-control)] border border-navy-100">
                <table className="w-full text-sm">
                  <thead className="bg-navy-50 text-2xs uppercase tracking-wide text-ink-faint">
                    <tr>
                      <th className="px-3 py-2 text-left">No</th>
                      <th className="px-3 py-2 text-left">Pekerjaan</th>
                      <th className="px-3 py-2 text-left">Waktu</th>
                      <th className="px-3 py-2 text-left">Lampiran</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((r, i) => (
                      <tr key={r._key} className="border-t border-navy-50">
                        <td className="px-3 py-2 text-ink-faint">{i + 1}</td>
                        <td className="px-3 py-2 text-ink">{r.description}</td>
                        <td className="px-3 py-2 text-ink-muted">{r.time_note || "-"}</td>
                        <td className="px-3 py-2">
                          {r.attachment_url ? (
                            <a href={r.attachment_url} target="_blank" rel="noreferrer" className="flex items-center gap-1 text-navy-700 hover:underline">
                              <Paperclip className="h-3 w-3" /> {r.attachment_name || "Lihat"}
                            </a>
                          ) : (
                            <span className="text-ink-faint">-</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="space-y-4 rounded-[var(--radius-card)] border border-navy-100 bg-white p-6 shadow-[var(--shadow-card)]">
              <div className="space-y-3">
                {rows.map((r, i) => (
                  <div key={r._key} className="flex items-start gap-2 rounded-[var(--radius-control)] border border-navy-50 bg-navy-50/30 p-3">
                    <span className="mt-2 shrink-0 text-2xs font-semibold text-ink-faint">{i + 1}</span>
                    <div className="flex-1 space-y-2">
                      <textarea
                        value={r.description}
                        onChange={(e) => updateRow(r._key, { description: e.target.value })}
                        placeholder="Deskripsi pekerjaan..."
                        rows={2}
                        className="w-full rounded-[var(--radius-control)] border border-navy-100 bg-white px-3 py-2 text-sm text-ink placeholder:text-ink-faint focus:border-navy-400"
                      />
                      <div className="flex flex-wrap items-center gap-2">
                        <input
                          value={r.time_note}
                          onChange={(e) => updateRow(r._key, { time_note: e.target.value })}
                          placeholder="Waktu (opsional), mis. 09:00-11:00"
                          className="w-48 rounded border border-navy-100 bg-white px-2.5 py-1.5 text-xs text-ink placeholder:text-ink-faint"
                        />
                        <label className="flex cursor-pointer items-center gap-1.5 rounded border border-navy-100 bg-white px-2.5 py-1.5 text-2xs font-medium text-ink-muted hover:bg-navy-50">
                          <Paperclip className="h-3 w-3" />
                          {r.uploading ? "Mengunggah..." : r.attachment_name ? r.attachment_name : "Lampiran (opsional)"}
                          <input
                            type="file"
                            className="hidden"
                            disabled={r.uploading}
                            onChange={(e) => handleAttachmentChange(r, e.target.files?.[0] || null)}
                          />
                        </label>
                        {r.attachment_url && !r.uploading && (
                          <button onClick={() => updateRow(r._key, { attachment_url: undefined, attachment_kind: undefined, attachment_name: undefined })} className="text-ink-faint hover:text-red-600">
                            <X className="h-3.5 w-3.5" />
                          </button>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={() => removeRow(r._key)}
                      disabled={rows.length === 1}
                      className="mt-2 shrink-0 rounded p-1.5 text-ink-faint hover:bg-red-50 hover:text-red-600 disabled:opacity-30"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                ))}
              </div>

              <button
                onClick={addRow}
                className="flex w-full items-center justify-center gap-2 rounded-[var(--radius-control)] border-2 border-dashed border-navy-100 py-2.5 text-xs font-medium text-ink-muted hover:border-navy-300 hover:bg-navy-50"
              >
                <Plus className="h-3.5 w-3.5" /> Tambah Baris
              </button>

              {errorMsg && (
                <p className="rounded-[var(--radius-control)] bg-red-50 px-3 py-2 text-xs font-medium text-red-700">{errorMsg}</p>
              )}

              <div className="flex items-center justify-end gap-2 border-t border-navy-50 pt-4">
                {report && (
                  <button onClick={() => { setEditing(false); load(); }} className="rounded border border-navy-100 px-3 py-2 text-xs font-medium text-ink-muted hover:bg-navy-50">
                    Batal
                  </button>
                )}
                <button
                  onClick={handleSubmit}
                  disabled={isSubmitting}
                  className="flex items-center gap-2 rounded-[var(--radius-control)] bg-navy-900 px-5 py-2.5 text-sm font-semibold text-white hover:bg-navy-800 disabled:opacity-50"
                >
                  {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                  {isSubmitting ? "Mengirim..." : "Kirim Laporan"}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
