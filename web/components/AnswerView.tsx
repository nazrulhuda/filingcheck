"use client";

import { Fragment, useState } from "react";

import type { Answer } from "@/lib/api";
import { checkReport } from "@/lib/checks";
import { type Citation, type FactCitation, segments } from "@/lib/citations";
import { type AnswerSource, costLine } from "@/lib/display";
import { factDetail, lineHeading } from "@/lib/facts";
import {
  BADGES,
  LABEL_KEY,
  LABEL_LINES,
  type NumberLabel,
  VERIFIED_CAVEAT,
  badgeText,
  hasBadges,
  withBadges,
} from "@/lib/labels";
import { mathText } from "@/lib/math";

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
        [{citation.number}] {citation.ticker}, fiscal year{" "}
        {citation.fiscal_year}, Item {citation.item}
      </div>
      <div className="mt-1 max-h-48 overflow-y-auto whitespace-pre-line break-words rounded border border-slate-100 bg-slate-50 p-2 text-slate-600">
        {citation.text || `${citation.quote}…`}
      </div>
      <a
        className="mt-2 inline-block text-accent underline hover:text-accent-strong"
        href={citation.source_url}
        target="_blank"
        rel="noreferrer"
      >
        Open the SEC document
      </a>
    </div>
  );
}

function FactDetailView({
  fact,
  answer,
}: {
  fact: FactCitation;
  answer: Answer;
}) {
  const detail = factDetail(fact, answer.facts_used ?? []);
  return (
    <div className="mt-2 rounded-md border border-slate-200 bg-white p-3 text-sm">
      <div className="font-medium text-slate-700">{detail.title}</div>
      <dl className="mt-1 grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5 text-slate-600">
        <dt className="text-slate-500">{lineHeading(fact)}</dt>
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
        className="mt-2 inline-block text-accent underline hover:text-accent-strong"
        href={detail.link}
        target="_blank"
        rel="noreferrer"
      >
        Open the SEC document
      </a>
    </div>
  );
}

// Green, red and amber (app/globals.css; they pass the contrast checks in lib/theme.test.ts),
// with a different symbol for each label, so the colour is never the only cue.
const BADGE_CLASS: Record<NumberLabel["label"], string> = {
  verified: "border-verified-line bg-verified-bg text-verified",
  unverified: "border-unverified-line bg-unverified-bg text-unverified",
  conflict: "border-conflict-line bg-conflict-bg text-conflict",
};

/** The three labels, one line each, with the badges the answers use. */
export function LabelGuide() {
  return (
    <section className="mt-6 text-sm text-slate-700" aria-labelledby="labels-title">
      <h2 id="labels-title" className="text-sm font-medium text-slate-800">
        The three labels on a number
      </h2>
      <ul className="mt-2 space-y-1">
        {LABEL_LINES.map(({ label, line }) => (
          <li key={label} className="flex gap-2">
            <span
              aria-hidden="true"
              className={`mt-0.5 inline-flex h-4 min-w-4 shrink-0 items-center justify-center rounded border px-0.5 text-[10px] font-bold leading-none ${BADGE_CLASS[label]}`}
            >
              {BADGES[label].symbol}
            </span>
            <span>
              <span className="font-medium">{BADGES[label].name}</span>: {line}.
            </span>
          </li>
        ))}
      </ul>
      <p className="mt-2 text-slate-500">{VERIFIED_CAVEAT}</p>
    </section>
  );
}

/** A figure's label: a small badge; hover shows its text, a tap shows it beside the badge. */
function LabelBadge({
  label,
  text,
  isOpen,
  onToggle,
}: {
  label: NumberLabel;
  text: string;
  isOpen: boolean;
  onToggle: () => void;
}) {
  const badge = BADGES[label.label];
  return (
    <>
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={isOpen}
        aria-label={`${badge.name}: ${text}`}
        title={text}
        className={`ml-0.5 inline-flex h-4 min-w-4 items-center justify-center rounded border px-0.5 align-text-top text-[10px] font-bold leading-none ${BADGE_CLASS[label.label]}`}
      >
        {badge.symbol}
      </button>
      {isOpen && (
        <span className="ml-1 rounded bg-slate-100 px-1 text-xs text-slate-700 [overflow-wrap:anywhere]">
          {badge.name}: {text}
        </span>
      )}
    </>
  );
}

// Citation chips in the accent: a filled chip for a passage, an outlined "F" chip for a fact.
// Green is kept for the Verified label.
function chipClass(isOpen: boolean, fact: boolean): string {
  if (isOpen)
    return fact ? "bg-accent-strong text-white" : "bg-accent text-white";
  return fact
    ? "bg-white text-accent-strong ring-1 ring-inset ring-accent/50 hover:bg-accent-soft"
    : "bg-accent-soft text-accent-strong hover:ring-1 hover:ring-inset hover:ring-accent";
}

/** The answer text with each citation marker as a chip that opens its passage or fact. */
export function AnswerText({ answer }: { answer: Answer }) {
  // "p3" is passage 3, "f1" is fact [F1].
  const [open, setOpen] = useState<string | null>(null);
  // "b2" is the badge at piece 2; one badge's text is shown at a time.
  const [openBadge, setOpenBadge] = useState<string | null>(null);
  const facts = answer.fact_citations ?? [];
  const parts = withBadges(
    segments(answer.text, answer.citations, facts),
    answer.number_labels ?? [],
  );
  const toggle = (key: string) => setOpen(open === key ? null : key);
  const openedPassage = answer.citations.find((c) => `p${c.number}` === open);
  const openedFact = facts.find((f) => `f${f.number}` === open);
  return (
    <div>
      <p className="whitespace-pre-line leading-7">
        {parts.map((part, i) =>
          part.kind === "text" ? (
            <Emphasis key={i} text={mathText(part.text)} />
          ) : part.kind === "badge" ? (
            <LabelBadge
              key={i}
              label={part.label}
              text={badgeText(part.label, facts)}
              isOpen={openBadge === `b${i}`}
              onToggle={() =>
                setOpenBadge(openBadge === `b${i}` ? null : `b${i}`)
              }
            />
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
      {hasBadges(answer) && (
        <p className="mt-2 text-xs text-slate-500">{LABEL_KEY}</p>
      )}
      {openedPassage && <CitationDetail citation={openedPassage} />}
      {openedFact && <FactDetailView fact={openedFact} answer={answer} />}
    </div>
  );
}

/** The agent's override log in plain words; shown for agent answers only. */
export function ChecksPanel({ answer }: { answer: Answer }) {
  if (answer.mode !== "agent") return null;
  const { summary, lookups } = checkReport(answer);
  return (
    <section className="mt-3 rounded-md border-l-4 border-slate-300 bg-slate-50 px-3 py-2 text-sm text-slate-700">
      <h3 className="font-medium text-slate-800">What was checked</h3>
      <p className="mt-1">{summary}</p>
      {lookups.map((lines, i) => (
        <div key={i} className="mt-2">
          {lookups.length > 1 && (
            <p className="text-xs font-medium text-slate-500">Lookup {i + 1}</p>
          )}
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
export function CostLine({
  answer,
  source,
}: {
  answer: Answer;
  source: AnswerSource;
}) {
  return (
    <p className="mt-2 text-xs text-slate-500">{costLine(answer, source)}</p>
  );
}
