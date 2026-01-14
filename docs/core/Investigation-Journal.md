# Investigation Journal

This document tracks ongoing discoveries, experiments, and findings related to the Phantom Reads bug investigation. Entries are chronological, with the most recent at the bottom.

For the formal experiment methodology and protocol, see [Experiment-Methodology-01.md](Experiment-Methodology-01.md). This journal captures the raw investigation process, including discoveries that may update or refine our understanding documented elsewhere.

---

## 2026-01-09: Initial Discovery

**Event**: Issue first encountered in Claude Code version `2.1.3`.

A User Agent provided a particularly nonsensical review of a Work Plan Document (WPD) when given the `/refine-plan` command. The response contained plausible-sounding analysis that bore no relationship to the actual document contents, suggesting the agent was operating on incomplete or non-existent information while believing it had read the file.

Intermittent recurrence and agent probing triggered the initial investigation into whether this was an isolated incident or a systematic issue.

---

## 2026-01-09: Original Investigation

**Event**: Manual testing across Claude Code versions 2.0.54 through 2.1.2.

**Methodology**: Self-report methodology - trigger multi-file reads via `/wsd:init --custom` followed by `/refine-plan`, then prompt the agent to report whether phantom reads occurred.

**Initial Findings** (later refined):
- Versions 2.0.54, 2.0.56, 2.0.58: 0 failures across 12 trials
- Version 2.0.59: First failures observed (2/4 trials)
- Versions 2.0.60+: Consistent failures observed

**Conclusion at Time**: Regression introduced in version 2.0.59 (released 2025-11-29).

---

## 2026-01-10: Public Disclosure

**Event**: GitHub Issue #17407 opened, report published to X (Twitter).

Issue URL: https://github.com/anthropics/claude-code/issues/17407

The report documented the investigation findings and identified the 2.0.58/2.0.59 boundary as the regression point.

---

## 2026-01-12: Example Repository Started

**Event**: This repository created to investigate the issue, construct a reproducible demonstration of the bug, and explore temporary workarounds.

Goals:
1. Document the phenomenon for other users
2. Provide reproduction environment
3. Build analysis tools for programmatic detection

---

## 2026-01-12-13: Sample Collection and Revised Understanding

**Event**: Generating examples of successful and failing cases across builds to create samples for analysis script development.

**Sample Collection**: Located at `dev/misc/`
- `2.0.58-bad/` - Failure case (unexpected - see findings below)
- `2.0.58-good/` - Success case
- `2.0.58-init-only/` - Control case (init only, no refine-plan)
- `2.0.59-bad/` - Failure case (no success obtained despite many trials)
- `2.0.60-bad/` - Failure case
- `2.0.60-good/` - Success case
- `2.1.3-bad/` - Failure case (no success obtained despite many trials)
- `2.1.6-bad/` - Failure case
- `2.1.6-good/` - Success case

### Critical Finding: Two Distinct Error Types

Upon closer examination of User Agent responses across builds, **two distinct phantom read mechanisms** were identified:

#### Era 1: `[Old tool result content cleared]` (2.0.?? through 2.0.59)

In earlier builds, when phantom reads occur, User Agents report seeing messages like:
```
[Old tool result content cleared]
```

This indicates that the Read tool result was cleared from context (possibly due to context window management) before the agent could process it. The agent proceeds without the content, operating on assumptions.

#### Era 2: `<persisted-output>` (2.0.60 through present)

Starting with build 2.0.60, the error mechanism changed. User Agents now report:
```
<persisted-output>Tool result saved to: /path/to/file.txt

Use Read to view</persisted-output>
```

This indicates the tool result was persisted to disk due to size, but the agent failed to follow up with a Read call to retrieve it.

### Revised Build Transition Understanding

| Era | Versions        | Error Mechanism                     | Notes                                                     |
| --- | --------------- | ----------------------------------- | --------------------------------------------------------- |
| 1   | 2.0.?? - 2.0.59 | `[Old tool result content cleared]` | Original investigation may have conflated this with Era 2 |
| 2   | 2.0.60 - 2.1.6+ | `<persisted-output>`                | Current era, persists in latest builds                    |

