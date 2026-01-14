# Feature Brief: Session Analysis Scripts

**Date**: 2026-01-12
**Prepared by**: User Agent (Workscope-20260112-155453)
**For**: Feature-Writer Agent

---

## Executive Summary

A suite of tools for capturing, collecting, and analyzing Claude Code session logs to programmatically detect phantom read occurrences across multiple trial sessions, providing objective evidence beyond AI self-reporting.

---

## Problem Statement

The Phantom Reads Investigation project needs to detect when Claude Code returns `<persisted-output>` markers instead of actual file content, and the agent proceeds without making follow-up reads. Currently, detection relies on AI self-reporting, which has inherent limitations (model incentives, introspection accuracy, non-determinism). We need programmatic detection that examines session logs directly.

Additionally, investigators need a streamlined workflow to:
1. Mark sessions as bona fide trials (vs. other project work)
2. Optionally export human-readable chat logs
3. Collect and match session files with their exports
4. Analyze results across multiple trials and Claude Code versions

---

## Solution Overview

A three-component solution:

1. **`/start-trial` Command**: A Claude Code custom command that generates a unique Trial Identifier (`YYYYMMDD-HHMMSS`) and embeds it in the session. This marker validates sessions as trials and enables matching between `.jsonl` files and chat exports.

2. **`collect_trials.py` Script**: Scans `~/.claude/projects/` for session files containing Trial Identifiers, scans `exports/` for matching chat exports, and copies matched pairs (or lone `.jsonl` files) to `results/` with standardized naming.

3. **`analyze_trials.py` Script**: Parses all `.jsonl` files in `results/`, detects phantom reads programmatically, extracts Claude Code version, and outputs an aggregated summary report showing trials and failures by version.

---

## Relationship to Existing Systems

### Related to `scripts/archive_claude_sessions.py`
The existing archive script provides patterns for:
- Locating `~/.claude/projects/` directory
- Iterating through project subdirectories
- Working with `.jsonl` session files

The new scripts will use similar patterns but with different purposes (trial collection vs. general archival).

### Related to `docs/core/Experiment-Methodology.md`
The methodology document describes the current manual trial process. This feature updates that workflow to include:
- Running `/start-trial` after `/wsd:init --custom`
- Optionally running `/export` and saving to `exports/`
- Running `collect_trials.py` and `analyze_trials.py` after trials complete

### Related to `docs/core/Action-Plan.md`
Phase 4 ("Analysis Tools") in the Action Plan will be replaced by a reference to this Feature Overview once created. The detailed implementation tasks will live in this feature's FIP.

### Sample Files for Reference
Investigation 1 produced sample files in `dev/misc/` that implementers should reference:
- `sample-session.jsonl` - Main session file structure
- `sample-agent.jsonl` - Sub-agent file structure (linked via `sessionId`)
- `sample-export.txt` - Chat export format

---

## Deliverables

### 1. New File: `.claude/commands/start-trial.md`
Claude Code custom command that:
- Runs the `date` command to get current timestamp
- Outputs `Trial Identifier: YYYYMMDD-HHMMSS` as the final line of response
- Format must match exactly for regex parsing by collection script

### 2. New File: `scripts/collect_trials.py`
Python script that:
- Derives this project's session directory from `cwd` (replace `/` with `-`, prepend `-`)
- Scans `.jsonl` files in that directory for `Trial Identifier: YYYYMMDD-HHMMSS` pattern
- Scans `exports/` directory for `.txt` files containing matching Trial Identifiers
- Copies matched pairs to `results/` as `trial-YYYYMMDD-HHMMSS.jsonl` and `trial-YYYYMMDD-HHMMSS.txt`
- Copies unmatched `.jsonl` trials (no export) as lone files
- Is idempotent: skips trials already present in `results/`
- Reports what was collected and matched

### 3. New File: `scripts/analyze_trials.py`
Python script that:
- Scans `results/` directory for `.jsonl` files
- For each file:
  - Extracts Claude Code version from `version` field
  - Detects phantom reads: `<persisted-output>` responses without follow-up reads
