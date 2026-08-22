"use client";
import { useState, useEffect } from "react";
import { CheckCircle2, Clock, CalendarCheck, Paperclip, Loader2, Pencil, Settings2 } from "lucide-react";
import Link from "next/link";
import { TopBar } from "@/components/TopBar";
import { apiJson, apiFetch, getStoredUser } from "@/lib/api";

interface FormField {
  id: string;
  label: string;
  field_type: "short_text" | "long_text" | "number" | "date" | "select" | "checkbox" | "file";
  options: string[];
  file_kind: "video" | "audio" | "document" | "any";
  is_required: boolean;
  sort_order: number;
}

interface Template {
  id: string;
  name: string;
  description: string | null;
  fields: FormField[];
}

interface Answer {
  value_text?: string;
  file_url?: string;
  file_kind?: string;
}

const ACCEPT_BY_KIND: Record<string, string> = {
  video: "video/*",
  audio: "audio/*",
  document: ".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt",
  any: "*",
};

export default function AttendancePage() {
  const user = getStoredUser();
  const isAdminTier = user?.role === "Admin" || user?.role === "SuperAdmin";

  const [isLoading, setIsLoading] = useState(true);
  const [template, setTemplate] = useState<Template | null>(null);
  const [submission, setSubmission] = useState<any>(null);
  const [editing, setEditing] = useState(false);
  const [values, setValues] = useState<Record<string, Answer>>({});
  const [uploadingField, setUploadingField] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const load = () => {
    setIsLoading(true);
    apiJson("/api/forms/submission/today")
      .then((data) => {
        setTemplate(data.template);
        setSubmission(data.submission);
        if (data.submission) {
          const prefill: Record<string, Answer> = {};
          for (const a of data.submission.answers || []) {
            prefill[a.field_id] = { value_text: a.value_text, file_url: a.file_url, file_kind: a.file_kind };
          }
          setValues(prefill);
        } else {
          setValues({});
        }
        setEditing(!data.submission);
      })
      .finally(() => setIsLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const setFieldValue = (fieldId: string, patch: Answer) => {
    setValues((prev) => ({ ...prev, [fieldId]: { ...prev[fieldId], ...patch } }));
  };

  const handleFileChange = async (field: FormField, file: File | null) => {
    if (!file) return;
    setUploadingField(field.id);
    setErrorMsg(null);
    try {
      const formData = new FormData();
      formData.append("field_id", field.id);
      formData.append("file", file);
      const res = await apiFetch("/api/forms/upload-answer", { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Upload gagal.");
      setFieldValue(field.id, { value_text: file.name, file_url: data.file_url, file_kind: data.file_kind });
    } catch (e: any) {
      setErrorMsg(e.message || "Upload file gagal.");
    } finally {
      setUploadingField(null);
    }
  };

  const handleSubmit = async () => {
    if (!template) return;
    setErrorMsg(null);

    const missing = template.fields.filter((f) => f.is_required && !values[f.id]?.value_text && !values[f.id]?.file_url);
    if (missing.length > 0) {
      setErrorMsg(`Wajib diisi: ${missing.map((f) => f.label).join(", ")}`);
      return;
    }

    setIsSubmitting(true);
    try {
      const answers = template.fields
        .filter((f) => values[f.id]?.value_text || values[f.id]?.file_url)
        .map((f) => ({ field_id: f.id, ...values[f.id] }));
      await apiJson("/api/forms/submit", { method: "POST", body: JSON.stringify({ answers }) });
      load();
    } catch (e: any) {
      setErrorMsg(e.message || "Gagal mengirim form.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const today = new Date().toLocaleDateString("id-ID", { weekday: "long", day: "numeric", month: "long", year: "numeric" });

  return (
    <div>
      <TopBar
        title="Kehadiran & Lapor Kerjaan"
        description="Isi form harian -- mengisi form ini otomatis tercatat sebagai hadir hari ini."
        action={
          isAdminTier ? (
            <Link
              href="/dashboard/settings/form-builder"
              className="flex items-center gap-2 rounded-[var(--radius-control)] border border-navy-100 bg-white px-3 py-2 text-xs font-semibold text-ink-muted hover:bg-navy-50"
            >
              <Settings2 className="h-3.5 w-3.5" /> Atur Form
            </Link>
          ) : undefined
        }
      />
      <div className="p-8">
        <div className="mx-auto max-w-xl">
          <div className="mb-4 flex items-center gap-2 text-xs text-ink-faint">
            <Clock className="h-3.5 w-3.5" /> {today}
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center rounded-[var(--radius-card)] border border-navy-100 bg-white p-12">
              <Loader2 className="h-5 w-5 animate-spin text-navy-700" />
            </div>
          ) : !template ? (
            <div className="space-y-3 rounded-[var(--radius-card)] border border-navy-100 bg-white p-8 text-center shadow-[var(--shadow-card)]">
              <CalendarCheck className="mx-auto h-8 w-8 text-ink-faint" />
              <p className="text-sm font-semibold text-ink">Form harian belum diatur</p>
              <p className="text-xs text-ink-faint">
                {isAdminTier
                  ? "Buat Form Kehadiran & Lapor Kerjaan dulu di halaman Atur Form."
                  : "Hubungi Admin/SuperAdmin untuk mengatur form harian."}
              </p>
              {isAdminTier && (
                <Link
                  href="/dashboard/settings/form-builder"
                  className="inline-flex items-center gap-2 rounded-[var(--radius-control)] bg-navy-900 px-4 py-2 text-xs font-semibold text-white hover:bg-navy-800"
                >
                  <Settings2 className="h-3.5 w-3.5" /> Atur Form Sekarang
                </Link>
              )}
            </div>
          ) : !editing && submission ? (
            <div className="space-y-4 rounded-[var(--radius-card)] border border-navy-100 bg-white p-6 shadow-[var(--shadow-card)]">
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-green-50">
                    <CheckCircle2 className="h-5 w-5 text-green-600" />
                  </span>
                  <div>
                    <p className="text-sm font-semibold text-ink">Sudah diisi hari ini</p>
                    <p className="text-xs text-ink-faint">
                      Terkirim pukul {submission.submitted_at?.slice(11, 16)}
                      {submission.status === "late" && <span className="ml-1.5 rounded-full bg-orange-50 px-2 py-0.5 text-2xs font-semibold text-orange-600">Terlambat</span>}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setEditing(true)}
                  className="flex shrink-0 items-center gap-1.5 rounded border border-navy-100 bg-white px-2.5 py-1.5 text-2xs font-semibold text-ink-muted hover:bg-navy-50"
                >
                  <Pencil className="h-3 w-3" /> Edit
                </button>
              </div>

              <div className="space-y-3 border-t border-navy-50 pt-4">
                {template.fields.map((f) => {
                  const a = values[f.id];
                  if (!a?.value_text && !a?.file_url) return null;
                  return (
                    <div key={f.id}>
                      <p className="text-2xs font-semibold uppercase tracking-wide text-ink-faint">{f.label}</p>
                      {a.file_url ? (
                        <a href={a.file_url} target="_blank" rel="noreferrer" className="mt-0.5 flex items-center gap-1.5 text-xs font-medium text-navy-700 hover:underline">
                          <Paperclip className="h-3 w-3" /> {a.value_text || "Lihat file"}
                        </a>
                      ) : (
                        <p className="mt-0.5 whitespace-pre-wrap text-sm text-ink">{a.value_text}</p>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="space-y-5 rounded-[var(--radius-card)] border border-navy-100 bg-white p-6 shadow-[var(--shadow-card)]">
              <div>
                <h3 className="text-sm font-semibold text-ink">{template.name}</h3>
                {template.description && <p className="mt-1 text-xs text-ink-faint">{template.description}</p>}
              </div>

              <div className="space-y-4">
                {template.fields.map((f) => (
                  <FieldInput
                    key={f.id}
                    field={f}
                    value={values[f.id]}
                    onChange={(patch) => setFieldValue(f.id, patch)}
                    onFileChange={(file) => handleFileChange(f, file)}
                    uploading={uploadingField === f.id}
                  />
                ))}
              </div>

              {errorMsg && (
                <p className="rounded-[var(--radius-control)] bg-red-50 px-3 py-2 text-xs font-medium text-red-700">{errorMsg}</p>
              )}

              <div className="flex items-center justify-end gap-2 border-t border-navy-50 pt-4">
                {submission && (
                  <button
                    onClick={() => { setEditing(false); load(); }}
                    className="rounded border border-navy-100 px-3 py-2 text-xs font-medium text-ink-muted hover:bg-navy-50"
                  >
                    Batal
                  </button>
                )}
                <button
                  onClick={handleSubmit}
                  disabled={isSubmitting}
                  className="flex items-center gap-2 rounded-[var(--radius-control)] bg-navy-900 px-5 py-2.5 text-sm font-semibold text-white hover:bg-navy-800 disabled:opacity-50"
                >
                  {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <CalendarCheck className="h-4 w-4" />}
                  {isSubmitting ? "Mengirim..." : "Kirim Form"}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function FieldInput({
  field, value, onChange, onFileChange, uploading,
}: {
  field: FormField;
  value?: Answer;
  onChange: (patch: Answer) => void;
  onFileChange: (file: File | null) => void;
  uploading: boolean;
}) {
  const label = (
    <label className="mb-1.5 block text-xs font-semibold text-ink">
      {field.label} {field.is_required && <span className="text-red-500">*</span>}
    </label>
  );

  const baseInput = "w-full rounded-[var(--radius-control)] border border-navy-100 bg-white px-3 py-2 text-sm text-ink placeholder:text-ink-faint focus:border-navy-400";

  switch (field.field_type) {
    case "long_text":
      return (
        <div>
          {label}
          <textarea
            rows={4}
            className={baseInput}
            value={value?.value_text || ""}
            onChange={(e) => onChange({ value_text: e.target.value })}
          />
        </div>
      );
    case "number":
      return (
        <div>
          {label}
          <input
            type="number"
            className={baseInput}
            value={value?.value_text || ""}
            onChange={(e) => onChange({ value_text: e.target.value })}
          />
        </div>
      );
    case "date":
      return (
        <div>
          {label}
          <input
            type="date"
            className={baseInput}
            value={value?.value_text || ""}
            onChange={(e) => onChange({ value_text: e.target.value })}
          />
        </div>
      );
    case "select":
      return (
        <div>
          {label}
          <select
            className={baseInput}
            value={value?.value_text || ""}
            onChange={(e) => onChange({ value_text: e.target.value })}
          >
            <option value="">Pilih...</option>
            {field.options.map((opt) => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </select>
        </div>
      );
    case "checkbox": {
      const selected: string[] = value?.value_text ? JSON.parse(value.value_text) : [];
      const toggle = (opt: string) => {
        const next = selected.includes(opt) ? selected.filter((o) => o !== opt) : [...selected, opt];
        onChange({ value_text: JSON.stringify(next) });
      };
      return (
        <div>
          {label}
          <div className="space-y-1.5">
            {field.options.map((opt) => (
              <label key={opt} className="flex items-center gap-2 text-sm text-ink">
                <input type="checkbox" checked={selected.includes(opt)} onChange={() => toggle(opt)} className="h-4 w-4 rounded border-navy-200" />
                {opt}
              </label>
            ))}
          </div>
        </div>
      );
    }
    case "file":
      return (
        <div>
          {label}
          <input
            type="file"
            accept={ACCEPT_BY_KIND[field.file_kind] || "*"}
            disabled={uploading}
            onChange={(e) => onFileChange(e.target.files?.[0] || null)}
            className="block w-full text-xs text-ink-muted file:mr-3 file:rounded-[var(--radius-control)] file:border-0 file:bg-navy-900 file:px-3 file:py-2 file:text-xs file:font-semibold file:text-white hover:file:bg-navy-800"
          />
          {uploading && <p className="mt-1 text-2xs text-ink-faint">Mengunggah...</p>}
          {!uploading && value?.file_url && <p className="mt-1 text-2xs text-green-600">Terunggah: {value.value_text}</p>}
          <p className="mt-1 text-2xs text-ink-faint">
            Format: {field.file_kind === "video" ? "video" : field.file_kind === "audio" ? "audio" : field.file_kind === "document" ? "dokumen" : "bebas"}
          </p>
        </div>
      );
    default:
      return (
        <div>
          {label}
          <input
            type="text"
            className={baseInput}
            value={value?.value_text || ""}
            onChange={(e) => onChange({ value_text: e.target.value })}
          />
        </div>
      );
  }
}