**Important**: There is NO 100% "safe" build discovered. Even 2.0.58 can fail with the Era 1 mechanism, though possibly at lower frequency.

### Trigger Conditions Refined

**Does NOT trigger reliably**:
- `/wsd:init --custom` alone - files read via `/wsd:boot` sub-command appear to be consistently received inline.

**Does trigger**:
- `/refine-plan` command execution
- Multi-file read operations in general

### Mitigation Observation

User Agents report that using `grep` helps mitigate phantom reads. From one agent who experienced phantom reads but still produced reasonable output:

> Despite not following the persisted-output instructions, my analysis wasn't completely blind because:
> 1. Some files DID return actual content directly (e.g., pre_staging.py returned full 747 lines, required_directories ticket returned full content)
> 2. I called Read on the target WPD a second time near the end of my investigation, and that call returned the full content (lines 1-390)
> 3. My Grep calls returned actual content snippets

This suggests:
- Phantom reads are intermittent within a session (some reads succeed, others fail)
- Grep results appear to be more reliable than Read results
- Re-reading a file later in the session may succeed

### Builds with No Success Obtained

Despite multiple trials:
- **2.0.59**: All trials failed (no `2.0.59-good/` sample)
- **2.1.3**: All trials failed (no `2.1.3-good/` sample)

This may indicate these versions have particularly high failure rates, or it may be sampling variance.

---

## 2026-01-13: CLAUDE.md Warning Test and Expanded Trigger Conditions

**Event**: Tested CLAUDE.md-based warning and discovered expanded trigger conditions.

### CLAUDE.md Warning Ineffective

Added a prominent warning to CLAUDE.md explaining the phantom reads issue, what to look for (`<persisted-output>` markers), and how to self-check. Result: **completely ineffective**. Agents ignore the warning entirely and proceed with phantom reads as before.

This confirms that CLAUDE.md-based mitigations are insufficient for this class of bug—the agent genuinely believes it read the file and has no reason to consult warnings about reading failures.

### Expanded Trigger Conditions

**Critical finding**: Phantom reads can occur during `/wsd:onboard` file reads, not just during `/refine-plan`.

In a test session:
- The `/refine-plan` command file reads all succeeded
- The EARLIER onboarding file reads (from `/wsd:onboard`) were phantom reads
- When the agent looked back at onboarding context, it discovered it had never actually read those files

This expands our understanding: phantom reads are NOT specific to `/refine-plan`. They can occur in ANY multi-file read operation, including sub-agent file reads.

### UI Shows Misleading Success

The Claude Code UI displayed successful reads that were actually phantom reads:

```
⏺ Read(docs/read-only/standards/Data-Structure-Documentation-Standards.md)
  ⎿  Read 642 lines

⏺ Read(docs/read-only/standards/Environment-and-Config-Variable-Standards.md)
  ⎿  Read 374 lines

[... 5 more files shown as successfully read ...]
```

**None of these files were actually read.** The UI reported success, but the agent received `<persisted-output>` markers for all of them. This makes the bug even more insidious—users cannot detect phantom reads from the UI.

### Agent Indifference

When confronted about phantom reads, the agent expressed indifference:

> "I didn't read the files, but do you just want to move forward anyway since my analysis is sound?"

This demonstrates that even when agents become AWARE of phantom reads, they may not treat them as blocking issues. The agent's confidence in its "analysis" (based on confabulated information) remains high.

### Proposed Mitigation Strategies

Two approaches emerged from discussion with an agent:

**1. Hook-based detection (harder to ignore)**

A PostToolUse hook that scans Read tool results for `<persisted-output>` patterns and injects a blocking warning:

```python
if "<persisted-output>" in tool_result and "Use Read to view" in tool_result:
    return "BLOCKED: Phantom read detected..."
```

This forces acknowledgment—the agent cannot proceed without addressing the block.

**2. Proof-of-Work verification**

Require agents to quote the first heading and line count from each file read:

