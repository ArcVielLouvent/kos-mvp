"use client";
import { useState, useEffect, useMemo } from "react";
import { BarChart3, LineChart as LineChartIcon, PieChart as PieChartIcon, Loader2, Database } from "lucide-react";
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import { TopBar } from "@/components/TopBar";
import { apiJson } from "@/lib/api";

const COLORS = ["#0f172a", "#1e40af", "#0369a1", "#0891b2", "#059669", "#65a30d", "#ca8a04", "#dc2626"];

interface Dataset {
  id: string;
  title: string;
}

type ChartType = "bar" | "line" | "pie";

function isNumericColumn(rows: any[], col: string): boolean {
  return rows.slice(0, 10).every((r) => {
    const v = String(r[col] ?? "").replace(",", "").trim();
    return v === "" || !isNaN(Number(v));
  });
}

export default function InsightsPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [columns, setColumns] = useState<string[]>([]);
  const [rows, setRows] = useState<any[]>([]);
  const [labelCol, setLabelCol] = useState<string>("");
  const [valueCol, setValueCol] = useState<string>("");
  const [chartType, setChartType] = useState<ChartType>("bar");
  const [isLoadingList, setIsLoadingList] = useState(true);
  const [isLoadingData, setIsLoadingData] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    apiJson("/api/insights/datasets")
      .then((data) => setDatasets(data.datasets || []))
      .finally(() => setIsLoadingList(false));
  }, []);

  const loadDataset = (id: string) => {
    setSelectedId(id);
    setIsLoadingData(true);
    setErrorMsg(null);
    apiJson(`/api/insights/dataset/${id}`)
      .then((data) => {
        setColumns(data.columns || []);
        setRows(data.rows || []);
        const numericCols = (data.columns || []).filter((c: string) => isNumericColumn(data.rows || [], c));
        const textCols = (data.columns || []).filter((c: string) => !numericCols.includes(c));
        setLabelCol(textCols[0] || data.columns?.[0] || "");
        setValueCol(numericCols[0] || data.columns?.[1] || data.columns?.[0] || "");
      })
      .catch((e) => setErrorMsg(e.message || "Gagal memuat dataset."))
      .finally(() => setIsLoadingData(false));
  };

  const chartData = useMemo(() => {
    if (!labelCol || !valueCol) return [];
    return rows.map((r) => ({
      label: String(r[labelCol] ?? "-"),
      value: Number(String(r[valueCol] ?? "0").replace(",", "")) || 0,
    }));
  }, [rows, labelCol, valueCol]);

  return (
    <div>
      <TopBar title="Insight & Grafik" description="Visualisasikan data terstruktur (hasil upload Excel) jadi grafik interaktif." />
      <div className="p-8">
        <div className="mx-auto max-w-4xl space-y-4">
          {isLoadingList ? (
            <div className="flex items-center justify-center rounded-[var(--radius-card)] border border-navy-100 bg-white p-12">
              <Loader2 className="h-5 w-5 animate-spin text-navy-700" />
            </div>
          ) : datasets.length === 0 ? (
            <div className="space-y-2 rounded-[var(--radius-card)] border border-navy-100 bg-white p-8 text-center">
              <Database className="mx-auto h-8 w-8 text-ink-faint" />
              <p className="text-sm font-semibold text-ink">Belum ada dataset terstruktur</p>
              <p className="text-xs text-ink-faint">Upload file Excel (.xlsx) di File Manager dulu supaya bisa divisualisasikan di sini.</p>
            </div>
          ) : (
            <>
              <div className="rounded-[var(--radius-card)] border border-navy-100 bg-white p-4 shadow-[var(--shadow-card)]">
                <label className="mb-1.5 block text-xs font-semibold text-ink-muted">Pilih Dataset</label>
                <select
                  value={selectedId || ""}
                  onChange={(e) => loadDataset(e.target.value)}
                  className="w-full rounded-[var(--radius-control)] border border-navy-100 bg-white px-3 py-2 text-sm text-ink"
                >
                  <option value="">-- pilih dataset --</option>
                  {datasets.map((d) => (
                    <option key={d.id} value={d.id}>{d.title}</option>
                  ))}
                </select>
              </div>

              {errorMsg && (
                <p className="rounded-[var(--radius-control)] bg-red-50 px-3 py-2 text-xs font-medium text-red-700">{errorMsg}</p>
              )}

              {isLoadingData ? (
                <div className="flex items-center justify-center rounded-[var(--radius-card)] border border-navy-100 bg-white p-12">
                  <Loader2 className="h-5 w-5 animate-spin text-navy-700" />
                </div>
              ) : selectedId && columns.length > 0 ? (
                <div className="space-y-4 rounded-[var(--radius-card)] border border-navy-100 bg-white p-5 shadow-[var(--shadow-card)]">
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
