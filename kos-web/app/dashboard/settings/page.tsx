"use client";
import { useState } from "react";
import { Building2, Image as ImageIcon, FileText, Upload } from "lucide-react";
import { TopBar } from "@/components/TopBar";

export default function SettingsPage() {
  const [tab, setTab] = useState<"general" | "branding" | "team">("general");

  return (
    <div>
      <TopBar title="Pengaturan" description="Kelola informasi dan branding perusahaan." />
      <div className="p-8">
        <div className="mb-6 flex gap-1 border-b border-navy-100">
          {[
            { id: "general", label: "Umum" },
            { id: "branding", label: "Branding" },
            { id: "team", label: "Keamanan Tim" },
          ].map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id as typeof tab)}
              className={`border-b-2 px-4 py-2.5 text-sm font-medium transition-colors ${
                tab === t.id
                  ? "border-navy-900 text-navy-900"
                  : "border-transparent text-ink-muted hover:text-ink"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {tab === "general" && (
          <div className="max-w-lg space-y-5 rounded-[var(--radius-card)] border border-navy-100 bg-white p-6 shadow-[var(--shadow-card)]">
            <div className="flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-[var(--radius-control)] bg-navy-900">
                <Building2 className="h-5 w-5 text-white" />
              </span>
              <div>
                <p className="text-sm font-semibold text-ink">Kopi Nusantara</p>
                <p className="text-xs text-ink-faint">Admin: admin@kopinusantara.com</p>
              </div>
            </div>
            <Field label="Nama Perusahaan" defaultValue="Kopi Nusantara" />
            <button className="rounded-[var(--radius-control)] bg-navy-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-navy-800">
              Simpan Perubahan
            </button>
          </div>
        )}

        {tab === "branding" && (
          <div className="max-w-lg space-y-6 rounded-[var(--radius-card)] border border-navy-100 bg-white p-6 shadow-[var(--shadow-card)]">
            <div>
              <p className="mb-1 text-sm font-semibold text-ink">Logo Perusahaan</p>
              <p className="mb-3 text-xs text-ink-muted">
                Nempel otomatis di kop dokumen yang di-generate AI lewat Chat KOS.
              </p>
              <UploadBox icon={ImageIcon} label="Belum ada logo diupload" />
            </div>
            <div>
              <p className="mb-1 text-sm font-semibold text-ink">Template Surat (.docx)</p>
              <p className="mb-3 text-xs text-ink-muted">
                Draf AI akan disisipkan ke dalam template ini, ikut font/kop template.
              </p>
              <UploadBox icon={FileText} label="Belum ada template diupload" />
            </div>
          </div>
        )}

        {tab === "team" && (
          <div className="max-w-lg space-y-4 rounded-[var(--radius-card)] border border-navy-100 bg-white p-6 shadow-[var(--shadow-card)]">
            <p className="text-sm text-ink-muted">
              Kelola siapa yang bisa menambah Admin baru dan level akses CRUD/read-only
              tersedia di halaman{" "}
              <a href="/dashboard/team" className="font-medium text-navy-700 hover:underline">
                Manajemen Tim
              </a>
              .
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

function Field({ label, defaultValue }: { label: string; defaultValue?: string }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm font-medium text-ink">{label}</span>
      <input
        defaultValue={defaultValue}
        className="w-full rounded-[var(--radius-control)] border border-navy-100 px-3 py-2.5 text-sm focus:border-navy-500 focus:outline-none"
      />
    </label>
  );
}

function UploadBox({ icon: Icon, label }: { icon: typeof ImageIcon; label: string }) {
  return (
    <div className="flex items-center justify-between rounded-[var(--radius-control)] border border-dashed border-navy-100 bg-navy-50 px-4 py-4">
      <div className="flex items-center gap-3">
        <Icon className="h-5 w-5 text-ink-faint" />
        <span className="text-sm text-ink-muted">{label}</span>
      </div>
      <button className="flex items-center gap-1.5 rounded-[var(--radius-control)] border border-navy-100 bg-white px-3 py-1.5 text-xs font-medium text-ink hover:bg-navy-100">
        <Upload className="h-3.5 w-3.5" /> Upload
      </button>
    </div>
  );
}