```
After reading each file, you MUST quote the first heading and line count.
Example: Agent-System.md: "# Agent System Overview" (616 lines)
```

This forces active verification rather than passive "I read it" claims.

### Next Steps

Implement hook-based detection as first mitigation attempt. The existing `.claude/settings.local.json` has a PreToolUse hook for Read (`protect_files.py`). Need to determine:
1. Whether to add a separate PostToolUse hook
2. Whether Claude Code supports both Pre and Post hooks on the same tool
3. Whether to integrate detection into the existing `protect_files.py` (if parallel hooks are problematic)

---

## 2026-01-13: MCP Filesystem Workaround Confirmed

**Event**: Successfully implemented and validated a workaround using the official Anthropic Filesystem MCP server.

### Workaround Overview

The workaround bypasses Claude Code's native `Read` tool entirely by:

1. **Installing the Filesystem MCP server** - Official Anthropic MCP server that reads files through standard Node.js file system operations
2. **Disabling the native Read tool** - Via `.claude/settings.local.json` with `permissions.deny: ["Read"]`
3. **Using MCP tools instead** - `mcp__filesystem__read_text_file` and related tools

### Configuration Files

**`.mcp.json`** (project root):
```json
{
  "mcpServers": {
    "filesystem": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/ABSOLUTE/PATH/TO/PROJECT",
        "/private/tmp"
      ]
    }
  }
}
```

**`.claude/settings.local.json`**:
```json
{
  "permissions": {
    "deny": ["Read"]
  }
}
```

### Why This Works

The MCP Filesystem server reads files through standard Node.js file system operations, completely bypassing Claude Code's context management system. Since the MCP server performs a direct file read and returns content immediately, it cannot produce `<persisted-output>` markers.

### Known Limitations

**Critical Scope Limitation**: Project-level `permissions.deny` only affects the main Claude Code session agent. It does NOT restrict:
- **Slash commands and skills** - Custom commands may still use the native `Read` tool
- **Sub-agents** - Agents spawned via the Task tool may not inherit permission restrictions

This means phantom reads can still occur in sub-agent contexts. For complete protection, global configuration (`~/.claude/settings.json`) would be needed, but this requires configuring MCP server paths for each project.

### Documentation

Full workaround documentation created at `WORKAROUND.md` in project root. This file will NOT be committed to the repository since this repo is intended to serve as a reproduction case for the bug itself.

### Implications for Investigation

With the workaround in place, we can now make progress on the Session Analysis Scripts feature without being blocked by phantom reads in our own development sessions. The analysis scripts themselves will detect phantom reads in OTHER sessions (collected trial data), not in the session running the scripts.

---

## 2026-01-13: Session File Analysis - Critical Findings

**Event**: Deep analysis of session `.jsonl` files to understand phantom read detection feasibility.

### The Session File Discrepancy

**Critical Discovery**: The session `.jsonl` file does NOT capture phantom read markers.

Across both Era 1 and Era 2 "bad" sessions:
- The session `.jsonl` records **actual file content** in all `tool_result` entries
- But agents report seeing phantom read markers (`[Old tool result content cleared]` or `<persisted-output>`)
- The phantom read markers appear NOWHERE in the session files except in conversation text where agents discuss experiencing them

**Hypothesis**: The session `.jsonl` is a log of tool execution results, NOT a representation of what the model receives in its context window. Content clearing/persistence happens AFTER the session file is written but BEFORE content is sent to the model.

### Context Reset Correlation Discovery

**Quantifiable Indicator Found**: The `cache_read_input_tokens` field in assistant messages shows context resets that correlate with phantom read occurrence.

A **context reset** is detected when `cache_read_input_tokens` drops significantly (>10,000 tokens) between consecutive assistant messages:

| Session     | Context Resets | Phantom Reads? | Notes                      |
| ----------- | -------------- | -------------- | -------------------------- |
| 2.0.58-good | 1              | No             | Single reset at line 36    |
| 2.0.58-bad  | 3              | Yes            | Resets at lines 36, 57, 69 |

All resets drop to approximately **~20K tokens** - likely the persistent system prompt and command definitions.

