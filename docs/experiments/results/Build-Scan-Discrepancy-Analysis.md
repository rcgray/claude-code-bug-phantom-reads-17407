# Build Scan Discrepancy Analysis

**Investigation ID**: Build-Scan-Discrepancy
**Planning Document**: `docs/experiments/planning/Build-Scan-Discrepancy-Investigation.md`
**Date Started**: 2026-01-29
**Date Analyzed**: 2026-01-30
**Triggered By**: Experiment-04-BuildScan results contradicting Barebones-2120 study

---

## Executive Summary

The Build Scan Discrepancy Investigation was triggered when build 2.1.20 showed 0% phantom read failure on Jan 27 and 86% failure on Jan 28 — the same build, the same protocol, the same environment. Across three phases of analysis spanning 55+ trials and 8 collections, the investigation traced this discrepancy to its root cause: **phantom read behavior is governed by server-side state, not client build version.**

The persistence mechanism — where the Claude Code harness saves tool results to disk and replaces them with `<persisted-output>` markers that the model ignores — is the sole determinant of phantom read occurrence. Whether persistence is enabled for a given session is controlled by Anthropic's server infrastructure and varies over time: 0% persistence on Jan 27, 100% on Jan 28, and ~80% (with a new sub-agent delegation behavior providing additional mitigation) on Jan 29. Build version adds no predictive value; build 2.1.6 (the oldest tested) is behaviorally indistinguishable from builds 2.1.20 and 2.1.22 on the same day.

Key findings: (1) `has_tool_results` is a near-perfect per-session outcome discriminator — false predicts SUCCESS with 100% accuracy (14/14), true predicts FAILURE with 85% accuracy (17/20, with 2 recoveries and 4 context overloads). (2) Persistence is chronological, not size-based — a 21-byte result is persisted while a 39KB file is not. (3) The session JSONL does not record phantom read markers; the persistence layer operates between logging and the model API call. (4) Post-reset context reconstruction reveals a ~42K token gap in failure trials, corresponding to file content replaced by compact markers. (5) Two independent server-side mitigations appeared on Jan 29: reduced persistence frequency and model preference for sub-agent delegation.

The investigation concludes that further experimentation yields diminishing returns — the key remaining unknown (what controls the server-side persistence decision) is outside our observation boundary. The project should shift from investigation to documentation and public reporting.

---

## The Discrepancy

On 2026-01-27, the Barebones-2120 experiment (`dev/misc/repro-attempts-04-2120/`) ran 5 trials on Claude Code build 2.1.20 and observed **0% failure rate** (5/5 SUCCESS). This led to the provisional conclusion that Anthropic had fixed phantom reads.

On 2026-01-28, the Experiment-04 Build Scan ran 11 additional trials on the **same build** (2.1.20) in collection `dev/misc/barebones-2120-2/` and observed **6 failures, 1 success, 4 context overloads** — an 86% failure rate among valid trials.

These experiments used the same protocol (Experiment-Methodology-04), the same test repository (`barebones-phantom-reads`), and were conducted within an estimated 4-hour window.

---

## Preliminary Findings (Pre-Investigation)

These findings were established during initial triage before the formal investigation began. They are documented in the planning document and reproduced here as the starting baseline.

### Finding 1: The Test Environment Did Not Change

Structural fingerprints are nearly identical across both collections:

| Metric            | repro-04-2120 (Jan 27)                                                         | barebones-2121 (Jan 28) |
| ----------------- | ------------------------------------------------------------------------------ | ----------------------- |
| File paths        | `/Users/gray/Projects/barebones-phantom-reads/docs/specs/*`                    | Same                    |
| Files targeted    | 9 spec files + WPD                                                             | Same 9 files            |
| Protocol sequence | `/context` → `/setup-hard` → `/context` → `/analyze-wpd` → inquiry → `/export` | Same                    |
| Post-setup tokens | 114,017–114,018                                                                | 114,223–114,226         |
| Baseline tokens   | 15,490 (trials 2–5)                                                            | 15,616                  |

The ~200-token difference in post-setup is negligible. This rules out environmental drift as the cause.

### Finding 2: `has_tool_results` Is the Discriminator

| Collection     | Trial  | Outcome | Files Read | Peak Tokens | has_tool_results |
| -------------- | ------ | ------- | ---------- | ----------- | ---------------- |
| repro-04-2120  | 095002 | SUCCESS | 9          | 159,633     | **false**        |
| repro-04-2120  | 100209 | SUCCESS | 9          | 172,990     | **false**        |
| repro-04-2120  | 100944 | SUCCESS | 9          | 173,000     | **false**        |
| barebones-2121 | 150640 | FAILURE | 9          | 159,840     | **true**         |
| barebones-2121 | 150657 | SUCCESS | **6**      | **131,802** | **false**        |
| barebones-2121 | 150706 | FAILURE | 9          | 159,856     | **true**         |

When the harness persisted tool results (`has_tool_results: true`), phantom reads occurred. When it did not, reads succeeded.

### Finding 3: The 2121 "Success" Was a Protocol Violation

Trial 150657 read only 6 files instead of 9, skipping `module-alpha.md`, `module-beta.md`, and `module-gamma.md`. This is an invalid trial.

---

## Phase 1: Existing Data Analysis

### Step 1.1: Pre-Process `barebones-2120-2`

**Objective**: Run `/update-trial-data` on all 11 trials in `dev/misc/barebones-2120-2/` to enable structural comparison with `repro-attempts-04-2120`.

**Status**: COMPLETE

**Pre-Processing Results**: All 11 trials successfully pre-processed. Each trial directory contains a `trial_data.json` (schema version 1.2).

#### Complete Trial Data Table

| Trial ID | Outcome | has_tool_results | Reads | Unique Files | Resets | Pattern     | Peak Tokens | 1st Reset From | 2nd Reset From | Baseline |
| -------- | ------- | ---------------- | ----- | ------------ | ------ | ----------- | ----------- | -------------- | -------------- | -------- |
| 134716   | UNKNOWN | **true**         | 19    | 19           | 1      | SINGLE_LATE | 123,111     | 123,111        | —              | 114,095  |
| 134724   | FAILURE | **true**         | 10    | 10           | 2      | OTHER       | 157,853     | 131,724        | 157,853        | 114,095  |
| 140143   | SUCCESS | **false**        | **6** | **6**        | 1      | SINGLE_LATE | 166,511     | 166,511        | —              | 114,098  |
| 140149   | FAILURE | **true**         | 10    | 10           | 2      | OTHER       | 138,641     | 123,114        | 138,641        | 114,095  |
| 140157   | FAILURE | **true**         | 10    | 10           | 2      | OTHER       | 151,788     | 131,733        | 151,788        | 114,099  |
| 142506   | UNKNOWN | **true**         | 14    | 14           | 1      | SINGLE_LATE | 151,778     | 131,722        | —              | 114,102  |
| 142515   | UNKNOWN | **true**         | 14    | 14           | 1      | SINGLE_LATE | 151,732     | 123,111        | —              | 114,100  |
| 142526   | FAILURE | **true**         | 10    | 10           | 2      | OTHER       | 151,763     | 131,722        | 151,763        | 114,099  |
| 143045   | UNKNOWN | **true**         | 14    | 14           | 1      | SINGLE_LATE | 151,711     | 123,114        | —              | 114,097  |
| 143056   | FAILURE | **true**         | 10    | 10           | 2      | OTHER       | 151,719     | 123,114        | 151,719        | 114,094  |
| 143105   | FAILURE | **true**         | 10    | 10           | 2      | OTHER       | 151,724     | 123,105        | 151,724        | 114,099  |

#### Comparison: Original 2120 Collection (repro-attempts-04-2120)

| Trial ID | Outcome | has_tool_results | Reads | Unique Files | Resets | Pattern     | Peak Tokens | Reset From | Baseline |
| -------- | ------- | ---------------- | ----- | ------------ | ------ | ----------- | ----------- | ---------- | -------- |
| 095002   | SUCCESS | **false**        | 9     | 9            | 1      | SINGLE_LATE | 159,633     | 159,633    | 114,017  |
| 100209   | SUCCESS | **false**        | 9     | 9            | 1      | SINGLE_LATE | 172,990     | 172,990    | 114,018  |
| 100701   | SUCCESS | **false**        | 9     | 9            | 1      | SINGLE_LATE | 172,999     | 172,999    | 114,023  |
| 100944   | SUCCESS | **false**        | 9     | 9            | 1      | SINGLE_LATE | 173,000     | 173,000    | 114,016  |
| 101305   | SUCCESS | **false**        | 9     | 9            | 1      | SINGLE_LATE | 159,921     | 159,921    | 114,017  |

#### Outcome Distribution

| Category                          | Count | Details                                               |
| --------------------------------- | ----- | ----------------------------------------------------- |
| FAILURE (confirmed phantom reads) | 6     | Trials 134724, 140149, 140157, 142526, 143056, 143105 |
| UNKNOWN (context overload)        | 4     | Trials 134716, 142506, 142515, 143045                 |
| SUCCESS                           | 1     | Trial 140143 (protocol violation — only 6 files read) |

#### Key Observations

**Observation 1: `has_tool_results` remains the perfect discriminator.**

All 10 trials with `has_tool_results: true` resulted in FAILURE or UNKNOWN. The single SUCCESS trial (140143) had `has_tool_results: false`. This is perfectly consistent with the preliminary findings from 2121 and the original 2120 collection. Across all data collected so far:

- `has_tool_results: false` → 100% SUCCESS (6/6 trials: 5 from original 2120, 1 from 2120-2)
- `has_tool_results: true` → 0% confirmed SUCCESS (0/12 trials across 2120-2 and 2121)

**Observation 2: The SUCCESS trial is another protocol violation.**

Trial 140143 read only 6 files: `pipeline-refactor.md` (WPD), `data-pipeline-overview.md`, `integration-layer.md`, `compliance-requirements.md`, `module-epsilon.md`, and `module-phi.md`. It skipped `module-alpha.md`, `module-beta.md`, and `module-gamma.md` — the exact same three files skipped in the barebones-2121 success trial (150657). By reading fewer files, the agent avoided triggering persistence and achieved a peak of 166K tokens with no persistence — identical to the original 2120 behavior. This trial is **invalid** as a data point for comparing success vs. failure because it avoided the conditions that trigger persistence.

**Observation 3: Two distinct behavioral profiles among `has_tool_results: true` trials.**

The 10 trials with persistence enabled split into two clear groups:

| Profile     | Trials | Outcome                   | Resets                     | Reads | Behavior                                                               |
| ----------- | ------ | ------------------------- | -------------------------- | ----- | ---------------------------------------------------------------------- |
| **FAILURE** | 6      | Confirmed phantom reads   | 2 (at ~69-71% and ~86-87%) | 10    | Agent ignored `<persisted-output>` markers                             |
| **UNKNOWN** | 4      | Session ended prematurely | 1 (at ~51-62%)             | 14-19 | Agent detected and attempted follow-up on `<persisted-output>` markers |

The UNKNOWN trials show agents that **correctly** detected `<persisted-output>` markers and attempted to re-read content from the `tool-results/` directory. However, this recovery attempt consumed additional context, and all 4 sessions hit context limits before the phantom read inquiry could be conducted. These 4 trials correspond to the "4 context overloads" reported in the investigation's problem statement.

The key distinction: FAILURE agents ignored deferred reads; UNKNOWN agents attempted recovery but ran out of context. Both groups had persistence enabled.

**Observation 4: First reset thresholds cluster into two bands.**

| Reset Band | Token Range     | Trials                                         |
| ---------- | --------------- | ---------------------------------------------- |
| ~123K      | 123,105–123,114 | 134716, 140149, 142515, 143045, 143056, 143105 |
| ~131K      | 131,722–131,733 | 134724, 140157, 142506, 142526                 |

All first resets drop to ~18,020–18,027 tokens (the base level). The two bands may reflect different read orderings or batch sizes triggering the threshold at slightly different cumulative points. Note that trial 140143 (SUCCESS, no persistence) reset at 166,511 — dramatically higher, because it accumulated all file content inline without persistence intercepting.

**Observation 5: The original 2120 collection resets at dramatically different thresholds.**

| Collection                | First Reset Range | Interpretation                                                            |
| ------------------------- | ----------------- | ------------------------------------------------------------------------- |
| repro-04-2120 (Jan 27)    | 159,633–173,000   | Reset after all 9 files read inline — too late to cause phantom reads     |
| barebones-2120-2 (Jan 28) | 123,105–131,733   | Reset during file processing — triggers persistence, causes phantom reads |

This is the most striking structural difference. When persistence is disabled (`has_tool_results: false`), the agent reads all files inline to 160-173K tokens, then a single late reset occurs harmlessly. When persistence is enabled (`has_tool_results: true`), the harness intercepts tool results at a lower threshold (~123-132K), persisting them to disk. This interception itself changes the session dynamics: the agent receives `<persisted-output>` markers instead of content, leading to phantom reads when the agent fails to follow up.

**Observation 6: Baselines are nearly identical, confirming environmental stability.**

