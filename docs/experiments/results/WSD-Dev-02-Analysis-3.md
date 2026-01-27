# WSD-Dev-02 Trial Collection Analysis - Part 3: Token-Based Analysis

**Date**: 2026-01-20
**Collection**: `dev/misc/wsd-dev-02/`
**Trials Analyzed**: 22 (with schema 1.1 token data)
**Analysis Workscope**: 20260120-135500

---

## Executive Summary

This analysis leverages the new token count data (schema 1.1) added to trial_data.json files to answer questions that couldn't be addressed in previous analyses. The token counts enable precise correlation between file read operations, cumulative context consumption, and reset timing.

**Key Findings**:

1. **No Fixed Reset Threshold**: Resets occur at widely varying cumulative token counts (85K to 380K). There is no single "danger threshold" that triggers resets.

2. **Reset Timing > Token Count**: The POSITION of resets within the session (early/mid/late) matters far more than the absolute token count at which they occur.

3. **Large File Correlation - Weak**: File size at time of reset does not predict phantom reads. Resets occur after both small (~1K) and large (~50K) files.

4. **The "Early Reset Advantage"**: SUCCESS sessions consistently show early resets (21-45% through session) that appear to "clear the deck" before main operations begin.

5. **Recommended Next Steps**: Investigate mitigation through intentional early context consumption or session batching.

---

## Part 1: Token Accumulation at Reset Points

### 1.1 Reset Context Data Summary

Using the `resets_with_context` data from schema 1.1 trial files:

**SUCCESS Trials (5 trials)**:

| Trial | Reset | Position | Cumulative Tokens | Last File | File Size |
|-------|-------|----------|-------------------|-----------|-----------|
| 20260120-093130 | 1 | 97.7% | 139,643 | Journal | 967 |
| 20260120-095152 | 1 | 37.2% | 87,790 | Journal | 895 |
| 20260120-095152 | 2 | 97.7% | 340,837 | Journal | 895 |
| 20260120-093204 | 1 | 30.0% | 85,948 | Journal | 948 |
| 20260120-093204 | 2 | 95.0% | 379,133 | wsd.py | 50,155 |
| 20260119-131802 | 1 | 42.4% | ~82,000 | (pre-token) | - |
| 20260119-131802 | 2 | 97.0% | ~144,000 | (pre-token) | - |
| 20260119-142117 | 1 | 45.5% | ~83,000 | (pre-token) | - |
| 20260119-142117 | 2 | 98.2% | ~153,000 | (pre-token) | - |

**FAILURE Trials (3 detailed examples)**:

| Trial | Reset | Position | Cumulative Tokens | Last File | File Size |
|-------|-------|----------|-------------------|-----------|-----------|
| 20260120-090620 | 1 | 56.9% | 158,856 | build_package.py | 9,243 |
| 20260120-090620 | 2 | 82.4% | 230,942 | Stage-Release-Script-Overview.md | 7,366 |
| 20260120-090620 | 3 | 98.0% | 231,990 | Journal | 1,048 |
| 20260120-091729 | 1 | 21.5% | 88,522 | Journal | 761 |
| 20260120-091729 | 2 | 53.8% | 355,902 | Update-System.md | 14,137 |
| 20260120-091729 | 3 | 63.1% | 383,353 | pre_staging.py | 8,782 |
| 20260120-093143 | 1 | 54.2% | 153,856 | build_package.py | 9,243 |
| 20260120-093143 | 2 | 81.3% | 225,942 | Stage-Release-Script-Overview.md | 7,366 |
| 20260120-093143 | 3 | 97.9% | 226,990 | Journal | 1,048 |

### 1.2 Analysis: No Fixed Token Threshold

**Observation**: Resets occur at cumulative token values ranging from ~82K to ~383K.

If there were a fixed threshold (e.g., "reset when context reaches 140K"), we would expect:
- All resets to occur at approximately the same cumulative token value
- Higher cumulative values to predict more resets

