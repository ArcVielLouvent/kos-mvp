import type { Metadata } from "next";
import "./globals.css";
import { ToastProvider } from "@/components/ToastProvider";

export const metadata: Metadata = {
    title: "KOS — Knowledge Operating System",
    description: "Sistem terpusat AI untuk pengetahuan dan operasional perusahaan.",
};

export default function RootLayout({
    children,
}: Readonly<{ children: React.ReactNode }>) {
    return (
        <html lang="id">
            <body className="antialiased">
                <ToastProvider>{children}</ToastProvider>
            </body>
        </html>
    );
}