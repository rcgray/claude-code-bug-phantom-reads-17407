# Build Scan Discrepancy Analysis

**Investigation ID**: Build-Scan-Discrepancy
**Planning Document**: `docs/experiments/planning/Build-Scan-Discrepancy-Investigation.md`
**Date Started**: 2026-01-29
**Date Analyzed**: _In Progress_
**Triggered By**: Experiment-04-BuildScan results contradicting Barebones-2120 study

---

## Executive Summary

_Placeholder — To be written after all phases are complete._

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

| Metric | repro-04-2120 (Jan 27) | barebones-2121 (Jan 28) |
|--------|------------------------|-------------------------|
| File paths | `/Users/gray/Projects/barebones-phantom-reads/docs/specs/*` | Same |
| Files targeted | 9 spec files + WPD | Same 9 files |
| Protocol sequence | `/context` → `/setup-hard` → `/context` → `/analyze-wpd` → inquiry → `/export` | Same |
| Post-setup tokens | 114,017–114,018 | 114,223–114,226 |
| Baseline tokens | 15,490 (trials 2–5) | 15,616 |

The ~200-token difference in post-setup is negligible. This rules out environmental drift as the cause.

### Finding 2: `has_tool_results` Is the Discriminator

| Collection | Trial | Outcome | Files Read | Peak Tokens | has_tool_results |
|---|---|---|---|---|---|
| repro-04-2120 | 095002 | SUCCESS | 9 | 159,633 | **false** |
| repro-04-2120 | 100209 | SUCCESS | 9 | 172,990 | **false** |
| repro-04-2120 | 100944 | SUCCESS | 9 | 173,000 | **false** |
| barebones-2121 | 150640 | FAILURE | 9 | 159,840 | **true** |
| barebones-2121 | 150657 | SUCCESS | **6** | **131,802** | **false** |
| barebones-2121 | 150706 | FAILURE | 9 | 159,856 | **true** |

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

| Trial ID | Outcome | has_tool_results | Reads | Unique Files | Resets | Pattern | Peak Tokens | 1st Reset From | 2nd Reset From | Baseline |
|----------|---------|-----------------|-------|-------------|--------|---------|-------------|---------------|---------------|----------|
| 134716 | UNKNOWN | **true** | 19 | 19 | 1 | SINGLE_LATE | 123,111 | 123,111 | — | 114,095 |
| 134724 | FAILURE | **true** | 10 | 10 | 2 | OTHER | 157,853 | 131,724 | 157,853 | 114,095 |
| 140143 | SUCCESS | **false** | **6** | **6** | 1 | SINGLE_LATE | 166,511 | 166,511 | — | 114,098 |
| 140149 | FAILURE | **true** | 10 | 10 | 2 | OTHER | 138,641 | 123,114 | 138,641 | 114,095 |
| 140157 | FAILURE | **true** | 10 | 10 | 2 | OTHER | 151,788 | 131,733 | 151,788 | 114,099 |
| 142506 | UNKNOWN | **true** | 14 | 14 | 1 | SINGLE_LATE | 151,778 | 131,722 | — | 114,102 |
| 142515 | UNKNOWN | **true** | 14 | 14 | 1 | SINGLE_LATE | 151,732 | 123,111 | — | 114,100 |
| 142526 | FAILURE | **true** | 10 | 10 | 2 | OTHER | 151,763 | 131,722 | 151,763 | 114,099 |
| 143045 | UNKNOWN | **true** | 14 | 14 | 1 | SINGLE_LATE | 151,711 | 123,114 | — | 114,097 |
| 143056 | FAILURE | **true** | 10 | 10 | 2 | OTHER | 151,719 | 123,114 | 151,719 | 114,094 |
| 143105 | FAILURE | **true** | 10 | 10 | 2 | OTHER | 151,724 | 123,105 | 151,724 | 114,099 |

#### Comparison: Original 2120 Collection (repro-attempts-04-2120)

