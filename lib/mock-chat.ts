export interface MockMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sourceTitle?: string;
  sourceType?: "Dokumen PDF" | "Spreadsheet" | "Video YouTube";
}

export interface MockSession {
  id: string;
  title: string;
  messages: MockMessage[];
}

export const MOCK_SESSIONS: MockSession[] = [
  {
    id: "s1",
    title: "Prosedur cuti karyawan",
    messages: [
      { id: "m1", role: "user", content: "Bagaimana prosedur cuti karyawan?" },
      {
        id: "m2",
        role: "assistant",
        content:
          "Maaf, informasi mengenai prosedur cuti belum tersedia di dalam database. Coba tanyakan ke Admin untuk menambahkan dokumen SOP cuti.",
      },
    ],
  },
  {
    id: "s2",
    title: "Cara membuat KPI",
    messages: [
      { id: "m3", role: "user", content: "Bagaimana teknik pembuatan KPI yang baik?" },
      {
        id: "m4",
        role: "assistant",
        content:
          "Berdasarkan video referensi yang tersedia, teknik pembuatan KPI yang baik mencakup penentuan indikator yang measurable, realistic, dan time-bound (SMART).",
        sourceTitle: "Teknik Pembuatan KPI",
        sourceType: "Video YouTube",
      },
    ],
  },
];