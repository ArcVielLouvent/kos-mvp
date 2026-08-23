"use client";
import { useState, useEffect } from "react";
import {
  Folder, Home, Download, Eye, Upload, Plus, Video, Trash2, Pencil, Move,
  ChevronLeft, ChevronRight, ArrowLeft, ChevronRight as Chevron, FolderOpen,
  X, CheckSquare, Square,
} from "lucide-react";
import { DocumentBadge } from "@/components/DocumentBadge";
import { FolderTreePicker } from "@/components/FolderTreePicker";
import { FilePreviewModal } from "@/components/FilePreviewModal";
import { apiFetch, apiJson } from "@/lib/api";

const PAGE_SIZE = 20;

function parentOf(path: string): string {
  const parts = path.split("/").filter(Boolean);
  if (parts.length <= 1) return "/";
  return "/" + parts.slice(0, -1).join("/") + "/";
}

export function FileManagerBody({ initialPath = "/" }: { initialPath?: string }) {
  const [currentPath, setCurrentPath] = useState(initialPath);
  const [data, setData] = useState<{ folders: any[]; files: any[]; total: number; writable: boolean }>({
    folders: [],
    files: [],
    total: 0,
    writable: false,
  });
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [actionMsg, setActionMsg] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadKey, setUploadKey] = useState(0);

  const [folderName, setFolderName] = useState("");
  const [showNewFolder, setShowNewFolder] = useState(false);
  const [ytTitle, setYtTitle] = useState("");
  const [ytUrl, setYtUrl] = useState("");
  const [ytDesc, setYtDesc] = useState("");
  const [showYoutube, setShowYoutube] = useState(false);

  const [selectedFolders, setSelectedFolders] = useState<Set<string>>(new Set());
  const [selectedDocs, setSelectedDocs] = useState<Set<string>>(new Set());
  const [previewFile, setPreviewFile] = useState<{ title: string; file_url: string } | null>(null);
  const [showMoveModal, setShowMoveModal] = useState(false);
  const [moveDestination, setMoveDestination] = useState("/");

  const loadFiles = async () => {
    setIsLoading(true);
    try {
      const result = await apiJson(
        `/api/files?path=${encodeURIComponent(currentPath)}&page=${page}&page_size=${PAGE_SIZE}`
      );
      setData(result);
      setActionMsg("");
    } catch (e: any) {
      setActionMsg(`Gagal memuat file: ${e.message || "tidak diketahui"}`);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadFiles();
  }, [currentPath, page]);

  useEffect(() => {
    setSelectedFolders(new Set());
    setSelectedDocs(new Set());
    setPage(1);
  }, [currentPath]);

  const handleCreateFolder = async () => {
    if (!folderName.trim()) return;
    setIsProcessing(true);
    try {
      const result = await apiJson("/api/folders", {
        method: "POST",
        body: JSON.stringify({ folder_name: folderName, current_path: currentPath }),
      });
      setActionMsg(result.message);
      setFolderName("");
      setShowNewFolder(false);
      loadFiles();
    } catch (e: any) {
      setActionMsg(e.message || "Gagal membuat folder.");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = e.target.files;
    if (!selectedFiles || selectedFiles.length === 0) return;
    const filesArray = Array.from(selectedFiles);
    setIsProcessing(true);

    let successCount = 0;
    const allErrors: string[] = [];

    for (let i = 0; i < filesArray.length; i++) {
      const f = filesArray[i];
      setActionMsg(`Memproses ${i + 1} dari ${filesArray.length}: ${f.name}...`);
      const formData = new FormData();
      formData.append("files", f);
      formData.append("folder_path", currentPath);
      try {
        const res = await apiFetch("/api/upload", { method: "POST", body: formData });
        const result = await res.json();
        successCount += result.successCount || 0;
        if (result.errors && result.errors.length > 0) allErrors.push(...result.errors);
      } catch {
        allErrors.push(`${f.name}: request gagal atau timeout.`);
      }
    }

    const summary = `${successCount} dari ${filesArray.length} file berhasil diunggah.`;
    setActionMsg(allErrors.length > 0 ? `${summary}\n${allErrors.join("\n")}` : summary);
    loadFiles();
    setIsProcessing(false);
    setUploadKey((k) => k + 1);
  };

  const handleAddYouTube = async () => {
    if (!ytTitle.trim() || !ytUrl.trim()) return;
    setIsProcessing(true);
    setActionMsg("AI sedang mengekstrak deskripsi video...");
    try {
      const result = await apiJson("/api/youtube", {
        method: "POST",
        body: JSON.stringify({ title: ytTitle, url: ytUrl, description: ytDesc, current_path: currentPath }),
      });
      setActionMsg(result.message);
      setYtTitle("");
      setYtUrl("");
      setYtDesc("");
      setShowYoutube(false);
      loadFiles();
    } catch (e: any) {
      setActionMsg(e.message || "Gagal memproses video YouTube.");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDeleteFolder = async (path: string) => {
    if (!confirm(`Hapus folder "${path}" beserta seluruh isinya secara permanen?`)) return;
    try {
      const result = await apiJson(`/api/folders?path=${encodeURIComponent(path)}`, { method: "DELETE" });
      setActionMsg(result.message);
      loadFiles();
    } catch (e: any) {
      setActionMsg(e.message || "Gagal menghapus folder.");
    }
  };

  const handleDeleteDoc = async (docId: string) => {
    if (!confirm("Hapus dokumen ini secara permanen?")) return;
    try {
      const result = await apiJson(`/api/documents?doc_id=${docId}`, { method: "DELETE" });
      setActionMsg(result.message);
      loadFiles();
    } catch (e: any) {
      setActionMsg(e.message || "Gagal menghapus dokumen.");
    }
  };

  const handleBulkDelete = async () => {
    const total = selectedFolders.size + selectedDocs.size;
    if (total === 0) return;
    if (!confirm(`Hapus ${total} item terpilih secara permanen?`)) return;
    try {
      const result = await apiJson("/api/documents/bulk-delete", {
        method: "POST",
        body: JSON.stringify({ folders: Array.from(selectedFolders), docs: Array.from(selectedDocs) }),
      });
      setActionMsg(result.message);
      setSelectedFolders(new Set());
      setSelectedDocs(new Set());
      loadFiles();
    } catch (e: any) {
      setActionMsg(e.message || "Gagal menghapus item terpilih.");
    }
  };

  const handleRenameFolder = async (path: string, currentName: string) => {
    const newName = prompt("Nama folder baru:", currentName);
    if (!newName || !newName.trim() || newName.trim() === currentName) return;
    try {
      const result = await apiJson("/api/folders/rename", {
        method: "PATCH",
        body: JSON.stringify({ old_path: path, new_name: newName.trim() }),
      });
      setActionMsg(result.message);
      loadFiles();
    } catch (e: any) {
      setActionMsg(e.message || "Gagal mengganti nama folder.");
    }
  };

  const handleMoveDoc = (docId: string) => {
    // Sama kayak bulk move -- pakai modal FolderTreePicker, bukan prompt()
    // teks manual. "Pindahkan 1 file" ini teknisnya bulk-move dengan isi 1 doc.
    setSelectedFolders(new Set());
    setSelectedDocs(new Set([docId]));
    setMoveDestination(currentPath);
    setShowMoveModal(true);
  };

  const toggleFolder = (path: string) => {
    setSelectedFolders((prev) => {
      const next = new Set(prev);
      next.has(path) ? next.delete(path) : next.add(path);
      return next;
    });
  };

  const toggleDoc = (id: string) => {
    setSelectedDocs((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const allSelected =
    (data.folders.length > 0 || data.files.length > 0) &&
    data.folders.every((f: any) => selectedFolders.has(f.path)) &&
    data.files.every((f: any) => selectedDocs.has(f.id));

  const toggleSelectAll = () => {
    if (allSelected) {
      setSelectedFolders(new Set());
      setSelectedDocs(new Set());
    } else {
      setSelectedFolders(new Set(data.folders.map((f: any) => f.path)));
      setSelectedDocs(new Set(data.files.map((f: any) => f.id)));
    }
  };

  const handleBulkMove = async () => {
    const total = selectedFolders.size + selectedDocs.size;
    if (total === 0) return;
    setIsProcessing(true);
    try {
      const result = await apiJson("/api/documents/bulk-move", {
        method: "POST",
        body: JSON.stringify({
          folders: Array.from(selectedFolders),
          docs: Array.from(selectedDocs),
          destination: moveDestination,
        }),
      });
      setActionMsg(result.message);
      setSelectedFolders(new Set());
      setSelectedDocs(new Set());
      setShowMoveModal(false);
      loadFiles();
    } catch (e: any) {
      setActionMsg(e.message || "Gagal memindahkan item terpilih.");
    } finally {
      setIsProcessing(false);
    }
  };

  const totalSelected = selectedFolders.size + selectedDocs.size;
  const totalPages = Math.max(1, Math.ceil((data.total || 0) / PAGE_SIZE));
  const crumbs = currentPath.split("/").filter(Boolean);

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-2 rounded-[var(--radius-card)] border border-navy-100 bg-white px-4 py-3 shadow-2xs">
        <button
          onClick={() => setCurrentPath(parentOf(currentPath))}
          disabled={currentPath === "/"}
          title="Kembali ke folder sebelumnya"
          className="flex h-8 w-8 items-center justify-center rounded-full text-ink-muted hover:bg-navy-50 disabled:opacity-30 disabled:hover:bg-transparent"
        >
          <ArrowLeft className="h-4 w-4" />
        </button>
        <div className="h-5 w-px bg-navy-100" />
        <button
          onClick={() => setCurrentPath("/")}
          className="flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold text-navy-900 hover:bg-navy-50"
        >
          <Home className="h-3.5 w-3.5" /> Drive
        </button>
        {crumbs.map((part, i) => {
          const accum = "/" + crumbs.slice(0, i + 1).join("/") + "/";
          const isLast = i === crumbs.length - 1;
          return (
            <div key={accum} className="flex items-center gap-2">
              <Chevron className="h-3.5 w-3.5 text-ink-faint" />
              <button
                onClick={() => setCurrentPath(accum)}
                className={`rounded-full px-2.5 py-1 text-xs font-medium hover:bg-navy-50 ${
                  isLast ? "text-navy-900 font-semibold" : "text-ink-muted"
                }`}
              >
                {part}
              </button>
            </div>
          );
        })}
        <span className="ml-auto flex items-center gap-1.5 rounded-full bg-navy-50 px-3 py-1 font-mono-data text-2xs text-ink-muted">
          <FolderOpen className="h-3 w-3" /> {currentPath}
        </span>
      </div>

      {data.writable && (
        <div className="flex flex-wrap items-center gap-2">
          {showNewFolder ? (
            <div className="flex items-center gap-1.5 rounded-[var(--radius-control)] border border-navy-200 bg-white px-1 py-1 shadow-2xs">
              <input
                autoFocus
                type="text"
                placeholder="Nama folder baru..."
                value={folderName}
                onChange={(e) => setFolderName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleCreateFolder();
                  if (e.key === "Escape") { setShowNewFolder(false); setFolderName(""); }
                }}
                className="px-2 py-1.5 text-xs focus:outline-none w-40"
              />
              <button onClick={handleCreateFolder} className="rounded bg-navy-900 px-3 py-1.5 text-2xs font-semibold text-white hover:bg-navy-800">
                Buat
              </button>
              <button onClick={() => { setShowNewFolder(false); setFolderName(""); }} className="px-2 py-1.5 text-2xs text-ink-faint hover:text-ink">
                Batal
              </button>
            </div>
          ) : (
            <button
              onClick={() => setShowNewFolder(true)}
              className="flex items-center gap-1.5 rounded-[var(--radius-control)] border border-navy-100 bg-white px-3 py-2 text-xs font-medium text-ink hover:bg-navy-50"
            >
              <Plus className="h-3.5 w-3.5" /> Folder Baru
            </button>
          )}

          {showYoutube ? (
            <div className="flex items-center gap-1.5 rounded-[var(--radius-control)] border border-navy-200 bg-white px-1 py-1 shadow-2xs">
              <input type="text" placeholder="Judul video..." value={ytTitle} onChange={(e) => setYtTitle(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleAddYouTube()} className="px-2 py-1.5 text-xs focus:outline-none w-28" />
              <input type="text" placeholder="Link YouTube..." value={ytUrl} onChange={(e) => setYtUrl(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleAddYouTube()} className="px-2 py-1.5 text-xs focus:outline-none w-32" />
              <button onClick={handleAddYouTube} className="rounded bg-navy-900 px-3 py-1.5 text-2xs font-semibold text-white hover:bg-navy-800">Tambah</button>
              <button onClick={() => { setShowYoutube(false); setYtTitle(""); setYtUrl(""); setYtDesc(""); }} className="px-2 py-1.5 text-2xs text-ink-faint hover:text-ink">Batal</button>
            </div>
          ) : (
            <button onClick={() => setShowYoutube(true)} className="flex items-center gap-1.5 rounded-[var(--radius-control)] border border-navy-100 bg-white px-3 py-2 text-xs font-medium text-ink hover:bg-navy-50">
              <Video className="h-3.5 w-3.5" /> Video YouTube
            </button>
          )}

          <label className="ml-auto flex cursor-pointer items-center gap-1.5 rounded-[var(--radius-control)] bg-navy-900 px-4 py-2 text-xs font-semibold text-white hover:bg-navy-800">
            <Upload className="h-3.5 w-3.5" />
            Unggah Berkas
            <input key={uploadKey} type="file" multiple onChange={handleFileUpload} disabled={isProcessing} className="hidden" />
          </label>
        </div>
      )}

      {actionMsg && (
        <div className="whitespace-pre-line rounded-[var(--radius-control)] border border-navy-100 bg-navy-50 px-4 py-2.5 text-xs font-medium text-navy-900">
          {actionMsg}
        </div>
      )}

      {data.writable && (data.folders.length > 0 || data.files.length > 0) && (
        <div className="flex items-center justify-between gap-4">
          <button
            onClick={toggleSelectAll}
            className="flex items-center gap-1.5 rounded-[var(--radius-control)] border border-navy-100 bg-white px-3 py-1.5 text-2xs font-semibold text-ink-muted hover:bg-navy-50"
          >
            {allSelected ? <CheckSquare className="h-3.5 w-3.5 text-navy-900" /> : <Square className="h-3.5 w-3.5" />}
            {allSelected ? "Batalkan Semua" : "Pilih Semua"}
          </button>

          {totalSelected > 0 && (
            <div className="flex flex-1 items-center justify-between gap-4 rounded-[var(--radius-card)] border border-navy-200 bg-navy-50 p-3">
              <span className="text-xs font-semibold text-navy-900">{totalSelected} item terpilih</span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => { setMoveDestination(currentPath); setShowMoveModal(true); }}
                  className="flex items-center gap-1.5 rounded bg-navy-900 px-3 py-1.5 text-2xs font-bold text-white hover:bg-navy-800"
                >
                  <Move className="h-3.5 w-3.5" /> Pindahkan Terpilih
                </button>
                <button onClick={handleBulkDelete} className="flex items-center gap-1.5 rounded bg-red-600 px-3 py-1.5 text-2xs font-bold text-white hover:bg-red-700">
                  <Trash2 className="h-3.5 w-3.5" /> Hapus Terpilih
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {showMoveModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={() => setShowMoveModal(false)}>
          <div className="w-full max-w-md space-y-3 rounded-[var(--radius-card)] bg-white p-5 shadow-xl" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-ink">Pindahkan {totalSelected} item ke...</h3>
              <button onClick={() => setShowMoveModal(false)} className="rounded-full p-1 text-ink-muted hover:bg-navy-50">
                <X className="h-4 w-4" />
              </button>
            </div>
            <FolderTreePicker value={moveDestination} onChange={setMoveDestination} />
            <div className="flex justify-end gap-2 pt-1">
              <button onClick={() => setShowMoveModal(false)} className="rounded border border-navy-100 px-3 py-1.5 text-xs font-medium text-ink-muted hover:bg-navy-50">
                Batal
              </button>
              <button
                onClick={handleBulkMove}
                disabled={isProcessing}
                className="rounded bg-navy-900 px-4 py-1.5 text-xs font-semibold text-white hover:bg-navy-800 disabled:opacity-50"
              >
                Pindahkan ke sini
              </button>
            </div>
          </div>
        </div>
      )}

      {previewFile && <FilePreviewModal file={previewFile} onClose={() => setPreviewFile(null)} />}

      {isLoading ? (
        <p className="animate-pulse text-sm text-ink-muted">Menyinkronkan data cloud...</p>
      ) : (
        <div className="space-y-5">
          {data.folders.length > 0 && (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
              {data.folders.map((f: any) => (
                <div
                  key={f.path}
                  onClick={() => setCurrentPath(f.path)}
                  className="group relative flex flex-col gap-3 rounded-[var(--radius-card)] border border-navy-100 bg-white p-4 shadow-2xs transition-all hover:-translate-y-0.5 hover:border-navy-300 hover:shadow-[var(--shadow-card)] cursor-pointer"
                >
                  <div className="flex items-start justify-between">
                    <span className="flex h-10 w-10 items-center justify-center rounded-[var(--radius-control)] bg-amber-50 text-amber-500">
                      <Folder className="h-5 w-5" fill="currentColor" strokeWidth={1} />
                    </span>
                    {data.writable && (
                      <input
                        type="checkbox"
                        checked={selectedFolders.has(f.path)}
                        onClick={(e) => e.stopPropagation()}
                        onChange={() => toggleFolder(f.path)}
                        className="mt-1 h-3.5 w-3.5 rounded border-navy-300 accent-navy-900"
                      />
                    )}
                  </div>
                  <span className="truncate text-sm font-medium text-ink group-hover:text-navy-900">{f.name}</span>
                  {data.writable && (
                    <div className="absolute bottom-3 right-3 flex gap-1 opacity-0 transition-opacity group-hover:opacity-100" onClick={(e) => e.stopPropagation()}>
                      <button onClick={() => handleRenameFolder(f.path, f.name)} className="rounded bg-white p-1 text-ink-muted shadow-sm hover:text-navy-900" title="Ubah Nama">
                        <Pencil className="h-3.5 w-3.5" />
                      </button>
                      <button onClick={() => handleDeleteFolder(f.path)} className="rounded bg-white p-1 text-ink-muted shadow-sm hover:text-red-600" title="Hapus">
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          <div className="overflow-hidden rounded-[var(--radius-card)] border border-navy-100 bg-white">
            {data.files.length === 0 ? (
              <p className="p-10 text-center text-xs text-ink-faint">Folder ini kosong atau belum memiliki dokumen.</p>
            ) : (
              <>
                <div className="hidden border-b border-navy-100 bg-navy-50/50 px-4 py-2 text-2xs font-semibold uppercase tracking-wide text-ink-faint sm:grid sm:grid-cols-[1fr_120px_160px]">
                  <span>Nama</span>
                  <span>Tanggal</span>
                  <span className="text-right">Aksi</span>
                </div>
                {data.files.map((f: any) => (
                  <div key={f.id} className="group flex items-center justify-between gap-3 border-b border-navy-50 px-4 py-3 last:border-0 hover:bg-navy-50/60 sm:grid sm:grid-cols-[1fr_120px_160px]">
                    <div className="flex min-w-0 items-center gap-3">
                      {data.writable && (
                        <input type="checkbox" checked={selectedDocs.has(f.id)} onChange={() => toggleDoc(f.id)} className="h-3.5 w-3.5 shrink-0 rounded border-navy-300 accent-navy-900" />
                      )}
                      <DocumentBadge type={f.metadata?.tipe_file || "default"} size="sm" />
                      <span className="truncate text-sm font-medium text-ink">{f.title}</span>
                    </div>
                    <span className="hidden text-xs text-ink-faint sm:block">{(f.created_at || "").slice(0, 10)}</span>
                    <div className="flex items-center justify-end gap-1.5">
                      {f.file_url && (
                        <>
                          <button onClick={() => setPreviewFile({ title: f.title, file_url: f.file_url })} className="flex items-center gap-1 rounded border border-navy-100 bg-white px-2.5 py-1 text-2xs font-semibold text-ink-muted hover:bg-navy-50">
                            <Eye className="h-3 w-3" /> Lihat
                          </button>
                          <a href={f.file_url} download={f.title} className="flex items-center gap-1 rounded border border-navy-100 bg-white px-2.5 py-1 text-2xs font-semibold text-ink-muted hover:bg-navy-50">
                            <Download className="h-3 w-3" /> Unduh
                          </a>
                        </>
                      )}
                      {data.writable && (
                        <div className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                          <button onClick={() => handleMoveDoc(f.id)} className="p-1 text-ink-muted hover:text-navy-700" title="Pindahkan">
                            <Move className="h-3.5 w-3.5" />
                          </button>
                          <button onClick={() => handleDeleteDoc(f.id)} className="p-1 text-ink-muted hover:text-red-600" title="Hapus">
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </>
            )}
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-4 pt-2">
              <button disabled={page <= 1} onClick={() => setPage((p) => Math.max(1, p - 1))} className="flex items-center gap-1 rounded border px-3 py-1.5 text-xs font-medium text-ink-muted bg-white disabled:opacity-40 hover:bg-navy-50">
                <ChevronLeft className="h-3.5 w-3.5" /> Sebelumnya
              </button>
              <span className="text-xs font-medium text-ink-faint">
                Halaman {page} dari {totalPages} <span className="opacity-60">({data.total} file total)</span>
              </span>
              <button disabled={page >= totalPages} onClick={() => setPage((p) => Math.min(totalPages, p + 1))} className="flex items-center gap-1 rounded border px-3 py-1.5 text-xs font-medium text-ink-muted bg-white disabled:opacity-40 hover:bg-navy-50">
                Berikutnya <ChevronRight className="h-3.5 w-3.5" />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
