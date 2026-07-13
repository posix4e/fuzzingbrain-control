<!-- SPDX-License-Identifier: Apache-2.0 -->
# FuzzingBrain-Bench control v1

This control measures the benchmark's direct model agent before evaluating
FuzzingBrain V2 or a new fuzzer integration. It separates a model/router failure
from a FuzzingBrain regression. The upstream FuzzingBrain checkout's
`v2/scripts/run_bench.py` evaluates the complete V2 pipeline instead.

The control uses pinned TrustedRouter model IDs. Do not substitute
`trustedrouter/auto`, `trustedrouter/fast`, or another moving router alias: the
underlying model can change between cells and invalidate the comparison.

## Panels

| panel | models | bugs | protocol | cells | purpose |
|---|---:|---:|---:|---:|---|
| `smoke` | 2 | 1 | 1 sample, 8 turns | 2 | Validate router, tools, Docker, MCP, and oracle plumbing only |
| `control` | 4 | 3 | 1 sample, 100 turns | 12 | Comparable public full-scan pilot |

The smoke models are `google/gemini-3-flash-preview` and
`deepseek/deepseek-v4-flash`. They are inexpensive representatives of two
provider families. A smoke result is not a model-quality score because it uses
a reduced turn budget.

The control models are:

- `openai/gpt-5.5`: strong closed-model ceiling.
- `anthropic/claude-sonnet-4.6`: independent strong closed-model family.
- `google/gemini-3-flash-preview`: fast, low-cost closed model.
- `deepseek/deepseek-v4-pro`: strong open-weight family.

The bug slice covers the benchmark's three runtime families without using one
of its known slow cases:

- `avro-03`: C / ASan / libFuzzer harness.
- `simdutf-01`: C++ / ASan / libFuzzer harness.
- `json-java-01`: JVM / Jazzer harness.

The control keeps the public full-scan budget of 100 turns. Cost is reduced by
using three representative bugs, not by changing the task protocol.

## Run

The wrapper parses the unusual credential file as data and ignores bare lines;
it never sources the file or copies the secret into this repository.
The public challenge images are amd64-only; on Apple silicon, the wrapper sets
`DOCKER_DEFAULT_PLATFORM=linux/amd64` and relies on the runtime's binfmt/QEMU
emulation.

```bash
# Secret-free plan (default)
python3 benchmark/run_benchmark_control.py --panel smoke

# After Docker is installed/running
python3 benchmark/run_benchmark_control.py --panel smoke --execute
python3 benchmark/run_benchmark_control.py --panel control --execute
```

Runs are resumable under `control-v1-smoke` and `control-v1`. Each executed run
writes `control-manifest.json` beside the results with the exact benchmark
commit, model IDs, bugs, samples, turn budget, and command. It never stores the
API key.

TrustedRouter returns exact per-request microdollar cost fields, but the current
upstream benchmark discards those extra fields and has no price entries for
vendor-prefixed IDs. Therefore, use its token counts plus TrustedRouter billing
as the cost record; a `$0` benchmark aggregate for these IDs is not free usage.

## Initial smoke result (2026-07-13)

The two-cell smoke completed against benchmark commit
`0831d79057b644498f2ccbc9adae08582366ecd7` in 95 seconds. Both cells reached
all 8 turns without an authentication error, malformed tool call, refusal,
Docker/MCP failure, or oracle transport error. Neither found the bug in this
reduced budget, which is not a failure of the infrastructure gate.

| model | termination | score | fresh input | cache read | output |
|---|---|---:|---:|---:|---:|
| `google/gemini-3-flash-preview` | `max_turns` | 0/5 | 19,542 | 0 | 209 |
| `deepseek/deepseek-v4-flash` | `max_turns` | 0/5 | 14,957 | 21,888 | 2,801 |

## Expansion gate

Do not start the full 68-bug sweep until all 12 control cells produce a
`score.json` without authentication, schema/tool-call, Docker, MCP, timeout, or
oracle transport failures. Model success at finding each bug is not required to
pass this infrastructure gate.

For the next model-expansion slice, add one expensive ceiling and three other
families: `anthropic/claude-opus-4.7`,
`google/gemini-3.1-pro-preview`, `moonshotai/kimi-k2.6`, and `z-ai/glm-5.2`.
Run those on the same three bugs before deciding which models earn a 68-bug,
two-sample sweep. Opus, Kimi, and GLM returned tool calls in a minimal router
probe. Gemini 3.1 Pro returned a valid completion but chose text instead of the
tool in that probe, so keep it provisional until it passes a real smoke cell.
