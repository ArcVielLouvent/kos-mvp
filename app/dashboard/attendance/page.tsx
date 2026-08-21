"use client";
import { useState, useEffect } from "react";
import { CheckCircle2, Clock, CalendarCheck } from "lucide-react";
import { TopBar } from "@/components/TopBar";
import { apiJson } from "@/lib/api";

export default function AttendancePage() {
    const [checkedIn, setCheckedIn] = useState(false);
    const [attendance, setAttendance] = useState<any>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);

    const load = () => {
        setIsLoading(true);
        apiJson("/api/attendance/today")
            .then((data) => {
                setCheckedIn(data.checkedIn);
                setAttendance(data.attendance);
            })
            .finally(() => setIsLoading(false));
    };

    useEffect(() => {
        load();
    }, []);

    const handleCheckIn = async () => {
        setIsSubmitting(true);
        try {
            await apiJson("/api/attendance/check-in", { method: "POST" });
            load();
        } finally {
            setIsSubmitting(false);
        }
    };

    const today = new Date().toLocaleDateString("id-ID", { weekday: "long", day: "numeric", month: "long", year: "numeric" });

    return (
        <div>
            <TopBar title="Kehadiran" description="Catat kehadiran Anda hari ini." />
            <div className="p-8">
                <div className="mx-auto max-w-md space-y-4 rounded-[var(--radius-card)] border border-navy-100 bg-white p-8 text-center shadow-[var(--shadow-card)]">
                    <span className={`mx-auto flex h-16 w-16 items-center justify-center rounded-full ${checkedIn ? "bg-green-50" : "bg-navy-50"}`}>
                        {checkedIn ? (
                            <CheckCircle2 className="h-8 w-8 text-green-600" />
                        ) : (
                            <CalendarCheck className="h-8 w-8 text-navy-700" />
                        )}
                    </span>

                    <div>
                        <p className="text-xs text-ink-faint">{today}</p>
                        <h3 className="mt-1 text-sm font-semibold text-ink">
                            {isLoading ? "Memuat..." : checkedIn ? "Anda sudah absen hari ini" : "Belum absen hari ini"}
                        </h3>
                    </div>

                    {checkedIn && attendance?.created_at && (
                        <p className="flex items-center justify-center gap-1.5 text-xs text-ink-muted">
                            <Clock className="h-3.5 w-3.5" /> Tercatat pukul {attendance.created_at.slice(11, 16)}
                        </p>
                    )}

                    {!checkedIn && (
                        <button
                            onClick={handleCheckIn}
                            disabled={isSubmitting || isLoading}
                            className="mx-auto flex items-center gap-2 rounded-[var(--radius-control)] bg-navy-900 px-6 py-2.5 text-sm font-semibold text-white hover:bg-navy-800 disabled:opacity-50"
                        >
                            <CalendarCheck className="h-4 w-4" />
                            {isSubmitting ? "Memproses..." : "Absen Sekarang"}
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}
