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

**Update (Jan 30, 2026)**: The investigation has reached a major milestone. Across 55+ controlled trials spanning builds 2.1.6 through 2.1.22, we have identified the **root cause mechanism** and discovered that **phantom read behavior is governed by server-side state, not client build version.** The same build can show 100% failure one day and 100% success the next. See the **[Server-Side Variability Theory](docs/theories/Server-Side-Variability-Theory.md)** for the complete findings.

Key discoveries from the Build Scan Discrepancy Investigation (Jan 28-30):

- **Root cause mapped**: The Claude Code harness persists tool results to disk and replaces them with `<persisted-output>` markers. The model ignores these markers and proceeds as if it read the files -- this is the phantom read.
- **Server-side control**: Whether persistence is enabled is controlled by Anthropic's API infrastructure, not the client build. Build 2.1.22 went from 100% failure (Jan 28) to 100% success (Jan 29) with no changes to the test environment.
- **Build version is irrelevant**: Build 2.1.6 (oldest tested) is behaviorally indistinguishable from builds 2.1.20 and 2.1.22 when tested on the same day.
- **Partial mitigation observed**: On Jan 29, two server-side changes appeared -- reduced persistence frequency and a new model tendency to delegate file reads to sub-agents. However, persistence was still observed in 80-100% of direct-read sessions, so phantom reads are **mitigated but not fixed.**
- **The MCP Filesystem workaround remains the only reliable mitigation** (see below).

The earlier **[Consolidated Theory](docs/theories/Consolidated-Theory.md)** introduced the X + Y threshold overflow model, which remains valid within a single session -- but the threshold T is now known to be externally variable (`T_effective(server_state)`).

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
7. **Controlled Experiments (Jan 26-27)**: Refined understanding with completed experiments 04A, 04D, 04K, 04L
8. **Build Scan & Root Cause (Jan 28-30)**: Scanned 16 builds (2.1.6-2.1.22); discovered same build reverses from 100% failure to 100% success overnight; traced root cause to server-controlled persistence mechanism; formalized Server-Side Variability Theory

### Theoretical Evolution: From "Danger Zone" to Server-Side Variability

The investigation initially converged on an X + Y interaction model (Jan 22-27):

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
interaction is NOT additive -- both X and Y must exceed some threshold simultaneously to trigger phantom
reads.

**Update (Jan 28-30): The Server-Side Variability Discovery**

The Build Scan Discrepancy Investigation revealed that the X+Y model's threshold T is not fixed -- it is controlled by Anthropic's server-side infrastructure and varies over time. The complete root cause chain:

1. The Claude Code harness decides (per-session, server-controlled) whether to persist tool results to disk
2. When persistence is active, file read results are saved to `tool-results/` files and replaced with `<persisted-output>` markers in the model's context
3. The model receives markers instead of file content and proceeds without following up
4. The model confabulates analysis for files it never actually read

Evidence: Build 2.1.22 showed 100% persistence/failure on Jan 28 and 0% persistence/100% success on Jan 29 -- same build, same files, same protocol. Build 2.1.6 (oldest tested) behaves identically to newer builds on the same day. The `has_tool_results` field in session data is a near-perfect outcome discriminator: `false` = 100% success (14/14 trials), `true` = 85% failure (17/20 trials, with 2 recoveries).

See the **[Server-Side Variability Theory](docs/theories/Server-Side-Variability-Theory.md)** and **[Build Scan Discrepancy Analysis](docs/experiments/results/Build-Scan-Discrepancy-Analysis.md)** for the full investigation.

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

### Open Questions

The investigation has answered its core research questions. The key remaining unknowns are:

- **What controls the server-side persistence decision?** We can observe the effects but not the cause. This is outside our observation boundary -- only Anthropic can answer this.
- **Is the Jan 29 mitigation permanent?** We have observed server-side improvement that may be intentional (targeted fix), incidental (side effect of other changes), or transient (like the Jan 27 improvement that reverted on Jan 28).
- **Can the model's recovery from `<persisted-output>` markers be made reliable?** Currently ~10% of persistence sessions show successful agent recovery. Understanding what enables recovery could lead to a model-level fix.

Previously planned experiments (04M, 04F, 04C, Easy/Medium/Hard scenarios) have been **superseded** by the Server-Side Variability findings -- their design assumptions (stable thresholds, deterministic input-output relationships) are invalidated by the discovery that server state varies the baseline from 0% to 100% failure.

See **[Research Questions](docs/core/Research-Questions.md)** for the complete catalog.

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

Phantom reads can be reproduced using [Experiment-Methodology-04](docs/experiments/methodologies/Experiment-Methodology-04.md), which triggers multi-file read operations in a controlled test repository. The key factors:

- **High pre-operation context consumption** (>50% of context window before triggering multi-file reads)
- **Multiple file reads during onboarding** (inflates baseline context)
- **Aggressive multi-file read operations** (triggers mid-session resets)

**Important caveat**: Reproduction success depends on **server-side conditions at the time of testing**. Under conditions where the harness persistence mechanism is active (observed in 80-100% of direct-read sessions as of Jan 29, 2026), the protocol reliably triggers phantom reads. Under conditions where persistence is disabled (as observed on Jan 27 and partially on Jan 29), the same protocol will succeed. You cannot control this variable -- check for the presence of a `tool-results/` directory in the session data to determine whether persistence was active in your trial.

See the **[Build Scan Discrepancy Analysis](docs/experiments/results/Build-Scan-Discrepancy-Analysis.md)** for the complete analysis of how server-side variability affects reproduction.

## Contributing

If you've experienced phantom reads:

1. Note your Claude Code version (`claude --version`)
2. Export your session logs if possible
3. Document which files were affected
4. Open an issue or contribute to the investigation

## References

- **GitHub Issue**: [anthropics/claude-code#17407](https://github.com/anthropics/claude-code/issues/17407)
- **Server-Side Variability Theory**: [docs/theories/Server-Side-Variability-Theory.md](docs/theories/Server-Side-Variability-Theory.md) — Latest theoretical framework explaining phantom read behavior as server-controlled
- **Build Scan Discrepancy Analysis**: [docs/experiments/results/Build-Scan-Discrepancy-Analysis.md](docs/experiments/results/Build-Scan-Discrepancy-Analysis.md) — Comprehensive 55+ trial analysis (the core investigation document)
- **Consolidated Theory**: [docs/theories/Consolidated-Theory.md](docs/theories/Consolidated-Theory.md) — Earlier unified framework (X + Y model), still valid within sessions
- **Timeline**: [docs/core/Timeline.md](docs/core/Timeline.md) — Concise chronological record of experiments and findings
- **Investigation Journal**: [docs/core/Investigation-Journal.md](docs/core/Investigation-Journal.md) — Detailed narrative discovery log
- **Research Questions**: [docs/core/Research-Questions.md](docs/core/Research-Questions.md) — Catalog of known and unknown information
- **Experiment Methodology**: [docs/experiments/methodologies/Experiment-Methodology-04.md](docs/experiments/methodologies/Experiment-Methodology-04.md)
- **Workaround Guide**: [WORKAROUND.md](WORKAROUND.md)
- **Prompt Logs**: [dev/prompts/archive](dev/prompts/archive/) - A record of every prompt used in this project

## License

MIT