| Collection                | Baseline Range  | Mean    |
| ------------------------- | --------------- | ------- |
| repro-04-2120 (Jan 27)    | 114,016–114,023 | 114,018 |
| barebones-2120-2 (Jan 28) | 114,094–114,102 | 114,098 |

The ~80-token difference is negligible. The test environment (files, protocol, repository state) did not change between the two sessions.

**Observation 7: Affected files are consistent across all FAILURE trials.**

All 6 FAILURE trials report the same 4 affected files:
- `data-pipeline-overview.md`
- `module-alpha.md`
- `module-beta.md`
- `module-gamma.md`

These are the files that received `<persisted-output>` markers that the agent failed to follow up on. The WPD file (`pipeline-refactor.md`) was also persisted in some trials but was successfully followed up on by the agent.

---

### Step 1.2: Compare 2120 Success vs 2120-2 Success

**Objective**: Compare the SUCCESS trial(s) in `barebones-2120-2` against the 5 SUCCESS trials in `repro-attempts-04-2120` to determine if they are structurally equivalent.

**Status**: COMPLETE

**Key Comparisons**:

| Metric              | repro-04-2120 SUCCESS trials (n=5) | barebones-2120-2 SUCCESS trial (140143) |
| ------------------- | ---------------------------------- | --------------------------------------- |
| `has_tool_results`  | **false** (all 5)                  | **false**                               |
| Peak token count    | 159,633–173,000                    | 166,511                                 |
| Files read (count)  | **9** (all 5 trials)               | **6**                                   |
| Post-setup baseline | 114,016–114,023                    | 114,098                                 |
| Reset count         | 1 (all 5 trials)                   | 1                                       |
| Reset pattern       | SINGLE_LATE (all 5)                | SINGLE_LATE                             |
| Reset threshold     | 159,633–173,000                    | 166,511                                 |
| Protocol compliance | **FULL**                           | **VIOLATION** — skipped 3 files         |

**Files read in trial 140143** (6 of 9):

| #   | File                       | Read?       |
| --- | -------------------------- | ----------- |
| 1   | pipeline-refactor.md (WPD) | Yes         |
| 2   | data-pipeline-overview.md  | Yes         |
| 3   | integration-layer.md       | Yes         |
| 4   | compliance-requirements.md | Yes         |
| 5   | module-alpha.md            | **SKIPPED** |
| 6   | module-beta.md             | **SKIPPED** |
| 7   | module-gamma.md            | **SKIPPED** |
| 8   | module-epsilon.md          | Yes         |
| 9   | module-phi.md              | Yes         |

**Findings**:

The 2120-2 SUCCESS trial is **not** a genuine structural match for the original 2120 successes. It is another protocol violation, identical in nature to the barebones-2121 success (trial 150657), which also read only 6 files and skipped the same three modules.

Where the trials superficially agree — `has_tool_results: false`, SINGLE_LATE reset pattern, peak tokens within the original range — these similarities are a *consequence* of the protocol violation, not independent confirmation. By reading only 6 files instead of 9, the agent consumed fewer tokens during its read operation, never triggered the persistence threshold, and therefore never encountered `<persisted-output>` markers. The trial avoided the failure condition rather than surviving it.

This means **there are zero valid SUCCESS trials in the 2120-2 collection**. Every trial that ran the full 9-file protocol on Jan 28 either failed (6 trials) or hit context limits during recovery attempts (4 trials). The original 2120 success pattern — reading all 9 files inline to 160-173K with no persistence — did not reproduce.

**Cross-collection protocol violation pattern**: The fact that two independent agents on different builds (2.1.20 in 2120-2 and 2.1.21 in 2121) both skipped the same three files (`module-alpha.md`, `module-beta.md`, `module-gamma.md`) suggests a consistent agent behavioral tendency when under context pressure. These three files are likely read in a batch or at a decision point where the agent can choose to skip them. This is not a harness difference — it is a model decision that happens to avoid the failure condition.

---

### Step 1.3: Compare Failure Profiles Across Collections

**Objective**: Verify that failure trials across collections share the same failure mechanism (`has_tool_results: true`, same affected files, same persistence behavior).

**Status**: COMPLETE

**Note**: The original table included a "216 Failures" column. No `barebones-216` collection exists. The closest available collection is `repro-attempts-04-barebones` (Jan 27, build unknown), which has been substituted. Collections `barebones-219`, `barebones-2114`, and `barebones-2115` lack `trial_data.json` files and cannot be included.

**Cross-Collection Failure Comparison**:

| Metric              | 2120-2 (n=6)                          | 2121 (n=2)         | 2122 (n=6)     | repro-04-barebones (n=4)    |
| ------------------- | ------------------------------------- | ------------------ | -------------- | --------------------------- |
| `has_tool_results`  | **true** (6/6)                        | **true** (2/2)     | **true** (6/6) | **true** (4/4)              |
| Affected file count | 4 (5/6 trials), 4 (1/6 different set) | 5 (2/2)            | 4–5 (varies)   | 3–9 (varies widely)         |
| Peak tokens         | 138K–158K                             | ~160K              | 132K–160K      | 133K–165K                   |
| Reset count         | 2 (all 6)                             | 1 (both)           | 1–2 (mixed)    | 2–3 (mixed)                 |
| 1st reset range     | 123K–132K                             | ~160K              | 132K–160K      | 125K–134K                   |
| Reset pattern       | OTHER (all 6)                         | SINGLE_LATE (both) | Mixed          | OTHER / EARLY_PLUS_MID_LATE |

#### Universal Finding: `has_tool_results` Is Absolute

Across all 18 FAILURE trials spanning 4 collections and at least 3 builds, `has_tool_results: true` is present in **100% of cases** (18/18). This is the only metric with perfect consistency. Combined with the 6 SUCCESS trials that all have `has_tool_results: false`, the discriminator holds with 100% accuracy across 24 classified trials.

#### Affected Files Are Position-Dependent, Not File-Dependent

The affected files vary between trials, even within the same collection. Frequency across all 18 failures:

| File                       | Affected | %    | Role                  |
| -------------------------- | -------- | ---- | --------------------- |
| module-alpha.md            | 18/18    | 100% | Always affected       |
| module-beta.md             | 15/18    | 83%  | Usually affected      |
| module-gamma.md            | 14/18    | 78%  | Usually affected      |
| data-pipeline-overview.md  | 14/18    | 78%  | Usually affected      |
| pipeline-refactor.md (WPD) | 7/18     | 39%  | Sometimes affected    |
| integration-layer.md       | 5/18     | 28%  | Occasionally affected |
| compliance-requirements.md | 5/18     | 28%  | Occasionally affected |
| module-epsilon.md          | 1/18     | 6%   | Rarely affected       |
| module-phi.md              | 1/18     | 6%   | Rarely affected       |

The variation is explained by **read order**. Agents read the 9 spec files in different sequences across trials. Files read after the persistence threshold is reached get `<persisted-output>` markers; files read before it receive inline content. `module-alpha.md` appears in every failure because it is consistently read early in the batch that crosses the threshold. `module-epsilon.md` and `module-phi.md` are almost never affected because they are typically read in positions that receive inline content.

Notably, 2120-2 trial 134724 has a different affected set (compliance-requirements, data-pipeline-overview, integration-layer, module-alpha) than the other 5 failures in the same collection, confirming that the affected files depend on the agent's read order, not on inherent file properties.

#### Two Distinct Reset Profiles Among Failures

Failures cluster into two reset profiles that appear across collections:

**Profile A — Mid-Session Double Reset:**
- 2 resets: first at ~123–132K, second at ~138–158K
- Pattern: OTHER
- Seen in: 2120-2 (6/6), 2122 (3/6), repro-04-barebones (2/4)
- Token progression example (2120-2 trial 134724): 15K → 114K → ... → 132K → **reset** → 18K → ... → 158K → **reset** → 18K

**Profile B — Late Single Reset:**
- 1 reset at ~160K
- Pattern: SINGLE_LATE
- Seen in: 2121 (2/2), 2122 (3/6)
- Token progression example (2121 trial 150640): 16K → 114K → ... → 123K → ... → 160K → **reset** → 18K

Both profiles produce phantom reads because `has_tool_results: true` in both cases — the harness persists tool results regardless of when the reset occurs. The persistence decision and the reset are **separate mechanisms**: persistence is triggered per-tool-result (when an individual result exceeds a size threshold), while resets are triggered by total context growth.

Profile A shows resets interrupting the read sequence mid-stream, while Profile B shows the agent completing all reads before a late reset. Both result in phantom reads because the `<persisted-output>` markers are delivered during the reads themselves, not caused by the reset.

**The 2122 collection is particularly instructive** because it contains both Profile A (3 trials) and Profile B (3 trials) within the same build, demonstrating that the reset profile is not build-dependent.

#### repro-04-barebones Shows an Extreme Variant

Trial 093127 stands out as the most extreme failure: 45 file reads(!), 3 resets, and all 9 files affected. This trial's agent attempted extensive recovery (reading tool-result files multiple times), driving 3 resets. Trial 094145 similarly shows 19 reads and 3 resets. These extreme cases demonstrate that aggressive recovery attempts can compound the problem rather than solving it.

#### Synthesis: One Root Cause, Variable Presentation

The failure mechanism is consistent across all collections at the fundamental level:

1. **Root cause**: `has_tool_results: true` — the harness persists tool results to disk
2. **Proximate cause**: Agent receives `<persisted-output>` markers and fails to follow up (or follows up too late)
3. **Variable factors**: Read order determines which files are affected; agent behavior determines the reset profile (ignoring markers → fewer resets; attempting recovery → more resets)

The structural variations (reset count, affected files, peak tokens) are **symptoms of the same disease presenting differently**, not evidence of different failure mechanisms.

---

### Step 1.4: Raw JSONL Deep Dive

**Objective**: Compare raw JSONL session files between a SUCCESS trial from `repro-attempts-04-2120` and a FAILURE trial from `barebones-2121` with similar peak tokens (~160K).

**Status**: COMPLETE

**Selected Trials for Comparison**:
- SUCCESS: Trial 095002 from `repro-attempts-04-2120` (build 2.1.20, Jan 27, peak 159,633 tokens)
- FAILURE: Trial 150640 from `barebones-2121` (build 2.1.21, Jan 28, peak 159,840 tokens)

These trials were selected for their near-identical peak token counts (~160K), allowing controlled comparison.

**Comparison Areas**:

| Area                     | SUCCESS Trial                   | FAILURE Trial                          | Difference                                                      |
| ------------------------ | ------------------------------- | -------------------------------------- | --------------------------------------------------------------- |
| Tool result format       | Full inline content, 10 results | Full inline content, 10 results        | **Identical** — no `<persisted-output>` markers in either JSONL |
| System message content   | 1 system message                | 1 system message                       | Structurally identical                                          |
| Harness behavior markers | No `tool-results/` directory    | `tool-results/` directory with 6 files | **Critical** — only external artifact                           |
| API response metadata    | Model: claude-opus-4-5-20251101 | Model: claude-opus-4-5-20251101        | Same model                                                      |
| Token accounting         | Post-reset total_input: 197,740 | Post-reset total_input: 155,715        | **42,025 token gap**                                            |

#### Finding 1: The JSONL Records Identical Content — No `<persisted-output>` Markers Anywhere

Every tool result in both sessions contains the **full file content**. Content lengths are byte-for-byte identical across all 9 file reads:

| File                       | SUCCESS Length | FAILURE Length | Match |
| -------------------------- | -------------- | -------------- | ----- |
| pipeline-refactor.md       | 28,371         | 28,371         | ✓     |
| module-alpha.md            | 29,348         | 29,348         | ✓     |
| module-beta.md             | 30,441         | 30,441         | ✓     |
| data-pipeline-overview.md  | 35,896         | 35,896         | ✓     |
| module-gamma.md            | 37,745         | 37,745         | ✓     |
| integration-layer.md       | 26,353         | 26,353         | ✓     |
| compliance-requirements.md | 21,779         | 21,779         | ✓     |
| module-epsilon.md          | 36,196         | 36,196         | ✓     |
| module-phi.md              | 38,734         | 38,734         | ✓     |

The `<persisted-output>` markers that the FAILURE agent experienced are **not recorded in the session JSONL**. This definitively confirms the Trial Analysis Guide's hypothesis: the session `.jsonl` is a log of tool execution results, not a representation of what the model receives in its context window. Content persistence/substitution happens in a layer between JSONL logging and the API call to the model.

#### Finding 2: The `tool-results/` Directory Is the Sole Artifact of Persistence

The FAILURE trial has a session subdirectory containing `tool-results/` with 6 persisted files. The SUCCESS trial has no session subdirectory at all.

**Persistence mapping (FAILURE trial)**:

