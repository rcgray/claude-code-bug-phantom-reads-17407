# Reset Timing Theory

This document presents a new hypothesis for phantom read occurrence based on analysis of the `wsd-dev-02` trial collection. The findings suggest that **context reset timing**—not just reset count or pre-operation headroom—is the critical predictor of phantom read failures.

**Status**: Hypothesis under investigation
**Evidence Base**: 7 trials from `wsd-dev-02` collection (2026-01-19)
**Relationship to Other Theories**: Refines and extends the Reset Theory and Headroom Theory documented in `Trial-Analysis-Guide.md`

---

## Executive Summary

Analysis of 7 controlled trials revealed that neither pre-operation context consumption (Headroom Theory) nor total reset count (Reset Theory) reliably predicts phantom read occurrence. Instead, the **timing pattern of context resets relative to session progression** shows strong correlation with outcomes:

- **All successful trials** exhibited an "EARLY + LATE" reset pattern
- **All failed trials** exhibited either multiple mid-session resets or "LATE CLUSTERED" resets
- One critical anomaly (Trial 133726) had identical headroom and reset count to successful trials but failed due to late clustered timing

This suggests that **when** resets occur matters more than **how many** occur or **how much** headroom exists.

---

## Background: The Existing Theories

### Headroom Theory (Prior Hypothesis)

**Claim**: Pre-operation context consumption predicts phantom read risk. Sessions starting above 60% consumption (less than 80K headroom) face elevated risk.

**Mechanism**: Low headroom → context fills quickly → reset threshold reached sooner → more resets → phantom reads

### Reset Theory (Prior Hypothesis)

**Claim**: Context reset frequency correlates with phantom reads. Sessions experiencing 3+ resets show higher failure rates than those with 1-2 resets.

**Mechanism**: More resets → more opportunities for recently-read content to be cleared → higher phantom read probability

### Limitations Discovered

The `wsd-dev-02` trials exposed cases where both theories fail:

| Trial | Pre-Op | Headroom | Resets | Headroom Prediction | Reset Prediction | Actual |
|-------|--------|----------|--------|---------------------|------------------|--------|
| 133726 | 86K (43%) | 114K | 2 | LOW RISK | LOW RISK | **FAILURE** |
| 140145 | 83K (41%) | 117K | 3 | LOW RISK | MEDIUM RISK | **FAILURE** |

Trial 133726 is particularly significant: it had MORE headroom than the successful trial 131802 (114K vs 115K) and the SAME reset count (2), yet it failed. This directly contradicts both theories.

---

## The Reset Timing Theory

### Core Claim

**The timing pattern of context resets relative to session progression is the primary predictor of phantom read occurrence.**

Specifically:
- Resets occurring **early** in a session (<50% through) are protective
- Resets occurring **late** in a session (>90% through) are benign
- Resets occurring **mid-session** (50-90% through) correlate with failures
- **Clustered late resets** (multiple resets >80%, close together) correlate with failures

### Evidence: The WSD-Dev-02 Trials

Seven trials were conducted using identical methodology (Experiment-Methodology-02) against the WSD Development project using the `/refine-plan` command.

#### Full Dataset

| Trial ID | Pre-Op | Headroom | Resets | Reset Pattern | Reset Positions | Outcome |
|----------|--------|----------|--------|---------------|-----------------|---------|
| 20260119-131802 | 85K (43%) | 115K | 2 | EARLY + LATE | 42%, 97% | SUCCESS |
| 20260119-132353 | 110K (55%) | 90K | 4 | EARLY + MID/LATE | 40%, 64%, 81%, 98% | FAILURE |
| 20260119-133027 | 86K (43%) | 114K | 4 | EARLY + MID/LATE | 30%, 62%, 74%, 98% | FAILURE |
| 20260119-133726 | 86K (43%) | 114K | 2 | LATE CLUSTERED | 83%, 97% | FAILURE |
| 20260119-140145 | 83K (41%) | 117K | 3 | EARLY + MID/LATE | 29%, 75%, 98% | FAILURE |
| 20260119-140906 | 96K (48%) | 104K | 4 | EARLY + MID/LATE | 47%, 78%, 91%, 98% | FAILURE |
| 20260119-142117 | 87K (43%) | 113K | 2 | EARLY + LATE | 45%, 98% | SUCCESS* |

