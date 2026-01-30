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

**Baseline Trial Collection**
- Captured 3 successful baseline trials on cloned repository
- Location: `dev/misc/self-examples/` (2.1.6-good-baseline-1, -2, -3)
- Purpose: Establish baseline measurements for reproduction environment

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

**Trial Data Schema Upgrade (1.1 → 1.2)**
- Schema 1.2 correctly handles failed file reads (file not found) in token counting timeline
- Stabilized helper script `dev/karpathy/extract_trial_data.py` for reliable extraction
- Reprocessed all 25 existing trials to Schema 1.2 (22 in wsd-dev-02, 3 in repro-attempts)

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

**Methodology 3.0 First Trial Collection**
- 9 trials collected using Experiment-Methodology-03 commands
- All trials reported SUCCESS (unexpected - hard scenarios expected to fail)
- Collection: `dev/misc/repro-attempts-03-firstrun/`
- Note: This unexpectedly uniform success led to discovery of methodology issues documented 2026-01-22-23

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

**Phase 10: Y-Increase Module Expansion**
- Created `docs/specs/module-epsilon.md` (Data Caching Layer, ~875 lines, ~8k tokens)
- Created `docs/specs/module-phi.md` (Pipeline Orchestration, ~900 lines, ~8k tokens)
- Integrated new modules into existing specs (data-pipeline-overview, integration-layer, pipeline-refactor WPD)
- Updated `/analyze-wpd` command to include new modules in required reading
- Purpose: Increase Y (operation context) from 42K to 57K tokens to reliably trigger phantom reads
- Added Phase 10 to [Reproduction-Specs-Collection FIP](../features/reproduction-specs-collection/Reproduction-Specs-Collection-Overview.md)

---

## 2026-01-24

**Experiment-Methodology-04 First Run**
- 8 trials (4 Hard, 4 Easy) with increased Y (added module-epsilon.md, module-phi.md)
- Collection: `dev/misc/repro-attempts-04-firstrun`
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

**Documentation Reorganization**
- Restructured `docs/` directory: moved experiment-related docs from `docs/core/` to dedicated subdirectories
- Created `docs/experiments/` (methodologies, results, planning, guides), `docs/theories/`, `docs/mitigations/`
- `docs/core/` narrowed to true core documents: PRD, Action-Plan, Investigation-Journal, Research-Questions, Design-Decisions, Timeline
- Updated PRD.md with directory structure guidance for future agents

**`/process-prompt-log` Command Created**
- New karpathy script for extracting discoveries from historical prompt logs into core documentation
- Targets: Timeline.md, Investigation-Journal.md, Research-Questions.md
- Designed to process the ~30 prompt log files accumulated over the project's lifetime

**X+Y Interaction Model Refined**
- User explicitly clarified that X and Y are *dependent on each other* with respect to T—not independent thresholds
- Anti-"magic number" framing established: the goal is to understand the interaction surface, not find isolated thresholds
- Updated RQ-B8 with research caution against hunting for independent threshold values
- 1M model formally declared OUT OF SCOPE (diagnostic only; investigation stays on 200K model)

**Experiment-04M Designed**
- X Boundary Exploration: test intermediate X values between `/setup-none` (X≈23K) and `/setup-easy` (X≈73K)
- Prescribed `/setup-mid` using `operations-manual-standard.md` for X≈50K
- Git branch approach proposed for 04B/04C/04F (restore pre-epsilon/phi state instead of surgical edits)

**Timeline Document Created**
- This document established for quick reference

---

## 2026-01-27

**Barebones-216 Experiment** (CC v2.1.6, barebones repo)
- Created stripped-down repository with only essential files (20 files, no WSD framework, no hooks)
- Ran 5 trials using Experiment-Methodology-04 with `/setup-hard`
- Results: 4 FAILURE, 1 INVALID (protocol violation) → **100% failure rate among valid trials**
- **Confirmed phantom reads are NOT WSD-specific** — bug reproduces without WSD framework or hooks
- Trial 092331 initially categorized as success; later reclassified as invalid (agent skipped 3 required files)
- Collection: `dev/misc/repro-attempts-04-barebones/`

**Barebones-2120 Experiment** (CC v2.1.20, barebones repo)
- Upgraded from locked v2.1.6 to current v2.1.20
- Same barebones repository as Barebones-216
- Ran 5 trials using Experiment-Methodology-04 with `/setup-hard`
- Results: 5 SUCCESS, 0 FAILURE (0% failure rate)
- **Anthropic changed something between 2.1.6 and 2.1.20** — our reliable repro case no longer triggers phantom reads
- Additional unrecorded trials also showed unanimous success
- Collection: `dev/misc/repro-attempts-04-2120/`

**Trial Data Pre-Processing**
- Ran `/update-trial-data` on all 10 trials across both collections
- Created `trial_data.json` for each trial

