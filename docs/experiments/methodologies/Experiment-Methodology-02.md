# Experiment Methodology (Version 2.0)

This document describes the current methodology for investigating and reproducing the Phantom Reads bug in Claude Code. It supersedes `Experiment-Methodology-01.md`, which is preserved for historical reference.

## Overview

The methodology has evolved from the original investigation to incorporate token consumption measurements via `/context` calls, improved artifact collection, and a more structured trial protocol. The core detection approach remains self-report-based: the Session Agent is prompted to introspect on whether it experienced phantom reads during a multi-file read operation.

### Key Changes from Version 1.0

1. **Token Consumption Measurement**: Trials now include `/context` calls before and after the trigger operation to capture token consumption data
2. **Artifact Collection**: Trials collect both chat exports (`.txt`) and session files (`.jsonl`) using Workscope ID as the coordination marker
3. **Standardized Trigger**: The `/refine-plan` command against a Work Plan Document (WPD) serves as the standardized trigger operation
4. **Repository-Based WPDs**: Trials use WPDs from `docs/wpds/` or similar locations rather than ad-hoc targets

### What Remains Unchanged

1. **Self-Report Detection**: Success/failure is still determined by Session Agent self-report
2. **Two-Era Model**: Phantom reads manifest via `[Old tool result content cleared]` (Era 1, builds ≤2.0.59) or `<persisted-output>` markers (Era 2, builds ≥2.0.60)
3. **Environment Setup**: Version pinning and auto-update disabling remain as documented in Version 1.0

## Environment Setup

Environment setup follows the same protocol as Version 1.0. For complete instructions, see `Experiment-Methodology-01.md` sections "Step 1: Disable Auto-Updates" and "Step 2: Install Target Version".

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
./src/cc_version.py --install 2.0.58

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

### Step 1: Initialize Fresh Context

Start a clean session using the WSD initialization command:

```
/wsd:init --custom
```

This establishes a fresh User Agent context with a unique Workscope ID (format: `YYYYMMDD-HHMMSS`). The Workscope ID serves as the coordination marker for all trial artifacts.

Record the Workscope ID for artifact naming.

### Step 2: Measure Pre-Operation Context

Run the `/context` command and record the output:

```
/context
```

Record:
- Total tokens consumed (e.g., "85k/200k tokens (42%)")
- Percentage of context used

This establishes the **pre-operation baseline** for token consumption analysis.

### Step 3: Execute Trigger Operation

Run the `/refine-plan` command against a target WPD:

```
/refine-plan <path-to-wpd>
```

Where `<path-to-wpd>` is the Work Plan Document to investigate. The repository provides test WPDs in `docs/wpds/`:
- `docs/wpds/refactor-easy.md` - Minimal scope
- `docs/wpds/refactor-medium.md` - Partial scope
- `docs/wpds/refactor-hard.md` - Full scope

Alternatively, use any WPD appropriate for the investigation context.

**Allow the Session Agent to complete its investigation.** Do not interrupt or provide guidance during the `/refine-plan` execution.

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

Disregard the Session Agent's investigation output. Prompt with the following:

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

### Step 7: Export Session Artifacts

Export the chat session using `/export` and save the resulting `.txt` file.

Naming convention:
```
../cc-exports/{WORKSCOPE_ID}.txt
```

Saving this in the `../cc-exports/` directory (a new directory adjacent to your copy of this repo) will allow trial results data to be easily gathered by the `src/collect_trials.py` script

Example: `../cc-exports/20260121-202917.txt`

**IMPORTANT: Save exports OUTSIDE the project directory.** Chat exports saved within the project directory become visible to subsequent sessions through file listing operations. This can contaminate trial isolation - a later session's `.jsonl` will contain references to earlier session UUIDs when the agent runs file discovery commands.

Recommended export location:
```
~/phantom-read-trials/{Difficulty}-{SessionUUID}.txt
```

After all trials are complete, exports can be moved into the repository's `dev/misc/` structure for archival.

### Step 8: Collect Session Files

After exporting, collect the session `.jsonl` files that contain the raw tool call history needed for analysis.

#### Using the Collection Script (Recommended)

The `collect_trials.py` script automates artifact collection, organizing files into Workscope ID-keyed directories:

```bash
./src/collect_trials.py -e ~/phantom-read-trials -d ./dev/misc/collected-trials -v
```

