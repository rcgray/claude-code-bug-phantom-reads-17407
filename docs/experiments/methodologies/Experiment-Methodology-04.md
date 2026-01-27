# Experiment Methodology (Version 4.0)

This document describes the current methodology for investigating and reproducing the Phantom Reads bug in Claude Code. It supersedes `Experiment-Methodology-03.md`, which is preserved for historical reference.

## Overview

The methodology has evolved from Version 3.0 to address practical issues discovered during initial trial runs. The key insight driving this revision is that **the `/context` command cannot be called programmatically by agents**—it must be invoked explicitly by the user at specific points in the trial protocol. This version restructures the trial flow around explicit user-invoked context measurements.

### Key Changes from Version 3.0

1. **Scenario-Specific Initialization**: The `/wsd:getid` command is replaced with three scenario-specific commands that combine ID generation with context pre-loading:
   - `/setup-easy` - Easy scenario (targets ~37% pre-operation consumption)
   - `/setup-medium` - Medium scenario (targets ~46% pre-operation consumption)
   - `/setup-hard` - Hard scenario (targets ~60% pre-operation consumption)

2. **Unified Analysis Command**: The three scenario-specific analysis commands (`/analyze-light`, `/analyze-standard`, `/analyze-thorough`) are consolidated into a single `/analyze-wpd` command. Scenario differentiation now occurs during initialization, not during analysis.

3. **Explicit Context Measurements**: Three `/context` calls are now explicit user steps in the protocol, not embedded in commands:
   - **Baseline**: Immediately after session start
   - **Post-Preload**: After scenario initialization
   - **Post-Analysis**: After the analysis operation completes

4. **File Size Adjustments**: Several specification files were modified to fit within Claude Code's 25k token hoisting limit and achieve target context levels:
   - `operations-manual.md` split into `operations-manual-standard.md` (19,323 tokens) and `operations-manual-exceptions.md` (21,988 tokens)
   - `architecture-deep-dive.md` trimmed by removing appendices and Section E

### What Remains Unchanged

1. **Self-Report Detection**: Success/failure is still determined by Session Agent self-report
2. **Two-Era Model**: Phantom reads manifest via `[Old tool result content cleared]` (Era 1, builds ≤2.0.59) or `<persisted-output>` markers (Era 2, builds ≥2.0.60)
3. **Environment Setup**: Version pinning and auto-update disabling remain as documented
4. **Artifact Collection**: Trial artifacts are collected using the same tooling and organization
5. **Target WPD**: All scenarios use `docs/wpds/pipeline-refactor.md` as the analysis target

### Rationale for Changes

Initial trials with Version 3.0 revealed two critical issues:

1. **Hoisted File Loading Failures**: The original `operations-manual.md` exceeded Claude Code's 25k token limit for hoisted file reads. When hoisting failed, the file was silently ignored, causing all scenarios to pass trivially due to insufficient context consumption.

2. **Context Command Limitation**: The `/context` command is a Claude Code built-in that cannot be invoked programmatically by agents. The Version 3.0 design assumed context measurements could be embedded within scenario commands, which proved impossible.

The new design addresses both issues: files are sized to fit within hoisting limits, and context measurements are explicit protocol steps performed by the user.

## Environment Setup

Environment setup follows the same protocol as previous versions. For complete instructions, see `Experiment-Methodology-01.md` sections "Step 1: Disable Auto-Updates" and "Step 2: Install Target Version".

Summary:

1. Edit `~/.claude/settings.json` to set `DISABLE_AUTOUPDATER: "1"`
2. Uninstall current Claude Code: `npm uninstall -g @anthropic-ai/claude-code`
3. Clear npm cache: `npm cache clean --force`
4. Install target version: `npm install -g @anthropic-ai/claude-code@<version>`
5. Verify: `claude --version`

### Using the Version Management Script

The `cc_version.py` script automates the environment setup process:

```bash
# Disable auto-updates to prevent mid-trial version changes
./src/cc_version.py --disable-auto-update

# Install the target version for testing
./src/cc_version.py --install 2.1.6

# Verify your configuration before running trials
./src/cc_version.py --status

# ... run your trials ...

# Restore defaults when investigation is complete
./src/cc_version.py --reset
```

