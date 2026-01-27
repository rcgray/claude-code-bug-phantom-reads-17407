# Consolidated Theory of Phantom Reads

This document consolidates our evolving understanding of the Phantom Reads phenomenon in Claude Code, integrating findings from 31+ controlled trials, manual experimentation, and systematic analysis of session data.

**Last Updated**: 2026-01-23

---

## Executive Summary

Phantom reads occur when Claude Code's Read tool executes successfully but the model receives placeholder markers instead of actual file content. The model proceeds without awareness of the gap, often confabulating plausible-sounding analysis based on incomplete information.

Our investigation has converged on a **dual-condition model**: phantom reads require both (1) an operation that would exceed the context window threshold, AND (2) a context reset occurring during deferred read processing. Neither condition alone is sufficient.

---

## The Core Mechanism

### What Happens During a Read

1. **Tool Execution**: The Read tool executes and retrieves file content
2. **Session Logging**: Content is recorded to the session `.jsonl` file
3. **Context Management**: A separate system decides what reaches the model
4. **Potential Transformation**: Large results may be persisted to disk or cleared from context
5. **Model Receipt**: The model receives either actual content OR a placeholder marker

**Critical Insight**: The session `.jsonl` file logs tool execution results, NOT what the model receives. Phantom read markers (`<persisted-output>` or `[Old tool result content cleared]`) appear nowhere in session files—only in agent self-reports discussing their experience.

### Two Eras of Phantom Reads

| Era | Versions | Marker | Mechanism |
|-----|----------|--------|-----------|
| 1 | ≤2.0.59 | `[Old tool result content cleared]` | Context clearing after logging |
| 2 | ≥2.0.60 | `<persisted-output>` | Disk persistence without follow-up |

Both eras exhibit the same fundamental problem: the model believes it read the file when it did not.

---

## The X + Y Model

Our latest experiments reveal that phantom reads are governed by a **threshold overflow model**:

### Variables

- **X** = Pre-operation context consumption (baseline + preloaded content)
- **Y** = Operation context requirement (files read during the triggering action)
- **T** = Context window threshold (appears to be sub-200K based on harness warnings)

### The Condition

**Phantom reads can only occur when X + Y > T**

When X + Y ≤ T, all content fits within the context window, no aggressive context management is triggered, and all reads complete successfully—even at very high utilization (90%+).

### Evidence

Experiment-Methodology-04 trials with calibrated preloading:

| Scenario | X (Pre-op) | Y (Operation) | X + Y | Outcome |
|----------|------------|---------------|-------|---------|
| Easy | 73K (37%) | 40K | 113K | SUCCESS |
| Medium | 92K (46%) | 40K | 132K | SUCCESS |
| Hard | 120K (60%) | 40K | 160K | SUCCESS |

All scenarios succeeded because X + Y remained within the ~200K threshold. When additional files were added to push Y higher (adding `module-epsilon.md` and `module-phi.md`), the Hard scenario began manifesting phantom reads.

### Implication

**There is no universally "dangerous" pre-operation consumption level.** A session at 60% pre-op with a small operation (Y) will succeed, while a session at 40% pre-op with a large operation (Y) may fail. The relationship between X and Y relative to T is what matters.

---

## Deferred Reads: The Proximate Cause

### What Are Deferred Reads?

When Claude Code initiates multiple file reads, some may be processed asynchronously rather than synchronously inserted into context. These "deferred reads" appear to be a performance optimization that becomes problematic when context management operations (resets) occur simultaneously.

### Conditions That Trigger Deferred Reads

Based on experimental observation, deferred reads appear to require:

1. **Multiple simultaneous reads**: Single file reads appear to complete synchronously
2. **Agent-initiated reads**: Hoisted files (via `@` notation) appear to load differently
3. **Threshold proximity**: May only occur when X + Y approaches or exceeds T

### The Failure Mode

```
1. Agent initiates batch read operation (e.g., via /refine-plan)
2. Some reads are deferred for async processing
3. Context management triggers a reset (due to approaching threshold)
4. Deferred reads complete but content is cleared/persisted during reset
5. Model receives placeholder markers instead of content
6. Model proceeds without awareness of the gap
```