**Analysis Planning**
- Created `docs/experiments/planning/Barebones-216.md` — analysis plan for the barebones v2.1.6 results
- Created `docs/experiments/planning/Barebones-2120.md` — analysis plan for the v2.1.20 results

**Discovered Behavior: Hoisted File Injection Mechanism**
- Agent self-reflection confirmed `@`-referenced files appear as full content in `<system-reminder>` blocks
- Explains why hoisting is immune to phantom reads: system messages are not subject to context management
- Documented as DB-I8 in Research-Questions.md

**Observation: Transient "0% remaining" UI Warning**
- Status bar occasionally flashes "0% remaining" during operations, then disappears
- May signal context reset in progress; not captured in session logs
- Documented as DB-I7 and RQ-F5 in Research-Questions.md

**New Investigation Goal**
- Re-establish a failure repro case on CC v2.1.20 (our current repro case no longer triggers)
- Perform "build search" between 2.1.6 and 2.1.20 to find where the change occurred
- Examine whether this is a fix, a threshold shift, or an optimization that invalidates our tuned scenario

**Barebones-216 Analysis Completed**
- RQ-by-RQ analysis (RQ-BB216-1 through RQ-BB216-5) documented in `docs/experiments/results/Barebones-216-Analysis.md`
- Trial 092331 reclassified from "success" to INVALID (protocol violation — agent skipped 3 of 8 required files)
- Official Barebones-216 failure rate corrected to 100% (4/4 valid trials)
- All 5 RQs answered; confirmed phantom reads are not WSD-specific, hook system is not a contributor

**Barebones-2120 Analysis Completed** (RQ-BB2120-1 through RQ-BB2120-7)
- RQ-by-RQ analysis documented in `docs/experiments/results/Barebones-2120-Analysis.md`
- Claude Code changelog compiled for versions 2.1.6 through 2.1.22 (workbench artifact for RQ-BB2120-7)
- RQ-BB2120-7 answered: changelog review identified candidate changes but no single definitive fix
- RQ-BB2120-6 and RQ-BB2120-8 remain open (require future experiments)

---

## 2026-01-28

**Build Scan Experiment** (CC v2.1.6 through v2.1.22, barebones repo)
- Tested every available build from 2.1.6 through 2.1.22 using Experiment-Methodology-04 with `/setup-hard` on the barebones repository
- Executed the planned "Build Search" experiment across the full version range

**Key Findings:**

| Build Range | Behavior |
| ----------- | -------- |
| 2.1.6 | Phantom reads (known from prior experiments) |
| 2.1.7 – 2.1.12 | **Method-04 cannot execute** — context overflow kills session during `/analyze-wpd` |
| 2.1.13 | Does not exist (version number skipped) |
| 2.1.14 | Context limit on all 3 trials |
| 2.1.15 | **First build after 2.1.6 where Method-04 can execute** — 3/3 phantom read failures |
| 2.1.16 – 2.1.19 | Phantom reads confirmed (same as 2.1.15 behavior) |
| 2.1.20 | **Mixed**: 5 failures, 1 success, 5 context limit (11 trials) — revises prior Barebones-2120 finding of 0% failure |
| 2.1.21 | Mixed: 2 failures, 1 success (3 trials); no context limits |
| 2.1.22 | **100% failure**: 6/6 phantom read failures; no context limits |

