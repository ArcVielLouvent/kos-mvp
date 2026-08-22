// API URL dinamis:
// - Lokal (localhost): langsung ke FastAPI lokal di :8000
// - Produksi: ke backend Railway lewat NEXT_PUBLIC_API_URL (di-set di
//   Vercel Project Settings -> Environment Variables), TANPA trailing slash.
//   Kalau env var belum di-set, fallback "" (relatif) -- ini akan gagal
//   sejak backend dipindah ke Railway (bukan lagi serverless function di
//   Vercel yang sama), jadi WAJIB diisi untuk build produksi.
export const API_URL =
    typeof window !== "undefined" && window.location.hostname === "localhost"
        ? "http://localhost:8000"
        : (process.env.NEXT_PUBLIC_API_URL || "").replace(/\/$/, "");

export interface KosUser {
    email: string;
    role: "SuperAdmin" | "Admin" | "Karyawan";
    company_id: string;
    company_name?: string;
    folder_access: string;
    permission_level?: "crud" | "read_only";
    position_title?: string | null;
    must_change_password?: boolean;
}

/** auth.py tidak menerbitkan token -- login cuma balikin data user apa
 * adanya, jadi kita simpan penuh di localStorage (identik dengan
 * st.session_state.user di app.py) dan kirim email-nya di tiap request
 * lewat header X-User-Email supaya backend tahu siapa yang minta. */
export function getStoredUser(): KosUser | null {
    if (typeof window === "undefined") return null;
    const raw = localStorage.getItem("kos_user");
    if (!raw) return null;
    try {
        return JSON.parse(raw);
    } catch {
        return null;
    }
}

export function setStoredUser(user: KosUser) {
    if (typeof window === "undefined") return;
    localStorage.setItem("kos_user", JSON.stringify(user));
}

export function clearStoredUser() {
    if (typeof window === "undefined") return;
    localStorage.removeItem("kos_user");
}

/** fetch wrapper: nempelin header X-User-Email otomatis, dan
 * Content-Type: application/json kalau body-nya bukan FormData. */
export async function apiFetch(path: string, options: RequestInit = {}) {
    const user = getStoredUser();
    const headers: Record<string, string> = {
        "X-User-Email": user?.email || "",
        ...(options.body && !(options.body instanceof FormData)
            ? { "Content-Type": "application/json" }
            : {}),
        ...((options.headers as Record<string, string>) || {}),
    };
    return fetch(`${API_URL}${path}`, { ...options, headers, cache: "no-store" });
}

export async function apiJson<T = any>(path: string, options: RequestInit = {}): Promise<T> {
    const res = await apiFetch(path, options);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
        throw new Error(data.detail || `Request gagal (${res.status})`);
    }
    return data as T;
}

/** Ubah base64 dari backend (mis. generatedFiles / analysisFile) jadi
 * file yang otomatis terunduh di browser. */
export function downloadBase64(filename: string, base64: string, mime = "application/octet-stream") {
    const byteChars = atob(base64);
    const byteNumbers = new Array(byteChars.length);
    for (let i = 0; i < byteChars.length; i++) byteNumbers[i] = byteChars.charCodeAt(i);
    const blob = new Blob([new Uint8Array(byteNumbers)], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
}