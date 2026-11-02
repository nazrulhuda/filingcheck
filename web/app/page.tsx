"use client";

import { type FormEvent, useEffect, useState } from "react";

import { AnswerText, CostLine } from "@/components/AnswerView";
import examplesData from "@/data/examples.json";
import {
  type Answer,
  ApiError,
  type Company,
  askStreaming,
  checkHealth,
  getCompanies,
  type Health,
} from "@/lib/api";
import { type AnswerSource, cachedNotice } from "@/lib/display";

type Example = { question: string; ticker: string | null; fiscal_year: number | null; answer: Answer };

const EXAMPLES = examplesData as Example[];
const MAX_QUESTION = 500;
const HEALTH_TIMEOUT_MS = 3000;
const WAKE_RETRY_MS = 5000;
const WAKE_GIVE_UP_MS = 70_000;

type Backend = "checking" | "waking" | Health;

type Shown =
  | { kind: "none" }
  | { kind: "streaming"; text: string }
  | {
      kind: "answer";
      question: string;
      answer: Answer;
      source: AnswerSource;
      notice: string | null;
    }
  | { kind: "error"; message: string };

export default function Home() {
  const [backend, setBackend] = useState<Backend>("checking");
  const [companies, setCompanies] = useState<Company[]>([]);
  const [question, setQuestion] = useState("");
  const [ticker, setTicker] = useState("");
  const [year, setYear] = useState("");
  const [shown, setShown] = useState<Shown>({ kind: "none" });
  const [busy, setBusy] = useState(false);

  // /health makes no database query, so asking it while the backend wakes is cheap.
  useEffect(() => {
    let cancelled = false;
    const started = Date.now();
    async function poll() {
      const health = await checkHealth(HEALTH_TIMEOUT_MS);
      if (cancelled) return;
      if (health === "unreachable" && Date.now() - started < WAKE_GIVE_UP_MS) {
        setBackend("waking");
        setTimeout(poll, WAKE_RETRY_MS);
        return;
      }
      setBackend(health);
      if (health === "ok") {
        getCompanies()
          .then((list) => !cancelled && setCompanies(list))
          .catch(() => undefined);
      }
    }
    poll();
    return () => {
      cancelled = true;
    };
  }, []);

  const years = companies.find((c) => c.ticker === ticker)?.fiscal_years ?? [];

  async function submit(event: FormEvent) {
    event.preventDefault();
    const text = question.trim();
    if (!text || busy) return;
    setBusy(true);
    setShown({ kind: "streaming", text: "" });
    try {
      const result = await askStreaming(
        {
          question: text,
          ...(ticker ? { ticker } : {}),
          ...(ticker && year ? { fiscal_year: Number(year) } : {}),
        },
        (soFar) => setShown({ kind: "streaming", text: soFar }),
      );
      // After the daily limit the API sends a saved example's answer: it belongs to that
      // example's question, not to the visitor's, and the page says so.
      setShown({
        kind: "answer",
        question: result.example?.question ?? text,
        answer: result.answer,
        source: result.cached ? "after-limit" : "new",
        notice: cachedNotice(result),
      });
    } catch (error) {
      const message =
        error instanceof ApiError
          ? error.message
          : "The API could not be reached; please try again in a minute.";
      setShown({ kind: "error", message });
    } finally {
      setBusy(false);
    }
  }

  function showExample(example: Example) {
    setQuestion(example.question);
    setTicker(example.ticker ?? "");
    setYear(example.fiscal_year ? String(example.fiscal_year) : "");
    setShown({
      kind: "answer",
      question: example.question,
      answer: example.answer,
      source: "example",
      notice: null,
    });
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-8 sm:py-12">
      <div
        role="status"
        className="mb-6 rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900"
      >
        Week 2 baseline: answers are not checked yet and numbers may be wrong; skeptical checks
        arrive in week 4
      </div>

      <h1 className="text-2xl font-semibold tracking-tight">FilingCheck</h1>
      <p className="mt-1 text-sm text-slate-600">
        Questions about the 10-K filings of 25 public companies, answered from the filings&apos;
        text with a citation for each claim.
      </p>

      {backend === "waking" && (
        <p className="mt-4 rounded-md bg-slate-100 px-3 py-2 text-sm text-slate-700">
          The backend is waking up (up to a minute). The saved examples below work meanwhile.
        </p>
      )}
      {backend === "unreachable" && (
        <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-800">
          The backend is not answering right now. The saved examples below still work.
        </p>
      )}
      {backend === "no-model" && (
        <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-800">
          The backend is up but has no language model configured right now.
        </p>
      )}

      <form onSubmit={submit} className="mt-6 space-y-3">
        <label htmlFor="question" className="block text-sm font-medium">
          Your question
        </label>
        <textarea
          id="question"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          maxLength={MAX_QUESTION}
          rows={3}
          placeholder="For example: What does Netflix say about intellectual-property claims?"
          className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-base focus:border-blue-600 focus:outline-none"
        />
        <p className="text-xs text-slate-500">
          Each question stands alone (no chat history). Questions are logged to improve the demo.
          Each question is sent to OpenAI to search the filings, and through OpenRouter to Groq, or
          to Google if that is busy, to write the answer; please don&apos;t enter personal
          information.
        </p>
        <div className="flex flex-wrap items-end gap-3">
          <label className="text-sm">
            <span className="block text-slate-600">Company (optional)</span>
            <select
              value={ticker}
              onChange={(e) => {
                setTicker(e.target.value);
                setYear("");
              }}
              disabled={companies.length === 0}
              className="mt-1 rounded-md border border-slate-300 bg-white px-2 py-1.5"
            >
              <option value="">Any company</option>
              {companies.map((c) => (
                <option key={c.ticker} value={c.ticker}>
                  {c.name} ({c.ticker})
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            <span className="block text-slate-600">Fiscal year (optional)</span>
            <select
              value={year}
              onChange={(e) => setYear(e.target.value)}
              disabled={years.length === 0}
              className="mt-1 rounded-md border border-slate-300 bg-white px-2 py-1.5"
            >
              <option value="">Any year</option>
              {years.map((y) => (
                <option key={y} value={y}>
                  {y}
                </option>
              ))}
            </select>
          </label>
          <button
            type="submit"
            disabled={busy || !question.trim() || backend !== "ok"}
            className="rounded-md bg-blue-700 px-4 py-2 text-sm font-medium text-white hover:bg-blue-800 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            {busy ? "Answering…" : "Ask"}
          </button>
          <label className="ml-auto flex cursor-not-allowed items-center gap-2 text-sm text-slate-400">
            <input type="checkbox" disabled className="h-4 w-4" />
            Skeptical checks: coming in Week 4
          </label>
        </div>
      </form>

      <section className="mt-6">
        <h2 className="text-sm font-medium text-slate-600">Examples</h2>
        <div className="mt-2 flex flex-wrap gap-2">
          {EXAMPLES.map((example) => (
            <button
              key={example.question}
              type="button"
              onClick={() => showExample(example)}
              className="rounded-full border border-slate-300 bg-white px-3 py-1 text-left text-sm hover:border-blue-600 hover:text-blue-800"
            >
              {example.question}
            </button>
          ))}
        </div>
      </section>

      <section className="mt-8" aria-live="polite">
        {shown.kind === "streaming" && (
          <div className="rounded-md border border-slate-200 bg-white p-4">
            <p className="whitespace-pre-line leading-7 text-slate-800">
              {shown.text || "Searching the filings…"}
            </p>
          </div>
        )}
        {shown.kind === "answer" && (
          <div className="rounded-md border border-slate-200 bg-white p-4">
            {shown.notice ? (
              <p role="status" className="mb-3 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-900">
                {shown.notice}
              </p>
            ) : (
              <p className="mb-3 text-sm font-medium text-slate-600">{shown.question}</p>
            )}
            {/* A new answer starts with every citation closed. */}
            <AnswerText key={`${shown.question}\n${shown.answer.text}`} answer={shown.answer} />
            <CostLine answer={shown.answer} source={shown.source} />
          </div>
        )}
        {shown.kind === "error" && (
          <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-800">
            {shown.message}
          </p>
        )}
      </section>
    </main>
  );
}
