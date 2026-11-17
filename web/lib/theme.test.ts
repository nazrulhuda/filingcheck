// The page's colours (web/app/globals.css): one accent, and three label colours that pass the
// WCAG contrast checks. Each label also keeps its own symbol, so colour is never the only cue.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const css = readFileSync(new URL("../app/globals.css", import.meta.url), "utf8");
const colour = (name: string): string => {
  const match = new RegExp(`--color-${name}:\\s*(#[0-9a-f]{6});`, "i").exec(css);
  assert.ok(match, `--color-${name} in globals.css`);
  return match[1];
};

/** WCAG 2 relative luminance and contrast ratio. */
function luminance(hex: string): number {
  const [r, g, b] = [1, 3, 5].map((i) => {
    const c = parseInt(hex.slice(i, i + 2), 16) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}
function contrast(a: string, b: string): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

const WHITE = "#ffffff";

test("the contrast formula gives the known ratios", () => {
  assert.equal(contrast("#000000", WHITE).toFixed(1), "21.0");
  assert.equal(contrast("#767676", WHITE).toFixed(1), "4.5");
});

test("the accent passes as link text on white and as white button text", () => {
  for (const name of ["accent", "accent-strong"]) {
    assert.ok(contrast(colour(name), WHITE) >= 4.5, name);
  }
  assert.ok(contrast(colour("accent-strong"), colour("accent-soft")) >= 4.5, "chip text");
});

test("each label's symbol passes on its badge, and its border stands out from white", () => {
  for (const label of ["verified", "conflict", "unverified"]) {
    assert.ok(contrast(colour(label), colour(`${label}-bg`)) >= 4.5, `${label} text`);
    assert.ok(contrast(colour(`${label}-line`), WHITE) >= 3, `${label} border`);
  }
});

test("the three labels are green, red and amber, and each differs from the accent", () => {
  const hue = (hex: string) => {
    const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    if (max === min) return 0;
    const h = max === r ? (g - b) / (max - min) : max === g ? 2 + (b - r) / (max - min) : 4 + (r - g) / (max - min);
    return (h * 60 + 360) % 360;
  };
  const verified = hue(colour("verified"));
  const conflict = hue(colour("conflict"));
  const unverified = hue(colour("unverified"));
  assert.ok(verified > 90 && verified < 160, `verified is green (${verified})`);
  assert.ok(conflict < 15 || conflict > 345, `conflict is red (${conflict})`);
  assert.ok(unverified > 20 && unverified < 50, `unverified is amber (${unverified})`);
  const accent = hue(colour("accent"));
  assert.ok(accent > 200 && accent < 250, `the accent is blue (${accent})`);
});
