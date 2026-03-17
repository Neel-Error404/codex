#!/usr/bin/env python3
"""Run the core validation suite for the GPT-5.4 agent upgrade branch."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
WORKDIR = REPO_ROOT / "codex-rs"


def resolve_cargo() -> str:
    env_cargo = os.environ.get("CARGO")
    if env_cargo:
        return env_cargo

    cargo_on_path = shutil.which("cargo")
    if cargo_on_path:
        return cargo_on_path

    userprofile = os.environ.get("USERPROFILE")
    if userprofile:
        candidate = Path(userprofile) / ".cargo" / "bin" / "cargo.exe"
        if candidate.exists():
            return str(candidate)

    return "cargo"


CARGO = resolve_cargo()


@dataclass
class Suite:
    name: str
    description: str
    command: list[str]


@dataclass
class SuiteResult:
    name: str
    description: str
    command: list[str]
    exit_code: int
    duration_seconds: float
    ok: bool


SUITES = [
    Suite(
        name="tool_search",
        description="Deferred tool discovery and tool_search normalization/tests.",
        command=[
            CARGO,
            "test",
            "-p",
            "codex-core",
            "--lib",
            "tool_search",
            "--",
            "--nocapture",
        ],
    ),
    Suite(
        name="sparse_context",
        description="Sparse-context, js_repl recursive inspection, and persistence tests.",
        command=[
            CARGO,
            "test",
            "-p",
            "codex-core",
            "--lib",
            "sparse_context",
            "--",
            "--nocapture",
        ],
    ),
    Suite(
        name="thread_synopsis_state_db",
        description="Structured thread synopsis bootstrap from persisted state.",
        command=[
            CARGO,
            "test",
            "-p",
            "codex-core",
            "--lib",
            "build_initial_context_includes_thread_synopsis_from_state_db",
            "--",
            "--nocapture",
        ],
    ),
    Suite(
        name="thread_sparse_context_state_db",
        description="SQLite persistence for full sparse-context payload blobs.",
        command=[
            CARGO,
            "test",
            "-p",
            "codex-state",
            "upsert_thread_sparse_context_persists_latest_value",
            "--",
            "--nocapture",
        ],
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format.",
    )
    parser.add_argument(
        "--suite",
        action="append",
        choices=[suite.name for suite in SUITES],
        help="Run only the named suite. Can be provided multiple times.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available suites and exit.",
    )
    return parser.parse_args()


def selected_suites(selected_names: list[str] | None) -> list[Suite]:
    if not selected_names:
        return SUITES
    selected = set(selected_names)
    return [suite for suite in SUITES if suite.name in selected]


def run_suite(suite: Suite) -> SuiteResult:
    started = time.perf_counter()
    completed = subprocess.run(suite.command, cwd=WORKDIR, check=False)
    duration = time.perf_counter() - started
    return SuiteResult(
        name=suite.name,
        description=suite.description,
        command=suite.command,
        exit_code=completed.returncode,
        duration_seconds=round(duration, 2),
        ok=completed.returncode == 0,
    )


def emit_text(results: list[SuiteResult]) -> None:
    print("Agent upgrade validation suites")
    print(f"Repo: {REPO_ROOT}")
    print(f"Workdir: {WORKDIR}")
    print("")
    for result in results:
        status = "PASS" if result.ok else "FAIL"
        command = " ".join(result.command)
        print(f"[{status}] {result.name}")
        print(f"  {result.description}")
        print(f"  command: {command}")
        print(f"  duration_seconds: {result.duration_seconds}")
        print(f"  exit_code: {result.exit_code}")
    print("")
    failures = [result.name for result in results if not result.ok]
    if failures:
        print(f"Overall: FAIL ({', '.join(failures)})")
    else:
        print("Overall: PASS")


def emit_json(results: list[SuiteResult]) -> None:
    payload = {
        "repo_root": str(REPO_ROOT),
        "workdir": str(WORKDIR),
        "results": [asdict(result) for result in results],
        "ok": all(result.ok for result in results),
    }
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")


def main() -> int:
    args = parse_args()
    suites = selected_suites(args.suite)

    if args.list:
        for suite in suites:
            print(f"{suite.name}: {suite.description}")
        return 0

    results = [run_suite(suite) for suite in suites]
    if args.format == "json":
        emit_json(results)
    else:
        emit_text(results)
    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