For complete documentation, see `docs/features/cc-version-script/CC-Version-Script-Overview.md`.

## Trial Protocol

Each trial follows this seven-step sequence with explicit user actions at each stage.

### Context Consumption Targets

The three scenarios target different pre-operation context consumption levels:

| Scenario | Command | Target Pre-Op | Expected Outcome |
|----------|---------|---------------|------------------|
| Easy | `/setup-easy` | ~37% (~73k tokens) | SUCCESS |
| Medium | `/setup-medium` | ~46% (~92k tokens) | MIXED |
| Hard | `/setup-hard` | ~60% (~120k tokens) | FAILURE |

**Observed measurements from calibration trials:**

```
After fresh session start (baseline):
- Total: ~24k tokens (12%)

After /setup-easy:
- Total: ~73k tokens (37%)

After /setup-medium:
- Total: ~92k tokens (46%)

After /setup-hard:
- Total: ~120k tokens (60%)
```

### Step 1: Measure Baseline Context

**Start a fresh Claude Code session** in the project directory, then immediately run:

```
/context
```

Record the baseline measurement. Expected: ~24k tokens (12%).

This establishes the **session baseline** before any commands execute.

### Step 2: Initialize Scenario

Run one of the scenario-specific initialization commands:

| Scenario | Command |
|----------|---------|
| Easy | `/setup-easy` |
| Medium | `/setup-medium` |
| Hard | `/setup-hard` |

The command will:
- Load scenario-specific specification files via `@file` references (hoisted reads)
- Generate a unique Workscope ID (format: `YYYYMMDD-HHMMSS`)
- Report the Workscope ID for artifact naming

**Record the Workscope ID.** This coordinates all trial artifacts.

### Step 3: Verify Pre-Operation Context

Run the context command to verify the scenario achieved its target:

```
/context
```

Record the pre-operation measurement. Compare against targets:
- Easy: ~73k tokens (37%)
- Medium: ~92k tokens (46%)
- Hard: ~120k tokens (60%)

If the measurement is significantly off-target, the trial may not produce valid results for its scenario category. Note any discrepancies.

### Step 4: Execute Analysis Operation

Run the unified analysis command against the target WPD:

```
/analyze-wpd docs/wpds/pipeline-refactor.md
```

**Allow the Session Agent to complete its analysis.** Do not interrupt or provide guidance during command execution.

The analysis command will:
- Read the target WPD
- Investigate related specifications
- Cross-reference with design decisions and documentation
- Report findings

### Step 5: Measure Post-Operation Context

Run the context command to capture final consumption:

```
/context
```

Record:
- Total tokens consumed
- Percentage of context used
- Delta from pre-operation measurement

### Step 6: Prompt for Self-Report

Disregard the Session Agent's analysis output. Prompt with the following:

```
We have recently seen a number of User Agents reporting issues reading files like the following:

<session-agent-response>
Looking back at my history, you're right. My first Read call for the file returned:

  <persisted-output>Tool result saved to: /Users/gray/.claude/projects/-Users-gray-Projects-workscope/dadf32a6-c83d-462d-b678-fbe7f191f42f/tool-results/toolu_019Nqx8qLWvdFSjvMsy5xFkM.txt

  Use Read to view</persisted-output>

  I did not follow up with a Read call to view that persisted output. I proceeded with my "investigation" without ever having actually read the file contents. I was operating completely blind, making assumptions about a document I never saw.

  The same thing happened with several other files at the start - WSD-Runtime-Metadata-Schema.md, WSD-Manifest-Schema.md, Manifest-Driven-Pipeline-Overview.md all returned <persisted-output> messages that I never followed up on
</session-agent-response>

I am debugging this recurring issue and I am checking to see if this particular session is a reproduction of this issue. Did you experience this during your execution of the command?
```

### Step 7: Record and Export Results

Based on the Session Agent's response, classify the trial:

- **SUCCESS**: Agent reports no phantom reads; all file content was received inline
- **FAILURE**: Agent confirms phantom reads; one or more files returned markers that were not followed up

Record additional details:
- Which files were affected (if reported)
- Agent's level of confidence in self-assessment
- Any anomalies or unexpected behavior
- Whether recovery was attempted

Export the chat session:

```
/export
```

Save the resulting `.txt` file to a location **outside the project directory**:

```
../cc-exports/{WORKSCOPE_ID}.txt
```

Example: `../cc-exports/20260123-143022.txt`

**IMPORTANT: Save exports OUTSIDE the project directory.** Chat exports saved within the project directory become visible to subsequent sessions through file listing operations, contaminating trial isolation.

## Post-Trial Processing

### Artifact Collection

After completing trials, use the collection script to organize artifacts:

```bash
./src/collect_trials.py -e ../cc-exports -d ./dev/misc/methodology-04-trials -v
```

The script:
- Scans the exports directory for chat export `.txt` files
- Extracts the Workscope ID from each export
- Locates corresponding session `.jsonl` files in `~/.claude/projects/`
- Copies all associated files to the destination
- Organizes artifacts into directories named by Workscope ID

### Trial Data Preprocessing

After collection, run the preprocessing tool for each trial:

```
/update-trial-data dev/misc/methodology-04-trials/{WORKSCOPE_ID}
```

Or batch process all trials:

```bash
for dir in ./dev/misc/methodology-04-trials/*/; do
    echo "Processing $dir"
    # Run /update-trial-data manually for each directory
done
```

The preprocessor creates a `trial_data.json` file containing:
- Context reset events with timing percentages
- File read operations with token counts
- Reset pattern classification
- Pre/post operation consumption metrics

## Scenario Design

### How Scenarios Control Outcomes

The scenarios differ only in their initialization phase, not their analysis phase:

| Scenario | Pre-Load Files | Target Pre-Op | Headroom |
|----------|----------------|---------------|----------|
| Easy | operations-manual (both parts) | ~37% | ~126k tokens |
| Medium | Easy + architecture-deep-dive | ~46% | ~108k tokens |
| Hard | Medium + troubleshooting-compendium | ~60% | ~80k tokens |

All three scenarios then execute identical analysis operations via `/analyze-wpd`.

### Pre-Load File Token Counts

The following files are loaded during scenario initialization:

| File | Tokens | Loaded By |
|------|--------|-----------|
| operations-manual-standard.md | ~19,323 | Easy, Medium, Hard |
| operations-manual-exceptions.md | ~21,988 | Easy, Medium, Hard |
| architecture-deep-dive.md | ~19,000 | Medium, Hard |
| troubleshooting-compendium.md | ~28,000 | Hard only |

### Why This Works

Based on the Reset Timing Theory (100% prediction accuracy on 31 trials from Version 2.0/3.0 methodology):

- **Easy**: High headroom (~126k) allows analysis to complete without mid-session resets
- **Medium**: Borderline headroom (~108k) may or may not trigger mid-session resets
- **Hard**: Low headroom (~80k) reliably triggers mid-session resets during analysis

The presence of any mid-session reset (50-90% through the session) is the critical failure predictor.

### Target Failure Rates

| Scenario | Target Failure Rate | Rationale |
|----------|---------------------|-----------|
| Easy | 0% | Sufficient headroom prevents mid-session resets |
| Medium | ~25-50% | Borderline headroom; outcome depends on session variance |
| Hard | ~75-100% | Insufficient headroom reliably triggers mid-session resets |

These targets are hypotheses to be validated through trials using this methodology.

## Current Theoretical Framework

### Reset Timing Theory (STRONGLY CONFIRMED)

The timing of context resets predicts phantom read occurrence with 100% accuracy across historical trials:

| Pattern | Description | Outcome |
|---------|-------------|---------|
| EARLY + LATE | First reset <50%, last >95%, no mid-session | 100% SUCCESS |
| SINGLE_LATE | Single reset >95% | 100% SUCCESS |
| MID-SESSION | Any reset between 50-90% of session | 100% FAILURE |

