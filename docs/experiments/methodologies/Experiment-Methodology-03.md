# Experiment Methodology (Version 3.0)

This document describes the current methodology for investigating and reproducing the Phantom Reads bug in Claude Code. It supersedes `Experiment-Methodology-02.md`, which is preserved for historical reference.

## Overview

The methodology has evolved from Version 2.0 to incorporate learnings from 31 trials across two collections (wsd-dev-02 and repro-attempts-02). The key insight driving this revision is that **pre-operation context consumption** is the critical variable for controlling phantom read occurrence, not the complexity of the trigger operation itself. This version introduces streamlined initialization and scenario-targeted analysis commands.

### Key Changes from Version 2.0

1. **Simplified Initialization**: The `/wsd:init --custom` command is replaced with `/wsd:getid`, which generates a Workscope ID without the full WSD platform onboarding overhead
2. **Scenario-Targeted Triggers**: The single `/refine-plan` command is replaced with three scenario-specific commands that control pre-operation context consumption:
   - `/analyze-light` - Easy scenario (targets <40% pre-op consumption)
   - `/analyze-standard` - Medium scenario (targets 40-50% pre-op consumption)
   - `/analyze-thorough` - Hard scenario (targets >50% pre-op consumption)
3. **Unified Target WPD**: All scenarios use `docs/wpds/pipeline-refactor.md` as the analysis target, with the scenario commands controlling context consumption through their onboarding behavior
4. **Theory-Informed Design**: Scenario designs are based on the Reset Timing Theory (100% prediction accuracy on 31 trials) and findings about onboarding read volume as the key trigger variable

### What Remains Unchanged

1. **Self-Report Detection**: Success/failure is still determined by Session Agent self-report
2. **Two-Era Model**: Phantom reads manifest via `[Old tool result content cleared]` (Era 1, builds ≤2.0.59) or `<persisted-output>` markers (Era 2, builds ≥2.0.60)
3. **Environment Setup**: Version pinning and auto-update disabling remain as documented
4. **Artifact Collection**: Trial artifacts are collected using the same tooling and organization

### Rationale for Changes

Analysis of the repro-attempts-02 collection revealed that the original reproduction scenarios differentiated by spec content volume, but the real trigger is **onboarding context consumption BEFORE the trigger fires**. The single failure case (20260121-202919) succeeded in triggering phantom reads not because of WPD complexity, but because it read more files during onboarding (19 vs 6-11), pushing pre-op consumption from ~36% to 54%.

The new scenario commands internalize this insight: they differentiate by how much context they consume during their execution, not by what they analyze.

## Environment Setup

Environment setup follows the same protocol as previous versions. For complete instructions, see `Experiment-Methodology-01.md` sections "Step 1: Disable Auto-Updates" and "Step 2: Install Target Version".

Summary:

1. Edit `~/.claude/settings.json` to set `DISABLE_AUTOUPDATER: "1"`
2. Uninstall current Claude Code: `npm uninstall -g @anthropic-ai/claude-code`
3. Clear npm cache: `npm cache clean --force`
4. Install target version: `npm install -g @anthropic-ai/claude-code@<version>`
5. Verify: `claude --version`

### Using the Version Management Script

The `cc_version.py` script automates the environment setup process, handling auto-update settings and version installation through a single command interface. This eliminates the risk of forgotten steps or typos during manual setup.

**Recommended workflow:**

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

The `--status` command displays auto-update state, installed version, and latest available version in a single view. Use `--list` to see all available versions from the npm registry.

For complete documentation of all commands and options, see `docs/features/cc-version-script/CC-Version-Script-Overview.md`.

## Trial Protocol

Each trial follows this standardized sequence:

### Baseline Context Consumption

A fresh Claude Code session consistently shows a baseline of pre-included content already consumed before any user interaction:

- **Baseline**: ~26k tokens (13% of 200k context window)
- **Variance**: Minimal (<1k tokens across 5 test sessions)

This baseline includes system prompts, tool definitions, and other infrastructure content that Claude Code loads automatically. All pre-operation measurements in this methodology are relative to this baseline - a "clean" session after `/wsd:getid` will show approximately 26-28k tokens consumed.

