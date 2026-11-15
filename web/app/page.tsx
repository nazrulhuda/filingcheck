"use client";

import { type FormEvent, useEffect, useRef, useState } from "react";

import {
  AnswerText,
  ChecksPanel,
  CostLine,
  LabelGuide,
} from "@/components/AnswerView";
import examplesData from "@/data/examples.json";
import resultsData from "@/data/results.json";
import trapData from "@/data/trap_examples.json";
import {
  type Answer,
  ApiError,
  type Company,
  askStreaming,
  checkHealth,
  getCompanies,
  type Health,
  type Progress,
} from "@/lib/api";
import { CANNOT, METRICS } from "@/lib/coverage";
import {
  type AnswerSource,
  askedWith,
  cachedNotice,
  pageQuestion,
} from "@/lib/display";
import { reviewNote } from "@/lib/notes";
import { type Results, resultLines } from "@/lib/results";
import {
  type Example,
  TRAP_NOTE,
  type TrapExample,
  plainExamples,
  trapExamples,
} from "@/lib/traps";

const EXAMPLES = examplesData as Example[];
const TRAPS = trapExamples(trapData as TrapExample[], EXAMPLES);
const PLAIN = plainExamples(EXAMPLES, TRAPS);
const RESULTS = resultsData as Results;
const REPO = "https://github.com/nazrulhuda/filingcheck";
const REPORT = `${REPO}/blob/main/${RESULTS.report}`;
const MAX_QUESTION = 500;
const HEALTH_TIMEOUT_MS = 3000;
const WAKE_RETRY_MS = 5000;
const WAKE_GIVE_UP_MS = 70_000;
const NO_STEPS: Progress = { steps: [], restarted: null };
const WIDE = "(min-width: 640px)";

/** A finished tool call's status in words. */
function statusWords(status: string): string {
  if (status === "ok") return "done";
  if (status === "skipped") return "not run (tool-call limit reached)";
  return "no result";
}

type Backend = "checking" | "waking" | Health;

type Shown =
  | { kind: "none" }
  | { kind: "streaming"; text: string; progress: Progress }
  | {
      kind: "answer";
      question: string;
      answer: Answer;
      source: AnswerSource;
      notice: string | null;
      /** For a clicked example: the filters it was asked with, and any review note. */
      asked?: string;
      note?: string | null;
    }
  | { kind: "error"; message: string };

const RESULTS_TITLE = "What the measurement found";
const BOX =
  "mt-5 rounded-md border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700";

function ResultsBody() {
  return (
    <>
      <ul className="mt-1 list-disc space-y-1 pl-5">
        {resultLines(RESULTS).map((line) => (
          <li key={line.lead}>
            <span className="font-medium">{line.lead}</span> {line.rest}
          </li>
        ))}
      </ul>
      <p className="mt-2">
        <a href={REPORT} className="text-blue-700 underline hover:text-blue-900">
          The full report
        </a>
      </p>
    </>
  );
}

/** The measured result in the README's three lines; every number from results.json. On
 * phones a closed panel, so the question box is not pushed far down; on wider screens open. */
function ResultsStrip() {
  return (
    <>
      <details className={`${BOX} sm:hidden`}>
        <summary className="cursor-pointer font-medium text-slate-800">
          {RESULTS_TITLE}
        </summary>
        <ResultsBody />
      </details>
      <section aria-labelledby="results-title" className={`${BOX} hidden sm:block`}>
        <h2 id="results-title" className="font-medium text-slate-800">
          {RESULTS_TITLE}
        </h2>
        <ResultsBody />
      </section>
    </>
  );
}

