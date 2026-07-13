#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Run the pinned FuzzingBrain-Bench control panels through TrustedRouter.

The credential file used on this machine is intentionally parsed as data.  It
is never sourced by a shell: only recognized KEY=VALUE assignments are read,
and unrelated/bare lines are ignored.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


REPO = Path(__file__).resolve().parents[1]
DEFAULT_BENCH = REPO / ".bench" / "FuzzingBrain-Bench"
DEFAULT_ROUTER_BASE = "https://api.trustedrouter.com/v1"
ALLOWED_ROUTER_HOSTS = {"api.trustedrouter.com"}


@dataclass(frozen=True)
class Panel:
    models: tuple[str, ...]
    bugs: tuple[str, ...]
    samples: tuple[int, ...]
    max_turns: int
    timeout_s: int
    experiment: str
    purpose: str


PANELS = {
    # This only validates Docker, MCP/oracle, router, and tool-call plumbing.  A
    # reduced turn budget makes it unsuitable for model-quality comparisons.
    "smoke": Panel(
        models=(
            "google/gemini-3-flash-preview",
            "deepseek/deepseek-v4-flash",
        ),
        bugs=("avro-03",),
        samples=(0,),
        max_turns=8,
        timeout_s=900,
        experiment="control-v1-smoke",
        purpose="cheap transport and harness validation (not a scored control)",
    ),
    # Keep the public full-scan protocol's complete 100-turn budget.  We reduce
    # cost by sampling languages and model families, not by changing the task.
    "control": Panel(
        models=(
            "openai/gpt-5.5",
            "anthropic/claude-sonnet-4.6",
            "google/gemini-3-flash-preview",
            "deepseek/deepseek-v4-pro",
        ),
        bugs=("avro-03", "simdutf-01", "json-java-01"),
        samples=(0,),
        max_turns=100,
        timeout_s=1800,
        experiment="control-v1",
        purpose="pinned 4-model x 3-language scientific pilot",
    ),
}


def _env_candidates(explicit: str | None) -> list[Path]:
    if explicit:
        return [Path(explicit).expanduser()]
    configured = os.environ.get("TRUSTEDROUTER_ENV_FILE")
    candidates = [
        Path.home() / ".tr-env",
        Path.home() / ".env-tr",
        Path.home() / "src" / ".env-tr",
    ]
    if configured:
        candidates.insert(0, Path(configured).expanduser())
    return candidates


def _find_env_file(explicit: str | None) -> Path:
    for candidate in _env_candidates(explicit):
        if candidate.is_file():
            return candidate.resolve()
    searched = ", ".join(str(p) for p in _env_candidates(explicit))
    raise RuntimeError(f"TrustedRouter credential file not found; searched: {searched}")


def _strip_outer_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _read_router_credentials(path: Path) -> tuple[str, str]:
    assignments: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            # In particular, never concatenate or execute an opaque bare line.
            continue
        name, value = line.split("=", 1)
        name = name.removeprefix("export ").strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            continue
        assignments[name] = _strip_outer_quotes(value)

    key = assignments.get("TRUSTEDROUTER_API_KEY") or assignments.get(
        "OPENAI_API_KEY"
    )
    if not key:
        raise RuntimeError(
            f"{path} has no TRUSTEDROUTER_API_KEY or OPENAI_API_KEY assignment"
        )
    if any(ch.isspace() for ch in key) or any(x in key for x in ("${", "$(", "`")):
        raise RuntimeError(f"refusing suspicious API-key syntax in {path}")

    raw_base = (
        os.environ.get("TRUSTEDROUTER_BASE_URL")
        or assignments.get("TRUSTEDROUTER_BASE_URL")
        or assignments.get("OPENAI_BASE_URL")
        or DEFAULT_ROUTER_BASE
    )
    # Handles a literal URL as well as ${VAR:-https://...} without evaluating
    # the shell expansion.
    match = re.search(r"https://[^\s}\"']+", raw_base)
    if not match:
        raise RuntimeError(f"no literal HTTPS TrustedRouter URL found in {path}")
    base = match.group(0).rstrip("/")
    parsed = urlparse(base)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_ROUTER_HOSTS:
        raise RuntimeError(
            f"refusing to send the API key to untrusted host {parsed.hostname!r}"
        )
    return key, base


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return proc.stdout.strip() if proc.returncode == 0 else "unknown"


def _build_command(
    python: Path,
    bench: Path,
    panel: Panel,
    experiment: str,
    jobs: int,
) -> list[str]:
    return [
        str(python),
        "-m",
        "fbbench.sweep.orchestrator",
        "--models",
        ",".join(panel.models),
        "--bugs",
        ",".join(panel.bugs),
        "--samples",
        ",".join(str(sample) for sample in panel.samples),
        "--max-turns",
        str(panel.max_turns),
        "--timeout",
        str(panel.timeout_s),
        "--exp",
        experiment,
        "--output",
        str(bench / "runs"),
        "--jobs",
        str(jobs),
        "--no-dashboard",
    ]


