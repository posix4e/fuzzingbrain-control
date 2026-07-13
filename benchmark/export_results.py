#!/usr/bin/env python3
"""Export sanitized FuzzingBrain-Bench score summaries for publication."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path


def export(run_dir: Path) -> dict:
    manifest_path = run_dir / "control-manifest.json"
    if not manifest_path.is_file():
        raise SystemExit(f"missing {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    results = []
    for score_path in sorted(run_dir.glob("**/score.json")):
        score = json.loads(score_path.read_text(encoding="utf-8"))
        cost_path = score_path.parent / "cost.json"
        cost = (
            json.loads(cost_path.read_text(encoding="utf-8"))
            if cost_path.is_file()
            else {}
        )
        required = score.get("config", {}).get("capability_set", [])
        capabilities = score.get("capabilities", {})
        results.append(
            {
                "model": score.get("model"),
                "bug_id": score.get("bug_id"),
                "solved": bool(required)
                and all(capabilities.get(name) == "fired" for name in required),
                "tier_score": score.get("tier_score"),
                "capabilities": capabilities,
                "turns_used": score.get("turns_used"),
                "duration_s": score.get("duration_s"),
                "terminated_reason": score.get("terminated_reason"),
                "refusal_retries": score.get("refusal_retries"),
                "malformed_retries": score.get("malformed_retries"),
                "input_tokens": cost.get("input_tokens"),
                "cache_read_tokens": cost.get("cache_read_tokens"),
                "cache_write_tokens": cost.get("cache_write_tokens"),
                "output_tokens": cost.get("output_tokens"),
                "pricing_known": cost.get("pricing_known", False),
            }
        )

    return {
        "schema_version": 1,
        "published_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "experiment": manifest.get("experiment"),
        "panel": manifest.get("panel"),
        "benchmark_commit": manifest.get("benchmark_commit"),
        "models": manifest.get("models", []),
        "bugs": manifest.get("bugs", []),
        "samples": manifest.get("samples", []),
        "max_turns": manifest.get("max_turns"),
        "timeout_s": manifest.get("timeout_s"),
        "expected_cells": manifest.get("cells"),
        "completed_cells": len(results),
        "results": results,
        "cost_note": (
            "The upstream benchmark does not preserve TrustedRouter's exact "
            "microdollar response field for vendor-prefixed model IDs. Token "
            "counts are published; the benchmark's displayed $0 is not spend."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    data = export(args.run_dir.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(
        f"exported {data['completed_cells']}/{data['expected_cells']} cells "
        f"to {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
