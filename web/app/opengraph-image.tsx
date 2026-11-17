// The link preview (1200 by 630): the logo, the page's one sentence and the demo address,
// drawn at build time with no outside images.
import { ImageResponse } from "next/og";

import { MARK_CHECK } from "@/components/Logo";
import { SENTENCE } from "@/lib/glance";

export const alt = `FilingCheck. ${SENTENCE}`;
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

const ACCENT = "#1e40af";
const DEMO = "filingcheck.vercel.app";

export default function OpenGraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: "80px 88px",
          background: "#ffffff",
          borderTop: `16px solid ${ACCENT}`,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 28 }}>
          <svg width="96" height="96" viewBox="0 0 32 32">
            <rect width="32" height="32" rx="7" fill={ACCENT} />
            <path
              d={MARK_CHECK}
              fill="none"
              stroke="#ffffff"
              strokeWidth="3.6"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <div style={{ display: "flex", fontSize: 88, fontWeight: 700, color: "#0f172a" }}>
            Filing<span style={{ color: ACCENT }}>Check</span>
          </div>
        </div>
        <div style={{ display: "flex", fontSize: 42, lineHeight: 1.35, color: "#334155" }}>
          {SENTENCE}
        </div>
        <div style={{ display: "flex", fontSize: 38, color: ACCENT }}>{DEMO}</div>
      </div>
    ),
    size,
  );
}
