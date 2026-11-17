// Before each build (and `npm run dev`): copy the README's pictures and the drawn diagram that the
// About page shows into public/about/, so the site serves them. The list is ABOUT_ASSETS.
import { copyFileSync, mkdirSync } from "node:fs";

import { ABOUT_ASSETS } from "../lib/readme.ts";

const repo = new URL("../../", import.meta.url);
const target = new URL("../public/about/", import.meta.url);
mkdirSync(target, { recursive: true });
for (const [path, file] of Object.entries(ABOUT_ASSETS)) {
  copyFileSync(new URL(path, repo), new URL(file, target));
}
console.log(`about-assets: ${Object.keys(ABOUT_ASSETS).length} files in public/about/`);