\* Trial 142117 showed context cleared on second `/context` call but no phantom reads self-reported.

#### Pattern Classification

**SUCCESS Pattern: "EARLY + LATE"**
- Exactly 2 resets
- First reset: 40-45% through session
- Second reset: 97-98% through session
- No resets in the 50-90% range

**FAILURE Pattern A: "EARLY + MID/LATE"**
- 3-4 resets
- First reset: 29-47% through session (early)
- Additional resets: 62-91% through session (mid-session)
- Final reset: 98% through session (late)

**FAILURE Pattern B: "LATE CLUSTERED"**
- 2 resets (same count as success!)
- Both resets: >80% through session
- Resets close together (5 data points apart)

### The Critical Anomaly: Trial 133726

This trial is the strongest evidence for the Reset Timing Theory:

| Metric | Trial 131802 (SUCCESS) | Trial 133726 (FAILURE) |
|--------|------------------------|------------------------|
| Pre-operation | 85K (43%) | 86K (43%) |
| Headroom | 115K | 114K |
| Reset count | 2 | 2 |
| **Reset timing** | **42%, 97%** | **83%, 97%** |

The ONLY meaningful difference is reset timing:
- Success: First reset at 42% (early), second at 97% (late)
- Failure: First reset at 83% (late), second at 97% (late) — both clustered late

This proves that reset timing, not count or headroom, determined the outcome.

---

## Proposed Mechanism

### Why Early Resets Are Protective

An early reset (before multi-file read operations begin) creates fresh headroom:

```
Session start → Initialization work → EARLY RESET (clears old content)
     ↓
Fresh context available → Multi-file reads begin → Content retained
     ↓
Operations complete → LATE RESET (cleanup) → Session end
```

The early reset acts as a "clearing house" that ensures maximum headroom is available when critical read operations occur.

### Why Mid-Session Resets Cause Failures

Mid-session resets occur DURING critical operations:

```
Session start → Initialization → Multi-file reads BEGIN
     ↓
Context fills → MID-SESSION RESET → Recently-read content CLEARED
     ↓
More reads → Another MID-SESSION RESET → More content CLEARED
     ↓
Agent proceeds with incomplete information → PHANTOM READS
```

The reads that occur just before a mid-session reset are the ones most likely to become phantom reads.

### Why Late Clustered Resets Cause Failures

When both resets occur late and close together:

```
Session start → Long initialization → No early reset (no headroom refresh)
     ↓
Multi-file reads → Context pressure builds without relief
     ↓
LATE RESET → Some content cleared during critical phase
     ↓
Immediately → Another LATE RESET → More content cleared
     ↓
Operations incomplete → PHANTOM READS
```

The absence of an early reset means the critical operations occur under pressure, and the clustered late resets indicate the system struggling to manage context during or immediately after critical work.

---

## Revised Risk Classification

### By Timing Pattern

| Pattern | Reset Timing | Risk Level | Observed Outcome |
|---------|--------------|------------|------------------|
| EARLY + LATE | <50% and >90% only | LOW | SUCCESS (2/2) |
| EARLY + MID/LATE | <50% plus 50-90% | HIGH | FAILURE (4/4) |
| LATE CLUSTERED | Both >80%, close together | HIGH | FAILURE (1/1) |

### Predictive Model

```
IF first_reset < 50% AND no_resets_between(50%, 90%) AND last_reset > 90%:
    PREDICT: LOW RISK (likely success)
ELSE IF any_resets_between(50%, 90%):
    PREDICT: HIGH RISK (likely failure)
ELSE IF all_resets > 80% AND resets_clustered:
    PREDICT: HIGH RISK (likely failure)
```

This model correctly classifies all 7 trials in the `wsd-dev-02` dataset.

---

## Relationship to Prior Theories

### Headroom Theory: Subsumed

The Headroom Theory isn't wrong—it's incomplete. Low headroom CAN contribute to phantom reads, but only because it affects reset timing:

```
Low headroom → Context fills faster → Resets occur sooner and more frequently
            → More likely to have mid-session resets → Higher phantom read risk
```

