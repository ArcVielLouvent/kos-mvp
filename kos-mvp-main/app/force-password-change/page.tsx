"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Lock, ShieldCheck } from "lucide-react";
import { apiJson, getStoredUser, setStoredUser } from "@/lib/api";

export default function ForcePasswordChangePage() {
    const router = useRouter();
    const [checked, setChecked] = useState(false);
    const [newPassword, setNewPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [error, setError] = useState("");
    const [isLoading, setIsLoading] = useState(false);

    const redirectHome = (role?: string) => {
        router.replace(role === "SuperAdmin" || role === "Admin" ? "/dashboard" : "/dashboard/chat");
    };

    useEffect(() => {
        const user = getStoredUser();
        if (!user) {
            router.replace("/auth");
            return;
        }
        if (!user.must_change_password) {
            redirectHome(user.role);
            return;
        }
        setChecked(true);
    }, [router]);

    const submit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");

        if (newPassword.length < 6) {
            setError("Password minimal 6 karakter.");
            return;
        }
        if (newPassword !== confirmPassword) {
            setError("Konfirmasi password tidak cocok.");
            return;
        }

        setIsLoading(true);
        try {
            await apiJson("/api/profile/password", {
                method: "POST",
                body: JSON.stringify({ new_password: newPassword }),
            });

            const user = getStoredUser();
            if (user) {
                setStoredUser({ ...user, must_change_password: false });
                redirectHome(user.role);
            } else {
                router.replace("/auth");
            }
        } catch (err: any) {
            setError(err.message || "Gagal memperbarui password.");
        } finally {
            setIsLoading(false);
        }
    };

    if (!checked) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-navy-50">
                <p className="text-sm text-navy-500">Memeriksa status akun...</p>
            </div>
        );
    }

    return (
        <div className="flex min-h-screen items-center justify-center bg-navy-50 px-4">
            <div className="w-full max-w-md overflow-hidden rounded-[var(--radius-card)] bg-white shadow-[var(--shadow-panel)]">
                <div className="bg-navy-900 p-8 text-center">
                    <span className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-white/10">
                        <ShieldCheck className="h-6 w-6 text-white" />
                    </span>
                    <h2 className="text-xl font-bold text-white">Buat Password Baru</h2>
                    <p className="mt-2 text-sm text-navy-300">
                        Demi keamanan, Anda wajib mengganti password sementara sebelum melanjutkan.
                    </p>
                </div>

                <form onSubmit={submit} className="space-y-4 p-8">
                    {error && (
                        <div className="rounded border border-red-100 bg-red-50 p-3 text-sm text-red-600">{error}</div>
                    )}

                    <div>
                        <label className="mb-1 block text-sm font-medium text-ink">Password Baru</label>
                        <div className="relative">
                            <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint" />
                            <input
                                type="password"
                                required
                                value={newPassword}
                                onChange={(e) => setNewPassword(e.target.value)}
                                className="w-full rounded-[var(--radius-control)] border border-navy-100 py-2.5 pl-10 pr-3 text-sm focus:border-navy-500 focus:outline-none"
                                placeholder="Minimal 6 karakter"
                            />
                        </div>
                    </div>

                    <div>
                        <label className="mb-1 block text-sm font-medium text-ink">Ulangi Password Baru</label>
                        <div className="relative">
                            <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint" />
                            <input
                                type="password"
                                required
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                className="w-full rounded-[var(--radius-control)] border border-navy-100 py-2.5 pl-10 pr-3 text-sm focus:border-navy-500 focus:outline-none"
                                placeholder="••••••••"
                            />
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={isLoading}
                        className="mt-2 flex w-full items-center justify-center gap-2 rounded-[var(--radius-control)] bg-navy-900 py-2.5 text-sm font-medium text-white hover:bg-navy-800 disabled:opacity-50"
                    >
                        {isLoading ? "Menyimpan..." : "Simpan & Lanjutkan"}
                    </button>
                </form>
            </div>
        </div>
    );
}