#!/usr/bin/env python3
"""Install local pre-commit and pre-push hooks for repo guardrails."""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def git_path(*parts: str) -> Path:
    completed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "--git-path", parts[0]],
        check=True,
        text=True,
        capture_output=True,
    )
    base = Path(completed.stdout.strip())
    return base if len(parts) == 1 else base.joinpath(*parts[1:])


def write_hook(path: Path, scope: str) -> None:
    script = f"""#!/usr/bin/env sh
set -eu
python "{(REPO_ROOT / "scripts" / "git_guardrails.py").as_posix()}" --scope {scope}
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(script, encoding="utf-8")
    path.chmod(0o755)


def main() -> int:
    pre_commit = git_path("hooks", "pre-commit")
    pre_push = git_path("hooks", "pre-push")

    write_hook(pre_commit, "staged")
    write_hook(pre_push, "push")

    print(f"Installed pre-commit hook at {pre_commit}")
    print(f"Installed pre-push hook at {pre_push}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
