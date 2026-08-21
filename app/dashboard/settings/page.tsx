"use client";
import { useState, useEffect } from "react";
import { TopBar } from "@/components/TopBar";
import { getStoredUser } from "@/lib/api";
import { apiJson } from "@/lib/api";
import { Building2, Users, Image as ImageIcon, FileText, Clock, AlertTriangle, Bell } from "lucide-react";

export default function SettingsPage() {
    const user = getStoredUser();
    const [settings, setSettings] = useState<any>(null);
    const [isSaving, setIsSaving] = useState(false);

    useEffect(() => {
        apiJson("/api/settings/company")
            .then(setSettings)
            .catch(() => setSettings(null));
    }, []);

    const toggle = async (key: "poin_pelanggaran_enabled" | "notify_atasan_enabled") => {
        if (!settings) return;
        const newValue = !settings[key];
        setSettings({ ...settings, [key]: newValue }); // optimistic
        setIsSaving(true);
        try {
            await apiJson("/api/settings/company", {
                method: "PATCH",
                body: JSON.stringify({ [key]: newValue }),
            });
        } catch {
            setSettings({ ...settings, [key]: !newValue }); // rollback kalau gagal
        } finally {
            setIsSaving(false);
        }
    };

    return (
        <div>
            <TopBar title="Pengaturan" description="Informasi workspace perusahaan." />
            <div className="space-y-6 p-8">
                <div className="max-w-lg space-y-4 rounded-[var(--radius-card)] border border-navy-100 bg-white p-6">
                    <h3 className="text-sm font-semibold text-ink">Informasi Workspace</h3>

                    <div className="space-y-3">
                        <div className="flex items-center gap-3">
                            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-navy-50">
                                <Building2 className="h-4 w-4 text-navy-700" />
                            </span>
                            <div>
                                <p className="text-2xs text-ink-faint">Nama Perusahaan</p>
                                <p className="text-sm font-medium text-ink">{user?.company_name || "-"}</p>
                            </div>
                        </div>

                        <div className="flex items-center gap-3">
                            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-navy-50">
                                <Users className="h-4 w-4 text-navy-700" />
                            </span>
                            <div>
                                <p className="text-2xs text-ink-faint">Company ID</p>
                                <p className="font-mono-data text-sm font-medium text-ink">{user?.company_id}</p>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="max-w-lg space-y-4 rounded-[var(--radius-card)] border border-navy-100 bg-white p-6">
                    <h3 className="text-sm font-semibold text-ink">Pengaturan Fitur Kehadiran & Laporan</h3>
                    <p className="text-xs text-ink-muted">
                        Fitur-fitur ini opsional -- Anda yang menentukan mana yang aktif untuk perusahaan Anda.
                    </p>

                    {!settings ? (
                        <p className="text-xs text-ink-faint">Memuat...</p>
                    ) : (
                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <div className="flex items-start gap-2.5">
                                    <AlertTriangle className="mt-0.5 h-4 w-4 text-ink-faint" />
                                    <div>
                                        <p className="text-sm font-medium text-ink">Poin Pelanggaran</p>
                                        <p className="text-xs text-ink-faint">Karyawan yang tidak lapor beberapa hari berturut-turut dapat poin pelanggaran.</p>
                                    </div>
                                </div>
                                <button
                                    onClick={() => toggle("poin_pelanggaran_enabled")}
                                    disabled={isSaving}
                                    className={`relative h-6 w-11 shrink-0 rounded-full transition-colors ${
                                        settings.poin_pelanggaran_enabled ? "bg-navy-900" : "bg-navy-100"
                                    }`}
                                >
                                    <span
                                        className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${
                                            settings.poin_pelanggaran_enabled ? "translate-x-5" : "translate-x-0.5"
                                        }`}
                                    />
                                </button>
                            </div>

                            <div className="flex items-center justify-between border-t border-navy-50 pt-4">
                                <div className="flex items-start gap-2.5">
                                    <Bell className="mt-0.5 h-4 w-4 text-ink-faint" />
                                    <div>
                                        <p className="text-sm font-medium text-ink">Notifikasi ke Atasan Langsung</p>
                                        <p className="text-xs text-ink-faint">Selain ke Anda, atasan langsung juga diberi tahu kalau bawahannya belum lapor.</p>
                                    </div>
                                </div>
                                <button
                                    onClick={() => toggle("notify_atasan_enabled")}
                                    disabled={isSaving}
                                    className={`relative h-6 w-11 shrink-0 rounded-full transition-colors ${
                                        settings.notify_atasan_enabled ? "bg-navy-900" : "bg-navy-100"
                                    }`}
                                >
                                    <span
                                        className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${
                                            settings.notify_atasan_enabled ? "translate-x-5" : "translate-x-0.5"
                                        }`}
                                    />
                                </button>
                            </div>
                        </div>
                    )}
                </div>

                <div className="max-w-lg space-y-4 rounded-[var(--radius-card)] border border-dashed border-navy-200 bg-navy-50/40 p-6">
                    <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4 text-navy-400" />
                        <h3 className="text-sm font-semibold text-ink-muted">Branding Perusahaan (Segera Hadir)</h3>
                    </div>
                    <p className="text-xs text-ink-faint">
                        Upload logo & template surat perusahaan akan tersedia di sini setelah fitur file-generation
                        AI digabungkan dari branch pengembangan terpisah.
                    </p>
                    <div className="flex gap-3 opacity-50">
                        <div className="flex flex-1 items-center gap-2 rounded border border-navy-100 bg-white px-3 py-2 text-xs text-ink-faint">
                            <ImageIcon className="h-3.5 w-3.5" /> Logo perusahaan
                        </div>
                        <div className="flex flex-1 items-center gap-2 rounded border border-navy-100 bg-white px-3 py-2 text-xs text-ink-faint">
                            <FileText className="h-3.5 w-3.5" /> Template surat (.docx)
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}