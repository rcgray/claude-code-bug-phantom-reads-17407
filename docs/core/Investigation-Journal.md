# Investigation Journal

This document tracks ongoing discoveries, experiments, and findings related to the Phantom Reads bug investigation. Entries are chronological, with the most recent at the bottom.

For the formal experiment methodology and protocol, see [Experiment-Methodology-04.md](../experiments/methodologies/Experiment-Methodology-04.md). This journal captures the raw investigation process, including discoveries that may update or refine our understanding documented elsewhere.

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

## 2026-01-13: PreToolUse Hook Workaround Attempt

**Event**: Attempted to use Claude Code hooks as a workaround mechanism before discovering the MCP solution.

### Approach

The idea was to use a PreToolUse hook with a "deny" response as a hack to inject file contents through the error mechanism. When a hook returns a deny message, that message is shown to the agent. By including the actual file contents in the deny message, we could theoretically bypass the phantom read issue.

### Implementation

Created a hook script (similar to the existing `reliable_read.py` in `dev/misc/`) that would:
1. Intercept Read tool calls via PreToolUse hook
2. Read the file contents directly
3. Return a "deny" response containing the actual file contents
4. The agent would receive the contents via the error message

### Result: FAILED

**Hooks are not reliable enough in Claude Code.** Even when the hooks were observed to fire (in the terminal), the agent behaved normally—still experiencing and confirming `<persisted-output>` responses. The hooks appeared to not fire consistently.

### Conclusion

Hook-based workarounds are not viable for phantom read mitigation. This led to exploring the MCP Filesystem server as an alternative approach.

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

## 2026-01-14: Context Reset Analysis Document

**Event**: Created formal analysis document for context reset theory.

Findings from session file analysis were formalized in `docs/theories/Context-Reset-Analysis.md`, documenting:
- The correlation between context reset frequency and phantom read occurrence
- The ~140K token threshold hypothesis for reset triggers
- Detection algorithm for counting resets in session files
- Risk classification framework (low/medium/high risk based on reset count)

### Reproduction Environment Plan

Created `docs/archive/reproduction-environment-plan.md` documenting the strategy for creating a controlled reproduction environment within this repository, based on the ~140K token threshold discovery.

Key insight: If we can control token consumption, we can control phantom read occurrence. The plan proposed creating dummy specification documents of known complexity that would push sessions above or below the threshold predictably.

---

## 2026-01-15: Reproduction Specs Collection Implementation and First Tests

**Event**: Implemented the Reproduction Specs Collection feature and conducted first reproduction trials.

### Feature Implementation

Completed implementation of `docs/features/reproduction-specs-collection/Reproduction-Specs-Collection-Overview.md`:
- Created 6 interconnected specification documents describing a fictional "Data Pipeline System"
- Created 3 test WPDs (easy, medium, hard) designed to trigger different levels of token consumption
- Total spec content: ~3,600 lines across 6 files

### Directory Structure

```
docs/
├── specs/                              # Dummy specification files
│   ├── data-pipeline-overview.md       # Hub document (425 lines)
│   ├── module-alpha.md                 # Ingestion module (742 lines)
│   ├── module-beta.md                  # Transformation module (741 lines)
│   ├── module-gamma.md                 # Output module (771 lines)
│   ├── integration-layer.md            # Cross-module protocols (530 lines)
│   └── compliance-requirements.md      # Audit/regulatory reqs (392 lines)
└── wpds/                               # Test Work Plan Documents
    ├── refactor-easy.md                # Minimal scope WPD
    ├── refactor-medium.md              # Partial scope WPD
    └── refactor-hard.md                # Full scope WPD
```

### Trial Methodology Enhancement

Enhanced the trial methodology to include `/context` calls at key points:

```
/wsd:init --custom
/context                    # Capture baseline
/refine-plan docs/wpds/refactor-{easy|medium|hard}.md
/context                    # Capture post-operation
[Prompt for phantom read self-report]
/export
```

This provides precise token consumption data at the critical juncture.

### First Trial Results

Conducted 3 trials (one for each difficulty level) in a clone of this repository:

| Trial  | Pre-/refine-plan | Post-/refine-plan | Delta | Expected | Actual  |
| ------ | ---------------- | ----------------- | ----- | -------- | ------- |
| Hard   | 95K (48%)        | 149K (75%)        | +54K  | FAILURE  | SUCCESS |
| Medium | 80K (40%)        | 123K (62%)        | +43K  | MIXED    | SUCCESS |
| Easy   | 74K (37%)        | 94K (47%)         | +20K  | SUCCESS  | SUCCESS |

**Result**: All three trials succeeded. The hard case was expected to fail but did not.

### Initial Analysis

The hard trial reached 149K tokens (75% of 200K context window) but experienced no phantom reads. This suggested either:
1. The ~140K threshold hypothesis was incorrect
2. The reproduction environment was missing some critical factor
3. The spec content alone was insufficient

Trial data saved to `dev/misc/repro-attempts/` for analysis.

---

## 2026-01-15: WSD Development Project Repeat Trials

**Event**: Conducted new trials in the WSD Development project (the original project where phantom reads were first encountered) using the enhanced `/context` methodology.

### Purpose

To obtain trials with embedded `/context` data from a project where phantom reads are KNOWN to occur, enabling comparison with the failed reproduction attempts.

### Results

Captured both a successful and failing trial:
- `dev/misc/wsd-dev-repeat/2.1.6-good/` - No phantom reads
- `dev/misc/wsd-dev-repeat/2.1.6-bad/` - Phantom reads confirmed

**Critical Data**:

| Metric                    | GOOD Trial     | BAD Trial      |
| ------------------------- | -------------- | -------------- |
| Pre-/refine-plan          | **85K (42%)**  | **126K (63%)** |
| Post-/refine-plan         | **159K (79%)** | **142K (71%)** |
| Delta during /refine-plan | **+74K**       | **+16K**       |
| Phantom Reads?            | **NO**         | **YES**        |

### Counter-Intuitive Discovery

**The BAD trial consumed FEWER total tokens but experienced phantom reads.**

The bad trial:
- Started at 126K tokens (63% context consumption)
- Ended at only 142K tokens (71%)
- Added only 16K tokens during `/refine-plan`
- Experienced phantom reads on multiple files

The good trial:
- Started at 85K tokens (42% context consumption)
- Ended at 159K tokens (79%)
- Added 74K tokens during `/refine-plan`
- All files read successfully inline

---

## 2026-01-15: Headroom Theory Discovered

**Event**: Analysis of the WSD Development repeat trials led to the discovery of the Headroom Theory.

### The Key Insight

The critical factor is **starting context consumption** (and therefore available headroom) before a multi-file read operation, NOT total content size or final token consumption.

**Headroom** = Available buffer space = Context Window Size - Current Consumption

### Why the Bad Trial Failed

The bad trial agent read more files during onboarding:
- `Python-Test-Environment-Isolation-Standards.md` (1,238 lines)
- `TypeScript-Test-Environment-Isolation-Standards.md` (1,251 lines)
- Additional standards files

This pushed context to 126K tokens (only 74K headroom) BEFORE `/refine-plan` even started. When the agent tried to read the spec files, it had insufficient buffer space and context management triggered phantom reads early.

The good trial had 115K headroom, allowing all files to be read without triggering aggressive context management.

### Why Our Reproduction Failed

Our reproduction environment's onboarding process consumes ~74-95K tokens, leaving 105-126K headroom. The WSD Development bad trial demonstrates that phantom reads occur when headroom drops below ~80K. Our trials never entered this danger zone.

### Relationship to Reset Theory

The Headroom Theory **supports and refines** the Reset Theory:

| Theory              | Explains                                                                   |
| ------------------- | -------------------------------------------------------------------------- |
| **Reset Theory**    | The MECHANISM - context resets clear content before the model processes it |
| **Headroom Theory** | The TRIGGER - low starting headroom causes earlier/more frequent resets    |

The theories are complementary:
1. Low headroom → More resets (Headroom Theory)
2. More resets → More phantom reads (Reset Theory)

### Documentation

Created `docs/theories/Headroom-Theory.md` to formally document these findings and their relationship to the Reset Theory.

### Implications for Reproduction Environment

To reliably trigger phantom reads, we must:
1. **Increase baseline consumption** before `/refine-plan` (not just spec content size)
2. **Target ~120-130K pre-operation** to reduce headroom to <80K
3. **Add substantial onboarding content** (e.g., large standards files similar to WSD Development)

### Risk Classification (Revised)

Based on the Headroom Theory:
- **Low risk**: <50% consumption (>100K headroom)
- **Medium risk**: 50-60% consumption (80-100K headroom)
- **High risk**: >60% consumption (<80K headroom)

---

## Evolving Theory

### What We Know For Certain

1. **The phenomenon is real** - agents demonstrate reduced competence discussing file contents
2. **Agents produce fabricated details** - bad line numbers, references to non-existent content
3. **Agents admit knowledge gaps** - lucid admissions they don't know file contents
4. **Alternative access methods work** - grep results, re-reads, and MCP reads succeed
5. **The workaround works** - MCP Filesystem has 100% success rate so far
6. **Context resets correlate** - more resets = higher phantom read risk
7. **Starting headroom matters** - low headroom before multi-file operations predicts phantom reads

### What Remains Uncertain

1. **Exact threshold** - Is the danger zone truly at ~120-130K starting consumption?
2. **Causation details** - Does low headroom cause more resets, or are both symptoms of the same underlying issue?
3. **File-level factors** - Are certain files more vulnerable than others?

### Current Working Theory

The Read tool records actual content to the session file, but a separate context management system decides what actually reaches the model. When context grows too large, older tool results are cleared/summarized. The session file doesn't capture this transformation because it logs tool execution, not model context.

**The Headroom Theory adds**: When a multi-file operation begins with already-high context consumption, the system has less buffer space and triggers context management sooner and more frequently, leading to more phantom reads.

Era 1 and Era 2 may represent different implementations of the same underlying behavior - managing large tool results when context is constrained.

---

## Open Questions

1. **What determines which reads become phantom reads?** Is it file size? Position in read sequence? Total context consumed? **Headroom at time of read?**

2. **Why does grep appear more reliable?** Is it because grep results are smaller? Different code path?

3. **What changed between 2.0.59 and 2.0.60?** The switch from `[Old tool result content cleared]` to `<persisted-output>` suggests a change in how large results are handled.

4. **Is there a precise headroom threshold?** Can we determine exactly what headroom level triggers the persisted-output behavior?

5. **Can we detect both eras programmatically?** Our analysis scripts may need to detect both error mechanisms.

6. **Can we validate headroom theory with additional trials?** Conduct trials with varying starting consumption levels.

---

## Next Steps

1. **Validate Headroom Theory** - Conduct trials with controlled starting consumption to verify threshold
2. **Update Reproduction Environment** - Add substantial onboarding content to reduce headroom
3. **Re-run Reproduction Trials** - Test whether increased baseline triggers phantom reads
4. **Update Documentation** - Revise Reproduction-Specs-Collection-Overview.md with headroom requirements