**Not all deferred reads become phantom reads.** Deferred reading may be a successful optimization that only fails when a reset occurs during processing.

---

## Reframing Existing Theories

### Reset Timing Theory — REFRAMED

**Original Understanding**: Mid-session resets (50-90% of session) predict phantom reads with 100% accuracy.

**Refined Understanding**: Mid-session resets correlate with phantom reads because:
1. Deferred reads only occur during multi-file operations
2. Multi-file operations (like `/refine-plan`) occur late in experimental flows
3. Late operations naturally push context into the 50-90% range
4. This is where X + Y is most likely to exceed T

The timing correlation may be an **artifact of experimental design** rather than a fundamental property of the bug. The true predictor is whether a reset occurs during deferred read processing.

### Headroom Theory — REFRAMED

**Original Understanding**: Low starting headroom (<80K remaining) predicts phantom reads.

**Refined Understanding**: Headroom matters only relative to operation size Y:
- Headroom = T - X
- Phantom reads occur when Y > Headroom
- A session with 50K headroom and 40K operation (Y) will succeed
- A session with 80K headroom and 100K operation (Y) will fail

**Headroom is not a universal threshold—it's a budget that must accommodate the operation.**

### Reset Count Theory — REFRAMED

**Original Understanding**: More resets correlate with more phantom reads (2 resets = safe, 4+ = failure).

**Refined Understanding**: Reset count correlates because:
1. Each reset is an opportunity for deferred reads to be disrupted
2. More resets = more opportunities for phantom read conditions
3. Sessions with higher X + Y trigger more resets
4. The count is a downstream indicator, not a causal factor

### Dynamic Context Pressure — SUPPORTED

**Hypothesis**: Rapid token accumulation triggers resets more readily than steady accumulation.

This remains plausible and may explain why batch reads (rapid accumulation) are more vulnerable than sequential reads with processing pauses between them.

---

## The "Clean Gap" Pattern — EXPLAINED

Successful sessions exhibit:
1. Early reset at <50% (during setup)
2. Uninterrupted processing window of 35-40%
3. Late reset at >90% (after work completes)

**Why this pattern succeeds**: The early reset occurs before the multi-file operation. The clean gap allows the operation to complete without reset interference. The late reset occurs after all reads have been processed.

**Why fragmented patterns fail**: Mid-session resets interrupt deferred read processing, converting them to phantom reads.

---

## Open Investigations

### Token Accounting Discrepancy

In Hard scenario trials:
- Files contributed: 23K (baseline) + 68K (preload) + 40K (operation) = **131K tokens**
- Harness reported: **156.5K tokens** (78.2% of 200K)
- Discrepancy: **~25K tokens unaccounted**

Possible explanations:
- Thinking tokens (extended thinking mode)
- System prompt overhead
- Message formatting overhead
- Conversation structure tokens

**Status**: Needs investigation to understand true context composition.

### Context Reporting Accuracy

The harness reports context limits that appear conservative:
- "10% remaining" reported at 152K (76% consumed)
- "0% remaining" reported at 180K (90% consumed)

This suggests either:
1. The harness reserves buffer space (like setting clocks forward)
2. The effective context window is smaller than 200K
3. Additional overhead not reflected in token counts

**Status**: Needs investigation to determine true operational threshold.

### Hoisting vs. Agent-Initiated Reads

Hoisted files (via `@` notation) appear to behave differently:
- Files exceeding 25K tokens are silently skipped
- Hoisted files don't seem to trigger phantom reads
- May use different code path than agent-initiated reads

**Experiment Proposed**: Hoist >200K tokens via `@` notation to test whether phantom reads can occur in hoisting alone, or only in agent-initiated reads.

### Reset Trigger Conditions

Despite extensive observation, we still don't know what triggers a reset:
- Not a fixed token threshold (observed at 82K-383K)
- Not purely rate-based (though rapid accumulation correlates)
- Not purely time-based
- May be a combination of factors

**Status**: Fundamental question requiring deeper harness investigation.

---