| #   | JSONL Line | Tool | File                       | Size     | Persisted? |
| --- | ---------- | ---- | -------------------------- | -------- | ---------- |
| 1   | 8          | Bash | `date` command             | 21 B     | **YES**    |
| 2   | 21         | Read | pipeline-refactor.md       | 28.59 KB | **YES**    |
| 3   | 25         | Read | data-pipeline-overview.md  | 39.12 KB | **YES**    |
| 4   | 26         | Read | module-alpha.md            | 31.14 KB | **YES**    |
| 5   | 27         | Read | module-beta.md             | 32.27 KB | **YES**    |
| 6   | 28         | Read | module-gamma.md            | 39.47 KB | **YES**    |
| 7   | 38         | Read | integration-layer.md       | 26.35 KB | no         |
| 8   | 39         | Read | compliance-requirements.md | 21.78 KB | no         |
| 9   | 40         | Read | module-epsilon.md          | 36.20 KB | no         |
| 10  | 41         | Read | module-phi.md              | 38.73 KB | no         |

The persistence boundary falls cleanly between the first batch of reads (lines 8–28, all persisted) and the second batch (lines 38–41, none persisted). This is a **chronological** split, not a size-based one.

#### Finding 3: Persistence Is NOT Size-Based

The 21-byte date command result was persisted alongside 28–39 KB file reads. Meanwhile, the 38.73 KB `module-phi.md` (the largest file read) was **not** persisted. This conclusively rules out a per-result size threshold as the persistence mechanism.

The persisted results are the **earliest 6 tool results** in the session. The non-persisted results are the **latest 4**. This is consistent with a context compaction mechanism that persists older tool results to free space, regardless of their size.

#### Finding 4: Post-Reset Token Accounting Reveals the 42K Gap

The most significant finding from the JSONL that `trial_data.json` does not capture is the **post-reset cache creation difference**:

| Metric                      | SUCCESS (L56) | FAILURE (L58) | Difference  |
| --------------------------- | ------------- | ------------- | ----------- |
| Pre-reset `cache_read`      | 159,633       | 159,840       | +207        |
| Post-reset `cache_read`     | 17,942        | 18,148        | +206        |
| Post-reset `cache_creation` | **179,788**   | **137,557**   | **−42,231** |
| Post-reset `total_input`    | **197,740**   | **155,715**   | **−42,025** |

After the context reset, the SUCCESS trial re-cached 179,788 tokens — nearly the full conversation. The FAILURE trial re-cached only 137,557 tokens, a **42,025 token deficit**. This deficit represents the content of persisted tool results that was replaced by compact `<persisted-output>` markers during context reconstruction.

The 42K token gap corresponds well to the 5 persisted file reads. Total persisted file content: ~170.6 KB of characters. At approximately 4 characters per token, this is ~42,650 tokens — closely matching the observed 42,231 token difference in `cache_creation`.

**Interpretation**: When the context reset occurred, the harness reconstructed the context by re-inserting all conversation content. For the SUCCESS trial, all tool results were re-inserted as full content (179K tokens). For the FAILURE trial, persisted tool results were replaced with `<persisted-output>` markers (~100 tokens each instead of ~8,000), resulting in 42K fewer tokens of actual content available to the model. The model then responded based on this truncated context, producing phantom reads.

#### Finding 5: The FAILURE Agent Produced Longer Analysis Despite Less Content

| Trial         | Analysis text length (chars) | Actual content available           |
| ------------- | ---------------------------- | ---------------------------------- |
| SUCCESS (L48) | 7,560                        | Full content of all 9 files        |
| FAILURE (L50) | 10,375                       | Content of 4 files + markers for 5 |

The FAILURE agent produced a 37% longer analysis despite having access to significantly less actual file content. This is consistent with confabulation — the agent generated plausible-sounding analysis for files it never actually read, resulting in more verbose (and fabricated) output. The agent later confirmed: its analysis was "fabricated" based on files never actually read.

#### Finding 6: Pre-Reset Session Structure Is Virtually Identical

Both sessions follow the exact same sequence:

```
L1-7:   User inputs (/context, /setup-hard, /analyze-wpd)
L8:     Assistant calls Bash (date command)
L9:     Tool result (date)
L10-11: Assistant produces Workscope ID text
L12-17: User inputs (/context, /analyze-wpd prompt)
L18-20: Assistant reads pipeline-refactor.md
L22-35: Assistant reads 4 files batch (alpha, beta, overview, gamma)
L37-48: Assistant reads 4 files batch (integration, compliance, epsilon, phi)
L48-50: Assistant produces analysis
L51:    System message
L53-57: User inputs (/context, inquiry prompt)
L56-58: Context reset
L56-59: Assistant responds about phantom reads
L59-67: Export and exit
```

The only structural difference is 2 extra lines in the FAILURE JSONL (68 vs 66 total). The tool call sequence, batching pattern, file read order, and conversation flow are otherwise identical.

#### Finding 7: Usage Patterns Track Within ~200 Tokens Until the Reset

| Sequence             | SUCCESS `cache_read` | FAILURE `cache_read` | Difference |
| -------------------- | -------------------- | -------------------- | ---------- |
| 1 (initial)          | 10,330               | 15,616               | +5,286     |
| 2 (post-setup)       | 114,017              | 114,223              | +206       |
| 3-4 (pre-reads)      | 114,148              | 114,337              | +189       |
| 5-9 (first batch)    | 115,669              | 115,874              | +205       |
| 10-14 (second batch) | 123,029              | 123,237              | +208       |
| 15 (pre-reset)       | 159,633              | 159,840              | +207       |
| 16 (post-reset)      | 17,942               | 18,148               | +206       |

The ~200-token offset is consistent throughout (except the initial 5,286 gap, which is likely a build version difference in system prompt size between 2.1.20 and 2.1.21). This near-perfect tracking confirms the two sessions are structurally equivalent from the API's perspective — the divergence occurs entirely in the harness layer between the JSONL log and the model.

#### Finding 8: The Persistence Decision Is Invisible in Session Data

Nothing in the pre-reset JSONL data distinguishes the SUCCESS trial from the FAILURE trial. The `cache_read`, `cache_creation`, `input_tokens`, and `output_tokens` values track within ~200 tokens. Both sessions hit the same total_input (~194K) before the reset. The only way to detect that persistence occurred is by examining the `tool-results/` directory — an artifact that exists entirely outside the session JSONL.

This means the persistence decision is made by the harness based on factors **external to the logged session data**. Possible factors include:
- Build version (client-side persistence configuration)
- Server-side API configuration (persistence thresholds, A/B testing)
- Session initialization state (presence of a session subdirectory)
- Temporal factors (time of day, server load)

The JSONL itself cannot explain the discrepancy.

---

## Phase 1 Synthesis

Phase 1 analyzed all available data across 4 collections (repro-04-2120, barebones-2120-2, barebones-2121, barebones-2122) plus repro-04-barebones, totaling 35 trials. The following conclusions emerge.

### The Root Cause Chain Is Fully Mapped

The Build Scan discrepancy is caused by a single binary decision: **whether the Claude Code harness persists tool results to disk.** The causal chain is:

1. **Harness persistence decision** → The harness either persists tool results to `tool-results/` files or delivers them inline. This decision is made per-session and appears to be all-or-nothing (no mixed sessions observed).
2. **Context reconstruction with markers** → When persistence is active, the context sent to the model replaces persisted tool results with `<persisted-output>` markers. This is invisible in the session JSONL, which always records full content.
3. **Agent fails to follow up** → The model receives markers instead of content but (in FAILURE cases) proceeds as if it received the actual file content, generating fabricated analysis.
4. **42K token context gap** → Post-reset cache reconstruction reveals a ~42,000 token gap in FAILURE trials: content that was persisted to disk and replaced by compact markers, never reaching the model's effective context.

### What We Know vs. What We Don't Know

**Established with high confidence (n=24+ trials):**
- `has_tool_results` is a 100% accurate discriminator between SUCCESS and FAILURE outcomes
- Persistence is positional/chronological, not size-based (21-byte date results get persisted; 39KB files do not)
- The session JSONL does NOT record `<persisted-output>` markers — the persistence layer operates between JSONL logging and the model API call
- The persistence decision is invisible in session data — pre-reset JSONL content is structurally identical between SUCCESS and FAILURE trials
- All zero-persistence sessions succeed; all persistence sessions either fail or hit context overload attempting recovery

**Not yet established:**
- **What triggers the harness to enable persistence.** The same build (2.1.20) produced zero persistence on Jan 27 and 100% persistence on Jan 28, with identical environments. This is the central unanswered question.
- **Whether the persistence decision is client-side or server-side.** It could be a harness configuration change, a server-side parameter, or an interaction between the two.
- **Whether the discrepancy is reproducible today.** We don't know if re-running build 2.1.20 would produce the Jan 27 pattern (no persistence) or the Jan 28 pattern (persistence).

### Implications for Phase 2

**Step 2.1 (Re-run 2.1.20) is high priority.** The central question — why did persistence behavior change between Jan 27 and Jan 28 — cannot be answered from existing data alone. Running new trials on 2.1.20 today will determine:
- If persistence is now consistently enabled (matching Jan 28): The Jan 27 success was a transient state, possibly due to a server-side change that was later reverted.
- If persistence is now disabled (matching Jan 27): The behavior is unstable over time, suggesting server-side variability.
- If results are mixed: The persistence decision may have a stochastic component.

**Step 2.2 (Re-run 2.1.22 as control) is valuable.** If 2.1.22 now produces successes (when it previously showed 100% failure), that would indicate a systemic server-side change affecting all builds.

**Step 2.3 (Cross-machine) remains low priority.** The environmental fingerprint analysis in Steps 1.1–1.2 strongly rules out machine-specific factors. The ~200-token offset between builds and the identical file content confirm the test environment is stable.

### Revised Understanding of the Discrepancy

The original framing of the discrepancy was: "the same experiment produced different results on the same build." Phase 1 reveals this is more precisely stated as: "the Claude Code harness made different persistence decisions for the same workload on the same build at different times." The experiment itself (files, protocol, token consumption) was identical. The variable is a binary harness-level decision — persist or don't persist — that determines whether phantom reads occur.

This reframing shifts the investigation from "what changed in the experiment" (nothing did) to "what controls the harness persistence decision" (unknown, but likely external to the session).

---

## Phase 2: Targeted Experiments

### Step 2.1: Replication Attempt on Build 2.1.20

**Objective**: Re-run Experiment-Methodology-04 on build 2.1.20 (3–5 trials) to test whether the original success pattern is reproducible.

**Status**: COMPLETE — Collection `schema-13-2120` (9 trials, Jan 29)

#### Complete Trial Data Table

| Trial ID | Outcome | has_tool_results | has_subagents | Main-Session Reads | Resets | Pattern | Peak total_input | 1st Reset From | Compaction Loss (1st) | Initial Cache |
| -------- | ------- | ---------------- | ------------- | ------------------ | ------ | ------- | ---------------- | -------------- | --------------------- | ------------- |
| 202633 | SUCCESS | **false** | false | 9 (full protocol) | 1 | SINGLE_LATE | 174,919 | 131,709 | −43,207 | 10,331 |
| 202641 | FAILURE | **true** | false | 15 (9 + recovery) | 3 | OTHER | 180,656 | 131,625 | −15,426 | 15,491 |
| 203017 | SUCCESS | **false** | **true** | 1 (delegation) | 1 | SINGLE_LATE | 134,021 | 123,109 | −10,909 | 15,491 |
| 203726 | SUCCESS | **false** | **true** | 4 (delegation) | 1 | SINGLE_LATE | 154,433 | 131,701 | −22,729 | 15,491 |
| 203737 | FAILURE | **true** | false | 11 (9 + recovery) | 2 | OTHER | 176,609 | 131,625 | −26,143 | 15,491 |
| 203749 | SUCCESS | **true** | false | 14 (9 + recovery) | 2 | OTHER | 180,252 | 131,626 | −15,410 | 15,491 |
| 204305 | SUCCESS | **false** | **true** | 1 (delegation) | 1 | SINGLE_LATE | 132,570 | 123,102 | −9,465 | 15,491 |
| 204311 | FAILURE | **true** | false | 12 (9 + recovery) | 2 | OTHER | 176,648 | 123,102 | −34,660 | 15,491 |
| 204316 | SUCCESS | **false** | **true** | 1 (delegation) | 1 | SINGLE_LATE | 136,889 | 127,833 | −9,053 | 15,491 |

#### Outcome Distribution

| Category | Count | Trials |
| -------- | ----- | ------ |
| SUCCESS (no persistence) | 1 | 202633 |
| SUCCESS (sub-agent delegation) | 4 | 203017, 203726, 204305, 204316 |
| SUCCESS (persistence + recovery) | 1 | 203749 |
| FAILURE (persistence, phantom reads) | 3 | 202641, 203737, 204311 |

#### Observation 1: The Original Success Pattern Was Reproduced — Once

Trial 202633 is a genuine reproduction of the Jan 27 pattern. It read all 9 spec files inline in the main session, had `has_tool_results: false`, exhibited a SINGLE_LATE reset with negative compaction loss (−43,207), and the agent confirmed no `<persisted-output>` markers were encountered. The peak total_input of 174,919 is consistent with the original repro-04-2120 range (159K–173K total_input, noting that the original collection reports peak_cache_read rather than total_input). This trial demonstrates that the zero-persistence condition that produced 5/5 successes on Jan 27 **can still occur** on the same build two days later.