Understanding this baseline is critical for interpreting scenario targets:
- **Easy (<40% pre-op)**: ~80k tokens, leaving ~54k for scenario command overhead
- **Medium (40-50% pre-op)**: ~80-100k tokens
- **Hard (>50% pre-op)**: >100k tokens, requiring substantial context loading

### Step 1: Initialize Fresh Context

Start a clean session using the simplified ID generation command:

```
/wsd:getid
```

This generates a unique Workscope ID (format: `YYYYMMDD-HHMMSS`) without the full WSD platform onboarding. The command:
- Runs the `date` command to get current timestamp
- Reports the Workscope ID for artifact naming
- Does NOT load WSD system files or create a Work Journal

After running `/wsd:getid`, context consumption should remain near baseline (~26-28k tokens).

Record the Workscope ID for artifact naming.

### Step 2: Measure Pre-Operation Context

Run the `/context` command and record the output:

```
/context
```

Record:
- Total tokens consumed (e.g., "27k/200k tokens (13%)")
- Percentage of context used

This establishes the **pre-operation baseline** for token consumption analysis. With `/wsd:getid`, this should remain near the session baseline (~26-28k tokens, 13-14%). Compare this to `/wsd:init --custom` which typically reaches 70-95k tokens (35-48%) due to WSD platform file loading.

### Step 3: Execute Trigger Operation

Run one of the scenario-targeted analysis commands against the unified target WPD:

| Scenario | Command | Target Pre-Op | Expected Outcome |
|----------|---------|---------------|------------------|
| Easy | `/analyze-light docs/wpds/pipeline-refactor.md` | <40% | SUCCESS |
| Medium | `/analyze-standard docs/wpds/pipeline-refactor.md` | 40-50% | MIXED |
| Hard | `/analyze-thorough docs/wpds/pipeline-refactor.md` | >50% | FAILURE |

Choose the appropriate command based on the reproduction scenario being tested.

**How the commands differ:**

- **`/analyze-light`**: Performs minimal context loading before analysis. Reads only the target WPD and directly referenced files.
- **`/analyze-standard`**: Performs moderate context loading. Reads the target WPD plus related specifications and standards.
- **`/analyze-thorough`**: Performs extensive context loading. Reads the target WPD plus comprehensive project documentation including Investigation-Journal.md and analysis documents, deliberately inflating pre-operation consumption.

**Allow the Session Agent to complete its analysis.** Do not interrupt or provide guidance during command execution.

### Step 4: Measure Post-Operation Context

Run `/context` again and record the output:

```
/context
```

Record:
- Total tokens consumed
- Percentage of context used
- Delta from pre-operation measurement

### Step 5: Prompt for Self-Report

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

### Step 6: Record Results

Based on the Session Agent's response, classify the trial:

- **SUCCESS**: Agent reports no phantom reads; all file content was received inline
- **FAILURE**: Agent confirms phantom reads; one or more files returned markers that were not followed up

Record additional details:
- Which files were affected (if reported)
- Agent's level of confidence in self-assessment
- Any anomalies or unexpected behavior
- Whether recovery was attempted (re-reading files after recognizing phantom reads)

### Step 7: Export Session Artifacts

Export the chat session using `/export` and save the resulting `.txt` file.

Naming convention:
```
../cc-exports/{WORKSCOPE_ID}.txt
```

Saving this in the `../cc-exports/` directory (a new directory adjacent to your copy of this repo) will allow trial results data to be easily gathered by the `src/collect_trials.py` script.

Example: `../cc-exports/20260122-143022.txt`

**IMPORTANT: Save exports OUTSIDE the project directory.** Chat exports saved within the project directory become visible to subsequent sessions through file listing operations. This can contaminate trial isolation.

### Step 8: Collect Session Files

After exporting, collect the session `.jsonl` files that contain the raw tool call history needed for analysis.

#### Using the Collection Script (Recommended)

The `collect_trials.py` script automates artifact collection, organizing files into Workscope ID-keyed directories:

```bash
./src/collect_trials.py -e ../cc-exports -d ./dev/misc/collected-trials -v
```

