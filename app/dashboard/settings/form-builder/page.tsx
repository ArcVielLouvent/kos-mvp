"use client";
import { useState, useEffect } from "react";
import { Plus, Trash2, GripVertical, Loader2, Save, ArrowLeft, X } from "lucide-react";
import Link from "next/link";
import { TopBar } from "@/components/TopBar";
import { apiJson } from "@/lib/api";

interface FieldDraft {
  _key: string;
  label: string;
  field_type: "short_text" | "long_text" | "number" | "date" | "select" | "checkbox" | "file";
  options: string[];
  file_kind: "video" | "audio" | "document" | "any";
  is_required: boolean;
}

const TYPE_LABELS: Record<string, string> = {
  short_text: "Teks Singkat",
  long_text: "Paragraf",
  number: "Angka",
  date: "Tanggal",
  select: "Pilihan (Dropdown)",
  checkbox: "Kotak Centang (Multi-pilih)",
  file: "Upload File",
};

function newField(): FieldDraft {
  return {
    _key: Math.random().toString(36).slice(2),
    label: "",
    field_type: "short_text",
    options: [],
    file_kind: "any",
    is_required: false,
  };
}

export default function FormBuilderPage() {
  const [name, setName] = useState("Form Kehadiran & Lapor Kerjaan");
  const [description, setDescription] = useState("");
  const [fields, setFields] = useState<FieldDraft[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState<string | null>(null);

  useEffect(() => {
    apiJson("/api/forms/template")
      .then((data) => {
        if (data.template) {
          setName(data.template.name);
          setDescription(data.template.description || "");
          setFields(
            (data.template.fields || []).map((f: any) => ({
              _key: f.id,
              label: f.label,
              field_type: f.field_type,
              options: f.options || [],
              file_kind: f.file_kind || "any",
              is_required: f.is_required,
            }))
          );
        } else {
          setFields([{ ...newField(), label: "Ringkasan pekerjaan hari ini", field_type: "long_text", is_required: true }]);
        }
      })
      .finally(() => setIsLoading(false));
  }, []);

  const updateField = (key: string, patch: Partial<FieldDraft>) => {
    setFields((prev) => prev.map((f) => (f._key === key ? { ...f, ...patch } : f)));
  };

  const removeField = (key: string) => {
    setFields((prev) => prev.filter((f) => f._key !== key));
  };

  const addField = () => {
    setFields((prev) => [...prev, newField()]);
  };

  const moveField = (index: number, dir: -1 | 1) => {
    setFields((prev) => {
      const next = [...prev];
      const target = index + dir;
      if (target < 0 || target >= next.length) return prev;
      [next[index], next[target]] = [next[target], next[index]];
      return next;
    });
  };

  const handleSave = async () => {
    setSaveMsg(null);
    if (fields.length === 0) {
      setSaveMsg("Form minimal punya 1 field.");
      return;
    }
    if (fields.some((f) => !f.label.trim())) {
      setSaveMsg("Semua field wajib punya label/pertanyaan.");
      return;
    }
    setIsSaving(true);
    try {
      await apiJson("/api/forms/template", {
        method: "PUT",
        body: JSON.stringify({
          name,
          description,
          fields: fields.map((f) => ({
            label: f.label.trim(),
            field_type: f.field_type,
            options: f.options.filter((o) => o.trim()),
            file_kind: f.file_kind,
            is_required: f.is_required,
          })),
        }),
      });
      setSaveMsg("Form berhasil disimpan.");
    } catch (e: any) {
      setSaveMsg(e.message || "Gagal menyimpan form.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div>
      <TopBar
        title="Atur Form Kehadiran & Lapor Kerjaan"
        description="Field bisa diatur bebas ala Google Forms -- termasuk upload video/audio/dokumen, wajib atau opsional."
        action={
          <Link href="/dashboard/attendance" className="flex items-center gap-2 rounded-[var(--radius-control)] border border-navy-100 bg-white px-3 py-2 text-xs font-semibold text-ink-muted hover:bg-navy-50">
            <ArrowLeft className="h-3.5 w-3.5" /> Kembali
          </Link>
        }
      />
      <div className="p-8">
        <div className="mx-auto max-w-2xl space-y-4">
          {isLoading ? (
            <div className="flex items-center justify-center rounded-[var(--radius-card)] border border-navy-100 bg-white p-12">
              <Loader2 className="h-5 w-5 animate-spin text-navy-700" />
            </div>
          ) : (
            <>
              <div className="space-y-3 rounded-[var(--radius-card)] border border-navy-100 bg-white p-5 shadow-[var(--shadow-card)]">
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Nama form"
                  className="w-full border-0 border-b border-navy-100 bg-transparent px-0 py-1.5 text-base font-semibold text-ink focus:border-navy-400 focus:outline-none"
                />
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Deskripsi (opsional) -- terlihat karyawan sebelum mengisi"
                  rows={2}
                  className="w-full resize-none border-0 bg-transparent px-0 text-xs text-ink-muted placeholder:text-ink-faint focus:outline-none"
                />
              </div>

              {fields.map((f, i) => (
                <div key={f._key} className="space-y-3 rounded-[var(--radius-card)] border border-navy-100 bg-white p-5 shadow-[var(--shadow-card)]">
                  <div className="flex items-start gap-2">
                    <GripVertical className="mt-2.5 h-4 w-4 shrink-0 text-ink-faint" />
                    <input
                      value={f.label}
                      onChange={(e) => updateField(f._key, { label: e.target.value })}
                      placeholder="Pertanyaan / label field"
                      className="flex-1 border-0 border-b border-navy-100 bg-transparent px-0 py-1.5 text-sm font-medium text-ink focus:border-navy-400 focus:outline-none"
                    />
                    <button onClick={() => removeField(f._key)} className="shrink-0 rounded p-1.5 text-ink-faint hover:bg-red-50 hover:text-red-600">
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>

                  <div className="flex flex-wrap items-center gap-3 pl-6">
                    <select
                      value={f.field_type}
                      onChange={(e) => updateField(f._key, { field_type: e.target.value as FieldDraft["field_type"] })}
                      className="rounded border border-navy-100 bg-white px-2.5 py-1.5 text-xs text-ink"
                    >
                      {Object.entries(TYPE_LABELS).map(([val, label]) => (
                        <option key={val} value={val}>{label}</option>
                      ))}
                    </select>

                    {f.field_type === "file" && (
                      <select
                        value={f.file_kind}
                        onChange={(e) => updateField(f._key, { file_kind: e.target.value as FieldDraft["file_kind"] })}
                        className="rounded border border-navy-100 bg-white px-2.5 py-1.5 text-xs text-ink"
                      >
                        <option value="any">Semua jenis file</option>
                        <option value="video">Video saja</option>
                        <option value="audio">Audio saja</option>
                        <option value="document">Dokumen saja</option>
                      </select>
                    )}

                    <label className="ml-auto flex items-center gap-1.5 text-xs font-medium text-ink-muted">
                      <input
                        type="checkbox"
                        checked={f.is_required}
                        onChange={(e) => updateField(f._key, { is_required: e.target.checked })}
                        className="h-3.5 w-3.5 rounded border-navy-200"
                      />
                      Wajib diisi
                    </label>

                    <div className="flex gap-1">
                      <button onClick={() => moveField(i, -1)} disabled={i === 0} className="rounded border border-navy-100 px-1.5 py-1 text-2xs text-ink-muted disabled:opacity-30">↑</button>
                      <button onClick={() => moveField(i, 1)} disabled={i === fields.length - 1} className="rounded border border-navy-100 px-1.5 py-1 text-2xs text-ink-muted disabled:opacity-30">↓</button>
                    </div>
                  </div>

                  {(f.field_type === "select" || f.field_type === "checkbox") && (
                    <div className="space-y-1.5 pl-6">
                      <p className="text-2xs font-semibold uppercase tracking-wide text-ink-faint">Pilihan</p>
                      {f.options.map((opt, oi) => (
                        <div key={oi} className="flex items-center gap-2">
                          <input
                            value={opt}
                            onChange={(e) => {
                              const next = [...f.options];
                              next[oi] = e.target.value;
                              updateField(f._key, { options: next });
                            }}
                            className="flex-1 rounded border border-navy-100 bg-white px-2.5 py-1.5 text-xs text-ink"
                          />
                          <button onClick={() => updateField(f._key, { options: f.options.filter((_, x) => x !== oi) })} className="text-ink-faint hover:text-red-600">
                            <X className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      ))}
                      <button
                        onClick={() => updateField(f._key, { options: [...f.options, ""] })}
                        className="flex items-center gap-1 text-2xs font-semibold text-navy-700 hover:underline"
                      >
                        <Plus className="h-3 w-3" /> Tambah pilihan
                      </button>
                    </div>
                  )}
                </div>
              ))}

              <button
                onClick={addField}
                className="flex w-full items-center justify-center gap-2 rounded-[var(--radius-card)] border-2 border-dashed border-navy-100 bg-white py-3 text-sm font-medium text-ink-muted hover:border-navy-300 hover:bg-navy-50"
              >
                <Plus className="h-4 w-4" /> Tambah Field
              </button>

              {saveMsg && (
                <p className="rounded-[var(--radius-control)] bg-navy-50 px-3 py-2 text-xs font-medium text-navy-900">{saveMsg}</p>
              )}

              <div className="flex justify-end">
                <button
                  onClick={handleSave}
                  disabled={isSaving}
                  className="flex items-center gap-2 rounded-[var(--radius-control)] bg-navy-900 px-5 py-2.5 text-sm font-semibold text-white hover:bg-navy-800 disabled:opacity-50"
                >
                  {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                  {isSaving ? "Menyimpan..." : "Simpan Form"}
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
