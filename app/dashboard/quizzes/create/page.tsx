"use client";
import { useState } from "react";
import { ArrowLeft, Sparkles, Loader2, FileText, X, Info } from "lucide-react";
import Link from "next/link";
import { TopBar } from "@/components/TopBar";
import { DocumentPicker } from "@/components/DocumentPicker";
import { FolderTreePicker } from "@/components/FolderTreePicker";
import { apiJson } from "@/lib/api";
import { useRouter } from "next/navigation";

export default function CreateQuizPage() {
  const router = useRouter();
  const [selectedDocs, setSelectedDocs] = useState<Map<string, string>>(new Map()); // id -> title
  const [sourceFolder, setSourceFolder] = useState<string | null>(null);
  const [pickerPath, setPickerPath] = useState("/");
  const [title, setTitle] = useState("");
  const [visibilityFolder, setVisibilityFolder] = useState("/");
  const [numQuestions, setNumQuestions] = useState(5);
  const [passingScore, setPassingScore] = useState(70);
  const [isGenerating, setIsGenerating] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const toggleDoc = (doc: { id: string; title: string }) => {
    setSourceFolder(null); // pilih dokumen manual membatalkan mode "seluruh folder"
    setSelectedDocs((prev) => {
      const next = new Map(prev);
      next.has(doc.id) ? next.delete(doc.id) : next.set(doc.id, doc.title);
      return next;
    });
  };

  const useFolder = (folderPath: string) => {
    setSelectedDocs(new Map()); // mode folder membatalkan pilihan dokumen manual
    setSourceFolder(folderPath);
  };

  const handleGenerate = async () => {
    if (selectedDocs.size === 0 && !sourceFolder) {
      setErrorMsg("Pilih minimal 1 dokumen, atau pakai tombol \"Pakai semua isi folder ini\".");
      return;
    }
    setErrorMsg(null);
    setIsGenerating(true);
    try {
      const result = await apiJson("/api/quizzes/generate", {
        method: "POST",
        body: JSON.stringify({
          source_document_ids: sourceFolder ? [] : Array.from(selectedDocs.keys()),
          source_folder_path: sourceFolder,
          title: title.trim() || undefined,
          folder_path: visibilityFolder,
          num_questions: numQuestions,
          passing_score: passingScore,
        }),
      });
      if (result.scopeNote) {
        alert(result.scopeNote); // folder-nya lebih besar dari batas 15 dokumen -- kasih tahu sebelum pindah halaman
      }
      router.push("/dashboard/quizzes");
    } catch (e: any) {
      setErrorMsg(e.message || "Gagal generate kuis. Coba dokumen lain atau kurangi jumlah soal.");
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div>
      <TopBar
        title="Buat Kuis dari Dokumen"
        description="AI akan membuat soal pilihan ganda berdasarkan isi dokumen yang dipilih."
        action={
          <Link href="/dashboard/quizzes" className="flex items-center gap-2 rounded-[var(--radius-control)] border border-navy-100 bg-white px-3 py-2 text-xs font-semibold text-ink-muted hover:bg-navy-50">
            <ArrowLeft className="h-3.5 w-3.5" /> Kembali
          </Link>
        }
      />
      <div className="p-8">
        <div className="mx-auto max-w-2xl space-y-5">
          <div>
            <label className="mb-1.5 block text-xs font-semibold text-ink">
              1. Sumber Soal <span className="font-normal text-ink-faint">-- dari File Manager, dokumen mana yang mau dijadikan bahan soal</span>
            </label>
            <DocumentPicker
              mode="multi"
              selectedIds={new Set(selectedDocs.keys())}
              onToggle={toggleDoc}
              onUseFolder={useFolder}
              currentFolderPath={pickerPath}
              onNavigate={setPickerPath}
            />
            <div className="mt-2 space-y-1">
              {sourceFolder ? (
                <p className="flex items-center gap-1.5 text-xs font-medium text-navy-700">
                  <FileText className="h-3.5 w-3.5" /> Memakai SEMUA dokumen di folder <span className="font-mono-data">{sourceFolder}</span> (maks. 15 dokumen)
                </p>
              ) : selectedDocs.size > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {Array.from(selectedDocs.entries()).map(([id, docTitle]) => (
                    <span key={id} className="flex items-center gap-1 rounded-full bg-navy-50 px-2.5 py-1 text-2xs font-medium text-navy-900">
                      {docTitle}
                      <button onClick={() => toggleDoc({ id, title: docTitle })} className="text-navy-400 hover:text-navy-900">
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-2xs text-ink-faint">Belum ada dokumen dipilih. Centang dokumen satu-satu, atau klik "Pakai semua isi folder ini" di pojok kanan atas kotak folder.</p>
              )}
            </div>
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-semibold text-ink">
              2. Siapa yang Bisa Lihat Kuis Ini <span className="font-normal text-ink-faint">-- BEDA dari sumber soal di atas, ini folder akses buat karyawan yang boleh mengerjakan kuisnya</span>
            </label>
            <FolderTreePicker value={visibilityFolder} onChange={setVisibilityFolder} />
          </div>

          <div className="rounded-[var(--radius-control)] bg-navy-50/60 p-3">
            <p className="flex items-start gap-2 text-2xs text-ink-muted">
              <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-navy-700" />
              Kotak folder di langkah 1 dan 2 memang terlihat mirip -- yang atas untuk <b>memilih bahan soal</b>, yang bawah untuk <b>menentukan siapa yang boleh mengerjakan</b> kuisnya nanti. Dua hal yang berbeda.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-xs font-semibold text-ink-muted">Judul Kuis (opsional)</label>
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Judul kuis"
                className="w-full rounded-[var(--radius-control)] border border-navy-100 bg-white px-3 py-2 text-sm text-ink placeholder:text-ink-faint"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold text-ink-muted">Jumlah Soal</label>
              <input
                type="number"
                min={3}
                max={15}
                value={numQuestions}
                onChange={(e) => setNumQuestions(Math.max(3, Math.min(15, Number(e.target.value))))}
                className="w-full rounded-[var(--radius-control)] border border-navy-100 bg-white px-3 py-2 text-sm text-ink"
              />
            </div>
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-ink-muted">Nilai Minimal Lulus</label>
            <input
              type="number"
              min={0}
              max={100}
              value={passingScore}
              onChange={(e) => setPassingScore(Math.max(0, Math.min(100, Number(e.target.value))))}
              className="w-full max-w-[160px] rounded-[var(--radius-control)] border border-navy-100 bg-white px-3 py-2 text-sm text-ink"
            />
          </div>

          {errorMsg && (
            <p className="rounded-[var(--radius-control)] bg-red-50 px-3 py-2 text-xs font-medium text-red-700">{errorMsg}</p>
          )}

          <button
            onClick={handleGenerate}
            disabled={isGenerating || (selectedDocs.size === 0 && !sourceFolder)}
            className="flex w-full items-center justify-center gap-2 rounded-[var(--radius-control)] bg-navy-900 py-2.5 text-sm font-semibold text-white hover:bg-navy-800 disabled:opacity-50"
          >
            {isGenerating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
            {isGenerating ? "AI sedang membuat soal..." : "Generate Kuis"}
          </button>
        </div>
      </div>
    </div>
  );
}
