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

    // Batas waktu diedit bebas dulu di state lokal (time picker HH:MM),
    // BARU dikirim ke server saat tombol "Simpan" diklik -- BEDA dari
    // toggle di atas yang auto-save, supaya user yakin dulu jamnya benar
    // sebelum ke-apply (jam 17:00 vs 07:00 gampang salah pencet di time picker).
    const [deadlineDraft, setDeadlineDraft] = useState<string | null>(null); // format "HH:MM"
    const [deadlineSaveMsg, setDeadlineSaveMsg] = useState<string | null>(null);
    useEffect(() => {
        if (settings && deadlineDraft === null) {
            const h = String(settings.attendance_deadline_hour ?? 24).padStart(2, "0");
            const m = String(settings.attendance_deadline_minute ?? 0).padStart(2, "0");
            setDeadlineDraft(`${h === "24" ? "23" : h}:${h === "24" ? "59" : m}`);
        }
    }, [settings]);

    const isDeadlineDirty =
        settings && deadlineDraft &&
        deadlineDraft !== `${String(settings.attendance_deadline_hour ?? 24).padStart(2, "0")}:${String(settings.attendance_deadline_minute ?? 0).padStart(2, "0")}`;

    const saveDeadline = async () => {
        if (!settings || !deadlineDraft) return;
        const [hStr, mStr] = deadlineDraft.split(":");
        const hour = Number(hStr), minute = Number(mStr);
        setSavingKey("attendance_deadline_hour");
        setDeadlineSaveMsg(null);
        try {
            const updated = await apiJson("/api/settings/company", {
                method: "PATCH",
                body: JSON.stringify({ attendance_deadline_hour: hour, attendance_deadline_minute: minute }),
            });
            setSettings(updated.settings);
            setDeadlineSaveMsg("Tersimpan.");
        } catch (e: any) {
            setDeadlineSaveMsg(e.message || "Gagal menyimpan.");
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
                                        <p className="text-sm font-medium text-ink">Batas Waktu Lapor Harian</p>
                                        <p className="mb-3 text-xs text-ink-faint">
                                            Jam berapa karyawan dianggap TERLAMBAT kalau belum isi Form Kehadiran/Lapor Kerjaan
                                            hari itu (jam WIB). Setelah lewat jam ini, sistem mulai mengirim pengingat.
                                        </p>
                                        <div className="flex items-center gap-2">
                                            <input
                                                type="time"
                                                value={deadlineDraft ?? "23:59"}
                                                onChange={(e) => setDeadlineDraft(e.target.value)}
                                                disabled={savingKey === "attendance_deadline_hour"}
                                                className="rounded-[var(--radius-control)] border border-navy-100 bg-white px-3 py-2 text-sm text-ink disabled:opacity-50"
                                            />
                                            <button
                                                onClick={saveDeadline}
                                                disabled={!isDeadlineDirty || savingKey === "attendance_deadline_hour"}
                                                className="rounded-[var(--radius-control)] bg-navy-900 px-4 py-2 text-xs font-semibold text-white hover:bg-navy-800 disabled:cursor-not-allowed disabled:opacity-40"
                                            >
                                                {savingKey === "attendance_deadline_hour" ? "Menyimpan..." : "Simpan"}
                                            </button>
                                            {deadlineSaveMsg && !isDeadlineDirty && (
                                                <span className="text-2xs font-medium text-green-600">{deadlineSaveMsg}</span>
                                            )}
                                        </div>
                                        {isDeadlineDirty && (
                                            <p className="mt-1.5 text-2xs text-amber-600">Belum disimpan -- klik "Simpan" supaya perubahan berlaku.</p>
                                        )}
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