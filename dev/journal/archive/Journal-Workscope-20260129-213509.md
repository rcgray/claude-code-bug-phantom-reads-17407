# Work Journal - 2026-01-29 21:35
## Workscope ID: Workscope-20260129-213509

## Initialization

- Read `docs/core/PRD.md` — Project overview for Phantom Reads Investigation (Issue #17407)
- Read WSD Platform system documents: Agent-System.md, Agent-Rules.md, Design-Decisions.md, Documentation-System.md, Checkboxlist-System.md, Workscope-System.md
- Generated Workscope ID: **20260129-213509**
- Initialized Work Journal at `dev/journal/archive/Journal-Workscope-20260129-213509.md`
- Mode: `--custom` — awaiting custom workscope from User

## Custom Workscope

**Assignment**: Analyze Step 2.1 of the Build Scan Discrepancy Investigation — replication attempt on Build 2.1.20 using collection `schema-13-2120`.

**Key Documents**:
- Planning: `docs/experiments/planning/Build-Scan-Discrepancy-Investigation.md`
- Results: `docs/experiments/results/Build-Scan-Discrepancy-Analysis.md`
- Guide: `docs/experiments/guides/Trial-Analysis-Guide.md`

**Objective**: Step 2.1 asks: Re-run Experiment-Methodology-04 on build 2.1.20 (3–5 trials) to test whether the original success pattern is reproducible. The trials have been collected in `dev/misc/schema-13-2120/`. I need to analyze the trial data, compare against prior findings, and update the Analysis document.

## Step 2.1 Analysis — COMPLETE

### Data Collection

Examined 9 trials in `dev/misc/schema-13-2120/`. All pre-processed with Schema 1.3 `trial_data.json` files. Extracted key metrics: outcome, has_tool_results, has_subagents, file read counts, reset analysis, persistence mapping, compaction loss.

### Key Findings

1. **Original success pattern reproduced (1/9 trials)**: Trial 202633 matches Jan 27 pattern exactly — 9 files inline, has_tool_results=false, SINGLE_LATE, negative compaction loss.

2. **Persistence non-deterministic within time window**: 4/9 sessions had persistence, 5/9 did not. Among direct-read trials only: 4/5 had persistence (80%).

3. **Sub-agent delegation confound (4/9 trials)**: Agents delegated file reads to Task/Explore sub-agents, offloading token pressure and avoiding persistence entirely.

4. **First recovery from `<persisted-output>` (trial 203749)**: Agent detected markers and read tool-result files successfully. Breaks the previously perfect `has_tool_results` discriminator.

5. **3 confirmed FAILURE trials**: 202641 (4 affected files, 3 resets), 203737 (3 affected, 2 resets), 204311 (2 affected, 2 resets).

6. **Result: MIXED** — suggests stochastic server-side behavior per investigation plan.

### Analysis Document Updates

- Wrote comprehensive Step 2.1 section to `Build-Scan-Discrepancy-Analysis.md` with 6 observations
- Updated RQ-BSD-3 from "Not answered" to "ANSWERED"
- Fixed Step 2.2 collection name from `schema-13-2120` to `schema-13-2122`
- Updated Document History

