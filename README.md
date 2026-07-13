# FuzzingBrain Control

A pinned, reproducible direct-agent control for evaluating
[FuzzingBrain](https://github.com/fuzzingbrain/afc-crs-all-you-need-is-a-fuzzing-brain)
and future fuzzer integrations against
[FuzzingBrain-Bench](https://github.com/OwenSanzas/FuzzingBrain-Bench).

**Website:** <https://posix4e.github.io/fuzzingbrain-control/>

The experiment asks a narrow question before a costly 68-bug sweep: can four
model families complete the same full-scan task across one C, one C++, and one
JVM challenge without infrastructure or protocol failures?

## Control v1

| dimension | selection |
|---|---|
| Models | `openai/gpt-5.5`, `anthropic/claude-sonnet-4.6`, `google/gemini-3-flash-preview`, `deepseek/deepseek-v4-pro` |
| Bugs | `avro-03` (C), `simdutf-01` (C++), `json-java-01` (JVM) |
| Protocol | Public full scan, one sample, up to 100 turns |
| Benchmark | Commit `0831d79057b644498f2ccbc9adae08582366ecd7` |
| Routing | Pinned model IDs through TrustedRouter; no moving aliases |

The preceding two-cell smoke used Gemini 3 Flash and DeepSeek V4 Flash for eight
turns on `avro-03`. Both completed without authentication, tool-schema, Docker,
MCP, or oracle transport failures.

The first published scored snapshot contains 8 of 12 cells. GPT-5.5 solved the
C target; Claude Sonnet 4.6 solved the C and JVM targets. The remaining DeepSeek
cells and Gemini's C++ cell are pending a resumed local runtime.

## Repository

- `app/` — the public results and methodology webpage.
- `benchmark/run_benchmark_control.py` — secret-safe, resumable control runner.
- `benchmark/export_results.py` — exports score and token summaries without
  transcripts, prompts, credentials, or private oracle data.
- `docs/methodology.md` — panel rationale, protocol, and expansion gate.
- `public/control-v1.json` — sanitized machine-readable results, generated after
  the run.

## Reproduce

Clone the current FuzzingBrain-Bench checkout under `.bench/FuzzingBrain-Bench`,
create its Python environment, and ensure Docker can run the public amd64
challenge images. On Apple silicon, the runner selects `linux/amd64` and relies
on binfmt/QEMU emulation.

The runner looks for a TrustedRouter credential assignment in
`$TRUSTEDROUTER_ENV_FILE`, `~/.tr-env`, `~/.env-tr`, or `~/src/.env-tr`. It parses
that file as data and ignores bare lines; it never sources the file or writes the
key to a manifest.

```bash
# Inspect the exact matrix without spending API credits.
python3 benchmark/run_benchmark_control.py --panel control

# Execute or resume the control.
python3 benchmark/run_benchmark_control.py --panel control --execute
```

To publish sanitized summaries:

```bash
python3 benchmark/export_results.py \
  .bench/FuzzingBrain-Bench/runs/control-v1 \
  public/control-v1.json
```

TrustedRouter returns exact per-request microdollar fields, but the current
upstream benchmark discards those fields for vendor-prefixed model IDs. The
published token counts remain valid; an upstream `$0` aggregate is not evidence
of free usage.

## Website development and deployment

Requires Node.js 22.13 or newer.

```bash
npm install
npm run dev
npm test
```

`npm run build` creates a static export under `out/`. Pushes to `main` deploy
that artifact through `.github/workflows/pages.yml`; no server runtime or
repository secret is required.

## Safety and publication boundary

This repository intentionally excludes API keys, `.env` files, raw transcripts,
model prompts and completions, challenge container contents, candidate PoCs, and
private oracle data. Only experiment configuration, capability results, token
buckets, and reproducibility metadata are published.

## License

Apache-2.0. The benchmark and FuzzingBrain retain their respective upstream
licenses.
