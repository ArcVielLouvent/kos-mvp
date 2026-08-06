"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/Sidebar";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
    const router = useRouter();
    const [user, setUser] = useState<{ role: string; email: string; company_id: string } | None>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        // Ambil data user asli yang disimpan saat sukses login kemarin
        const savedUser = localStorage.getItem("kos_user");

        if (!savedUser) {
            // Jika tidak ada data login, paksa tendang ke halaman auth
            router.push("/auth");
            return;
        }

        try {
            setUser(JSON.parse(savedUser));
        } catch (e) {
            localStorage.removeItem("kos_user");
            router.push("/auth");
        } finally {
            setIsLoading(false);
        }
    }, [router]);

    // Tampilkan loading screen sementara sistem memeriksa status login
    if (isLoading) {
        return (
            <div className="flex h-screen w-full items-center justify-center bg-navy-50">
                <p className="animate-pulse text-sm text-navy-900 font-medium">Memuat Workspace Anda...</p>
            </div>
        );
    }

    return (
        <div className="flex h-screen w-full bg-navy-50 overflow-hidden text-ink">
            {/* Sidebar menggunakan data USER ASLI hasil login */}
            <Sidebar
                role={user?.role || "Karyawan"}
                userEmail={user?.email || "user@perusahaan.com"}
                companyName="Workspace Perusahaan" // Anda bisa menambahkan field company_name di objek user API jika diperlukan
            />

            {/* Area Konten Utama */}
            <main className="flex-1 overflow-y-auto bg-[#fafafa]">
                {children}
            </main>
        </div>
    );
}