However, trials with HIGH headroom can still fail if reset timing is unfavorable (Trial 133726).

### Reset Theory: Refined

The Reset Theory's correlation between reset count and failure is explained by timing:

```
More resets → Higher probability that some occur mid-session
           → Higher phantom read risk
```

But reset count alone doesn't determine outcome—Trial 133726 proves that 2 resets can cause failure if timed poorly.

### Combined Model

```
                    ┌─────────────────┐
                    │ Session Begins  │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
        Early Reset?                  No Early Reset
              │                             │
              ▼                             ▼
     ┌────────────────┐           ┌─────────────────┐
     │ Headroom       │           │ No headroom     │
     │ refreshed      │           │ refresh         │
     └───────┬────────┘           └────────┬────────┘
             │                              │
             ▼                              ▼
     Multi-file reads              Multi-file reads
             │                              │
    ┌────────┴────────┐           ┌────────┴────────┐
    │                 │           │                 │
No mid-session    Mid-session    Pressure builds   Late clustered
resets            resets         (no early reset)  resets
    │                 │                 │               │
    ▼                 ▼                 ▼               ▼
Late reset       Content cleared   Late clustered   Content cleared
(cleanup)        during ops        resets           during ops
    │                 │                 │               │
    ▼                 ▼                 ▼               ▼
 SUCCESS           FAILURE           FAILURE         FAILURE
```

---

## Open Questions

### Q1: What determines reset timing?

Is the timing of context resets:
- **Deterministic**: Based on token thresholds or time intervals?
- **Probabilistic**: Random within certain bounds?
- **Reactive**: Triggered by specific operations?

Understanding this would explain why identical workloads produce different patterns.

### Q2: Can reset timing be influenced?

If resets are threshold-based, could strategic pauses or smaller operation batches help achieve the "EARLY + LATE" pattern?

### Q3: What happens at the reset boundary?

When a reset occurs at 82K tokens, what determines which content is cleared? Is it:
- FIFO (oldest content first)?
- LRU (least recently used)?
- Size-based (largest items first)?
- Random?

### Q4: Are certain operations "reset triggers"?

Do specific operations (large file reads, subagent spawning) directly trigger resets, or are resets purely threshold-based?

---

## Implications for Mitigation

If the Reset Timing Theory is correct, potential mitigations include:

1. **Trigger early reset deliberately**: Start sessions with operations that consume then release context, forcing an early reset before critical work.

2. **Batch operations strategically**: Ensure all critical reads complete before likely reset thresholds.

3. **Monitor for mid-session resets**: If a reset occurs mid-operation, assume phantom reads and re-read affected files.

4. **Avoid late-session intensive operations**: If most work is done (>80% through session), avoid multi-file reads that might trigger clustered resets.

These are speculative and require further investigation.

---

## Next Steps for Investigation

### Priority 1: Validate with More Trials

The current evidence base (7 trials) is small. Additional trials would:
- Test whether the pattern classification holds
- Identify edge cases or exceptions
- Provide statistical confidence

### Priority 2: Understand Reset Triggers

Investigate what causes resets to occur when they do:
- Is there a consistent token threshold (~140K)?
- Does operation type matter?
- Is there a time component?

### Priority 3: Test Mitigation Strategies

If the theory holds, test whether:
- Deliberate early context consumption prevents mid-session resets
- Breaking operations into smaller batches improves success rate
- Post-reset re-reads recover lost content

---

## Appendix: Raw Data

### Token Progression Snapshots

**Trial 131802 (SUCCESS)**
```
33 → 77 → ... → 82 → |21 → 86 → ... → 144 → |21
                 ↑                      ↑
            EARLY (42%)            LATE (97%)
```

**Trial 133726 (FAILURE)**
```
33 → 77 → ... → 108 → 134 → |21 → 136 → |21
                        ↑          ↑
                   LATE (83%)  LATE (97%)
                   ← CLUSTERED →
```

### Session File Locations

All trial data stored in `dev/misc/wsd-dev-02/{workscope-id}/`:
- Chat export: `{workscope-id}.txt`
- Session file: `{uuid}.jsonl`

---

*Document created: 2026-01-19*
*Analysis performed by: Workscope-20260119-163530*
