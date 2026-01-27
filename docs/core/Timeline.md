# Investigation Timeline

A concise chronological record of the Phantom Reads investigation. For detailed narratives, see [Investigation-Journal.md](Investigation-Journal.md).

---

## 2026-01-09

**Initial Discovery**
- Bug first encountered in Claude Code version 2.1.3
- User Agent provided nonsensical WPD review via `/refine-plan` command
- Agent appeared to operate on non-existent information while believing it had read files

**Original Investigation Begins**
- Manual testing across Claude Code versions 2.0.54 through 2.1.2
- Self-report methodology: trigger reads via `/wsd:init --custom` + `/refine-plan`
- Initial finding: Regression appeared to begin at version 2.0.59

---

## 2026-01-10

**Public Disclosure**
- GitHub Issue #17407 opened: https://github.com/anthropics/claude-code/issues/17407
- Report published to X (Twitter)
- Identified 2.0.58/2.0.59 boundary as regression point (later revised)

---

## 2026-01-12

**Repository Created**
- This repository established for investigation, reproduction, and workaround development
- Goals: documentation, reproduction environment, analysis tools

---

## 2026-01-12-13

**Sample Collection and Revised Understanding**
- Generated success/failure samples across builds: 2.0.58, 2.0.59, 2.0.60, 2.1.3, 2.1.6
- Samples stored in `dev/misc/example-sessions/`

**Critical Discovery: Two Distinct Eras**
- **Era 1** (≤2.0.59): `[Old tool result content cleared]` mechanism
- **Era 2** (≥2.0.60): `<persisted-output>` marker mechanism
- Revised understanding: NO "safe" version exists

**CLAUDE.md Warning Test**
- Added prominent warning about phantom reads to CLAUDE.md
- Result: **Completely ineffective** - agents ignore warnings

**MCP Filesystem Workaround Discovered**
- Implemented workaround using `@modelcontextprotocol/server-filesystem`
- Bypasses native Read tool via `permissions.deny: ["Read"]`
- Result: **100% success rate** in testing
- Documentation: [WORKAROUND.md](../../WORKAROUND.md)

**Session File Analysis**
- Discovery: Session `.jsonl` files do NOT capture phantom read markers
- Hypothesis: Context management transforms content AFTER logging, BEFORE model receives it
- Found correlation: Context resets (via `cache_read_input_tokens` drops) predict phantom reads

---

## 2026-01-14

**Context Reset Analysis Documented**
- Created `docs/theories/Context-Reset-Analysis.md`
- Documented ~140K token threshold hypothesis
- Created reproduction environment plan

---

## 2026-01-15

**Reproduction Specs Collection Feature**
- Implemented fictional "Data Pipeline System" specification set
- 6 interconnected spec files (~3,600 lines total)
- 3 test WPDs: easy, medium, hard scenarios
- Location: `docs/specs/`, `docs/wpds/`

**First Reproduction Trials**
- 3 trials (one per difficulty) in cloned repository
- Result: **All succeeded** (unexpected - hard case was expected to fail)
- Hard case reached 149K tokens (75%) but no phantom reads

**WSD Development Project Repeat Trials**
- Conducted trials in original project where phantom reads were known to occur
- Captured both success and failure cases with embedded `/context` data
- Samples: `dev/misc/wsd-dev-repeat/`

**Headroom Theory Discovered**
- Key insight: Starting context consumption (headroom) before operation matters more than total content
- Bad trial: Started at 126K (63%), only added 16K, but FAILED
- Good trial: Started at 85K (42%), added 74K, SUCCEEDED
- Documentation: [docs/theories/Headroom-Theory.md](../theories/Headroom-Theory.md)

---

## 2026-01-16-17

**CC Version Script Completed**
- Implemented `src/cc_version.py` for managing Claude Code versions
- Features: `--disable-auto-update`, `--list`, `--status`, `--install`, `--reset`
- 64 test cases
- Specification: [docs/features/cc-version-script/CC-Version-Script-Overview.md](../features/cc-version-script/CC-Version-Script-Overview.md)

---

## 2026-01-18

**Collect Trials Script Completed**
- Implemented `src/collect_trials.py` for gathering trial artifacts
- Handles all session storage structures (flat, hybrid, hierarchical)
- 40+ test cases
- Specification: [docs/features/collect-trials-script/Collect-Trials-Script-Overview.md](../features/collect-trials-script/Collect-Trials-Script-Overview.md)