/** What the data holds and what it cannot answer: open on wide screens, closed on phones. */
function WhatYouCanAsk({ companies }: { companies: Company[] }) {
  const panel = useRef<HTMLDetailsElement>(null);
  useEffect(() => {
    if (panel.current && window.matchMedia(WIDE).matches) panel.current.open = true;
  }, []);
  return (
    <details
      ref={panel}
      className="mt-5 rounded-md border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700"
    >
      <summary className="cursor-pointer font-medium text-slate-800">
        What you can ask
      </summary>
      <ul className="mt-2 list-disc space-y-1 pl-5">
        <li>
          <span className="font-medium">Numbers:</span> the {METRICS.length}{" "}
          metrics below, annual, for the company as a whole, from each
          filing&apos;s own XBRL data: {METRICS.map(([, name]) => name).join(", ")}.
        </li>
        <li>
          <span className="font-medium">Text:</span> what the 10-K passages say,
          for example about risks, legal claims or currency exposure.
        </li>
        <li>
          <span className="font-medium">It cannot answer:</span>{" "}
          {CANNOT.join("; ")}.
        </li>
        <li>Each question stands alone (no chat history).</li>
      </ul>
      <details className="mt-3">
        <summary className="cursor-pointer font-medium text-slate-800">
          The 25 companies and the fiscal years held
        </summary>
        {companies.length > 0 ? (
          <ul className="mt-1 grid gap-x-6 gap-y-0.5 text-xs text-slate-600 sm:grid-cols-2">
            {companies.map((c) => (
              <li key={c.ticker}>
                {c.name} ({c.ticker}): {c.fiscal_years.join(", ")}
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-1 text-xs text-slate-500">
            The list appears when the backend answers.
          </p>
        )}
      </details>
    </details>
  );
}

export default function Home() {
  const [backend, setBackend] = useState<Backend>("checking");
  const [companies, setCompanies] = useState<Company[]>([]);
  const [question, setQuestion] = useState("");
  const [ticker, setTicker] = useState("");
  const [year, setYear] = useState("");
  const [checks, setChecks] = useState(true);
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
    let progress = NO_STEPS;
    let soFar = "";
    setShown({ kind: "streaming", text: "", progress });
    try {
      const result = await askStreaming(
        pageQuestion(text, ticker, year, checks),
        (received) => {
          soFar = received;
          setShown({ kind: "streaming", text: soFar, progress });
        },
        (next) => {
          progress = next;
          setShown({ kind: "streaming", text: soFar, progress });
        },
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
      asked: askedWith(
        example.company_name,
        example.ticker,
        example.fiscal_year,
      ),
      note: reviewNote(example.question),
    });
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-8 sm:py-12">
      <h1 className="text-2xl font-semibold tracking-tight">FilingCheck</h1>
      <p className="mt-1 text-sm text-slate-600">
        Questions about the 10-K filings of 25 public companies, answered from
        the filings&apos; text and their own XBRL numbers; the model is asked to
        cite a passage or a fact for each claim.
      </p>

      <p className="mt-4 rounded-md border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
        The model answers with three tools. Before each tool call runs, the
        server checks it against the question and the data: it can correct the
        call or send it back to the model. Every number in the answer is then
        labeled against the sources the answer used.
      </p>

      <ResultsStrip />

      {backend === "waking" && (
        <p className="mt-4 rounded-md bg-slate-100 px-3 py-2 text-sm text-slate-700">
          The backend is waking up (up to a minute). The saved examples below
          work meanwhile.
        </p>
      )}
      {backend === "unreachable" && (
        <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-800">
          The backend is not answering right now. The saved examples below still
          work.
        </p>
      )}
      {backend === "no-model" && (
        <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-800">
          The backend is up but has no language model configured right now.
        </p>
      )}

      <WhatYouCanAsk companies={companies} />

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
          Each question stands alone (no chat history). Questions are logged to
          improve the demo. Each question is sent to OpenAI to search the
          filings, and through OpenRouter to Groq, or to Google if that is busy,
          to write the answer; please don&apos;t enter personal information.
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
          <div className="text-sm sm:ml-auto">
            <label className="flex cursor-pointer items-center gap-2 text-slate-700">
              <input
                type="checkbox"
                checked={checks}
                onChange={(e) => setChecks(e.target.checked)}
                aria-describedby="checks-hint"
                className="h-4 w-4"
              />
              Skeptical checks: {checks ? "on" : "off"}
            </label>
            <p id="checks-hint" className="mt-0.5 text-xs text-slate-500">
              Turn the checks off and ask the same question to compare.
            </p>
          </div>
        </div>
      </form>

      <section className="mt-6">
        <h2 className="text-sm font-medium text-slate-600">Examples</h2>
        <div className="mt-2 flex flex-wrap gap-2">
          {PLAIN.map((example) => (
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

      <section className="mt-6" aria-labelledby="traps-title">
        <h2 id="traps-title" className="text-sm font-medium text-slate-600">
          Try a trap question
        </h2>
        <p className="mt-0.5 text-xs text-slate-500">{TRAP_NOTE}</p>
        <div className="mt-2 flex flex-wrap gap-2">
          {TRAPS.map((trap) => (
            <button
              key={trap.id}
              type="button"
              onClick={() => showExample(trap)}
              className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-left text-sm hover:border-blue-600 hover:text-blue-800"
            >
              <span className="block">{trap.question}</span>
              <span className="block text-xs text-slate-500">{trap.trap}</span>
            </button>
          ))}
        </div>
      </section>

      <section className="mt-8" aria-live="polite">
        {shown.kind === "streaming" && (
          <div className="rounded-md border border-slate-200 bg-white p-4">
            {shown.progress.restarted && (
              <p className="mb-2 text-sm text-slate-500">
                {shown.progress.restarted}
              </p>
            )}
            {shown.progress.steps.length > 0 && (
              <ul className="mb-3 space-y-1 text-sm text-slate-600">
                {shown.progress.steps.map((step, i) => (
                  <li key={i}>
                    {step.label}…{" "}
                    <span className="text-slate-400">
                      {statusWords(step.status)}
                    </span>
                  </li>
                ))}
              </ul>
            )}
            <p className="whitespace-pre-line leading-7 text-slate-800">
              {shown.text || "Working on it…"}
            </p>
          </div>
        )}
        {shown.kind === "answer" && (
          <div className="rounded-md border border-slate-200 bg-white p-4">
            {shown.notice ? (
              <p
                role="status"
                className="mb-3 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-900"
              >
                {shown.notice}
              </p>
            ) : (
              <div className="mb-3">
                <p className="text-sm font-medium text-slate-600">
                  {shown.question}
                </p>
                {shown.asked && (
                  <p className="mt-0.5 text-xs text-slate-500">{shown.asked}</p>
                )}
              </div>
            )}
            {/* A new answer starts with every citation closed. */}
            <AnswerText
              key={`${shown.question}\n${shown.answer.text}`}
              answer={shown.answer}
            />
            {shown.note && (
              <p className="mt-3 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
                {shown.note}
              </p>
            )}
            <ChecksPanel answer={shown.answer} />
            <CostLine answer={shown.answer} source={shown.source} />
          </div>
        )}
        {shown.kind === "error" && (
          <p
            role="alert"
            className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-800"
          >
            {shown.message}
          </p>
        )}
      </section>

      <LabelGuide />

      <footer className="mt-10 border-t border-slate-200 pt-4 text-xs text-slate-500">
        <a href={REPO} className="text-blue-700 underline hover:text-blue-900">
          The code on GitHub
        </a>
        {" · "}
        <a href={REPORT} className="text-blue-700 underline hover:text-blue-900">
          The full results report
        </a>
      </footer>
    </main>
  );
}