---

## 2026-01-16-17: CC Version Script Completed

**Event**: Implemented and tested the CC Version Script (`src/cc_version.py`).

### Purpose

The CC Version Script automates the tedious manual process of managing Claude Code versions during phantom reads investigation trials. It replaces the multi-step npm commands and manual JSON editing documented in the experiment methodology with a single streamlined command interface.

### Features Implemented

- **`--disable-auto-update`** - Sets `env.DISABLE_AUTOUPDATER` to `"1"` in `~/.claude/settings.json`
- **`--enable-auto-update`** - Removes the setting to restore auto-update behavior
- **`--list`** - Lists available Claude Code versions from npm registry
- **`--status`** - Shows auto-updater state, installed version, and latest available version
- **`--install <version>`** - Installs a specific Claude Code version (validates against available versions)
- **`--reset`** - Restores defaults (enable auto-update, install latest version)

### Design Decisions

- **Conservative error handling** - Any unexpected condition results in clear error message and exit
- **Idempotent operations** - Enable/disable commands can be run multiple times safely
- **Backup creation** - Creates timestamped backups before modifying settings.json
- **Dependency injection** - All external dependencies (filesystem, subprocess, time) are injectable for testing

### Testing

Comprehensive test suite with 64 test cases covering:
- Settings file manipulation and backup
- Auto-update enable/disable with various initial states
- Version querying and validation
- Installation sequence orchestration
- CLI argument parsing and mutual exclusivity
- Integration workflows

### Specification

Full specification at `docs/features/cc-version-script/CC-Version-Script-Overview.md`.

---

## 2026-01-18: Collect Trials Script Completed

**Event**: Implemented and tested the Collect Trials Script (`src/collect_trials.py`).

### Purpose

The Collect Trials Script automates the collection and organization of phantom read trial artifacts from Claude Code sessions. It eliminates the tedious manual process of gathering chat exports and session `.jsonl` files after running reproduction trials.

### Features Implemented

- **Automated artifact collection** - Locates and gathers all files associated with a trial (chat exports, session `.jsonl` files, subagent logs, tool results)
- **Workscope-keyed organization** - Structures collected artifacts into directories named by Workscope ID (`YYYYMMDD-HHMMSS`)
- **Session structure abstraction** - Transparently handles all Claude Code session storage structures (flat, hybrid, hierarchical)
- **Idempotent batch processing** - Skips already-collected trials, removes processed exports

### Session Storage Structures Handled

The script correctly handles all observed session file organization patterns:

1. **Flat Structure** (2.0.58, 2.0.59) - Agent files at root level, no subdirectory
2. **Hybrid Structure** (2.0.60) - Agent files at root, subdirectory with tool-results/ only
3. **Hierarchical Structure** (2.1.3, 2.1.6) - All content in subdirectory with subagents/ and tool-results/

The unified collection algorithm handles all structures without needing to detect which type is present.

### Collection Algorithm

```
1. Validate input directories exist
2. Scan exports for Workscope IDs (pattern: Workscope ID:? Workscope-?YYYYMMDD-HHMMSS)
3. Derive session directory from current working directory
4. For each export: create trial directory, find session by Workscope ID, copy all files
5. Delete source export only after successful collection
6. Report summary with collected/skipped/failed counts
```

### Testing

Comprehensive test suite with 40+ test cases covering:
- Input validation and path encoding
- Export scanning with both Workscope ID formats
- Session file discovery and UUID extraction
- Unified copy algorithm for all three structure types
- Idempotency guarantees
- Integration workflows with mixed structures

### Specification

Full specification at `docs/features/collect-trials-script/Collect-Trials-Script-Overview.md`.

---

## Investigation Tooling Status

With the completion of these two scripts, the core investigation tooling for Phase 4 is now available:

| Tool                     | Purpose                                    | Status     |
| ------------------------ | ------------------------------------------ | ---------- |
| `src/cc_version.py`      | Manage Claude Code versions                | ✅ Complete |
| `src/collect_trials.py`  | Collect trial artifacts                    | ✅ Complete |
| Session Analysis Scripts | Detect phantom reads in collected sessions | 🔲 Pending  |

The analysis scripts (Phase 4.3) will build on the collected trial data to programmatically detect phantom read occurrences, removing reliance on agent self-reporting.

---

## 2026-01-19: WSD-Dev-02 Collection and Reset Timing Theory

**Event**: Created the wsd-dev-02 trial collection and discovered the Reset Timing Theory.

### Collection Overview

Conducted 7 initial trials using Experiment-Methodology-02 against the WSD Development project, triggering multi-file read operations via the `/refine-plan` command. Trials were collected in `dev/misc/wsd-dev-02/`.

| Trial ID        | Outcome | Pre-Op % | Headroom | Resets | Pattern          |
| --------------- | ------- | -------- | -------- | ------ | ---------------- |
| 20260119-131802 | SUCCESS | 43%      | 115K     | 2      | EARLY + LATE     |
| 20260119-132353 | FAILURE | 55%      | 90K      | 4      | EARLY + MID/LATE |
| 20260119-133027 | FAILURE | 43%      | 114K     | 4      | EARLY + MID/LATE |
| 20260119-133726 | FAILURE | 43%      | 114K     | 2      | LATE CLUSTERED   |
| 20260119-140145 | FAILURE | 41%      | 117K     | 3      | EARLY + MID/LATE |
| 20260119-140906 | FAILURE | 48%      | 104K     | 4      | EARLY + MID/LATE |
| 20260119-142117 | SUCCESS | 43%      | 113K     | 2      | EARLY + LATE     |

### Key Discovery: Reset Timing Theory

Analysis revealed that **reset timing pattern** is more predictive than either headroom or reset count alone.

**Pattern Classification**:

| Pattern              | Description                                       | Risk |
| -------------------- | ------------------------------------------------- | ---- |
| **EARLY + LATE**     | First reset <50%, last reset >90%, no mid-session | LOW  |
| **EARLY + MID/LATE** | Early reset plus one or more mid-session (50-90%) | HIGH |
| **LATE CLUSTERED**   | All resets >80% and close together                | HIGH |

**Critical Evidence**: Trial 133726 had identical metrics to successful trials (86K pre-op, 114K headroom, 2 resets) but FAILED due to LATE CLUSTERED timing (resets at 83% and 97%). This proves timing matters more than count or headroom.

### Trial Data Preprocessing Tool

Created `.claude/commands/update-trial-data.md` - a preprocessing tool that extracts data from trial session files into structured `trial_data.json` files for analysis. This enables systematic comparison across trials.

Full analysis documented in: `docs/experiments/results/WSD-Dev-02-Analysis-1.md`

---

## 2026-01-20: WSD-Dev-02 Expanded Analysis (22 Trials)

**Event**: Added 15 additional trials to the wsd-dev-02 collection, bringing total to 22 trials.

### Results Summary

- **Total Trials**: 22
- **SUCCESS**: 5 (22.7%)
- **FAILURE**: 17 (77.3%)

### Reset Timing Theory Strongly Validated

The expanded dataset achieved **100% prediction accuracy** for the Reset Timing Theory:

| Pattern             | Trials | Outcomes         |
| ------------------- | ------ | ---------------- |
| EARLY_PLUS_LATE     | 4      | **100% SUCCESS** |
| SINGLE_LATE         | 1      | **100% SUCCESS** |
| EARLY_PLUS_MID_LATE | 11     | **100% FAILURE** |
| LATE_CLUSTERED      | 2      | **100% FAILURE** |
| OTHER               | 4      | **100% FAILURE** |

**Critical Insight**: The presence of **any mid-session reset (50-90% through the session)** is a near-perfect predictor of phantom read occurrence.

### Theory Validation Summary

| Theory                  | Status              | Notes                            |
| ----------------------- | ------------------- | -------------------------------- |
| **Reset Timing Theory** | STRONGLY CONFIRMED  | 100% prediction accuracy         |
| **Reset Count Theory**  | PARTIALLY VALIDATED | Correlates but not deterministic |
| **Headroom Theory**     | WEAKENED            | Necessary but not sufficient     |

### The "Clean Gap" Pattern

Successful sessions exhibit a "clean gap" pattern:
1. Early reset occurs during initialization/setup phase
2. Main file reading operations proceed without interruption
3. Late reset occurs only after operations complete

This suggests the agent's context can "survive" resets at natural breakpoints, but cannot survive resets that interrupt active file processing.

Full analysis documented in: `docs/experiments/results/WSD-Dev-02-Analysis-2.md`

---

## 2026-01-20: Token-Based Analysis

**Event**: Enhanced trial_data.json with token count data (schema 1.1) and performed detailed token-based analysis.

### Token Count Collection

Collected token counts for all files read across trials using the Anthropic API. Data stored in `dev/misc/wsd-dev-02/file_token_counts.json`. Updated the `/update-trial-data` preprocessing tool to incorporate token data into `trial_data.json` files.

### Key Findings

#### 1. No Fixed Reset Threshold

Resets occur at widely varying cumulative token counts:
- **Early resets (SUCCESS)**: 82K-88K cumulative tokens
- **Mid-session resets (FAILURE)**: 153K-383K cumulative tokens
- **Late resets (both)**: 140K-379K cumulative tokens

The 5x variation (82K to 383K) rules out a simple threshold model.

#### 2. Large File Correlation - Weak

File size at reset point does NOT predict outcome. Resets occur after both small (<1K) and large (>10K) files in both SUCCESS and FAILURE cases.

#### 3. The "Clean Gap" Pattern - Quantified

**SUCCESS Trials**:
| Trial           | Early Reset | Late Reset | Gap Width | Tokens in Gap |
| --------------- | ----------- | ---------- | --------- | ------------- |
| 20260120-095152 | 87,790      | 340,837    | 60.5%     | 253,047       |
| 20260120-093204 | 85,948      | 379,133    | 65.0%     | 293,185       |

SUCCESS trials show large "clean gaps" (55-65% of session) where work proceeds uninterrupted.

#### 4. Dynamic Context Pressure Hypothesis

**New Hypothesis**: Resets are triggered by **rate of context accumulation** rather than absolute values.

Supporting evidence:
- SUCCESS sessions show steady token progression with natural pauses
- FAILURE sessions show rapid batch reads without breathing room
- Same cumulative total can succeed or fail depending on accumulation rate

### Tentative Safe Batch Size

Based on the data:
- **After an early reset**: ~60-70K tokens can be read safely
- **Without an early reset**: First reset occurs around 68K tokens into read operations
- **Recommended safe batch**: ~50K tokens between reset opportunities

### Revised Risk Model

| Risk Level   | Primary Indicator                      | Token Signature                 |
| ------------ | -------------------------------------- | ------------------------------- |
| **LOW**      | SINGLE_LATE or EARLY_PLUS_LATE pattern | Work completes in protected gap |
| **HIGH**     | Any reset in 50-90% range              | Active work disrupted           |
| **CRITICAL** | Multiple resets in 50-90%              | Repeated mid-session disruption |

