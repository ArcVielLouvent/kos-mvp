"use client";
import { useState } from "react";
import { Upload, Inbox, CheckCircle2, AlertCircle } from "lucide-react";
import { TopBar } from "@/components/TopBar";
import { apiFetch } from "@/lib/api";

export default function UploadDokumenPage() {
    const [isProcessing, setIsProcessing] = useState(false);
    const [message, setMessage] = useState<{ text: string; type: "success" | "error" } | null>(null);
    const [uploadKey, setUploadKey] = useState(0);

    const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFiles = e.target.files;
        if (!selectedFiles || selectedFiles.length === 0) return;
        const filesArray = Array.from(selectedFiles);
        setIsProcessing(true);
        setMessage(null);

        let successCount = 0;
        const errors: string[] = [];

        for (let i = 0; i < filesArray.length; i++) {
            const f = filesArray[i];
            setMessage({ text: `Memproses ${i + 1} dari ${filesArray.length}: ${f.name}...`, type: "success" });
            const formData = new FormData();
            formData.append("files", f);
            formData.append("folder_path", "/Kotak Masuk/");
            try {
                const res = await apiFetch("/api/upload", { method: "POST", body: formData });
                const result = await res.json();
                successCount += result.successCount || 0;
                if (result.errors?.length) errors.push(...result.errors);
            } catch {
                errors.push(`${f.name}: request gagal atau timeout.`);
            }
        }

        const summary = `${successCount} dari ${filesArray.length} dokumen berhasil dikirim ke Kotak Masuk.`;
        setMessage({
            text: errors.length > 0 ? `${summary}\n${errors.join("\n")}` : summary,
            type: errors.length > 0 && successCount === 0 ? "error" : "success",
        });
        setIsProcessing(false);
        setUploadKey((k) => k + 1);
    };

    return (
        <div>
            <TopBar title="Upload Dokumen" description="Dokumen yang Anda upload akan masuk ke Kotak Masuk untuk disortir oleh Admin." />
            <div className="p-8">
                <div className="mx-auto max-w-lg space-y-4 rounded-[var(--radius-card)] border border-navy-100 bg-white p-8 text-center shadow-[var(--shadow-card)]">
                    <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-navy-50">
                        <Inbox className="h-6 w-6 text-navy-700" />
                    </span>
                    <div>
                        <h3 className="text-sm font-semibold text-ink">Kirim ke Kotak Masuk</h3>
                        <p className="mt-1 text-xs text-ink-muted">
                            Anda tidak perlu memilih folder -- dokumen otomatis masuk ke Kotak Masuk,
                            nanti disortir oleh Admin/SuperAdmin ke folder yang sesuai.
                        </p>
                    </div>

                    <label className="mx-auto flex w-fit cursor-pointer items-center gap-2 rounded-[var(--radius-control)] bg-navy-900 px-5 py-2.5 text-sm font-semibold text-white hover:bg-navy-800">
                        <Upload className="h-4 w-4" />
                        {isProcessing ? "Memproses..." : "Pilih Dokumen"}
                        <input
                            key={uploadKey}
                            type="file"
                            multiple
                            onChange={handleUpload}
                            disabled={isProcessing}
                            className="hidden"
                        />
                    </label>

                    {message && (
                        <div
                            className={`flex items-start gap-2 whitespace-pre-line rounded-[var(--radius-control)] border px-4 py-3 text-left text-xs ${
                                message.type === "error"
                                    ? "border-red-100 bg-red-50 text-red-700"
                                    : "border-navy-100 bg-navy-50 text-navy-900"
                            }`}
                        >
                            {message.type === "error" ? (
                                <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                            ) : (
                                <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                            )}
                            {message.text}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
