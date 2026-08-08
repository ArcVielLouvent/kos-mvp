"use client";
import { useState, useEffect } from "react";
import { Folder, Home, Download, Upload, Loader2, Plus, Video, Trash2, Pencil, Move, ChevronLeft, ChevronRight } from "lucide-react";
import { TopBar } from "@/components/TopBar";
import { DocumentBadge } from "@/components/DocumentBadge";
import { apiFetch, apiJson } from "@/lib/api";

const PAGE_SIZE = 20;

export default function FileManagerPage() {
  const [currentPath, setCurrentPath] = useState("/");
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

  const [folderName, setFolderName] = useState("");
  const [ytTitle, setYtTitle] = useState("");
  const [ytUrl, setYtUrl] = useState("");
  const [ytDesc, setYtDesc] = useState("");

  const [selectedFolders, setSelectedFolders] = useState<Set<string>>(new Set());
  const [selectedDocs, setSelectedDocs] = useState<Set<string>>(new Set());

  const loadFiles = async () => {
    setIsLoading(true);
    console.log("[DEBUG] fetch path:", currentPath, "page:", page); // <-- tambahkan
    try {
      const result = await apiJson(
        `/api/files?path=${encodeURIComponent(currentPath)}&page=${page}&page_size=${PAGE_SIZE}`
      );
      console.log("[DEBUG] response:", result); // <-- tambahkan
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
    setIsProcessing(true);
    setActionMsg("AI sedang menyusun potongan berkas...");
    const formData = new FormData();
    Array.from(selectedFiles).forEach((f) => formData.append("files", f));
    formData.append("folder_path", currentPath);

    try {
      const res = await apiFetch("/api/upload", { method: "POST", body: formData });
      const result = await res.json();
      setActionMsg(result.message);
      loadFiles();
    } catch {
      setActionMsg("Gagal memproses unggah berkas.");
    } finally {
      setIsProcessing(false);
      e.target.value = "";
    }
  };

  const handleAddYouTube = async () => {
    if (!ytTitle.trim() || !ytUrl.trim()) return;
    setIsProcessing(true);
    setActionMsg("AI Gemini sedang mengekstrak deskripsi video...");
    try {
      const result = await apiJson("/api/youtube", {
        method: "POST",
        body: JSON.stringify({ title: ytTitle, url: ytUrl, description: ytDesc, current_path: currentPath }),
      });
      setActionMsg(result.message);
      setYtTitle("");
      setYtUrl("");
      setYtDesc("");
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

  const handleMoveDoc = async (docId: string) => {
    const newPath = prompt("Pindahkan dokumen ke folder (mis. /SOP/):", currentPath);
    if (!newPath) return;
    try {
      const result = await apiJson("/api/documents/move", {
        method: "PATCH",
        body: JSON.stringify({ doc_id: docId, new_path: newPath }),
      });
      setActionMsg(result.message);
      loadFiles();
    } catch (e: any) {
      setActionMsg(e.message || "Gagal memindahkan dokumen.");
    }
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

  const totalSelected = selectedFolders.size + selectedDocs.size;
  const totalPages = Math.max(1, Math.ceil((data.total || 0) / PAGE_SIZE));

  return (
    <div>
      <TopBar title="File Manager" description="Kelola dokumen & pangkalan data AI perusahaan." />
      <div className="p-8 space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <button onClick={() => setCurrentPath("/")} className="flex items-center gap-1.5 rounded-[var(--radius-control)] bg-navy-900 px-3 py-2 font-medium text-white text-xs">
            <Home className="h-4 w-4" /> Root Drive
          </button>

          {data.writable && (
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5 rounded border p-1 bg-white">
                <input type="text" placeholder="Nama folder..." value={folderName} onChange={(e) => setFolderName(e.target.value)} className="px-2 py-1 text-xs focus:outline-none w-28" />
                <button onClick={handleCreateFolder} className="p-1.5 bg-navy-50 rounded hover:bg-navy-100"><Plus className="h-3.5 w-3.5 text-navy-900" /></button>
              </div>

              <div className="flex items-center gap-1.5 rounded border p-1 bg-white">
                <input type="text" placeholder="Judul Video..." value={ytTitle} onChange={(e) => setYtTitle(e.target.value)} className="px-2 py-1 text-xs focus:outline-none w-24" />
                <input type="text" placeholder="Link YT..." value={ytUrl} onChange={(e) => setYtUrl(e.target.value)} className="px-2 py-1 text-xs focus:outline-none w-24" />
                <button onClick={handleAddYouTube} className="p-1.5 bg-navy-50 rounded hover:bg-navy-100"><Video className="h-3.5 w-3.5 text-navy-900" /></button>
              </div>

              <label className="flex items-center gap-1.5 rounded bg-navy-900 px-3 py-2 font-medium text-white cursor-pointer hover:bg-navy-800 text-xs">
                <Upload className="h-3.5 w-3.5" />
                <span>Unggah Berkas</span>
                <input type="file" multiple onChange={handleFileUpload} disabled={isProcessing} className="hidden" />
              </label>
            </div>
          )}
        </div>

        {actionMsg && (
          <div className="rounded bg-navy-50 p-3 text-xs font-medium text-navy-900 border border-navy-100 animate-fade-in">
            {actionMsg}
          </div>
        )}

        {data.writable && totalSelected > 0 && (
          <div className="flex items-center justify-between gap-4 rounded-[var(--radius-card)] border border-red-100 bg-red-50 p-3 shadow-2xs animate-fade-in">
            <span className="text-xs font-semibold text-red-700">{totalSelected} item terpilih untuk dihapus</span>
            <button
              onClick={handleBulkDelete}
              className="flex items-center gap-1.5 rounded bg-red-600 px-3 py-1.5 text-2xs font-bold text-white hover:bg-red-700 shadow-sm"
            >
              <Trash2 className="h-3.5 w-3.5" /> Hapus Terpilih Secara Permanen
            </button>
          </div>
        )}

        {isLoading ? (
          <p className="animate-pulse text-sm text-ink-muted">Menyinkronkan data cloud...</p>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {data.folders?.map((f: any) => (
                <div
                  key={f.path}
                  onClick={() => {
                    console.log("[DEBUG] folder diklik:", f.path);
                    setCurrentPath(f.path);
                  }}
                  className="group flex items-center justify-between rounded-[var(--radius-card)] border border-navy-100 bg-white p-3 hover:bg-navy-50 shadow-sm transition-all cursor-pointer"
                >
                  {/* PENTING: stopPropagation cuma di checkbox itu sendiri,
                      bukan di wrapper yang juga isinya nama folder --
                      supaya klik nama folder tetap bubbling ke onClick di atas. */}
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    {data.writable && (
                      <input
                        type="checkbox"
                        checked={selectedFolders.has(f.path)}
                        onClick={(e) => e.stopPropagation()}
                        onChange={() => toggleFolder(f.path)}
                        className="rounded border-navy-300 accent-navy-900 cursor-pointer h-3.5 w-3.5 shrink-0"
                      />
                    )}

                    <div className="flex items-center gap-2 text-left flex-1 min-w-0 select-none">
                      <Folder className="h-4 w-4 text-navy-700 shrink-0 group-hover:text-navy-900" />
                      <span className="text-xs font-medium text-ink truncate group-hover:underline">{f.name}</span>
                    </div>
                  </div>

                  {data.writable && (
                    <div className="flex shrink-0 gap-1 opacity-0 group-hover:opacity-100 transition-opacity" onClick={(e) => e.stopPropagation()}>
                      <button onClick={() => handleRenameFolder(f.path, f.name)} className="p-1 text-ink-muted hover:text-navy-900" title="Ubah Nama"><Pencil className="h-3.5 w-3.5" /></button>
                      <button onClick={() => handleDeleteFolder(f.path)} className="p-1 text-ink-muted hover:text-red-600" title="Hapus Folder"><Trash2 className="h-3.5 w-3.5" /></button>
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div className="overflow-hidden rounded-[var(--radius-card)] border border-navy-100 bg-white shadow-xs">
              {data.files?.length === 0 ? (
                <p className="p-8 text-xs text-ink-faint text-center">Folder ini kosong atau belum memiliki dokumen.</p>
              ) : (
                data.files?.map((f: any) => (
                  <div key={f.id} className="group flex items-center justify-between border-b border-navy-100 px-4 py-2.5 hover:bg-navy-50 transition-all">
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      {data.writable && (
                        <input
                          type="checkbox"
                          checked={selectedDocs.has(f.id)}
                          onChange={() => toggleDoc(f.id)}
                          className="rounded border-navy-300 accent-navy-900 cursor-pointer h-3.5 w-3.5"
                        />
                      )}
                      <DocumentBadge type={f.metadata?.tipe_file || "default"} size="sm" />
                      <span className="text-xs font-medium text-ink truncate max-w-md">{f.title}</span>
                      <span className="text-2xs text-ink-faint font-mono hidden sm:inline-block">{(f.created_at || "").slice(0, 10)}</span>
                    </div>

                    <div className="flex items-center gap-2">
                      {f.file_url && (
                        <a
                          href={f.file_url}
                          target="_blank"
                          rel="noreferrer"
                          className="rounded border border-navy-100 bg-white px-2.5 py-1 text-2xs font-semibold text-ink-muted hover:bg-navy-50 flex items-center gap-1 shadow-2xs transition-colors"
                        >
                          <Download className="h-3 w-3" /> Unduh
                        </a>
                      )}
                      {data.writable && (
                        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button onClick={() => handleMoveDoc(f.id)} className="p-1 text-ink-muted hover:text-navy-700" title="Pindahkan Berkas"><Move className="h-3.5 w-3.5" /></button>
                          <button onClick={() => handleDeleteDoc(f.id)} className="p-1 text-ink-muted hover:text-red-600" title="Hapus Berkas"><Trash2 className="h-3.5 w-3.5" /></button>
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>

            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-4 pt-2">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="flex items-center gap-1 rounded border px-3 py-1.5 text-xs font-medium text-ink-muted bg-white disabled:opacity-40 hover:bg-navy-50 transition-all shadow-2xs"
                >
                  <ChevronLeft className="h-3.5 w-3.5" /> Sebelumnya
                </button>
                <span className="text-xs font-medium text-ink-faint">
                  Halaman {page} dari {totalPages} <span className="opacity-60">({data.total} file total)</span>
                </span>
                <button
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  className="flex items-center gap-1 rounded border px-3 py-1.5 text-xs font-medium text-ink-muted bg-white disabled:opacity-40 hover:bg-navy-50 transition-all shadow-2xs"
                >
                  Berikutnya <ChevronRight className="h-3.5 w-3.5" />
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}