Full analysis documented in: `docs/experiments/results/WSD-Dev-02-Analysis-3.md`

---

## 2026-01-21: Trial Data Preprocessing Improvements

**Event**: Enhanced the `/update-trial-data` script and upgraded all trial_data.json files to Schema 1.2.

### Improvements Made

- **Script reliability**: Fixed issues in `scripts/extract_trial_data.py` for more robust session parsing
- **Static helper file**: Updated the karpathy script to use a static helper file approach
- **Schema upgrade**: All relevant trials now use Schema 1.2 with improved data structure

### Token Count Collection

Ran pre-processing and determined token counts for the collection file `file_token_counts.json` in preparation for cross-project analysis. This enables systematic comparison of token consumption patterns across different trial collections.

---

## 2026-01-21: Repro-Attempts-02 Collection and Analysis

**Event**: Conducted 9 trials across three reproduction scenarios (Easy, Medium, Hard) and completed analysis.

### Collection Overview

First trial collection specifically designed to test reproduction scenarios at different failure rate targets:

| Scenario | Target Failure Rate | Actual Failure Rate |
|----------|---------------------|---------------------|
| Hard     | 100%                | 33% (1/3)           |
| Medium   | 50%                 | 0% (0/3)            |
| Easy     | 0%                  | 0% (0/3)            |

Trial data collected in `dev/misc/repro-attempts-02/`.

### Critical Achievement: First Reproduction Success

**The single Hard scenario failure (20260121-202919) represents the first successful phantom read occurrence in any reproduction scenario**, breaking the "Hawthorne Effect" concern that conducting trials in a project dedicated to studying the bug might prevent it from manifesting.

### The Failure Case: 20260121-202919

The failure stood out across every metric:

| Metric                | Failure (202919) | Success Average | Delta   |
|-----------------------|------------------|-----------------|---------|
| Pre-op consumption    | 54% (107K)       | 40% (79K)       | +14%    |
| Total resets          | 4                | 2               | +2      |
| Mid-session resets    | 3 (57%, 72%, 84%)| 0-1             | +2-3    |
| File reads            | 19               | 10              | +9      |
| Tool results dir      | Present          | Absent          | —       |

**Reset Pattern**:
```
Failure: 57% → 72% → 84% → 96% (3 consecutive mid-session resets)
Success: ~50% → ~89% (borderline early, then late after work completes)
```

### Theory Validation

**Reset Timing Theory: STRONGLY VALIDATED**
- Previous: 100% prediction accuracy on 22 WSD-Dev-02 trials
- This collection: 100% prediction accuracy on 9 trials
- **Combined: 31/31 trials match predictions (100%)**

**Reset Count Theory: STRENGTHENED**
- 2 resets: 8 trials, 100% SUCCESS
- 4 resets: 1 trial, 100% FAILURE
- Correlation stronger than previously recognized

### New Theories Identified

#### Mid-Session Reset Accumulation

A single borderline mid-session reset (50-65%) appears survivable. Multiple mid-session resets guarantee failure.

| Mid-Session Resets | Expected Outcome     |
|--------------------|----------------------|
| 0                  | Safe                 |
| 1 (borderline)     | Likely survivable    |
| 2+                 | Likely failure       |
| 3+                 | Guaranteed failure   |

#### Sustained Processing Gap Requirement

Successful trials show a consistent pattern:
- First reset at ~50% (boundary of danger zone)
- No resets until ~89% (after file processing completes)
- Creates a ~35-40% "clean gap" for uninterrupted work

**Hypothesis**: Success requires an uninterrupted processing window of at least 25-30% of session duration.

#### Onboarding Read Count as Trigger Variable

The failure case read significantly more files during onboarding (19 vs 6-11), pushing pre-op consumption from ~36% to 54%.

**Causal chain identified**: Onboarding read volume → higher pre-op → lower headroom → more resets during trigger phase → phantom reads.

### Key Insight

**Our reproduction scenarios differentiate by spec content volume, but the real trigger is onboarding context consumption BEFORE the trigger fires.**

Both successful Hard trials had identical metrics to Medium trials (~36% pre-op, 2 resets). The single failure had elevated pre-op consumption due to additional onboarding reads.

### Recovery Behavior Observed

Notably, the failure was a **recovered failure**. The agent:
1. Recognized the `<persisted-output>` markers
2. Understood this was phantom reads (from project context)
3. Re-read the original files successfully
4. Completed the task with actual file content

This suggests the Hawthorne Effect may not prevent phantom reads from occurring, but may enable recovery through agent awareness.

Full analysis documented in: `docs/experiments/results/Repro-Attempts-02-Analysis-1.md`

---

## Evolving Theory

### What We Know For Certain

1. **The phenomenon is real** - agents demonstrate reduced competence discussing file contents
2. **Agents produce fabricated details** - bad line numbers, references to non-existent content
3. **Agents admit knowledge gaps** - lucid admissions they don't know file contents
4. **Alternative access methods work** - grep results, re-reads, and MCP reads succeed
5. **The workaround works** - MCP Filesystem has 100% success rate so far
6. **Context resets correlate** - more resets = higher phantom read risk
7. **Starting headroom matters** - low headroom before multi-file operations predicts phantom reads
8. **Reset TIMING is critical** - mid-session resets (50-90%) predict failure with 100% accuracy (31/31 trials)
9. **No fixed token threshold** - resets occur at 82K-383K cumulative tokens
10. **Accumulation rate matters** - rapid batch reads without pauses increase risk
11. **Reset COUNT correlates strongly** - 2 resets = safe (100%), 4+ resets = failure (100% in current data)
12. **Multiple mid-session resets guarantee failure** - 3+ consecutive mid-session resets have 100% failure rate
13. **Reproduction is achievable** - first phantom read successfully triggered in reproduction scenario
14. **Hawthorne Effect doesn't prevent occurrence** - but may enable recovery through agent awareness

### What Remains Uncertain

1. **Exact mechanism** - What internally triggers a reset at a specific moment?
2. **Rate threshold** - Is there a tokens-per-turn rate that reliably predicts resets?
3. **Mitigation effectiveness** - Can intentional early resets or batching prevent failures?
4. **Single mid-session reset survivability** - Is one borderline (50-65%) mid-session reset consistently survivable?
5. **Clean gap minimum** - Is 25-30% uninterrupted processing window truly required for success?

### Current Working Theory

The Read tool records actual content to the session file, but a separate context management system decides what actually reaches the model. When context grows too large OR accumulates too rapidly, older tool results are cleared/summarized.

**The Reset Timing Theory refines our understanding**: It's not just HOW MUCH context, but WHEN resets occur. Resets during active file processing (50-90% of session) clear content before the model processes it, causing phantom reads. Resets at natural breakpoints (early setup, late completion) are survivable.

**The Dynamic Context Pressure Hypothesis adds**: Rapid token accumulation (batch reads without processing pauses) may trigger resets more readily than steady accumulation, even at lower total counts.

**The Mid-Session Reset Accumulation Theory adds**: A single borderline mid-session reset may be survivable, but multiple mid-session resets (2+) correlate with failure, and 3+ consecutive mid-session resets guarantee failure.

**The Sustained Processing Gap Requirement**: Successful sessions exhibit a "clean gap" of ~35-40% of session duration where work proceeds uninterrupted between an early reset and a late reset. Failure occurs when this gap is fragmented by mid-session resets.

### Theory Status Summary (as of 2026-01-21)

| Theory | Status | Evidence |
|--------|--------|----------|
| Reset Timing | **STRONGLY CONFIRMED** | 31/31 trials (100%) |
| Reset Count | **STRENGTHENED** | 2 resets = safe, 4+ = failure |
| Headroom | **SUPPORTED** | Correlates but insufficient alone |
| Mid-Session Accumulation | **NEW** | 2+ mid-session = likely failure |
| Sustained Processing Gap | **NEW** | ~25-30% uninterrupted window |
| Dynamic Context Pressure | **HYPOTHESIS** | Needs rate-based validation |

---

## Open Questions

1. **What internally triggers a reset?** Is it threshold-based, rate-based, time-based, or some combination?

2. **Can intentional early resets prevent mid-session resets?** If we force an early reset, does it provide a "clean gap" for subsequent operations?

3. **Does batching with processing pauses help?** Can we prevent rapid accumulation by inserting summarization steps between read batches?

4. **Why does grep appear more reliable?** Different code path? Smaller result sizes?

5. **Can we predict reset timing?** Given starting conditions, can we estimate when resets will occur?

6. **Are these findings version-specific?** Do they hold across Era 1 and Era 2 builds?

7. **How to reliably achieve target failure rates in reproduction scenarios?** Current scenarios differentiate by spec content volume, but onboarding context consumption appears more critical.

8. **Is there a pre-op threshold?** The repro-attempts-02 failure had 54% pre-op vs ~36-46% for successes. Is >50% pre-op a danger zone?

9. **Can agent awareness enable reliable recovery?** The repro failure showed recovery via re-reading. Can this be systematized?

---

## Next Steps

### Immediate Actions (Reproduction Scenario Refinement)

1. **Update Hard scenario onboarding** - Require reading `Investigation-Journal.md` and `Trial-Analysis-Guide.md` before the trigger to inflate pre-op consumption
2. **Target pre-op thresholds**:
   - Hard: >50% pre-op
   - Medium: 45-50% pre-op
   - Easy: <40% pre-op
3. **Run validation trials** - 5-10 Hard trials with updated onboarding to verify improved failure rate

### Research Priorities

4. **Test pre-op threshold hypothesis** - Run trials at specific starting points (45%, 50%, 55%)
5. **Validate reset count correlation** - Collect more data on 2 vs 3+ resets
6. **Test "Intentional Early Reset" mitigation** - Force early context consumption to trigger reset, then execute multi-file operations in "clean gap"
7. **Test "Session Batching" mitigation** - Break reads into smaller batches with processing gaps
8. **Investigate recovery mechanisms** - Can consistent re-reading serve as a systematic mitigation?
9. **Cross-Version Testing** - Confirm findings aren't version-specific

### Documentation Updates

10. **Update `Trial-Analysis-Guide.md`** - Add "Mid-Session Reset Accumulation" pattern
11. **Consider updating `Experiment-Methodology-02.md`** - With refined predictions based on 31-trial dataset
12. **Ensure README reflects latest findings**

---

## 2026-01-22: Experiment-Methodology-03 Design

**Event**: Designed Experiment-Methodology-03 with simplified initialization and scenario-targeted commands.

### Design Goals

Based on the repro-attempts-02 analysis showing that **onboarding context consumption** (not spec content volume) is the real trigger, the v3.0 methodology was designed to:

1. **Eliminate `/wsd:init --custom`** - Replace with minimal `/wsd:getid` for Workscope ID generation only
2. **Control pre-op consumption via commands** - Three scenario commands (`/analyze-light`, `/analyze-standard`, `/analyze-thorough`) that preload different amounts of context via `@` file notation
3. **Use unified target WPD** - All scenarios use `docs/wpds/pipeline-refactor.md` as the analysis target

