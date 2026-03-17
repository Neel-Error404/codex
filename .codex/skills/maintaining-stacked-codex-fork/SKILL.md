---
name: maintaining-stacked-codex-fork
description: Use when syncing this Codex fork with upstream while preserving stacked local branches, worktrees, validation steps, and credential-safety checks.
---

# Maintaining Stacked Codex Fork

## Overview

Use this when updating the local Codex fork from `openai/codex` without losing the stacked custom layers.
Prefer rebasing the stack in order instead of merging random branches together.

## Branch Roles

- `main`: local mirror of upstream `openai/codex/main`; keep it clean
- `feat/azure-provider-retries-realigned`: provider/chat-wire base layer
- `feat/gpt54-agent-upgrades`: GPT-5.4 tool search, compaction, and sparse-context layer

## Guardrails First

1. Confirm the target worktree is clean with `git status --short`.
2. Install hooks once per clone with `python scripts/install_git_guardrails.py`.
3. Run `python scripts/git_guardrails.py --scope staged` before commits and trust hook failures.
4. Never commit real credentials, local `config.toml`, `.env`, cert bundles, or private keys.
5. Keep secrets in user-local config and environment variables, not in the repo.

## Update Protocol

1. `git fetch upstream origin --prune`
2. Update local `main` to `upstream/main`
3. Rebase `feat/azure-provider-retries-realigned` onto refreshed `main`
4. Run the provider-layer tests before moving on
5. Rebase `feat/gpt54-agent-upgrades` onto refreshed `feat/azure-provider-retries-realigned`
6. Run `just agent-upgrades-check`
7. Update the founder log / maintenance docs with new commit SHAs and validation status
8. Push rebased branches with `git push --force-with-lease origin <branch>`

## Conflict Policy

- Prefer `rebase` for upstream sync
- Prefer `cherry-pick` for selectively lifting isolated fixes across branches
- Avoid merge commits on maintenance branches unless you are intentionally creating an integration branch
- If upstream changes overlap `tools/spec.rs`, `tools/js_repl/mod.rs`, state migrations, or provider transport code, review those diffs manually before continuing

## Validation

- Provider layer: run the targeted `codex-core` and `codex-api` tests for custom provider support
- GPT-5.4 layer: run `python scripts/agent_upgrade_check.py --format text`
- If either layer changes transport, tool schema, or state persistence, rerun focused exact tests in addition to the scripted suite

## Output

Leave behind:

- updated branch tips
- validation evidence
- updated docs under `docs/plans/`
- no unreviewed secret-scan findings
