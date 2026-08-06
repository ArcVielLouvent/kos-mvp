// Data contoh untuk pratinjau tampilan -- ganti dengan query Supabase asli
// (tabel `documents` dan `folders`) begitu backend final tersambung.
import type { KosDocument } from "./types";

export interface MockFolder {
    path: string;
    name: string;
}

export const MOCK_FOLDERS: MockFolder[] = [
    { path: "/SOP & Operasional/", name: "SOP & Operasional" },
    { path: "/HRD & Karyawan/", name: "HRD & Karyawan" },
    { path: "/Keuangan/", name: "Keuangan" },
    { path: "/Penilaian Karyawan/", name: "Penilaian Karyawan" },
    { path: "/Penilaian Karyawan/KPI/", name: "KPI" },
    { path: "/Penilaian Karyawan/Tabel KPI/", name: "Tabel KPI" },
];

export const MOCK_DOCUMENTS: any[] = [
    {
        id: "1",
        title: "SOP Mesin Espresso.pdf",
        folder_path: "/SOP & Operasional/",
        file_url: "#",
        metadata: { tipe_file: "Dokumen PDF" },
        created_at: "2026-07-21T10:00:00Z",
    },
    {
        id: "2",
        title: "FORM PENGAJUAN SDM BARU.docx",
        folder_path: "/HRD & Karyawan/",
        file_url: "#",
        metadata: { tipe_file: "Dokumen Word" },
        created_at: "2026-07-20T09:00:00Z",
    },
    {
        id: "3",
        title: "Kamus KPI Manajer Produksi.xlsx",
        folder_path: "/Penilaian Karyawan/KPI/",
        file_url: "#",
        metadata: { tipe_file: "Spreadsheet" },
        created_at: "2026-07-21T08:00:00Z",
    },
    {
        id: "4",
        title: "Kamus KPI Manajer PPIC.xlsx",
        folder_path: "/Penilaian Karyawan/KPI/",
        file_url: "#",
        metadata: { tipe_file: "Spreadsheet" },
        created_at: "2026-07-21T08:05:00Z",
    },
    {
        id: "5",
        title: "Teknik Pembuatan KPI",
        folder_path: "/Penilaian Karyawan/KPI/",
        file_url: "https://youtu.be/dQw4w9WgXcQ",
        metadata: { tipe_file: "Video YouTube" },
        created_at: "2026-07-19T14:00:00Z",
    },
];

export function normalizePath(path: string) {
    let p = path.trim();
    if (!p.startsWith("/")) p = "/" + p;
    if (!p.endsWith("/")) p += "/";
    return p;
}

export function getChildFolders(currentPath: string): MockFolder[] {
    const norm = normalizePath(currentPath);
    const seen = new Set<string>();
    const result: MockFolder[] = [];
    for (const f of MOCK_FOLDERS) {
        if (f.path.startsWith(norm) && f.path !== norm) {
            const rest = f.path.slice(norm.length);
            const segment = rest.split("/")[0];
            const childPath = norm + segment + "/";
            if (segment && !seen.has(childPath)) {
                seen.add(childPath);
                result.push({ path: childPath, name: segment });
            }
        }
    }
    return result;
}

export function getDocumentsInFolder(currentPath: string): any[] {
    const norm = normalizePath(currentPath);
    return MOCK_DOCUMENTS.filter((d) => d.folder_path === norm);
}