### Preload Strategy

The design used hoisted file loading (`@docs/specs/file.md` notation) to force context inflation before the analysis task:

| Scenario | Preload Files | Target Pre-Op |
|----------|---------------|---------------|
| Easy | operations-manual.md | ~35% |
| Medium | Easy + architecture-deep-dive.md | ~46% |
| Hard | Medium + troubleshooting-compendium.md | ~55% |

Documentation created: `docs/experiments/methodologies/Experiment-Methodology-03.md`

---

## 2026-01-22: Repro-Attempts-03 First Trial Collection

**Event**: Conducted first trials using Experiment-Methodology-03.

### Collection Details

Ran 9 trials across three scenario commands:
- `/analyze-thorough docs/wpds/pipeline-refactor.md` (Hard) - 3 trials
- `/analyze-standard docs/wpds/pipeline-refactor.md` (Medium) - 3 trials  
- `/analyze-light docs/wpds/pipeline-refactor.md` (Easy) - 3 trials

All trials conducted in `phantom-read-clone` project (repository without MCP workaround) using Claude Code v2.1.6 (locked).

### Results

**ALL 9 TRIALS SUCCEEDED** - no phantom reads reported.

| Trial ID | Scenario | Outcome |
|----------|----------|---------|
| 20260122-182020 | Mixed | SUCCESS |
| 20260122-182033 | Mixed | SUCCESS |
| 20260122-182627 | Mixed | SUCCESS |
| 20260122-182636 | Mixed | SUCCESS |
| 20260122-182646 | Mixed | SUCCESS |
| 20260122-183100 | Mixed | SUCCESS |
| 20260122-183106 | Mixed | SUCCESS |
| 20260122-183114 | Mixed | SUCCESS |
| 20260122-184620 | Mixed | SUCCESS |

### Post-Processing

- Trials collected to `dev/misc/repro-attempts-03-firstrun/`
- Each trial preprocessed with `/update-trial-data` to create `trial_data.json`
- `file_token_counts.json` was intentionally NOT created for this collection

### Significance

The unexpected 100% success rate across ALL scenarios (including hard) triggered investigation into why the methodology wasn't producing the expected differentiated results. This investigation led to the discoveries documented in the following section - specifically the ~25K hoisting limit and the inability of agents to invoke `/context`.

---

## 2026-01-22-23: Methodology 3.0 Trial Failures and Discoveries

**Event**: Initial trials with Experiment-Methodology-03 revealed critical issues requiring methodology refinement.

### Issue 1: Hoisted File Loading Limit (25k Tokens)

**Discovery**: Claude Code's `@` file notation has a ~25,000 token limit for hoisted reads. Files exceeding this limit are **silently ignored**.

The original `operations-manual.md` (~45k tokens) exceeded this limit, causing it to be completely skipped during hoisting. This meant **all scenarios started at the baseline** (~24k tokens, 12%), and all trials trivially succeeded because pre-operation consumption never reached target levels.

**Resolution**: Split `operations-manual.md` into two files:
- `operations-manual-standard.md` (962 lines, 19,323 tokens)
- `operations-manual-exceptions.md` (2,497 lines, 21,988 tokens)

Both files are now below the 25k limit and load successfully.

### Issue 2: Hard Scenario Context Overflow

**Discovery**: After fixing the operations-manual split, the Hard scenario consistently failed due to **running out of context entirely** rather than experiencing phantom reads.

The combined preload (operations-manual parts + architecture-deep-dive + troubleshooting-compendium) pushed context too high, causing complete session failure instead of the desired mid-session reset pattern.

**Resolution**: Trimmed `architecture-deep-dive.md` by removing appendices and Section E, reducing its size to better fit the target context window.

### Issue 3: `/context` Cannot Be Called by Agents

**Discovery**: The `/context` command (Claude Code built-in for displaying token consumption) **cannot be invoked programmatically by agents**. It only works when explicitly typed by the user.

This broke the original methodology design that assumed context measurements could be embedded within scenario commands or checked programmatically at key points.

**Resolution**: Restructured the trial protocol to require explicit user `/context` calls at three points:
1. **Baseline**: Immediately after starting fresh session
2. **Post-preload**: After running initialization command
3. **Post-analysis**: After running analysis command

### Methodology Restructuring

Based on these discoveries, the command structure was completely redesigned:

**Old Structure (v3.0 design)**:
- `/wsd:getid` → Generate ID only
- `/analyze-light` → Preload + analyze (Easy)
- `/analyze-standard` → Preload + analyze (Medium)
- `/analyze-thorough` → Preload + analyze (Hard)

**New Structure (v4.0 design)**:
- `/setup-easy` → Preload Easy files + generate ID
- `/setup-medium` → Preload Medium files + generate ID
- `/setup-hard` → Preload Hard files + generate ID
- `/analyze-wpd` → Unified analysis command (same for all scenarios)

This separation enables:
- User can run `/context` between initialization and analysis
- Scenario differentiation happens during initialization, not analysis
- Single analysis command simplifies testing

### Calibrated Context Measurements

After all adjustments, calibration trials showed:

| Step | Tokens | % Context |
|------|--------|-----------|
| Fresh session baseline | ~24k | 12% |
| After `/setup-easy` | ~73k | 37% |
| After `/setup-medium` | ~92k | 46% |
| After `/setup-hard` | ~120k | 60% |

These match the target ranges for each scenario tier.

### Documentation Updates

1. Created `docs/experiments/methodologies/Experiment-Methodology-04.md` documenting the refined 7-step protocol
2. Updated `docs/features/reproduction-specs-collection/Reproduction-Specs-Collection-Overview.md`:
   - Version 2.0.0 → 3.0.0
   - Updated command descriptions and token budgets
   - Added Phase 9 "Methodology Refinement" to FIP documenting all changes

### Key Lessons Learned

1. **Test hoisting limits early** - Large files may be silently ignored
2. **User intervention is required** - Some Claude Code features can't be called programmatically
3. **Calibrate before running trials** - Verify context measurements hit targets
4. **Document discoveries as they happen** - Trial-and-error insights are valuable for posterity

---

## Evolving Theory

### Theory Status Summary (as of 2026-01-23)

| Theory | Status | Evidence |
|--------|--------|----------|
| Reset Timing | **STRONGLY CONFIRMED** | 31/31 trials (100%) |
| Reset Count | **STRENGTHENED** | 2 resets = safe, 4+ = failure |
| Headroom | **SUPPORTED** | Correlates but insufficient alone |
| Mid-Session Accumulation | **SUPPORTED** | 2+ mid-session = likely failure |
| Sustained Processing Gap | **SUPPORTED** | ~25-30% uninterrupted window |
| Dynamic Context Pressure | **HYPOTHESIS** | Needs rate-based validation |
| **Hoisting Limit** | **NEW - CONFIRMED** | ~25k tokens per hoisted file |

### What We Know For Certain (Updated)

All previous certainties remain valid, plus:

15. **Hoisted files have a ~25k token limit** - Files exceeding this are silently ignored
16. **`/context` command requires user invocation** - Cannot be called by agents programmatically
17. **Scenario differentiation via preload works** - `/setup-*` commands achieve target pre-op levels

---

## Open Questions (Updated)

Previous questions remain, plus:

10. **Can we achieve reliable failure rates with v4.0 methodology?** - Need validation trials with the refined protocol
11. **Are there other Claude Code features with similar limitations?** - What else can't agents invoke?
12. **What determines the hoisting limit?** - Is it exactly 25k? Does it vary by model or context?

---

## Next Steps (Updated)

### Immediate Actions

1. **Run validation trials with Methodology 4.0** - 5 trials per scenario (15 total) to verify success/failure rates
2. **Document any additional discoveries** - Continue updating this journal
3. **Refine context targets if needed** - Adjust based on trial results

### Research Priorities

4. **Investigate hoisting limit details** - Determine exact threshold and variation factors
5. **Test cross-version consistency** - Verify v4.0 methodology works across Claude Code versions
6. **Continue theory validation** - More data points for Reset Timing and related theories

---

## 2026-01-23: Consolidated Theory and X + Y Model

**Event**: Created `Consolidated-Theory.md` establishing a unified theoretical framework based on manual experimentation with Experiment-Methodology-04.

### The Critical Discovery

All Experiment-Methodology-04 scenarios (Easy, Medium, Hard) succeeded despite reaching high context utilization (up to 90%). The breakthrough insight came from analyzing **why** they all succeeded:

| Scenario | Pre-op (X) | Operation (Y) | X + Y | Outcome |
|----------|------------|---------------|-------|---------|
| Easy | 73K (37%) | 40K | 113K | SUCCESS |
| Medium | 92K (46%) | 40K | 132K | SUCCESS |
| Hard | 120K (60%) | 40K | 160K | SUCCESS |

**All scenarios succeeded because X + Y remained within the context threshold (~200K).**

When additional files (`module-epsilon.md`, `module-phi.md`) were added to increase Y, the Hard scenario began manifesting phantom reads.

### The X + Y Model

This leads to the primary theoretical framework:

- **X** = Pre-operation context consumption (baseline + preloaded content)
- **Y** = Operation context requirement (files read during the triggering action)
- **T** = Context window threshold (appears to be sub-200K based on harness warnings)

**Phantom reads can only occur when X + Y > T**

This reframes our understanding: there is no universally "dangerous" pre-operation consumption level. A session at 60% pre-op with a small Y will succeed; a session at 40% pre-op with a large Y may fail.

### Reframing Previous Theories

The X + Y model explains why previous theories showed strong correlations:

| Previous Theory | Why It Correlated | Actual Mechanism |
|-----------------|-------------------|------------------|
| Headroom Theory | Higher X leaves less room for Y | X + Y overflow is what matters |
| Reset Timing | Mid-session is when deferred reads occur | Reset during deferred processing |
| Reset Count | More resets = more opportunities | Downstream indicator, not cause |
| Clean Gap | Operation completes before reset | Allows Y to process uninterrupted |

### Four Conditions Required for Phantom Reads

Based on current evidence, phantom reads require ALL of the following:

1. **Threshold Overflow**: X + Y > T
2. **Deferred Reads**: Multiple files read simultaneously (batch operation)
3. **Agent-Initiated**: Reads triggered by agent, not hoisting
4. **Reset During Processing**: Context reset while reads are deferred

Remove any condition and phantom reads don't occur.

### Why Within-Threshold Operations Succeed

Even the Hard scenario at 90% context utilization succeeded because:
- All file content (X + Y = 160K) fits within the ~200K threshold
- No aggressive context management is triggered
- No reads need to be deferred or cleared
- The harness can simply accumulate content normally

The "0% remaining" warning at 180K (90%) suggests the harness reserves buffer space, but this is just a warning—not a trigger for phantom reads.

### Open Investigations Identified

