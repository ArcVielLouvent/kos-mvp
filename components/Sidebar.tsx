"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { LayoutDashboard, MessageSquare, FolderTree, Users, Settings, User, LogOut } from "lucide-react";
import { cn } from "@/lib/utils";

export function Sidebar({ role, userEmail, companyName }: { role: string; userEmail: string; companyName: string }) {
  const pathname = usePathname();
  const router = useRouter();

  const handleLogout = () => {
    localStorage.removeItem("kos_user");
    router.push("/auth");
  };

  const navItems = [
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "Chat KOS", href: "/dashboard/chat", icon: MessageSquare },
    { name: "File Manager", href: "/dashboard/files", icon: FolderTree },
    { name: "Manajemen Tim", href: "/dashboard/team", icon: Users },
  ];

  return (
    <div className="flex w-64 shrink-0 flex-col border-r border-navy-100 bg-white">
      <div className="flex h-16 items-center border-b border-navy-100 px-6">
        <h1 className="font-display text-lg font-bold tracking-tight text-navy-900">
          KOS <span className="font-normal text-ink-muted">Workspace</span>
        </h1>
      </div>

      <nav className="flex-1 space-y-1 p-4">
        <div className="mb-4 px-3 text-xs font-semibold uppercase tracking-wider text-ink-faint">Menu Utama</div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;
          return (
            <Link key={item.href} href={item.href} className={cn("group flex items-center gap-3 rounded-[var(--radius-control)] px-3 py-2 text-sm font-medium transition-colors", isActive ? "bg-navy-50 text-navy-900" : "text-ink-muted hover:bg-navy-50 hover:text-ink")}>
              <Icon className={cn("h-4 w-4", isActive ? "text-navy-700" : "text-ink-faint group-hover:text-ink-muted")} />
              {item.name}
            </Link>
          );
        })}

        {role === "Admin" || role === "SuperAdmin" ? (
          <>
            <div className="mb-4 mt-6 px-3 text-xs font-semibold uppercase tracking-wider text-ink-faint">Admin Panel</div>
            <Link href="/dashboard/settings" className={cn("group flex items-center gap-3 rounded-[var(--radius-control)] px-3 py-2 text-sm font-medium transition-colors", pathname === "/dashboard/settings" ? "bg-navy-50 text-navy-900" : "text-ink-muted hover:bg-navy-50 hover:text-ink")}>
              <Settings className={cn("h-4 w-4", pathname === "/dashboard/settings" ? "text-navy-700" : "text-ink-faint group-hover:text-ink-muted")} />
              Pengaturan
            </Link>
          </>
        ) : null}
      </nav>

      <div className="border-t border-navy-100 p-4">
        <div className="mb-3 flex items-center gap-3 px-2">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-navy-900 text-xs font-semibold text-white">
            {userEmail ? userEmail.slice(0, 2).toUpperCase() : "US"}
          </span>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-ink">{userEmail}</p>
            <p className="truncate text-xs text-ink-faint">{companyName} · {role}</p>
          </div>
        </div>
        <div className="flex gap-1">
          <Link href="/dashboard/profile" className="flex flex-1 items-center justify-center gap-2 rounded-[var(--radius-control)] px-2 py-1.5 text-xs font-medium text-ink-muted hover:bg-navy-50 hover:text-ink">
            <User className="h-3.5 w-3.5" /> Profil
          </Link>
          <button onClick={handleLogout} className="flex flex-1 items-center justify-center gap-2 rounded-[var(--radius-control)] px-2 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50">
            <LogOut className="h-3.5 w-3.5" /> Keluar
          </button>
        </div>
      </div>
    </div>
  );
}
