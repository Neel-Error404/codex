param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$releaseBin = Join-Path $repoRoot "codex-rs\target\release\codex.exe"
$debugBin = Join-Path $repoRoot "codex-rs\target\debug\codex.exe"

if (Test-Path $releaseBin) {
    $bin = $releaseBin
} elseif (Test-Path $debugBin) {
    $bin = $debugBin
} else {
    Write-Error "No Codex binary found. Build one with `cargo build -p codex-cli --release` or `cargo build -p codex-cli`."
    exit 1
}

& $bin @Args
exit $LASTEXITCODE
