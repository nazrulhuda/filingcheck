// The About page shows the README's own sections, read from README.md at build time: one source,
// nothing new to drift. This module splits the README into those sections and their blocks, in
// the README's words; the page only renders them.

const REPO = "https://github.com/nazrulhuda/filingcheck";

export const ABOUT_TITLE = "About FilingCheck: the results and how it was built";

/** The README's sections the About page shows, in the README's order. */
export const ABOUT_SECTIONS = [
  "What this project shows",
  "By the numbers",
  "Results",
  "How it is built",
  "How one question goes through it",
  "Known limits",
  "Not built",
  "Reproduce the results",
  "Related work",
];

/** The sections the README starts with a bold lead instead of a heading: the two above Results. */
const BOLD_LEADS = ["What this project shows", "By the numbers"];

/** The README's chart in these sections, and the drawn diagram, by their file in public/about/
 * (copied there before each build by scripts/about-assets.mjs). */
export const ABOUT_ASSETS: Record<string, string> = {
  "docs/results/final_summary.png": "final_summary.png",
  "docs/architecture.svg": "architecture.svg",
};

export type InlineNode =
  | { kind: "text"; text: string }
  | { kind: "bold"; children: InlineNode[] }
  | { kind: "italic"; children: InlineNode[] }
  | { kind: "code"; text: string }
  | { kind: "link"; href: string; children: InlineNode[] };

export type Block =
  | { kind: "paragraph"; text: string }
  | { kind: "list"; ordered: boolean; items: string[] }
  | { kind: "table"; header: string[]; align: ("left" | "right")[]; rows: string[][] }
  | { kind: "code"; lang: string; text: string }
  | { kind: "image"; alt: string; src: string };

export type Section = { id: string; title: string; blocks: Block[] };

