// Small line icons for the "How it works" steps and the "What's inside" tiles: plain SVG drawn
// here, in the accent colour, hidden from screen readers (the text beside each one says it all).

import type { ReactNode } from "react";

const PATHS: Record<string, ReactNode> = {
  ask: <path d="M4 5h16v10H10l-4 4v-4H4z" />,
  check: (
    <>
      <path d="M12 3l7 3v5c0 4.4-2.9 7.9-7 10-4.1-2.1-7-5.6-7-10V6z" />
      <path d="M9 12l2.2 2.2L15.5 10" />
    </>
  ),
  label: (
    <>
      <path d="M4 4h7.5L20 12.5 12.5 20 4 11.5z" />
      <circle cx="8.5" cy="8.5" r="1.4" />
    </>
  ),
  data: (
    <>
      <path d="M6 3h8.5L19 7.5V21H6z" />
      <path d="M14 3v5h5M9 12.5h7M9 16.5h7" />
    </>
  ),
  search: (
    <>
      <circle cx="10.5" cy="10.5" r="6" />
      <path d="M15 15l5 5" />
    </>
  ),
  numbers: <path d="M4 20h16M7.5 17v-5M12 17V7M16.5 17v-8" />,
  agent: (
    <>
      <circle cx="6" cy="12" r="2.2" />
      <circle cx="18" cy="6" r="2.2" />
      <circle cx="18" cy="18" r="2.2" />
      <path d="M8 11l8-4M8 13l8 4" />
    </>
  ),
  testing: <path d="M10 6h10M10 12h10M10 18h10M3.5 6l1.3 1.3L7.5 4.6M3.5 12l1.3 1.3 2.7-2.7M3.5 18l1.3 1.3 2.7-2.7" />,
};

export type IconName = keyof typeof PATHS;

export function Icon({ name }: { name: IconName }) {
  return (
    <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-accent-soft text-accent">
      <svg
        width="18"
        height="18"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
        focusable="false"
      >
        {PATHS[name]}
      </svg>
    </span>
  );
}

/** The icon for each "How it works" step and each "What's inside" tile, in their order. */
export const STEP_ICONS: IconName[] = ["ask", "check", "label"];
export const INSIDE_ICONS: Record<string, IconName> = {
  Data: "data",
  Search: "search",
  Numbers: "numbers",
  Agent: "agent",
  Checks: "check",
  Testing: "testing",
};
