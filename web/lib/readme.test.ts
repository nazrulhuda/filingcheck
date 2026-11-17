// The About page renders the README's own sections: one source, nothing new. These tests read the
// README itself, so a README change shows on the page at the next build.
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

import {
  ABOUT_ASSETS,
  ABOUT_SECTIONS,
  ABOUT_TITLE,
  type Block,
  type InlineNode,
  href,
  imageSrc,
  inline,
  readmeDescription,
  readmeSections,
} from "./readme.ts";

const repo = (path: string) => new URL(`../../${path}`, import.meta.url);
const read = (path: string) => readFileSync(repo(path), "utf8");
const README = read("README.md");
const sections = readmeSections(README);
const blocks = (title: string): Block[] => {
  const section = sections.find((s) => s.title === title);
  assert.ok(section, title);
  return section.blocks;
};

test("the About page holds the README's sections, in its order", () => {
  assert.deepEqual(ABOUT_SECTIONS, [
    "What this project shows",
    "By the numbers",
    "The result",
    "How it is built",
    "How one question goes through it",
    "What the measurement showed",
    "Results",
    "Known limits",
    "What works today",
    "Not built",
    "Reproduce the results",
    "Related work",
  ]);
  assert.deepEqual(
    sections.map((s) => s.title),
    ABOUT_SECTIONS,
  );
  assert.equal(sections.find((s) => s.title === "Results")?.id, "results");
});

test("it leaves out the title block, its badges and How to run", () => {
  const all = JSON.stringify(sections);
  for (const left of ["How to run", "Live demo:", "badge.svg", "<!--", "Built with Python", "make ingest"]) {
    assert.ok(!all.includes(left), left);
  }
});

test("every paragraph, list item, table cell and code block is the README's own text", () => {
  for (const block of sections.flatMap((s) => s.blocks)) {
    const texts =
      block.kind === "paragraph"
        ? [block.text]
        : block.kind === "list"
          ? block.items
          : block.kind === "table"
            ? [...block.header, ...block.rows.flat()]
            : block.kind === "code"
              ? [block.text]
              : [block.alt, block.src];
    for (const text of texts) assert.ok(README.includes(text), text.slice(0, 80));
  }
});

test("the Results section's first claim is the README's first: the prompt-rules result", () => {
  const claims = blocks("Results").filter(
    (b): b is Extract<Block, { kind: "paragraph" }> => b.kind === "paragraph" && b.text.startsWith("**"),
  );
  assert.ok(
    claims[0].text.startsWith(
      "**The same rules written into the prompt did better than the server-side checks on accuracy.**",
    ),
  );
  const afterHeading = README.slice(README.indexOf("## Results")).split("\n");
  assert.equal(
    afterHeading.find((line) => line.startsWith("**")),
    claims[0].text,
  );
});

test("the diagram is drawn from docs/architecture.mmd, and the drawing is of its current source", () => {
  const code = blocks("How it is built").find((b) => b.kind === "code");
  assert.ok(code && code.kind === "code");
  assert.equal(code.lang, "mermaid");
  assert.equal(code.text.trim(), read("docs/architecture.mmd").trim());
  const digest = createHash("sha256").update(readFileSync(repo("docs/architecture.mmd"))).digest("hex");
  assert.ok(read("docs/architecture.svg").startsWith(`<!-- Drawn from docs/architecture.mmd (SHA-256 ${digest})`));
  assert.equal(ABOUT_ASSETS["docs/architecture.svg"], "architecture.svg");
});

test("the README's pictures in these sections are served by the site", () => {
  const images = sections
    .flatMap((s) => s.blocks)
    .filter((b): b is Extract<Block, { kind: "image" }> => b.kind === "image");
  assert.deepEqual(
    images.map((i) => i.src),
    ["docs/results/final_summary.png", "docs/results/final_rates.png"],
  );
  for (const image of images) {
    assert.ok(ABOUT_ASSETS[image.src], image.src);
    assert.equal(imageSrc(image.src), `/about/${ABOUT_ASSETS[image.src]}`);
  }
  for (const path of Object.keys(ABOUT_ASSETS)) assert.ok(existsSync(repo(path)), path);
});

