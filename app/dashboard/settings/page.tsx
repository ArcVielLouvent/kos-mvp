"use client";
import { useState } from "react";
import { TopBar } from "@/components/TopBar";

const API_URL = typeof window !== "undefined" && window.location.hostname === "localhost"
    ? "http://localhost:8000"
    : "";

export default function SettingsPage() {
    const [companyName, setCompanyName] = useState("");
    const [msg, setMsg] = useState("");
    const [isSuccess, setIsSuccess] = useState(true);

    const submit = async () => {
        if (!companyName.trim()) return;
        setMsg("Menyimpan...");

        const token = typeof window !== "undefined" ? localStorage.getItem("sb-access-token") || localStorage.getItem("supabase_token") : null;

        try {
            const res = await fetch(`${API_URL}/api/settings`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({ companyName })
            });
            const data = await res.json();

            setIsSuccess(res.ok);
            setMsg(data.message || "Pengaturan berhasil diperbarui.");
        } catch (err) {
            setIsSuccess(false);
            setMsg("Error: Gagal memperbarui pengaturan ke server.");
        }
    };

    return (
        <div>
            <TopBar title="Pengaturan" description="Informasi perusahaan." />
            <div className="p-8">
                <div className="max-w-lg space-y-4 rounded-[var(--radius-card)] border border-navy-100 bg-white p-6">
                    <label className="text-xs font-semibold text-ink-muted block mb-1">Nama Perusahaan / Workspace</label>
                    <input
                        value={companyName}
                        onChange={e => setCompanyName(e.target.value)}
                        placeholder="Masukkan nama perusahaan baru..."
                        className="w-full rounded border px-3 py-2 text-sm focus:outline-none focus:border-navy-500"
                    />
                    <button onClick={submit} className="rounded bg-navy-900 px-4 py-2 text-sm font-medium text-white hover:bg-navy-800">
                        Simpan Perubahan
                    </button>
                    {msg && (
                        <p className={`text-sm font-medium ${isSuccess ? "text-green-600" : "text-red-600"}`}>
                            {msg}
                        </p>
                    )}
                </div>
            </div>
        </div>
    );
}
