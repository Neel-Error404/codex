# Founder Log: Codex Custom Stack

Date: 2026-03-17

## What exists now

- upstream-aligned provider base branch:
  - `feat/azure-provider-retries-realigned`
  - tip: `078d7be7d`
- stacked GPT-5.4 branch:
  - `feat/gpt54-agent-upgrades`
  - tip: `8b59426dc`

## What shipped in the stack

- custom provider chat-wire support plus provider-defined model lists
- deferred `tool_search` for app tools and deferred dynamic tools
- structured compaction carry-forward via persisted thread synopsis
- sparse-context / RLM-style recursive inspection scaffold
- SQLite-backed sparse-context state persistence
- validation harness for the GPT-5.4 stack
- repo-local fork maintenance skill for future upstream sync work
- local pre-commit / pre-push secret-scan guardrails plus manual scan script

## Operational decisions

- keep the provider layer and GPT-5.4 layer on separate branches
- rebase the stack in order instead of merging maintenance branches together
- push rebased maintenance branches with `--force-with-lease`
- install local secret-scan hooks in every clone before commit/push activity

## Validation snapshot

- focused `codex-core` exact tests for sparse-context and deferred `tool_search`: passing
- `tools::handlers::tool_search` tests: passing
- `python scripts/agent_upgrade_check.py --format text`: passing

## Remaining follow-up

- wire the same maintenance protocol into the fork remote after the next upstream refresh
- build a more explicit benchmark harness for long-thread quality/cost comparisons
- keep reviewing upstream changes in `tools/spec.rs`, `js_repl`, and state persistence paths first
