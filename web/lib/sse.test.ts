import assert from "node:assert/strict";
import { test } from "node:test";

import { createSseParser } from "./sse.ts";

test("events split across chunks are put back together", () => {
  const parser = createSseParser();
  assert.deepEqual(parser.push('event: token\ndata: {"text": "Pe'), []);
  assert.deepEqual(parser.push('so"}\n\nevent: token\ndata: {"text": " risk"}\n\n'), [
    { event: "token", data: '{"text": "Peso"}' },
    { event: "token", data: '{"text": " risk"}' },
  ]);
});

test("carriage returns and a missing event name are handled", () => {
  const parser = createSseParser();
  assert.deepEqual(parser.push('data: {"a": 1}\r\n\r\nevent: final\r\ndata: {}\r\n\r\n'), [
    { event: "message", data: '{"a": 1}' },
    { event: "final", data: "{}" },
  ]);
});

test("an unfinished event is kept until its blank line arrives", () => {
  const parser = createSseParser();
  assert.deepEqual(parser.push("event: final\ndata: {}\n"), []);
  assert.deepEqual(parser.push("\n"), [{ event: "final", data: "{}" }]);
});
