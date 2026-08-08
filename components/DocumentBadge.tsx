import {
    FileText,
    FileSpreadsheet,
    Presentation,
    Image as ImageIcon,
    Video,
    FileAudio,
    SquarePlay,
    File,
} from "lucide-react";
import { cn } from "@/lib/utils";

const TYPE_CONFIG = {
    "Dokumen PDF": { icon: FileText, bg: "bg-red-50", fg: "text-red-600", label: "PDF" },
    "Dokumen Word": { icon: FileText, bg: "bg-blue-50", fg: "text-blue-600", label: "Word" },
    "Dokumen RTF": { icon: FileText, bg: "bg-blue-50", fg: "text-blue-600", label: "RTF" },
    "Spreadsheet": { icon: FileSpreadsheet, bg: "bg-green-50", fg: "text-green-600", label: "Excel" },
    "CSV Data": { icon: FileSpreadsheet, bg: "bg-green-50", fg: "text-green-600", label: "CSV" },
    "Presentasi": { icon: Presentation, bg: "bg-orange-50", fg: "text-orange-600", label: "Slide" },
    "Gambar": { icon: ImageIcon, bg: "bg-purple-50", fg: "text-purple-600", label: "Gambar" },
    "Media Transkrip": { icon: Video, bg: "bg-pink-50", fg: "text-pink-600", label: "Media" },
    "Video YouTube": { icon: SquarePlay, bg: "bg-red-50", fg: "text-red-600", label: "YouTube" },
    "Teks": { icon: File, bg: "bg-gray-100", fg: "text-gray-600", label: "Teks" },
    "default": { icon: File, bg: "bg-gray-100", fg: "text-gray-600", label: "File" },
};

export function DocumentBadge({ type, size = "md" }: { type: string; size?: "sm" | "md" }) {
    const config = TYPE_CONFIG[type as keyof typeof TYPE_CONFIG] || TYPE_CONFIG.default;
    const Icon = config.icon;

    return (
        <div
            title={type}
            className={cn(
                "flex shrink-0 items-center justify-center rounded-[var(--radius-control)]",
                config.bg,
                config.fg,
                size === "sm" ? "h-8 w-8" : "h-10 w-10"
            )}
        >
            <Icon className={size === "sm" ? "h-4 w-4" : "h-5 w-5"} />
        </div>
    );
}