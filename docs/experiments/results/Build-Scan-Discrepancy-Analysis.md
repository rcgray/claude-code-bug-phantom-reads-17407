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

**Status**: _Not started_

**Results**:

_Placeholder — Record pre-processing results here. Include:_
- _Number of trials successfully pre-processed_
- _Any trials that failed pre-processing and why_
- _Initial observations from the generated trial_data.json files_

---

### Step 1.2: Compare 2120 Success vs 2120-2 Success

**Objective**: Compare the SUCCESS trial(s) in `barebones-2120-2` against the 5 SUCCESS trials in `repro-attempts-04-2120` to determine if they are structurally equivalent.

**Status**: _Not started_

**Key Comparisons**:

| Metric | repro-04-2120 SUCCESS trials | barebones-2120-2 SUCCESS trial(s) |
|--------|------------------------------|-----------------------------------|
| `has_tool_results` | _Placeholder_ | _Placeholder_ |
| Peak token count | _Placeholder_ | _Placeholder_ |
| Files read (count) | _Placeholder_ | _Placeholder_ |
| Post-setup baseline | _Placeholder_ | _Placeholder_ |
| Reset patterns | _Placeholder_ | _Placeholder_ |
| Protocol compliance | _Placeholder_ | _Placeholder_ |

**Findings**:

_Placeholder — Was the 2120-2 success a genuine match or another protocol violation?_

---

### Step 1.3: Compare Failure Profiles Across Collections

**Objective**: Verify that failure trials across collections share the same failure mechanism (`has_tool_results: true`, same affected files, same persistence behavior).

**Status**: _Not started_

**Cross-Collection Failure Comparison**:

| Metric | 2120-2 Failures | 2121 Failures | 2122 Failures | 216 Failures |
|--------|-----------------|---------------|---------------|--------------|
| `has_tool_results` | _Placeholder_ | _Placeholder_ | _Placeholder_ | _Placeholder_ |
| Affected files | _Placeholder_ | _Placeholder_ | _Placeholder_ | _Placeholder_ |
| Peak tokens | _Placeholder_ | _Placeholder_ | _Placeholder_ | _Placeholder_ |
| Reset positions | _Placeholder_ | _Placeholder_ | _Placeholder_ | _Placeholder_ |
| Persistence mechanism | _Placeholder_ | _Placeholder_ | _Placeholder_ | _Placeholder_ |

**Findings**:

_Placeholder — Is the failure mechanism consistent across builds and sessions, or are there structural variations?_

---

### Step 1.4: Raw JSONL Deep Dive

**Objective**: Compare raw JSONL session files between a SUCCESS trial from `repro-attempts-04-2120` and a FAILURE trial from `barebones-2121` with similar peak tokens (~160K).

**Status**: _Not started_

**Selected Trials for Comparison**:
- SUCCESS: _Placeholder (trial ID from repro-04-2120)_
- FAILURE: _Placeholder (trial ID from barebones-2121)_

**Comparison Areas**:

| Area | SUCCESS Trial | FAILURE Trial | Difference |
|------|--------------|---------------|------------|
| Tool result format | _Placeholder_ | _Placeholder_ | _Placeholder_ |
| System message content | _Placeholder_ | _Placeholder_ | _Placeholder_ |
| Harness behavior markers | _Placeholder_ | _Placeholder_ | _Placeholder_ |
| API response metadata | _Placeholder_ | _Placeholder_ | _Placeholder_ |
| Token accounting | _Placeholder_ | _Placeholder_ | _Placeholder_ |

**Findings**:

_Placeholder — Are there low-level structural differences that trial_data.json doesn't capture?_

---

## Phase 1 Synthesis

_Placeholder — After Steps 1.1–1.4 are complete, summarize what the existing data tells us before running new experiments. This synthesis should inform which Phase 2 steps are necessary._

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

**Status**: _Not answered_

**Evidence**: _Placeholder_

**Finding**: _Placeholder_

**Significance**: _Placeholder_

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

**Status**: _Not answered_

**Evidence**: _Placeholder (depends on Step 1.4 results)_

**Finding**: _Placeholder_

**Significance**: _Placeholder_

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
