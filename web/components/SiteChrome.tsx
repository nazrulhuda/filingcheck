// The top bar and the footer, the same on the home page and the About page.
import Link from "next/link";

import { Logo } from "@/components/Logo";
import resultsData from "@/data/results.json";
import { JUMP_LINKS, STACK } from "@/lib/glance";
import type { Results } from "@/lib/results";

const RESULTS = resultsData as Results;
const REPO = "https://github.com/nazrulhuda/filingcheck";
const REPORT = `${REPO}/blob/main/${RESULTS.report}`;
const PREREGISTRATION = `${REPO}/blob/main/eval/PREREGISTRATION.md`;
const KNOWN_LIMITS = `${REPO}#known-limits`;
const LINK = "text-accent underline hover:text-accent-strong";

/** The logo at the left, the links at the right; on phones the links scroll sideways. */
export function TopBar() {
  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-4 py-2">
        <Logo />
        <nav
          aria-label="Sections"
          className="flex min-w-0 gap-4 overflow-x-auto whitespace-nowrap text-[13px] font-medium sm:gap-6 sm:text-[15px]"
        >
          {JUMP_LINKS.map((link) =>
            link.href.startsWith("http") ? (
              <a key={link.href} href={link.href} className="py-2 text-slate-700 hover:text-accent">
                {link.label}
              </a>
            ) : (
              <Link key={link.href} href={link.href} className="py-2 text-slate-700 hover:text-accent">
                {link.label}
              </Link>
            ),
          )}
        </nav>
      </div>
    </header>
  );
}

/** Who built it, the project's links and the stack. */
export function Footer() {
  return (
    <footer className="mt-12 space-y-2 border-t border-slate-200 pt-5 text-sm text-slate-600">
      <p>
        Built by Nazrul Huda Shanto
        {" · "}
        <a href="https://github.com/nazrulhuda" className={LINK}>
          GitHub
        </a>
        {" · "}
        <a href="https://www.linkedin.com/in/mshanto/" className={LINK}>
          LinkedIn
        </a>
      </p>
      <p>
        <a href={REPO} className={LINK}>
          Code
        </a>
        {" · "}
        <a href={REPORT} className={LINK}>
          Full report
        </a>
        {" · "}
        <a href={PREREGISTRATION} className={LINK}>
          Pre-registration
        </a>
        {" · "}
        <a href={KNOWN_LIMITS} className={LINK}>
          Known limits
        </a>
      </p>
      <p className="text-xs text-slate-500">{STACK}</p>
    </footer>
  );
}
