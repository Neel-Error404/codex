#!/usr/bin/env python3
"""Scan repo changes for likely credentials before commit/push."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent

SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("openai_api_key", re.compile(r"\bsk-(proj-)?[A-Za-z0-9_-]{20,}\b")),
    (
        "github_token",
        re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b"),
    ),
    ("github_pat", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
    ("aws_access_key_id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    (
        "azure_connection_string",
        re.compile(r"DefaultEndpointsProtocol=https;AccountName=[^;\s]+;AccountKey=[^;\s]+"),
    ),
    (
        "slack_token",
        re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    ),
    (
        "private_key_block",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |)PRIVATE KEY-----"),
    ),
]

SUSPICIOUS_FILENAMES = {
    ".env",
    ".env.local",
    ".env.development",
    ".env.production",
    ".env.staging",
    ".npmrc",
    ".pypirc",
    "id_rsa",
    "id_ed25519",
    "credentials",
    "secrets.toml",
}

SUSPICIOUS_SUFFIXES = {".pem", ".p12", ".pfx", ".key", ".asc"}

ALLOWLISTED_FINDINGS: set[tuple[str, str]] = {
    ("suspicious_filename", ".npmrc"),
    ("openai_api_key", "codex-rs/cli/src/login.rs"),
}

TEXT_SUFFIX_ALLOWLIST = {
    ".md",
    ".txt",
    ".json",
    ".toml",
    ".yaml",
    ".yml",
    ".rs",
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".sh",
    ".ps1",
    ".sql",
    ".cfg",
    ".ini",
}


@dataclass
class Finding:
    kind: str
    path: str
    detail: str


def run_git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        check=check,
        text=True,
        encoding="utf-8",
        errors="ignore",
        capture_output=True,
    )


def run_git_bytes(*args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        check=check,
        text=False,
        capture_output=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scope",
        choices=("staged", "push", "tracked"),
        default="staged",
        help="Which file set to inspect.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format.",
    )
    return parser.parse_args()


def candidate_files(scope: str) -> list[Path]:
    if scope == "staged":
        completed = run_git("diff", "--cached", "--name-only", "--diff-filter=ACMR", check=False)
        names = completed.stdout.splitlines()
    elif scope == "push":
        completed = run_git(
            "diff",
            "--name-only",
            "--diff-filter=ACMR",
            "@{upstream}...HEAD",
            check=False,
        )
        if completed.returncode != 0:
            completed = run_git("ls-files", check=False)
        names = completed.stdout.splitlines()
    else:
        completed = run_git("ls-files", check=False)
        names = completed.stdout.splitlines()

    return [REPO_ROOT / name for name in names if name.strip()]


def should_skip_binary_bytes(data: bytes, path: Path) -> bool:
    if path.suffix.lower() in TEXT_SUFFIX_ALLOWLIST:
        return False
    return b"\x00" in data[:4096]


def read_candidate_bytes(path: Path, scope: str) -> bytes | None:
    rel = path.relative_to(REPO_ROOT).as_posix()
    if scope == "staged":
        completed = run_git_bytes("show", f":{rel}", check=False)
        if completed.returncode == 0:
            return completed.stdout
    elif scope in {"push", "tracked"}:
        completed = run_git_bytes("show", f"HEAD:{rel}", check=False)
        if completed.returncode == 0:
            return completed.stdout

    try:
        return path.read_bytes()
    except OSError:
        return None


def inspect_filename(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    lower_name = path.name.lower()
    lower_parts = {part.lower() for part in path.parts}

    if lower_name in SUSPICIOUS_FILENAMES:
        findings.append(
            Finding(
                kind="suspicious_filename",
                path=str(path.relative_to(REPO_ROOT)),
                detail=f"tracked file name `{path.name}` usually stores local credentials",
            )
        )

    if path.suffix.lower() in SUSPICIOUS_SUFFIXES and "fixtures" not in lower_parts:
        findings.append(
            Finding(
                kind="suspicious_suffix",
                path=str(path.relative_to(REPO_ROOT)),
                detail=f"tracked file suffix `{path.suffix}` may contain private material",
            )
        )

    return findings


def is_allowlisted(kind: str, rel: str) -> bool:
    normalized = rel.replace("\\", "/")
    return (kind, normalized) in ALLOWLISTED_FINDINGS


def inspect_content(path: Path, scope: str) -> list[Finding]:
    findings: list[Finding] = []
    candidate = read_candidate_bytes(path, scope)
    if candidate is None or should_skip_binary_bytes(candidate, path):
        return findings

    text = candidate.decode("utf-8", errors="ignore")
    rel = str(path.relative_to(REPO_ROOT))

    for kind, pattern in SECRET_PATTERNS:
        match = pattern.search(text)
        if match and not is_allowlisted(kind, rel):
            findings.append(
                Finding(
                    kind=kind,
                    path=rel,
                    detail=f"matched `{match.group(0)[:80]}`",
                )
            )

    return findings


def emit_text(findings: list[Finding], scope: str) -> None:
    print(f"git_guardrails scope={scope}")
    if not findings:
        print("PASS: no likely credential leaks detected")
        return

    print("FAIL: potential credential leaks detected")
    for finding in findings:
        print(f"- [{finding.kind}] {finding.path}: {finding.detail}")


def emit_json(findings: list[Finding], scope: str) -> None:
    payload = {
        "scope": scope,
        "ok": not findings,
        "findings": [asdict(finding) for finding in findings],
    }
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")


def main() -> int:
    args = parse_args()
    files = candidate_files(args.scope)
    findings: list[Finding] = []

    for path in files:
        for finding in inspect_filename(path):
            if not is_allowlisted(finding.kind, finding.path):
                findings.append(finding)
        findings.extend(inspect_content(path, args.scope))

    if args.format == "json":
        emit_json(findings, args.scope)
    else:
        emit_text(findings, args.scope)

    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
