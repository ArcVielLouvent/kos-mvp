"use client";
import { Download, X } from "lucide-react";

const OFFICE_EXTS = new Set(["doc", "docx", "ppt", "pptx", "xls", "xlsx"]);
const IMAGE_EXTS = new Set(["jpg", "jpeg", "png", "webp", "gif", "bmp"]);
const VIDEO_EXTS = new Set(["mp4", "mov", "webm", "avi", "mkv", "3gp"]);
const AUDIO_EXTS = new Set(["mp3", "wav", "aac", "ogg", "flac", "aiff"]);

function extOf(name: string): string {
  return (name.split(".").pop() || "").toLowerCase();
}

export interface PreviewableFile {
  title: string;
  file_url: string;
}

/** Modal preview file langsung di dalam KOS -- dipakai di File Manager
 * maupun di Chat (klik sumber dokumen), tidak perlu buka tab baru atau
 * unduh dulu untuk sekadar melihat isinya. Gambar/PDF/audio/video di-embed
 * langsung; dokumen Office (docx/pptx/xlsx) dilewatkan ke Microsoft Office
 * Online Viewer (butuh URL file publicly-accessible). Format yang tidak
 * didukung browser tetap dikasih tombol buka/unduh sebagai fallback. */
export function FilePreviewModal({ file, onClose }: { file: PreviewableFile; onClose: () => void }) {
  const ext = extOf(file.title);
  const isImage = IMAGE_EXTS.has(ext);
  const isPdf = ext === "pdf";
  const isVideo = VIDEO_EXTS.has(ext);
  const isAudio = AUDIO_EXTS.has(ext);
  const isOffice = OFFICE_EXTS.has(ext);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={onClose}>
      <div
        className="flex max-h-[90vh] w-full max-w-4xl flex-col overflow-hidden rounded-[var(--radius-card)] bg-white shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-navy-100 px-4 py-3">
          <span className="truncate text-sm font-semibold text-ink">{file.title}</span>
          <div className="flex items-center gap-2">
            <a href={file.file_url} download={file.title} className="flex items-center gap-1 rounded border border-navy-100 bg-white px-2.5 py-1 text-2xs font-semibold text-ink-muted hover:bg-navy-50">
              <Download className="h-3 w-3" /> Unduh
            </a>
            <button onClick={onClose} className="rounded-full p-1.5 text-ink-muted hover:bg-navy-50 hover:text-ink">
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
        <div className="flex-1 overflow-auto bg-navy-50/40 p-2">
          {isImage ? (
            <img src={file.file_url} alt={file.title} className="mx-auto max-h-[75vh] rounded object-contain" />
          ) : isPdf ? (
            <iframe src={file.file_url} title={file.title} className="h-[75vh] w-full rounded border-0" />
          ) : isVideo ? (
            <video src={file.file_url} controls className="mx-auto max-h-[75vh] w-full rounded" />
          ) : isAudio ? (
            <div className="flex h-40 items-center justify-center">
              <audio src={file.file_url} controls className="w-full max-w-md" />
            </div>
          ) : isOffice ? (
            <iframe
              src={`https://view.officeapps.live.com/op/embed.aspx?src=${encodeURIComponent(file.file_url)}`}
              title={file.title}
              className="h-[75vh] w-full rounded border-0 bg-white"
            />
          ) : (
            <div className="flex h-40 flex-col items-center justify-center gap-2 text-center">
              <p className="text-xs text-ink-faint">Format file ini belum bisa ditampilkan langsung di dalam KOS.</p>
              <a href={file.file_url} target="_blank" rel="noreferrer" className="text-xs font-semibold text-navy-700 underline">
                Buka di tab baru
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
