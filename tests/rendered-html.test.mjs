import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const outputRoot = new URL("../out/", import.meta.url);

async function renderedHtml() {
  return readFile(new URL("index.html", outputRoot), "utf8");
}

test("statically exports the control report", async () => {
  const html = await renderedHtml();
  assert.match(html, /<title>FuzzingBrain Control/);
  assert.match(html, /A fixed point for/);
  assert.match(html, /Control matrix/);
  assert.match(html, /openai\/gpt-5\.5|GPT-5\.5/);
  assert.match(html, /avro-03/);
  assert.match(html, /Protocol before scale/);
  assert.doesNotMatch(
    html,
    /codex-preview|Your site is taking shape|SkeletonPreview/,
  );
});

test("uses GitHub Pages paths and social metadata", async () => {
  const html = await renderedHtml();
  assert.match(html, /\/fuzzingbrain-control\/_next\//);
  assert.match(
    html,
    /https:\/\/posix4e\.github\.io\/fuzzingbrain-control\/og\.png/,
  );
  assert.match(html, /summary_large_image/);
  assert.doesNotMatch(html, /chatgpt\.site|Starter Project|codex-preview/);
});
