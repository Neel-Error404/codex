# GPT-5.4 Agent Upgrades Status

This note tracks the Codex work completed in this branch to improve tool-heavy,
long-running sessions. It ties together compaction, deferred tool discovery,
and the current sparse-context / RLM-style recursive inspection layer.

## Goal

Reduce prompt bloat, keep long sessions accurate for longer, and make the agent
inspect context on demand instead of front-loading full schemas or large source
trees into every turn.

## Implemented

### 1. Compaction now produces structured carry-forward state

Compaction already existed. This branch extends it so compacted summaries can be
preserved as a structured `ThreadSynopsis` and reinjected into later turns.

What changed:

- compacted summaries are normalized into `core_facts`, `pending_steps`, and
  `constraints`
- the latest structured synopsis is stored in the SQLite state DB
- initial turn context injects the persisted synopsis inside
  `<thread_synopsis>...</thread_synopsis>`
- sparse-context flows use the latest synopsis as the canonical seed and can
  override stale scratchpad facts with newer compaction output

Key files:

- `codex-rs/core/src/compact.rs`
- `codex-rs/core/src/codex.rs`
- `codex-rs/core/src/state_db.rs`
- `codex-rs/state/src/runtime/threads.rs`
- `codex-rs/state/migrations/0020_thread_synopsis.sql`

Impact:

- history compaction no longer only shrinks prompt text; it now leaves behind a
  structured memory anchor the runtime can reuse
- later turns get cleaner carry-forward context without replaying full history

### 2. Deferred tool discovery via `tool_search`

This branch adds a built-in `tool_search` tool that returns deferred app and
dynamic tool definitions in a grouped, model-friendly shape.

What changed:

- deferred dynamic tools with `defer_loading = true` are indexed for search
- deferred connector/app tools are grouped by namespace
- matching is done over names, descriptions, connector metadata, and input
  parameter keys
- result payloads preserve `defer_loading` so the model can inspect lightweight
  descriptors before pulling heavier schemas
- tool registration is automatic when deferred app tools or deferred dynamic
  tools are present

Key files:

- `codex-rs/core/src/tools/handlers/tool_search.rs`
- `codex-rs/core/src/tools/handlers/tool_search_tests.rs`
- `codex-rs/core/src/tools/spec.rs`
- `codex-rs/core/src/tools/spec_tests.rs`

Impact:

- tool-heavy sessions stop paying the full schema cost up front
- the model can discover only the relevant tool namespace or function for the
  current sub-task

### 3. Sparse-context / RLM-style recursive inspection scaffold

This branch adds a real host-assisted recursive inspection workflow. The model
is instructed to inspect on demand, use `js_repl` as a persistent scratchpad,
and keep only bounded summaries in active state.

What changed:

- new `sparse_context` feature flag biases turn setup toward inspect-on-demand
  behavior
- when `js_repl` is enabled, sparse-context instructions explicitly steer the
  model to use `js_repl`, `tool_search`, `list_dir`, `grep_files`, and
  `read_file` instead of loading large context eagerly
- `js_repl` scratchpad state is pre-seeded with:
  - `thread_synopsis`
  - `facts`
  - `file_summaries`
  - `open_questions`
- `js_repl` syncs sparse context bidirectionally with the host
- sparse-context state survives kernel resets and is restored from SQLite-backed
  thread state when needed
- file summaries are bounded by entry count, per-path bytes, per-summary bytes,
  and total bytes

Key files:

- `codex-rs/core/src/codex.rs`
- `codex-rs/core/src/tools/js_repl/mod.rs`
- `codex-rs/core/src/tools/js_repl/kernel.js`
- `codex-rs/core/src/tools/js_repl/mod_tests.rs`
- `codex-rs/core/src/state_db.rs`
- `codex-rs/state/src/runtime/threads.rs`
- `codex-rs/state/migrations/0021_thread_sparse_context.sql`

Impact:

- the runtime now supports recursive, demand-driven inspection across longer
  tasks without forcing full codebase/history injection
- useful intermediate state can persist across multiple REPL calls and kernel
  restarts

## Hardening Added

The sparse-context layer now includes:

- fallback from corrupt persisted sparse-context blobs to synopsis-only seeding
- canonical merge rules that prefer the latest thread synopsis over stale
  scratchpad facts
- truncation safeguards for file summary state
- telemetry for:
  - sparse-context seed source
  - persisted blob parse failures
  - sparse-context sync status
  - file-summary truncation reasons
  - persisted sparse-context payload size

## What This Is, And What It Is Not

This branch **does implement** a real recursive-inspection scaffold:

- inspect on demand instead of loading everything up front
- persistent scratchpad variables
- sparse state synchronization between host and REPL
- state restoration across resets and later turns

This branch **does not yet implement** the full research system described in
the RLM paper/repo:

- no separate learned controller or RLM-specific training loop
- no paper-accurate multi-step program execution policy
- no benchmark harness yet that proves parity with the published system

The current implementation is best described as:

> an RLM-style runtime scaffold built from existing Codex tools, not a full
> reproduction of the research stack

## Current Readiness

Ready in this branch:

- structured compaction carry-forward
- deferred tool discovery for app and dynamic tools
- sparse-context turn instructions
- persistent `js_repl` scratchpad state
- SQLite-backed synopsis and sparse-context persistence
- sparse-context hardening and telemetry
- repeatable validation harness via `python scripts/agent_upgrade_check.py` or
  `just agent-upgrades-check`

Still recommended before calling the work complete:

- extend the validation harness into a true benchmark/eval harness for
  long-thread and tool-heavy tasks
- document exact user-facing enablement once `sparse_context` is promoted beyond
  under-development status
- decide whether `sparse_context` remains instruction-only or grows additional
  targeted file-slice helpers

## Suggested Next Step

Build an internal evaluation harness that compares:

- baseline compaction-only behavior
- compaction + tool search
- compaction + tool search + sparse context

Measure at minimum:

- input token count
- average time to first tool call
- total time to task completion
- number of full-file reads vs targeted inspections
- recovery quality after kernel reset or long-session drift