However, this was the only direct-read trial without persistence. Among the 5 trials where the agent read files directly in the main session (no sub-agent delegation), 4/5 (80%) had persistence enabled. The original success pattern is reproducible but rare under current conditions.

#### Observation 2: Sub-Agent Delegation Is a New Behavioral Confound

Four trials (203017, 203726, 204305, 204316) show a behavioral pattern not observed in any prior collection: the agent delegated most or all spec file reads to Task/Explore sub-agents. Sub-agents operate in their own context windows, so their file reads do not contribute to the main session's token accumulation. This means the main session never reached the persistence trigger.

Evidence of delegation from chat exports:
- Trial 204305: `Explore(Read pipeline specs for WPD review)` — 1 file in main session, 8 via sub-agent
- Trial 203726: 4 files read directly, then `Explore(Read module specs for analysis)` — 5 via sub-agent
- Trials 203017 and 204316: Similar delegation patterns

The delegation trials all show `has_tool_results: false` and dramatically lower peak total_input (132K–154K vs 174K–181K for direct-read trials), confirming that sub-agent delegation effectively bypasses the persistence mechanism. These trials succeeded not by surviving the persistence condition, but by avoiding it entirely through a different reading strategy.

This is functionally analogous to the "protocol violations" in barebones-2120-2 (trials reading only 6 files), but achieved through delegation rather than omission — the files were genuinely read, just not in the main session context.

**Implication for methodology**: The sub-agent delegation pattern was not observed in Jan 27 or Jan 28 trials. It may reflect a behavioral tendency that has emerged through model updates or may be stochastic. Future experiments may need to account for this confound, either by designing protocols that prevent delegation or by tracking it as a variable.

#### Observation 3: Recovery from `<persisted-output>` Is Possible

Trial 203749 is the first confirmed SUCCESS with `has_tool_results: true` across all collections analyzed in this investigation. The agent received `<persisted-output>` markers for 5 files (pipeline-refactor.md, data-pipeline-overview.md, integration-layer.md, compliance-requirements.md, module-alpha.md) but detected the markers and read the persisted tool-result files. The agent's self-report states: "This session is not a reproduction of the described bug. The follow-up reads succeeded." Some files were read partially (via limit parameters).

This trial is structurally similar to the UNKNOWN (context overload) trials in barebones-2120-2 — both show agents attempting to recover from `<persisted-output>` markers. The difference is that 203749's agent completed the recovery without exhausting context, while the 2120-2 UNKNOWN agents ran out of context during recovery. The key difference may be the recovery strategy: 203749 used limit parameters to read partial file content, reducing token consumption during recovery.

**Impact on the `has_tool_results` discriminator**: Prior to this trial, `has_tool_results` was a perfect binary discriminator (100% accuracy across 24 classified trials). Trial 203749 breaks this perfection. The revised discriminator is:

| has_tool_results | Outcome | Count | Percentage |
| ---------------- | ------- | ----- | ---------- |
| false | SUCCESS | 6 (original 2120) + 5 (schema-13-2120) = 11 | 100% SUCCESS |
| true | FAILURE | 3 (schema-13-2120) + 12 (prior collections) = 15 | 88% FAILURE |
| true | SUCCESS (recovery) | 1 (schema-13-2120) | 6% SUCCESS |
| true | UNKNOWN (overload) | 4 (barebones-2120-2) | N/A |

`has_tool_results: false` remains a perfect predictor of SUCCESS. `has_tool_results: true` is necessary for FAILURE but no longer sufficient — recovery is possible.

#### Observation 4: Persistence Is Not Uniform Within a Time Window

This is the most significant finding for RQ-BSD-1. Within the same ~20-minute window (20:26–20:43 on Jan 29), sessions on the same build showed **mixed** persistence behavior:

| Persistence state | Trials | Count |
| ----------------- | ------ | ----- |
| No persistence | 202633, 203017, 203726, 204305, 204316 | 5/9 (56%) |
| Persistence enabled | 202641, 203737, 203749, 204311 | 4/9 (44%) |

Prior collections showed uniform behavior:
- repro-04-2120 (Jan 27): 0% persistence (5/5 sessions)
- barebones-2120-2 (Jan 28): 100% persistence (11/11 sessions)
- schema-13-2120 (Jan 29): **mixed** — 44% persistence

However, the 5 non-persistence trials include 4 sub-agent delegation trials where the main session read 1–4 files. If we restrict to direct-read trials (no sub-agents), the persistence rate is 4/5 (80%). The single non-persistence direct-read trial (202633) was the first trial in the collection, starting with a lower initial cache (10,331 vs 15,491 for all subsequent trials). Whether the cold-cache state influenced the persistence decision is unknown but noted.

#### Observation 5: Affected Files Remain Consistent with Prior Findings

The 3 FAILURE trials show the same affected file pattern established in Step 1.3:

| File | 202641 | 203737 | 204311 | Affected in prior collections |
| ---- | ------ | ------ | ------ | ----------------------------- |
| module-alpha.md | **YES** | **YES** | **YES** | 100% (18/18) |
| module-beta.md | **YES** | — | — | 83% (15/18) |
| module-gamma.md | **YES** | — | — | 78% (14/18) |
| module-epsilon.md | **YES** | — | — | 6% (1/18) |
| data-pipeline-overview.md | — | **YES** | **YES** | 78% (14/18) |
| integration-layer.md | — | **YES** | — | 28% (5/18) |

`module-alpha.md` remains affected in 100% of failures (now 21/21 across all collections). The variation in other affected files continues to reflect read order differences rather than file-specific properties.

#### Observation 6: First Reset Thresholds Cluster Consistently

| Reset Band | Token Range | Trials |
| ---------- | ----------- | ------ |
| ~123K | 123,102–123,109 | 203017, 204305, 204311 |
| ~128K | 127,833 | 204316 |
| ~131K | 131,625–131,709 | 202633, 202641, 203726, 203737, 203749 |

The ~123K and ~131K bands are consistent with the barebones-2120-2 findings (Step 1.1, Observation 4). The ~128K value for trial 204316 is a new intermediate band. All reset drops go to ~18,021–18,027 (the base level), consistent across all collections.

Notably, trial 204311 (FAILURE, persistence) and trial 204305 (SUCCESS, no persistence) both reset at exactly 123,102 tokens. This confirms Phase 1's finding that the reset threshold itself does not determine the persistence decision — two structurally identical sessions can diverge based on a persistence decision made independently of their token state.

#### Step 2.1 Interpretation

The results are **MIXED**, which the investigation plan identified as suggesting **stochastic server-side behavior**. Specifically:

1. **The original 2120 success pattern is reproducible but rare.** Under current API conditions (Jan 29), a build 2.1.20 session reading all 9 files inline without persistence succeeded once out of five attempts (20%). The Jan 27 pattern of 100% success is not the current norm.

2. **The persistence decision is non-deterministic.** Within the same time window on the same build, some sessions have persistence enabled and some do not. This rules out a simple "the API changed on date X" explanation and points to a stochastic or session-initialization-dependent mechanism.

3. **The dominant state has shifted toward persistence.** Across the three 2120 test windows:
   - Jan 27: 0% persistence (5 trials)
   - Jan 28: 100% persistence (11 trials)
   - Jan 29: 80% persistence among direct-read trials (4/5), 44% overall (4/9)

   The trend suggests persistence is now the default behavior, with occasional non-persistence sessions occurring stochastically.

4. **Agent behavioral variation is a significant confound.** Sub-agent delegation (4/9 trials) and successful recovery from persistence (1/9 trials) introduce outcome variability independent of the persistence mechanism. Future experiments need to control for or track these behavioral variables.

---

### Step 2.2: Replication on Build 2.1.22 as Control

**Objective**: Run 3 trials on build 2.1.22 to confirm it still shows 100% failure. Serves as a control for API stability.

**Status**: COMPLETE — Collection `schema-13-2122` (6 trials, Jan 29)

#### Complete Trial Data Table

| Trial ID | Outcome | has_tool_results | has_subagents | Main-Session Reads | Resets | Pattern | Peak total_input | 1st Reset From | Compaction Loss (1st) | Initial Cache |
| -------- | ------- | ---------------- | ------------- | ------------------ | ------ | ------- | ---------------- | -------------- | --------------------- | ------------- |
| 210131 | SUCCESS | **false** | **true** | 1 (delegation) | 1 | SINGLE_LATE | 136,511 | 123,238 | −13,270 | 15,617 |
| 210142 | SUCCESS | **false** | **true** | 1 (delegation) | 1 | SINGLE_LATE | 139,598 | 123,231 | −16,364 | 15,617 |
| 210155 | SUCCESS | **false** | **true** | 1 (delegation) | 1 | SINGLE_LATE | 135,425 | 123,234 | −12,188 | 15,617 |
| 211057 | SUCCESS | **false** | **true** | 1 (delegation) | 1 | SINGLE_LATE | 140,243 | 123,238 | −17,002 | 15,617 |
| 211105 | SUCCESS | **false** | **true** | 1 (delegation) | 1 | SINGLE_LATE | 138,888 | 123,240 | −15,645 | 15,617 |
| 211109 | SUCCESS | **false** | false | 9 (full protocol) | 1 | SINGLE_LATE | 198,434 | 162,740 | −35,691 | 15,617 |

#### Outcome Distribution

| Category | Count | Trials |
| -------- | ----- | ------ |
| SUCCESS (sub-agent delegation) | 5 | 210131, 210142, 210155, 211057, 211105 |
| SUCCESS (direct read, full protocol) | 1 | 211109 |
| FAILURE | 0 | — |

#### Comparison with Prior barebones-2122 Collection (Jan 28)

| Metric | barebones-2122 (Jan 28, n=6) | schema-13-2122 (Jan 29, n=6) |
| ------ | ---------------------------- | ---------------------------- |
| Outcome | **6/6 FAILURE** (100%) | **6/6 SUCCESS** (0% failure) |
| `has_tool_results` | **true** (6/6) | **false** (6/6) |
| `has_subagents` | false (6/6) | true (5/6), false (1/6) |
| Main-session reads | 9–10 per trial | 1 per trial (5), 9 per trial (1) |
| Peak total_input | 167K–195K | 135K–198K |
| Reset count | 1–2 (mixed) | 1 (all) |
| Reset pattern | Mixed (OTHER / SINGLE_LATE) | SINGLE_LATE (all) |
| Baseline | 15,617 (all) | 15,617 (all) |

#### Observation 1: Complete Reversal — 100% Failure to 100% Success

Build 2.1.22, previously the most reliable reproduction target with 100% failure (6/6 on Jan 28), now shows **0% failure** (0/6 on Jan 29). This is the systemic change scenario the investigation plan identified as the key control signal: "If 2.1.22 also suddenly shows successes, we know something systemic changed."

The reversal is total. Not a single trial showed persistence (`has_tool_results: true`), compared to 100% persistence in the prior collection. This rules out stochastic variation as the sole explanation — a probabilistic persistence mechanism would need to produce at least some persistence in 6 trials if the base rate were anywhere near the prior 100%.

#### Observation 2: Sub-Agent Delegation Dominates Again

Five of six trials (83%) used sub-agent delegation, with the main session reading only the WPD (`pipeline-refactor.md`) and delegating all 8 spec file reads to Task/Explore sub-agents. This is the same pattern observed in schema-13-2120, where 4/9 trials (44%) used delegation.

The delegation pattern was absent in all prior collections (Jan 27–28). Its sudden appearance across both schema-13 collections (Jan 29, two builds) suggests a behavioral change in the model — either a model update or a stochastic shift in the model's tool-use strategy. The delegation effectively bypasses the persistence mechanism by keeping main-session token accumulation below the trigger threshold.

#### Observation 3: Trial 211109 Is the Critical Data Point

Trial 211109 is the **sole direct-read trial** in the collection and the most important data point for the control question. It read all 9 spec files directly in the main session without sub-agent delegation, reaching a peak `total_input` of **198,434** — nearly the 200K context limit. Despite this extreme context pressure:

- `has_tool_results: false` — no persistence occurred
- `has_subagents: false` — no delegation
- 9 files read successfully (full protocol compliance)
- SINGLE_LATE reset at 162,740 `cache_read` (79.7% position)
- Compaction loss: −35,691 (large negative = full content reconstruction)
- Agent confirmed: "No, I did not experience that issue in this session."

This trial is structurally identical to the original repro-04-2120 SUCCESS pattern — all files read inline, single late reset, negative compaction loss, full content available to the model. The key difference: this is on build 2.1.22, which showed 100% failure with 100% persistence just one day earlier.

The reset at 162,740 is particularly notable. In the prior barebones-2122 collection, trials with persistence showed first resets at 132K–160K. Trial 211109 reset at 163K with no persistence — the harness allowed the session to accumulate all file content inline to a higher threshold than any prior 2.1.22 trial before resetting. This is consistent with the Jan 27 repro-04-2120 pattern (resets at 160K–173K, no persistence).

