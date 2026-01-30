# GitHub Issue #17407 — Update Draft

**For posting to**: https://github.com/anthropics/claude-code/issues/17407
**Date**: January 30, 2026
**Context**: Three-week investigation update; first substantive post since initial report

---

## Investigation Update: Root Cause Identified, Server-Side Mitigation Observed

Three weeks ago, I opened this issue after discovering that Claude Code silently fails to deliver file contents to the model — a bug I called "phantom reads." Since then, I've conducted a systematic investigation across 126+ controlled trials, 17 builds (2.1.3 through 2.1.22), and three weeks of comparative data. The investigation repository is public: [rcgray/claude-code-bug-phantom-reads-17407](https://github.com/rcgray/claude-code-bug-phantom-reads-17407)

Here's what we now know.

### The Root Cause

The phantom read mechanism is fully mapped:

1. The Claude Code harness decides — per session — whether to persist tool results to disk (saved as files in a `tool-results/` directory alongside the session `.jsonl`).
2. When persistence is active, file read results in the model's context are replaced with `<persisted-output>` markers directing the model to issue a follow-up Read.
3. The model ignores these markers and proceeds as if it received the actual file content.
4. The model then confabulates analysis for files it never read. It exhibits no awareness of the gap.

The session `.jsonl` always records the full file content — the persistence/substitution layer operates *between* the JSONL logger and the API call to the model. This is why the bug is invisible in exported session data: the log says the read succeeded, but the model never received the content.

The `<persisted-output>` mechanism is not new — it's the documented behavior for large tool results. What makes it a bug is step 3: the model's systematic failure to follow up on these markers. In ~85% of sessions where persistence occurs, the model ignores every marker. In ~10%, it detects and partially recovers. In ~5%, it exhausts the context window attempting recovery.

### The Critical Discovery: Server-Side Control

The investigation's most significant finding is that **phantom read behavior is governed by server-side state, not the client build version.**

Evidence: Build 2.1.22 showed **100% failure** (6/6 trials, all with persistence) on January 28, and **100% success** (6/6 trials, zero persistence) on January 29 — same build, same test files, same protocol, same machine. Build 2.1.6 (the oldest build we tested, from January 13) behaves identically to builds 2.1.20 and 2.1.22 when tested on the same day. The build version adds no predictive value; server-side state determines everything.

### Recent Mitigation (Last 24-48 Hours)

Between January 28 and January 29, we observed two changes that substantially reduce phantom read exposure:

1. **Reduced persistence frequency**: The harness appears to persist tool results less often. On Jan 28, persistence was active in 100% of sessions across all builds tested. On Jan 29, it dropped to 80-100% of direct-read sessions (build-dependent sampling, small N).

2. **Model behavioral shift**: The model began preferring to delegate file reads to sub-agents (via the Task tool), a strategy absent in all prior testing (28+ trials across Jan 27-28). Sub-agents operate in their own context windows, so their reads are not subject to the main session's persistence mechanism. This delegation appeared simultaneously across builds 2.1.6, 2.1.20, and 2.1.22 — confirming it's a server-side behavioral change (model weights or system prompt), not a client update.

Together, these changes mean phantom reads are **substantially less likely** than they were 48 hours ago. But they are **not eliminated**: persistence was still observed in 80-100% of sessions where the model read files directly (without delegation), and when persistence occurs, ~85% of sessions still result in phantom reads.

### The MCP Filesystem Workaround Still Works

The workaround documented in the repository — using the `@modelcontextprotocol/server-filesystem` MCP server to bypass the native Read tool — continues to provide 100% protection. It works because MCP tool results follow a different code path that is not subject to the persistence mechanism. If you are affected by phantom reads, this remains the most reliable mitigation regardless of server-side conditions.

### What This Means for Users

- **The situation is meaningfully better than it was 48 hours ago.** The combination of reduced persistence and model delegation means most sessions will avoid phantom reads under current conditions.
- **It is not fixed.** The root cause (model ignoring `<persisted-output>` markers) is unaddressed. The mitigation reduces exposure to the trigger condition, not the vulnerability itself.
- **We cannot predict permanence.** We observed a similar improvement on Jan 27 (0% persistence) that reverted on Jan 28 (100% persistence). Whether the current improvement holds is unknown.
- **Build version doesn't matter.** Don't upgrade or downgrade hoping to avoid phantom reads. The variable is server-side.

### For Maintainers

If any Claude Code maintainers are following this issue, the investigation repository contains detailed analysis that may be useful:

- **[Server-Side Variability Theory](https://github.com/rcgray/claude-code-bug-phantom-reads-17407/blob/main/docs/theories/Server-Side-Variability-Theory.md)** — The theoretical framework with all evidence
- **[Build Scan Discrepancy Analysis](https://github.com/rcgray/claude-code-bug-phantom-reads-17407/blob/main/docs/experiments/results/Build-Scan-Discrepancy-Analysis.md)** — The comprehensive 55+ trial analysis document
- **[Trial data](https://github.com/rcgray/claude-code-bug-phantom-reads-17407/tree/main/dev/misc)** — Raw session data (JSONL exports, preprocessed `trial_data.json` files) for independent verification

The key diagnostic: the presence of a `tool-results/` directory in the session subdirectory (alongside the `.jsonl` file) is a perfect indicator that persistence occurred. The `has_tool_results` field in our preprocessed data is a near-perfect outcome discriminator: `false` = 100% success (14/14 trials), `true` = 85% failure (17/20).

The root cause appears to be in the layer that reconstructs context after persisting tool results — specifically, the model receiving compact `<persisted-output>` markers instead of actual content, and then not following through on the "Use Read to view" instruction embedded in those markers. A possible fix path: either ensure the model reliably follows up on persisted-output markers, or avoid replacing tool results with markers in the first place when the result is a file read that the model will need to reference.

---

*This investigation was conducted entirely using Claude Code itself (with the MCP Filesystem workaround to prevent phantom reads during the investigation). The repository documents every prompt, every trial, and every analytical step.*