The script:
- Scans the exports directory for chat export `.txt` files
- Extracts the Workscope ID from each export
- Locates the corresponding session `.jsonl` files in `~/.claude/projects/`
- Copies all associated files (main session, subagents, tool-results) to the destination
- Organizes artifacts into directories named by Workscope ID
- Handles all Claude Code session storage structures (flat, hybrid, hierarchical) automatically

**Important**: Run the script from the project root directory where trials were conducted.

For complete documentation, see `docs/features/collect-trials-script/Collect-Trials-Script-Overview.md`.

### Step 9: Preprocess Trial Data

After collection, run the trial data preprocessing tool to extract structured analysis data:

```
/update-trial-data dev/misc/collected-trials/{WORKSCOPE_ID}
```

This creates a `trial_data.json` file in the trial directory containing:
- Context reset events with timing percentages
- File read operations with token counts
- Reset pattern classification
- Pre/post operation consumption metrics

The preprocessed data enables systematic comparison across trials using the established theories.

## Recommended Batch Workflow

For running multiple trials efficiently, use the following batch workflow:

### During Trial Execution

1. **Run trials sequentially**, completing Steps 1-7 for each trial
2. **Export each trial** to a common exports directory (e.g., `../cc-exports/`)
3. **Do not collect session files** between trials—continue to the next trial

### After All Trials Complete

1. **Run the collection script once** to batch-process all exports:

```bash
./src/collect_trials.py -e ../cc-exports -d ./dev/misc/methodology-03-trials -v
```

2. **Preprocess all trials**:

```bash
for dir in ./dev/misc/methodology-03-trials/*/; do
    /update-trial-data "$dir"
done
```

3. **Review the summary** showing collected, skipped, and failed trials

### Idempotent Re-runs

The collection script supports safe re-execution:
- **Already-collected trials are skipped**: If a trial directory exists, the script skips it
- **Processed exports are removed**: Successfully collected exports are deleted from the source directory
- **Failures don't block progress**: Individual trial failures don't stop the batch

## Artifact Organization

Trial artifacts are organized by collection context:

```
dev/misc/
├── methodology-03-trials/        # Trials using this methodology
│   ├── 20260122-143022/
│   │   ├── 20260122-143022.txt   # Chat export
│   │   ├── {uuid}.jsonl          # Session file
│   │   ├── {uuid}/               # Session artifacts
│   │   │   ├── subagents/
│   │   │   └── tool-results/
│   │   └── trial_data.json       # Preprocessed analysis data
│   └── 20260122-152301/
├── wsd-dev-02/                   # Historical collection (22 trials)
├── repro-attempts-02/            # Historical collection (9 trials)
└── example-sessions/             # Historical trials (Methodology 1.0)
```

## Scenario Design Rationale

### The Key Insight

From 31 trials across two collections, the Reset Timing Theory achieved 100% prediction accuracy:

| Pattern | Description | Outcome |
|---------|-------------|---------|
| EARLY + LATE | First reset <50%, last >95%, no mid-session | 100% SUCCESS |
| SINGLE_LATE | Single reset >95% | 100% SUCCESS |
| MID-SESSION | Any reset between 50-90% of session | 100% FAILURE |

The presence of **any mid-session reset** (50-90% through the session) is the critical failure predictor.

### How Scenarios Control Outcomes

Rather than varying WPD complexity (which proved ineffective), the scenario commands vary **onboarding context consumption**:

| Scenario | Mechanism | Target Pre-Op | Expected Resets |
|----------|-----------|---------------|-----------------|
| Easy | Minimal reads before analysis | <40% | 1-2 (EARLY + LATE) |
| Medium | Moderate reads before analysis | 40-50% | 2-3 (borderline mid) |
| Hard | Extensive reads before analysis | >50% | 3+ (multiple mid-session) |

The Hard scenario deliberately reads large documentation files (Investigation-Journal.md at ~1000 lines, analysis documents) to push pre-op consumption above 50%, reducing headroom and triggering mid-session resets during the subsequent file reading operations.

### Target Failure Rates

