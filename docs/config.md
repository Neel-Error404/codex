# Configuration

For basic configuration instructions, see [this documentation](https://developers.openai.com/codex/config-basic).

For advanced configuration instructions, see [this documentation](https://developers.openai.com/codex/config-advanced).

For a full configuration reference, see [this documentation](https://developers.openai.com/codex/config-reference).

## Connecting to MCP servers

Codex can connect to MCP servers configured in `~/.codex/config.toml`. See the configuration reference for the latest MCP server options:

- https://developers.openai.com/codex/config-reference

## Apps (Connectors)

Use `$` in the composer to insert a ChatGPT connector; the popover lists accessible
apps. The `/apps` command lists available and installed apps. Connected apps appear first
and are labeled as connected; others are marked as can be installed.

## Notify

Codex can run a notification hook when the agent finishes a turn. See the configuration reference for the latest notification settings:

- https://developers.openai.com/codex/config-reference

When Codex knows which client started the turn, the legacy notify JSON payload also includes a top-level `client` field. The TUI reports `codex-tui`, and the app server reports the `clientInfo.name` value from `initialize`.

## JSON Schema

The generated JSON Schema for `config.toml` lives at `codex-rs/core/config.schema.json`.

## Custom model providers

Custom `model_providers` can now opt into either `wire_api = "responses"` or
`wire_api = "chat"` depending on which OpenAI-compatible endpoint the provider
supports.

If a provider does not expose a Codex-compatible `/models` catalog, you can pin
picker-visible model slugs directly in `config.toml`:

```toml
[model_providers.azure_foundry]
name = "Azure Foundry"
base_url = "https://example.services.ai.azure.com/models"
env_key = "AZURE_INFERENCE_CREDENTIAL"
wire_api = "chat"
models = ["kimi-k2", "deepseek-v3.2"]
```

The active provider for a session comes from `model_provider`, and Codex now
uses that effective provider when refreshing models and building the picker.

## SQLite State DB

Codex stores the SQLite-backed state DB under `sqlite_home` (config key) or the
`CODEX_SQLITE_HOME` environment variable. When unset, WorkspaceWrite sandbox
sessions default to a temp directory; other modes default to `CODEX_HOME`.

The SQLite state DB is also where this branch persists:

- structured thread synopses derived from compaction
- sparse-context payloads used by the `js_repl` recursive inspection scaffold

## Experimental Long-Thread Features

This branch adds several experimental long-thread features that work together
for tool-heavy and long-running sessions.

You can enable them either in `config.toml` or from the `/experimental` menu.
`sparse_context` remains disabled by default even when exposed in
`/experimental`.

```toml
[features]
js_repl = true
sparse_context = true
```

Notes:

- `js_repl` enables the persistent Node-backed JavaScript scratchpad.
- `sparse_context` biases the runtime toward inspect-on-demand behavior and
  uses `js_repl` as the recursive working memory layer when available.
- `js_repl_tools_only` can be enabled if you want direct model-visible tool
  access restricted to `js_repl` / `js_repl_reset`.
- deferred tool discovery is exposed via the built-in `tool_search` tool when
  deferred app tools or deferred dynamic tools are present; there is no
  separate user-facing config knob for this path.

For the implementation status and exact scope of these features, see
[`docs/plans/2026-03-17-gpt54-agent-upgrades.md`](./plans/2026-03-17-gpt54-agent-upgrades.md).

## Custom CA Certificates

Codex can trust a custom root CA bundle for outbound HTTPS and secure websocket
connections when enterprise proxies or gateways intercept TLS. This applies to
login flows and to Codex's other external connections, including Codex
components that build reqwest clients or secure websocket clients through the
shared `codex-client` CA-loading path and remote MCP connections that use it.

Set `CODEX_CA_CERTIFICATE` to the path of a PEM file containing one or more
certificate blocks to use a Codex-specific CA bundle. If
`CODEX_CA_CERTIFICATE` is unset, Codex falls back to `SSL_CERT_FILE`. If
neither variable is set, Codex uses the system root certificates.

`CODEX_CA_CERTIFICATE` takes precedence over `SSL_CERT_FILE`. Empty values are
treated as unset.

The PEM file may contain multiple certificates. Codex also tolerates OpenSSL
`TRUSTED CERTIFICATE` labels and ignores well-formed `X509 CRL` sections in the
same bundle. If the file is empty, unreadable, or malformed, the affected Codex
HTTP or secure websocket connection reports a user-facing error that points
back to these environment variables.

## Notices

Codex stores "do not show again" flags for some UI prompts under the `[notice]` table.

## Plan mode defaults

`plan_mode_reasoning_effort` lets you set a Plan-mode-specific default reasoning
effort override. When unset, Plan mode uses the built-in Plan preset default
(currently `medium`). When explicitly set (including `none`), it overrides the
Plan preset. The string value `none` means "no reasoning" (an explicit Plan
override), not "inherit the global default". There is currently no separate
config value for "follow the global default in Plan mode".

## Realtime start instructions

`experimental_realtime_start_instructions` lets you replace the built-in
developer message Codex inserts when realtime becomes active. It only affects
the realtime start message in prompt history and does not change websocket
backend prompt settings or the realtime end/inactive message.

Ctrl+C/Ctrl+D quitting uses a ~1 second double-press hint (`ctrl + c again to quit`).