---

## 2026-01-19

**WSD-Dev-02 Collection Started**
- 7 initial trials using Experiment-Methodology-02
- Location: `dev/misc/wsd-dev-02/`

**Reset Timing Theory Discovered**
- Reset timing PATTERN more predictive than count or headroom alone
- Patterns: EARLY+LATE (safe), EARLY+MID/LATE (dangerous), LATE CLUSTERED (dangerous)
- Trial 133726: Identical metrics to success but FAILED due to late clustered timing

**Trial Data Preprocessing Tool Created**
- `.claude/commands/update-trial-data.md` (karpathy script)
- Extracts session data into structured `trial_data.json` files
- Analysis: [docs/experiments/results/WSD-Dev-02-Analysis-1.md](../experiments/results/WSD-Dev-02-Analysis-1.md)

---

## 2026-01-20

**WSD-Dev-02 Expanded to 22 Trials**
- Added 15 additional trials
- Results: 5 SUCCESS (22.7%), 17 FAILURE (77.3%)

**Reset Timing Theory Validated**
- **100% prediction accuracy** across all 22 trials
- EARLY+LATE / SINGLE_LATE → SUCCESS
- Any mid-session reset (50-90%) → FAILURE
- Analysis: [docs/experiments/results/WSD-Dev-02-Analysis-2.md](../experiments/results/WSD-Dev-02-Analysis-2.md)

**Token-Based Analysis (Schema 1.1)**
- Collected token counts for all files via Anthropic API
- Key finding: No fixed reset threshold (82K-383K observed)
- "Clean Gap" pattern quantified: SUCCESS trials show 55-65% uninterrupted processing windows
- Analysis: [docs/experiments/results/WSD-Dev-02-Analysis-3.md](../experiments/results/WSD-Dev-02-Analysis-3.md)

---

## 2026-01-21

**Trial Data Schema Upgrade (1.2)**
- Fixed `scripts/extract_trial_data.py` reliability issues
- All trials upgraded to Schema 1.2

**Repro-Attempts-02 Collection**
- 9 trials across Easy/Medium/Hard scenarios
- Results: 1 failure (Hard), 8 successes
- **First successful phantom read in controlled reproduction scenario**
- Analysis: [docs/experiments/results/Repro-Attempts-02-Analysis-1.md](../experiments/results/Repro-Attempts-02-Analysis-1.md)

**Combined Analysis: 31 Trials**
- Reset Timing Theory: **31/31 (100%) prediction accuracy**
- Reset Count correlation strengthened: 2 resets = safe, 4+ = failure
- New theory: Mid-Session Reset Accumulation (2+ mid-session resets = failure)

---

## 2026-01-22

**Experiment-Methodology-03 Designed**
- Simplified initialization with `/wsd:getid`
- Scenario-targeted commands with preload via `@` file notation
- Target: Control pre-op consumption via hoisted files

---

## 2026-01-22-23

**Methodology 3.0 Trial Failures**
- Discovery: **~25K token limit** on hoisted files (silently ignored if exceeded)
- Discovery: `/context` command **cannot be called by agents**
- Hard scenario caused context overflow errors instead of phantom reads

**Methodology Restructured to 4.0**
- Separated setup commands (`/setup-easy`, `/setup-medium`, `/setup-hard`) from analysis (`/analyze-wpd`)
- Split large files to stay under 25K limit
- Calibrated context measurements confirmed
- Documentation: [docs/experiments/methodologies/Experiment-Methodology-04.md](../experiments/methodologies/Experiment-Methodology-04.md)

---

## 2026-01-23

**Consolidated Theory Document Created**
- Established X + Y model framework
- X = pre-operation context, Y = operation context, T = threshold
- Phantom reads require X + Y > T (with additional conditions)
- Documentation: [docs/theories/Consolidated-Theory.md](../theories/Consolidated-Theory.md)

---

## 2026-01-24

**Experiment-Methodology-04 First Run**
- 8 trials (4 Hard, 4 Easy) with increased Y (added module-epsilon.md, module-phi.md)
- Result: **100% FAILURE across ALL scenarios** (including Easy)
- Y increased from 42K (7 files) to 57K (9 files)