1. **Token Accounting Discrepancy**: Files contribute 131K tokens but harness reports 156K total. The ~25K discrepancy may be thinking tokens, system overhead, or message formatting.

2. **Context Reporting Accuracy**: Harness reports "10% remaining" at 76% consumed and "0% remaining" at 90% consumed. Either the effective threshold is lower than 200K, or the harness reserves buffer space.

3. **Hoisting vs Agent-Initiated Reads**: Hoisted files (via `@` notation) appear to use a different code path:
   - Files >25K tokens are silently skipped
   - Hoisted files don't seem to trigger phantom reads
   - Proposed experiment: Hoist >200K tokens to test if phantom reads can occur via hoisting alone

4. **Reset Trigger Mechanism**: Despite extensive observation, we still don't know what triggers a reset. Not a fixed threshold (82K-383K observed), not purely rate-based, not time-based.

### Implications for Reproduction Scenarios

To reliably trigger phantom reads, scenarios must ensure X + Y > T:

| Scenario | Target X | Target Y | Target X+Y | Expected |
|----------|----------|----------|------------|----------|
| Easy | 37% (73K) | 40K | 113K (<T) | SUCCESS |
| Medium | 46% (92K) | 60K | 152K (~T) | MIXED |
| Hard | 60% (120K) | 80K+ | 200K+ (>T) | FAILURE |

The Hard scenario needs Y increased (adding more spec files) to push X + Y over threshold.

### Correct Harness Behavior When X + Y > T

An important observation: when the original `operations-manual.md` was too large and pushed Hard scenarios over the threshold, the harness responded by **erroring out with a context saturation message**. This is the **correct behavior** that should occur instead of phantom reads.

The MCP Filesystem workaround achieves this same correct behavior—when context fills up, you get an error, not silent phantom reads.

### Documentation Created

Created `docs/theories/Consolidated-Theory.md` as the authoritative theoretical reference, superseding individual theory discussions scattered throughout the Investigation Journal.

---

## 2026-01-24: Experiment-Methodology-04 First Run - Universal Failure

**Event**: Ran first validation trials with Experiment-Methodology-04 and discovered unexpected universal failure across all scenarios.

### Trial Collection

Conducted 8 trials (4 Hard, 4 Easy) using the updated methodology with increased Y (added `module-epsilon.md` and `module-phi.md`). Trial data collected in `dev/misc/repro-attempts-04-firstrun/`.

### Results Summary

| Scenario | Trials | X (Pre-op) | Y (Operation) | X + Y | Outcome |
|----------|--------|------------|---------------|-------|---------|
| Hard | 4 | 120K (60%) | 57K | 177K | **100% FAILURE** |
| Easy | 4 | 73K (37%) | 57K | 130K | **100% FAILURE** |

**Critical Finding**: Even the Easy scenario, with X + Y = 130K (well under the 200K threshold), failed consistently. This directly contradicts the X + Y model.

### Reset Pattern Anomaly

All trials showed SINGLE_LATE reset patterns (resets at 64-83% through session):

| Trial | Scenario | Reset Position | Reset From | Pattern | Outcome |
|-------|----------|----------------|------------|---------|---------|
| 20260124-112940 | Hard | 64% | 129K | SINGLE_LATE | FAILURE |
| 20260124-115841 | Easy | 83% | 132K | SINGLE_LATE | FAILURE |
| 20260124-120502 | Easy | 83% | 119K | SINGLE_LATE | FAILURE |

According to the Reset Timing Theory (previously 31/31 = 100% accuracy), SINGLE_LATE patterns should predict SUCCESS. This represents the **first systematic violation** of that theory.

### The Critical Variable: Y Size

Comparing Method-03 (100% success) to Method-04 (100% failure):

| Variable | Method-03 | Method-04 | Changed? |
|----------|-----------|-----------|----------|
| Easy X | 73K | 73K | No |
| Hard X | 120K | 120K | No |
| Y | 42K (7 files) | 57K (9 files) | **YES** |
| T | 200K | 200K | No |

The ONLY change was Y: from 42K tokens (7 files) to 57K tokens (9 files).

**Files in Method-03 Y** (7 files, ~42K tokens):
1. `pipeline-refactor.md` (5,652 tokens)
2. `data-pipeline-overview.md` (6,732 tokens)
3. `module-alpha.md` (6,204 tokens)
4. `module-beta.md` (6,198 tokens)
5. `module-gamma.md` (7,658 tokens)
6. `integration-layer.md` (5,532 tokens)
7. `compliance-requirements.md` (3,939 tokens)

**Files in Method-04 Y** (9 files, ~57K tokens):
- All of the above, plus:
8. `module-epsilon.md` (7,666 tokens) ← NEW
9. `module-phi.md` (7,639 tokens) ← NEW

### New Hypothesis: Y-Size Threshold

**Hypothesis**: Y has an absolute threshold (~40-50K tokens) beyond which phantom reads occur regardless of X.

Supporting evidence:
- Method-03 (Y=42K): 100% success across all X values
- Method-04 (Y=57K): 100% failure across all X values
- X values were identical between experiments
- T was unchanged

This reframes the model: it's not X + Y > T that triggers phantom reads, but Y > Y_threshold.

### Post-Analysis Context Deficit

Post-operation context was lower than expected X + Y, indicating content loss:

| Scenario | Expected (X + Y) | Actual Post-Analysis | Deficit |
|----------|------------------|----------------------|---------|
| Easy | 130K | 113-120K | 10-17K lost |
| Hard | 177K | 170-189K | 0-7K lost |

The Easy scenario showed MORE deficit despite having MORE headroom, suggesting phantom reads hit both scenarios equally.

### Experiment Brainstorming

Identified 11 experiments to test the refined hypothesis. Full details in `docs/experiments/planning/Post-Experiment-04-Ideas.md`.

**Tier 1 - Critical (Run First)**:
- **Experiment A**: Minimal X (Easy-0) - Test if Y threshold is absolute
- **Experiment B**: 8-File Y Threshold - Find exact cutoff (test Y=50K)
- **Experiment D**: Max X, Minimal Y - Test if hoisted content is safe

**Tier 2 - Important**:
- **Experiment F**: File Count vs Tokens - What triggers the threshold?
- **Experiment H**: Intentional Early Reset - Can we create safe windows?
- **Experiment K**: 1M Context Model - Does T matter at all?

**Tier 3 - Supporting**:
- Experiments C, E, G, I, J - Various refinements and diagnostics

### Key Questions for Next Phase

1. Is Y threshold absolute (independent of X)?
2. Where exactly is the Y threshold (42K-57K range)?
3. Is the trigger file count or token count?
4. Does hoisted content contribute to phantom reads?
5. Does T (context window) matter at all?

---

## Theory Status Summary (as of 2026-01-24)

| Theory | Status | Notes |
|--------|--------|-------|
| **Y-Size Threshold** | 🆕 HYPOTHESIS | Y alone may have ~40-50K ceiling |
| **X + Y Model** | ⚠️ CHALLENGED | Easy scenario failed despite X+Y < T |
| **Reset Timing** | ⚠️ VIOLATED | SINGLE_LATE predicted success, got failure |
| **Deferred Reads** | SUPPORTED | Multi-file agent reads can be deferred |
| **Headroom** | WEAKENED | X variation didn't affect outcomes |
| **Reset Count** | REFRAMED | Downstream indicator, not causal |
| **Clean Gap** | UNCERTAIN | May not apply when Y exceeds threshold |
| **Dynamic Pressure** | SUPPORTED | May explain batch read vulnerability |
| **Hoisting Limit** | CONFIRMED | ~25K tokens per hoisted file |

---

## Next Steps (Updated 2026-01-24)

### Immediate Actions (Tier 1 Experiments)

1. ✅ **Increase Hard scenario Y**: Added `module-epsilon.md` and `module-phi.md` - DONE
2. ✅ **Run validation trials**: Completed 8 trials - DONE (unexpected 100% failure)
3. **Run Experiment A**: Minimal X (Easy-0) to test if Y threshold is absolute
4. **Run Experiment B**: 8-File threshold test to narrow Y threshold range
5. **Run Experiment D**: Max X, Minimal Y to test hoisting safety

### Research Priorities

6. **Determine Y threshold**: Is it between 42K-50K or 50K-57K?
7. **Test file count vs token count**: Is the trigger quantity of files or total tokens?
8. **Test 1M context model**: Does T actually matter, or is threshold internal?

### Documentation

9. **Update Consolidated-Theory.md**: Reflect Y-Size Threshold hypothesis
10. **Update README**: Once theory is validated

See `docs/experiments/planning/Post-Experiment-04-Ideas.md` for full experiment details and execution plan.

---

## 2026-01-26: Token Accounting Clarification and Experiment Status Update

**Event**: Clarified token accounting terminology and updated experiment status following completion of 04A, 04D, 04K, and 04L.

### Token Accounting Reference

When discussing context consumption, we use the following terms consistently:

| Term | Definition | Example |
|------|------------|---------|
| **Baseline** | Harness overhead present in ALL sessions (system prompt, tools, etc.) | ~23K tokens |
| **Preload** | File tokens hoisted via `@` notation in setup commands | Varies by command |
| **Overhead** | Additional tokens observed beyond file content (~38-42% of preload) | Reading overhead, message formatting |
| **X (total)** | Total observed context after setup = Baseline + Preload + Overhead | Reported by `/context` |

**Setup Command Token Breakdown**:

| Command | Preload (file tokens) | Observed X (total) | Overhead |
|---------|----------------------|-------------------|----------|
| `/setup-none` | 0K | ~23K | 0K (no files) |
| `/setup-easy` | ~35K | ~73K | ~15K (43%) |
| `/setup-medium` | ~50K | ~92K | ~19K (38%) |
| `/setup-hard` | ~68K | ~120K | ~29K (43%) |

**Key Insight**: The `/setup-none` command has zero preload but still has the ~23K baseline that ALL sessions start with (harness system prompt, tools, etc.). This is why 04A reports X≈23K, not X=0.

### Completed Experiment Summary

| Experiment | X (total) | Y | Outcome | Key Finding |
|------------|-----------|---|---------|-------------|
| **04A** | ~23K (0 preload) | 57K (9 files) | 6/6 SUCCESS | Y=57K is safe when X is low |
| **04D** | ~150K (maxload) | 6K (1 file) | SUCCESS | High X is safe when Y is minimal |
| **04K** | Various | 57K (9 files) | 6/6 SUCCESS | 1M model avoids phantom reads |
| **04L** | ~150K (maxload) | 6K (1 file) | SUCCESS | Harness avoids redundant reads |
| **Method-04** | 73K-120K | 57K (9 files) | 8/8 FAILURE | High X + High Y = danger zone |

### Current Understanding

The X+Y interaction is the critical factor:
- **Low X + High Y** → SUCCESS (04A)
- **High X + Low Y** → SUCCESS (04D)
- **High X + High Y** → FAILURE (Method-04)

The transition point for X (when Y=57K) lies somewhere between 23K and 73K. Experiment-04M will explore this boundary by testing intermediate X values.