test("relative links go to the files on GitHub; web links and anchors stay", () => {
  assert.equal(href("eval/README.md"), "https://github.com/nazrulhuda/filingcheck/blob/main/eval/README.md");
  assert.equal(href("filingcheck/app/"), "https://github.com/nazrulhuda/filingcheck/tree/main/filingcheck/app/");
  assert.equal(href("https://arxiv.org/abs/2608.10213"), "https://arxiv.org/abs/2608.10213");
  assert.equal(href("#known-limits"), "#known-limits");
});

test("inline text: bold, code and links, nested", () => {
  assert.deepEqual(inline("**A [b](x.md)** and `c`."), [
    {
      kind: "bold",
      children: [
        { kind: "text", text: "A " },
        {
          kind: "link",
          href: "https://github.com/nazrulhuda/filingcheck/blob/main/x.md",
          children: [{ kind: "text", text: "b" }],
        },
      ],
    },
    { kind: "text", text: " and " },
    { kind: "code", text: "c" },
    { kind: "text", text: "." },
  ]);
  assert.deepEqual(inline("no marks"), [{ kind: "text", text: "no marks" }]);
});

test("tables keep their header, alignment and cells", () => {
  const table = blocks("By the numbers").find((b) => b.kind === "table");
  assert.ok(table && table.kind === "table");
  assert.deepEqual(table.header, ["Part", "What it is"]);
  assert.equal(table.rows.length, 10);
  const results = blocks("Results").find((b) => b.kind === "table");
  assert.ok(results && results.kind === "table");
  assert.deepEqual(results.align.slice(0, 2), ["left", "right"]);
});

test("the About page has its own title, and its description is the README's one line", () => {
  assert.equal(ABOUT_TITLE, "About FilingCheck: the results and how it was built");
  assert.equal(readmeDescription(README), README.split("\n")[2]);
  assert.ok(readmeDescription(README).startsWith("An agent that answers questions"));
});

test("single-asterisk emphasis is italic", () => {
  assert.deepEqual(inline("server-side *repair* of arguments"), [
    { kind: "text", text: "server-side " },
    { kind: "italic", children: [{ kind: "text", text: "repair" }] },
    { kind: "text", text: " of arguments" },
  ]);
});

/** Every piece of text the About page renders from the README's inline markdown. */
function renderedTexts(nodes: InlineNode[]): string[] {
  return nodes.flatMap((node) =>
    node.kind === "text" || node.kind === "code" ? [node.text] : renderedTexts(node.children),
  );
}

test("no rendered text on the About page still holds a markdown marker", () => {
  const sources = sections.flatMap((s) =>
    s.blocks.flatMap((b) =>
      b.kind === "paragraph"
        ? [b.text]
        : b.kind === "list"
          ? b.items
          : b.kind === "table"
            ? [...b.header, ...b.rows.flat()]
            : [],
    ),
  );
  const marker = /\*\*|`|\]\(|(^|[\s(])\*[^\s*]|[^\s*]\*($|[\s.,;:)])|(^|\s)#{1,6}\s|<!--/;
  for (const source of sources) {
    for (const piece of renderedTexts(inline(source))) {
      assert.doesNotMatch(piece, marker, source.slice(0, 80));
    }
  }
});

test("the About page says it shows the README, and its charts open full size", () => {
  const page = read("web/app/about/page.tsx");
  assert.ok(page.includes("This page shows the project's"));
  assert.ok(page.includes("https://github.com/nazrulhuda/filingcheck/blob/main/README.md"));
  assert.ok(page.includes("<a href={imageSrc(block.src)}>"), "each chart links to its picture");
  assert.ok(page.includes('<a href={imageSrc("docs/architecture.svg")}>'), "and so does the diagram");
});
