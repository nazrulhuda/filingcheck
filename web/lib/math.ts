// The model sometimes writes its working as LaTeX ("\((a - b) / b \times 100 = 114.20\%\)").
// The answer view shows it cleanly; the stored text, the labels and the checks do not change.

const REPLACEMENTS: Record<string, string> = {
  "\\(": "",
  "\\)": "",
  "\\times": "×",
  "\\%": "%",
  "\\,": " ", // a thin space
};

const PATTERN = /\\\(|\\\)|\\times|\\%|\\,/g;

/** The text with the working's LaTeX delimiters removed and its few symbols written out. */
export function mathText(text: string): string {
  return text.replace(PATTERN, (match) => REPLACEMENTS[match] ?? match);
}