| Trial ID | Outcome | has_tool_results | Reads | Unique Files | Resets | Pattern | Peak Tokens | Reset From | Baseline |
|----------|---------|-----------------|-------|-------------|--------|---------|-------------|------------|----------|
| 095002 | SUCCESS | **false** | 9 | 9 | 1 | SINGLE_LATE | 159,633 | 159,633 | 114,017 |
| 100209 | SUCCESS | **false** | 9 | 9 | 1 | SINGLE_LATE | 172,990 | 172,990 | 114,018 |
| 100701 | SUCCESS | **false** | 9 | 9 | 1 | SINGLE_LATE | 172,999 | 172,999 | 114,023 |
| 100944 | SUCCESS | **false** | 9 | 9 | 1 | SINGLE_LATE | 173,000 | 173,000 | 114,016 |
| 101305 | SUCCESS | **false** | 9 | 9 | 1 | SINGLE_LATE | 159,921 | 159,921 | 114,017 |

#### Outcome Distribution

| Category | Count | Details |
|----------|-------|---------|
| FAILURE (confirmed phantom reads) | 6 | Trials 134724, 140149, 140157, 142526, 143056, 143105 |
| UNKNOWN (context overload) | 4 | Trials 134716, 142506, 142515, 143045 |
| SUCCESS | 1 | Trial 140143 (protocol violation — only 6 files read) |

#### Key Observations

**Observation 1: `has_tool_results` remains the perfect discriminator.**

All 10 trials with `has_tool_results: true` resulted in FAILURE or UNKNOWN. The single SUCCESS trial (140143) had `has_tool_results: false`. This is perfectly consistent with the preliminary findings from 2121 and the original 2120 collection. Across all data collected so far:

- `has_tool_results: false` → 100% SUCCESS (6/6 trials: 5 from original 2120, 1 from 2120-2)
- `has_tool_results: true` → 0% confirmed SUCCESS (0/12 trials across 2120-2 and 2121)

**Observation 2: The SUCCESS trial is another protocol violation.**

Trial 140143 read only 6 files: `pipeline-refactor.md` (WPD), `data-pipeline-overview.md`, `integration-layer.md`, `compliance-requirements.md`, `module-epsilon.md`, and `module-phi.md`. It skipped `module-alpha.md`, `module-beta.md`, and `module-gamma.md` — the exact same three files skipped in the barebones-2121 success trial (150657). By reading fewer files, the agent avoided triggering persistence and achieved a peak of 166K tokens with no persistence — identical to the original 2120 behavior. This trial is **invalid** as a data point for comparing success vs. failure because it avoided the conditions that trigger persistence.

**Observation 3: Two distinct behavioral profiles among `has_tool_results: true` trials.**

The 10 trials with persistence enabled split into two clear groups:

| Profile | Trials | Outcome | Resets | Reads | Behavior |
|---------|--------|---------|--------|-------|----------|
| **FAILURE** | 6 | Confirmed phantom reads | 2 (at ~69-71% and ~86-87%) | 10 | Agent ignored `<persisted-output>` markers |
| **UNKNOWN** | 4 | Session ended prematurely | 1 (at ~51-62%) | 14-19 | Agent detected and attempted follow-up on `<persisted-output>` markers |

The UNKNOWN trials show agents that **correctly** detected `<persisted-output>` markers and attempted to re-read content from the `tool-results/` directory. However, this recovery attempt consumed additional context, and all 4 sessions hit context limits before the phantom read inquiry could be conducted. These 4 trials correspond to the "4 context overloads" reported in the investigation's problem statement.

The key distinction: FAILURE agents ignored deferred reads; UNKNOWN agents attempted recovery but ran out of context. Both groups had persistence enabled.

**Observation 4: First reset thresholds cluster into two bands.**

| Reset Band | Token Range | Trials |
|------------|-------------|--------|
| ~123K | 123,105–123,114 | 134716, 140149, 142515, 143045, 143056, 143105 |
| ~131K | 131,722–131,733 | 134724, 140157, 142506, 142526 |

