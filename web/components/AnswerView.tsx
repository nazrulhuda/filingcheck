"use client";

import { Fragment, useState } from "react";

import type { Answer } from "@/lib/api";
import { type Citation, segments } from "@/lib/citations";
import { type AnswerSource, costLine } from "@/lib/display";

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

/** The answer text with each citation marker as a chip that opens its passage. */
export function AnswerText({ answer }: { answer: Answer }) {
  const [open, setOpen] = useState<number | null>(null);
  const parts = segments(answer.text, answer.citations);
  const opened = answer.citations.find((c) => c.number === open);
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
                  key={c.number}
                  type="button"
                  onClick={() => setOpen(open === c.number ? null : c.number)}
                  aria-expanded={open === c.number}
                  title={`${c.ticker} FY${c.fiscal_year}, Item ${c.item}`}
                  className={`rounded px-1.5 text-xs font-semibold leading-5 ${
                    open === c.number
                      ? "bg-blue-700 text-white"
                      : "bg-blue-100 text-blue-800 hover:bg-blue-200"
                  }`}
                >
                  {c.number}
                </button>
              ))}
            </span>
          ),
        )}
      </p>
      {opened && <CitationDetail citation={opened} />}
    </div>
  );
}

/** Who answered, how long it took and what it cost. */
export function CostLine({ answer, source }: { answer: Answer; source: AnswerSource }) {
  return <p className="mt-4 text-xs text-slate-500">{costLine(answer, source)}</p>;
}