#### Observation 4: Baselines Confirm Environmental Stability

All 6 schema-13-2122 trials show identical initial cache of 15,617 tokens — matching the prior barebones-2122 collection exactly. The test environment (files, protocol, repository state, build) is unchanged. The only variable is the date: Jan 28 vs Jan 29.

#### Observation 5: Delegation Trials Show Uniform Structure

The 5 delegation trials are remarkably uniform:

| Metric | Range | Notes |
| ------ | ----- | ----- |
| Initial cache | 15,617 (all) | Identical |
| Peak cache_read | 123,231–123,240 | ~9-token spread |
| Peak total_input | 135,425–140,243 | ~5K spread |
| Reset from | 123,231–123,240 | Matches peak cache_read |
| Reset to | 18,148–18,153 | Standard base level |
| Compaction loss | −12,188 to −17,002 | All negative (no content loss) |
| Session lines | 61–63 | Nearly identical session length |

This uniformity confirms that delegation trials follow a highly reproducible path: setup → read WPD → delegate spec reads to sub-agent → produce analysis → inquiry → reset → respond → export. The main session never accumulates enough file content to approach the persistence trigger.

#### Observation 6: Timing Relative to schema-13-2120

The schema-13-2122 trials ran approximately 20–30 minutes after the schema-13-2120 trials:

| Collection | Time range | Persistence rate (direct-read) |
| ---------- | ---------- | ------------------------------ |
| schema-13-2120 | 20:26–20:43 (Jan 29) | 80% (4/5 direct-read trials) |
| schema-13-2122 | 21:01–21:11 (Jan 29) | **0%** (0/1 direct-read trial) |

The schema-13-2120 collection showed 80% persistence among direct-read trials (4/5). Thirty minutes later, the schema-13-2122 collection showed 0% persistence (0/1 direct-read, 0/6 overall). However, with only 1 direct-read trial in the 2122 collection, the apparent difference could be sampling noise — a single non-persistence trial is consistent with the ~20% non-persistence rate observed in 2120's direct-read trials. The 5 delegation trials cannot distinguish persistence rates because they never reach the threshold.

#### Step 2.2 Interpretation

The control test produced a result opposite to the expected outcome. Rather than confirming continued 100% failure, build 2.1.22 showed **100% success with 0% persistence**. This is the strongest evidence yet that **something systemic changed** between the Jan 28 test session and the Jan 29 test session.

The findings can be interpreted at two levels:

**1. The persistence mechanism appears disabled or substantially reduced.**

Across both schema-13 collections (builds 2.1.20 and 2.1.22 on Jan 29), no delegation trial showed persistence, and only 4/5 direct-read trials on 2.1.20 showed persistence. The single direct-read trial on 2.1.22 (211109) showed zero persistence despite reaching 198K total_input — well above the thresholds where persistence was universally triggered on Jan 28. This suggests the harness persistence mechanism has been modified, possibly disabled, or is now triggering at a much higher threshold.

**2. Sub-agent delegation is now the dominant reading strategy.**

The model's strong preference for delegation (5/6 trials on 2.1.22, 4/9 on 2.1.20) means that even if persistence were still enabled, most trials would avoid it. This behavioral change — absent in all prior collections — independently reduces the observed failure rate regardless of the underlying persistence mechanism.

**Impact on investigation conclusions:**

The control test was designed to validate the Build Scan methodology by confirming a stable failure condition. Instead, it revealed that the condition is unstable — build 2.1.22 went from 100% failure to 100% success in approximately 24 hours. This instability has implications for all Build Scan conclusions:

- The "dead zone" (builds 2.1.7–2.1.14) may not be permanent
- Build-specific failure rates from the Jan 28 scan may not be reproducible
- The distinction between "safe" and "unsafe" builds may be temporal rather than version-dependent
- Future experiments must account for both persistence variability AND delegation variability

---

### Step 2.3: Server-Side Behavior Verification on Build 2.1.6

**Replaces**: The original Step 2.3 (Cross-Machine Replication) has been removed. Phase 1 environmental analysis conclusively ruled out machine-specific factors, and Step 2.2 revealed a more urgent line of inquiry.

**Objective**: Run Experiment-Methodology-04 on build 2.1.6 (3–5 trials) to verify whether server-side behavioral changes (persistence reduction, sub-agent delegation) extend to a much older build. User observation on Jan 30 confirmed that build 2.1.6 now exhibits Task tool delegation — behavior absent in all prior testing across any build.

**Status**: COMPLETE — Collection `schema-13-216` (6 trials, Jan 29)

#### Complete Trial Data Table

| Trial ID | Outcome | has_tool_results | has_subagents | Main-Session Reads | Resets | Pattern | Peak total_input | 1st Reset From | Compaction Loss (1st) | Initial Cache |
| -------- | ------- | ---------------- | ------------- | ------------------ | ------ | ------- | ---------------- | -------------- | --------------------- | ------------- |
| 230228 | FAILURE | **true** | false | 10 (9 + WPD re-read) | 2 | OTHER | 175,225 | 133,899 | −20,026 | 14,053 |
| 230236 | SUCCESS | **false** | **true** | 1 (delegation) | 1 | SINGLE_LATE | 145,671 | 140,978 | −4,690 | 15,825 |
| 230244 | SUCCESS | **true** | false | 14 (9 + 5 recovery) | 2 | EARLY_PLUS_LATE | 176,683 | 133,894 | −9,181 | 15,825 |
| 231053 | SUCCESS | **false** | **true** | 4 (delegation) | 1 | SINGLE_LATE | 158,809 | 153,444 | −5,362 | 15,825 |
| 231100 | FAILURE | **true** | false | 10 (9 + WPD recovery) | 2 | OTHER | 166,477 | 125,286 | −17,856 | 15,825 |
| 231108 | SUCCESS | **false** | **true** | 4 (delegation) | 1 | SINGLE_LATE | 157,204 | 152,387 | −4,814 | 15,825 |

#### Outcome Distribution

| Category | Count | Trials |
| -------- | ----- | ------ |
| SUCCESS (sub-agent delegation) | 3 | 230236, 231053, 231108 |
| SUCCESS (persistence + recovery) | 1 | 230244 |
| FAILURE (persistence, phantom reads) | 2 | 230228, 231100 |

#### Observation 1: Build 2.1.6 Exhibits Both Delegation AND Persistence — Definitive Server-Side Confirmation

This is the most significant finding of Step 2.3 and the strongest evidence yet for the server-side variability theory. Build 2.1.6 is the oldest build tested in this investigation, predating all other tested builds by a wide margin. Sub-agent delegation was absent from all testing prior to Jan 29 (28+ trials across builds 2.1.20–2.1.22). Yet 3/6 trials on 2.1.6 show `has_subagents: true` — identical in structure to the delegation patterns observed on builds 2.1.20 (4/9) and 2.1.22 (5/6) earlier the same day.

A client-side explanation is now definitively ruled out. Build 2.1.6's client harness was released long before delegation became a behavioral pattern. The Task tool for sub-agent spawning existed in the client, but the model's *tendency* to use it for file reads is controlled by model weights and/or system prompts — both served from the API. Build 2.1.6 could not have been designed or updated to prefer delegation, yet it delegates at exactly the rate expected if the server is driving the behavior.

#### Observation 2: Persistence Rate Is 100% Among Direct-Read Trials

| Trial Type | Persistence | Count |
|-----------|------------|-------|
| Direct-read (no delegation) | 3/3 (100%) | 230228, 230244, 231100 |
| Delegation | 0/3 (0%) | 230236, 231053, 231108 |
| Overall | 3/6 (50%) | — |

Every trial that read files directly in the main session had persistence enabled. This is the highest direct-read persistence rate in any Jan 29 collection (compared to 80% on 2.1.20 and 0/1 on 2.1.22). However, with only 3 direct-read trials, the apparent 100% rate is consistent with the ~80% rate observed on 2.1.20 (p = 0.51 for 3/3 given p=0.8 base rate). The key finding is not the exact rate but the confirmation that persistence remains active on build 2.1.6 — the mechanism is not build-gated.

Delegation trials, by reading only 1–4 files in the main session, never triggered persistence. This is structurally identical to the delegation trials in schema-13-2120 and schema-13-2122.

#### Observation 3: Second Confirmed Recovery from `<persisted-output>` Markers

Trial 230244 is a SUCCESS with `has_tool_results: true`. The agent detected `<persisted-output>` markers for 5 files (pipeline-refactor.md, data-pipeline-overview.md, module-alpha.md, module-beta.md, module-gamma.md) and followed up by reading the corresponding `tool-results/` files. The agent's notes state: "I experienced the persisted-output indirection, I did not ignore it." The agent read the WPD tool-result fully and 4 spec tool-results partially (50–100 lines each), supplementing with targeted Grep searches against original files.

The reset pattern is EARLY_PLUS_LATE (36.6% and 90.3%), which may have aided recovery: the early reset at 36.6% (sequence position 34 of 93 events) provided a clean context window during which the agent performed its recovery reads (sequences 35–41). The second reset at 90.3% occurred after recovery was complete.

This is now the second confirmed recovery SUCCESS after trial 203749 in schema-13-2120. Updated `has_tool_results` discriminator across all classified trials:

| has_tool_results | Outcome | Count | Percentage |
| ---------------- | ------- | ----- | ---------- |
| false | SUCCESS | 11 (prior) + 3 (schema-13-216) = 14 | 100% SUCCESS |
| true | FAILURE | 15 (prior) + 2 (schema-13-216) = 17 | 85% FAILURE |
| true | SUCCESS (recovery) | 1 (prior) + 1 (schema-13-216) = 2 | 10% SUCCESS |
| true | UNKNOWN (overload) | 4 (prior) | N/A |

`has_tool_results: false` remains a perfect predictor of SUCCESS (14/14). `has_tool_results: true` now shows a ~10% recovery rate (2/20 classified).

#### Observation 4: First Reset Thresholds Cluster Consistently

| Reset Band | Token Range | Trials |
| ---------- | ----------- | ------ |
| ~125K | 125,286 | 231100 |
| ~134K | 133,894–133,899 | 230228, 230244 |

The ~125K band aligns with the ~123K band observed in barebones-2120-2 and schema-13-2120. The ~134K band is slightly higher than the ~131K band in prior collections but within the same general cluster. Delegation trials reset at 141K–153K — higher because the main session accumulated less file content, allowing context to grow further before the reset threshold was reached.

The consistency of reset bands across builds 2.1.6, 2.1.20, and 2.1.22 is further evidence that reset thresholds are server-controlled parameters, not client-determined values.

#### Observation 5: Affected Files Remain Consistent

| Trial | Affected Files |
|-------|---------------|
| 230228 | data-pipeline-overview, module-alpha, module-beta, module-gamma, pipeline-refactor (5) |
| 231100 | data-pipeline-overview, module-alpha, module-beta, module-gamma (4) |

`module-alpha.md` remains affected in 100% of failures — now 23/23 across all collections. The affected file pattern continues to reflect read order (earlier files in the batch are persisted; later ones are not) rather than file-specific properties.

Trial 230228 includes `pipeline-refactor.md` (the WPD) among affected files, but the agent subsequently re-read it successfully (sequence 10). Trial 231100 shows the agent followed up on the WPD's persisted output (reading the tool-result file) but did not follow up on the 4 spec file markers.

#### Observation 6: Timing Context — Persistence Remained Strong for Direct Reads

The schema-13-216 trials ran approximately 2 hours after schema-13-2122:

| Collection | Time (Jan 29) | Build | Direct-Read Persistence | Delegation Rate |
|-----------|--------------|-------|------------------------|-----------------|
| schema-13-2120 | 20:26–20:43 | 2.1.20 | 80% (4/5) | 44% (4/9) |
| schema-13-2122 | 21:01–21:11 | 2.1.22 | 0% (0/1) | 83% (5/6) |
| schema-13-216 | 23:02–23:11 | 2.1.6 | 100% (3/3) | 50% (3/6) |

The single direct-read trial in schema-13-2122 (0% persistence) is too small to draw conclusions. The 2.1.6 data (100% persistence among direct reads) is consistent with the ~80% rate observed 2.5 hours earlier on 2.1.20. There is no evidence that persistence rates changed significantly across the Jan 29 evening window.

The delegation rate on 2.1.6 (50%) falls between the rates observed on 2.1.20 (44%) and 2.1.22 (83%). All three builds show delegation at substantial rates, confirming this is a server-driven behavioral shift that applies uniformly regardless of client version.

#### Observation 7: Initial Cache Anomaly in Trial 230228

Trial 230228 shows `initial_cache_read` of 14,053 — lower than the 15,825 observed in all other schema-13-216 trials. This ~1,772-token difference parallels the cold-cache observation in schema-13-2120, where trial 202633 (the sole non-persistence direct-read success) had a lower initial cache of 10,331 vs. 15,491 for subsequent trials. However, unlike the 2.1.20 case, trial 230228's lower initial cache did NOT prevent persistence — it had `has_tool_results: true` and resulted in FAILURE. This weakens any hypothesis that cold-cache state protects against persistence.

