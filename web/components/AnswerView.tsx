"use client";

import { Fragment, useState } from "react";

import type { Answer } from "@/lib/api";
import { checkSummary } from "@/lib/checks";
import { type Citation, type FactCitation, segments } from "@/lib/citations";
import { type AnswerSource, costLine } from "@/lib/display";
import { factDetail } from "@/lib/facts";

/** **bold** inside a run of answer text; everything else is shown as written. */
function Emphasis({ text }: { text: string }) {
  const pieces = text.split(/(\*\*[^*]+\*\*)/g);
  return (
    <>
      {pieces.map((piece, i) =>
        piece.startsWith("**") && piece.endsWith("**") && piece.length > 4 ? (
          <strong key={i}>{piece.slice(2, -2)}</strong>
        ) : (
          <Fragment key={i}>{piece}</Fragment>
        ),
      )}
    </>
  );
}

function CitationDetail({ citation }: { citation: Citation }) {
  return (
    <div className="mt-2 rounded-md border border-slate-200 bg-white p-3 text-sm">
      <div className="font-medium text-slate-700">
        [{citation.number}] {citation.ticker}, fiscal year {citation.fiscal_year}, Item{" "}
        {citation.item}
      </div>
      <p className="mt-1 whitespace-pre-line text-slate-600">{citation.quote}…</p>
      <a
        className="mt-2 inline-block text-blue-700 underline hover:text-blue-900"
        href={citation.source_url}
        target="_blank"
        rel="noreferrer"
      >
        Open the SEC document
      </a>
    </div>
  );
}

function FactDetailView({ fact, answer }: { fact: FactCitation; answer: Answer }) {
  const detail = factDetail(fact, answer.facts_used ?? []);
  return (
    <div className="mt-2 rounded-md border border-slate-200 bg-white p-3 text-sm">
      <div className="font-medium text-slate-700">{detail.title}</div>
      <dl className="mt-1 grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5 text-slate-600">
        <dt className="text-slate-500">Line</dt>
        <dd>{detail.label}</dd>
        <dt className="text-slate-500">Value as filed</dt>
        <dd className="break-all">{detail.value}</dd>
        {detail.period && (
          <>
            <dt className="text-slate-500">Period</dt>
            <dd>{detail.period}</dd>
          </>
        )}
      </dl>
      <a
        className="mt-2 inline-block text-blue-700 underline hover:text-blue-900"
        href={detail.link}
        target="_blank"
        rel="noreferrer"
      >
        Open the SEC document
      </a>
    </div>
  );
}

function chipClass(isOpen: boolean, fact: boolean): string {
  if (isOpen) return fact ? "bg-emerald-700 text-white" : "bg-blue-700 text-white";
  return fact
    ? "bg-emerald-100 text-emerald-800 hover:bg-emerald-200"
    : "bg-blue-100 text-blue-800 hover:bg-blue-200";
}

/** The answer text with each citation marker as a chip that opens its passage or fact. */
export function AnswerText({ answer }: { answer: Answer }) {
  // "p3" is passage 3, "f1" is fact [F1].
  const [open, setOpen] = useState<string | null>(null);
  const facts = answer.fact_citations ?? [];
  const parts = segments(answer.text, answer.citations, facts);
  const toggle = (key: string) => setOpen(open === key ? null : key);
  const openedPassage = answer.citations.find((c) => `p${c.number}` === open);
  const openedFact = facts.find((f) => `f${f.number}` === open);
  return (
    <div>
      <p className="whitespace-pre-line leading-7">
        {parts.map((part, i) =>
          part.kind === "text" ? (
            <Emphasis key={i} text={part.text} />
          ) : (
            <span key={i} className="mx-0.5 inline-flex gap-0.5 align-baseline">
              {part.citations.map((c) => (
                <button
                  key={`p${c.number}`}
                  type="button"
                  onClick={() => toggle(`p${c.number}`)}
                  aria-expanded={open === `p${c.number}`}
                  title={`${c.ticker} FY${c.fiscal_year}, Item ${c.item}`}
                  className={`rounded px-1.5 text-xs font-semibold leading-5 ${chipClass(open === `p${c.number}`, false)}`}
                >
                  {c.number}
                </button>
              ))}
              {part.facts.map((f) => (
                <button
                  key={`f${f.number}`}
                  type="button"
                  onClick={() => toggle(`f${f.number}`)}
                  aria-expanded={open === `f${f.number}`}
                  title="A number from the filing's XBRL data"
                  className={`rounded px-1.5 text-xs font-semibold leading-5 ${chipClass(open === `f${f.number}`, true)}`}
                >
                  F{f.number}
                </button>
              ))}
            </span>
          ),
        )}
      </p>
      {openedPassage && <CitationDetail citation={openedPassage} />}
      {openedFact && <FactDetailView fact={openedFact} answer={answer} />}
    </div>
  );
}

/** The agent's override log in plain words; shown for agent answers only. */
export function ChecksPanel({ answer }: { answer: Answer }) {
  if (answer.mode !== "agent") return null;
  const { summary, lookups } = checkSummary(answer.overrides ?? []);
  return (
    <section className="mt-4 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700">
      <h3 className="font-medium text-slate-800">What was checked</h3>
      <p className="mt-1">{summary}</p>
      {lookups.map((lines, i) => (
        <div key={i} className="mt-2">
          {lookups.length > 1 && <p className="text-xs font-medium text-slate-500">Lookup {i + 1}</p>}
          <ul className="list-disc space-y-0.5 pl-5">
            {lines.map((line, j) => (
              <li key={j}>{line}</li>
            ))}
          </ul>
        </div>
      ))}
    </section>
  );
}

/** Who answered, how long it took and what it cost. */
export function CostLine({ answer, source }: { answer: Answer; source: AnswerSource }) {
  return <p className="mt-4 text-xs text-slate-500">{costLine(answer, source)}</p>;
}