The script:
- Scans the exports directory for chat export `.txt` files
- Extracts the Workscope ID from each export
- Locates the corresponding session `.jsonl` files in `~/.claude/projects/`
- Copies all associated files (main session, subagents, tool-results) to the destination
- Organizes artifacts into directories named by Workscope ID
- Handles all Claude Code session storage structures (flat, hybrid, hierarchical) automatically

**Important**: Run the script from the project root directory where trials were conducted. The script derives the session file location from the current working directory.

For complete documentation, see `docs/features/collect-trials-script/Collect-Trials-Script-Overview.md`.

#### Manual Collection

Alternatively, copy session files manually from `~/.claude/projects/`. Session files are located in a project-specific directory. Look for recent `.jsonl` files matching your session UUID.

Required files:
- Main session `.jsonl` file (named with session UUID)
- `subagents/` directory (if present)
- `tool-results/` directory (if present)

## Recommended Batch Workflow

For running multiple trials efficiently, use the following batch workflow that separates trial execution from artifact collection:

### During Trial Execution

1. **Run trials sequentially**, completing Steps 1-7 for each trial
2. **Export each trial** to a common exports directory (e.g., `~/phantom-read-trials/`)
3. **Do not collect session files** between trials—continue to the next trial

### After All Trials Complete

1. **Run the collection script once** to batch-process all exports:

```bash
./src/collect_trials.py -e ~/phantom-read-trials -d ./dev/misc/collected-trials -v
```

2. **Review the summary** showing collected, skipped, and failed trials
3. **Organize by version** if testing multiple Claude Code versions:

```bash
# Collect trials into version-specific directories
./src/collect_trials.py -e ~/phantom-read-trials/v2.0.58 -d ./dev/misc/v2.0.58-trials -v
./src/collect_trials.py -e ~/phantom-read-trials/v2.1.6 -d ./dev/misc/v2.1.6-trials -v
```

### Idempotent Re-runs

The collection script supports safe re-execution:
- **Already-collected trials are skipped**: If a trial directory exists, the script skips it
- **Processed exports are removed**: Successfully collected exports are deleted from the source directory
- **Failures don't block progress**: Individual trial failures don't stop the batch

This enables workflows where you run trials incrementally and collect periodically without worrying about duplicates.

## Artifact Organization

Trial artifacts are organized by investigation context:

```
dev/misc/
├── repro-attempts/           # Trials using docs/wpds/ WPDs
│   ├── easy-1/
│   │   ├── Easy-{uuid}.txt
│   │   ├── {uuid}.jsonl
│   │   └── {uuid}/
│   │       └── subagents/
│   ├── medium-1/
│   └── hard-1/
├── collected-trials/         # Batch-collected trials (by Workscope ID)
│   ├── 20260115-143022/
│   │   ├── 20260115-143022.txt
│   │   ├── {uuid}.jsonl
│   │   └── {uuid}/
│   └── 20260115-152301/
├── wsd-dev-repeat/           # Trials on WSD Development project
│   ├── 2.1.6-good/
│   └── 2.1.6-bad/
└── session-examples/         # Historical trials (Methodology 1.0)
    ├── 2.0.58-good/
    ├── 2.0.58-bad/
    ├── 2.1.6-good/
    └── 2.1.6-bad/
```

The Workscope ID coordinates artifacts within a trial directory. The session UUID (from Claude Code) links the chat export to the session files.

## Results

### Reproduction Attempts (This Repository)

Trials conducted on the phantom-read-clone repository using `docs/wpds/` test WPDs:

| Trial    | WPD                | Pre-Op Tokens | Post-Op Tokens | Result  |
| -------- | ------------------ | ------------- | -------------- | ------- |
| easy-1   | refactor-easy.md   | 74K (37%)     | 94K (47%)      | SUCCESS |
| medium-1 | refactor-medium.md | 80K (40%)     | 123K (62%)     | SUCCESS |
| hard-1   | refactor-hard.md   | 95K (48%)     | 149K (75%)     | SUCCESS |

All three trials succeeded (no phantom reads), despite `refactor-hard.md` being designed to reliably trigger phantom reads.

### WSD Development Project Trials

Trials conducted on the parent WSD Development project (a larger, more complex codebase):

| Trial      | Pre-Op Tokens | Post-Op Tokens | Result  |
| ---------- | ------------- | -------------- | ------- |
| 2.1.6-good | 85K (42%)     | 159K (79%)     | SUCCESS |
| 2.1.6-bad  | 126K (63%)    | 142K (71%)     | FAILURE |