All first resets drop to ~18,020–18,027 tokens (the base level). The two bands may reflect different read orderings or batch sizes triggering the threshold at slightly different cumulative points. Note that trial 140143 (SUCCESS, no persistence) reset at 166,511 — dramatically higher, because it accumulated all file content inline without persistence intercepting.

**Observation 5: The original 2120 collection resets at dramatically different thresholds.**

| Collection | First Reset Range | Interpretation |
|------------|------------------|----------------|
| repro-04-2120 (Jan 27) | 159,633–173,000 | Reset after all 9 files read inline — too late to cause phantom reads |
| barebones-2120-2 (Jan 28) | 123,105–131,733 | Reset during file processing — triggers persistence, causes phantom reads |

This is the most striking structural difference. When persistence is disabled (`has_tool_results: false`), the agent reads all files inline to 160-173K tokens, then a single late reset occurs harmlessly. When persistence is enabled (`has_tool_results: true`), the harness intercepts tool results at a lower threshold (~123-132K), persisting them to disk. This interception itself changes the session dynamics: the agent receives `<persisted-output>` markers instead of content, leading to phantom reads when the agent fails to follow up.

**Observation 6: Baselines are nearly identical, confirming environmental stability.**

| Collection | Baseline Range | Mean |
|------------|---------------|------|
| repro-04-2120 (Jan 27) | 114,016–114,023 | 114,018 |
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

| Metric | repro-04-2120 SUCCESS trials (n=5) | barebones-2120-2 SUCCESS trial (140143) |
|--------|------------------------------|-----------------------------------|
| `has_tool_results` | **false** (all 5) | **false** |
| Peak token count | 159,633–173,000 | 166,511 |
| Files read (count) | **9** (all 5 trials) | **6** |
| Post-setup baseline | 114,016–114,023 | 114,098 |
| Reset count | 1 (all 5 trials) | 1 |
| Reset pattern | SINGLE_LATE (all 5) | SINGLE_LATE |
| Reset threshold | 159,633–173,000 | 166,511 |
| Protocol compliance | **FULL** | **VIOLATION** — skipped 3 files |

**Files read in trial 140143** (6 of 9):

| # | File | Read? |
|---|------|-------|
| 1 | pipeline-refactor.md (WPD) | Yes |
| 2 | data-pipeline-overview.md | Yes |
| 3 | integration-layer.md | Yes |
| 4 | compliance-requirements.md | Yes |
| 5 | module-alpha.md | **SKIPPED** |
| 6 | module-beta.md | **SKIPPED** |
| 7 | module-gamma.md | **SKIPPED** |
| 8 | module-epsilon.md | Yes |
| 9 | module-phi.md | Yes |

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

| Metric | 2120-2 (n=6) | 2121 (n=2) | 2122 (n=6) | repro-04-barebones (n=4) |
|--------|-------------|------------|------------|-------------------------|
| `has_tool_results` | **true** (6/6) | **true** (2/2) | **true** (6/6) | **true** (4/4) |
| Affected file count | 4 (5/6 trials), 4 (1/6 different set) | 5 (2/2) | 4–5 (varies) | 3–9 (varies widely) |
| Peak tokens | 138K–158K | ~160K | 132K–160K | 133K–165K |
| Reset count | 2 (all 6) | 1 (both) | 1–2 (mixed) | 2–3 (mixed) |
| 1st reset range | 123K–132K | ~160K | 132K–160K | 125K–134K |
| Reset pattern | OTHER (all 6) | SINGLE_LATE (both) | Mixed | OTHER / EARLY_PLUS_MID_LATE |

#### Universal Finding: `has_tool_results` Is Absolute

Across all 18 FAILURE trials spanning 4 collections and at least 3 builds, `has_tool_results: true` is present in **100% of cases** (18/18). This is the only metric with perfect consistency. Combined with the 6 SUCCESS trials that all have `has_tool_results: false`, the discriminator holds with 100% accuracy across 24 classified trials.

#### Affected Files Are Position-Dependent, Not File-Dependent

The affected files vary between trials, even within the same collection. Frequency across all 18 failures:

| File | Affected | % | Role |
|------|----------|---|------|
| module-alpha.md | 18/18 | 100% | Always affected |
| module-beta.md | 15/18 | 83% | Usually affected |
| module-gamma.md | 14/18 | 78% | Usually affected |
| data-pipeline-overview.md | 14/18 | 78% | Usually affected |
| pipeline-refactor.md (WPD) | 7/18 | 39% | Sometimes affected |
| integration-layer.md | 5/18 | 28% | Occasionally affected |
| compliance-requirements.md | 5/18 | 28% | Occasionally affected |
| module-epsilon.md | 1/18 | 6% | Rarely affected |
| module-phi.md | 1/18 | 6% | Rarely affected |

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

| Area | SUCCESS Trial | FAILURE Trial | Difference |
|------|--------------|---------------|------------|
| Tool result format | Full inline content, 10 results | Full inline content, 10 results | **Identical** — no `<persisted-output>` markers in either JSONL |
| System message content | 1 system message | 1 system message | Structurally identical |
| Harness behavior markers | No `tool-results/` directory | `tool-results/` directory with 6 files | **Critical** — only external artifact |
| API response metadata | Model: claude-opus-4-5-20251101 | Model: claude-opus-4-5-20251101 | Same model |
| Token accounting | Post-reset total_input: 197,740 | Post-reset total_input: 155,715 | **42,025 token gap** |

#### Finding 1: The JSONL Records Identical Content — No `<persisted-output>` Markers Anywhere

Every tool result in both sessions contains the **full file content**. Content lengths are byte-for-byte identical across all 9 file reads:

| File | SUCCESS Length | FAILURE Length | Match |
|------|--------------|---------------|-------|
| pipeline-refactor.md | 28,371 | 28,371 | ✓ |
| module-alpha.md | 29,348 | 29,348 | ✓ |
| module-beta.md | 30,441 | 30,441 | ✓ |
| data-pipeline-overview.md | 35,896 | 35,896 | ✓ |
| module-gamma.md | 37,745 | 37,745 | ✓ |
| integration-layer.md | 26,353 | 26,353 | ✓ |
| compliance-requirements.md | 21,779 | 21,779 | ✓ |
| module-epsilon.md | 36,196 | 36,196 | ✓ |
| module-phi.md | 38,734 | 38,734 | ✓ |

The `<persisted-output>` markers that the FAILURE agent experienced are **not recorded in the session JSONL**. This definitively confirms the Trial Analysis Guide's hypothesis: the session `.jsonl` is a log of tool execution results, not a representation of what the model receives in its context window. Content persistence/substitution happens in a layer between JSONL logging and the API call to the model.

#### Finding 2: The `tool-results/` Directory Is the Sole Artifact of Persistence

The FAILURE trial has a session subdirectory containing `tool-results/` with 6 persisted files. The SUCCESS trial has no session subdirectory at all.

**Persistence mapping (FAILURE trial)**:

| # | JSONL Line | Tool | File | Size | Persisted? |
|---|-----------|------|------|------|-----------|
| 1 | 8 | Bash | `date` command | 21 B | **YES** |
| 2 | 21 | Read | pipeline-refactor.md | 28.59 KB | **YES** |
| 3 | 25 | Read | data-pipeline-overview.md | 39.12 KB | **YES** |
| 4 | 26 | Read | module-alpha.md | 31.14 KB | **YES** |
| 5 | 27 | Read | module-beta.md | 32.27 KB | **YES** |
| 6 | 28 | Read | module-gamma.md | 39.47 KB | **YES** |
| 7 | 38 | Read | integration-layer.md | 26.35 KB | no |
| 8 | 39 | Read | compliance-requirements.md | 21.78 KB | no |
| 9 | 40 | Read | module-epsilon.md | 36.20 KB | no |
| 10 | 41 | Read | module-phi.md | 38.73 KB | no |

The persistence boundary falls cleanly between the first batch of reads (lines 8–28, all persisted) and the second batch (lines 38–41, none persisted). This is a **chronological** split, not a size-based one.

