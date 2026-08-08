"use client";
import { useState } from "react";
import { TopBar } from "@/components/TopBar";
import { getStoredUser, apiJson } from "@/lib/api";
import { Lock, Mail, Shield, Building2, FolderOpen } from "lucide-react";

export default function ProfilePage() {
    const user = getStoredUser();
    const [newPassword, setNewPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [msg, setMsg] = useState("");
    const [isSuccess, setIsSuccess] = useState(true);
    const [isLoading, setIsLoading] = useState(false);

    const submit = async () => {
        setMsg("");

        if (newPassword.length < 6) {
            setIsSuccess(false);
            setMsg("Password minimal 6 karakter.");
            return;
        }
        if (newPassword !== confirmPassword) {
            setIsSuccess(false);
            setMsg("Konfirmasi password tidak cocok.");
            return;
        }

        setIsLoading(true);
        try {
            const data = await apiJson("/api/profile/password", {
                method: "POST",
                body: JSON.stringify({ new_password: newPassword }),
            });
            setIsSuccess(true);
            setMsg(data.message || "Password berhasil diperbarui.");
            setNewPassword("");
            setConfirmPassword("");
        } catch (err: any) {
            setIsSuccess(false);
            setMsg(err.message || "Gagal memperbarui password.");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div>
            <TopBar title="Profil Saya" description="Informasi akun dan keamanan." />
            <div className="space-y-6 p-8">
                <div className="max-w-lg space-y-4 rounded-[var(--radius-card)] border border-navy-100 bg-white p-6">
                    <h3 className="text-sm font-semibold text-ink">Informasi Akun</h3>

                    <div className="space-y-3">
                        <div className="flex items-center gap-3">
                            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-navy-50">
                                <Mail className="h-4 w-4 text-navy-700" />
                            </span>
                            <div>
                                <p className="text-2xs text-ink-faint">Email</p>
                                <p className="text-sm font-medium text-ink">{user?.email}</p>
                            </div>
                        </div>

                        <div className="flex items-center gap-3">
                            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-navy-50">
                                <Shield className="h-4 w-4 text-navy-700" />
                            </span>
                            <div>
                                <p className="text-2xs text-ink-faint">Peran</p>
                                <p className="text-sm font-medium text-ink">
                                    {user?.role}{user?.position_title ? ` · ${user.position_title}` : ""}
                                </p>
                            </div>
                        </div>

                        <div className="flex items-center gap-3">
                            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-navy-50">
                                <Building2 className="h-4 w-4 text-navy-700" />
                            </span>
                            <div>
                                <p className="text-2xs text-ink-faint">Perusahaan</p>
                                <p className="text-sm font-medium text-ink">{user?.company_name || "-"}</p>
                            </div>
                        </div>

                        <div className="flex items-center gap-3">
                            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-navy-50">
                                <FolderOpen className="h-4 w-4 text-navy-700" />
                            </span>
                            <div>
                                <p className="text-2xs text-ink-faint">Cakupan Folder</p>
                                <p className="font-mono-data text-sm font-medium text-ink">{user?.folder_access}</p>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="max-w-lg space-y-4 rounded-[var(--radius-card)] border border-navy-100 bg-white p-6">
                    <h3 className="text-sm font-semibold text-ink">Ganti Password</h3>

                    <div>
                        <label className="mb-1 block text-xs font-semibold text-ink-muted">Password Baru</label>
                        <div className="relative">
                            <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint" />
                            <input
                                type="password"
                                value={newPassword}
                                onChange={(e) => setNewPassword(e.target.value)}
                                placeholder="Minimal 6 karakter"
                                className="w-full rounded-[var(--radius-control)] border border-navy-100 py-2.5 pl-10 pr-3 text-sm focus:border-navy-500 focus:outline-none"
                            />
                        </div>
                    </div>

                    <div>
                        <label className="mb-1 block text-xs font-semibold text-ink-muted">Ulangi Password Baru</label>
                        <div className="relative">
                            <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint" />
                            <input
                                type="password"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                placeholder="••••••••"
                                className="w-full rounded-[var(--radius-control)] border border-navy-100 py-2.5 pl-10 pr-3 text-sm focus:border-navy-500 focus:outline-none"
                            />
                        </div>
                    </div>

                    <button
                        onClick={submit}
                        disabled={isLoading}
                        className="rounded bg-navy-900 px-4 py-2 text-sm font-medium text-white hover:bg-navy-800 disabled:opacity-50"
                    >
                        {isLoading ? "Menyimpan..." : "Update Password"}
                    </button>

                    {msg && (
                        <p className={`text-sm font-medium ${isSuccess ? "text-green-600" : "text-red-600"}`}>{msg}</p>
                    )}
                </div>
            </div>
        </div>
    );
}