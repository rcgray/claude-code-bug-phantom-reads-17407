# Barebones-216 Experiment Planning

**Experiment ID**: Barebones-216
**Collection**: `dev/misc/repro-attempts-04-barebones/`
**Date Conducted**: 2026-01-27
**Claude Code Version**: 2.1.6 (locked)
**Status**: Trials complete, analysis pending

---

## Executive Summary

This experiment tests whether the Phantom Reads bug manifests in a minimal "barebones" environment stripped of all non-essential project infrastructure. By removing the Workscope-Dev (WSD) framework and all auxiliary files, we isolate the reproduction scenario to only the files necessary for triggering and observing phantom reads.

**High-Level Results**: 4 failures, 1 success (80% failure rate)

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

| Trial ID        | Outcome     | Notes                                |
| --------------- | ----------- | ------------------------------------ |
| 20260127-092331 | **SUCCESS** | Unexpected - first ever Hard success |
| 20260127-092743 | FAILURE     | Expected                             |
| 20260127-093127 | FAILURE     | Expected                             |
| 20260127-093818 | FAILURE     | Expected                             |
| 20260127-094145 | FAILURE     | Expected                             |

**Failure Rate**: 80% (4/5)
**Success Rate**: 20% (1/5)

**Additional Validation**: The User ran additional informal trials beyond these 5 to confirm the pattern. All showed unanimous failure.

### Comparison to Prior Data

| Environment                          | Protocol                              | Failure Rate  |
| ------------------------------------ | ------------------------------------- | ------------- |
| Full investigation repo (Method-04)  | setup-hard + setup-easy + analyze-wpd | 100% (8/8)    |
| **Barebones repo (this experiment)** | setup-hard + analyze-wpd              | **80% (4/5)** |
| WSD Development project              | /refine-plan                          | 77% (17/22)   |

The barebones environment shows a failure rate consistent with, though slightly lower than, the full repo. The single success is notable (possibly a fluke) and warrants investigation.

---

## Research Questions

### RQ-BB216-1: Does removing WSD framework eliminate phantom reads?

**Status**: ANSWERED - NO

**Finding**: Phantom reads occur at 80% rate even without WSD framework. This confirms the bug is a Claude Code harness issue, not a WSD interaction.

**Significance**: High. This validates our entire investigation approach and confirms the bug affects all Claude Code users, not just WSD users.

### RQ-BB216-2: How does barebones context consumption compare to the full repo?

**Status**: OPEN - Requires analysis

**Hypothesis**: The barebones environment should have lower baseline context consumption since there's less project content for the harness to consider.

**Analysis approach**:
1. Extract X values (post-setup context) from all 5 trials
2. Compare to Method-04 trials from `dev/misc/repro-attempts-04-firstrun/`
3. Calculate the "hidden overhead" difference

**Expected metrics**:
- Baseline (fresh session): Should be similar (~23K) as this is harness overhead
- Post-setup X: May be lower if project complexity adds overhead
- Y (operation): Should be identical (same files read)

**Why this matters**: If barebones has significantly lower overhead, it suggests our investigation repo adds context pressure. This could affect threshold calculations and scenario tuning.

### RQ-BB216-3: Why did trial 20260127-092331 succeed?

**Status**: OPEN - Requires analysis

**Significance**: This is the FIRST SUCCESS ever observed in Experiment-Methodology-04. All prior Hard and Easy trials (8/8 in Method-04 firstrun) failed.

**Hypothesis options**:
1. Different reset timing pattern (EARLY_PLUS_LATE vs SINGLE_LATE)
2. Lower actual X or Y due to measurement variance
3. Agent behavioral difference (sequential vs parallel reads)
4. Statistical variance in a stochastic system

**Analysis approach**:
1. Extract full metrics from `trial_data.json`
2. Compare reset patterns to the 4 failures
3. Examine chat export for behavioral differences
4. Look for any "near miss" indicators in failures

### RQ-BB216-4: Does the `protect_files.py` hook contribute to phantom reads?

**Status**: OPEN - Requires follow-up experiment

**Background**: The WSD framework includes a PreToolUse hook (`protect_files.py`) that intercepts Read operations to block sensitive file access. While this hook doesn't modify successful reads, it does add a processing layer.

**Current finding**: Barebones (no hook) still shows 80% failure rate, so the hook is NOT the cause of phantom reads.

**Remaining question**: Could the hook be a *contributor* that increases failure rate? The full repo showed 100% failure vs barebones 80%.

**Proposed follow-up**: Import `protect_files.py` into barebones repo and run additional trials to see if failure rate increases.

### RQ-BB216-5: Do standard theory predictions hold in the barebones environment?

**Status**: OPEN - Requires analysis

**Theories to validate**:
1. **Reset Timing**: Do failures show mid-session resets (50-90%)?
2. **X+Y Interaction**: Is X+Y > some threshold in failures?
3. **Deferred Reads**: Are phantom reads associated with batch read operations?
4. **Self-Report**: Do agents correctly identify phantom reads when they occur?

**Analysis approach**: Apply standard analysis methodology from `docs/experiments/guides/Trial-Analysis-Guide.md` to all 5 trials.

---

## Analysis Methodology

### Phase 1: Pre-Processing (COMPLETED)

The `/update-trial-data` command has been run on all trials, generating `trial_data.json` files with:
- Context measurements (X, Y, totals)
- Reset patterns and timing
- File read sequences
- Self-report outcomes

### Phase 2: Quantitative Analysis

For each trial, extract and tabulate:

| Metric              | Source            | Purpose                       |
| ------------------- | ----------------- | ----------------------------- |
| Baseline context    | `/context` output | Harness overhead              |
| Post-setup X        | `/context` output | Pre-operation consumption     |
| Post-analysis total | `/context` output | X + Y verification            |
| Reset count         | `trial_data.json` | Reset theory validation       |
| Reset positions (%) | `trial_data.json` | Timing pattern classification |
| Files read          | `trial_data.json` | Y composition                 |
| Phantom read count  | Self-report       | Outcome verification          |

**Cross-collection comparison**: Create side-by-side table comparing Barebones-216 trials to Method-04 firstrun trials.

### Phase 3: Qualitative Analysis

**For the success trial (092331)**:
1. Read full chat export
2. Identify any behavioral differences from failure trials
3. Look for evidence of actual file content receipt
4. Check for unusual patterns or agent decisions

**For failure trials**:
1. Verify `<persisted-output>` markers in agent experience
2. Check self-report accuracy
3. Note any partial successes or recovery attempts

### Phase 4: Synthesis

1. Confirm/refute each research question
2. Document findings for Investigation Journal
3. Update Research-Questions.md with new findings
4. Identify any new questions raised by the data

---

## Expected Deliverables

1. **Analysis document**: `docs/experiments/results/Barebones-216-Analysis.md`
2. **Investigation Journal update**: New entry documenting findings
3. **Research Questions update**: Status changes for relevant RQs
4. **Potential follow-up experiment design**: If hook contribution question warrants testing

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