#### Step 2.3 Interpretation

The results are **MIXED**, which the investigation plan identified as consistent with the **stochastic persistence mechanism**. However, the critical finding is not the mixed outcome distribution but the behavioral fingerprint: build 2.1.6 is structurally indistinguishable from builds 2.1.20 and 2.1.22 tested on the same day.

| Behavioral Dimension | Build 2.1.6 (Jan 29) | Build 2.1.20 (Jan 29) | Build 2.1.22 (Jan 29) |
|---------------------|----------------------|----------------------|----------------------|
| Delegation present? | Yes (3/6, 50%) | Yes (4/9, 44%) | Yes (5/6, 83%) |
| Persistence in direct-reads? | Yes (3/3, 100%) | Yes (4/5, 80%) | No (0/1, 0%) |
| Recovery observed? | Yes (1 trial) | Yes (1 trial) | No |
| Reset bands | ~125K, ~134K | ~123K, ~128K, ~131K | ~123K |
| Failure mechanism | Identical | Identical | N/A (no failures) |
| Baselines | 14,053–15,825 | 10,331–15,491 | 15,617 |

Three builds spanning a wide version range, tested within 3 hours on the same evening, show the same behavioral patterns. The build version adds no predictive value beyond what the server state already determines. This definitively answers RQ-BSD-4 and resolves the investigation's central question: **the persistence decision is server-controlled, not build-controlled, and this extends to the oldest builds in the investigation.**

---

## Phase 2 Synthesis (Complete — Steps 2.1–2.3)

Steps 2.1–2.3 collectively establish, with high confidence, that phantom read behavior is governed by **server-side variability**, not client build versions.

### The Server-Side Variability Finding

Four test windows across three builds produced distinct behavioral regimes. Step 2.3 extends the evidence to build 2.1.6 — the oldest build in the investigation:

| Date | Build(s) | Persistence Rate (Direct-Read) | Delegation Rate | Outcome |
| ---- | -------- | ------------------------------ | --------------- | ------- |
| Jan 27 | 2.1.20 | 0% (0/5) | 0% (0/5) | 100% success |
| Jan 28 | 2.1.20, 2.1.21, 2.1.22 | 100% (23/23) | 0% (0/23) | 100% failure* |
| Jan 29 (early) | 2.1.20, 2.1.22 | ~67% (4/6 direct-reads) | 60% (9/15) | Mostly success |
| Jan 29 (late) | 2.1.6 | 100% (3/3 direct-reads) | 50% (3/6) | Mixed |

\* Among valid trials (excluding protocol violations and context overloads)

The Jan 28 → Jan 29 transition remains the most dramatic: build 2.1.22 went from 100% failure to 100% success in approximately 24 hours. Step 2.3 provides the definitive cross-era test: build 2.1.6 behaves identically to newer builds tested the same day, despite spanning a wide version gap.

### Two Independent Server-Side Changes

The data reveals two separate mechanisms that shifted between Jan 28 and Jan 29:

1. **Persistence mechanism change**: The harness persistence trigger was modified. On Jan 28, every session had persistence enabled. On Jan 29, persistence was reduced to ~80% of direct-read trials on build 2.1.20, 0% on the single direct-read trial on build 2.1.22, and 100% on 3 direct-read trials on build 2.1.6. The per-session stochastic behavior is consistent across builds — what varies is the server's probability of enabling persistence, not any client-side property.

2. **Model behavioral change**: The model began preferring sub-agent delegation for file reads. This strategy, absent in all 28+ prior trials (Jan 27–28), appeared across all three builds tested on Jan 29: 44% on 2.1.20, 83% on 2.1.22, and 50% on 2.1.6. Build 2.1.6 is the strongest evidence for this being a server-side change — its client harness predates all other tested builds and could not have been designed to encourage delegation, yet it delegates at the same rate as newer builds.

### Recovery as an Emerging Third Factor

Step 2.3 confirmed a second recovery SUCCESS (trial 230244), bringing the total to 2 out of 20 classified `has_tool_results: true` trials (~10%). Both recovery successes involved agents that detected `<persisted-output>` markers and actively read the tool-result files. While recovery is too infrequent to serve as a reliable mitigation, it represents a third pathway to success alongside non-persistence and delegation:

| Success Pathway | Mechanism | Reliability |
|----------------|-----------|-------------|
| No persistence | Server disables persistence for session | ~20–100% depending on server state |
| Sub-agent delegation | Model delegates reads to sub-agents | ~44–83% of sessions on Jan 29 |
| Recovery | Agent detects and follows up on markers | ~10% of persistence sessions |

### Implications

These findings have been formalized in `docs/theories/Server-Side-Variability-Theory.md`. The key implications:

- Build-specific failure rates measured on Jan 28 reflect that day's server state, not inherent build properties
- The X+Y model's threshold T is externally variable: `T_effective(server_state)`
- The observed improvement is a **mitigation, not a confirmed fix** — persistence was still observed in 80–100% of direct-read trials on Jan 29
- Permanence of the mitigation is unknown (Jan 27 also showed improvement that reverted on Jan 28)
- Build version is irrelevant to phantom read occurrence — the same server state produces the same behavioral fingerprint across builds 2.1.6, 2.1.20, and 2.1.22

### Phase 2 Complete

All three targeted experiments are complete. The central finding is unambiguous: **server-side state, not client build version, determines phantom read behavior.** Phase 3 will integrate these findings with the theoretical framework and assess whether the project should redirect toward closure.

---

## Phase 3: Theoretical Integration

### Step 3.1: Revise the X+Y Model — Server-Side Variability Theory

**Objective**: Determine whether the X+Y model needs a stochastic component to account for the discrepancy.

**Status**: COMPLETE — See `docs/theories/Server-Side-Variability-Theory.md`

**Current X+Y Model**: For a given X (pre-operation context) and Y (operation tokens), the outcome is deterministic — either X+Y exceeds the effective threshold T and triggers phantom reads, or it doesn't.

**Discrepancy Challenge**: The 2120 data shows the same X (~114K) and Y (~45-60K) producing different outcomes (SUCCESS on Jan 27, FAILURE on Jan 28). Three hypotheses were evaluated:

1. **T_effective varies**: The threshold is not fixed but varies due to server-side configuration
2. **Persistence is probabilistic**: Whether the harness persists tool results depends on factors beyond just token count
3. **A hidden variable**: Some unmeasured factor distinguishes the two sessions

**Analysis**: All three hypotheses are supported to some degree, and they are not mutually exclusive:

- **Hypothesis 1 (T_effective varies)**: Strongly supported. Build 2.1.22 went from 100% failure (Jan 28, persistence threshold ~123–160K) to 100% success (Jan 29, no persistence even at 198K total_input). The effective threshold either increased dramatically or persistence was disabled entirely.

- **Hypothesis 2 (Persistence is probabilistic)**: Supported. Within the Jan 29 schema-13-2120 collection, direct-read trials showed 80% persistence and 20% non-persistence in the same ~20-minute window on the same build. The persistence decision has a stochastic component.

- **Hypothesis 3 (Hidden variable)**: The "hidden variable" is server-side state — configuration parameters, model routing, or infrastructure state that varies across time but is invisible in session data. This is now well-characterized rather than hidden.

**Revised Model**:

The X+Y model is extended with external variability:

```
Phantom reads occur when:
  X + Y > T_effective(server_state)
  AND persistence is enabled for this session (probabilistic, server-controlled)
  AND the agent does not recover from <persisted-output> markers
```

Where `T_effective` and persistence enablement are server-side variables. The model remains valid — it correctly predicts that within-threshold operations are safe — but its predictions are now conditional on server state, which the experiment cannot control.

---

### Step 3.2: Assess Impact on Build Scan Conclusions

**Objective**: Determine which Build Scan conclusions remain valid given the discrepancy findings.

**Status**: COMPLETE

The original Build Scan (`Experiment-04-BuildScan.md`) was conducted entirely on Jan 28, 2026. The Discrepancy Investigation (Phases 1–2) subsequently demonstrated that phantom read behavior is governed by server-side state, not client build version. This section reassesses each Build Scan conclusion in light of that finding.

#### Revision Framework

The central question for each conclusion is: **Does this reflect a build-level property (client-side code), or does it reflect the server state at the time of testing?**

- **Build-level properties** are determined by client code and persist regardless of server state. Examples: changelog-documented client code changes, context blocking limit calculations, `/context` command behavior.
- **Server-state properties** are determined by Anthropic's API infrastructure and vary over time. Examples: persistence trigger behavior, model delegation tendencies, effective context thresholds.

Conclusions rooted in build-level properties remain valid. Conclusions rooted in server-state properties are artifacts of Jan 28's conditions and should not be treated as permanent characteristics of those builds.

#### Build Scan Conclusions: Revised Assessment

| # | Conclusion | Original Assessment | Revised Assessment | Basis |
|---|-----------|---------------------|-------------------|-------|
| 1 | "Dead zone" builds 2.1.7–2.1.14 | Context overload renders protocol inoperable | **Likely valid (client-side)** — see analysis below | Build-level |
| 2 | Build 2.1.22 as best reproduction target | 100% failure rate (6/6) | **Invalidated** — reversed to 100% success on Jan 29 | Server-state |
| 3 | Build 2.1.20 as potential "fix" | Contradicted by 2120-2 data | **Fully resolved** — neither "fix" nor "unfixed"; behavior varies with server state | Server-state |
| 4 | Builds 2.1.15–2.1.19 consistently reproduce | 100% failure in scan | **Artifact of Jan 28 server state** — untestable as inherent build properties from single-day data | Server-state |
| 5 | No context overloads in 2.1.21+ | 0/18 runs showed overload | **Partially valid** — correct for dead-zone-type overloads; context exhaustion during recovery is a separate, server-state-dependent phenomenon | Mixed |

#### Detailed Analysis Per Conclusion

**Conclusion 1: "Dead Zone" Builds 2.1.7–2.1.14**

*Original*: Context overload renders the experiment protocol inoperable. Sessions hit 0% remaining memory and die during `/analyze-wpd`.

*Revised*: **Likely valid as a build-level property.** The changelogs for builds within this range document explicit client-side code changes to context blocking limits:
- Build 2.1.7: "Fixed orphaned tool_results, context blocking limit"
- Build 2.1.9: "Context window blocking limit calculation corrected"
- Build 2.1.14: "Fixed a regression where the context window blocking limit was calculated too aggressively, blocking users at ~65% context usage instead of the intended ~98%"

These are client-side code changes — the harness computes a blocking limit and terminates the session when it is reached. This is distinct from the server-side persistence mechanism that causes phantom reads. The dead zone overloads are best understood as a client-side regression (an overly aggressive blocking calculation) that was introduced in 2.1.7 and fixed by 2.1.15.

*Caveat*: We cannot be absolutely certain these builds would overload under all server conditions, because we have no data on them under Jan 29-type server conditions. However, the changelog evidence strongly favors a client-side explanation, and context blocking limits are logically a client-side computation. This is the Build Scan conclusion with the highest confidence of being genuinely build-specific.

*Confidence*: **High** that the dead zone is a build-level property.

---

**Conclusion 2: Build 2.1.22 as Best Reproduction Target**

*Original*: 100% failure rate (6/6), no context overloads, most recent stable build.

*Revised*: **Invalidated.** Build 2.1.22 reversed from 100% failure (Jan 28, `barebones-2122`) to 100% success (Jan 29, `schema-13-2122`) in approximately 24 hours with zero changes to the test environment. This is the single most definitive piece of evidence in the investigation: a build cannot retroactively change its behavior, so the variable must be external.

The Build Scan's recommendation to "adopt build 2.1.22 as the new project target" was based on data from a single server-state snapshot. Under the Server-Side Variability Theory, no build can be designated as a reliable reproduction target because failure rates reflect server state at time of testing, not inherent build properties. A build that fails 100% today may succeed 100% tomorrow.

*Practical implication*: The concept of a "best reproduction target" build is no longer meaningful. Reproduction reliability depends on server state, which the experimenter cannot control. Any build from 2.1.15 onward (outside the dead zone) is equally viable as a test platform, and equally subject to server-state variability.

*Confidence*: **Very high** that this conclusion is invalidated.

---

**Conclusion 3: Build 2.1.20 as Potential "Fix"**

*Original*: Initially interpreted as a fix (Barebones-2120 study, 5/5 success on Jan 27), then contradicted by the Build Scan (86% failure in `barebones-2120-2` on Jan 28).

*Revised*: **Fully resolved — this was the founding discrepancy of the investigation.** Build 2.1.20's behavior varied across three test windows:

| Date | Collection | Persistence | Failure Rate |
|------|-----------|-------------|-------------|
| Jan 27 | repro-attempts-04-2120 | 0% (0/5) | 0% (0/5) |
| Jan 28 | barebones-2120-2 | 100% (10/11) | 86% (6/7 valid) |
| Jan 29 | schema-13-2120 | 44% overall, 80% direct-read | 33% (3/9) |

