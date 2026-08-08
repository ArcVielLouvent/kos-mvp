"use client";
import { TopBar } from "@/components/TopBar";
import { getStoredUser } from "@/lib/api";
import { Building2, Users, Image as ImageIcon, FileText, Clock } from "lucide-react";

export default function SettingsPage() {
    const user = getStoredUser();

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