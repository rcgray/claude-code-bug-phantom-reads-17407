# Claude Code Phantom Reads Investigation

This repository documents and provides tools to reproduce the **Phantom Reads** bug in Claude Code ([Issue #17407](https://github.com/anthropics/claude-code/issues/17407)).

## What Are Phantom Reads?

The Phantom Reads bug causes Claude Code to believe it has successfully read file contents when it has not. The AI proceeds confidently with its task, operating on incomplete or non-existent information—often producing plausible-sounding but incorrect outputs.

This bug is particularly insidious because:

- **Silent Failure**: Claude exhibits no awareness that it missed file content and moves forward with regular confidence
- **Intermittent Occurrence**: The bug doesn't manifest consistently, making it easy to dismiss as occasional model error
- **Masked by Capability**: Claude's strong reasoning allows it to "gap fill" plausibly, producing outputs that appear reasonable but are based on assumptions rather than actual file content
- **UI Shows Success**: The Claude Code interface displays successful reads even when phantom reads occur

### Two Distinct Mechanisms

The bug manifests differently depending on the Claude Code version:

| Era   | Versions         | Error Mechanism                                                    |
| ----- | ---------------- | ------------------------------------------------------------------ |
| Era 1 | 2.0.54 - 2.0.59  | `[Old tool result content cleared]` - Content cleared from context |
| Era 2 | 2.0.60 - present | `<persisted-output>` markers returned instead of content           |

**Important**: There is no known "safe" version. All tested versions from 2.0.54 through 2.1.6 have exhibited phantom read behavior under certain conditions.

## Workaround Available

A working mitigation exists using the official Anthropic Filesystem MCP server. This workaround bypasses Claude Code's native `Read` tool entirely, preventing phantom reads through an architecturally different code path.

**See [WORKAROUND.md](WORKAROUND.md) for complete setup instructions.**

The workaround:
- Uses the `@modelcontextprotocol/server-filesystem` package
- Disables the native `Read` tool via permission settings
- Forces all file reads through the MCP server, which reads files reliably

Note: Project-level configuration only protects the main session. Slash commands and sub-agents may still use the native Read tool. See the workaround documentation for details on scope limitations.

## Purpose of This Repository

This repository serves three purposes:

1. **Documentation**: Explain the Phantom Reads phenomenon for affected users
2. **Reproduction**: Provide an environment to trigger and observe phantom reads
3. **Analysis**: Build tools to programmatically detect phantom reads in session logs


## Investigation Status

The investigation is ongoing and documented in [docs/core/Investigation-Journal.md](docs/core/Investigation-Journal.md).

### Key Findings

- **Context resets correlate with phantom reads**: The `cache_read_input_tokens` field in session data shows context resets that predict phantom read risk
- **Session files don't capture the bug**: The `.jsonl` session log records actual file content, but the model receives phantom read markers—the transformation happens after logging
- **Grep appears more reliable**: Agents report that `grep` results succeed when `Read` operations fail
- **CLAUDE.md warnings are ineffective**: Agents ignore warnings about phantom reads because they genuinely believe they read the files
- **MCP bypass works**: The Filesystem MCP server provides 100% success rate in testing

### Current Working Theory

The Read tool records actual content to the session file, but a separate context management system decides what actually reaches the model. When context grows too large, older tool results are cleared or summarized. The session file doesn't capture this transformation because it logs tool execution, not model context.

## Original Experiment

The bug was discovered during development work in early January 2026. Systematic testing across Claude Code versions identified version boundaries and characterized the two error mechanisms.

The original experiment methodology is documented in [docs/core/Experiment-Methodology-01.md](docs/core/Experiment-Methodology-01.md). Key findings from the original investigation:

- **Trigger condition**: Multi-file read operations, especially via custom commands like `/refine-plan`
- **Detection method**: Self-report methodology—prompting agents to introspect on their read history
- **Version boundary**: The transition from Era 1 to Era 2 mechanisms occurs at the 2.0.59/2.0.60 boundary

The original conclusion that versions 2.0.58 and earlier were unaffected has been revised—subsequent testing confirmed phantom reads can occur in those versions via the Era 1 mechanism.

## Symptoms You May Have Noticed

If you've experienced any of these, phantom reads may be the cause:

- Claude produces analysis that sounds plausible but doesn't match file contents
- Claude claims to have "thoroughly reviewed" documents it clearly didn't understand
- Multi-file operations produce inconsistent quality across files
- Work quality seems to vary randomly between sessions
- Claude seems "dumber" than expected despite using a capable model

## How to Reproduce

Reliable repro case in progress

## Contributing

If you've experienced phantom reads:

1. Note your Claude Code version (`claude --version`)
2. Export your session logs if possible
3. Document which files were affected
4. Open an issue or contribute to the investigation

## References

- **GitHub Issue**: [anthropics/claude-code#17407](https://github.com/anthropics/claude-code/issues/17407)
- **Investigation Journal**: [docs/core/Investigation-Journal.md](docs/core/Investigation-Journal.md)
- **Experiment Methodology**: [docs/core/Experiment-Methodology-01.md](docs/core/Experiment-Methodology-01.md)
- **Workaround Guide**: [WORKAROUND.md](WORKAROUND.md)

## License

MIT
