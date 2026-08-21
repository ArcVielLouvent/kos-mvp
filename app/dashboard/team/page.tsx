"use client";
import { useState, useEffect } from "react";
import { UserPlus } from "lucide-react";
import { TopBar } from "@/components/TopBar";
import { FolderTreePicker } from "@/components/FolderTreePicker";
import { apiJson } from "@/lib/api";
import { useToast } from "@/components/ToastProvider";
import { Copy } from "lucide-react";

export default function TeamPage() {
  const [emails, setEmails] = useState("");
  const [folder, setFolder] = useState("/");
  const [positionTitle, setPositionTitle] = useState("");
  const [managerEmail, setManagerEmail] = useState("");
  const [existingUsers, setExistingUsers] = useState<any[]>([]);
  const [msg, setMsg] = useState("");
  const [isSuccess, setIsSuccess] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [tempPasswords, setTempPasswords] = useState<Record<string, string> | null>(null);
  const { showToast } = useToast();

  useEffect(() => {
    apiJson("/api/team/users")
      .then((data) => setExistingUsers(data.users || []))
      .catch(() => setExistingUsers([]));
  }, []);

  const copyAllAsTable = () => {
    if (!tempPasswords) return;
    const header = "Email\tPassword";
    const rows = Object.entries(tempPasswords).map(([email, pw]) => `${email}\t${pw}`);
    navigator.clipboard.writeText([header, ...rows].join("\n"));
    showToast("Tabel disalin -- tinggal Ctrl+V ke Excel/Sheets.", "success");
  };

  const submit = async () => {
    if (!emails.trim()) {
      setIsSuccess(false);
      setMsg("Masukkan minimal satu email.");
      return;
    }

    setIsLoading(true);
    setMsg("Menyimpan...");
    setTempPasswords(null);

    try {
      const data = await apiJson("/api/team/employees", {
        method: "POST",
        body: JSON.stringify({
          emails,
          folder,
          position_title: positionTitle || undefined,
          manager_email: managerEmail || undefined,
        }),
      });

      setIsSuccess(true);
      setEmails("");
      setPositionTitle("");
      setTempPasswords(data.temporaryPasswords || null);
      setMsg(data.message || "Proses pendaftaran tim selesai.");
    } catch (err: any) {
      setIsSuccess(false);
      setMsg(err.message || "Gagal terhubung dengan server.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <TopBar title="Manajemen Tim" description="Tambahkan karyawan baru dan atur akses folder mereka." />
      <div className="grid grid-cols-1 gap-6 p-8 lg:grid-cols-2">
        {/* Kolom kiri: form pendaftaran */}
        <div className="space-y-4 rounded-[var(--radius-card)] border border-navy-100 bg-white p-6">
          <h3 className="text-sm font-semibold text-ink">Daftarkan Karyawan</h3>

          <div>
            <label className="mb-1 block text-xs font-semibold text-ink-muted">Daftar Email</label>
            <textarea
              value={emails}
              onChange={(e) => setEmails(e.target.value)}
              rows={5}
              placeholder="Satu email per baris untuk daftar massal..."
              className="w-full rounded border px-3 py-2 text-sm focus:outline-none focus:border-navy-500"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-ink-muted">Jabatan (opsional)</label>
            <input
              type="text"
              value={positionTitle}
              onChange={(e) => setPositionTitle(e.target.value)}
              placeholder="Berlaku untuk semua email di atas"
              className="w-full rounded border px-3 py-2 text-sm focus:outline-none focus:border-navy-500"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-ink-muted">Atasan Langsung (opsional)</label>
            <select
              value={managerEmail}
              onChange={(e) => setManagerEmail(e.target.value)}
              className="w-full rounded border border-navy-100 px-3 py-2 text-sm focus:outline-none focus:border-navy-500"
            >
              <option value="">-- Tidak ada / langsung ke Owner --</option>
              {existingUsers.map((u: any) => (
                <option key={u.email} value={u.email}>
                  {u.full_name ? `${u.full_name} (${u.email})` : u.email}
                </option>
              ))}
            </select>
            <p className="mt-1 text-2xs text-ink-faint">
              Menentukan siapa yang melihat laporan/kehadiran karyawan ini -- terpisah dari akses folder.
            </p>
          </div>

          <div>
            <p className="mb-1 text-xs font-semibold text-ink-muted">Folder Akses Terpilih</p>
            <div className="rounded border border-navy-100 bg-navy-50 px-3 py-2 font-mono-data text-sm text-navy-900">
              {folder}
            </div>
            <p className="mt-1 text-2xs text-ink-faint">Pilih folder tujuan lewat panel di sebelah kanan.</p>
          </div>

          <button
            onClick={submit}
            disabled={isLoading}
            className="flex items-center gap-2 rounded bg-navy-900 px-4 py-2 text-sm font-medium text-white hover:bg-navy-800 disabled:opacity-50"
          >
            <UserPlus className="h-4 w-4" /> {isLoading ? "Mendaftarkan..." : "Daftarkan"}
          </button>

          {msg && (
            <p className={`text-sm font-medium ${isSuccess ? "text-green-600" : "text-red-600"}`}>{msg}</p>
          )}

          {tempPasswords && Object.keys(tempPasswords).length > 0 && (
            <div className="mt-4">
              <button
                onClick={copyAllAsTable}
                className="mb-2 flex items-center gap-1.5 rounded border border-navy-100 bg-white px-3 py-1.5 text-xs font-medium text-ink hover:bg-navy-50"
              >
                <Copy className="h-3.5 w-3.5" /> Salin Semua sebagai Tabel
              </button>
              <div className="overflow-hidden rounded border border-navy-100">
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
            </div>
          )}
        </div>

        {/* Kolom kanan: folder tree picker */}
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-ink">Pilih Folder Akses</h3>
          <p className="text-xs text-ink-faint">
            Karyawan yang didaftarkan hanya bisa melihat dokumen di dalam folder ini (dan sub-foldernya).
          </p>
          <FolderTreePicker value={folder} onChange={setFolder} />
        </div>
      </div>
    </div>
  );
}