The Jan 27 result was neither a "fix" nor an anomaly — it was a genuine observation of server-state conditions where persistence was disabled. The Jan 28 result reflected different server conditions where persistence was universally enabled. The Jan 29 result showed the stochastic intermediate state. The build itself did not change; the server conditions did.

*Practical implication*: The question "Did Anthropic fix phantom reads in build 2.1.20?" is malformed. The correct framing is: "Were phantom reads temporarily mitigated by server-side conditions on Jan 27?" The answer is yes, but the mitigation was transient and reverted within hours.

*Confidence*: **Very high** that the discrepancy is fully explained by server-side variability.

---

**Conclusion 4: Builds 2.1.15–2.1.19 Consistently Reproduce**

*Original*: All runs on these builds during the Jan 28 scan showed phantom reads (100% failure).

*Revised*: **Artifact of Jan 28 server state.** These builds were tested only on Jan 28, when ALL builds showed 100% persistence (23/23 direct-read trials across builds 2.1.20–2.1.22 also had 100% persistence). Their 100% failure rate is indistinguishable from the universal Jan 28 baseline — every build tested on Jan 28 had 100% persistence.

Under Jan 29 conditions, builds 2.1.20, 2.1.22, and 2.1.6 all showed reduced persistence and/or delegation-mediated success. There is no reason to believe builds 2.1.15–2.1.19 would behave differently under those same conditions — the investigation has demonstrated that build version adds no predictive value beyond server state.

*Practical implication*: We cannot make any build-specific claims about 2.1.15–2.1.19 from single-day data. If re-tested today, their behavior would likely mirror whatever the current server state produces on any other post-dead-zone build.

*Confidence*: **High** that these failure rates are server-state artifacts, not build properties.

---

**Conclusion 5: No Context Overloads in 2.1.21+**

*Original*: Across 18 runs on builds 2.1.21 and 2.1.22, zero context overloads were observed.

*Revised*: **Partially valid — requires disambiguation of two different "overload" phenomena.**

The Build Scan uses "context overload" to describe two distinct situations:

1. **Dead-zone overloads** (builds 2.1.7–2.1.14): The client-side context blocking limit calculation was too aggressive, terminating sessions at ~65% context usage. This is a build-level property caused by client code, and the fix (builds 2.1.14–2.1.15) is genuinely build-specific. The conclusion that builds 2.1.21+ do not exhibit dead-zone overloads is **valid**.

2. **Recovery-exhaustion overloads** (the 4 UNKNOWN trials in `barebones-2120-2`): Agents detected `<persisted-output>` markers and attempted recovery reads, consuming so much additional context that the session exhausted its window. This is a consequence of persistence behavior and is **server-state-dependent**. Build 2.1.20 showed these on Jan 28 but not Jan 29.

The original conclusion conflates these two phenomena. The refined conclusion is:

- **Dead-zone overloads**: Absent in 2.1.15+ (build-level fix). **Valid.**
- **Recovery-exhaustion overloads**: Absent in 2.1.21+ on Jan 28, but this reflects Jan 28 server conditions (100% persistence but well-behaved session dynamics). Under different server conditions, recovery-exhaustion overloads could occur on any build where persistence is enabled and the agent attempts recovery.

*Confidence*: **High** for the dead-zone component; **Medium** for the recovery-exhaustion component (limited data).

#### Synthesis: What Remains of the Build Scan?

The Build Scan (`Experiment-04-BuildScan.md`) remains valuable as a **historical record of Jan 28, 2026 server conditions** and as a **catalog of client-side build differences** (dead zone, `/context` command evolution, npm deprecation warnings). However, its primary use case — identifying builds where phantom reads do or do not occur — is invalidated by the Server-Side Variability Theory.

**Conclusions that survive:**
- The dead zone (builds 2.1.7–2.1.14) is a genuine client-side regression, likely valid regardless of server state
- The `/context` command evolution (broken in 2.1.9–2.1.12, double-print in 2.1.15–2.1.19, fixed in 2.1.20+) is a client-side observation unaffected by server state
- Phantom reads are not "fixed" in any tested build — confirmed and strengthened by the Discrepancy Investigation

**Conclusions that are invalidated:**
- Build-specific failure rates (all are artifacts of Jan 28 server state)
- Build 2.1.22 as preferred reproduction target
- The concept of "safe" or "unsafe" builds

**Conclusions that need reframing:**
- "Build 2.1.20 as potential fix" → fully resolved as server-state variability
- "No context overloads in 2.1.21+" → valid for dead-zone overloads, uncertain for recovery-exhaustion overloads

The Build Scan's most enduring contribution is not its build-specific failure rates but its discovery of the **Build Scan Discrepancy itself** — the 2.1.20 contradiction between Jan 27 (0% failure) and Jan 28 (86% failure) that triggered this investigation and led to the Server-Side Variability Theory.

---

### Step 3.3: Closure Assessment

**Objective**: Determine whether the investigation's findings — particularly the server-side mitigation observed on Jan 29 — warrant redirecting the project toward closure and reporting.

**Status**: COMPLETE

This assessment addresses four questions posed in the investigation plan.

#### Question 1: Has Anthropic Effectively Mitigated Phantom Reads?

**Answer: Partially — exposure is reduced, but the root cause is unaddressed.**

Two server-side changes observed on Jan 29 reduce phantom read exposure:

1. **Reduced persistence frequency**: Persistence was observed in 80–100% of direct-read trials on Jan 29, down from 100% on Jan 28. At least one direct-read trial on build 2.1.22 (trial 211109) reached 198K total_input with zero persistence — behavior impossible under Jan 28 conditions. However, 80–100% persistence for direct reads is still very high. The root cause — that persisted tool results are replaced by `<persisted-output>` markers the model fails to follow up on — is not addressed.

2. **Sub-agent delegation**: The model's new tendency to delegate file reads to sub-agents (44–83% of trials on Jan 29) independently avoids the persistence trigger. But delegation is a model behavioral tendency, not a guarantee — it is not user-controllable and varies stochastically.

The mitigation is real but has three critical limitations:

- **Not a fix**: The persistence mechanism is not eliminated. Direct-read sessions still show 80–100% persistence on Jan 29. When persistence occurs and the agent does not delegate or recover, phantom reads still happen (5 confirmed failures on Jan 29 across builds 2.1.6 and 2.1.20).
- **Not user-controllable**: Neither persistence reduction nor delegation is within the user's control. The only user-controllable mitigation remains the MCP Filesystem bypass (see `WORKAROUND.md`).
- **Permanence unknown**: We have one day of improved behavior (Jan 29). Jan 27 also showed improvement that reverted on Jan 28. Without longitudinal data, we cannot determine whether the Jan 29 state is stable.

#### Question 2: Is Further Reproduction Scenario Work (Easy/Medium/Hard) Still Necessary or Relevant?

**Answer: The original calibration goal is infeasible. A simplified reproduction approach is still valuable.**

The original Aim #3 from the PRD envisioned three calibrated scenarios:
- **Easy**: Always succeeds (0% phantom reads)
- **Hard**: Always fails (100% phantom reads)
- **Medium**: 50% failure rate

The Server-Side Variability Theory makes precise calibration infeasible:

- **Easy** is achievable by keeping X+Y well below any observed threshold, or by using the MCP Filesystem workaround (which bypasses the persistence mechanism entirely). The `/setup-easy` scenario likely works under all server conditions because it keeps context consumption low enough that persistence is never triggered.
- **Hard** cannot be guaranteed. A scenario designed to trigger phantom reads will fail only when persistence is enabled — and we cannot control the persistence decision. Under Jan 27 conditions (0% persistence), even the most aggressive scenario would succeed. The "Hard" scenario is better described as "triggers phantom reads when server conditions permit," which is ~80–100% of the time under current conditions for direct-read sessions.
- **Medium** is essentially impossible to calibrate. The baseline failure rate varies from 0% to 100% depending on server state, making a fixed 50% target meaningless.

**What remains valuable**: A reproduction case that demonstrates the phenomenon when conditions are favorable. This means:
- A scenario that reads enough files to cross the persistence threshold (~9 spec files in the barebones repository)
- Instructions for users to detect whether persistence occurred (check for `tool-results/` directory)
- Clear framing that reproduction depends on server conditions and is not guaranteed on any given day
- The MCP Filesystem workaround as a verified control condition (always succeeds, regardless of server state)

This simplified approach is already largely in place via Experiment-Methodology-04. The remaining work is documentation and packaging for public consumption, not further experimentation.

#### Question 3: Should the Project Shift Focus from Investigation to Documentation and Public Reporting?

**Answer: Yes. The investigation has reached a natural plateau.**

The project's four Aims (from `docs/core/PRD.md`) are at the following state:

| Aim | Description | Status |
|-----|------------|--------|
| **#1** | Understand the nature and cause of phantom reads | **Substantially achieved.** Root cause chain fully mapped (persistence → marker substitution → agent ignores markers). X+Y model with server-side variability explains observed behavior. Trigger conditions identified (mid-session persistence of tool results). Key unknown: what controls the server-side persistence decision. |
| **#2** | Find a temporary workaround | **Achieved.** MCP Filesystem bypass validated at 100% success rate. Documented in `WORKAROUND.md`. |
| **#3** | Create a dependable reproduction case | **Partially achieved.** Reproduction works reliably under persistence-enabled server conditions (~80–100% of direct-read sessions currently). Cannot guarantee reproduction on any given day due to server-side variability. Easy/Medium/Hard calibration infeasible. |
| **#4** | Create tools for analyzing token management | **Achieved.** `trial_data.json` preprocessing (Schema 1.3), `collect_trials.py`, persistence mapping, compaction loss analysis, reset detection algorithms. |

Further investigation yields diminishing returns for two reasons:

1. **The key remaining unknown is outside our observation boundary.** What controls the server-side persistence decision cannot be determined from external experiments. We can observe the effects but not the cause. Only Anthropic can answer this question.

2. **The experimental methodology has a fundamental confound.** Server-side variability means that trials collected on different days (or even within the same day) may reflect different server conditions. Controlling for this would require either (a) simultaneous comparative trials (impractical with a single machine and sequential protocol) or (b) very large sample sizes per condition (expensive in API usage and time).

The investigation's value now lies in **communicating** what was learned, not in further experimentation. The appropriate next steps are:

1. **Finalize this analysis document** (Executive Summary, Conclusions, Document History)
2. **Update the public README.md** with current findings, including the server-side variability discovery
3. **Update the Investigation Journal** with the investigation's conclusion
4. **Assess Action Plan** for items that should be marked complete, deferred, or reframed

#### Question 4: What Monitoring or Follow-Up Is Needed?

**Answer: Periodic spot checks and community monitoring.**

The permanence of the Jan 29 mitigation is unknown. Recommended follow-up:

1. **Periodic spot checks**: Run 3–5 trials on a fixed build (e.g., 2.1.22) every few days to track persistence rate and delegation rate over time. This creates a time series that reveals whether the server state is stable, trending toward improvement, or oscillating.