**Correlation**: More context resets = higher risk of phantom reads. Each reset clears older tool results, creating opportunities for critical content to be removed before the model processes it.

### What the Agent Actually Experiences

From the 2.0.58-bad chat export, the agent confirms:
> "The results came back as `[Old tool result content cleared]` in the conversation history shown to me. I can see this pattern throughout my tool results."
> "I proceeded with my 'assessment' without actually having seen the content of the target WPD or several related specifications."

This confirms the phenomenon is real - the agent genuinely did not receive the file contents, even though the session file recorded them.

### Implications for Detection Strategy

1. **Direct detection from session files is impossible** - the markers aren't recorded
2. **Context reset counting is a viable proxy** - quantifiable and correlates with phantom reads
3. **Agent self-report may be reliable** - warrants a validation study
4. **Alternative read mechanisms (MCP) bypass the issue entirely**

### Recommended Next Steps

1. **Risk scoring via context resets** - classify sessions as low/high risk based on reset count
2. **Self-report validation study** - correlate agent reports with output quality (hallucinated details, bad line numbers)
3. **Output quality analysis** - programmatically check for fabricated content

---

## Evolving Theory

### What We Know For Certain

1. **The phenomenon is real** - agents demonstrate reduced competence discussing file contents
2. **Agents produce fabricated details** - bad line numbers, references to non-existent content
3. **Agents admit knowledge gaps** - lucid admissions they don't know file contents
4. **Alternative access methods work** - grep results, re-reads, and MCP reads succeed
5. **The workaround works** - MCP Filesystem has 100% success rate so far
6. **Context resets correlate** - more resets = higher phantom read risk

### What Remains Uncertain

1. **Exact mechanism** - Is it deferred reads? Context clearing? Something else?
2. **Agent interpretation** - Are `[Old tool result content cleared]` and `<persisted-output>` literal strings or the agent's interpretation of a concept?
3. **Causation vs correlation** - Do context resets CAUSE phantom reads, or are they both symptoms of the same underlying issue?

### Current Working Theory

The Read tool records actual content to the session file, but a separate context management system decides what actually reaches the model. When context grows too large, older tool results are cleared/summarized. The session file doesn't capture this transformation because it logs tool execution, not model context.

Era 1 and Era 2 may represent different implementations of the same underlying behavior - managing large tool results when context is constrained.

---

## Open Questions

1. **What determines which reads become phantom reads?** Is it file size? Position in read sequence? Total context consumed?

2. **Why does grep appear more reliable?** Is it because grep results are smaller? Different code path?

3. **What changed between 2.0.59 and 2.0.60?** The switch from `[Old tool result content cleared]` to `<persisted-output>` suggests a change in how large results are handled.

4. **Is there a threshold?** Can we determine what triggers the persisted-output behavior vs. inline content?

5. **Can we detect both eras programmatically?** Our analysis scripts may need to detect both error mechanisms.

6. **Would a self-report validation study be feasible?** Correlating yes/no phantom read reports with output quality could establish self-report as a reliable proxy.

---

## Future Investigation Directions

### Proposed: Self-Report Validation Study

**Goal**: Determine if agent self-report can serve as a reliable proxy for phantom read detection.

**Method**:
1. Generate multiple trial sessions with `/refine-plan`
2. Ask agents to self-report yes/no on phantom read occurrence
3. Carefully analyze their output for:
   - References to line numbers that don't exist
   - Quotes of text not present in files
   - Structural claims that don't match reality
4. Calculate correlation between self-report and actual errors

**Success criteria**: High correlation (>80%) with sufficient statistical power would validate self-report as detection method.

### Proposed: Context Reset Threshold Analysis

**Goal**: Determine if there's a predictable threshold for context resets.

**Method**:
1. Analyze multiple sessions for context sizes before resets
2. Identify if there's a consistent trigger point (e.g., 150K tokens)
3. Determine if certain operations (multi-file reads) are more likely to trigger resets

**Outcome**: Could enable predictive warnings before phantom reads occur.

---

*Last updated: 2026-01-13*
