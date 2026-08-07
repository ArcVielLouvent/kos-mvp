"use client";
import { useState, useEffect } from "react";
import { TopBar } from "@/components/TopBar";

const API_URL = typeof window !== "undefined" && window.location.hostname === "localhost"
  ? "http://localhost:8000"
  : "";

export default function ProfilePage() {
  const [email, setEmail] = useState("Memuat profil...");
  const [password, setPassword] = useState("");
  const [msg, setMsg] = useState("");
  const [isSuccess, setIsSuccess] = useState(true);

  // Ambil data profil aktif secara dinamis dari backend saat halaman dimuat
  useEffect(() => {
    const token = typeof window !== "undefined" ? localStorage.getItem("sb-access-token") || localStorage.getItem("supabase_token") : null;

    fetch(`${API_URL}/api/auth/me`, { // Sesuaikan route GET profile/me di backend Anda jika berbeda
      method: "GET",
      headers: {
        "Authorization": `Bearer ${token}`
      }
    })
      .then(res => res.json())
      .then(data => {
        if (data.email) setEmail(data.email);
      })
      .catch(() => setEmail("Gagal memuat detail akun."));
  }, []);

  const submit = async () => {
    if (!password) {
      setIsSuccess(false);
      setMsg("Silakan isi password baru terlebih dahulu.");
      return;
    }

    setMsg("Menyimpan...");
    const token = typeof window !== "undefined" ? localStorage.getItem("sb-access-token") || localStorage.getItem("supabase_token") : null;

    try {
      const res = await fetch(`${API_URL}/api/profile`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ password })
      });
      const data = await res.json();

      setIsSuccess(res.ok);
      setMsg(data.message || "Profil sukses diperbarui.");
      if (res.ok) setPassword(""); // Reset kolom input password jika sukses
    } catch (err) {
      setIsSuccess(false);
      setMsg("Error: Gagal mengirim instruksi pembaruan.");
    }
  };

  return (
    <div>
      <TopBar title="Profil Saya" />
      <div className="p-8">
        <div className="max-w-lg space-y-4 rounded-[var(--radius-card)] border border-navy-100 bg-white p-6">
          <div>
            <label className="text-xs font-semibold text-ink-muted block mb-1">Email Aktif</label>
            <p className="text-sm font-semibold bg-navy-50 px-3 py-2 rounded border border-navy-100 text-ink">{email}</p>
          </div>
          <div>
            <label className="text-xs font-semibold text-ink-muted block mb-1">Ubah Keamanan</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="Masukkan password baru akun Anda..."
              className="w-full rounded border px-3 py-2 text-sm focus:outline-none focus:border-navy-500"
            />
          </div>
          <button onClick={submit} className="rounded bg-navy-900 px-4 py-2 text-sm font-medium text-white hover:bg-navy-800">
            Update Profil
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