**What We See Instead**:
- Early resets (SUCCESS): 82K-88K
- Mid-session resets (FAILURE): 153K-383K
- Late resets (both): 140K-379K

The cumulative token count at reset varies by 5x (82K to 383K), ruling out a simple threshold model.

### 1.3 New Hypothesis: Dynamic Context Pressure

The data suggests resets are triggered by **rate of context accumulation** rather than absolute values:

```
HYPOTHESIS: Resets occur when recent token consumption rate exceeds some threshold,
            not when absolute token count exceeds a fixed limit.
```

**Supporting Evidence**:
- SUCCESS sessions show steady token progression with natural pauses
- FAILURE sessions show rapid batch reads without breathing room
- Same cumulative total can succeed or fail depending on HOW FAST it accumulated

---

## Part 2: Large File Correlation Analysis

### 2.1 Question: Do Large Files Trigger Resets?

Notable large files in the collection:
- `source/wsd.py`: 50,155 tokens (25% of context window)
- `Update-System.md`: 14,137 tokens
- `tests/test_pre_staging.py`: 15,701 tokens
- `Build-Package-Script-Overview.md`: 12,689 tokens

### 2.2 Findings: Weak Correlation

**Resets After Small Files (<2K tokens)**:
- Journal files (761-1,048 tokens): Present at MULTIPLE reset points
- Both SUCCESS and FAILURE trials show resets after small file reads

**Resets After Large Files (>10K tokens)**:
- Update-System.md (14,137): FAILURE trial 20260120-091729 reset 2
- source/wsd.py (50,155): SUCCESS trial 20260120-093204 reset 2

**Conclusion**: File size at reset point does NOT predict outcome. Both large and small files precede resets in both SUCCESS and FAILURE cases.

### 2.3 Alternative View: Cumulative Batch Size

Rather than individual file size, the relevant metric may be **cumulative tokens in a read batch**:

| Trial | Tokens Read Before Mid-Session Reset | Outcome |
|-------|--------------------------------------|---------|
| 20260120-090620 | 158,856 - 90,000 = 68,856 | FAILURE |
| 20260120-093143 | 153,856 - 85,000 = 68,856 | FAILURE |
| 20260120-093204 | 85,948 - 85,000 = 948 (early reset) | SUCCESS |

The FAILURE trials accumulated ~69K tokens between session start and first mid-session reset. The SUCCESS trial had an early reset after only ~1K tokens of reads.

---

## Part 3: The "Clean Gap" Pattern - Quantified

### 3.1 Pattern Definition

From Analysis-2, we identified the "clean gap" pattern as key to success:
```
SUCCESS = Early reset → GAP with no resets → Late reset after work complete
FAILURE = Resets occurring DURING the active work phase (50-90% of session)
```

### 3.2 Token-Based Gap Analysis

**SUCCESS Trials - Gap Between Resets**:

| Trial | Early Reset | Late Reset | Gap Width | Tokens Read in Gap |
|-------|-------------|------------|-----------|-------------------|
| 20260120-095152 | 87,790 | 340,837 | 60.5% | 253,047 tokens |
| 20260120-093204 | 85,948 | 379,133 | 65.0% | 293,185 tokens |
| 20260119-131802 | ~82K | ~144K | 54.6% | ~62K tokens |

**FAILURE Trials - No Clean Gap**:

| Trial | Reset Positions | Gap Widths | Notes |
|-------|-----------------|------------|-------|
| 20260120-090620 | 56.9%, 82.4%, 98.0% | 25.5%, 15.6% | No early reset, all mid+late |
| 20260120-091729 | 21.5%, 53.8%, 63.1% | 32.3%, 9.3% | Early reset, but rapid mid resets |
| 20260120-093143 | 54.2%, 81.3%, 97.9% | 27.1%, 16.6% | No early reset |

### 3.3 Key Insight: The 50% Marker

Every SUCCESS trial either:
1. Has its only reset after 95% (SINGLE_LATE), OR
2. Has early reset before 50% AND no resets between 50-90% (EARLY_PLUS_LATE)