### Next Experiments

1. **04M** (X Boundary Exploration): Create `/setup-mid` (~50K X) and test with Y=57K
2. **04C/04F via Git Branch**: Restore pre-epsilon/phi state and test file count vs token count
3. **04G** (Sequential vs Parallel): Test accumulation rate hypothesis

---

## 2026-01-26: Documentation Reorganization and Investigation Infrastructure

**Event**: Restructured project documentation, refined theoretical framework, and created tools for systematic knowledge capture.

### Documentation Restructuring

As the project grew, `docs/core/` had become cluttered with documents of varying lifecycles—experiment results, theory documents, and methodology files mixed in with true core documents. A reorganization moved these into dedicated subdirectories:

- `docs/experiments/` — methodologies, results, planning documents, and analysis guides
- `docs/theories/` — theoretical framework documents (Consolidated-Theory, Headroom-Theory, Context-Reset-Analysis)
- `docs/mitigations/` — workaround documentation

The `docs/core/` directory was narrowed to documents that serve the project for its entire lifetime: PRD, Action-Plan, Investigation-Journal, Research-Questions, Design-Decisions, and the newly created Timeline.

The PRD.md was updated with directory structure guidance so future agents would understand the organization and maintain it.

### X+Y Interaction Model Refinement

A critical conceptual clarification emerged during discussion of next experiments. Multiple agents had been drifting toward "magic number hunting"—trying to find independent threshold values for X or Y in isolation. The User clarified that X and Y are *dependent on each other with respect to T*, and the investigation's goal is to understand their interaction surface, not to identify isolated thresholds.

The evidence supports this:
- Y=57K succeeds with X≈0 (04A) but fails with X=73K (Method-04)
- X=150K succeeds with Y=6K (04D) but X=73K fails with Y=57K (Method-04)
- X+Y=130K fails (Method-04 Easy) while X+Y=162K succeeds (Method-03 Hard)

Simple additive models (X + Y > T) are contradicted by the data. The interaction is more complex.

RQ-B8 was updated with an explicit research caution against hunting for independent threshold values.

### 1M Model Scoping Decision

The 1M context model was formally declared OUT OF SCOPE for further investigation. Experiment-04K had been a one-time diagnostic to confirm T is a relevant variable—not a direction to pursue. Multiple agents had suggested further 1M testing or framed it as a recommended workaround. Notes were added to both Post-Experiment-04-Ideas.md and Research-Questions.md (RQ-G4, RQ-G5) to prevent recurrence.

### Experiment-04D: Context Saturation Observation

During the Experiment-04D trials, the Hard+maxload scenario (X=150K from hoisting + 68K from setup-hard preload) pushed context to capacity. The harness responded by **erroring out with a context saturation message**—it could not execute `/analyze-wpd` because there was insufficient remaining context. Notably, this is the *correct* harness behavior: refusing to proceed rather than silently producing phantom reads.

This observation reinforced the distinction between:
- **Correct behavior**: Context full → explicit error → agent knows it failed
- **Phantom read behavior**: Context pressured → silent deferral/clearing → agent believes it read successfully

The Easy+maxload variant (lower base X) succeeded without phantom reads, confirming hoisting safety even at high total context.

### Experiment-04M Designed

To explore the X boundary where Y=57K transitions from safe to dangerous, Experiment-04M was designed:
- Create `/setup-mid` that preloads a single file (`operations-manual-standard.md`, 19.3K tokens) for X≈50K
- This fills the gap between `/setup-none` (X≈23K, SUCCESS with 04A) and `/setup-easy` (X≈73K, FAILURE with Method-04)
- Follow-up variants (`/setup-low` at X≈44K, `/setup-high` at X≈60K) planned based on results

A git branch approach was proposed for Experiments 04B/04C/04F—branching the repository and restoring the pre-epsilon/phi state rather than performing invasive surgical edits to remove cross-references.

### `/process-prompt-log` Command Created

To address the growing gap between raw investigation activity and documented knowledge, a new karpathy script was created: `/process-prompt-log`. This command takes a historical prompt log file as input and systematically extracts discoveries, experiments, and findings into the three core documentation files:

- `docs/core/Timeline.md` — concise chronological record
- `docs/core/Investigation-Journal.md` — detailed narrative
- `docs/core/Research-Questions.md` — RQ catalog and discovered behaviors

The command was designed to process the ~30 prompt log files that had accumulated over the project's lifetime, enabling systematic knowledge capture across multiple workscopes.

### Timeline Document Created

A new core document, `docs/core/Timeline.md`, was established to provide a concise, scannable chronological record of the investigation. Where the Investigation Journal provides detailed narratives, the Timeline serves as a quick reference for when specific experiments were run, what their outcomes were, and when key discoveries were made.

---

## 2026-01-27: Barebones Experiments and Version 2.1.20 Discovery

**Event**: Ran two experiment collections testing phantom reads in a stripped-down repository and on the latest Claude Code version.

### Motivation

Two outstanding questions motivated this work:

1. **Is the phantom reads bug WSD-specific?** The investigation had been conducted entirely within projects containing the WSD framework. WSD includes a hook-based file protection system (`.claude/hooks/protect_files.py`) and substantial documentation infrastructure. We needed to confirm that phantom reads occur independently of WSD.

2. **Does the latest Claude Code version still exhibit the bug?** The investigation had been locked to CC v2.1.6 since the issue was confirmed. Meanwhile, Claude Code had progressed to v2.1.20. Staying relevant required testing the current version.

### Barebones Repository Setup

Created a minimal repository containing only the files needed to execute Experiment-Methodology-04:

```
├── .claude/commands/     (5 command files: analyze-wpd, setup-easy/medium/hard/none)
├── CLAUDE.md             (generated via Claude Code /init)
├── docs/specs/           (12 specification files)
├── docs/wpds/            (pipeline-refactor.md)
└── src/collect_trials.py
```

Total: 20 files across 7 directories. No WSD framework, no hooks, no investigation infrastructure.

### Barebones-216 Results (CC v2.1.6)

Ran 5 trials using Experiment-Methodology-04 with `/setup-hard`:

| Trial ID | Outcome | Notes |
|----------|---------|-------|
| 20260127-092331 | **INVALID** | Protocol violation — agent skipped 3 of 8 required files |
| 20260127-092743 | FAILURE | 3 files affected |
| 20260127-093127 | FAILURE | ALL 9 files affected (catastrophic) |
| 20260127-093818 | FAILURE | 3 files affected |
| 20260127-094145 | FAILURE | 4 files affected |

**Result**: 4 FAILURE, 1 INVALID → **100% failure rate among valid trials**

**Key Finding**: Phantom reads reproduce in a barebones environment with no WSD framework, no hooks, and minimal project overhead. This definitively confirms the bug is NOT WSD-specific.

**Trial 092331 Reclassification**: Initially categorized as "success" based on self-report (the agent did not experience phantom reads). Detailed analysis revealed the agent failed to read 3 of the 8 explicitly listed spec files (module-alpha, module-beta, module-gamma), reducing Y below the danger threshold. This is a protocol violation, not evidence of a safe condition. The trial's lower peak context (160K vs 175K+ in valid trials) is a direct consequence of reading fewer files.

### Barebones-2120 Results (CC v2.1.20)

Upgraded to CC v2.1.20 and ran 5 trials with the same protocol:

| Trial ID | Outcome |
|----------|--------|
| 20260127-095002 | SUCCESS |
| 20260127-100209 | SUCCESS |
| 20260127-100701 | SUCCESS |
| 20260127-100944 | SUCCESS |
| 20260127-101305 | SUCCESS |

**Result**: 5 SUCCESS, 0 FAILURE (0% failure rate)

Additional unrecorded trials also showed unanimous success.

**Key Finding**: Our reliable repro case (Method-04 + `/setup-hard`) no longer triggers phantom reads on CC v2.1.20. Something changed between 2.1.6 and 2.1.20.

### Analysis of 2.1.20 Results

The unanimous success on 2.1.20 is an overwhelming signal that should not be attributed to chance. Several possible explanations were identified:

1. **Bug Fix**: Anthropic may have fixed the phantom reads issue entirely.
2. **Threshold Shift**: The "unaccounted" ~40% overhead on read operations may have been reduced through optimization, meaning our carefully tuned scenario no longer sufficiently pressures the context window.
3. **Mechanism Change**: The deferred read mechanism may have changed again (a potential "Era 3"), requiring updated detection methodology.
4. **Optimization Side-Effect**: An unrelated optimization may have incidentally prevented our specific trigger conditions.

We cannot yet rule out any of these explanations. The critical next step is to attempt re-establishing a failure repro case on 2.1.20 — if phantom reads can still be triggered with a larger payload, it's a threshold shift rather than a fix.

### Discovered Behaviors

Two notable behaviors were recorded from agent observations during these experiments:

**Hoisted File Injection Mechanism**: An agent's self-reflection during a Barebones trial revealed that files loaded via `@` notation in slash commands appear as full content in `<system-reminder>` blocks:

> "The four files loaded via the /setup-hard skill's @ references appeared as full content in `<system-reminder>` blocks, so those were actually available to me."

This explains the architectural immunity of hoisted content: `<system-reminder>` blocks are part of the system message structure, which is not subject to the context management that clears/persists tool results. This resolves RQ-A5 and RQ-C3.

**Transient "0% remaining" UI Warning**: The User has observed that during operation commands (`/analyze-wpd`), the Claude Code status bar occasionally flashes "0% remaining" briefly before disappearing. This is not captured in session logs. The hypothesis is that this transient warning signals a context reset in progress.

### New Investigation Goals

The 2.1.20 results introduce several new priorities:

1. **Re-establish failure repro on 2.1.20**: Increase the data payload beyond our current Method-04 tuning to test whether phantom reads can still be triggered on the newer build.
2. **Build search (2.1.6 → 2.1.20)**: Binary search through intermediate builds to identify precisely where the behavioral change occurred.
3. **Comparative analysis**: Closely examine token patterns, reset behavior, and deferred read handling between the Barebones-216 failures and Barebones-2120 successes — these are identical protocols differing only in CC version.
4. **Examine Barebones-216 catastrophic trial**: Trial 20260127-093127 saw 45 reads through 6+ levels of nested `<persisted-output>` redirects, with the agent fabricating an entire 12-point analysis with invented quotes — a detailed case study in phantom read confabulation.

### Analysis Planning

Created two analysis planning documents:
- `docs/experiments/planning/Barebones-216.md` — detailed analysis plan for the v2.1.6 barebones results
- `docs/experiments/planning/Barebones-2120.md` — detailed analysis plan for the v2.1.20 results

Both documents include the rationale, setup details, high-level results, research questions, and proposed analytical approaches for another agent to execute.

### Trial Data Pre-Processing

Ran `/update-trial-data` on all 10 trials across both collections, creating `trial_data.json` files for each.

### Implications for the Investigation

