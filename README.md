# Claude Code Phantom Reads Investigation

This repository documents and provides tools to reproduce the **Phantom Reads** bug in Claude Code ([Issue #17407](https://github.com/anthropics/claude-code/issues/17407)).

## What Are Phantom Reads?

The Phantom Reads bug causes Claude Code to believe it has successfully read file contents when it has not. The AI proceeds confidently with its task, operating on incomplete or non-existent information—often producing plausible-sounding but incorrect outputs.

This bug is particularly insidious because:

- **Silent Failure**: Claude exhibits no awareness that it missed file content and moves forward with regular confidence
- **Intermittent Occurrence**: The bug doesn't manifest consistently, making it easy to dismiss as occasional model error
- **Masked by Capability**: Claude's strong reasoning allows it to "gap fill" plausibly, producing outputs that appear reasonable but are based on assumptions rather than actual file content
- **UI Shows Success**: The Claude Code interface displays successful reads even when phantom reads occur

## Purpose of This Repository

This repository serves three purposes:

1. **Documentation**: Explain the Phantom Reads phenomenon for affected users
2. **Reproduction**: Provide an environment to trigger and observe phantom reads
3. **Analysis**: Build tools to programmatically detect phantom reads in session logs

## Temporary Workaround Available

A working mitigation exists using the official Anthropic Filesystem MCP server. This workaround bypasses Claude Code's native `Read` tool entirely, preventing phantom reads through an architecturally different code path.

**See [WORKAROUND.md](WORKAROUND.md) for complete setup instructions.**

The workaround:
- Uses the `@modelcontextprotocol/server-filesystem` package
- Disables the native `Read` tool via permission settings
- Forces all file reads through the MCP server, which reads files reliably

Note: Project-level configuration only protects the main session. Slash commands and sub-agents may still use the native Read tool. See the workaround documentation for details on scope limitations.



## Investigation Status

The investigation is ongoing. For a unified explanation of our findings, see the **[Consolidated Theory](docs/theories/Consolidated-Theory.md)**, which introduces the **X + Y threshold overflow model**: phantom reads occur when pre-operation context (X) plus operation files (Y) exceeds the context threshold (T). This model explains how our various theories—reset timing, headroom, reset count—fit together as parts of a causal chain.

Detailed experimental history is documented in the **[Investigation Journal](docs/core/Investigation-Journal.md)**, with a summary available in the **[Project Timeline](docs/core/Timeline.md)**.

## The Journey of Discovery

The investigation has evolved through several phases:

1. **Initial Discovery (Jan 9)**: Bug first noticed when an agent gave nonsensical WPD reviews
2. **Version Boundary Testing (Jan 9-10)**: Incorrectly concluded pre-2.0.59 was safe
3. **Revised Understanding (Jan 12-13)**: Discovered both eras have phantom reads, just different mechanisms
4. **MCP Workaround (Jan 13)**: Validated that MCP Filesystem bypasses the bug entirely (100% success)
5. **Theory Development (Jan 14-21)**: Developed Reset Timing Theory, Headroom Theory, then the X+Y Model
6. **Methodology Refinement (Jan 22-24)**: Built controlled experiments, discovered hoisting limits and
methodology issues
7. **Current State (Jan 26-27)**: Refined understanding with completed experiments 04A, 04D, 04K, 04L

### Current Theoretical Understanding: The "Danger Zone" Model

The investigation has converged on an X + Y interaction model:

- X = Pre-operation context consumption (baseline + hoisted content)
- Y = Operation context requirement (files read by agent during task)
- T = Context window threshold

Key Finding: Simple X + Y > T is NOT the trigger. The interaction is more complex:

| Condition          | X    | Y   | X+Y  | Outcome             |
| ------------------ | ---- | --- | ---- | ------------------- |
| High X only        | 150K | 6K  | 156K | SUCCESS (04L)       |
| High Y only        | ≈0   | 57K | ~57K | SUCCESS (04A)       |
| Both moderate-high | 73K+ | 57K | 130K | FAILURE (Method-04) |
| High X, moderate Y | 120K | 42K | 162K | SUCCESS (Method-03) |

Critical Insight: The lower total (130K) fails while the higher total (162K) succeeds. This proves the
interaction is NOT additive—both X and Y must exceed some threshold simultaneously to trigger phantom
reads.

### What's Been Confirmed

1. **Hoisting is safe** - Content loaded via @ notation becomes <system-reminder> blocks (part of system
message, immune to context management)
2. **MCP Filesystem works** - 100% success rate, bypasses the bug entirely
3. **1M model avoids the issue** - Same protocols that fail on 200K model succeed on 1M model (but this is
out of scope)
4. **Reset timing correlates but isn't causal** - The same reset patterns produce opposite outcomes depending
on model capacity
5. **T (context window) matters** - The 200K model has limitations the 1M model doesn't share

### Confirmed Mitigations

1. MCP Filesystem - Replace native Read with MCP tools (current workaround in this project)
2. Hoisting - Pre-load files via @ notation to move them from Y to X
3. 1M Model - Use larger context window (confirmed to work but out of scope)

### Open Questions and Next Steps

Key Remaining Questions:
- What is the exact X threshold above which Y=57K becomes dangerous? (somewhere between 0 and 73K)
- Is the trigger file count, token count, or both? (04F planned)
- What internally triggers a context reset? (still unknown)

Next Experiments:
- 04M: X Boundary Exploration - test intermediate X values (e.g., ~50K) with Y=57K
- 04B/04C/04F: File count vs token count testing (requires surgical edits to remove cross-references)
- 04G: Sequential vs parallel read patterns

### Research Questions Catalog Status

See **[Research Questions](docs/core/Research-Questions.md)** document for details.

| Category                | Total | Open | Answered | Hypothesis    |
| ----------------------- | ----- | ---- | -------- | ------------- |
| A: Core Mechanism       | 5     | 2    | 1        | 2             |
| B: Threshold Behavior   | 8     | 3    | 4        | 1             |
| C: Hoisting Behavior    | 4     | 0    | 3        | 1             |
| D: Reset Timing         | 3     | 1    | 0        | 2             |
| E: Read Patterns        | 6     | 3    | 0        | 3             |
| F: Measurement          | 5     | 4    | 1        | 0             |
| G: Cross-Version/Model  | 5     | 3    | 1        | 1             |
| H: Persisted Output     | 3     | 3    | 0        | 0             |
| I: Discovered Behaviors | 8     | -    | -        | 7 (confirmed) |
| TOTAL                   | 47    | 19   | 10       | 10            |

## Original Experiment

The bug was discovered during development work in early January 2026. Systematic testing across Claude Code versions identified version boundaries and characterized the two error mechanisms.

The original experiment methodology is documented in [docs/experiments/methodologies/Experiment-Methodology-01.md](docs/experiments/methodologies/Experiment-Methodology-01.md). Key findings from the original investigation:

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

We have achieved the first successful phantom read reproduction in a controlled scenario. The key factors:

- **High pre-operation context consumption** (>50% of context window before triggering multi-file reads)
- **Multiple file reads during onboarding** (inflates baseline context)
- **Aggressive multi-file read operations** (triggers mid-session resets)

A reliable, user-friendly reproduction protocol is in development. Current methodology documented in [docs/experiments/methodologies/Experiment-Methodology-04.md](docs/experiments/methodologies/Experiment-Methodology-04.md).

## Contributing

If you've experienced phantom reads:

1. Note your Claude Code version (`claude --version`)
2. Export your session logs if possible
3. Document which files were affected
4. Open an issue or contribute to the investigation

## References

- **GitHub Issue**: [anthropics/claude-code#17407](https://github.com/anthropics/claude-code/issues/17407)
- **Consolidated Theory**: [docs/theories/Consolidated-Theory.md](docs/theories/Consolidated-Theory.md) — Unified theoretical framework (X + Y model)
- **Timeline**: [docs/core/Timeline.md](docs/core/Timeline.md) — Concise chronological record of experiments and findings
- **Investigation Journal**: [docs/core/Investigation-Journal.md](docs/core/Investigation-Journal.md) — Detailed narrative discovery log
- **Research Questions**: [docs/core/Research-Questions.md](docs/core/Research-Questions.md) — Catalog of known and unknown information
- **Experiment Methodology**: [docs/experiments/methodologies/Experiment-Methodology-04.md](docs/experiments/methodologies/Experiment-Methodology-04.md)
- **Workaround Guide**: [WORKAROUND.md](WORKAROUND.md)
- **Prompt Logs**: [dev/prompts/archive](dev/prompts/archive/) - A record of every prompt used in this project

## License

MIT