Based on the Reset Timing Theory and observed data:

| Scenario | Target Failure Rate | Rationale |
|----------|---------------------|-----------|
| Easy | 0% | Sufficient headroom prevents mid-session resets |
| Medium | ~25-50% | Borderline headroom; outcome depends on session variance |
| Hard | ~75-100% | Insufficient headroom reliably triggers mid-session resets |

These targets are hypotheses to be validated through trials using this methodology.

## Current Theoretical Framework

### Reset Timing Theory (STRONGLY CONFIRMED)

The timing of context resets predicts phantom read occurrence with 100% accuracy across 31 trials:

- **Safe patterns**: EARLY_PLUS_LATE, SINGLE_LATE
- **Failure patterns**: EARLY_PLUS_MID_LATE, LATE_CLUSTERED, multiple mid-session

A "context reset" is detected when `cache_read_input_tokens` drops >10,000 tokens between consecutive assistant messages.

### Headroom Theory (SUPPORTED)

Starting context consumption ("headroom") correlates with reset timing:
- High headroom (>100K available) → resets occur at natural breakpoints
- Low headroom (<80K available) → resets occur mid-operation

```
Headroom = Context Window Size (200K) - Current Token Consumption
```

### Mid-Session Reset Accumulation (NEW)

From repro-attempts-02 analysis:
- 0 mid-session resets: Safe
- 1 borderline mid-session reset (50-65%): Likely survivable
- 2+ mid-session resets: Likely failure
- 3+ consecutive mid-session resets: Guaranteed failure

### Sustained Processing Gap Requirement (NEW)

Successful trials exhibit a "clean gap" of ~35-40% of session duration where work proceeds uninterrupted between an early reset and a late reset. Failure occurs when this gap is fragmented by mid-session resets.

### Dynamic Context Pressure Hypothesis (UNVALIDATED)

Resets may be triggered by **rate of context accumulation** rather than absolute values. Rapid batch reads without processing pauses may trigger resets more readily than steady accumulation.

## Limitations

### Self-Report Reliability

The methodology relies on the Session Agent's ability to accurately introspect on its own tool call history. Known limitations:

1. **Model Incentives**: LLMs may be biased toward reporting success
2. **Introspection Accuracy**: Models may misremember or confabulate about past operations
3. **Non-Determinism**: Responses vary between runs independent of actual behavior
4. **Confirmation Bias**: The prompt explicitly describes the phenomenon, potentially priming reports

Despite these limitations, the strong correlation between self-reported outcomes and context reset patterns (100% across 31 trials) provides confidence that the methodology detects a real phenomenon.

### Hawthorne Effect

Conducting trials in a project explicitly dedicated to studying phantom reads could theoretically affect agent behavior. However, the first successful reproduction (20260121-202919) demonstrated that phantom reads can occur even in this context. Notably, that trial showed **recovery behavior**—the agent recognized the phantom reads and re-read files successfully, suggesting awareness may enable recovery but doesn't prevent occurrence.

### Version Specificity

The theoretical framework was developed primarily on Claude Code version 2.1.6 with Opus 4.5. Results may differ on other versions or models, particularly across the Era 1/Era 2 boundary.

### Scenario Command Availability

This methodology requires the scenario-specific commands (`/wsd:getid`, `/analyze-light`, `/analyze-standard`, `/analyze-thorough`) to be implemented. See the referenced command specifications for implementation details.

## References

- `Experiment-Methodology-02.md` - Previous methodology version (superseded)
- `Experiment-Methodology-01.md` - Original investigation methodology (historical)
- `Investigation-Journal.md` - Chronological discovery log
- `WSD-Dev-02-Analysis-1.md` - Initial 7-trial analysis
- `WSD-Dev-02-Analysis-2.md` - Expanded 22-trial analysis
- `WSD-Dev-02-Analysis-3.md` - Token-based analysis
- `Repro-Attempts-02-Analysis-1.md` - 9-trial reproduction analysis
- `PRD.md` - Project overview
- GitHub Issue: https://github.com/anthropics/claude-code/issues/17407

---

*Version 3.0 - 2026-01-22*
