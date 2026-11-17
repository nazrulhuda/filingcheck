// The About page: the README's own sections, read from README.md at build time and shown in the
// site's style. It adds no wording about results; lib/readme.ts splits the README, this renders it.
import { readFileSync } from "node:fs";
import { join } from "node:path";

import type { Metadata } from "next";
import { Fragment } from "react";

import { Footer, TopBar } from "@/components/SiteChrome";
import {
  ABOUT_TITLE,
  type Block,
  type InlineNode,
  imageSrc,
  inline,
  readmeDescription,
  readmeSections,
} from "@/lib/readme";

// The page is static: the README is read once, when the site is built.
const README = readFileSync(join(process.cwd(), "..", "README.md"), "utf8");
const SECTIONS = readmeSections(README);

// Its own title and description; the link preview stays the home page's.
export const metadata: Metadata = { title: ABOUT_TITLE, description: readmeDescription(README) };

const LINK = "text-accent underline hover:text-accent-strong";
const README_ON_GITHUB = "https://github.com/nazrulhuda/filingcheck/blob/main/README.md";

function Inline({ nodes }: { nodes: InlineNode[] }) {
  return (
    <>
      {nodes.map((node, i) =>
        node.kind === "text" ? (
          <Fragment key={i}>{node.text}</Fragment>
        ) : node.kind === "bold" ? (
          <strong key={i} className="font-semibold text-slate-900">
            <Inline nodes={node.children} />
          </strong>
        ) : node.kind === "italic" ? (
          <em key={i}>
            <Inline nodes={node.children} />
          </em>
        ) : node.kind === "code" ? (
          // Long identifiers break anywhere, so the page fits a phone's width.
          <code
            key={i}
            className="rounded bg-slate-100 px-1 py-0.5 font-mono text-[0.88em] text-slate-800 [overflow-wrap:anywhere]"
          >
            {node.text}
          </code>
        ) : (
          <a key={i} href={node.href} className={LINK}>
            <Inline nodes={node.children} />
          </a>
        ),
      )}
    </>
  );
}

const text = (value: string) => <Inline nodes={inline(value)} />;

/** The diagram's description, from its own boxes: the labels in docs/architecture.mmd. */
function diagramAlt(source: string): string {
  const labels = [...source.matchAll(/\["([^"]+)"\]/g)].map((m) => m[1].replaceAll("<br/>", ", "));
  return `Diagram: ${labels.join("; ")}.`;
}

function BlockView({ block }: { block: Block }) {
  switch (block.kind) {
    case "paragraph":
      return <p className="mt-3 leading-7 text-slate-700">{text(block.text)}</p>;
    case "list": {
      const List = block.ordered ? "ol" : "ul";
      return (
        <List
          className={`mt-3 space-y-2 pl-6 leading-7 text-slate-700 ${block.ordered ? "list-decimal" : "list-disc"}`}
        >
          {block.items.map((item, i) => (
            <li key={i}>{text(item)}</li>
          ))}
        </List>
      );
    }
    case "table":
      return (
        <div className="mt-4 overflow-x-auto rounded-lg border border-slate-200 bg-white">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-50">
              <tr>
                {block.header.map((cell, i) => (
                  <th
                    key={i}
                    className={`border-b border-slate-200 px-3 py-2 font-semibold text-slate-800 ${block.align[i] === "right" ? "text-right" : "text-left"}`}
                  >
                    {text(cell)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {block.rows.map((row, r) => (
                <tr key={r} className="border-b border-slate-100 last:border-0">
                  {row.map((cell, i) => (
                    <td
                      key={i}
                      className={`px-3 py-2 align-top text-slate-700 ${block.align[i] === "right" ? "text-right tabular-nums" : "text-left"}`}
                    >
                      {text(cell)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    case "code":
      if (block.lang === "mermaid") {
        // On phones the diagram keeps a readable width and scrolls sideways; it opens full size.
        return (
          <div className="mt-4 overflow-x-auto rounded-lg border border-slate-200 bg-white p-2">
            <a href={imageSrc("docs/architecture.svg")}>
              {/* eslint-disable-next-line @next/next/no-img-element -- a static SVG drawn from the .mmd */}
              <img
                src={imageSrc("docs/architecture.svg")}
                alt={diagramAlt(block.text)}
                className="w-full min-w-[900px] sm:min-w-0"
              />
            </a>
          </div>
        );
      }
      return (
        <pre className="mt-3 overflow-x-auto rounded-lg bg-slate-100 p-3 text-[13px] leading-6 text-slate-800">
          <code>{block.text}</code>
        </pre>
      );
    case "image":
      // A chart opens full size, as the diagram does.
      return (
        <div className="mt-4">
          <a href={imageSrc(block.src)}>
            {/* eslint-disable-next-line @next/next/no-img-element -- the README's own chart, served as a file */}
            <img
              src={imageSrc(block.src)}
              alt={block.alt}
              className="block w-full rounded-lg border border-slate-200 bg-white"
            />
          </a>
        </div>
      );
  }
}

export default function About() {
  return (
    <>
      <TopBar />
      <main id="top" className="mx-auto max-w-4xl px-4 pb-8 pt-6 sm:pt-8">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-[32px] sm:leading-tight">
          {ABOUT_TITLE}
        </h1>
        <p className="mt-2 text-slate-600">
          {"This page shows the project's "}
          <a href={README_ON_GITHUB} className={LINK}>
            README
          </a>
          , as it is on GitHub.
        </p>
        <nav aria-label="On this page" className="mt-5 rounded-lg border border-slate-200 bg-white p-4 text-sm">
          <p className="font-semibold text-slate-800">On this page</p>
          <ol className="mt-2 grid gap-x-6 gap-y-1 sm:grid-cols-2 lg:grid-cols-3">
            {SECTIONS.map((section) => (
              <li key={section.id}>
                <a href={`#${section.id}`} className={LINK}>
                  {section.title}
                </a>
              </li>
            ))}
          </ol>
        </nav>
        {SECTIONS.map((section) => (
          <section key={section.id} id={section.id} className="mt-12 scroll-mt-4">
            <h2 className="text-xl font-semibold text-slate-900 sm:text-2xl">{section.title}</h2>
            {section.blocks.map((block, i) => (
              <BlockView key={i} block={block} />
            ))}
          </section>
        ))}
        <Footer />
      </main>
    </>
  );
}
