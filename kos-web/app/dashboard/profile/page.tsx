"use client";
import { useState } from "react";
import { TopBar } from "@/components/TopBar";

export default function ProfilePage() {
  const [msg, setMsg] = useState("");

  const submit = async () => {
    setMsg("Menyimpan...");
    const res = await fetch("/api/profile", { method: "POST" });
    const data = await res.json();
    setMsg(data.message);
  };

  return (
    <div>
      <TopBar title="Profil Saya" />
      <div className="p-8">
        <div className="max-w-lg space-y-4 rounded-[var(--radius-card)] border border-navy-100 bg-white p-6">
          <p className="text-sm font-semibold">admin@kopinusantara.com</p>
          <input type="password" placeholder="Password Baru" className="w-full rounded border px-3 py-2 text-sm" />
          <button onClick={submit} className="rounded border px-4 py-2 text-sm">Update Profil</button>
          {msg && <p className="text-sm font-medium text-green-600">{msg}</p>}
        </div>
      </div>
    </div>
  );
}