/** A section's anchor: "Known limits" is "known-limits". */
export function slug(title: string): string {
  return title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

/** Where a README link goes from the site: a relative link becomes the file on GitHub. */
export function href(url: string): string {
  if (/^(https?:|mailto:|#)/.test(url)) return url;
  const path = url.replace(/^\.\//, "");
  return `${REPO}/${path.endsWith("/") ? "tree" : "blob"}/main/${path}`;
}

/** Where a README picture is served from: the site's copy, else the file on GitHub. */
export function imageSrc(src: string): string {
  const file = ABOUT_ASSETS[src];
  return file ? `/about/${file}` : href(src);
}

/** The README's one-line description: the first line after its title. */
export function readmeDescription(markdown: string): string {
  const lines = markdown.replace(/\r\n/g, "\n").split("\n");
  return lines.find((line, i) => i > 0 && line.trim() !== "") ?? "";
}

/** Bold, italic, inline code and links, nested as the README writes them; the rest is text. */
export function inline(text: string): InlineNode[] {
  const out: InlineNode[] = [];
  const push = (piece: string) => {
    if (!piece) return;
    const last = out.at(-1);
    if (last?.kind === "text") last.text += piece;
    else out.push({ kind: "text", text: piece });
  };
  let rest = text;
  while (rest) {
    const mark = /\*\*|\*|`|\[/.exec(rest);
    if (!mark) {
      push(rest);
      break;
    }
    push(rest.slice(0, mark.index));
    rest = rest.slice(mark.index);
    if (mark[0] === "`") {
      const end = rest.indexOf("`", 1);
      if (end === -1) {
        push(rest);
        break;
      }
      out.push({ kind: "code", text: rest.slice(1, end) });
      rest = rest.slice(end + 1);
    } else if (mark[0] === "**") {
      const end = rest.indexOf("**", 2);
      if (end === -1) {
        push(rest);
        break;
      }
      out.push({ kind: "bold", children: inline(rest.slice(2, end)) });
      rest = rest.slice(end + 2);
    } else if (mark[0] === "*") {
      // *word* is italic; an asterisk with no closing pair stays as it is.
      const italic = /^\*(\S(?:[^*]*?\S)?)\*(?!\*)/.exec(rest);
      if (italic) {
        out.push({ kind: "italic", children: inline(italic[1]) });
        rest = rest.slice(italic[0].length);
      } else {
        push("*");
        rest = rest.slice(1);
      }
    } else {
      const link = /^\[([^\]]*)\]\(([^)\s]+)\)/.exec(rest);
      if (link) {
        out.push({ kind: "link", href: href(link[2]), children: inline(link[1]) });
        rest = rest.slice(link[0].length);
      } else {
        push("[");
        rest = rest.slice(1);
      }
    }
  }
  return out;
}

const BULLET = /^- (.*)$/;
const NUMBERED = /^\d+\. (.*)$/;
const STARTS_BLOCK = /^(```|\||- |\d+\. |!\[)/;

function cells(row: string): string[] {
  return row
    .trim()
    .replace(/^\||\|$/g, "")
    .split("|")
    .map((cell) => cell.trim());
}

function blocksOf(lines: string[]): Block[] {
  const blocks: Block[] = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (!line.trim() || /^<!--.*-->$/.test(line.trim())) {
      i += 1;
      continue;
    }
    const fence = /^```(\w*)\s*$/.exec(line);
    if (fence) {
      const body: string[] = [];
      i += 1;
      while (i < lines.length && !/^```\s*$/.test(lines[i])) body.push(lines[i++]);
      i += 1;
      blocks.push({ kind: "code", lang: fence[1], text: body.join("\n") });
      continue;
    }
    if (line.startsWith("|")) {
      const rows: string[] = [];
      while (i < lines.length && lines[i].startsWith("|")) rows.push(lines[i++]);
      const [head, separator, ...body] = rows;
      blocks.push({
        kind: "table",
        header: cells(head),
        align: cells(separator).map((cell) => (cell.endsWith(":") ? "right" : "left")),
        rows: body.map(cells),
      });
      continue;
    }
    const image = /^!\[([^\]]*)\]\(([^)]+)\)\s*$/.exec(line);
    if (image) {
      blocks.push({ kind: "image", alt: image[1], src: image[2] });
      i += 1;
      continue;
    }
    if (BULLET.test(line) || NUMBERED.test(line)) {
      const ordered = NUMBERED.test(line);
      const pattern = ordered ? NUMBERED : BULLET;
      const items: string[] = [];
      while (i < lines.length && pattern.test(lines[i])) items.push(pattern.exec(lines[i++])![1]);
      blocks.push({ kind: "list", ordered, items });
      continue;
    }
    const paragraph: string[] = [];
    while (i < lines.length && lines[i].trim() && !STARTS_BLOCK.test(lines[i])) {
      paragraph.push(lines[i++]);
    }
    blocks.push({ kind: "paragraph", text: paragraph.join(" ") });
  }
  return blocks;
}

/** The README's sections the About page shows, each with its blocks, in the README's order. A
 * section starts at its "## " heading or, for the first two, at its bold lead; the title block
 * before them and the sections not listed are left out. */
export function readmeSections(markdown: string): Section[] {
  const found: { title: string; lines: string[] }[] = [];
  let current: { title: string; lines: string[] } | null = null;
  for (const line of markdown.replace(/\r\n/g, "\n").split("\n")) {
    const heading = /^## (.+)$/.exec(line);
    const lead = BOLD_LEADS.find((title) => line.startsWith(`**${title}**`));
    if (heading || lead) {
      current = { title: heading ? heading[1].trim() : lead!, lines: [] };
      found.push(current);
      if (lead) {
        // The rest of the lead's line, in the README's words, opens the section.
        const rest = line.slice(`**${lead}**`.length).replace(/^[\s,:]+/, "");
        if (rest) current.lines.push(rest);
      }
      continue;
    }
    if (current) current.lines.push(line);
  }
  return found
    .filter((section) => ABOUT_SECTIONS.includes(section.title))
    .map((section) => ({
      id: slug(section.title),
      title: section.title,
      blocks: blocksOf(section.lines),
    }));
}
