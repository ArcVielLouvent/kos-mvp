"use client";
import { KeyRound, Briefcase } from "lucide-react";
import { TopBar } from "@/components/TopBar";

export default function ProfilePage() {
    return (
        <div>
            <TopBar title="Profil Saya" description="Informasi akun dan keamanan Anda." />
            <div className="grid max-w-3xl grid-cols-1 gap-6 p-8 lg:grid-cols-2">
                <div className="space-y-5 rounded-[var(--radius-card)] border border-navy-100 bg-white p-6 shadow-[var(--shadow-card)]">
                    <div className="flex items-center gap-3">
                        <span className="flex h-12 w-12 items-center justify-center rounded-full bg-navy-100 text-sm font-semibold text-navy-700">
                            AD
                        </span>
                        <div>
                            <p className="text-sm font-semibold text-ink">admin@kopinusantara.com</p>
                            <p className="text-xs text-ink-faint">Admin</p>
                        </div>
                    </div>
                    <Field label="Jabatan" icon={Briefcase} placeholder="mis. Owner / Direktur Operasional" />
                    <button className="rounded-[var(--radius-control)] bg-navy-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-navy-800">
                        Simpan Perubahan
                    </button>
                </div>
                <div className="space-y-5 rounded-[var(--radius-card)] border border-navy-100 bg-white p-6 shadow-[var(--shadow-card)]">
                    <div className="flex items-center gap-2">
                        <KeyRound className="h-4 w-4 text-ink-muted" />
                        <p className="text-sm font-semibold text-ink">Ganti Password</p>
                    </div>
                    <Field label="Password Baru" type="password" placeholder="••••••••" />
                    <Field label="Ulangi Password Baru" type="password" placeholder="••••••••" />
                    <button className="rounded-[var(--radius-control)] border border-navy-100 px-4 py-2.5 text-sm font-medium text-ink hover:bg-navy-50">
                        Perbarui Password
                    </button>
                </div>
            </div>
        </div>
    );
}

function Field({
    label,
    icon: Icon,
    type = "text",
    placeholder,
}: {
    label: string;
    icon?: typeof KeyRound;
    type?: string;
    placeholder?: string;
}) {
    return (
        <label className="block">
            <span className="mb-1.5 flex items-center gap-1.5 text-sm font-medium text-ink">
                {Icon && <Icon className="h-3.5 w-3.5 text-ink-faint" />}
                {label}
            </span>
            <input
                type={type}
                placeholder={placeholder}
                className="w-full rounded-[var(--radius-control)] border border-navy-100 px-3 py-2.5 text-sm placeholder:text-ink-faint focus:border-navy-500 focus:outline-none"
            />
        </label>
    );
}