**Reset Timing Theory Violated**
- SINGLE_LATE patterns (previously 100% SUCCESS) now showed FAILURE
- First systematic violation of the theory

**Y-Size Threshold Hypothesis Formed**
- Hypothesis: Y has an absolute threshold (~40-57K) beyond which phantom reads occur
- Later refined by subsequent experiments

**Post-Experiment-04-Ideas Created**
- Brainstormed 11 experiments (04A through 04K) to test refined hypotheses
- Tiered by priority: Critical (A, B, D), Important (F, H, K), Supporting (C, E, G, I, J)
- Documentation: [docs/experiments/planning/Post-Experiment-04-Ideas.md](../experiments/planning/Post-Experiment-04-Ideas.md)

---

## 2026-01-25

**Experiment-04A Completed** (Minimal X)
- 6 trials with X≈0 (no preload), Y=57K (9 files)
- Result: **100% SUCCESS**
- **Disproved absolute Y threshold** - Y=57K is safe when X is low

**Experiment-04D Completed** (Max X, Minimal Y)
- Trials with X=150K (maxload), Y=6K (1 file)
- Result: **100% SUCCESS**
- Confirmed high X is safe when Y is minimal
- Confirmed hoisting does NOT cause phantom reads

**Experiment-04K Completed** (1M Context Model)
- 6 trials using `claude-sonnet-4-20250514` with 1M context
- Same protocol as Method-04 that caused 100% failure
- Result: **100% SUCCESS**
- **Confirmed T (context window) matters** - 1M model avoids phantom reads
- Trial 20260125-211544 reached 202K tokens and succeeded
- Note: 1M model declared OUT OF SCOPE for further investigation

**Experiment-04L Completed** (Hoisting Redundancy)
- Tested if harness avoids redundant reads for hoisted files
- Result: Only 96 token difference between explicit and implicit file listing
- **Confirmed harness is intelligent about redundant reads**

---

## 2026-01-26

**Research Questions Catalog Created**
- `docs/core/Research-Questions.md` established
- 38 questions across 8 categories
- 9 answered, 10 hypothesis, 19 open

**Token Accounting Clarified**
- Documented baseline (~23K), preload, overhead (~40%), and total X
- Updated Investigation Journal with terminology reference

**Experiment-04 Preliminary Results Documented**
- [docs/experiments/results/Experiment-04-Prelim-Results.md](../experiments/results/Experiment-04-Prelim-Results.md)

**Current Understanding: "Danger Zone" Model**
- Phantom reads on 200K model require BOTH:
  - X ≥ ~73K tokens (pre-operation context)
  - Y ≥ ~50K tokens (agent-initiated reads)
- Safe conditions:
  - X ≈ 0 → any tested Y succeeds
  - Y minimal (~6K) → any tested X succeeds
  - 1M model → any tested combination succeeds

**Timeline Document Created**
- This document established for quick reference

---

## Pending Experiments

| Experiment | Description | Status |
|------------|-------------|--------|
| **04M** | X Boundary Exploration - test intermediate X values | Planned |
| **04B** | 8-File Y Threshold - narrow Y threshold range | Planned |
| **04F** | File Count vs Tokens - what triggers the threshold? | Planned |
| **04G** | Sequential vs Parallel Reads - accumulation rate | Planned |
| **04C** | Sanity Check - restore pre-epsilon/phi state | Planned |

---

## Quick Reference: Key Documents by Topic

| Topic | Document |
|-------|----------|
| Unified theory | [Consolidated-Theory.md](../theories/Consolidated-Theory.md) |
| Detailed narrative | [Investigation-Journal.md](Investigation-Journal.md) |
| Research questions | [Research-Questions.md](Research-Questions.md) |
| 22-trial analysis | [WSD-Dev-02-Analysis-3.md](../experiments/results/WSD-Dev-02-Analysis-3.md) |
| First reproduction | [Repro-Attempts-02-Analysis-1.md](../experiments/results/Repro-Attempts-02-Analysis-1.md) |
| Experiment-04 results | [Experiment-04-Prelim-Results.md](../experiments/results/Experiment-04-Prelim-Results.md) |
| Current methodology | [Experiment-Methodology-04.md](../experiments/methodologies/Experiment-Methodology-04.md) |
| Workaround | [WORKAROUND.md](../../WORKAROUND.md) |

---

*Last updated: 2026-01-26*
