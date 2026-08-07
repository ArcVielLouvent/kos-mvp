"use client";
import { useState, useEffect } from "react";
import { UserPlus, Loader2 } from "lucide-react";
import { TopBar } from "@/components/TopBar";
import { apiJson } from "@/lib/api";

export default function TeamPage() {
  const [emails, setEmails] = useState("");
  const [folder, setFolder] = useState("/");
  const [positionTitle, setPositionTitle] = useState("");
  const [msg, setMsg] = useState("");
  const [isSuccess, setIsSuccess] = useState(true);
  const [tempPasswords, setTempPasswords] = useState<Record<string, string> | null>(null);

  // State baru untuk menampung daftar folder dinamis dari database
  const [availableFolders, setAvailableFolders] = useState<string[]>(["/"]);
  const [isLoadingFolders, setIsLoadingFolders] = useState(true);

  // Ambil daftar folder asli dari backend secara otomatis saat halaman dibuka
  useEffect(() => {
    const fetchFolders = async () => {
      try {
        // Memanggil endpoint pembaca root folder (/) untuk melihat subfolder yang tersedia
        const result = await apiJson("/api/folders/children?path=/");
        if (result && result.children) {
          const folderPaths = result.children.map((c: any) => c.path);
          // Gabungkan root (/) dengan folder anak yang ditemukan di cloud
          setAvailableFolders(["/", ...folderPaths]);
        }
      } catch (e) {
        console.error("Gagal memuat daftar folder otomatis:", e);
      } finally {
        setIsLoadingFolders(false);
      }
    };
    fetchFolders();
  }, []);

  const submit = async () => {
    setMsg("Menyimpan...");
    setTempPasswords(null);

    try {
      const data = await apiJson("/api/team/employees", {
        method: "POST",
        body: JSON.stringify({ emails, folder, position_title: positionTitle || undefined }),
      });

      setIsSuccess(true);
      setEmails("");
      setPositionTitle("");
      setTempPasswords(data.temporaryPasswords || null);
      setMsg(data.message || "Proses pendaftaran tim selesai.");
    } catch (err: any) {
      setIsSuccess(false);
      setMsg(err.message || "Gagal terhubung dengan server.");
    }
  };

  return (
    <div>
      <TopBar title="Manajemen Tim" description="Tambahkan karyawan baru." />
      <div className="p-8">
        <div className="max-w-lg space-y-4 rounded-[var(--radius-card)] border border-navy-100 bg-white p-6">
          <textarea
            value={emails}
            onChange={(e) => setEmails(e.target.value)}
            rows={4}
            placeholder="Masukkan email karyawan (pisahkan dengan baris baru untuk mendaftarkan massal)..."
            className="w-full rounded border px-3 py-2 text-sm focus:outline-none focus:border-navy-500"
          />
          <input
            type="text"
            value={positionTitle}
            onChange={(e) => setPositionTitle(e.target.value)}
            placeholder="Jabatan (opsional, berlaku untuk semua email di atas)"
            className="w-full rounded border px-3 py-2 text-sm focus:outline-none focus:border-navy-500"
          />

          {/* MENGUBAH SELECT MENJADI DINAMIS BERDASARKAN ISI SUPABASE */}
          <div className="space-y-1">
            <label className="text-2xs font-semibold text-ink-muted">Pilih Hak Akses Direktori Folder</label>
            <select
              value={folder}
              onChange={(e) => setFolder(e.target.value)}
              disabled={isLoadingFolders}
              className="w-full rounded border px-3 py-2 text-sm focus:outline-none focus:border-navy-500 bg-white disabled:opacity-50"
            >
              {availableFolders.map((pathStr) => (
                <option key={pathStr} value={pathStr}>{pathStr}</option>
              ))}
            </select>
          </div>

          <button onClick={submit} className="flex gap-2 rounded bg-navy-900 px-4 py-2 text-sm font-medium text-white hover:bg-navy-800">
            <UserPlus className="h-4 w-4" /> Daftarkan
          </button>

          {msg && (
            <p className={`text-sm font-medium ${isSuccess ? "text-green-600" : "text-red-600"}`}>{msg}</p>
          )}

          {tempPasswords && Object.keys(tempPasswords).length > 0 && (
            <div className="overflow-hidden rounded border border-navy-100 mt-4">
              <table className="w-full text-xs">
                <thead className="bg-navy-50">
                  <tr>
                    <th className="px-3 py-2 text-left font-medium text-ink-muted">Email</th>
                    <th className="px-3 py-2 text-left font-medium text-ink-muted">Password sementara</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(tempPasswords).map(([email, pw]) => (
                    <tr key={email} className="border-t border-navy-100">
                      <td className="px-3 py-2">{email}</td>
                      <td className="px-3 py-2 font-mono-data">{pw}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