The "bad" trial consumed **fewer total tokens** but experienced phantom reads because it **started at higher consumption** (126K vs 85K).

### Analysis

The WSD Development trials revealed an important pattern: pre-operation token consumption appears more predictive of phantom read occurrence than total token consumption or content size. This observation led to the development of the Headroom Theory (see below).

The reproduction attempts on this repository all started with relatively low pre-operation consumption (<100K), leaving substantial "headroom" in the context window. This may explain why even the "hard" WPD failed to trigger phantom reads.

## Current Investigation Areas

### Reset Theory

The **Reset Theory** proposes that phantom reads correlate with **context reset frequency**. Sessions with phantom reads exhibit approximately 2x the number of context resets compared to successful sessions.

A context reset is detected by analyzing `cache_read_input_tokens` in session `.jsonl` files. When this value drops dramatically (>10,000 tokens) between consecutive assistant messages, a reset has occurred.

For detailed analysis, see `Context-Reset-Analysis.md`.

### Headroom Theory

The **Headroom Theory** refines our understanding by identifying **starting context consumption** as a critical predictor. "Headroom" is the available buffer space before a multi-file read operation begins:

```
Headroom = Context Window Size - Current Token Consumption
```

Lower starting headroom leads to earlier and more frequent context resets, which increases phantom read probability.

For detailed analysis, see `Headroom-Theory.md`.

### Relationship Between Theories

The two theories are complementary:
- **Reset Theory** explains the **mechanism**: context resets clear content before the model processes it
- **Headroom Theory** explains the **trigger**: low starting headroom causes earlier/more frequent resets

Together they form a causal chain:
```
High pre-operation consumption → Low headroom → More resets → More phantom reads
```

### Finding the Smoking Gun

Both theories are derived from correlation analysis of self-reported outcomes. The current investigation seeks a **programmatic indicator** that can detect phantom reads without relying on Session Agent self-report.

Candidates under investigation:
- Presence of `<persisted-output>` markers without subsequent Read calls for the persisted file
- `[Old tool result content cleared]` markers in the session history
- Specific `cache_read_input_tokens` patterns that predict phantom reads

Until a reliable programmatic indicator is found, self-report remains the primary detection method.

## Limitations

### Self-Report Reliability

The methodology relies on the Session Agent's ability to accurately introspect on its own tool call history. Known limitations:

1. **Model Incentives**: LLMs may be biased toward reporting success
2. **Introspection Accuracy**: Models may misremember or confabulate about past operations
3. **Non-Determinism**: Responses vary between runs independent of actual behavior
4. **Confirmation Bias**: The prompt explicitly describes the phenomenon, potentially priming reports

Despite these limitations, the correlation between self-reported phantom reads and context consumption patterns provides confidence that the methodology detects a real phenomenon.

### Reproduction Reliability

The current reproduction environment (this repository with `docs/wpds/` WPDs) has not yet achieved reliable phantom read triggering. All three difficulty tiers produced successful outcomes during initial testing.

The Headroom Theory suggests this may be due to the repository's relatively lean onboarding process, which leaves substantial headroom before the trigger operation. Further refinement of the reproduction environment is ongoing.

### Version Specificity

All documented trials were conducted on Claude Code version 2.1.6 with Opus 4.5. Results may differ on other versions or models.

### Trial Isolation

Each trial should be fully independent, but artifacts saved within the project directory can create cross-contamination. During WSD Development project trials, we discovered that a chat export saved to the project directory appeared in a subsequent session's file listing tool results. The sessions were properly isolated at the Claude Code level, but filesystem artifacts created apparent cross-references.

To maintain clean trial isolation:
1. Save chat exports outside the project directory during active trials
2. Remove any trial artifacts from the project directory before starting subsequent trials
3. Move exports into the repository's archival structure only after all related trials are complete

## References

- `Experiment-Methodology-01.md` - Original investigation methodology (historical)
- `Context-Reset-Analysis.md` - Reset Theory analysis
- `Headroom-Theory.md` - Headroom Theory analysis
- `Investigation-Journal.md` - Chronological discovery log
- `PRD.md` - Project overview
- GitHub Issue: https://github.com/anthropics/claude-code/issues/17407

---

*Version 2.1 - 2026-01-19*