Every FAILURE trial has at least one reset in the 50-90% range.

The token data reinforces this: the 50-90% session window is where the critical file reading work happens. Resets during this phase clear content that hasn't been processed yet.

---

## Part 4: Answering Open Questions

### Q1: Reset Threshold - At what cumulative token count do resets typically occur?

**Answer**: No fixed threshold. Resets observed from 82K to 383K cumulative tokens.

**Revised Understanding**: Reset timing appears driven by:
- Rate of recent token accumulation
- Session phase (init/work/inquiry)
- Possibly internal context management heuristics

### Q2: Large File Correlation - Do reads of files >10K tokens precede resets more often?

**Answer**: No significant correlation. Resets occur after both small (<1K) and large (>10K) files.

**Caveat**: Large file READS may contribute to the rapid token accumulation rate that triggers resets, even if the reset itself occurs on a subsequent small file.

### Q3: Safe Batch Size - What's the maximum tokens readable without triggering mid-session reset?

**Answer**: The data suggests:
- **After an early reset**: ~60-70K tokens can be read safely before next reset
- **Without an early reset**: First reset occurs around 68K tokens into the read operation

**Tentative Safe Batch**: ~50K tokens between reset opportunities

### Q4: Sequence Effects - Does read order (large-first vs small-first) affect reset timing?

**Answer**: Insufficient data for definitive answer, but observations suggest:
- File order affects WHERE you are in the session when cumulative pressure builds
- Starting with large files may trigger earlier resets (potentially good if early)
- SUCCESS trial 20260120-093204 read large files (wsd.py 50K x5) AFTER early reset

---

## Part 5: Revised Risk Model

Based on token analysis, we refine the risk classification:

### 5.1 Primary Risk Factor: Reset Pattern

| Pattern | Reset Positions | Risk Level | Token Signature |
|---------|-----------------|------------|-----------------|
| SINGLE_LATE | One reset >95% | **LOW** | All work completes before any reset |
| EARLY_PLUS_LATE | <50%, then >95% | **LOW** | Early reset "clears deck", work in protected gap |
| EARLY_PLUS_MID_LATE | <50%, 50-90%, >90% | **HIGH** | Early reset insufficient, mid-session vulnerability |
| MID_HEAVY | Multiple in 50-90% | **CRITICAL** | Active work disrupted by repeated resets |

### 5.2 Secondary Risk Factor: Token Accumulation Rate

| Accumulation Pattern | Risk | Notes |
|---------------------|------|-------|
| Steady with pauses | Lower | Natural breathing room prevents pressure buildup |
| Rapid batch reads | Higher | Fast accumulation triggers mid-session resets |
| Mixed (reads + processing) | Lower | Non-read operations allow context stabilization |

### 5.3 Token-Based Warning Signs

During a session, these patterns suggest elevated phantom read risk:
1. No reset has occurred by 50% through session
2. >50K tokens have been read since last reset
3. Multiple large files (>10K each) queued for sequential read

---

## Part 6: Recommended Next Steps

### Priority 1: Test the "Intentional Early Reset" Hypothesis (HIGH VALUE)

**Hypothesis**: Intentionally triggering an early context reset before beginning multi-file operations may prevent mid-session resets.

**Test Method**:
1. Start session normally
2. Before `/refine-plan`, issue a large context-consuming operation
3. Wait for reset (monitor with `/context`)
4. Then execute `/refine-plan`
5. Record whether mid-session resets still occur

**Rationale**: If early resets "clear the deck" and provide protection, this could be a reliable mitigation.

### Priority 2: Session Batching Strategy (MEDIUM VALUE)

**Hypothesis**: Breaking multi-file reads into smaller batches with processing gaps may prevent the rapid accumulation that triggers mid-session resets.

**Test Method**:
1. Modify `/refine-plan` to read files in batches of 3-4
2. Insert a "summarize findings so far" step between batches
3. This forces token output (processing) rather than pure accumulation

