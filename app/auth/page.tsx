"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Building2, Mail, Lock, LogIn, UserPlus } from "lucide-react";
import { API_URL } from "@/lib/api";

export default function AuthPage() {
  const router = useRouter();
  const [view, setView] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [company, setCompany] = useState("");

  const [error, setError] = useState("");
  const [msg, setMsg] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(""); setMsg(""); setIsLoading(true);

    try {
      const res = await fetch(`${API_URL}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
      });
      const data = await res.json();

      if (res.ok) {
        localStorage.setItem("kos_user", JSON.stringify(data.user));

        const role = data.user?.role;
        const target = data.user?.must_change_password
          ? "/force-password-change"
          : role === "SuperAdmin" || role === "Admin"
            ? "/dashboard"
            : "/dashboard/chat";

        router.push(target);
      } else {
        const errMsg = data.detail || "Email atau password salah.";
        setError(errMsg);
        alert("Gagal Login: " + errMsg);
      }
    } catch (err: any) {
      setError("Kesalahan jaringan, tidak dapat menghubungi backend.");
      alert("Error Jaringan: Gagal menghubungi server API.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(""); setMsg(""); setIsLoading(true);

    try {
      const res = await fetch(`${API_URL}/api/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ company_name: company, admin_email: email, password })
      });
      const data = await res.json();

      if (res.ok) {
        setMsg(data.message || "Pendaftaran sukses. Silakan login.");
        alert("Pendaftaran berhasil! Silakan Login.");
        setView("login");
        setPassword("");
      } else {
        const errMsg = data.detail || "Gagal mendaftar.";
        setError(errMsg);
        alert("Gagal Daftar: " + errMsg);
      }
    } catch (err: any) {
      setError("Kesalahan jaringan, tidak dapat menghubungi backend.");
      alert("Error Jaringan: Gagal menghubungi server API.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative z-10 flex min-h-screen items-center justify-center bg-navy-50 px-4">
      <div className="relative z-20 w-full max-w-md overflow-hidden rounded-[var(--radius-card)] bg-white shadow-[var(--shadow-panel)]">

        <div className="bg-navy-900 p-8 text-center">
          <h2 className="text-2xl font-bold text-white">Knowledge Operating System</h2>
          <p className="mt-2 text-sm text-navy-300">Sistem terpusat AI perusahaan</p>
        </div>

        <div className="p-8">
          {error && <div className="mb-4 rounded border border-red-100 bg-red-50 p-3 text-sm text-red-600">{error}</div>}
          {msg && <div className="mb-4 rounded border border-green-100 bg-green-50 p-3 text-sm text-green-600">{msg}</div>}

          {view === "login" ? (
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="mb-1 block text-sm font-medium text-ink">Email</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint" />
                  <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className="w-full rounded-[var(--radius-control)] border border-navy-100 py-2.5 pl-10 pr-3 text-sm focus:border-navy-500 focus:outline-none" placeholder="admin@kopinusantara.com" />
                </div>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-ink">Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint" />
                  <input type="password" required value={password} onChange={(e) => setPassword(e.target.value)} className="w-full rounded-[var(--radius-control)] border border-navy-100 py-2.5 pl-10 pr-3 text-sm focus:border-navy-500 focus:outline-none" placeholder="••••••••" />
                </div>
              </div>
              <button type="submit" disabled={isLoading} className="relative z-30 mt-2 flex w-full cursor-pointer items-center justify-center gap-2 rounded-[var(--radius-control)] bg-navy-900 py-2.5 text-sm font-medium text-white hover:bg-navy-800 disabled:opacity-50">
                <LogIn className="h-4 w-4" /> {isLoading ? "Memproses..." : "Login Workspace"}
              </button>
              <button type="button" onClick={() => { setView("register"); setError(""); setMsg(""); }} className="relative z-30 mt-4 block w-full cursor-pointer text-center text-sm font-medium text-navy-700 hover:underline">
                Daftar perusahaan baru (SuperAdmin)
              </button>
            </form>
          ) : (
            <form onSubmit={handleRegister} className="space-y-4">
              <div>
                <label className="mb-1 block text-sm font-medium text-ink">Nama Perusahaan</label>
                <div className="relative">
                  <Building2 className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint" />
                  <input type="text" required value={company} onChange={(e) => setCompany(e.target.value)} className="w-full rounded-[var(--radius-control)] border border-navy-100 py-2.5 pl-10 pr-3 text-sm focus:border-navy-500 focus:outline-none" placeholder="PT Kopi Nusantara" />
                </div>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-ink">Email Admin</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint" />
                  <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className="w-full rounded-[var(--radius-control)] border border-navy-100 py-2.5 pl-10 pr-3 text-sm focus:border-navy-500 focus:outline-none" placeholder="admin@perusahaan.com" />
                </div>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-ink">Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint" />
                  <input type="password" required value={password} onChange={(e) => setPassword(e.target.value)} className="w-full rounded-[var(--radius-control)] border border-navy-100 py-2.5 pl-10 pr-3 text-sm focus:border-navy-500 focus:outline-none" placeholder="••••••••" />
                </div>
              </div>
              <button type="submit" disabled={isLoading} className="relative z-30 mt-2 flex w-full cursor-pointer items-center justify-center gap-2 rounded-[var(--radius-control)] bg-navy-900 py-2.5 text-sm font-medium text-white hover:bg-navy-800 disabled:opacity-50">
                <UserPlus className="h-4 w-4" /> {isLoading ? "Memproses..." : "Buat Perusahaan"}
              </button>
              <button type="button" onClick={() => { setView("login"); setError(""); setMsg(""); }} className="relative z-30 mt-4 block w-full cursor-pointer text-center text-sm font-medium text-navy-700 hover:underline">
                Kembali ke login
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}