2. **Community monitoring**: The GitHub issue (#17407) serves as a natural monitoring channel. If other users report recurrence of phantom reads after the mitigation, this indicates the mitigation is unstable or was reverted.

3. **New build testing**: When significant Claude Code releases occur, run a small batch of trials to check whether phantom read behavior has changed. Focus on `has_tool_results` and `has_subagents` as the key discriminators.

4. **MCP workaround validation**: Periodically verify that the MCP Filesystem bypass continues to work. If Anthropic changes the persistence mechanism, the workaround's effectiveness should be re-confirmed.

None of these monitoring activities require the investigation-level rigor of formal experiments. They are lightweight checks to ensure the current state is maintained.

#### Closure Recommendation

**The Build Scan Discrepancy Investigation should be closed.** All phases are complete, all research questions are answered, the Server-Side Variability Theory is formalized and strongly supported, and further experimentation offers diminishing returns.

**The broader Phantom Reads project should shift focus to documentation and reporting.** The investigation phase has produced a substantial body of knowledge:
- 55+ trials across 8+ collections
- Root cause chain fully mapped
- Server-Side Variability Theory with strong cross-build, cross-day evidence
- Validated workaround
- Comprehensive analysis tools

This knowledge should be consolidated into public-facing documentation (README, reproduction instructions, workaround guide) and submitted to the GitHub issue as a comprehensive report. The project's value shifts from discovery to communication.

---

## Research Question Answers

### RQ-BSD-1: Why did the harness persist tool results in some sessions and not others?

**Status**: ANSWERED

**Evidence**: Across 50+ trials in 7 collections spanning 3 days and 3+ builds, the persistence decision is controlled by **server-side state that varies over time**. Key evidence from Phase 2:

- Build 2.1.22 showed 100% persistence on Jan 28 and 0% persistence on Jan 29 (same environment, same protocol)
- Build 2.1.20 showed 0% persistence on Jan 27, 100% on Jan 28, and ~80% (direct-reads) on Jan 29
- Within a single 20-minute window (Jan 29, build 2.1.20), persistence was stochastic — 80% of direct-read trials had it, 20% did not
- The persistence decision is invisible in session JSONL data (Step 1.4)

**Finding**: The persistence decision is controlled by **server-side configuration** that:
1. Varies between days (Jan 27: off, Jan 28: on, Jan 29: partially on)
2. Has a stochastic component within time windows (mixed results in same 20-minute window)
3. Is not determined by client build version (same build produces different persistence across days)
4. Is not determined by any metric visible in the session JSONL

The most parsimonious explanation is that Anthropic's infrastructure controls the persistence mechanism through server-side parameters that have changed multiple times during our observation period, possibly as part of active development or A/B testing.

**Significance**: This answer fundamentally reframes the investigation. The persistence decision — and therefore phantom read occurrence — is externally controlled and cannot be predicted from within the experiment. See `docs/theories/Server-Side-Variability-Theory.md`.

---

### RQ-BSD-2: Is the discrepancy explained by server-side changes?

**Status**: ANSWERED

**Evidence**: The Build Scan Discrepancy — 0% failure on Jan 27 vs. 100% failure on Jan 28 for the same build (2.1.20) — is fully explained by a server-side change that enabled the persistence mechanism between those two test windows. Step 2.2 provided the definitive evidence: build 2.1.22 reversed from 100% failure (Jan 28) to 100% success (Jan 29), proving that the variable is temporal (server-side) rather than version-based (client-side).

Additionally, two independent server-side changes were identified:
1. **Persistence mechanism change**: The harness persistence trigger was modified between Jan 28 and Jan 29, substantially reducing persistence frequency
2. **Model behavioral change**: The model began preferring sub-agent delegation for file reads, a strategy absent in all Jan 27–28 trials but present in 60% of Jan 29 trials across multiple builds, and confirmed on build 2.1.6 on Jan 30

**Finding**: **Yes.** The discrepancy is fully explained by server-side changes. The specific server-side factors cannot be identified from our position as external observers, but the most plausible candidates are: infrastructure configuration changes, model weights or routing updates, and/or system prompt modifications — all of which are served from Anthropic's API and can change without a client version bump.

**Significance**: This finding invalidates the investigation's original implicit assumption that build version is the primary independent variable. All build-specific conclusions from the Jan 28 Build Scan are artifacts of that day's server state, not properties of the builds themselves.

---

### RQ-BSD-3: Can we reproduce the original 2120 success pattern?

**Status**: ANSWERED (Step 2.1)

**Evidence**: 9 trials on build 2.1.20 collected on Jan 29 in `schema-13-2120`. Of 5 direct-read trials (no sub-agent delegation), 1 (trial 202633) reproduced the original pattern exactly: 9 files inline, `has_tool_results: false`, SINGLE_LATE reset, peak total_input 174,919, negative compaction loss. The other 4 direct-read trials had persistence enabled (3 FAILURE, 1 recovery SUCCESS). An additional 4 trials used sub-agent delegation, which avoids the persistence condition entirely.

**Finding**: The original success pattern **is reproducible but rare**. Under current API conditions (Jan 29), a direct-read session on build 2.1.20 has approximately a 20% chance (1/5) of avoiding persistence and succeeding. The Jan 27 pattern of 100% success (5/5) was either a transient state or a statistical cluster within a low-probability regime. The persistence decision appears stochastic — within the same 20-minute window, sessions on the same build showed mixed persistence behavior (44% overall, 80% among direct-read trials).

**Significance**: This finding resolves the central discrepancy. The Jan 27 success and Jan 28 failure are not contradictory — they represent different draws from a probabilistic process. The persistence mechanism is not a fixed binary state that switched between days; it is a per-session decision with a probability that may vary over time but was never truly 0% or 100%. The Jan 27 result (5/5 success) was consistent with an ~80% non-persistence probability at that time, while the Jan 28 result (11/11 persistence) was consistent with a ~100% persistence probability. The Jan 29 result (mixed) confirms the stochastic nature.

---

### RQ-BSD-4: Is the persistence threshold build-specific?

**Status**: ANSWERED — No, it is server-state-specific

**Evidence**: The same build (2.1.20) showed three different persistence profiles across three days:
- Jan 27: No persistence at all (sessions reached 160–173K cache_read without triggering persistence)
- Jan 28: 100% persistence (persistence triggered at ~123–132K)
- Jan 29: 80% persistence among direct-reads (persistence triggered at ~123–132K when present; no persistence in 1/5 direct-read trials reaching 175K)

Build 2.1.22 showed an even more dramatic reversal:
- Jan 28: 100% persistence (6/6 trials, resets at 132K–160K)
- Jan 29: 0% persistence (0/6 trials, including one direct-read trial reaching 163K cache_read / 198K total_input)

**Finding**: The persistence threshold is **not build-specific**. It is controlled by server-side state that varies over time. The same build can show 100% persistence one day and 0% the next. There may be build-specific differences in *how* the harness interacts with the server (Era 1 vs. Era 2 mechanisms), but the *decision* to persist is server-controlled.

**Significance**: This finding, combined with RQ-BSD-2, eliminates the possibility of identifying "safe" or "unsafe" builds. Any build can exhibit phantom reads depending on server-side conditions at the time of use.

---

### RQ-BSD-5: Do the raw JSONL files reveal any structural differences?

**Status**: ANSWERED

**Evidence**: Line-by-line comparison of SUCCESS trial 095002 (`repro-04-2120`, build 2.1.20, Jan 27) and FAILURE trial 150640 (`barebones-2121`, build 2.1.21, Jan 28), both with ~160K peak tokens. See Step 1.4 for full analysis.

**Finding**: The raw JSONL files are **structurally identical** between SUCCESS and FAILURE trials. Tool result content is byte-for-byte the same. Token usage tracks within ~200 tokens throughout. No `<persisted-output>` markers appear in either JSONL. The only new insight not captured by `trial_data.json` is the **post-reset cache_creation gap**: SUCCESS re-cached 179,788 tokens while FAILURE re-cached only 137,557 tokens — a 42,231 token deficit corresponding to the persisted file content. This gap reveals the phantom read mechanism in action (persisted content replaced by compact markers during context reconstruction) but does NOT explain why persistence was enabled in one session and not the other.

**Significance**: The JSONL comparison definitively establishes that the persistence decision occurs **outside the logged session data**. The session JSONL is a faithful record of tool execution but NOT of what the model receives. The discrepancy cannot be diagnosed from session data alone — it requires understanding the harness's persistence control mechanism, which is external to what we can observe.

---

## Conclusions

### 1. What caused the discrepancy between the two 2120 test sessions?

The discrepancy is fully explained by **server-side variability in the persistence mechanism**. On Jan 27, the server did not enable persistence for any session on build 2.1.20 — all 5 trials read files inline and succeeded. On Jan 28, the server enabled persistence for all sessions across all builds — 100% of direct-read trials had `has_tool_results: true` and phantom reads occurred. The test environment, protocol, and build were identical; the server-side persistence decision was the sole variable.

### 2. Is the X+Y model still valid?

Yes, but it requires a stochastic extension. The model's core prediction — that phantom reads occur when cumulative context (X+Y) exceeds an effective threshold — remains valid within a single session. However, the threshold T is not fixed: it varies with server-side state (`T_effective(server_state)`), and whether persistence is enabled at all is a per-session probabilistic decision. The revised model is:

```
Phantom reads occur when:
  X + Y > T_effective(server_state)
  AND persistence is enabled for this session
  AND the agent does not recover from <persisted-output> markers
```

This extension is formalized in `docs/theories/Server-Side-Variability-Theory.md`.

### 3. Which Build Scan conclusions remain trustworthy?

Only conclusions rooted in client-side code changes survive. The dead zone (builds 2.1.7–2.1.14) is likely a genuine build-level regression in context blocking limit calculations. The `/context` command evolution across builds is client-side. All build-specific failure rates are artifacts of Jan 28 server conditions and cannot be treated as inherent build properties. The concept of "safe" or "unsafe" builds is invalidated. See Step 3.2 for the detailed assessment of all five Build Scan conclusions.

### 4. What are the implications for future experiment methodology?

Three methodological implications emerge:

1. **Time is a confound.** Trials collected on different days (or even hours apart) may reflect different server states. Future experiments must either collect all data within a tight time window or explicitly track server-state indicators (`has_tool_results`, `has_subagents`) to control for this confound.

2. **Behavioral variability must be tracked.** Sub-agent delegation, which appeared on Jan 29 and was absent prior, fundamentally changes the session dynamics. Future experiments must record whether delegation occurred and analyze delegating and non-delegating trials separately.

3. **Large sample sizes are essential.** With persistence probability ranging from 0% to 100% across server states, and delegation probability from 0% to 83%, small batches (3–5 trials) cannot reliably characterize behavior. The investigation's most misleading result — the Barebones-2120 study's 5/5 success — was a small-sample artifact.

### 5. Are held experiments now unblocked?

**No — they are superseded.** The experiments on hold (04M, 04F, 04C, Easy/Medium/Hard scenarios) were designed to map threshold boundaries, test file count vs. token relationships, and calibrate reproduction scenarios. All assume a deterministic or near-deterministic relationship between inputs and outcomes. The Server-Side Variability Theory demonstrates that this assumption is false: the same inputs produce different outcomes depending on server state.

These experiments are not merely blocked — their design assumptions are invalidated. Mapping a threshold boundary requires a stable threshold. Calibrating a reproduction scenario requires a stable failure rate. Neither condition holds.

The project should redirect from experimental investigation to documentation and public reporting (see Step 3.3 Closure Assessment).

---

## Document History

- **2026-01-29**: Initial creation with placeholders for progressive completion
- **2026-01-29**: Step 1.1 completed — full pre-processing analysis of `barebones-2120-2` (11 trials)
- **2026-01-29**: Step 1.2 completed — 2120-2 success confirmed as protocol violation, zero valid successes in collection
- **2026-01-29**: Step 1.3 completed — cross-collection failure comparison (18 failures, 4 collections); `has_tool_results` confirmed as universal discriminator
- **2026-01-29**: Step 1.4 completed — raw JSONL deep dive between SUCCESS (095002) and FAILURE (150640); confirmed JSONL records full content (no `<persisted-output>` markers), discovered 42K token post-reset gap, established persistence is chronological not size-based, confirmed persistence decision is invisible in session data
- **2026-01-29**: Phase 1 Synthesis completed — full root cause chain mapped; central question identified as what controls the harness persistence decision; RQ-BSD-1 partially answered, RQ-BSD-5 fully answered
- **2026-01-29**: Step 2.1 completed — 9 trials on build 2.1.20 (Jan 29); original success pattern reproduced once (trial 202633, 1/5 direct-read trials); persistence is non-deterministic within same time window; sub-agent delegation identified as new behavioral confound (4/9 trials); first confirmed recovery from `<persisted-output>` (trial 203749); RQ-BSD-3 answered
- **2026-01-30**: Step 2.2 completed — 6 trials on build 2.1.22 (Jan 29); complete reversal from 100% failure (Jan 28) to 100% success (Jan 29); 0% persistence across all trials; sub-agent delegation in 5/6 trials; trial 211109 is critical direct-read full-protocol success at 198K total_input with zero persistence; confirms systemic server-side change
- **2026-01-30**: Phase 2 Synthesis (partial) written; Step 2.3 replaced (Cross-Machine → Server-Side Behavior Verification on 2.1.6); Step 3.1 completed (Server-Side Variability Theory formalized); RQ-BSD-1 fully answered, RQ-BSD-2 answered, RQ-BSD-4 answered; theory document created at `docs/theories/Server-Side-Variability-Theory.md`
- **2026-01-30**: Step 2.3 completed — 6 trials on build 2.1.6 (Jan 29); 2 FAILURE, 3 SUCCESS (delegation), 1 SUCCESS (recovery); delegation confirmed on oldest tested build (3/6 trials); persistence 100% among direct-read trials (3/3); second recovery SUCCESS confirmed (trial 230244); build 2.1.6 behaviorally indistinguishable from builds 2.1.20 and 2.1.22 on same day — definitive server-side confirmation; Phase 2 Synthesis updated to reflect all three steps complete
- **2026-01-30**: Step 3.2 completed — Assessed all 5 Build Scan conclusions against build-level vs. server-state framework. Dead zone (2.1.7–2.1.14) likely valid as client-side regression. Build 2.1.22 as reproduction target invalidated. Build 2.1.20 "fix" fully resolved as server-state variability. Builds 2.1.15–2.1.19 failure rates identified as Jan 28 server-state artifacts. No-overloads conclusion partially valid (disambiguated dead-zone vs. recovery-exhaustion overloads).
- **2026-01-30**: Step 3.3 completed — Closure assessment. Anthropic's mitigation is partial (reduced persistence, delegation) but not a fix (persistence 80–100% of direct reads, root cause unaddressed, permanence unknown). Easy/Medium/Hard calibration infeasible under server-side variability. Project should shift to documentation and reporting. Investigation closed.
- **2026-01-30**: Executive Summary and Conclusions written. Document finalized. All phases, steps, research questions, and success criteria complete.