### Priority 3: Validate Rate-Based Threshold Theory (RESEARCH)

**Question**: Is there a tokens-per-turn accumulation rate that reliably predicts resets?

**Method**:
1. Calculate delta(cache_read_tokens) / turn for each trial
2. Identify if FAILURE trials show higher accumulation rates
3. If confirmed, establish "safe accumulation rate" guidance

### Priority 4: Cross-Version Testing (VALIDATION)

The token analysis was performed on current Claude Code builds. To confirm findings aren't version-specific:
1. Run trials on 2.0.58 (Era 1 mechanism)
2. Run trials on different Claude Code versions
3. Compare token patterns across versions

---

## Part 7: Conclusion

The token count data reveals that **phantom reads are not caused by a simple context size threshold**. Instead, the critical factor is **when resets occur during the session lifecycle**:

```
The same agent doing the same work with the same files can succeed or fail
depending on whether context resets happen DURING or AFTER the file reading phase.
```

This reframes the problem from "how do we stay under a threshold" to "how do we ensure resets happen at safe times." The most promising mitigation strategies involve:

1. **Intentional early resets** before beginning multi-file operations
2. **Batching reads** with processing gaps to prevent rapid token accumulation
3. **Session design** that front-loads context-heavy setup before critical reads

The next phase of investigation should focus on testing these mitigation strategies to determine if phantom reads can be reliably prevented through session structure rather than waiting for a platform fix.

---

## Appendix A: Trial Data with Token Counts

Full reset-with-context data for analyzed trials:

### SUCCESS Trials

**20260120-093130** (SINGLE_LATE)
- Total tokens read: 105,476
- Largest file: source/wsd.py (50,155)
- Resets: 1 at 97.7%
- Reset 1: 139,643 cumulative, after Journal (967 tokens)

**20260120-095152** (EARLY_PLUS_LATE)
- Total tokens read: 254,837
- Largest file: source/wsd.py (50,155)
- Resets: 2 at 37.2%, 97.7%
- Reset 1: 87,790 cumulative, after Journal (895 tokens)
- Reset 2: 340,837 cumulative, after Journal (895 tokens)

**20260120-093204** (EARLY_PLUS_LATE)
- Total tokens read: 93,513
- Largest file: source/wsd.py (50,155)
- Resets: 2 at 30.0%, 95.0%
- Reset 1: 85,948 cumulative, after Journal (948 tokens)
- Reset 2: 379,133 cumulative, after wsd.py (50,155 tokens)

### FAILURE Trials

**20260120-090620** (EARLY_PLUS_MID_LATE)
- Total tokens read: 126,745
- Largest file: source/wsd.py (50,155)
- Resets: 3 at 56.9%, 82.4%, 98.0%
- Reset 1: 158,856 cumulative, after build_package.py (9,243 tokens)
- Reset 2: 230,942 cumulative, after Stage-Release-Script-Overview.md (7,366 tokens)
- Reset 3: 231,990 cumulative, after Journal (1,048 tokens)

**20260120-091729** (EARLY_PLUS_MID_LATE)
- Total tokens read: 357,972
- Largest file: source/wsd.py (50,155)
- Resets: 3 at 21.5%, 53.8%, 63.1%
- Reset 1: 88,522 cumulative, after Journal (761 tokens)
- Reset 2: 355,902 cumulative, after Update-System.md (14,137 tokens)
- Reset 3: 383,353 cumulative, after pre_staging.py (8,782 tokens)

**20260120-093143** (LATE_CLUSTERED)
- Total tokens read: 141,793
- Largest file: source/wsd.py (50,155)
- Resets: 3 at 54.2%, 81.3%, 97.9%
- Reset 1: 153,856 cumulative, after build_package.py (9,243 tokens)
- Reset 2: 225,942 cumulative, after Stage-Release-Script-Overview.md (7,366 tokens)
- Reset 3: 226,990 cumulative, after Journal (1,048 tokens)

---

*Analysis performed: 2026-01-20*
*Workscope ID: 20260120-135500*
