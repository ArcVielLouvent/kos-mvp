"use client";
import { useState, useEffect, useMemo } from "react";
import { BarChart3, LineChart as LineChartIcon, PieChart as PieChartIcon, Loader2, Database, X, FileText } from "lucide-react";
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import { TopBar } from "@/components/TopBar";
import { DocumentPicker } from "@/components/DocumentPicker";
import { apiJson } from "@/lib/api";

const COLORS = ["#0f172a", "#1e40af", "#0369a1", "#0891b2", "#059669", "#65a30d", "#ca8a04", "#dc2626"];

type ChartType = "bar" | "line" | "pie";

function isNumericColumn(rows: any[], col: string): boolean {
  return rows.slice(0, 10).every((r) => {
    const v = String(r[col] ?? "").replace(",", "").trim();
    return v === "" || !isNaN(Number(v));
  });
}

export default function InsightsPage() {
  const [hasAnyDataset, setHasAnyDataset] = useState<boolean | null>(null); // null = belum tahu
  const [selectedDocs, setSelectedDocs] = useState<Map<string, string>>(new Map());
  const [sourceFolder, setSourceFolder] = useState<string | null>(null);
  const [pickerPath, setPickerPath] = useState("/");

  const [columns, setColumns] = useState<string[]>([]);
  const [rows, setRows] = useState<any[]>([]);
  const [sources, setSources] = useState<string[]>([]);
  const [labelCol, setLabelCol] = useState<string>("");
  const [valueCol, setValueCol] = useState<string>("");
  const [chartType, setChartType] = useState<ChartType>("bar");
  const [isLoadingData, setIsLoadingData] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isReprocessing, setIsReprocessing] = useState(false);
  const [reprocessMsg, setReprocessMsg] = useState<string | null>(null);

  const checkAnyDataset = () => {
    apiJson("/api/insights/datasets")
      .then((data) => setHasAnyDataset((data.datasets || []).length > 0))
      .catch(() => setHasAnyDataset(false));
  };

  useEffect(() => {
    checkAnyDataset();
  }, []);

  const reprocessOldFiles = async () => {
    setIsReprocessing(true);
    setReprocessMsg(null);
    try {
      const result = await apiJson("/api/insights/reprocess", { method: "POST" });
      const parts = [];
      if (result.fixed?.length) parts.push(`${result.fixed.length} berhasil diproses ulang`);
      if (result.still_failed?.length) parts.push(`${result.still_failed.length} tetap gagal (bukan data tabular)`);
      setReprocessMsg(parts.length ? parts.join(", ") + "." : "Tidak ada file .xlsx lama yang perlu diproses ulang.");
      if (result.fixed?.length) checkAnyDataset();
    } catch (e: any) {
      setReprocessMsg(e.message || "Gagal memproses ulang.");
    } finally {
      setIsReprocessing(false);
    }
  };

  const toggleDoc = (doc: { id: string; title: string }) => {
    setSourceFolder(null);
    setSelectedDocs((prev) => {
      const next = new Map(prev);
      next.has(doc.id) ? next.delete(doc.id) : next.set(doc.id, doc.title);
      return next;
    });
  };

  const useFolder = (folderPath: string) => {
    setSelectedDocs(new Map());
    setSourceFolder(folderPath);
  };

  const loadCombined = async () => {
    if (selectedDocs.size === 0 && !sourceFolder) return;
    setIsLoadingData(true);
    setErrorMsg(null);
    try {
      const data = await apiJson("/api/insights/combine", {
        method: "POST",
        body: JSON.stringify({
          doc_ids: sourceFolder ? [] : Array.from(selectedDocs.keys()),
          folder_path: sourceFolder,
        }),
      });
      setColumns(data.columns || []);
      setRows(data.rows || []);
      setSources(data.sources || []);
      const numericCols = (data.columns || []).filter((c: string) => isNumericColumn(data.rows || [], c));
      const textCols = (data.columns || []).filter((c: string) => !numericCols.includes(c));
      setLabelCol(textCols[0] || data.columns?.[0] || "");
      setValueCol(numericCols[0] || data.columns?.[1] || data.columns?.[0] || "");
    } catch (e: any) {
      setColumns([]);
      setRows([]);
      setErrorMsg(e.message || "Gagal memuat dataset.");
    } finally {
      setIsLoadingData(false);
    }
  };

  useEffect(() => {
    loadCombined();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sourceFolder, selectedDocs.size]);

  const chartData = useMemo(() => {
    if (!labelCol || !valueCol) return [];
    return rows.map((r) => ({
      label: String(r[labelCol] ?? "-"),
      value: Number(String(r[valueCol] ?? "0").replace(",", "")) || 0,
    }));
  }, [rows, labelCol, valueCol]);

  return (
    <div>
      <TopBar title="Insight & Grafik" description="Visualisasikan data terstruktur (hasil upload Excel) jadi grafik interaktif -- bisa gabungkan beberapa file sekaligus kalau strukturnya seragam." />
      <div className="p-8">
        <div className="mx-auto max-w-4xl space-y-4">
          {hasAnyDataset === false && (
            <div className="space-y-3 rounded-[var(--radius-card)] border border-navy-100 bg-white p-8 text-center">
              <Database className="mx-auto h-8 w-8 text-ink-faint" />
              <p className="text-sm font-semibold text-ink">Belum ada dataset terstruktur</p>
              <p className="text-xs text-ink-faint">Upload file Excel (.xlsx) di File Manager dulu supaya bisa divisualisasikan di sini.</p>
              <p className="text-2xs text-ink-faint">
                Sudah upload tapi tidak muncul? Beberapa file lama gagal diproses karena format tabelnya -- coba proses ulang di bawah ini.
              </p>
              <button
                onClick={reprocessOldFiles}
                disabled={isReprocessing}
                className="mx-auto flex items-center gap-2 rounded-[var(--radius-control)] border border-navy-100 bg-white px-4 py-2 text-xs font-semibold text-ink-muted hover:bg-navy-50 disabled:opacity-50"
              >
                {isReprocessing ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Database className="h-3.5 w-3.5" />}
                {isReprocessing ? "Memproses..." : "Proses Ulang File Excel Lama"}
              </button>
              {reprocessMsg && <p className="text-2xs font-medium text-navy-700">{reprocessMsg}</p>}
            </div>
          )}

          {hasAnyDataset && (
            <>
              <div className="flex justify-end">
                <button
                  onClick={reprocessOldFiles}
                  disabled={isReprocessing}
                  className="flex items-center gap-1.5 text-2xs font-semibold text-navy-700 hover:underline disabled:opacity-50"
                >
                  {isReprocessing ? <Loader2 className="h-3 w-3 animate-spin" /> : null}
                  {isReprocessing ? "Memproses..." : "Cek file Excel lama yang belum muncul"}
                </button>
              </div>
              {reprocessMsg && <p className="text-2xs font-medium text-navy-700">{reprocessMsg}</p>}

              <div>
                <label className="mb-1.5 block text-xs font-semibold text-ink">
                  Pilih Dataset <span className="font-normal text-ink-faint">-- centang beberapa file Excel sekaligus, atau pakai semua isi 1 folder</span>
                </label>
                <DocumentPicker
                  mode="multi"
                  selectedIds={new Set(selectedDocs.keys())}
                  onToggle={toggleDoc}
                  onUseFolder={useFolder}
                  currentFolderPath={pickerPath}
                  onNavigate={setPickerPath}
                />
                <div className="mt-2">
                  {sourceFolder ? (
                    <p className="flex items-center gap-1.5 text-xs font-medium text-navy-700">
                      <FileText className="h-3.5 w-3.5" /> Memakai semua dataset Excel di folder <span className="font-mono-data">{sourceFolder}</span>
                    </p>
                  ) : selectedDocs.size > 0 ? (
                    <div className="flex flex-wrap gap-1.5">
                      {Array.from(selectedDocs.entries()).map(([id, title]) => (
                        <span key={id} className="flex items-center gap-1 rounded-full bg-navy-50 px-2.5 py-1 text-2xs font-medium text-navy-900">
                          {title}
                          <button onClick={() => toggleDoc({ id, title })} className="text-navy-400 hover:text-navy-900">
                            <X className="h-3 w-3" />
                          </button>
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-2xs text-ink-faint">Belum ada dataset dipilih.</p>
                  )}
                </div>
              </div>

              {errorMsg && (
                <p className="rounded-[var(--radius-control)] bg-amber-50 px-3 py-2 text-xs font-medium text-amber-800">{errorMsg}</p>
              )}

              {isLoadingData ? (
                <div className="flex items-center justify-center rounded-[var(--radius-card)] border border-navy-100 bg-white p-12">
                  <Loader2 className="h-5 w-5 animate-spin text-navy-700" />
                </div>
              ) : columns.length > 0 ? (
                <div className="space-y-4 rounded-[var(--radius-card)] border border-navy-100 bg-white p-5 shadow-[var(--shadow-card)]">
                  {sources.length > 1 && (
                    <p className="text-2xs text-ink-faint">Digabung dari {sources.length} file: {sources.join(", ")}</p>
                  )}
                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                    <div>
                      <label className="mb-1 block text-2xs font-semibold text-ink-muted">Kolom Label (sumbu kategori)</label>
                      <select value={labelCol} onChange={(e) => setLabelCol(e.target.value)} className="w-full rounded border border-navy-100 bg-white px-2.5 py-1.5 text-xs text-ink">
                        {columns.map((c) => <option key={c} value={c}>{c}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="mb-1 block text-2xs font-semibold text-ink-muted">Kolom Nilai (angka)</label>
                      <select value={valueCol} onChange={(e) => setValueCol(e.target.value)} className="w-full rounded border border-navy-100 bg-white px-2.5 py-1.5 text-xs text-ink">
                        {columns.map((c) => <option key={c} value={c}>{c}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="mb-1 block text-2xs font-semibold text-ink-muted">Jenis Grafik</label>
                      <div className="flex gap-1.5">
                        <button onClick={() => setChartType("bar")} className={`flex flex-1 items-center justify-center gap-1 rounded border px-2 py-1.5 text-2xs font-semibold ${chartType === "bar" ? "border-navy-900 bg-navy-900 text-white" : "border-navy-100 text-ink-muted hover:bg-navy-50"}`}>
                          <BarChart3 className="h-3.5 w-3.5" /> Bar
                        </button>
                        <button onClick={() => setChartType("line")} className={`flex flex-1 items-center justify-center gap-1 rounded border px-2 py-1.5 text-2xs font-semibold ${chartType === "line" ? "border-navy-900 bg-navy-900 text-white" : "border-navy-100 text-ink-muted hover:bg-navy-50"}`}>
                          <LineChartIcon className="h-3.5 w-3.5" /> Line
                        </button>
                        <button onClick={() => setChartType("pie")} className={`flex flex-1 items-center justify-center gap-1 rounded border px-2 py-1.5 text-2xs font-semibold ${chartType === "pie" ? "border-navy-900 bg-navy-900 text-white" : "border-navy-100 text-ink-muted hover:bg-navy-50"}`}>
                          <PieChartIcon className="h-3.5 w-3.5" /> Pie
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="h-96 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      {chartType === "bar" ? (
                        <BarChart data={chartData}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                          <XAxis dataKey="label" tick={{ fontSize: 11 }} angle={-25} textAnchor="end" height={70} />
                          <YAxis tick={{ fontSize: 11 }} />
                          <Tooltip />
                          <Bar dataKey="value" fill="#0f172a" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      ) : chartType === "line" ? (
                        <LineChart data={chartData}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                          <XAxis dataKey="label" tick={{ fontSize: 11 }} angle={-25} textAnchor="end" height={70} />
                          <YAxis tick={{ fontSize: 11 }} />
                          <Tooltip />
                          <Line type="monotone" dataKey="value" stroke="#0f172a" strokeWidth={2} dot={{ r: 3 }} />
                        </LineChart>
                      ) : (
                        <PieChart>
                          <Pie data={chartData} dataKey="value" nameKey="label" cx="50%" cy="50%" outerRadius={130} label>
                            {chartData.map((_, i) => (
                              <Cell key={i} fill={COLORS[i % COLORS.length]} />
                            ))}
                          </Pie>
                          <Tooltip />
                          <Legend wrapperStyle={{ fontSize: 11 }} />
                        </PieChart>
                      )}
                    </ResponsiveContainer>
                  </div>
                </div>
              ) : null}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
