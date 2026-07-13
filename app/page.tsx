import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "FuzzingBrain Control — Reproducible Model Baselines",
  description:
    "A pinned, three-runtime control for evaluating FuzzingBrain and future fuzzer integrations.",
};

type Status = "solved" | "partial" | "miss" | "running" | "pending";

type Cell = {
  score?: number;
  turns?: number;
  status: Status;
  reason?: string;
};

type ModelRow = {
  id: string;
  short: string;
  family: string;
  role: string;
  cells: Record<string, Cell>;
};

const bugs = [
  { id: "avro-03", language: "C", harness: "ASan · libFuzzer" },
  { id: "simdutf-01", language: "C++", harness: "ASan · libFuzzer" },
  { id: "json-java-01", language: "JVM", harness: "Jazzer" },
];

const models: ModelRow[] = [
  {
    id: "openai/gpt-5.5",
    short: "GPT-5.5",
    family: "OpenAI",
    role: "Strong closed ceiling",
    cells: {
      "avro-03": { score: 5, turns: 15, status: "solved", reason: "voluntary" },
      "simdutf-01": { score: 0, turns: 12, status: "miss", reason: "voluntary" },
      "json-java-01": { score: 2, turns: 9, status: "partial", reason: "voluntary" },
    },
  },
  {
    id: "anthropic/claude-sonnet-4.6",
    short: "Sonnet 4.6",
    family: "Anthropic",
    role: "Independent closed family",
    cells: {
      "avro-03": { score: 5, turns: 56, status: "solved", reason: "voluntary" },
      "simdutf-01": { score: 0, turns: 100, status: "miss", reason: "voluntary" },
      "json-java-01": { score: 5, turns: 15, status: "solved", reason: "voluntary" },
    },
  },
  {
    id: "google/gemini-3-flash-preview",
    short: "Gemini 3 Flash",
    family: "Google",
    role: "Fast low-cost control",
    cells: {
      "avro-03": { score: 0, turns: 100, status: "miss", reason: "max_turns" },
      "simdutf-01": { status: "pending" },
      "json-java-01": { score: 0, turns: 100, status: "miss", reason: "max_turns" },
    },
  },
  {
    id: "deepseek/deepseek-v4-pro",
    short: "DeepSeek V4 Pro",
    family: "DeepSeek",
    role: "Open-weight family",
    cells: {
      "avro-03": { status: "pending" },
      "simdutf-01": { status: "pending" },
      "json-java-01": { status: "pending" },
    },
  },
];

const completedCells = models.reduce(
  (count, model) =>
    count +
    Object.values(model.cells).filter(
      (cell) => cell.status !== "pending" && cell.status !== "running",
    ).length,
  0,
);

function CellScore({ cell }: { cell: Cell }) {
  if (cell.status === "pending" || cell.status === "running") {
    return (
      <div className={`score score-${cell.status}`}>
        <span className="status-dot" aria-hidden="true" />
        <span>{cell.status}</span>
      </div>
    );
  }

  return (
    <div className={`score score-${cell.status}`}>
      <strong>{cell.score}/5</strong>
      <span>{cell.turns} turns</span>
    </div>
  );
}