A "context reset" is detected when `cache_read_input_tokens` drops >10,000 tokens between consecutive assistant messages.

### Headroom Theory (SUPPORTED)

Starting context consumption ("headroom") correlates with reset timing:
- High headroom (>100K available) → resets occur at natural breakpoints
- Low headroom (<80K available) → resets occur mid-operation

```
Headroom = Context Window Size (200K) - Current Token Consumption
```

### Sustained Processing Gap Requirement

Successful trials exhibit a "clean gap" of ~35-40% of session duration where work proceeds uninterrupted between an early reset and a late reset. Failure occurs when this gap is fragmented by mid-session resets.

## Limitations

### Self-Report Reliability

The methodology relies on the Session Agent's ability to accurately introspect on its own tool call history. Known limitations:

1. **Model Incentives**: LLMs may be biased toward reporting success
2. **Introspection Accuracy**: Models may misremember or confabulate about past operations
3. **Non-Determinism**: Responses vary between runs independent of actual behavior
4. **Confirmation Bias**: The prompt explicitly describes the phenomenon, potentially priming reports

Despite these limitations, the strong correlation between self-reported outcomes and context reset patterns provides confidence that the methodology detects a real phenomenon.

### Context Command Limitation

The `/context` command is a Claude Code built-in that cannot be invoked programmatically by agents. This requires explicit user intervention at three points in the protocol, preventing full automation of trials.

### File Size Constraints

Claude Code imposes a ~25k token limit on hoisted file reads (files referenced via `@file` syntax). Files exceeding this limit are silently ignored, which caused all initial Version 3.0 trials to pass trivially. The specification files have been adjusted to fit within this limit, but this constraint limits the maximum context that can be pre-loaded through hoisting.

### Version Specificity

The theoretical framework was developed primarily on Claude Code version 2.1.6 with Opus 4.5. Results may differ on other versions or models, particularly across the Era 1/Era 2 boundary.

## Artifact Organization

Trial artifacts are organized by collection context:

```
dev/misc/
├── methodology-04-trials/        # Trials using this methodology
│   ├── 20260123-143022/
│   │   ├── 20260123-143022.txt   # Chat export
│   │   ├── {uuid}.jsonl          # Session file
│   │   ├── {uuid}/               # Session artifacts
│   │   │   ├── subagents/
│   │   │   └── tool-results/
│   │   └── trial_data.json       # Preprocessed analysis data
│   └── 20260123-152301/
├── methodology-03-trials/        # Historical collection (Version 3.0)
├── wsd-dev-02/                   # Historical collection (22 trials)
├── repro-attempts-02/            # Historical collection (9 trials)
└── example-sessions/             # Historical trials (Methodology 1.0)
```

## Quick Reference: Trial Checklist

```
[ ] 1. Start fresh session
[ ] 2. /context → Record baseline (~24k, 12%)
[ ] 3. /setup-{easy|medium|hard} → Record Workscope ID
[ ] 4. /context → Verify pre-op target reached
[ ] 5. /analyze-wpd docs/wpds/pipeline-refactor.md → Wait for completion
[ ] 6. /context → Record post-op consumption
[ ] 7. Prompt for self-report → Classify SUCCESS/FAILURE
[ ] 8. /export → Save to ../cc-exports/{WORKSCOPE_ID}.txt
```

## References

- `Experiment-Methodology-03.md` - Previous methodology version (superseded)
- `Experiment-Methodology-02.md` - Version 2.0 methodology (historical)
- `Experiment-Methodology-01.md` - Original investigation methodology (historical)
- `Investigation-Journal.md` - Chronological discovery log
- `WSD-Dev-02-Analysis-1.md` - Initial 7-trial analysis
- `WSD-Dev-02-Analysis-2.md` - Expanded 22-trial analysis
- `WSD-Dev-02-Analysis-3.md` - Token-based analysis
- `PRD.md` - Project overview
- GitHub Issue: https://github.com/anthropics/claude-code/issues/17407

---

*Version 4.0 - 2026-01-23*
