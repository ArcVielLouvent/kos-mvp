"use client";
import { useState } from "react";
import { UserPlus } from "lucide-react";
import { TopBar } from "@/components/TopBar";

// API URL dinamis (Vercel otomatis pakai domain produksi kosong, lokal pakai localhost)
const API_URL = typeof window !== "undefined" && window.location.hostname === "localhost"
  ? "http://localhost:8000"
  : "";

export default function TeamPage() {
  const [emails, setEmails] = useState("");
  const [folder, setFolder] = useState("/");
  const [msg, setMsg] = useState("");
  const [isSuccess, setIsSuccess] = useState(true);

  const submit = async () => {
    setMsg("Menyimpan...");

    // Ambil token JWT session user yang tersimpan dari localStorage saat login
    const token = typeof window !== "undefined" ? localStorage.getItem("sb-access-token") || localStorage.getItem("supabase_token") : null;

    try {
      const res = await fetch(`${API_URL}/api/team`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}` // Identitas pengirim otomatis terdeteksi di backend
        },
        body: JSON.stringify({ emails, folder }) // Bersih tanpa parameter user_id manual
      });

      const data = await res.json();

      if (res.ok && data.status === "success") {
        setIsSuccess(true);
        setEmails(""); // Bersihkan input teks jika sukses
      } else {
        setIsSuccess(false);
      }
      setMsg(data.message || "Proses pendaftaran tim selesai.");
    } catch (err: any) {
      setIsSuccess(false);
      setMsg("Error: Gagal terhubung dengan server.");
    }
  };

  return (
    <div>
      <TopBar title="Manajemen Tim" description="Tambahkan karyawan baru." />
      <div className="p-8">
        <div className="max-w-lg space-y-4 rounded-[var(--radius-card)] border border-navy-100 bg-white p-6">
          <textarea
            value={emails}
            onChange={e => setEmails(e.target.value)}
            rows={4}
            placeholder="Masukkan email karyawan (pisahkan dengan baris baru untuk mendaftarkan massal)..."
            className="w-full rounded border px-3 py-2 text-sm focus:outline-none focus:border-navy-500"
          />
          <select value={folder} onChange={e => setFolder(e.target.value)} className="w-full rounded border px-3 py-2 text-sm focus:outline-none focus:border-navy-500">
            <option value="/">/</option>
            <option value="/SOP/">/SOP/</option>
          </select>
          <button onClick={submit} className="flex gap-2 rounded bg-navy-900 px-4 py-2 text-sm font-medium text-white hover:bg-navy-800">
            <UserPlus className="h-4 w-4" /> Daftarkan
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