#### Finding 3: Persistence Is NOT Size-Based

The 21-byte date command result was persisted alongside 28–39 KB file reads. Meanwhile, the 38.73 KB `module-phi.md` (the largest file read) was **not** persisted. This conclusively rules out a per-result size threshold as the persistence mechanism.

The persisted results are the **earliest 6 tool results** in the session. The non-persisted results are the **latest 4**. This is consistent with a context compaction mechanism that persists older tool results to free space, regardless of their size.

#### Finding 4: Post-Reset Token Accounting Reveals the 42K Gap

The most significant finding from the JSONL that `trial_data.json` does not capture is the **post-reset cache creation difference**:

| Metric | SUCCESS (L56) | FAILURE (L58) | Difference |
|--------|--------------|---------------|------------|
| Pre-reset `cache_read` | 159,633 | 159,840 | +207 |
| Post-reset `cache_read` | 17,942 | 18,148 | +206 |
| Post-reset `cache_creation` | **179,788** | **137,557** | **−42,231** |
| Post-reset `total_input` | **197,740** | **155,715** | **−42,025** |

After the context reset, the SUCCESS trial re-cached 179,788 tokens — nearly the full conversation. The FAILURE trial re-cached only 137,557 tokens, a **42,025 token deficit**. This deficit represents the content of persisted tool results that was replaced by compact `<persisted-output>` markers during context reconstruction.

The 42K token gap corresponds well to the 5 persisted file reads. Total persisted file content: ~170.6 KB of characters. At approximately 4 characters per token, this is ~42,650 tokens — closely matching the observed 42,231 token difference in `cache_creation`.

**Interpretation**: When the context reset occurred, the harness reconstructed the context by re-inserting all conversation content. For the SUCCESS trial, all tool results were re-inserted as full content (179K tokens). For the FAILURE trial, persisted tool results were replaced with `<persisted-output>` markers (~100 tokens each instead of ~8,000), resulting in 42K fewer tokens of actual content available to the model. The model then responded based on this truncated context, producing phantom reads.

#### Finding 5: The FAILURE Agent Produced Longer Analysis Despite Less Content

| Trial | Analysis text length (chars) | Actual content available |
|-------|---------------------------|------------------------|
| SUCCESS (L48) | 7,560 | Full content of all 9 files |
| FAILURE (L50) | 10,375 | Content of 4 files + markers for 5 |

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

| Sequence | SUCCESS `cache_read` | FAILURE `cache_read` | Difference |
|----------|---------------------|---------------------|------------|
| 1 (initial) | 10,330 | 15,616 | +5,286 |
| 2 (post-setup) | 114,017 | 114,223 | +206 |
| 3-4 (pre-reads) | 114,148 | 114,337 | +189 |
| 5-9 (first batch) | 115,669 | 115,874 | +205 |
| 10-14 (second batch) | 123,029 | 123,237 | +208 |
| 15 (pre-reset) | 159,633 | 159,840 | +207 |
| 16 (post-reset) | 17,942 | 18,148 | +206 |

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

**Status**: _Not started_

**Trial Results**:

| Trial ID | Outcome | Files Read | Peak Tokens | has_tool_results | Reset Positions |
|----------|---------|------------|-------------|------------------|-----------------|
| _Placeholder_ | _Placeholder_ | _Placeholder_ | _Placeholder_ | _Placeholder_ | _Placeholder_ |
| _Placeholder_ | _Placeholder_ | _Placeholder_ | _Placeholder_ | _Placeholder_ | _Placeholder_ |
| _Placeholder_ | _Placeholder_ | _Placeholder_ | _Placeholder_ | _Placeholder_ | _Placeholder_ |

**Interpretation**:
- _If all SUCCESS_: _Placeholder_
- _If all FAILURE_: _Placeholder_
- _If MIXED_: _Placeholder_

---

### Step 2.2: Replication on Build 2.1.22 as Control

**Objective**: Run 3 trials on build 2.1.22 to confirm it still shows 100% failure. Serves as a control for API stability.

**Status**: _Not started_

**Trial Results**:

| Trial ID | Outcome | Files Read | Peak Tokens | has_tool_results | Reset Positions |
|----------|---------|------------|-------------|------------------|-----------------|
| _Placeholder_ | _Placeholder_ | _Placeholder_ | _Placeholder_ | _Placeholder_ | _Placeholder_ |
| _Placeholder_ | _Placeholder_ | _Placeholder_ | _Placeholder_ | _Placeholder_ | _Placeholder_ |
| _Placeholder_ | _Placeholder_ | _Placeholder_ | _Placeholder_ | _Placeholder_ | _Placeholder_ |

**Interpretation**:

_Placeholder — Does 2.1.22 still show consistent 100% failure? If not, something systemic changed._

---

### Step 2.3: Cross-Machine Replication (Low Priority)

**Objective**: Test whether the discrepancy is tied to the specific test machine or user identity.

**Status**: _Not started_ (Low priority — only pursue if Steps 2.1–2.2 fail to explain the discrepancy)

**Results**:

_Placeholder — Only fill in if this step is pursued._

---

## Phase 2 Synthesis

_Placeholder — After targeted experiments, summarize what was learned about reproducibility and API stability._

---

## Phase 3: Theoretical Integration

### Step 3.1: Revise or Confirm the X+Y Model

**Objective**: Determine whether the X+Y model needs a stochastic component to account for the discrepancy.

**Status**: _Not started_

**Current X+Y Model**: For a given X (pre-operation context) and Y (operation tokens), the outcome is deterministic — either X+Y exceeds the effective threshold T and triggers phantom reads, or it doesn't.

**Discrepancy Challenge**: The 2120 data shows the same X (~114K) and Y (~45-60K) producing different outcomes (SUCCESS on Jan 27, FAILURE on Jan 28). This suggests either:

1. **T_effective varies**: The threshold is not fixed but varies due to server-side configuration, A/B testing, or infrastructure rotation
2. **Persistence is probabilistic**: Whether the harness persists tool results depends on factors beyond just token count
3. **A hidden variable**: Some unmeasured factor distinguishes the two sessions

**Analysis**:

_Placeholder — Based on Phase 1 and Phase 2 findings, which explanation best fits the data? Does the model need revision?_

**Proposed Model Update (if needed)**:

_Placeholder — If the model needs a stochastic component, describe it here._

---

### Step 3.2: Assess Impact on Build Scan Conclusions

**Objective**: Determine which Build Scan conclusions remain valid given the discrepancy findings.

**Status**: _Not started_

**Build Scan Conclusions Under Review**:

| Conclusion | Original Assessment | Revised Assessment |
|------------|--------------------|--------------------|
| "Dead zone" builds 2.1.7–2.1.14 | Context overload renders protocol inoperable | _Placeholder_ |
| Build 2.1.22 as best reproduction target | 100% failure rate (6/6) | _Placeholder_ |
| Build 2.1.20 as potential "fix" | Contradicted by 2120-2 data | _Placeholder_ |
| Builds 2.1.15–2.1.19 consistently reproduce | 100% failure in scan | _Placeholder_ |
| No context overloads in 2.1.21+ | 0/18 runs showed overload | _Placeholder_ |

**Revised Conclusions**:

_Placeholder — Which conclusions stand, which need caveats, and which are invalidated?_

---

## Research Question Answers

### RQ-BSD-1: Why did the harness persist tool results in some sessions and not others?

**Status**: PARTIALLY ANSWERED (Phase 1 evidence only)

**Evidence**: Across 35 trials in 5 collections, persistence (`has_tool_results: true`) is a binary per-session decision that perfectly predicts outcome. The JSONL deep dive (Step 1.4) confirmed that the persistence decision is invisible in session data — pre-reset content is identical between SUCCESS and FAILURE trials. Persistence is chronological (earlier results persisted, later ones not), not size-based (21-byte date result persisted; 39KB files not persisted). The same build (2.1.20) produced 0% persistence on Jan 27 and 100% persistence on Jan 28 with identical workloads.