The 2.1.20 results represent a potential inflection point for the investigation. If Anthropic has fixed the underlying issue, our reproduction case becomes historical documentation. If this is merely a threshold shift, we need to recalibrate — similar to the journey from Experiment-Methodology-03 (100% success) to Experiment-Methodology-04 (100% failure through payload tuning).

The WSD hook question is resolved: the `.claude/hooks/protect_files.py` hook is NOT a contributor to phantom reads, since the barebones repo (without any hooks) reproduces at the same rate.

---

## 2026-01-28: Build Scan Experiment (v2.1.6 through v2.1.22)

**Event**: Executed the planned "Build Search" experiment, testing every available Claude Code build from 2.1.6 through 2.1.22 on the barebones repository using Experiment-Methodology-04 with `/setup-hard`.

### Motivation

The Barebones-2120 experiment (Jan 27) had shown a dramatic shift: our reliable 100% failure case on v2.1.6 produced 0% failure on v2.1.20. The planned response was a binary search through intermediate builds to identify where the behavioral change occurred. Instead of a binary search, a comprehensive scan of every available build was conducted.

### Methodology

Each build was installed via `cc_version.py --install <version>`, and trials were run using the standard Experiment-Methodology-04 protocol (`/setup-hard` followed by `/analyze-wpd`) in the barebones repository. Trial outcomes were categorized as:
- **Failure** (phantom reads self-reported)
- **Success** (no phantom reads self-reported)
- **Context limit reached** (session died before completing the operation)

### Results by Build

| Build | Trials | Failures | Successes | Context Limit | Notes |
|-------|--------|----------|-----------|---------------|-------|
| 2.1.6 | (prior) | (prior) | - | - | Known 100% failure |
| 2.1.7–2.1.12 | Multiple | 0 | 0 | ALL | Method-04 cannot execute |
| 2.1.13 | — | — | — | — | **Does not exist** (version skipped) |
| 2.1.14 | 3 | 0 | 0 | 3 | Context limit on all |
| 2.1.15 | 3 | 3 | 0 | 0 | First post-2.1.6 executable build |
| 2.1.16–2.1.19 | (noted) | Yes | — | — | Same behavior as 2.1.15 |
| 2.1.20 | 11 | 5 | 1 | 5 | Mixed results |
| 2.1.21 | 3 | 2 | 1 | 0 | Mixed; no context limits |
| 2.1.22 | 6 | 6 | 0 | 0 | 100% failure; no context limits |

### The "Dead Zone": Builds 2.1.7 through 2.1.14

Builds 2.1.7 through 2.1.12 consistently hit a context overflow error during the `/analyze-wpd` command, causing the session to die with a "0% memory" / "context full" message. This means our Experiment-Methodology-04 literally cannot execute on these builds — they fail before the trigger operation even begins.

Build 2.1.14 shows the same context limit behavior but begins to recover. Build 2.1.15 is the first build after 2.1.6 where the methodology can execute successfully.

The dead zone raises an important question: what changed in these intermediate builds that made context management more aggressive? This may be related to the same context management system that causes phantom reads, but with the opposite effect — instead of silently clearing content (phantom reads), the system refuses to proceed at all (context overflow).

### Revision of Barebones-2120 Findings

The prior Barebones-2120 study (Jan 27) found 0% failure across 5 trials on v2.1.20, leading to the conclusion that "Anthropic changed something" and our repro case no longer triggered. The larger 11-trial study in this build scan reveals a more nuanced picture:

- 5 failures (phantom reads confirmed)
- 1 success
- 5 context limit errors

The prior study's 5/5 success was likely a small-sample artifact. Build 2.1.20 still exhibits phantom reads — it just also frequently hits context limits, and the small prior sample happened to draw from the success/context-limit population without hitting any failures.

### Build 2.1.22: New Reliable Failure Case

Build 2.1.22 (the latest at time of testing) shows 100% failure (6/6 trials, all phantom reads) with zero context limit errors. This provides:

1. A **reliable failure case on a current build** (replacing v2.1.6 which was increasingly outdated)
2. Evidence that **phantom reads are NOT fixed** in the latest Claude Code version
3. A clean signal (no context limits muddying the data) for future analysis

### `/context` Command Behavior Changes

The build scan revealed that the `/context` command's behavior changed significantly across versions:

- **2.1.6 and earlier**: `/context` prints to the session chat normally
- **2.1.9**: `/context` changed to an interstitial dialog that doesn't persist in the chat log; described as "very buggy" with display issues
- **2.1.14**: `/context` restored to the original behavior (printing to session chat)
- **2.1.15 through 2.1.19**: `/context` prints its output **twice** to the session chat (double-print bug)
- **2.1.20**: Double-print bug fixed; `/context` returns to normal behavior

