"use client";

import { type FormEvent, useEffect, useRef, useState } from "react";

import {
  AnswerText,
  ChecksPanel,
  CostLine,
  LabelGuide,
} from "@/components/AnswerView";
import { Icon, INSIDE_ICONS, STEP_ICONS } from "@/components/Icons";
import { Logo } from "@/components/Logo";
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
import {
  answerInView,
  cardLine,
  CHIPS,
  type Chip,
  enterAsks,
  FIRST_EXAMPLE,
  INSIDE,
  JUMP_LINKS,
  MORE_CHIPS,
  PRIVACY_NOTE,
  resultTiles,
  scrollBehavior,
  SENTENCE,
  STACK,
  STEPS,
  TRAP_LINE,
} from "@/lib/glance";
import { reviewNote } from "@/lib/notes";
import { type Results, resultLines } from "@/lib/results";
import { type Example, type TrapExample, trapExamples } from "@/lib/traps";

const EXAMPLES = examplesData as Example[];
const TRAPS = trapExamples(trapData as TrapExample[], EXAMPLES);
const TRAP_QUESTIONS = new Set(TRAPS.map((t) => t.question));
const SAVED = new Map<string, Example>([...EXAMPLES, ...TRAPS].map((e) => [e.question, e]));
const RESULTS = resultsData as Results;
const REPO = "https://github.com/nazrulhuda/filingcheck";
const REPORT = `${REPO}/blob/main/${RESULTS.report}`;
const PREREGISTRATION = `${REPO}/blob/main/eval/PREREGISTRATION.md`;
const KNOWN_LIMITS = `${REPO}#known-limits`;
const MAX_QUESTION = 500;
const HEALTH_TIMEOUT_MS = 3000;
const WAKE_RETRY_MS = 5000;
const WAKE_GIVE_UP_MS = 70_000;
const NO_STEPS: Progress = { steps: [], restarted: null };
// The question box grows with its text up to six rows: 6 × 28 px lines + 16 px padding + border.
const BOX_MAX_PX = 6 * 28 + 16 + 2;
const CHECKS_HINT = "Turn the checks off and ask the same question to compare.";

const LINK = "text-accent underline hover:text-accent-strong";
const BOX = "rounded-md border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700";
const TILE = "rounded-lg border border-slate-200 bg-white p-4";
const SECTION_TITLE = "text-lg font-semibold text-slate-900";
const CHIP =
  "rounded-full border border-slate-300 bg-white px-2.5 py-1 text-[13px] text-slate-700 hover:border-accent hover:text-accent-strong";
// The answer card is the only box with an accent border, and its strip says what it holds.
const CARD = "overflow-hidden rounded-lg border-2 border-accent bg-white";
const STRIP = "bg-accent-soft px-4 py-1.5 text-xs font-semibold text-accent-strong";

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
      /** A saved trap example: its strip says it was chosen. */
      trap?: boolean;
    }
  | { kind: "error"; message: string };

/** A saved example's answer as the page shows it, with no request made. */
function exampleShown(example: Example): Shown {
  return {
    kind: "answer",
    question: example.question,
    answer: example.answer,
    source: "example",
    notice: null,
    asked: askedWith(example.company_name, example.ticker, example.fiscal_year),
    note: reviewNote(example.question),
    trap: TRAP_QUESTIONS.has(example.question),
  };
}

const FIRST = SAVED.get(FIRST_EXAMPLE);
const FIRST_SHOWN: Shown = FIRST ? exampleShown(FIRST) : { kind: "none" };

