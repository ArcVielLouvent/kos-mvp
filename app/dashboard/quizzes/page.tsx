"use client";
import { useState, useEffect } from "react";
import { GraduationCap, Plus, CheckCircle2, XCircle, Clock, ArrowLeft, Loader2 } from "lucide-react";
import Link from "next/link";
import { TopBar } from "@/components/TopBar";
import { apiJson, getStoredUser } from "@/lib/api";

interface Question {
  question: string;
  options: string[];
  correct_index?: number;
}

export default function QuizzesPage() {
  const user = getStoredUser();
  const isAdminTier = user?.role === "Admin" || user?.role === "SuperAdmin";

  const [quizzes, setQuizzes] = useState<any[]>([]);
  const [myAttempts, setMyAttempts] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeQuiz, setActiveQuiz] = useState<any>(null);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [result, setResult] = useState<any>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const load = () => {
    setIsLoading(true);
    Promise.all([
      apiJson("/api/quizzes"),
      apiJson("/api/quizzes/attempts/me"),
    ])
      .then(([quizData, attemptData]) => {
        setQuizzes(quizData.quizzes || []);
        setMyAttempts(attemptData.attempts || []);
      })
      .finally(() => setIsLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const attemptedQuizIds = new Set(myAttempts.map((a) => a.quiz_id));

  const openQuiz = async (quizId: string) => {
    const quiz = await apiJson(`/api/quizzes/${quizId}`);
    setActiveQuiz(quiz);
    setAnswers({});
    setResult(null);
  };

  const submitQuiz = async () => {
    if (!activeQuiz) return;
    setIsSubmitting(true);
    try {
      const res = await apiJson(`/api/quizzes/${activeQuiz.id}/attempts`, {
        method: "POST",
        body: JSON.stringify({ answers }),
      });
      setResult(res);
      load();
    } catch (e: any) {
      alert(e.message || "Gagal mengirim jawaban.");
    } finally {
      setIsSubmitting(false);
    }
  };

  // ---------- MODE: MENGERJAKAN KUIS ----------
  if (activeQuiz) {
    const questions: Question[] = activeQuiz.questions || [];
    const allAnswered = questions.every((_, i) => answers[i] !== undefined);

    return (
      <div>
        <TopBar
          title={activeQuiz.title}
          description={`${questions.length} soal -- nilai minimal lulus ${activeQuiz.passing_score}`}
          action={
            <button onClick={() => setActiveQuiz(null)} className="flex items-center gap-2 rounded-[var(--radius-control)] border border-navy-100 bg-white px-3 py-2 text-xs font-semibold text-ink-muted hover:bg-navy-50">
              <ArrowLeft className="h-3.5 w-3.5" /> Kembali
            </button>
          }
        />
        <div className="p-8">
          <div className="mx-auto max-w-2xl space-y-4">
            {result ? (
              <div className="space-y-4 rounded-[var(--radius-card)] border border-navy-100 bg-white p-8 text-center shadow-[var(--shadow-card)]">
                {result.passed ? (
                  <CheckCircle2 className="mx-auto h-12 w-12 text-green-600" />
                ) : (
                  <XCircle className="mx-auto h-12 w-12 text-red-500" />
                )}
                <p className="text-2xl font-bold text-ink">{result.score}</p>
                <p className="text-sm text-ink-muted">
                  {result.correct} dari {result.total} jawaban benar -- {result.passed ? "Lulus" : "Belum lulus"}
                </p>
                <button
                  onClick={() => setActiveQuiz(null)}
                  className="mt-2 rounded-[var(--radius-control)] bg-navy-900 px-5 py-2.5 text-sm font-semibold text-white hover:bg-navy-800"
                >
                  Kembali ke Daftar Kuis
                </button>
              </div>
            ) : (
              <>
                {questions.map((q, i) => (
                  <div key={i} className="rounded-[var(--radius-card)] border border-navy-100 bg-white p-5 shadow-[var(--shadow-card)]">
                    <p className="mb-3 text-sm font-semibold text-ink">{i + 1}. {q.question}</p>
                    <div className="space-y-2">
                      {q.options.map((opt, oi) => (
                        <label
                          key={oi}
                          className={`flex cursor-pointer items-center gap-2 rounded-[var(--radius-control)] border px-3 py-2 text-sm ${answers[i] === oi ? "border-navy-900 bg-navy-50" : "border-navy-100 hover:bg-navy-50/50"}`}
                        >
                          <input
                            type="radio"
                            name={`q${i}`}
                            checked={answers[i] === oi}
                            onChange={() => setAnswers((prev) => ({ ...prev, [i]: oi }))}
                            className="h-4 w-4"
                          />
                          {opt}
                        </label>
                      ))}
                    </div>
                  </div>
                ))}
                <button
                  onClick={submitQuiz}
                  disabled={!allAnswered || isSubmitting}
                  className="flex w-full items-center justify-center gap-2 rounded-[var(--radius-control)] bg-navy-900 py-2.5 text-sm font-semibold text-white hover:bg-navy-800 disabled:opacity-50"
                >
                  {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}
                  {isSubmitting ? "Mengirim..." : "Kirim Jawaban"}
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    );
  }

  // ---------- MODE: DAFTAR KUIS ----------
  return (
    <div>
      <TopBar
        title="Kuis Training"
        description="Uji pemahaman terhadap SOP & dokumen perusahaan."
        action={
          isAdminTier ? (
            <Link href="/dashboard/quizzes/create" className="flex items-center gap-2 rounded-[var(--radius-control)] bg-navy-900 px-3 py-2 text-xs font-semibold text-white hover:bg-navy-800">
              <Plus className="h-3.5 w-3.5" /> Buat Kuis dari Dokumen
            </Link>
          ) : undefined
        }
      />
      <div className="p-8">
        <div className="mx-auto max-w-2xl space-y-6">
          {isLoading ? (
            <div className="flex items-center justify-center rounded-[var(--radius-card)] border border-navy-100 bg-white p-12">
              <Loader2 className="h-5 w-5 animate-spin text-navy-700" />
            </div>
          ) : quizzes.length === 0 ? (
            <p className="rounded-[var(--radius-card)] border border-navy-100 bg-white p-8 text-center text-sm text-ink-faint">
              Belum ada kuis tersedia.
            </p>
          ) : (
            <div className="space-y-2">
              {quizzes.map((q: any) => {
                const attempt = myAttempts.find((a) => a.quiz_id === q.id);
                return (
                  <button
                    key={q.id}
                    onClick={() => openQuiz(q.id)}
                    className="flex w-full items-center justify-between gap-3 rounded-[var(--radius-card)] border border-navy-100 bg-white p-4 text-left shadow-[var(--shadow-card)] hover:-translate-y-0.5 transition-transform"
                  >
                    <div className="flex items-center gap-3">
                      <span className="flex h-10 w-10 items-center justify-center rounded-full bg-navy-50">
                        <GraduationCap className="h-5 w-5 text-navy-700" />
                      </span>
                      <div>
                        <p className="text-sm font-semibold text-ink">{q.title}</p>
                        <p className="text-2xs text-ink-faint">Nilai minimal lulus: {q.passing_score}</p>
                      </div>
                    </div>
                    {attempt && (
                      <span className={`flex items-center gap-1 rounded-full px-2.5 py-1 text-2xs font-semibold ${attempt.passed ? "bg-green-50 text-green-700" : "bg-red-50 text-red-600"}`}>
                        {attempt.passed ? <CheckCircle2 className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}
                        {attempt.score}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          )}

          {myAttempts.length > 0 && (
            <div>
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-faint">Riwayat Kuis Saya</p>
              <div className="space-y-1.5">
                {myAttempts.map((a: any) => (
                  <div key={a.id} className="flex items-center justify-between rounded-[var(--radius-control)] border border-navy-50 bg-navy-50/40 px-3 py-2 text-xs">
                    <span className="text-ink">{a.quizzes?.title || "Kuis"}</span>
                    <span className="flex items-center gap-2 text-ink-faint">
                      <Clock className="h-3 w-3" /> {(a.created_at || "").slice(0, 10)}
                      <span className={`font-semibold ${a.passed ? "text-green-600" : "text-red-500"}`}>{a.score}</span>
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
