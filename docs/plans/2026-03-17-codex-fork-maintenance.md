# Codex Fork Maintenance Protocol

This fork now carries a two-layer stack on top of upstream `openai/codex`:

- `feat/azure-provider-retries-realigned`
- `feat/gpt54-agent-upgrades`

The goal of this note is to keep future upstream updates safe, repeatable, and
free of accidental credential leaks.

## Credential Safety

Rules:

- never commit real API keys, Azure credentials, cert bundles, or private keys
- keep runtime secrets in user-local config and environment variables
- treat `.env*`, local auth files, and certificate material as workstation-only
- install the local hooks in every fresh clone:

```shell
python scripts/install_git_guardrails.py
```

Manual scans:

```shell
python scripts/git_guardrails.py --scope staged
python scripts/git_guardrails.py --scope push
```

The hooks block commits and pushes when the scan finds:

- likely token formats such as OpenAI, GitHub, Slack, or AWS keys
- private key blocks
- tracked files with suspicious names like `.env` or `id_rsa`
- tracked certificate/key suffixes outside normal fixture paths

## Upstream Update Protocol

### Branch structure

- `main`: local mirror of `upstream/main`
- `feat/azure-provider-retries-realigned`: provider compatibility base
- `feat/gpt54-agent-upgrades`: tool search + compaction + sparse context

### Standard update flow

1. Fetch both remotes:

   ```shell
   git fetch upstream origin --prune
   ```

2. Refresh local `main` from upstream:

   ```shell
   git checkout main
   git pull --ff-only upstream main
   ```

   Do not do this inside a dirty worktree. Prefer a fresh maintenance worktree.

3. Rebase the Azure/provider layer:

   ```shell
   git checkout feat/azure-provider-retries-realigned
   git rebase main
   ```

4. Run the provider validation set.

5. Rebase the GPT-5.4 layer:

   ```shell
   git checkout feat/gpt54-agent-upgrades
   git rebase feat/azure-provider-retries-realigned
   ```

6. Run:

   ```shell
   just agent-upgrades-check
   ```

7. Update the founder log with:

- new upstream base SHA
- layer commit SHAs
- validation status
- unresolved conflicts or follow-up work

8. Push rebased branches safely:

   ```shell
   git push --force-with-lease origin feat/azure-provider-retries-realigned
   git push --force-with-lease origin feat/gpt54-agent-upgrades
   ```

## When To Rebase Vs Cherry-Pick

- Use `rebase` when you are moving the whole maintained stack forward on top of upstream.
- Use `cherry-pick` when upstream lands an isolated fix that should be applied to one custom branch before the rest of the stack is updated.
- Avoid maintenance-branch merge commits. They make later upstream conflict review materially harder.

## High-Risk Overlap Areas

Review these manually whenever upstream moves:

- `codex-rs/core/src/tools/spec.rs`
- `codex-rs/core/src/tools/js_repl/mod.rs`
- `codex-rs/core/src/codex.rs`
- `codex-rs/core/src/state_db.rs`
- `codex-rs/state/src/runtime/threads.rs`
- provider transport and chat-completions serialization code

## Local Skill

This repo now includes:

- `.codex/skills/maintaining-stacked-codex-fork/SKILL.md`

Use it whenever updating the fork against upstream or preparing rebased pushes.
