"use client";
import { useState } from "react";
import { UserPlus } from "lucide-react";
import { TopBar } from "@/components/TopBar";

export default function TeamPage() {
  const [emails, setEmails] = useState("");
  const [folder, setFolder] = useState("/");
  const [msg, setMsg] = useState("");

  const submit = async () => {
    setMsg("Menyimpan...");
    const res = await fetch("/api/team", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ emails, folder })
    });
    const data = await res.json();
    setMsg(data.message);
  };

  return (
    <div>
      <TopBar title="Manajemen Tim" description="Tambahkan karyawan baru." />
      <div className="p-8">
        <div className="max-w-lg space-y-4 rounded-[var(--radius-card)] border border-navy-100 bg-white p-6">
          <textarea value={emails} onChange={e => setEmails(e.target.value)} rows={4} placeholder="Email karyawan..." className="w-full rounded border px-3 py-2 text-sm" />
          <select value={folder} onChange={e => setFolder(e.target.value)} className="w-full rounded border px-3 py-2 text-sm">
            <option value="/">/</option><option value="/SOP/">/SOP/</option>
          </select>
          <button onClick={submit} className="flex gap-2 rounded bg-navy-900 px-4 py-2 text-white"><UserPlus className="h-4 w-4"/> Daftarkan</button>
          {msg && <p className="text-sm font-medium text-green-600">{msg}</p>}
        </div>
      </div>
    </div>
  );
}
