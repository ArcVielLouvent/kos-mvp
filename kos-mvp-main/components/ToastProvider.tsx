"use client";
import { createContext, useContext, useState, useCallback, ReactNode } from "react";
import { CheckCircle2, AlertCircle, Info } from "lucide-react";
import { cn } from "@/lib/utils";

type ToastType = "success" | "error" | "info";
interface ToastItem {
    id: number;
    message: string;
    type: ToastType;
}

const ToastContext = createContext<{ showToast: (message: string, type?: ToastType) => void } | null>(null);

export function useToast() {
    const ctx = useContext(ToastContext);
    if (!ctx) throw new Error("useToast must be used inside ToastProvider");
    return ctx;
}

export function ToastProvider({ children }: { children: ReactNode }) {
    const [toasts, setToasts] = useState<ToastItem[]>([]);

    const showToast = useCallback((message: string, type: ToastType = "info") => {
        const id = Date.now() + Math.random();
        setToasts((prev) => [...prev, { id, message, type }]);
        setTimeout(() => {
            setToasts((prev) => prev.filter((t) => t.id !== id));
        }, 3000);
    }, []);

    return (
        <ToastContext.Provider value={{ showToast }}>
            {children}
            <div className="pointer-events-none fixed left-1/2 top-6 z-[100] flex -translate-x-1/2 flex-col items-center gap-2">
                {toasts.map((t) => (
                    <div
                        key={t.id}
                        className={cn(
                            "pointer-events-auto flex items-center gap-2 rounded-[var(--radius-control)] px-4 py-3 text-sm font-medium text-white shadow-[var(--shadow-panel)]",
                            t.type === "success" ? "bg-navy-900" : t.type === "error" ? "bg-red-600" : "bg-navy-700"
                        )}
                    >
                        {t.type === "success" ? (
                            <CheckCircle2 className="h-4 w-4 shrink-0" />
                        ) : t.type === "error" ? (
                            <AlertCircle className="h-4 w-4 shrink-0" />
                        ) : (
                            <Info className="h-4 w-4 shrink-0" />
                        )}
                        {t.message}
                    </div>
                ))}
            </div>
        </ToastContext.Provider>
    );
}