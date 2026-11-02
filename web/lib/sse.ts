// A server-sent-events reader for the bytes of a streamed response, which may split an
// event across chunks.

export type SseEvent = { event: string; data: string };

/** Feed it text as it arrives; it returns each event once its blank line has arrived. */
export function createSseParser(): { push(chunk: string): SseEvent[] } {
  let buffer = "";
  return {
    push(chunk: string): SseEvent[] {
      buffer += chunk;
      // A trailing "\r" may be the first half of "\r\n"; keep it for the next chunk.
      const held = buffer.endsWith("\r") ? "\r" : "";
      const text = (held ? buffer.slice(0, -1) : buffer).replace(/\r\n?/g, "\n");
      const blocks = text.split("\n\n");
      buffer = (blocks.pop() ?? "") + held;
      const events: SseEvent[] = [];
      for (const block of blocks) {
        let event = "message";
        const data: string[] = [];
        for (const line of block.split("\n")) {
          if (line.startsWith("event:")) event = line.slice(6).trim();
          else if (line.startsWith("data:")) data.push(line.slice(5).replace(/^ /, ""));
        }
        if (data.length) events.push({ event, data: data.join("\n") });
      }
      return events;
    },
  };
}