- Aggregates results by version
- Outputs summary report to stdout in format:
  ```
  Claude Code Phantom Reads Analysis
  ==================================

  Version    Trials    Failures    Rate
  -------    ------    --------    ----
  2.0.54     4         0           0%
  2.0.58     4         0           0%
  2.0.59     4         2           50%
  ...

  ------------------------------------------
  Total (up to 2.0.58):    12 trials, 0 failures (0%)
  Total (2.0.59+):         10 trials, 7 failures (70%)
  ```

### 4. New Directory: `exports/`
Empty directory where investigators save `/export` output (any filename, `.txt` format).

### 5. New Directory: `results/`
Empty directory where collected trial data is stored with standardized naming.

### 6. Updates: `docs/core/Experiment-Methodology.md`
Update the "Trial Execution" section to document the new workflow:
1. `/wsd:init --custom`
2. `/start-trial` (NEW)
3. `/refine-plan docs/tickets/open/<trigger-ticket>.md`
4. Prompt for self-report
5. `/export` (optional) - save to `exports/`
6. Exit Claude Code
7. Run `python scripts/collect_trials.py`
8. Run `python scripts/analyze_trials.py`

### 7. Updates: `docs/core/Action-Plan.md`
Replace Phase 4 content with a reference to this Feature Overview:
```
## Phase 4: Analysis Tools

- [ ] **4.1** - Implement session analysis scripts (see docs/features/session-analysis-scripts/Session-Analysis-Scripts-Overview.md)
```

---

## Design Constraints

### Trial Identifier Format
- Must be exactly `Trial Identifier: YYYYMMDD-HHMMSS`
- Scripts use regex to find FIRST occurrence in a file
- No support for multiple trials per session (investigators expected to use one trial per session)

### Project Directory Derivation
- `cwd` → replace `/` with `-` → prepend `-` → subdirectory name under `~/.claude/projects/`
- Example: `/Users/gray/Projects/claude-code-bug-phantom-reads-17407` → `-Users-gray-Projects-claude-code-bug-phantom-reads-17407`

### Phantom Read Detection Logic
A phantom read occurs when:
1. A Read tool invocation returns a response containing `<persisted-output>` marker
2. The persisted file path from the marker is NOT subsequently read in the same session

### Version Extraction
- `.jsonl` files: Extract `version` field from message lines (e.g., `"version":"2.0.58"`)
- `.txt` exports: Version in header line `Claude Code v2.0.58` (for human reference only; scripts analyze `.jsonl`)

### Idempotency
- `collect_trials.py`: Skip if `trial-YYYYMMDD-HHMMSS.jsonl` already exists in `results/`
- `analyze_trials.py`: Always regenerates report from current `results/` contents

### Agent Files
- Sub-agent files (`agent-*.jsonl`) contain `sessionId` linking to parent session
- Phantom reads in sub-agent contexts should be included in analysis
- The Trial Identifier appears in the main session file, not agent files

---

## Out of Scope

- **Parsing chat exports programmatically**: Self-report comparison remains manual
- **Real-time monitoring**: Scripts run after trials complete, not during
- **Automated trial execution**: Investigators manually run trials
- **Cross-project analysis**: Scripts analyze only this project's sessions
- **Production hardening**: Scripts are convenience tools for investigators, not hardened against bad actors

---

## Success Criteria

1. Running `/start-trial` in Claude Code outputs a unique Trial Identifier
2. Running `collect_trials.py` correctly identifies trial sessions and matches them with exports
3. Running `analyze_trials.py` correctly detects phantom reads and produces accurate version-aggregated statistics
4. The workflow is documented clearly enough that investigators can follow it without additional guidance
5. Scripts are idempotent and can be run multiple times safely

---

## Implementation Notes

### File Counts
- 1 new command file
- 2 new Python scripts
- 2 new directories (empty, with `.gitkeep`)
- 2 documentation updates

### Reference Files
Implementers should examine these files in `dev/misc/`:
- `sample-session.jsonl` - Shows message structure, `version` field location, how tool calls appear
- `sample-agent.jsonl` - Shows `sessionId` linkage, `isSidechain` flag
- `sample-export.txt` - Shows header format with version

### Existing Code Reference
- `scripts/archive_claude_sessions.py` - Patterns for session directory access

### Regression Boundary
The summary report specifically separates "up to 2.0.58" (pre-regression) from "2.0.59+" (post-regression) based on investigation findings documented in `docs/core/PRD.md`.

---

## Questions for Feature-Writer

None - this brief captures all design decisions from the discovery conversation.