These changes are significant for our methodology, which relies on `/context` output to measure token consumption at key points. The interstitial behavior in 2.1.9 would make our methodology unusable on that build (context measurements wouldn't appear in exports).

### Context Limit Elimination in 2.1.21+

Across 18 total runs on builds 2.1.21 and 2.1.22, zero context overload errors were observed. This contrasts with 2.1.20 (5/11 context limits) and earlier builds (2.1.7–2.1.14 all context limits). Something changed between 2.1.20 and 2.1.21 that eliminated context overflow behavior — the harness appears to have become better at managing context without outright failure.

However, the phantom reads persist. This suggests the "fix" in 2.1.21+ was to the context overflow behavior, not to the phantom read behavior. The system now handles context pressure without crashing, but still silently defers/clears reads.

### Additional Observation: npm-to-Native Installer Transition

Starting with build 2.1.15, Claude Code began issuing a warning: "Claude Code has switched from npm to native installer." This is triggered by our `cc_version.py` script which installs via npm. The warning does not appear to affect CC's operation — all trials ran normally despite it.

### Trial Collections

Six new collections were created:
- `dev/misc/barebones-219` — 3 trials, v2.1.9 (all context limit)
- `dev/misc/barebones-2114` — 3 trials, v2.1.14 (all context limit)
- `dev/misc/barebones-2115` — 3 trials, v2.1.15 (all phantom read failures)
- `dev/misc/barebones-2120-2` — 11 trials, v2.1.20 (mixed)
- `dev/misc/barebones-2121` — 3 trials, v2.1.21 (mixed)
- `dev/misc/barebones-2122` — 6 trials, v2.1.22 (all phantom read failures)

Pre-processing via `/update-trial-data` was completed for barebones-2121 and barebones-2122. The other collections (barebones-219, barebones-2114, barebones-2115, barebones-2120-2) were not pre-processed during this session.

### Implications

1. **Phantom reads are NOT fixed** — Build 2.1.22 (latest) shows 100% failure rate
2. **The investigation can now target 2.1.22** — Provides a reliable, current-build failure case
3. **The dead zone (2.1.7–2.1.14) reveals context management evolution** — Builds went through aggressive-overflow → partial-recovery → phantom-reads phases
4. **Barebones-2120 findings are revised** — 0% failure was a sampling artifact; actual rate is ~45% failure (excluding context limits)
5. **Context limit elimination in 2.1.21+** — The harness improved at handling pressure, but phantom reads remain

---

## 2026-01-29: Build Scan Follow-Up and Discrepancy Investigation

**Event**: Documented the build scan results formally, identified a critical discrepancy in the Barebones-2120 data, and planned a new investigation to resolve it.

### Build Scan Results Documentation

The build-by-build timeline and results from the Jan 28 scan were formally documented in `docs/experiments/results/Experiment-04-BuildScan.md`. This document captures the full progression from 2.1.6 through 2.1.22, including the "dead zone" (2.1.7–2.1.14), the return to phantom-read behavior (2.1.15+), and the elimination of context limits in 2.1.21+.

The existing `docs/experiments/results/Barebones-2120-Analysis.md` was also updated with the revised findings from the larger 11-trial study, noting these as updates to preserve the original analysis (which was based on `dev/misc/repro-attempts-04-2120`).

### Barebones-2121 Success Reclassified

During review of the build scan data, the single "success" in `dev/misc/barebones-2121` was identified as a protocol violation — the agent did not follow the experiment protocol correctly, making the trial invalid. This is the same pattern seen in Barebones-216 trial 092331 (where an agent skipped required files, reducing Y below the danger threshold).

This reclassification is significant because it prevents the investigation from pursuing a red herring. Without this finding, the 2.1.21 success might have suggested that the build had some protective behavior that 2.1.22 lost — which is not the case.

### The Build-Scan Discrepancy Question

The most pressing question to emerge from the build scan analysis is: **Why did the original Barebones-2120 study (`dev/misc/repro-attempts-04-2120`, 5/5 success) differ so dramatically from the build-scan 2.1.20 results (`dev/misc/barebones-2120-2`, 5 failures/1 success/5 context limits)?**

Both test sets used the same protocol (Experiment-Methodology-04 with `/setup-hard`), the same barebones repository, and the same Claude Code build (2.1.20). The only difference was timing — the original study was run first, and the build-scan trials were run approximately 1 hour later within the same ~4-hour experimental window.

Several investigation approaches were considered:
- Compare `dev/misc/barebones-2122` to `dev/misc/repro-attempts-04-2120` to identify test environment changes
- Compare `dev/misc/barebones-2120-2` to `dev/misc/repro-attempts-04-2120` as an apples-to-apples v2.1.20 comparison
- Compare the single success in `dev/misc/barebones-2121` to its failures (though this was later invalidated as a protocol violation)

A key concern was raised: could Anthropic have made server-side changes within the 4-hour window that affected outcomes? This would have major implications for reproducibility across all experiments.

The investigation plan was formalized in `docs/experiments/planning/Build-Scan-Discrepancy-Investigation.md`, and a placeholder analysis document was created at `docs/experiments/results/Build-Scan-Discrepancy-Analysis.md` for progressive multi-session analysis.

### Pre-Processing of Barebones-2120-2 Trials

All 11 trials in `dev/misc/barebones-2120-2/` were pre-processed via `/update-trial-data`, creating `trial_data.json` files for each. This collection had been created during the Jan 28 build scan but had not been pre-processed at that time. Pre-processing is a prerequisite for the planned discrepancy analysis.

### Implications

The Build-Scan Discrepancy investigation was given priority over continuing the planned phantom read mechanism experiments (04B, 04F, 04M, etc.). The reasoning: if test results can vary significantly within hours due to external factors, any conclusions drawn from our experiments might be unreliable. Understanding whether this variability is environmental, server-side, or statistical is essential before investing further in detailed threshold analysis.

### Build-Scan Discrepancy Analysis Begins

The first four steps (1.1–1.4) of the Build-Scan Discrepancy investigation plan were executed against the `barebones-2120-2` trial data. The analysis proceeded session by session, with findings documented progressively in `docs/experiments/results/Build-Scan-Discrepancy-Analysis.md`. This multi-session analysis compares the `repro-attempts-04-2120` collection (5/5 success) against `barebones-2120-2` (5 failures, 1 success, 5 context limits) — both using the same CC build, protocol, and repository.

### Trial Data Schema 1.3 Upgrade

During the discrepancy analysis, agent review of the trial data revealed opportunities to improve the `trial_data.json` structure. This led to the design and execution of a Schema 1.3 upgrade:

**Design Phase**: A 10-point design discussion refined the schema changes. Key decisions included:
1. Renaming fields for accuracy
2. Adding `persisted_non_reads` so read type counts sum correctly
3. Clarifying expected file format notes
4. Adding structure definitions for sessions without sub-directories
5. Handling zero-reset edge cases
6. Updating guidance documentation to reflect new schema fields
7. Keeping `total_tokens_consumed` as a convenience alias

The upgrade was deliberately scoped as a self-contained ticket (`docs/tickets/open/upgrade-trial-data-schema-1-3.md`) and executed through a full WSD lifecycle. The implementation updated `dev/karpathy/extract_trial_data.py` and `.claude/commands/update-trial-data.md`.

An observation about `file_token_counts.json`: this manually-acquired token counts file was assessed as low-value during analysis (inflated counts from full-file-length counting instead of actual read portions). The existing code gracefully handles its absence by truncating the `token_analysis` section, so no removal was needed.

### Health Check Cleanup

Following the Schema 1.3 implementation, a health check revealed accumulated issues: 10 type checking errors, 6 doc completeness warnings, and 22 linting issues. All were resolved in a dedicated session, including 4 complex linting fixes that required careful refactoring.

### Mass Re-Processing

With Schema 1.3 in place, all build scan trial collections were re-processed via `/update-trial-data` to bring them up to the new schema:
- `dev/misc/repro-attempts-04-2120/` — 5 trials (v2.1.20, Round 1)
- `dev/misc/barebones-2120-2/` — 11 trials (v2.1.20, Round 2)
- `dev/misc/barebones-2121/` — 3 trials (v2.1.21)
- `dev/misc/barebones-2122/` — 6 trials (v2.1.22)

This ensures all trial data is on a consistent schema for the ongoing discrepancy analysis and future experiments.

---

## 2026-01-29 (Evening): Schema-13 Experiments and Task Agent Delegation Discovery

**Event**: Ran additional Method-04 trials on builds 2.1.20 and 2.1.22 using the barebones repository, discovering that Session Agent delegation of Read operations to Task sub-agents is a significant confounding variable in trial outcomes.

### Schema-13 Trial Collections

Two new collections were created during the evening session:

- **`dev/misc/schema-13-2120`** — 9 trials on CC v2.1.20. Results: 3 direct successes, 3 failures, 3 successes attributed to Task agent delegation.
- **`dev/misc/schema-13-2122`** — 6 trials on CC v2.1.22. Results: ALL 6 succeeded, with ALL trials using Task agent delegation.

Trial data was collected using `collect_trials.py` from the barebones repository and pre-processed via `/update-trial-data` with the newly upgraded Schema 1.3.

### Discovery: Task Agent Delegation

The most significant finding from this session was the identification of **Task agent delegation** as a confounding variable in trial outcomes. In some trials, the Session Agent did not directly read the specification files itself. Instead, it spawned Task sub-agents to perform the Read operations and report back.

The User's notes from the session capture this observation concisely:

> - Agents report delegating Read operations to "Task" agents in some (all?) successes in 2.1.20
> - ALL Trials delegated to "Task" agents in 2.1.22 (and therefore succeeded)

This behavioral pattern has profound implications for trial classification:

- **Direct-read trials**: The Session Agent reads files using the Read tool in its own context. These trials are subject to the normal phantom read mechanism.
- **Delegation trials**: The Session Agent spawns Task sub-agents to read files. Each sub-agent operates in its own context window, reading far fewer files than the full 9-file set. This structurally avoids the context pressure conditions that trigger phantom reads.

### 2.1.22 Success Reversal Explained

The schema-13-2122 results initially appeared to contradict the Jan 28 build scan finding of 100% failure on v2.1.22 (6/6 in `barebones-2122`). However, the delegation confound resolves this apparent contradiction: the Jan 29 trials succeeded not because the bug was fixed or server-side conditions changed, but because the Session Agents adopted a different behavioral pattern (delegation) that structurally avoids the trigger conditions.

This finding was subsequently integrated into the Build-Scan Discrepancy Analysis (`docs/experiments/results/Build-Scan-Discrepancy-Analysis.md`), where it became a central component of the investigation's conclusions.

### Implications

1. **Methodological**: Future trial analysis must classify trials as "direct-read" vs. "delegation" before drawing conclusions about phantom read rates. Aggregate success/failure rates that mix both types are misleading.
2. **Theoretical**: Task sub-agent reads may be structurally immune to phantom reads because each sub-agent operates in a fresh, small context window that never approaches the danger zone thresholds.
3. **Behavioral**: The tendency for agents to use delegation appears to vary across builds and potentially over time, introducing a non-deterministic behavioral variable into our experiments.

---

## 2026-01-30: Build-Scan Discrepancy Investigation Completed and Investigation Closure

**Event**: Completed all remaining steps of the Build-Scan Discrepancy investigation, formalized the Server-Side Variability Theory, and recommended closure of the experimental investigation phase.

### Build-Scan Discrepancy Analysis Completed

The multi-session Build-Scan Discrepancy Analysis was completed through all planned steps:

**Step 2.1 (schema-13-2120, 9 trials on v2.1.20)**: Confirmed that persistence behavior is non-deterministic within the same time window. Among direct-read trials on Jan 29, 80% (4/5) showed persistence — compared to 0% on Jan 27 (same build, same protocol). Sub-agent delegation was identified as a new confound: 4/9 trials used delegation, and all 4 succeeded. The original Barebones-2120 success pattern (Jan 27) was reproduced exactly once (trial 202633: 1/5 direct-read trials), confirming it was a statistically possible but unlikely event rather than a systematic difference.

**Step 2.2 (schema-13-2122, 6 trials on v2.1.22)**: Produced the investigation's most dramatic result — a complete reversal from 100% failure (Jan 28, `barebones-2122`) to 100% success (Jan 29). Zero trials showed tool result persistence. Sub-agent delegation appeared in 5/6 trials. Trial 211109 was especially significant: a direct-read trial that succeeded at 198K total input tokens with zero persistence — proving that even without delegation, the server-side persistence mechanism had changed. This single trial is the strongest evidence for a systemic server-side change.

**Step 2.3 (schema-13-216, 6 trials on v2.1.6)**: Extended the investigation to the oldest tested build, replacing the original Cross-Machine Replication step (which Phase 1 environmental analysis had rendered unnecessary). Results: 2 FAILURE (direct-read with persistence), 3 SUCCESS (delegation), 1 SUCCESS (recovery from `<persisted-output>`). Build 2.1.6 showed 50% delegation rate (3/6 trials) and 100% persistence among direct-read trials (3/3) — behaviorally indistinguishable from builds 2.1.20 and 2.1.22 tested the same day. This is the strongest evidence for server-side control: the oldest client build, whose code predates all other tested builds, behaves identically to the newest when tested under the same server conditions.

### Server-Side Variability Theory Formalized (Step 3.1)

The investigation's central finding was formalized as the Server-Side Variability Theory, documented in `docs/theories/Server-Side-Variability-Theory.md`. The core claim: phantom read occurrence is primarily determined by server-side state — not by client build version.

Two distinct server-side changes were identified between Jan 28 and Jan 29:

1. **Persistence mechanism change**: The harness persistence trigger was modified, substantially reducing the rate at which tool results are persisted to disk (the root cause of phantom reads).
2. **Model behavioral change**: The model began preferring sub-agent delegation for file reads, a strategy that independently avoids the persistence trigger by keeping main-session token accumulation low.

Together, these constitute a **mitigation, not a fix**. Persistence was still observed in 80–100% of direct-read trials on Jan 29, and the root cause — that persisted tool results are replaced by markers the model fails to follow up on — has not been addressed. The mitigation reduces exposure to the root cause rather than eliminating it.

The theory adds a critical dimension to the existing X+Y model from the Consolidated Theory: **T is not fixed.** The effective threshold varies based on server-side configuration. The revised model becomes: phantom reads occur when X + Y > T_effective(server_state) AND persistence is enabled for the session AND the agent does not recover from `<persisted-output>` markers.

### Build Scan Conclusions Revised (Step 3.2)

The original Build Scan conclusions from Jan 28 were reassessed against the server-side variability framework:

- **"Dead Zone" (2.1.7–2.1.14)**: Likely VALID as a client-side regression — these builds probably cannot handle the context load regardless of server state.
- **Build 2.1.22 as reproduction target**: INVALIDATED — 2.1.22's 100% failure was a Jan 28 server-state artifact, not a permanent build characteristic.
- **Build 2.1.20 as "fix"**: FULLY RESOLVED — the original 5/5 success was a small-sample artifact combined with a favorable server state on Jan 27.
- **Builds 2.1.15–2.1.19 failure rates**: Jan 28 server-state ARTIFACTS — cannot be treated as permanent failure rates.
- **No context overloads in 2.1.21+**: PARTIALLY VALID — likely reflects genuine client-side improvement, but needs confirmation under varied server states.

### Investigation Closure (Step 3.3)

The formal closure assessment concluded:

- Anthropic's mitigation is partial but significant — reduced persistence frequency and model delegation preference substantially reduce phantom read occurrence.
- Easy/Medium/Hard reproduction calibration (Aim #3) is **infeasible** under server-side variability — the server state changes the effective threshold, making fixed calibration impossible.
- Remaining planned experiments (04M, 04B, 04F, 04G, 04C) are **deprioritized** — server-side variability undermines the threshold analysis they were designed to perform.
- The investigation should redirect from experimental work to **documentation and public reporting**.

### Public Communication

With the investigation reaching its conclusion, preparation began for public-facing updates:

- A README.md update was proposed to reflect the latest findings for anyone following the investigation repository.
- A summary for GitHub Issue #17407 was drafted for posting to the original Anthropic issue, providing a three-week investigation update for the maintainers. This was considered time-sensitive, given that the mitigation effects had been observed in the preceding 12–24 hours and Anthropic had released four builds (2.1.23 through 2.1.26) in rapid succession — an unusually fast cadence suggesting active tuning.

### Implications

1. **The investigation has achieved its primary aims**: The phantom reads mechanism is well-understood (Aim #1), a reliable workaround exists via MCP Filesystem (Aim #2), analysis tools are mature (Aim #4), and while Aim #3 (calibrated reproduction) proved infeasible, the investigation produced extensive data and a comprehensive theoretical framework explaining why.
2. **No build is inherently "safe" or "unsafe"**: Build-specific failure rates reflect the server state at test time, not permanent build characteristics.
3. **The MCP Filesystem workaround remains the only reliable mitigation**: It bypasses the persistence mechanism entirely, regardless of server state.
4. **Sub-agent delegation is an emerging natural mitigation** but is not user-controllable — the model may or may not choose to delegate.

---

*Last updated: 2026-01-30*
