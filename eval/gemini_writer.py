"""Ask Google Gemini, outside the coding session, to write the second held-out file (Day 37).

The model receives only the committed prompt's bytes as one user message: no system
instruction, no tools, no search grounding, the provider's default temperature, and an output
limit large enough for 84 lines. The model is chosen by a rule before the call: list the models
the key can use and take the newest Gemini Pro (versioned names only: no "-latest" alias, no
text-to-speech, image or custom-tools variant); if there is none, the newest Flash that is not
Flash-Lite. One request; it is retried only if it fails with no reply. A short or cut-off reply
is kept as it is. The key (GEMINI_API_KEY in .env) goes in a request header and is never printed
or written.

"Can use" means the model answers a request. On 2026-11-13 the newest Pro
(gemini-3.1-pro-preview) returned the free tier's quota error (HTTP 429) on the request and both
retries, and gemini-2.5-pro returned 404, so the key has no usable Pro; that record is
`<date>_heldout2_gemini_request_pro-attempts.json`. The rule then picks the newest Flash:
`--model models/gemini-3.8-flash` names it, and the script checks that it is the newest listed
Flash that is not Flash-Lite.

Run: `uv run python eval/gemini_writer.py [--model models/...]`. Writes, in
`eval/questions/heldout_source/`:
`<date>_heldout2_gemini_output.md` (the reply's text, unedited),
`<date>_heldout2_gemini_request.json` (the request as sent, without the key) and
`<date>_heldout2_gemini_response.json` (the model version, token counts, finish reason and the
models listed).
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from dotenv import load_dotenv  # noqa: E402

API = "https://generativelanguage.googleapis.com/v1beta"
PROMPT = REPO / "eval" / "questions" / "heldout_source" / "2026-11-13_heldout2_agent_prompt.md"
PROMPT_SHA256 = "a729b9e573a05cb74da7bd8c0a0244e48839d338437157742be4bdece8e44b62"
OUT = REPO / "eval" / "questions" / "heldout_source"
PRO_RE = re.compile(r"^models/gemini-(\d+(?:\.\d+)?)-pro(?:-preview)?$")
FLASH_RE = re.compile(r"^models/gemini-(\d+(?:\.\d+)?)-flash(?:-preview)?$")
TRIES = 3


def call(url: str, key: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    """One request to the Gemini API, the key in a header."""
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"x-goog-api-key": key, "Content-Type": "application/json"}
    with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=headers)) as r:
        result: dict[str, Any] = json.load(r)
        return result


def listed_models(key: str) -> list[dict[str, Any]]:
    """Every model the key can use for generateContent."""
    models: list[dict[str, Any]] = []
    token = ""
    while True:
        page = call(f"{API}/models?pageSize=1000" + (f"&pageToken={token}" if token else ""), key)
        models += [
            m
            for m in page.get("models", [])
            if "generateContent" in m.get("supportedGenerationMethods", [])
        ]
        token = page.get("nextPageToken", "")
        if not token:
            return models


def choose(models: list[dict[str, Any]]) -> dict[str, Any]:
    """The newest Gemini Pro by version; else the newest Flash that is not Flash-Lite.

    At one version a stable name wins over a preview.
    """
    for pattern in (PRO_RE, FLASH_RE):
        found = [(m, pattern.match(m["name"])) for m in models]
        ranked = [
            (float(match.group(1)), "preview" not in m["name"], m) for m, match in found if match
        ]
        if ranked:
            return max(ranked, key=lambda t: (t[0], t[1]))[2]
    raise SystemExit("no Gemini Pro or Flash model is listed for this key")


def main() -> int:
    """List, choose, ask once, and write the reply and the record."""
    parser = argparse.ArgumentParser(prog="eval/gemini_writer.py")
    parser.add_argument("--model", help="the newest Flash, after no Pro answered (see above)")
    args = parser.parse_args()
    load_dotenv(REPO / ".env")
    key = os.environ["GEMINI_API_KEY"]
    prompt_bytes = PROMPT.read_bytes()
    if hashlib.sha256(prompt_bytes).hexdigest() != PROMPT_SHA256:
        raise SystemExit("the prompt file does not match its committed SHA-256")
    models = listed_models(key)
    names = [m["name"] for m in models]
    print("models the key can use for generateContent:")
    for name in names:
        print(" ", name)
    model = choose(models)
    if args.model:
        flash = choose([m for m in models if not PRO_RE.match(m["name"])])
        if flash["name"] != args.model:
            raise SystemExit(f"{args.model} is not the newest listed Flash ({flash['name']})")
        model = flash
    print("chosen:", model["name"], "| output limit", model.get("outputTokenLimit"))
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt_bytes.decode("utf-8")}]}],
        "generationConfig": {"maxOutputTokens": int(model.get("outputTokenLimit") or 65536)},
    }
    today = datetime.now(UTC).date().isoformat()
    url = f"{API}/{model['name']}:generateContent"
    attempts: list[dict[str, Any]] = []
    response: dict[str, Any] | None = None
    for attempt in range(1, TRIES + 1):
        started = datetime.now(UTC).isoformat()
        try:
            response = call(url, key, body)
            attempts.append({"attempt": attempt, "at": started, "result": "reply"})
            break
        except urllib.error.HTTPError as exc:  # no reply: the only case that is retried
            attempts.append({"attempt": attempt, "at": started, "result": f"HTTP {exc.code}"})
        except urllib.error.URLError as exc:
            attempts.append({"attempt": attempt, "at": started, "result": type(exc).__name__})
        time.sleep(20 * attempt)
    record = {
        "date": today,
        "endpoint": url,
        "model": model["name"],
        "model_listed_version": model.get("version"),
        "prompt_file": str(PROMPT.relative_to(REPO)).replace("\\", "/"),
        "prompt_sha256": PROMPT_SHA256,
        "request_body": {
            **body,
            "contents": "<the prompt file's text, unchanged>",
        },
        "settings": "no system instruction, no tools, no search grounding, default temperature",
        "attempts": attempts,
    }
    (OUT / f"{today}_heldout2_gemini_request.json").write_text(
        json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    if response is None:
        print("no reply after", TRIES, "tries:", attempts)
        return 1
    candidate = (response.get("candidates") or [{}])[0]
    parts = (candidate.get("content") or {}).get("parts") or []
    text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
    output = OUT / f"{today}_heldout2_gemini_output.md"
    output.write_bytes(text.encode("utf-8"))
    meta = {
        "model_version": response.get("modelVersion"),
        "response_id": response.get("responseId"),
        "finish_reason": candidate.get("finishReason"),
        "usage": response.get("usageMetadata"),
        "parts": len(parts),
        "thought_parts_left_out": sum(1 for p in parts if p.get("thought")),
        "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "models_listed": names,
        "chosen_by_rule": model["name"],
    }
    (OUT / f"{today}_heldout2_gemini_response.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    lines = [ln for ln in text.splitlines() if re.match(r"^\s*[1-7]\s*\|", ln)]
    print(
        f"reply: {len(text)} characters, {len(lines)} question lines, "
        f"finish {meta['finish_reason']}, model version {meta['model_version']}"
    )
    print("output SHA-256:", meta["output_sha256"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