def _write_manifest(
    bench: Path,
    env_file: Path,
    base_url: str,
    panel_name: str,
    panel: Panel,
    experiment: str,
    jobs: int,
    command: list[str],
) -> Path:
    out = bench / "runs" / experiment
    out.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": 1,
        "panel": panel_name,
        "purpose": panel.purpose,
        "experiment": experiment,
        "models": list(panel.models),
        "bugs": list(panel.bugs),
        "samples": list(panel.samples),
        "max_turns": panel.max_turns,
        "timeout_s": panel.timeout_s,
        "jobs": jobs,
        "cells": len(panel.models) * len(panel.bugs) * len(panel.samples),
        "benchmark_commit": _git(bench, "rev-parse", "HEAD"),
        "controller_commit": _git(REPO, "rev-parse", "HEAD"),
        "controller_dirty": bool(_git(REPO, "status", "--short")),
        "router_base_url": base_url,
        "docker_default_platform": "linux/amd64",
        "credential_source": str(env_file),
        "command": command,
        "cost_note": (
            "TrustedRouter billing is authoritative. The upstream benchmark "
            "does not price vendor-prefixed router model IDs."
        ),
    }
    path = out / "control-manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    # Keep the plan ahead of the child process's live output when stdout is a
    # pipe (the normal Codex/CI case).
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(line_buffering=True)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--panel", choices=sorted(PANELS), default="smoke")
    parser.add_argument("--bench", default=str(DEFAULT_BENCH))
    parser.add_argument("--env-file", default=None)
    parser.add_argument("--exp", default=None, help="override the resumable experiment name")
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="run the matrix; without this flag, print a secret-free plan",
    )
    args = parser.parse_args(argv)

    if args.jobs < 1:
        parser.error("--jobs must be at least 1")

    panel = PANELS[args.panel]
    bench = Path(args.bench).expanduser().resolve()
    if not (bench / "pyproject.toml").is_file():
        parser.error(f"benchmark checkout not found at {bench}")
    bench_dirty = _git(bench, "status", "--short")
    if bench_dirty:
        parser.error(f"benchmark checkout must be clean; found:\n{bench_dirty}")

    env_file = _find_env_file(args.env_file)
    key, base_url = _read_router_credentials(env_file)
    mode = stat.S_IMODE(env_file.stat().st_mode)
    if mode & 0o077:
        print(
            f"WARNING: {env_file} is mode {mode:03o}; consider chmod 600 {env_file}",
            file=sys.stderr,
        )

    python = bench / ".venv" / "bin" / "python"
    experiment = args.exp or panel.experiment
    command = _build_command(python, bench, panel, experiment, args.jobs)
    cells = len(panel.models) * len(panel.bugs) * len(panel.samples)

    print(f"panel:      {args.panel} - {panel.purpose}")
    print(f"benchmark:  {bench} @ {_git(bench, 'rev-parse', '--short=12', 'HEAD')}")
    print(f"credentials: {env_file} (parsed, never sourced)")
    print(f"models:     {', '.join(panel.models)}")
    print(f"bugs:       {', '.join(panel.bugs)}")
    print(f"matrix:     {cells} cells, samples={panel.samples}, turns={panel.max_turns}")
    print(f"experiment: {experiment}")
    print(f"command:    {shlex.join(command)}")

    if not args.execute:
        print("plan only; add --execute to run")
        return 0
    if not python.is_file():
        parser.error(
            f"benchmark virtualenv missing; create it with:\n"
            f"  python3 -m venv {bench / '.venv'}\n"
            f"  {bench / '.venv/bin/python'} -m pip install -e {bench}"
        )
    if shutil.which("docker") is None:
        parser.error("Docker is required to execute FuzzingBrain-Bench")
    docker_info = subprocess.run(
        ["docker", "info"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if docker_info.returncode != 0:
        parser.error("the Docker CLI is installed, but its daemon is not running")

    manifest = _write_manifest(
        bench,
        env_file,
        base_url,
        args.panel,
        panel,
        experiment,
        args.jobs,
        command,
    )
    print(f"manifest:   {manifest}")

    env = os.environ.copy()
    env["OPENROUTER_API_KEY"] = key
    env["OPENROUTER_BASE_URL"] = base_url
    # The public challenge images are currently amd64-only. Colima provides
    # binfmt/QEMU on Apple silicon, but the Docker CLI must select that platform.
    env["DOCKER_DEFAULT_PLATFORM"] = "linux/amd64"
    return subprocess.run(command, cwd=bench, env=env, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
