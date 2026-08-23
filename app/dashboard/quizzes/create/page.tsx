"use client";
import { useState } from "react";
import { ArrowLeft, Sparkles, Loader2, FileText } from "lucide-react";
import Link from "next/link";
import { TopBar } from "@/components/TopBar";
import { DocumentPicker } from "@/components/DocumentPicker";
import { FolderTreePicker } from "@/components/FolderTreePicker";
import { apiJson } from "@/lib/api";
import { useRouter } from "next/navigation";

export default function CreateQuizPage() {
  const router = useRouter();
  const [selectedDoc, setSelectedDoc] = useState<{ id: string; title: string } | null>(null);
  const [title, setTitle] = useState("");
  const [folderPath, setFolderPath] = useState("/");
  const [numQuestions, setNumQuestions] = useState(5);
  const [passingScore, setPassingScore] = useState(70);
  const [isGenerating, setIsGenerating] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!selectedDoc) {
      setErrorMsg("Pilih dokumen sumber dulu.");
      return;
    }
    setErrorMsg(null);
    setIsGenerating(true);
    try {
      await apiJson("/api/quizzes/generate", {
        method: "POST",
        body: JSON.stringify({
          source_document_id: selectedDoc.id,
          title: title.trim() || `Kuis: ${selectedDoc.title}`,
          folder_path: folderPath,
          num_questions: numQuestions,
          passing_score: passingScore,
        }),
      });
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
        <div className="mx-auto max-w-2xl space-y-4">
          <div>
            <label className="mb-1.5 block text-xs font-semibold text-ink">1. Pilih Dokumen Sumber</label>
            <DocumentPicker selectedId={selectedDoc?.id || null} onSelect={setSelectedDoc} />
            {selectedDoc && (
              <p className="mt-1.5 flex items-center gap-1.5 text-xs text-navy-700">
                <FileText className="h-3.5 w-3.5" /> Terpilih: {selectedDoc.title}
              </p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-xs font-semibold text-ink-muted">Judul Kuis (opsional)</label>
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder={selectedDoc ? `Kuis: ${selectedDoc.title}` : "Judul kuis"}
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

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-xs font-semibold text-ink-muted">Nilai Minimal Lulus</label>
              <input
                type="number"
                min={0}
                max={100}
                value={passingScore}
                onChange={(e) => setPassingScore(Math.max(0, Math.min(100, Number(e.target.value))))}
                className="w-full rounded-[var(--radius-control)] border border-navy-100 bg-white px-3 py-2 text-sm text-ink"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold text-ink-muted">Folder Kuis (siapa yang bisa lihat)</label>
              <FolderTreePicker value={folderPath} onChange={setFolderPath} />
            </div>
          </div>

          {errorMsg && (
            <p className="rounded-[var(--radius-control)] bg-red-50 px-3 py-2 text-xs font-medium text-red-700">{errorMsg}</p>
          )}

          <button
            onClick={handleGenerate}
            disabled={isGenerating || !selectedDoc}
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
