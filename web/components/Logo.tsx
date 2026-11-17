// The text logo: a small check mark in the accent, then the name. The mark is plain SVG drawn
// here; app/icon.svg (the favicon) and app/opengraph-image.tsx draw the same mark.

/** The mark's path in a 32 by 32 box: a rounded square with a check in it. */
export const MARK_CHECK = "M9 16.5l4.6 4.6L23.2 11.4";

export function LogoMark({ size = 28 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      aria-hidden="true"
      focusable="false"
      className="shrink-0 text-accent"
    >
      <rect width="32" height="32" rx="7" fill="currentColor" />
      <path
        d={MARK_CHECK}
        fill="none"
        stroke="#ffffff"
        strokeWidth="3.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/** The page title: the mark and "FilingCheck", read as one word. */
export function Logo() {
  return (
    <h1 className="flex items-center gap-2.5 text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
      <LogoMark />
      <span>
        Filing<span className="text-accent">Check</span>
      </span>
    </h1>
  );
}
