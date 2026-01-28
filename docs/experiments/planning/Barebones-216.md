# Barebones-216 Experiment Planning

**Experiment ID**: Barebones-216
**Collection**: `dev/misc/repro-attempts-04-barebones/`
**Date Conducted**: 2026-01-27
**Claude Code Version**: 2.1.6 (locked)
**Status**: ✅ COMPLETE - Analysis finalized

---

## Executive Summary

This experiment tests whether the Phantom Reads bug manifests in a minimal "barebones" environment stripped of all non-essential project infrastructure. By removing the Workscope-Dev (WSD) framework and all auxiliary files, we isolate the reproduction scenario to only the files necessary for triggering and observing phantom reads.

**High-Level Results**: 4 valid failures, 1 invalid trial (protocol violation) → **100% failure rate among valid trials**

This confirms phantom reads are a Claude Code harness issue, not an artifact of the WSD framework or our investigation repository's complexity.

---

## Background and Rationale

### The Phantom Reads Investigation Context

The Phantom Reads bug (Claude Code Issue #17407) causes the AI agent to believe it has successfully read file contents when it has not. The bug was first discovered in January 2026 and has been under systematic investigation using controlled experiments.

Prior to this experiment, all trials were conducted in either:
1. **The WSD Development project** - The original project where phantom reads were first encountered (77% natural failure rate)
2. **The Phantom Reads Investigation repository** - A dedicated research repository containing the WSD framework, extensive documentation, analysis tools, and experiment infrastructure

Both environments contain substantial "overhead" beyond what's strictly necessary for reproduction:
- WSD framework files (`docs/read-only/`, agent definitions, etc.)
- Investigation documentation (`docs/core/`, `docs/theories/`, etc.)
- Analysis scripts and tools (`src/`, `scripts/`)
- Hook systems (`.claude/hooks/protect_files.py`)
- Historical trial data (`dev/misc/`)

### Why a Barebones Test?

Several questions motivated this experiment:

1. **Is the bug WSD-specific?** Could some interaction between the WSD framework and Claude Code be causing or contributing to phantom reads?

2. **Does project complexity affect the bug?** The investigation repository has grown substantially. Does this complexity contribute to context pressure or other factors?

3. **Can we provide a minimal reproduction case?** For reporting to Anthropic and for other users to verify, a minimal example is more valuable than one requiring a complex framework.

4. **Does the WSD hook system contribute?** The `protect_files.py` hook intercepts Read operations. While it doesn't modify successful reads, could it be a confounding factor?

### Relationship to Prior Experiments

This experiment uses the same protocol as **Experiment-Methodology-04**, which established our first reliable "in the lab" reproduction of phantom reads. Specifically:

- **Method-04 on full repo**: 8/8 FAILURE (100% failure rate) with `/setup-hard` + `/analyze-wpd`
- **This experiment**: Same protocol, minimal environment

The comparison allows us to isolate environment effects while holding the protocol constant.

---

## Experimental Setup

### Environment Configuration

A new repository was created containing ONLY the files necessary to execute Experiment-Methodology-04:

```
barebones-phantom-reads/
├── .claude/
│   └── commands/
│       ├── analyze-wpd.md      # Unified analysis command
│       ├── setup-easy.md       # Low preload (~73K X)
│       ├── setup-hard.md       # High preload (~120K X)
│       ├── setup-medium.md     # Medium preload (~92K X)
│       └── setup-none.md       # Minimal preload (~23K X)
├── CLAUDE.md                   # Minimal, auto-generated via /init
├── docs/
│   ├── specs/                  # Specification files (hoisted as X)
│   │   ├── architecture-deep-dive.md
│   │   ├── compliance-requirements.md
│   │   ├── data-pipeline-overview.md
│   │   ├── integration-layer.md
│   │   ├── module-alpha.md
│   │   ├── module-beta.md
│   │   ├── module-epsilon.md
│   │   ├── module-gamma.md
│   │   ├── module-phi.md
│   │   ├── operations-manual-exceptions.md
│   │   ├── operations-manual-standard.md
│   │   └── troubleshooting-compendium.md
│   └── wpds/
│       └── pipeline-refactor.md  # Target WPD for analysis
└── src/
    └── collect_trials.py       # Trial collection utility

7 directories, 20 files
```

**What was REMOVED** (compared to full investigation repo):
- All WSD framework files (`docs/read-only/`, agent definitions, etc.)
- All investigation documentation (`docs/core/`, `docs/theories/`, etc.)
- All experiment results and analysis (`docs/experiments/results/`)
- All historical trial data (`dev/misc/`)
- The `protect_files.py` hook system (`.claude/hooks/`)
- MCP Filesystem configuration (`.mcp.json`)
- Project-level permission denials (`.claude/settings.local.json`)

**What was RETAINED**:
- The 12 spec files that comprise the preload content (X)
- The target WPD for analysis
- The setup and analysis commands
- The trial collection utility

### Protocol

The standard Experiment-Methodology-04 7-step protocol was followed:

1. Start fresh Claude Code session
2. Run `/context` (baseline measurement)
3. Run `/setup-hard` (preload ~120K tokens)
4. Run `/context` (post-setup measurement)
5. Run `/analyze-wpd docs/wpds/pipeline-refactor.md` (trigger operation)
6. Run `/context` (post-analysis measurement)
7. Self-report prompt (query Session Agent report of phantom read occurrence)
8. Export chat and collect trial artifacts

### Variables

| Variable            | Value        | Notes                             |
| ------------------- | ------------ | --------------------------------- |
| X (pre-op context)  | ~120K tokens | Via `/setup-hard` hoisting        |
| Y (operation files) | ~57K tokens  | 9 spec files read during analysis |
| T (context window)  | 200K tokens  | Standard model                    |
| Claude Code version | 2.1.6        | Locked via `cc_version.py`        |

---

## Results Summary

| Trial ID        | Outcome     | Notes                                         |
| --------------- | ----------- | --------------------------------------------- |
| 20260127-092331 | **INVALID** | Protocol violation - agent skipped 3 files    |
| 20260127-092743 | FAILURE     | Expected                                      |
| 20260127-093127 | FAILURE     | Expected                                      |
| 20260127-093818 | FAILURE     | Expected                                      |
| 20260127-094145 | FAILURE     | Expected                                      |

**Valid Trial Failure Rate**: 100% (4/4)

**Note on Trial 092331**: This trial was initially recorded as a "success," but analysis revealed it was a **protocol violation**—the agent failed to read 3 of the 8 files explicitly listed in the `/analyze-wpd` command's "Suggested Documentation." This is analogous to a human researcher failing to follow the experimental protocol; the trial is invalid and excluded from the failure rate calculation.

**Additional Validation**: The User ran 4 additional informal trials beyond these 5 to confirm the pattern. All showed unanimous failure.

### Comparison to Prior Data

| Environment                          | Protocol                              | Failure Rate      |
| ------------------------------------ | ------------------------------------- | ----------------- |
| Full investigation repo (Method-04)  | setup-hard + setup-easy + analyze-wpd | 100% (8/8)        |
| **Barebones repo (this experiment)** | setup-hard + analyze-wpd              | **100% (4/4)**    |
| WSD Development project              | /refine-plan                          | 77% (17/22)       |

The barebones environment shows a failure rate identical to the full repo when the protocol is followed correctly. The 77% rate in WSD Development represents "natural" occurrence without controlled setup.

---

## Research Questions

### RQ-BB216-1: Does removing WSD framework eliminate phantom reads?

**Status**: ✅ ANSWERED - **NO**

**Finding**: Phantom reads occur at 100% rate in the barebones environment (among valid trials). This confirms the bug is a Claude Code harness issue, not a WSD interaction.

**Significance**: High. This validates our entire investigation approach and confirms the bug affects all Claude Code users, not just WSD users.

### RQ-BB216-2: How does barebones context consumption compare to the full repo?

**Status**: ✅ ANSWERED

**Finding**: Barebones has ~3-4k tokens lower baseline overhead (20k vs 23k) due to reduced project complexity. This difference is negligible (~2% of context window) and has no effect on phantom read occurrence—both environments show 100% failure rate.

### RQ-BB216-3: Why did trial 20260127-092331 "succeed"?

**Status**: ✅ ANSWERED - **Protocol Violation**

**Finding**: Trial 092331 did NOT succeed. The agent failed to follow the experimental protocol by skipping 3 of 8 explicitly listed files (`module-alpha.md`, `module-beta.md`, `module-gamma.md`). This is a protocol violation that invalidates the trial, not evidence of variability in Y or the experimental conditions.

**Key Insight**: The original conclusion that "Y is non-deterministic" was incorrect. All operations involving LLMs have baseline non-determinism, but this rare protocol failure doesn't indicate Y has special variability. When the protocol is followed correctly, Y is effectively deterministic and phantom reads occur at 100% rate.

**Analogy**: Concluding that Y is non-deterministic from this single malfunction would be like concluding humans have a non-deterministic number of eyes because birth defects exist—technically true but misleading.

### RQ-BB216-4: Does the `protect_files.py` hook contribute to phantom reads?

**Status**: ✅ ANSWERED - **NO**

**Finding**: Both environments show identical 100% failure rates (full repo with hook: 8/8, barebones without hook: 4/4). The hook neither causes nor contributes to phantom reads.

### RQ-BB216-5: Do standard theory predictions hold in the barebones environment?

**Status**: ✅ ANSWERED - **YES**

**Finding**: All standard theory predictions hold:
- **Reset Timing Theory**: All failures show mid-session resets (50-90%)
- **X+Y Interaction**: All failures occur at expected context levels
- **Deferred Reads**: All failures have `has_tool_results: true`
- **Self-Report Accuracy**: 100% accurate across all trials

---

## Deliverables

1. ✅ **Analysis document**: `docs/experiments/results/Barebones-216-Analysis.md`
2. ⏳ **Investigation Journal update**: Pending
3. ⏳ **Research Questions update**: Pending
4. ❌ **Hook contribution follow-up**: Not needed (RQ-BB216-4 answered)

---

## Dependencies and Prerequisites

**Required files for analysis**:
- `dev/misc/repro-attempts-04-barebones/*/trial_data.json` (5 files)
- `dev/misc/repro-attempts-04-barebones/*/chat-export.md` (5 files)
- `dev/misc/repro-attempts-04-firstrun/*/trial_data.json` (for comparison)

**Required context**:
- `docs/experiments/methodologies/Experiment-Methodology-04.md`
- `docs/experiments/guides/Trial-Analysis-Guide.md`
- `docs/theories/Consolidated-Theory.md`
- `docs/core/Research-Questions.md`

---

## Document History

- **2026-01-27**: Initial creation
- **2026-01-27**: Updated to reflect correct interpretation of trial 092331 as protocol violation; changed official failure rate to 100% (4/4); marked all RQs as answered
