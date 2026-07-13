import assert from "node:assert/strict";
import test from "node:test";

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request("https://control.example/", {
      headers: { accept: "text/html", host: "control.example" },
    }),
    {
      ASSETS: {
        fetch: async () => new Response("Not found", { status: 404 }),
      },
    },
    {
      waitUntil() {},
      passThroughOnException() {},
    },
  );
}

test("server-renders the control report", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /<title>FuzzingBrain Control/);
  assert.match(html, /A fixed point for/);
  assert.match(html, /Control matrix/);
  assert.match(html, /openai\/gpt-5\.5|GPT-5\.5/);
  assert.match(html, /avro-03/);
  assert.match(html, /Protocol before scale/);
  assert.doesNotMatch(html, /codex-preview|Your site is taking shape|SkeletonPreview/);
});

test("publishes social metadata without starter markers", async () => {
  const response = await render();
  const html = await response.text();
  assert.match(html, /og:image/);
  assert.match(html, /og\.png/);
  assert.match(html, /summary_large_image/);
  assert.doesNotMatch(html, /Starter Project|codex-preview/);
});