**Finding (Partial)**: The persistence decision is controlled by a factor **external to the session content and token consumption**. It is not determined by file size, total tokens, or any metric visible in the session JSONL. The most likely candidates are: (a) a server-side configuration parameter that changed between Jan 27 and Jan 28, (b) a client-side harness configuration that differs between builds or over time, or (c) a non-deterministic harness behavior. Phase 2 experiments are needed to distinguish these possibilities.

**Significance**: This is the central question of the entire investigation. Until we understand what controls the persistence decision, we cannot predict when phantom reads will occur or design reliable reproduction scenarios.

---

### RQ-BSD-2: Is the discrepancy explained by server-side changes?

**Status**: _Not answered_

**Evidence**: _Placeholder_

**Finding**: _Placeholder_

**Significance**: _Placeholder_

---

### RQ-BSD-3: Can we reproduce the original 2120 success pattern?

**Status**: _Not answered_

**Evidence**: _Placeholder (depends on Step 2.1 results)_

**Finding**: _Placeholder_

**Significance**: _Placeholder_

---

### RQ-BSD-4: Is the persistence threshold build-specific?

**Status**: _Not answered_

**Evidence**: _Placeholder_

**Finding**: _Placeholder_

**Significance**: _Placeholder_

---

### RQ-BSD-5: Do the raw JSONL files reveal any structural differences?

**Status**: ANSWERED

**Evidence**: Line-by-line comparison of SUCCESS trial 095002 (`repro-04-2120`, build 2.1.20, Jan 27) and FAILURE trial 150640 (`barebones-2121`, build 2.1.21, Jan 28), both with ~160K peak tokens. See Step 1.4 for full analysis.

**Finding**: The raw JSONL files are **structurally identical** between SUCCESS and FAILURE trials. Tool result content is byte-for-byte the same. Token usage tracks within ~200 tokens throughout. No `<persisted-output>` markers appear in either JSONL. The only new insight not captured by `trial_data.json` is the **post-reset cache_creation gap**: SUCCESS re-cached 179,788 tokens while FAILURE re-cached only 137,557 tokens — a 42,231 token deficit corresponding to the persisted file content. This gap reveals the phantom read mechanism in action (persisted content replaced by compact markers during context reconstruction) but does NOT explain why persistence was enabled in one session and not the other.

**Significance**: The JSONL comparison definitively establishes that the persistence decision occurs **outside the logged session data**. The session JSONL is a faithful record of tool execution but NOT of what the model receives. The discrepancy cannot be diagnosed from session data alone — it requires understanding the harness's persistence control mechanism, which is external to what we can observe.

---

## Conclusions

_Placeholder — To be written after all phases are complete. Should address:_

1. _What caused the discrepancy between the two 2120 test sessions?_
2. _Is the X+Y model still valid, or does it need a stochastic component?_
3. _Which Build Scan conclusions remain trustworthy?_
4. _What are the implications for future experiment methodology?_
5. _Are any experiments currently on hold (04M, 04F, 04C, Easy/Medium/Hard scenarios) now unblocked?_

---

## Document History

- **2026-01-29**: Initial creation with placeholders for progressive completion
- **2026-01-29**: Step 1.1 completed — full pre-processing analysis of `barebones-2120-2` (11 trials)
- **2026-01-29**: Step 1.2 completed — 2120-2 success confirmed as protocol violation, zero valid successes in collection
- **2026-01-29**: Step 1.3 completed — cross-collection failure comparison (18 failures, 4 collections); `has_tool_results` confirmed as universal discriminator
- **2026-01-29**: Step 1.4 completed — raw JSONL deep dive between SUCCESS (095002) and FAILURE (150640); confirmed JSONL records full content (no `<persisted-output>` markers), discovered 42K token post-reset gap, established persistence is chronological not size-based, confirmed persistence decision is invisible in session data
- **2026-01-29**: Phase 1 Synthesis completed — full root cause chain mapped; central question identified as what controls the harness persistence decision; RQ-BSD-1 partially answered, RQ-BSD-5 fully answered
