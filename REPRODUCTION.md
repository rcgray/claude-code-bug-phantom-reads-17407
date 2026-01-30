# Reproducing Phantom Reads

This guide walks you through reproducing the Phantom Reads bug ([Issue #17407](https://github.com/anthropics/claude-code/issues/17407)) using the minimal reproduction environment included in this repository.

## Background

The Phantom Reads bug causes Claude Code to believe it has successfully read file contents when it has not. The `repro/` directory contains a self-contained, 20-file reproduction environment that reliably triggers the bug under the right conditions. It uses a fictional "Data Pipeline System" specification set as the payload — Claude is asked to analyze a work plan that requires cross-referencing multiple specification documents, creating the multi-file read pressure that triggers phantom reads.

This reproduction environment was validated across 55+ controlled trials (see [Investigation Journal](docs/core/Investigation-Journal.md) for details). It is the same environment used in the Barebones-216 experiment, which confirmed that phantom reads are a Claude Code harness issue — not specific to any project framework or file structure.

## Important Caveat: Server-Side Variability

**Whether phantom reads occur depends partly on server-side conditions you cannot control.** The Claude Code harness decides per-session whether to persist tool results to disk. When persistence is active, phantom reads are triggered reliably (~85% failure rate). When persistence is not active, the same protocol succeeds 100% of the time.

This means:
- You may run this reproduction and see 100% success one day, then 100% failure the next
- This is not a flaw in the reproduction — it reflects the actual bug behavior
- Check for a `tool-results/` directory in your session data (`~/.claude/projects/`) to determine whether persistence was active in your trial

See the [Server-Side Variability Theory](docs/theories/Server-Side-Variability-Theory.md) for the full analysis of this phenomenon.

## Prerequisites

- **Claude Code** installed (any version from 2.0.54 onward has exhibited phantom reads)
- **Node.js** 18+ (required by Claude Code)
- A terminal with bash or zsh

### Optional: Pin a Specific Version

If you want to test a specific Claude Code build for comparison purposes, you can use the included version management script:

```bash
# From inside the repro directory:
python3 src/cc_version.py --disable-auto-update
python3 src/cc_version.py --install 2.1.6
python3 src/cc_version.py --status

# When finished, restore defaults:
python3 src/cc_version.py --reset
```

This is optional — you can run the reproduction on whatever version you currently have installed.

## Setup

### Step 1: Copy the Reproduction Environment

Copy `repro/` to a **standalone directory outside this repository**. The reproduction must run in its own isolated project to avoid interference from this repository's configuration files (`.mcp.json`, `.claude/settings.local.json`, etc.).

```bash
cp -r repro /tmp/phantom-reads-repro
cd /tmp/phantom-reads-repro
```

You can place it anywhere you like — the key requirement is that it is not nested inside another project that has Claude Code configuration that might affect behavior (such as the MCP Filesystem workaround this investigation uses).

### Step 2: Verify the Structure

Confirm the directory looks like this:

```
phantom-reads-repro/
├── CLAUDE.md
├── .claude/commands/
│   ├── analyze-wpd.md
│   ├── setup-easy.md
│   ├── setup-medium.md
│   ├── setup-hard.md
│   └── setup-none.md
├── docs/
│   ├── specs/          (12 specification files)
│   └── wpds/
│       └── pipeline-refactor.md
└── src/
    ├── cc_version.py
    └── collect_trials.py
```

### Step 3: Initialize Git (Optional but Recommended)

Claude Code works best inside a git repository:

```bash
git init
git add -A
git commit -m "Initial reproduction environment"
```

## Running a Trial

Each trial tests whether Claude Code can correctly read and analyze multiple specification files under context pressure. The protocol has three scenarios that control how much context is consumed before the multi-file read operation.

### Scenarios

| Scenario | Setup Command | Pre-Load | Expected Context | Purpose |
|----------|---------------|----------|-----------------|---------|
| Easy | `/setup-easy` | 2 files (~41K tokens) | ~37% | Baseline — should succeed |
| Medium | `/setup-medium` | 3 files (~60K tokens) | ~46% | Borderline — mixed results |
| Hard | `/setup-hard` | 4 files (~88K tokens) | ~60% | Pressure test — likely to trigger phantom reads |

The `/setup-none` command loads no preload files and serves as a control.

**For your first trial, use `/setup-hard`** — it creates the most context pressure and is most likely to trigger the bug (when server-side conditions permit).

### Trial Protocol

#### 1. Start a Fresh Session

Open a new terminal in the reproduction directory and start Claude Code:

```bash
cd /tmp/phantom-reads-repro
claude
```

#### 2. Measure Baseline Context

Immediately run:

```
/context
```

Record the numbers. Expected baseline: ~24K tokens (12%).

#### 3. Run the Scenario Setup

```
/setup-hard
```

The command will load specification files into context and generate a Workscope ID (a timestamp like `20260130-143022`). **Record this ID** — it identifies your trial artifacts.

#### 4. Measure Post-Setup Context

```
/context
```

Record the numbers. For `/setup-hard`, expect ~120K tokens (60%).

#### 5. Trigger the Multi-File Read

```
/analyze-wpd docs/wpds/pipeline-refactor.md
```

**Let Claude work without interruption.** The analysis command directs Claude to read the target WPD and cross-reference it against the specification files — this is the operation that triggers phantom reads.

Wait for Claude to finish its analysis.

#### 6. Measure Final Context

```
/context
```

Record the numbers.

#### 7. Check for Phantom Reads

After Claude finishes, paste the following prompt **verbatim**:

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

#### 8. Classify the Result

Based on Claude's response:

- **SUCCESS**: Claude reports receiving actual file content for all files
- **FAILURE**: Claude confirms it received `<persisted-output>` markers or `[Old tool result content cleared]` messages instead of file content

#### 9. Export the Session

```
/export
```

Save the export file **outside the reproduction directory** to avoid contaminating future trials:

```bash
# Save to a dedicated exports directory
mkdir -p ~/phantom-reads-exports
# Move the export file there, renaming it with the Workscope ID
```

## Interpreting Results

### If You See SUCCESS

This means one of:
- Server-side persistence was not active during your session
- The harness did not persist tool results for this particular session

This does **not** mean your version is safe. Try again on a different day — server-side conditions change.

### If You See FAILURE

You have reproduced the Phantom Reads bug. Claude received markers instead of file content and proceeded without awareness of the gap. Common signs in the analysis output:

- Vague or generic observations that could apply to any specification
- Claims about file content that don't match what the files actually say
- Inconsistent depth of analysis across files (some detailed, some superficial)
- Confident assertions about documents that were never actually read

### Verifying Programmatically

After a trial, check your Claude Code session data for the presence of persisted tool results:

```bash
# Find your session directory (most recent)
ls -lt ~/.claude/projects/ | head -5

# Look for tool-results directories
find ~/.claude/projects/ -name "tool-results" -type d -maxdepth 4
```

If a `tool-results/` directory exists for your session, the harness persisted tool results to disk — this is the mechanism that causes phantom reads.

## Collecting Trial Data

If you're running multiple trials for systematic analysis, the included `collect_trials.py` script automates artifact collection:

```bash
# Create an exports directory outside the project
mkdir -p ~/phantom-reads-exports

# After running several trials and exporting each one to ~/phantom-reads-exports:
python3 src/collect_trials.py \
  -e ~/phantom-reads-exports \
  -d ~/phantom-reads-results \
  -v
```

The script:
- Scans the exports directory for chat export files
- Extracts Workscope IDs from each export
- Locates and copies associated session `.jsonl` files from `~/.claude/projects/`
- Organizes everything into directories named by Workscope ID

## What the Reproduction Environment Contains

The environment is intentionally minimal:

- **12 specification files** (`docs/specs/`): Formal documentation of a fictional Data Pipeline System with five modules (ingestion, transformation, output, caching, orchestration). These are the files Claude is asked to read and cross-reference.
- **1 work plan document** (`docs/wpds/pipeline-refactor.md`): A proposed refactoring that spans all five modules. Analyzing it properly requires reading and understanding the specification files.
- **5 custom commands** (`.claude/commands/`): The setup commands that control context preloading, plus the analysis command that triggers multi-file reads.
- **2 utility scripts** (`src/`): `cc_version.py` for version management and `collect_trials.py` for artifact collection.
- **CLAUDE.md**: Instructions that orient Claude to the fictional project.

None of these files reference phantom reads, the investigation, or the bug itself. Claude approaches the analysis as a normal documentation review task.

## The Workaround

If you're here because phantom reads are affecting your actual work, there is a validated workaround. The MCP Filesystem server bypasses Claude Code's native Read tool entirely, preventing phantom reads through a different code path. It has achieved 100% success across all testing.

See **[WORKAROUND.md](WORKAROUND.md)** for complete setup instructions.

## References

- [Issue #17407](https://github.com/anthropics/claude-code/issues/17407) — The original bug report
- [Server-Side Variability Theory](docs/theories/Server-Side-Variability-Theory.md) — Why results vary between sessions
- [Experiment Methodology](docs/experiments/methodologies/Experiment-Methodology-04.md) — Full experimental protocol
- [Investigation Journal](docs/core/Investigation-Journal.md) — Detailed narrative of the investigation