## Conditions Required for Phantom Reads

Based on current evidence, phantom reads require ALL of the following:

| Condition | Description | Evidence |
|-----------|-------------|----------|
| **Threshold Overflow** | X + Y > T | All within-threshold scenarios succeed |
| **Deferred Reads** | Multiple files read simultaneously | Single reads appear safe |
| **Agent-Initiated** | Reads triggered by agent, not hoisting | Hoisted files behave differently |
| **Reset During Processing** | Context reset while reads are deferred | Clean gap pattern succeeds |

**Remove any condition and phantom reads don't occur.**

---

## Implications for Reproduction

### Why Current Scenarios Succeed

Our Experiment-Methodology-04 scenarios all have X + Y within the threshold:
- Easy: 113K < T
- Medium: 132K < T
- Hard: 160K < T

Even at 90% utilization, if all content fits, no phantom reads occur.

### How to Reliably Trigger Phantom Reads

To create a reliable reproduction:
1. **Increase Y**: Add more files to the operation phase (e.g., `module-epsilon.md`, `module-phi.md`)
2. **Ensure X + Y > T**: Pre-operation consumption + operation files must exceed threshold
3. **Use agent-initiated reads**: The `/analyze-wpd` pattern triggers batch reads
4. **Don't use hoisting for operation files**: Hoisted files appear to load differently

### Proposed Scenario Refinement

| Scenario | Target X | Target Y | Target X+Y | Expected |
|----------|----------|----------|------------|----------|
| Easy | 37% (73K) | 40K | 113K (<T) | SUCCESS |
| Medium | 46% (92K) | 60K | 152K (~T) | MIXED |
| Hard | 60% (120K) | 80K+ | 200K+ (>T) | FAILURE |

The Hard scenario needs Y increased to push X + Y over threshold.

---

## Theory Status Summary

| Theory | Status | Refinement |
|--------|--------|------------|
| **X + Y Model** | NEW - PRIMARY | Threshold overflow is necessary condition |
| **Deferred Reads** | NEW - PRIMARY | Multi-file agent reads can be deferred |
| **Reset Timing** | REFRAMED | Artifact of when deferred reads occur |
| **Headroom** | REFRAMED | Relative to Y, not universal |
| **Reset Count** | REFRAMED | Downstream indicator, not causal |
| **Clean Gap** | EXPLAINED | Allows operation to complete before reset |
| **Dynamic Pressure** | SUPPORTED | May explain batch read vulnerability |

---

## Future Directions

### Immediate Actions

1. **Increase Hard scenario Y**: Add files to push X + Y over threshold
2. **Run validation trials**: Confirm revised scenarios produce expected outcomes
3. **Investigate token discrepancy**: Account for the ~25K missing tokens

### Research Priorities

4. **Test hoisting-only scenario**: Can >200K hoisted tokens trigger phantom reads?
5. **Investigate reset triggers**: What internally causes a reset at a specific moment?
6. **Test intentional early reset mitigation**: Force early reset to create protected window
7. **Measure effective threshold T**: Determine actual operational limit

### Documentation

8. **Update Experiment-Methodology-04**: With refined scenario parameters
9. **Update Investigation-Journal**: With these consolidated findings
10. **Update README**: Reflect current theoretical understanding

---

## Conclusion

The phantom reads bug is not a simple threshold problem but a **confluence of conditions**: context overflow, deferred reads, agent-initiated operations, and reset timing. Our previous theories captured correlations that are now explained by this unified model.

The key insight is that **within-threshold operations are safe regardless of utilization percentage**. Phantom reads require pushing beyond the context window's capacity while simultaneously experiencing a reset during deferred read processing.

This understanding enables more precise reproduction scenarios and points toward potential mitigations: avoiding threshold overflow, using sequential reads instead of batch operations, or forcing early resets to create protected processing windows.

---

*This document supersedes individual theory discussions in the Investigation Journal. For historical context and raw experimental data, see `Investigation-Journal.md` and the analysis documents (`WSD-Dev-02-Analysis-*.md`, `Repro-Attempts-02-Analysis-1.md`).*
