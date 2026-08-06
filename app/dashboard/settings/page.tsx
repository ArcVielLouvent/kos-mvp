"use client";
import { useState } from "react";
import { TopBar } from "@/components/TopBar";

export default function SettingsPage() {
    const [companyName, setCompanyName] = useState("Kopi Nusantara");
    const [msg, setMsg] = useState("");

    const submit = async () => {
        setMsg("Menyimpan...");
        const res = await fetch("/api/settings", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ companyName })
        });
        const data = await res.json();
        setMsg(data.message);
    };

    return (
        <div>
            <TopBar title="Pengaturan" description="Informasi perusahaan." />
            <div className="p-8">
                <div className="max-w-lg space-y-4 rounded-[var(--radius-card)] border border-navy-100 bg-white p-6">
                    <input value={companyName} onChange={e => setCompanyName(e.target.value)} className="w-full rounded border px-3 py-2 text-sm" />
                    <button onClick={submit} className="rounded bg-navy-900 px-4 py-2 text-white">Simpan Perubahan</button>
                    {msg && <p className="text-sm font-medium text-green-600">{msg}</p>}
                </div>
            </div>
        </div>
    );
}
