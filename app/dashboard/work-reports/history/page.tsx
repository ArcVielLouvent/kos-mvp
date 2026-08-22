"use client";
import { useState, useEffect } from "react";
import { ArrowLeft, Paperclip, Loader2, Image as ImageIcon, FileText, Video, Music } from "lucide-react";
import Link from "next/link";
import { TopBar } from "@/components/TopBar";
import { FilePreviewModal } from "@/components/FilePreviewModal";
import { apiJson } from "@/lib/api";

const KIND_ICON: Record<string, any> = {
  image: ImageIcon,
  video: Video,
  audio: Music,
  document: FileText,
};

export default function WorkReportHistoryPage() {
  const [reports, setReports] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [previewFile, setPreviewFile] = useState<{ title: string; file_url: string } | null>(null);

  useEffect(() => {
    apiJson("/api/work-reports/history")
      .then((data) => setReports(data.reports || []))
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <div>
      <TopBar
        title="Riwayat Laporan Saya"
        description="Semua laporan kerjaan yang pernah kamu kirim."
        action={
          <Link href="/dashboard/work-reports" className="flex items-center gap-2 rounded-[var(--radius-control)] border border-navy-100 bg-white px-3 py-2 text-xs font-semibold text-ink-muted hover:bg-navy-50">
            <ArrowLeft className="h-3.5 w-3.5" /> Kembali
          </Link>
        }
      />
      <div className="p-8">
        <div className="mx-auto max-w-3xl space-y-4">
          {isLoading ? (
            <div className="flex items-center justify-center rounded-[var(--radius-card)] border border-navy-100 bg-white p-12">
              <Loader2 className="h-5 w-5 animate-spin text-navy-700" />
            </div>
          ) : reports.length === 0 ? (
            <p className="rounded-[var(--radius-card)] border border-navy-100 bg-white p-8 text-center text-sm text-ink-faint">
              Belum ada laporan yang dikirim.
            </p>
          ) : (
            reports.map((r) => (
              <div key={r.id} className="rounded-[var(--radius-card)] border border-navy-100 bg-white p-5 shadow-[var(--shadow-card)]">
                <p className="mb-3 text-sm font-semibold text-ink">
                  {new Date(r.report_date).toLocaleDateString("id-ID", { weekday: "long", day: "numeric", month: "long", year: "numeric" })}
                </p>
                <div className="space-y-2">
                  {(r.rows || []).map((row: any) => {
                    const Icon = row.attachment_kind ? KIND_ICON[row.attachment_kind] || Paperclip : null;
                    return (
                      <div key={row.id} className="flex items-start justify-between gap-3 rounded-[var(--radius-control)] bg-navy-50/50 px-3 py-2">
                        <div className="min-w-0 flex-1">
                          <p className="text-sm text-ink">{row.description}</p>
                          {row.time_note && <p className="mt-0.5 text-2xs text-ink-faint">{row.time_note}</p>}
                        </div>
                        {row.attachment_url && Icon && (
                          <button
                            onClick={() => setPreviewFile({ title: row.attachment_url.split("/").pop()?.split("?")[0] || "Lampiran", file_url: row.attachment_url })}
                            className="flex shrink-0 items-center gap-1 rounded border border-navy-100 bg-white px-2 py-1 text-2xs font-semibold text-navy-900 hover:bg-navy-100"
                          >
                            <Icon className="h-3 w-3" /> Lihat
                          </button>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
      {previewFile && <FilePreviewModal file={previewFile} onClose={() => setPreviewFile(null)} />}
    </div>
  );
}