export default function Home() {
  return (
    <main>
      <header className="site-header">
        <a className="wordmark" href="#top" aria-label="FuzzingBrain Control home">
          <span className="wordmark-mark">FB</span>
          <span>CONTROL / V1</span>
        </a>
        <nav aria-label="Primary navigation">
          <a href="#results">Results</a>
          <a href="#protocol">Protocol</a>
          <a
            className="nav-github"
            href="https://github.com/posix4e/fuzzingbrain-control"
          >
            GitHub ↗
          </a>
        </nav>
      </header>

      <section className="hero" id="top">
        <div className="eyebrow">
          <span className="pulse" aria-hidden="true" />
          Control run in progress · 8/12 cells · July 13, 2026
        </div>
        <h1>
          A fixed point for
          <br />
          <span>fuzzer progress.</span>
        </h1>
        <p className="hero-copy">
          Before extending FuzzingBrain to new fuzzers, we need to know what the
          models can do on their own. This pinned control holds model, task, and
          budget constant across C, C++, and JVM targets.
        </p>
        <div className="hero-actions">
          <a className="button button-primary" href="#results">
            Inspect the matrix
          </a>
          <a
            className="button button-quiet"
            href="https://github.com/OwenSanzas/FuzzingBrain-Bench"
          >
            Benchmark source ↗
          </a>
        </div>
      </section>

      <section className="stat-grid" aria-label="Control summary">
        <article>
          <span className="stat-label">Scored cells</span>
          <strong>{completedCells}<small>/12</small></strong>
          <span className="stat-note">one sample · up to 100 turns</span>
        </article>
        <article>
          <span className="stat-label">Pinned models</span>
          <strong>4</strong>
          <span className="stat-note">four independent families</span>
        </article>
        <article>
          <span className="stat-label">Runtime families</span>
          <strong>3</strong>
          <span className="stat-note">C · C++ · JVM</span>
        </article>
        <article>
          <span className="stat-label">Benchmark commit</span>
          <strong className="commit">0831d790</strong>
          <span className="stat-note">68 public challenges</span>
        </article>
      </section>

      <section className="results-section" id="results">
        <div className="section-heading">
          <div>
            <span className="kicker">01 / Current evidence</span>
            <h2>Control matrix</h2>
          </div>
          <p>
            Scores show fired capability rungs out of five. A cell is solved only
            when every rung required by that challenge fires.
          </p>
        </div>

        <div className="matrix-wrap">
          <table>
            <thead>
              <tr>
                <th scope="col">Model</th>
                {bugs.map((bug) => (
                  <th scope="col" key={bug.id}>
                    <span>{bug.id}</span>
                    <small>{bug.language} · {bug.harness}</small>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {models.map((model) => (
                <tr key={model.id}>
                  <th scope="row">
                    <span className="model-name">{model.short}</span>
                    <small>{model.family} · {model.role}</small>
                  </th>
                  {bugs.map((bug) => (
                    <td key={bug.id}>
                      <CellScore cell={model.cells[bug.id]} />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="legend" aria-label="Result legend">
          <span><i className="legend-solved" /> solved</span>
          <span><i className="legend-partial" /> partial</span>
          <span><i className="legend-miss" /> no rung fired</span>
          <span><i className="legend-running" /> running / pending</span>
        </div>
      </section>

      <section className="smoke-callout">
        <div className="smoke-index">00</div>
        <div>
          <span className="kicker">Infrastructure gate · passed</span>
          <h2>Two models, eight turns, zero protocol failures.</h2>
          <p>
            Gemini 3 Flash and DeepSeek V4 Flash both completed the reduced-budget
            smoke on <code>avro-03</code>. Neither found the bug, but both produced
            complete transcripts and scores without authentication, tool-schema,
            Docker, MCP, or oracle transport errors.
          </p>
        </div>
        <div className="smoke-metric">
          <strong>95s</strong>
          <span>wall time</span>
        </div>
      </section>

      <section className="protocol-section" id="protocol">
        <div className="section-heading">
          <div>
            <span className="kicker">02 / Experimental design</span>
            <h2>Protocol before scale</h2>
          </div>
          <p>
            We reduce cost by narrowing the matrix—not by weakening the public
            full-scan task or changing its turn budget.
          </p>
        </div>

        <div className="protocol-grid">
          <article>
            <span className="step-number">A</span>
            <h3>Pin the route</h3>
            <p>
              Explicit model IDs replace moving aliases. Every cell records the
              model, benchmark commit, bug, sample, and turn ceiling.
            </p>
          </article>
          <article>
            <span className="step-number">B</span>
            <h3>Sample the runtimes</h3>
            <p>
              One C, one C++, and one JVM challenge expose different harness and
              tool-use behavior before the 68-bug sweep.
            </p>
          </article>
          <article>
            <span className="step-number">C</span>
            <h3>Repeat for variance</h3>
            <p>
              The next gate repeats the same 12 cells with sample 1. One lucky
              exploit should not choose the full-sweep lineup.
            </p>
          </article>
          <article>
            <span className="step-number">D</span>
            <h3>Change one system</h3>
            <p>
              Freeze this direct-agent baseline, then compare unmodified
              FuzzingBrain and each fuzzer integration on the same matrix.
            </p>
          </article>
        </div>
      </section>

      <section className="decision-section">
        <div>
          <span className="kicker">03 / Decision rule</span>
          <h2>Earn the 68-bug sweep.</h2>
        </div>
        <ol>
          <li><span>1</span>Complete 12/12 cells without systemic failures.</li>
          <li><span>2</span>Capture exact router-reported spend.</li>
          <li><span>3</span>Repeat the panel and measure variance.</li>
          <li><span>4</span>Expand model families on the same three bugs.</li>
          <li><span>5</span>Select the full sweep by quality, stability, and cost.</li>
        </ol>
      </section>

      <footer>
        <div>
          <span className="wordmark-mark">FB</span>
          <p>
            Reproducible controls for FuzzingBrain.<br />
            No credentials or private oracle data are published.
          </p>
        </div>
        <div className="footer-links">
          <a href="https://fuzzingbrain.github.io/fuzzingbrain-tech-report.pdf">Technical report ↗</a>
          <a href="https://trustedrouter.com/docs">Router documentation ↗</a>
          <a href="https://github.com/posix4e/fuzzingbrain-control">Source ↗</a>
        </div>
      </footer>
    </main>
  );
}
