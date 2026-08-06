"use client";
import { UserPlus } from "lucide-react";
import { TopBar } from "@/components/TopBar";

// Sesuai db.py:add_users_bulk versi main -- cuma bisa tambah Karyawan,
// belum ada "Tambah Admin" / level permission (itu fitur branch dev).
export default function TeamPage() {
    return (
        <div>
            <TopBar title="Manajemen Tim" description="Tambahkan karyawan baru ke workspace." />
            <div className="p-8">
                <div className="max-w-lg space-y-4 rounded-[var(--radius-card)] border border-navy-100 bg-white p-6 shadow-[var(--shadow-card)]">
                    <label className="block">
                        <span className="mb-1.5 block text-sm font-medium text-ink">
                            Daftar email karyawan (pisah baris)
                        </span>
                        <textarea
                            rows={5}
                            placeholder={"karyawan1@kopinusantara.com\nkaryawan2@kopinusantara.com"}
                            className="w-full rounded-[var(--radius-control)] border border-navy-100 px-3 py-2.5 text-sm placeholder:text-ink-faint focus:border-navy-500 focus:outline-none"
                        />
                    </label>
                    <label className="block">
                        <span className="mb-1.5 block text-sm font-medium text-ink">Folder Akses</span>
                        <select className="w-full rounded-[var(--radius-control)] border border-navy-100 px-3 py-2.5 text-sm focus:border-navy-500 focus:outline-none">
                            <option>/</option>
                            <option>/SOP & Operasional/</option>
                            <option>/Keuangan/</option>
                        </select>
                    </label>
                    <button className="flex items-center gap-2 rounded-[var(--radius-control)] bg-navy-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-navy-800">
                        <UserPlus className="h-4 w-4" /> Daftarkan Karyawan
                    </button>
                </div>
            </div>
        </div>
    );
}