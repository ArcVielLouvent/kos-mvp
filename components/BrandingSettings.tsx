"use client";
import { useState, useEffect } from "react";
import { Image as ImageIcon, FileText, Upload, Loader2, CheckCircle2 } from "lucide-react";
import { apiFetch, apiJson } from "@/lib/api";

export function BrandingSettings() {
  const [branding, setBranding] = useState<{ logo_url?: string; docx_template_url?: string } | null>(null);
  const [uploadingLogo, setUploadingLogo] = useState(false);
  const [uploadingTemplate, setUploadingTemplate] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const load = () => {
    apiJson("/api/team/branding")
      .then(setBranding)
      .catch(() => setBranding(null));
  };

  useEffect(() => {
    load();
  }, []);

  const uploadLogo = async (file: File | null) => {
    if (!file) return;
    setUploadingLogo(true);
    setMsg(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await apiFetch("/api/team/branding/logo", { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Gagal upload logo.");
      setMsg("Logo tersimpan.");
      load();
    } catch (e: any) {
      setMsg(e.message || "Gagal upload logo.");
    } finally {
      setUploadingLogo(false);
    }
  };

  const uploadTemplate = async (file: File | null) => {
    if (!file) return;
    setUploadingTemplate(true);
    setMsg(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await apiFetch("/api/team/branding/template", { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Gagal upload template.");
      setMsg("Template tersimpan.");
      load();
    } catch (e: any) {
      setMsg(e.message || "Gagal upload template.");
    } finally {
      setUploadingTemplate(false);
    }
  };

  return (
    <div className="space-y-4 rounded-[var(--radius-card)] border border-navy-100 bg-white p-5 shadow-[var(--shadow-card)]">
      <div>
        <h3 className="text-sm font-semibold text-ink">Branding Perusahaan</h3>
        <p className="mt-1 text-xs text-ink-faint">
          Logo & template dipakai otomatis saat AI membuatkan dokumen lewat Chat KOS (mis. ketik "buatkan SOP...").
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <p className="flex items-center gap-1.5 text-xs font-semibold text-ink-muted">
            <ImageIcon className="h-3.5 w-3.5" /> Logo Perusahaan
            {branding?.logo_url && <CheckCircle2 className="h-3.5 w-3.5 text-green-600" />}
          </p>
          {branding?.logo_url && (
            <img src={branding.logo_url} alt="Logo perusahaan" className="h-16 w-16 rounded border border-navy-100 object-contain p-1" />
          )}
          <label className="flex cursor-pointer items-center justify-center gap-2 rounded-[var(--radius-control)] border border-dashed border-navy-100 bg-navy-50/30 py-3 text-xs font-medium text-ink-muted hover:border-navy-300">
            {uploadingLogo ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
            {uploadingLogo ? "Mengunggah..." : branding?.logo_url ? "Ganti Logo" : "Upload Logo (PNG/JPG)"}
            <input type="file" accept=".png,.jpg,.jpeg" disabled={uploadingLogo} className="hidden" onChange={(e) => uploadLogo(e.target.files?.[0] || null)} />
          </label>
        </div>

        <div className="space-y-2">
          <p className="flex items-center gap-1.5 text-xs font-semibold text-ink-muted">
            <FileText className="h-3.5 w-3.5" /> Template Surat (.docx)
            {branding?.docx_template_url && <CheckCircle2 className="h-3.5 w-3.5 text-green-600" />}
          </p>
          <p className="text-2xs text-ink-faint">
            {branding?.docx_template_url ? "Template kosongan sudah tersimpan." : "Belum ada template -- AI akan pakai format polos."}
          </p>
          <label className="flex cursor-pointer items-center justify-center gap-2 rounded-[var(--radius-control)] border border-dashed border-navy-100 bg-navy-50/30 py-3 text-xs font-medium text-ink-muted hover:border-navy-300">
            {uploadingTemplate ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
            {uploadingTemplate ? "Mengunggah..." : branding?.docx_template_url ? "Ganti Template" : "Upload Template (.docx)"}
            <input type="file" accept=".docx" disabled={uploadingTemplate} className="hidden" onChange={(e) => uploadTemplate(e.target.files?.[0] || null)} />
          </label>
        </div>
      </div>

      {msg && <p className="rounded-[var(--radius-control)] bg-navy-50 px-3 py-2 text-xs font-medium text-navy-900">{msg}</p>}
    </div>
  );
}
