"use client";
import { useState, useEffect } from "react";
import { TopBar } from "@/components/TopBar";
import { getStoredUser } from "@/lib/api";
import { apiJson } from "@/lib/api";
import { Building2, Users, Clock, AlertTriangle, Bell } from "lucide-react";
import { BrandingSettings } from "@/components/BrandingSettings";

export default function SettingsPage() {
    const user = getStoredUser();
    const [settings, setSettings] = useState<any>(null);
    const [savingKey, setSavingKey] = useState<string | null>(null);

    useEffect(() => {
        apiJson("/api/settings/company")
            .then(setSettings)
            .catch(() => setSettings(null));
    }, []);

    const toggle = async (key: "poin_pelanggaran_enabled" | "notify_atasan_enabled") => {
        if (!settings) return;
        const newValue = !settings[key];
        setSettings({ ...settings, [key]: newValue }); // optimistic
        setSavingKey(key);
        try {
            await apiJson("/api/settings/company", {
                method: "PATCH",
                body: JSON.stringify({ [key]: newValue }),
            });
        } catch {
            setSettings({ ...settings, [key]: !newValue }); // rollback kalau gagal
        } finally {
            setSavingKey((k) => (k === key ? null : k));
        }
    };

    // Slider di-drag bebas dulu di UI (state lokal, tanpa nembak API tiap
    // gerakan mouse) -- baru di-commit ke backend saat user lepas slider
    // (onMouseUp/onTouchEnd/onChange final), supaya tidak spam PATCH.
    const [deadlineDraft, setDeadlineDraft] = useState<number | null>(null);
    useEffect(() => {
        if (settings && deadlineDraft === null) {
            setDeadlineDraft(settings.attendance_deadline_hour ?? 24);
        }
    }, [settings]);

    const commitDeadline = async (value: number) => {
        if (!settings) return;
        const prev = settings.attendance_deadline_hour;
        setSettings({ ...settings, attendance_deadline_hour: value }); // optimistic
        setSavingKey("attendance_deadline_hour");
        try {
            await apiJson("/api/settings/company", {
                method: "PATCH",
                body: JSON.stringify({ attendance_deadline_hour: value }),
            });
        } catch {
            setSettings({ ...settings, attendance_deadline_hour: prev }); // rollback
            setDeadlineDraft(prev);
        } finally {
            setSavingKey((k) => (k === "attendance_deadline_hour" ? null : k));
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
                                    disabled={savingKey === "poin_pelanggaran_enabled"}
                                    className={`relative h-6 w-11 shrink-0 rounded-full transition-colors disabled:opacity-60 ${
                                        settings.poin_pelanggaran_enabled ? "bg-navy-900" : "bg-navy-100"
                                    }`}
                                >
                                    <span
                                        className={`absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${
                                            settings.poin_pelanggaran_enabled ? "translate-x-5" : "translate-x-0"
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
                                    disabled={savingKey === "notify_atasan_enabled"}
                                    className={`relative h-6 w-11 shrink-0 rounded-full transition-colors disabled:opacity-60 ${
                                        settings.notify_atasan_enabled ? "bg-navy-900" : "bg-navy-100"
                                    }`}
                                >
                                    <span
                                        className={`absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${
                                            settings.notify_atasan_enabled ? "translate-x-5" : "translate-x-0"
                                        }`}
                                    />
                                </button>
                            </div>

                            <div className="border-t border-navy-50 pt-4">
                                <div className="flex items-start gap-2.5">
                                    <Clock className="mt-0.5 h-4 w-4 text-ink-faint" />
                                    <div className="flex-1">
                                        <div className="flex items-center justify-between">
                                            <p className="text-sm font-medium text-ink">Batas Waktu Lapor Harian</p>
                                            <span className="rounded-full bg-navy-900 px-2.5 py-0.5 text-2xs font-bold text-white">
                                                {deadlineDraft ?? settings.attendance_deadline_hour ?? 24}:00
                                            </span>
                                        </div>
                                        <p className="mb-3 text-xs text-ink-faint">
                                            Karyawan dianggap terlambat kalau belum isi Form Kehadiran/Lapor Kerjaan sebelum jam ini.
                                        </p>
                                        <input
                                            type="range"
                                            min={1}
                                            max={24}
                                            step={1}
                                            value={deadlineDraft ?? settings.attendance_deadline_hour ?? 24}
                                            onChange={(e) => setDeadlineDraft(Number(e.target.value))}
                                            onMouseUp={(e) => commitDeadline(Number((e.target as HTMLInputElement).value))}
                                            onTouchEnd={(e) => commitDeadline(Number((e.target as HTMLInputElement).value))}
                                            disabled={savingKey === "attendance_deadline_hour"}
                                            className="h-2 w-full cursor-pointer appearance-none rounded-full bg-navy-100 accent-navy-900 disabled:cursor-not-allowed disabled:opacity-50"
                                        />
                                        <div className="mt-1 flex justify-between text-2xs text-ink-faint">
                                            <span>01:00</span>
                                            <span>12:00</span>
                                            <span>24:00</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                <div className="max-w-2xl">
                    <BrandingSettings />
                </div>
            </div>
        </div>
    );
}