**Build-Specific Behaviors Discovered:**
- Build 2.1.9: `/context` command changed to interstitial dialog (doesn't print to chat)
- Build 2.1.14: `/context` restored to original behavior
- Build 2.1.15: `/context` double-prints output (persists through 2.1.19, fixed in 2.1.20)
- Build 2.1.15: First npm-to-native installer transition warning
- No context overload errors observed in 2.1.21+ (18 total runs)

**Trial Collections Created:**
- `dev/misc/barebones-219` (3 trials, v2.1.9)
- `dev/misc/barebones-2114` (3 trials, v2.1.14)
- `dev/misc/barebones-2115` (3 trials, v2.1.15)
- `dev/misc/barebones-2120-2` (11 trials, v2.1.20)
- `dev/misc/barebones-2121` (3 trials, v2.1.21)
- `dev/misc/barebones-2122` (6 trials, v2.1.22)

**Pre-processing:** Ran `/update-trial-data` on barebones-2121 and barebones-2122 trials

**Significance:**
- Builds 2.1.7–2.1.14 represent a "dead zone" where our methodology cannot execute
- The prior Barebones-2120 study (5/5 success) is revised by the larger 11-trial study showing mixed results
- Build 2.1.22 provides a new reliable 100% failure case on a recent build
- Build 2.1.15 (Jan 21) is the earliest post-2.1.6 build where phantom reads can be studied

---

## 2026-01-29

**Build Scan Results Documentation**
- Created `docs/experiments/results/Experiment-04-BuildScan.md` — formal documentation of the build-by-build timeline and results from the Jan 28 scan
- Updated `docs/experiments/results/Barebones-2120-Analysis.md` with revised findings from the larger 11-trial study (revising the original 5-trial conclusions)

**Key Finding: Barebones-2121 Success Was a Protocol Violation**
- The single "success" in `dev/misc/barebones-2121` was identified as an invalid trial (agent violated protocol), NOT a genuine deviation from the failure pattern
- This prevents pursuit of red herrings when analyzing 2.1.21 results

**Build-Scan Discrepancy Investigation**
- Identified key open question: Why did the original Barebones-2120 study (`dev/misc/repro-attempts-04-2120`, 5/5 success) differ from the build-scan 2.1.20 results (`dev/misc/barebones-2120-2`, mixed) when run within the same ~4-hour window?
- Created investigation plan: `docs/experiments/planning/Build-Scan-Discrepancy-Investigation.md`
- Created analysis placeholder: `docs/experiments/results/Build-Scan-Discrepancy-Analysis.md` (for progressive multi-session analysis)

**Pre-Processing**
- Ran `/update-trial-data` on all 11 trials in `dev/misc/barebones-2120-2/` (previously unprocessed)

**Build-Scan Discrepancy Analysis (Steps 1.1–1.4)**
- Began multi-session analysis of the `barebones-2120-2` vs `repro-attempts-04-2120` discrepancy
- Completed Steps 1.1 through 1.4 of the investigation plan against `barebones-2120-2` trial data
- Results documented progressively in `docs/experiments/results/Build-Scan-Discrepancy-Analysis.md`

**Trial Data Schema Upgrade (1.2 → 1.3)**
- Analysis needs prompted design of Schema 1.3 improvements to `trial_data.json`
- Created ticket: `docs/tickets/open/upgrade-trial-data-schema-1-3.md`
- Refined via `/refine-plan` with 10-point design discussion
- Executed all phases via full WSD lifecycle (`/wsd:init`, `/wsd:prepare`, `/wsd:execute`, `/wsd:close`)
- Updated `dev/karpathy/extract_trial_data.py` and `.claude/commands/update-trial-data.md`

**Health Check Cleanup**
- Resolved 10 type checking errors, 6 doc completeness warnings, 22 linting issues (including 4 complex fixes)
- All health checks passing after cleanup

**Mass Re-Processing with Schema 1.3**
- Re-ran `/update-trial-data` on all build scan collections with the new Schema 1.3:
  - `dev/misc/repro-attempts-04-2120/` (5 trials)
  - `dev/misc/barebones-2120-2/` (11 trials)
  - `dev/misc/barebones-2121/` (3 trials)
  - `dev/misc/barebones-2122/` (6 trials)

---

## 2026-01-29 (Evening)

**Schema-13 Experiments** (CC v2.1.20 and v2.1.22, barebones repo)
- Ran additional trials on builds 2.1.20 and 2.1.22 using Method-04 with `/setup-hard`
- Collection `schema-13-2120`: 9 trials on v2.1.20 — 3 direct successes, 3 failures, 3 successes via Task agent delegation
- Collection `schema-13-2122`: 6 trials on v2.1.22 — ALL 6 succeeded, ALL used Task agent delegation
- Trial data collected via `collect_trials.py` and pre-processed with Schema 1.3 `/update-trial-data`

**Key Discovery: Task Agent Delegation as Confounding Variable**
- Session Agents in some trials delegated Read operations to Task sub-agents instead of reading files directly
- Delegation correlates with success: 100% of delegation trials succeeded across both builds
- In v2.1.20: 4/9 trials used delegation (all succeeded); 5 direct-read trials showed mixed results
- In v2.1.22: 5/6 trials used delegation (all succeeded)
- This explains the apparent "reversal" of 2.1.22 from 100% failure (Jan 28) to 100% success (Jan 29): agent behavioral shift to delegation, not a server-side change

**Significance:**
- Task agent delegation is a previously unrecognized confounding variable in trial outcomes
- Sub-agent reads may bypass the main session's context management, structurally avoiding phantom reads
- Future methodology must account for delegation vs. direct-read trial classification

---

## 2026-01-30

**Build-Scan Discrepancy Investigation Completed**
- Completed all remaining steps of the Build-Scan Discrepancy investigation (Steps 2.1–2.3, 3.1–3.3)
- Step 2.1: Analyzed schema-13-2120 (9 trials, v2.1.20) — confirmed persistence is non-deterministic within same time window; delegation identified as confound
- Step 2.2: Analyzed schema-13-2122 (6 trials, v2.1.22) — complete reversal from 100% failure (Jan 28) to 100% success (Jan 29); 0% persistence; confirms systemic server-side change
- Step 2.3: Analyzed schema-13-216 (6 trials, v2.1.6) — delegation confirmed on oldest tested build (3/6 trials); persistence 100% among direct-read trials; 2.1.6 behaviorally indistinguishable from newer builds on same day
- Step 3.1: Server-Side Variability Theory formalized
- Step 3.2: Build Scan conclusions revised (2.1.22 as reproduction target invalidated; 2.1.20 "fix" resolved as server-state variability)
- Step 3.3: Closure assessment completed — investigation shifts from experimentation to documentation/reporting

**Server-Side Variability Theory Formalized**
- Created [Server-Side-Variability-Theory.md](../theories/Server-Side-Variability-Theory.md)
- Core claim: Phantom read occurrence is primarily determined by server-side state, not client build version
- Evidence: Build 2.1.22 reversed from 100% failure (Jan 28) to 100% success (Jan 29) with zero environment changes
- Two distinct server-side changes identified: reduced persistence frequency + model behavioral shift to sub-agent delegation
- Characterization: Anthropic's changes are a **mitigation, not a fix** — persistence still 80–100% of direct reads; root cause unaddressed

**Schema-13-216 Collection** (CC v2.1.6, barebones repo)
- 6 trials: 2 FAILURE (direct-read), 3 SUCCESS (delegation), 1 SUCCESS (recovery from `<persisted-output>`)
- Collected via `collect_trials.py`, pre-processed with Schema 1.3
- Strongest evidence for server-side control: oldest tested build behaves identically to newest on same day

**Investigation Closure Recommended**
- Easy/Medium/Hard calibration (Aim #3) deemed infeasible under server-side variability
- Remaining planned experiments (04M, 04B, 04F, etc.) deprioritized — server-side variability undermines threshold analysis
- Project direction: shift to documentation, public reporting, and consolidation

**Public Communication Prepared**
- README.md update proposed to reflect latest findings for public viewers
- GitHub Issue #17407 update drafted summarizing three weeks of investigation for Anthropic maintainers
- Time-sensitive: mitigation effects observed in last 12–24 hours

---

## Pending Experiments

| Experiment | Description                                         | Status  |
| ---------- | --------------------------------------------------- | ------- |
| **04M**    | X Boundary Exploration - test intermediate X values | Deprioritized (server-side variability) |
| **04B**    | 8-File Y Threshold - narrow Y threshold range       | Deprioritized (server-side variability) |
| **04F**    | File Count vs Tokens - what triggers the threshold? | Deprioritized (server-side variability) |
| **04G**    | Sequential vs Parallel Reads - accumulation rate    | Deprioritized (server-side variability) |
| **04C**    | Sanity Check - restore pre-epsilon/phi state        | Deprioritized (server-side variability) |
| **Build Search** | Build scan 2.1.6→2.1.22 for behavior change | ✅ Completed (2026-01-28) |
| **2120 Repro** | Re-establish failure case on v2.1.20             | ✅ Resolved — server-state variability (2026-01-30) |
| **Build-Scan Discrepancy** | Investigate 2.1.20 result variability | ✅ Completed (2026-01-30) |

---

## Quick Reference: Key Documents by Topic

| Topic                 | Document                                                                                  |
| --------------------- | ----------------------------------------------------------------------------------------- |
| Unified theory        | [Consolidated-Theory.md](../theories/Consolidated-Theory.md)                              |
| Server-side variability | [Server-Side-Variability-Theory.md](../theories/Server-Side-Variability-Theory.md)       |
| Detailed narrative    | [Investigation-Journal.md](Investigation-Journal.md)                                      |
| Research questions    | [Research-Questions.md](Research-Questions.md)                                            |
| 22-trial analysis     | [WSD-Dev-02-Analysis-3.md](../experiments/results/WSD-Dev-02-Analysis-3.md)               |
| First reproduction    | [Repro-Attempts-02-Analysis-1.md](../experiments/results/Repro-Attempts-02-Analysis-1.md) |
| Experiment-04 results | [Experiment-04-Prelim-Results.md](../experiments/results/Experiment-04-Prelim-Results.md) |
| Barebones-216 analysis | [Barebones-216-Analysis.md](../experiments/results/Barebones-216-Analysis.md)             |
| Barebones-2120 analysis | [Barebones-2120-Analysis.md](../experiments/results/Barebones-2120-Analysis.md)           |
| Build scan results    | [Experiment-04-BuildScan.md](../experiments/results/Experiment-04-BuildScan.md)            |
| Build scan discrepancy | [Build-Scan-Discrepancy-Analysis.md](../experiments/results/Build-Scan-Discrepancy-Analysis.md) |
| Current methodology   | [Experiment-Methodology-04.md](../experiments/methodologies/Experiment-Methodology-04.md) |
| Workaround            | [WORKAROUND.md](../../WORKAROUND.md)                                                      |

---

*Last updated: 2026-01-30*
