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

### Latest Progress: 22-Trial Analysis

We conducted 22 controlled trials and discovered that **reset timing pattern** is the dominant predictor of phantom reads—achieving **100% prediction accuracy** on our dataset.

| Pattern | Description | Outcome |
|---------|-------------|---------|
| EARLY + LATE | First reset <50%, last >95%, no mid-session | **100% SUCCESS** |
| SINGLE_LATE | Single reset >95% | **100% SUCCESS** |
| MID-SESSION | Any reset between 50-90% of session | **100% FAILURE** |

The critical finding: **mid-session resets (50-90% through the session) predict phantom reads with near-perfect accuracy**, regardless of reset count or starting headroom.

### Key Findings

- **Reset timing is the dominant factor**: When resets occur matters more than how many occur or how much context is consumed
- **The "Clean Gap" pattern**: Successful sessions have early resets (before main work) and late resets (after work completes), with no resets during active file reading
- **No fixed token threshold**: Resets occur at widely varying cumulative token counts (82K-383K), ruling out a simple threshold model
- **Accumulation rate matters**: Rapid batch reads without processing pauses appear to trigger mid-session resets more readily
- **Session files don't capture the bug**: The `.jsonl` log records actual content, but phantom read markers appear after logging
- **MCP bypass works**: The Filesystem MCP server provides 100% success rate in testing

### Current Working Theory

The Read tool records actual content to the session file, but a separate context management system decides what actually reaches the model. **The critical factor is WHEN context resets occur during a session**:

- **Resets during active file processing (50-90% of session)** → Content cleared before the model processes it → **Phantom reads**
- **Resets at natural breakpoints (early setup, late completion)** → Content already processed → **Success**

The "Clean Gap" pattern describes successful sessions: an early reset clears initialization overhead, then main file reading proceeds uninterrupted, with any final reset occurring only after operations complete.

### Theories Summary

| Theory | Status | Notes |
|--------|--------|-------|
| **Reset Timing Theory** | ✅ CONFIRMED | 100% prediction accuracy on 22 trials |
| **Reset Count Theory** | ⚠️ PARTIAL | Correlates but not deterministic |
| **Headroom Theory** | ⚠️ WEAKENED | Necessary but not sufficient |
| **Dynamic Context Pressure** | 🔬 HYPOTHESIS | Rate of accumulation may trigger resets |

See [docs/core/WSD-Dev-02-Analysis-3.md](docs/core/WSD-Dev-02-Analysis-3.md) for the full token-based analysis.

## Original Experiment

The bug was discovered during development work in early January 2026. Systematic testing across Claude Code versions identified version boundaries and characterized the two error mechanisms.

The original experiment methodology is documented in [docs/core/Experiment-Methodology-01.md](docs/core/Experiment-Methodology-01.md). Key findings from the original investigation:

- **Trigger condition**: Multi-file read operations, especially via custom commands like `/refine-plan`
- **Detection method**: Self-report methodology—prompting agents to introspect on their read history
- **Version boundary**: The transition from Era 1 to Era 2 mechanisms occurs at the 2.0.59/2.0.60 boundary

The original conclusion that versions 2.0.58 and earlier were unaffected has been revised—subsequent testing confirmed phantom reads can occur in those versions via the Era 1 mechanism.

For testing specific Claude Code versions, use the `cc_version.py` script (`src/cc_version.py`) to manage auto-update settings and version installation. Run `./src/cc_version.py --status` to check your current configuration, or see [docs/features/cc-version-script/CC-Version-Script-Overview.md](docs/features/cc-version-script/CC-Version-Script-Overview.md) for complete documentation.

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
