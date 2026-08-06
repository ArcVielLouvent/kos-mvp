import { Sidebar } from "@/components/Sidebar";

// TODO: Nanti ganti dengan data user asli dari session Supabase saat disambungkan
const MOCK_USER = {
    role: "Admin", // Ganti ke "Karyawan" untuk mengetes tampilan non-admin
    email: "admin@kopinusantara.com",
    companyName: "Kopi Nusantara",
};

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
    return (
        <div className="flex h-screen w-full bg-navy-50 overflow-hidden text-ink">
            {/* Sidebar selalu di kiri */}
            <Sidebar
                role={MOCK_USER.role}
                userEmail={MOCK_USER.email}
                companyName={MOCK_USER.companyName}
            />

            {/* Area Konten Utama - bisa di-scroll secara independen */}
            <main className="flex-1 overflow-y-auto bg-[#fafafa]">
                {children}
            </main>
        </div>
    );
}