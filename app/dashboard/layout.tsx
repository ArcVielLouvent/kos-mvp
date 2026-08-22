"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/Sidebar";
import { NotificationBell } from "@/components/NotificationBell";
import { getStoredUser, KosUser } from "@/lib/api";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
    const router = useRouter();
    const [user, setUser] = useState<KosUser | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const savedUser = getStoredUser();

        if (!savedUser) {
            router.push("/auth");
            return;
        }

        if (savedUser.must_change_password) {
            router.push("/force-password-change");
            return;
        }

        setUser(savedUser);
        setIsLoading(false);
    }, [router]);

    if (isLoading) {
        return (
            <div className="flex h-screen w-full items-center justify-center bg-navy-50">
                <p className="animate-pulse text-sm text-navy-900 font-medium">Memuat Workspace Anda...</p>
            </div>
        );
    }

    return (
        <div className="flex h-screen w-full bg-navy-50 overflow-hidden text-ink">
            <Sidebar
                role={user?.role || "Karyawan"}
                userEmail={user?.email || "user@perusahaan.com"}
                companyName={user?.company_name || "Workspace Perusahaan"}
            />

            <main className="relative flex-1 overflow-y-auto bg-[#fafafa]">
                <NotificationBell />
                {children}
            </main>
        </div>
    );
}