/** What the data holds and what it cannot answer: closed until opened, on every screen. */
function WhatYouCanAsk({ companies }: { companies: Company[] }) {
  return (
    <details className={`mt-12 ${BOX}`}>
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

/** Three steps in a row (stacked on phones); the earlier explainer, unchanged, in a closed panel. */
function HowItWorks() {
  return (
    <section id="how-it-works" className="mt-12 scroll-mt-4" aria-labelledby="how-title">
      <h2 id="how-title" className={SECTION_TITLE}>
        How it works
      </h2>
      <ol className="mt-3 grid gap-3 sm:grid-cols-3">
        {STEPS.map((step, i) => (
          <li key={step} className={`${TILE} flex items-center gap-3 text-sm text-slate-800`}>
            <Icon name={STEP_ICONS[i]} />
            <span>
              {i + 1}. {step}
            </span>
          </li>
        ))}
      </ol>
      <details className={`mt-3 ${BOX}`}>
        <summary className="cursor-pointer font-medium text-slate-800">In more detail</summary>
        <p className="mt-2">
          The model answers with three tools. Before each tool call runs, the
          server checks it against the question and the data: it can correct the
          call or send it back to the model. Every number in the answer is then
          labeled against the sources the answer used.
        </p>
      </details>
      <LabelGuide />
    </section>
  );
}

/** The measured result as four tiles in the README's order; the README's three lines, unchanged,
 * in a closed panel. Every number is from results.json or checked against the report. */
function ResultsSection() {
  return (
    <section id="results" className="mt-12 scroll-mt-4" aria-labelledby="results-title">
      <h2 id="results-title" className={SECTION_TITLE}>
        What the measurement found
      </h2>
      <p className="mt-1 text-sm text-slate-600">{TRAP_LINE}</p>
      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        {resultTiles(RESULTS).map((tile) => (
          <div key={tile.figure} className={TILE}>
            <p className="text-2xl font-semibold tabular-nums text-accent-strong">
              {tile.figure}
            </p>
            <p className="mt-1 text-sm text-slate-700">{tile.text}</p>
            {tile.note && <p className="mt-2 text-xs text-slate-500">{tile.note}</p>}
          </div>
        ))}
      </div>
      <p className="mt-3 text-sm">
        <a href={REPORT} className={LINK}>
          The full report
        </a>
      </p>
      <details className={`mt-3 ${BOX}`}>
        <summary className="cursor-pointer font-medium text-slate-800">Details</summary>
        <ul className="mt-2 list-disc space-y-1 pl-5">
          {resultLines(RESULTS).map((line) => (
            <li key={line.lead}>
              <span className="font-medium">{line.lead}</span> {line.rest}
            </li>
          ))}
        </ul>
      </details>
    </section>
  );
}

/** One tile per part of the system: what it is, with no claim about its effect. */
function Inside() {
  return (
    <section id="whats-inside" className="mt-12 scroll-mt-4" aria-labelledby="inside-title">
      <h2 id="inside-title" className={SECTION_TITLE}>
        What&apos;s inside
      </h2>
      <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {INSIDE.map((tile) => (
          <div key={tile.name} className={`${TILE} flex gap-3`}>
            <Icon name={INSIDE_ICONS[tile.name]} />
            <div>
              <p className="text-sm font-semibold text-slate-900">{tile.name}</p>
              <p className="mt-1 text-sm text-slate-700">{tile.text}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="mt-12 space-y-2 border-t border-slate-200 pt-5 text-sm text-slate-600">
      <p>
        Built by Nazrul Huda Shanto
        {" · "}
        <a href="https://github.com/nazrulhuda" className={LINK}>
          GitHub
        </a>
        {" · "}
        <a href="https://www.linkedin.com/in/mshanto/" className={LINK}>
          LinkedIn
        </a>
        {" · "}
        <a href="https://dev.nazrulhuda.com" className={LINK}>
          dev.nazrulhuda.com
        </a>
      </p>
      <p>
        <a href={REPO} className={LINK}>
          Code
        </a>
        {" · "}
        <a href={REPORT} className={LINK}>
          Full report
        </a>
        {" · "}
        <a href={PREREGISTRATION} className={LINK}>
          Pre-registration
        </a>
        {" · "}
        <a href={KNOWN_LIMITS} className={LINK}>
          Known limits
        </a>
      </p>
      <p className="text-xs text-slate-500">{STACK}</p>
    </footer>
  );
}

export default function Home() {
  const [backend, setBackend] = useState<Backend>("checking");
  const [companies, setCompanies] = useState<Company[]>([]);
  const [question, setQuestion] = useState("");
  const [ticker, setTicker] = useState("");
  const [year, setYear] = useState("");
  const [checks, setChecks] = useState(true);
  const [shown, setShown] = useState<Shown>(FIRST_SHOWN);
  const [busy, setBusy] = useState(false);
  const [more, setMore] = useState(false);
  // Counts requests to bring the answer card into view: an answer starting, or a chip clicked.
  const [reveal, setReveal] = useState(0);
  const box = useRef<HTMLTextAreaElement>(null);
  const answerArea = useRef<HTMLElement>(null);

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

  // The question box grows with its text, from three rows up to six.
  useEffect(() => {
    const el = box.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight + 2, BOX_MAX_PX)}px`;
  }, [question]);

  // Bring the answer card into view if its top is off the screen.
  useEffect(() => {
    const el = answerArea.current;
    if (reveal === 0 || !el) return;
    if (answerInView(el.getBoundingClientRect().top, window.innerHeight)) return;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    el.scrollIntoView({ behavior: scrollBehavior(reduced), block: "start" });
  }, [reveal]);

  const years = companies.find((c) => c.ticker === ticker)?.fiscal_years ?? [];
  const canAsk = !busy && question.trim() !== "" && backend === "ok";

  async function submit(event: FormEvent) {
    event.preventDefault();
    const text = question.trim();
    if (!text || busy) return;
    setBusy(true);
    let progress = NO_STEPS;
    let soFar = "";
    setShown({ kind: "streaming", text: "", progress });
    setReveal((n) => n + 1);
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
        trap: Boolean(result.cached && result.example && TRAP_QUESTIONS.has(result.example.question)),
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

  function showChip(chip: Chip) {
    const example = SAVED.get(chip.question);
    if (!example) return;
    setQuestion(example.question);
    setTicker(example.ticker ?? "");
    setYear(example.fiscal_year ? String(example.fiscal_year) : "");
    setShown(exampleShown(example));
    setReveal((n) => n + 1);
  }

  function chipButton(chip: Chip) {
    return (
      <button
        key={chip.question}
        type="button"
        onClick={() => showChip(chip)}
        title={chip.question}
        aria-label={chip.question}
        className={CHIP}
      >
        {chip.label}
      </button>
    );
  }

  return (
    <>
      <header className="border-b border-slate-200 bg-band">
        <div className="mx-auto flex max-w-5xl flex-col gap-1.5 px-4 py-3 sm:flex-row sm:items-center sm:gap-6">
          <Logo />
          <div>
            <p className="text-sm text-slate-700 sm:text-[15px]">{SENTENCE}</p>
            <nav aria-label="On this page" className="mt-1 flex flex-wrap gap-x-4 text-sm">
              {JUMP_LINKS.map((link) => (
                <a key={link.href} href={link.href} className={LINK}>
                  {link.label}
                </a>
              ))}
            </nav>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 pb-8 pt-3">
        {backend === "waking" && (
          <p className="mb-3 rounded-md bg-slate-100 px-3 py-2 text-sm text-slate-700">
            The backend is waking up (up to a minute). The saved examples below
            work meanwhile.
          </p>
        )}
        {backend === "unreachable" && (
          <p className="mb-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-800">
            The backend is not answering right now. The saved examples below still
            work.
          </p>
        )}
        {backend === "no-model" && (
          <p className="mb-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-800">
            The backend is up but has no language model configured right now.
          </p>
        )}

        <form onSubmit={submit}>
          <label htmlFor="question" className="sr-only">
            Your question
          </label>
          <textarea
            id="question"
            ref={box}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => {
              if (!enterAsks(e.key, e.shiftKey, e.nativeEvent.isComposing)) return;
              e.preventDefault();
              if (canAsk) e.currentTarget.form?.requestSubmit();
            }}
            maxLength={MAX_QUESTION}
            rows={3}
            placeholder="For example: What does Netflix say about intellectual-property claims?"
            style={{ maxHeight: BOX_MAX_PX }}
            className="block w-full resize-none overflow-y-auto rounded-lg border border-slate-400 bg-white px-3 py-2 text-lg leading-7 text-slate-900 focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/40"
          />
          <div className="mt-2 flex flex-wrap items-end gap-x-3 gap-y-2">
            <label className="min-w-[9rem] flex-1 text-xs sm:flex-none">
              <span className="block text-slate-600">Company (optional)</span>
              <select
                value={ticker}
                onChange={(e) => {
                  setTicker(e.target.value);
                  setYear("");
                }}
                disabled={companies.length === 0}
                className="mt-0.5 w-full rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm sm:w-60"
              >
                <option value="">Any company</option>
                {companies.map((c) => (
                  <option key={c.ticker} value={c.ticker}>
                    {c.name} ({c.ticker})
                  </option>
                ))}
              </select>
            </label>
            <label className="text-xs">
              <span className="block text-slate-600">Fiscal year (optional)</span>
              <select
                value={year}
                onChange={(e) => setYear(e.target.value)}
                disabled={years.length === 0}
                className="mt-0.5 rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm"
              >
                <option value="">Any year</option>
                {years.map((y) => (
                  <option key={y} value={y}>
                    {y}
                  </option>
                ))}
              </select>
            </label>
            <label
              title={CHECKS_HINT}
              className="flex cursor-pointer items-center gap-2 py-1.5 text-sm text-slate-700"
            >
              <input
                type="checkbox"
                checked={checks}
                onChange={(e) => setChecks(e.target.checked)}
                aria-describedby="checks-hint"
                className="h-4 w-4 accent-accent"
              />
              Skeptical checks: {checks ? "on" : "off"}
              <span id="checks-hint" className="sr-only">
                {CHECKS_HINT}
              </span>
            </label>
            <button
              type="submit"
              disabled={!canAsk}
              className="ml-auto rounded-md bg-accent px-6 py-2 text-sm font-medium text-white hover:bg-accent-strong disabled:cursor-not-allowed disabled:bg-slate-300"
            >
              {busy ? "Answering…" : "Ask"}
            </button>
          </div>
          <p className="mt-1.5 text-xs text-slate-500">{PRIVACY_NOTE}</p>
        </form>

        <div className="mt-2 flex flex-wrap items-center gap-1.5" role="group" aria-label="Saved examples">
          <span className="mr-0.5 text-sm font-medium text-slate-700">Try:</span>
          {CHIPS.map(chipButton)}
          <button
            type="button"
            onClick={() => setMore((open) => !open)}
            aria-expanded={more}
            aria-controls="more-examples"
            className={CHIP}
          >
            {more ? "Fewer" : "More"}
          </button>
          <span id="more-examples" hidden={!more} className="contents">
            {MORE_CHIPS.map(chipButton)}
          </span>
        </div>

        <section ref={answerArea} className="mt-3 scroll-mt-4" aria-live="polite">
          {shown.kind === "streaming" && (
            <div className={CARD}>
              <p className={STRIP}>{cardLine("working", false)}</p>
              <div className="px-4 py-3">
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
            </div>
          )}
          {shown.kind === "answer" && (
            <div className={CARD}>
              <p className={STRIP}>
                {cardLine(shown.source === "new" ? "new" : shown.source, Boolean(shown.trap))}
              </p>
              <div className="px-4 py-3">
                {shown.notice ? (
                  <p
                    role="status"
                    className="mb-3 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-900"
                  >
                    {shown.notice}
                  </p>
                ) : (
                  <p className="mb-2 text-sm font-medium text-slate-600">
                    {shown.question}
                    {shown.asked && (
                      <span className="ml-2 inline-block text-xs font-normal text-slate-500">{shown.asked}</span>
                    )}
                  </p>
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

        <WhatYouCanAsk companies={companies} />
        <HowItWorks />
        <ResultsSection />
        <Inside />
        <Footer />
      </main>
    </>
  );
}
