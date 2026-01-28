# Barebones-2120 Experiment Analysis

**Experiment ID**: Barebones-2120  
**Collection**: `dev/misc/repro-attempts-04-2120/`  
**Date Conducted**: 2026-01-27  
**Claude Code Version**: 2.1.20  
**Analyst**: User Agent (Workscope-20260127-205322)  
**Analysis Date**: 2026-01-27  

---

## Executive Summary

This experiment tested whether the Phantom Reads bug persists in Claude Code version 2.1.20, representing a 14-version jump from our locked testing version (2.1.6). Using identical protocol and environment as Barebones-216, the version variable was isolated.

**Critical Finding**: The Phantom Reads bug appears to be **ABSENT or fundamentally mitigated** in version 2.1.20.

| Metric       | Barebones-216 (v2.1.6)  | Barebones-2120 (v2.1.20) | Change   |
|--------------|-------------------------|--------------------------|----------|
| Failure Rate | 100% (4/4 valid trials) | **0% (0/5)**             | **-100%** |
| Success Rate | 0% (0/4 valid trials)   | **100% (5/5)**           | **+100%** |
| Protocol     | Identical               | Identical                | None     |
| Environment  | Identical               | Identical                | None     |

This dramatic reversal with only the version changing strongly suggests a harness-level change occurred between versions 2.1.6 and 2.1.20.

---

## RQ-BB2120-1: Did Anthropic fix or mitigate the Phantom Reads bug?

**Status**: ANSWERED - STRONG EVIDENCE OF FIX OR MITIGATION

### Primary Evidence

**100% outcome reversal with version as the ONLY variable:**
- Same barebones repository
- Same protocol (Experiment-Methodology-04)
- Same file set (12 spec files + WPD)
- Same `/setup-hard` preload configuration
- ONLY difference: Claude Code version (2.1.6 → 2.1.20)

### Trial Summary Comparison

**Barebones-2120 (v2.1.20) - All Trials:**

| Trial ID        | Outcome | Resets | Pattern     | Peak Tokens | Tool Results Dir |
|-----------------|---------|--------|-------------|-------------|------------------|
| 20260127-095002 | SUCCESS | 1      | SINGLE_LATE | 159,633     | No               |
| 20260127-100209 | SUCCESS | 1      | SINGLE_LATE | 172,990     | No               |
| 20260127-100701 | SUCCESS | 1      | SINGLE_LATE | 172,999     | No               |
| 20260127-100944 | SUCCESS | 1      | SINGLE_LATE | 173,000     | No               |
| 20260127-101305 | SUCCESS | 1      | SINGLE_LATE | 159,921     | No               |

**Success Rate**: 5/5 (100%)  
**Average Resets**: 1.0  
**Reset Pattern**: 100% SINGLE_LATE (resets at 84.8-86.6% of session)

**Barebones-216 (v2.1.6) - Valid Trials:**

| Trial ID        | Outcome | Resets | Pattern            | Peak Tokens | Tool Results Dir |
|-----------------|---------|--------|--------------------|-------------|------------------|
| 20260127-092743 | FAILURE | 2      | OTHER              | ~162,700    | Yes              |
| 20260127-093127 | FAILURE | 3      | EARLY_PLUS_MID_LATE| ~161,709    | Yes              |
| 20260127-093818 | FAILURE | 2      | OTHER              | ~162,693    | Yes              |
| 20260127-094145 | FAILURE | 3      | OTHER              | ~164,893    | Yes              |

**Failure Rate**: 4/4 (100%)  
**Average Resets**: 2.5  
**Reset Patterns**: Mixed, including mid-session resets

### Key Observations

#### 1. Reset Pattern Consistency in 2.1.20

**ALL 2.1.20 trials exhibited SINGLE_LATE pattern** - exactly the pattern the Reset Timing Theory predicted would succeed. The resets occurred at 84.8-86.6% through the session, well after all file reading operations completed.

This is in stark contrast to 2.1.6 trials, which showed:
- Multiple resets (2-3 per trial)
- Mid-session resets during active file reading
- Varied and unpredictable reset patterns

#### 2. Tool Results Directory Absence

**No `tool-results/` directories were created in ANY 2.1.20 trial.** This indicates:
- No tool results were persisted to disk
- All Read operations returned content inline
- The `<persisted-output>` mechanism was not triggered

In 2.1.6 trials, all 4 valid trials created `tool-results/` directories with multiple persisted files.

#### 3. Peak Token Consumption

Both version collections reached similar peak token levels:
- 2.1.20: 159-173K tokens (average ~167K)
- 2.1.6: 162-164K tokens (average ~163K)

The similar peak consumption indicates the context pressure was equivalent. The difference in outcomes cannot be attributed to one version reaching higher token counts than the other.

#### 4. Agent Self-Reports

**2.1.20 agents unanimously reported:**
- "No, I did not experience this issue"
- "All Read calls returned inline content with line numbers"
- "No `<persisted-output>` messages encountered"

**2.1.6 agents unanimously reported:**
- "Yes, I did experience this issue"
- Confirmed receiving `<persisted-output>` markers
- Acknowledged proceeding without actual file content

### Statistical Significance

With 4 valid trials in 2.1.6 and 5 trials in 2.1.20, Fisher's exact test yields **p < 0.01** for the observed difference (4/4 failures vs 0/5 failures), representing a highly significant result.

The probability this outcome occurred by chance is less than 1%.

### Interpretation

Four possible explanations for this finding:

**A. Deliberate Fix (Most Likely)**
Anthropic identified and fixed the Phantom Reads mechanism between 2.1.6 and 2.1.20. This could have been:
- Direct response to GitHub Issue #17407
- Internal detection of the same issue
- Part of broader context management improvements

**B. Incidental Fix (Plausible)**
A related change (optimization, refactoring, architectural improvement) inadvertently resolved the issue without Anthropic explicitly targeting phantom reads. Possible changes:
- Context management algorithm improvements
- Tool result handling optimizations
- Memory or caching architecture changes

**C. Threshold Shift (Less Likely)**
Context management thresholds changed, making our X+Y scenario no longer sufficient to trigger the bug. However:
- Peak token consumption was similar between versions
- If merely a threshold shift, we'd expect to see some variation in 2.1.20 outcomes
- The 100% success rate suggests more than threshold adjustment

**D. Mechanism Change (Least Likely)**
The bug still exists but manifests differently. However:
- No new marker types were observed
- Agents confirmed receiving actual content
- No evidence of alternative phantom read indicators

### Conclusion for RQ-BB2120-1

**Answer**: YES, Anthropic appears to have fixed or significantly mitigated the Phantom Reads bug between versions 2.1.6 and 2.1.20.

**Evidence Strength**: Very Strong
- 100% outcome reversal
- Statistically significant (p < 0.01)
- Consistent reset patterns in 2.1.20 (all SINGLE_LATE)
- No persisted outputs in 2.1.20
- Similar context pressure in both versions

**Most Probable Explanation**: Deliberate or incidental fix in the harness's context management system.

**Confidence Level**: High (90%+)

The uniformity of 2.1.20 successes, combined with the absence of tool-results directories and consistent SINGLE_LATE patterns matching theoretical predictions, provides compelling evidence that the underlying mechanism causing phantom reads has been resolved.

---

## Next Steps

### Immediate Questions to Answer

1. **RQ-BB2120-8**: At which version between 2.1.6 and 2.1.20 did the behavior change?
   - Binary search to identify exact version boundary
   - Would narrow the range of potential changes

2. **RQ-BB2120-7**: What changed in Claude Code between these versions?
   - Review release notes/changelogs
   - Look for context management or tool result handling changes

3. **RQ-BB2120-6**: Can phantom reads still be triggered in 2.1.20 with extreme conditions?
   - Test `/setup-extreme` with higher X
   - Add more spec files to increase Y
   - Determine if fix is complete or threshold-based

### Research Implications

**If this finding holds:**
1. The Phantom Reads bug may be **resolved for users on current versions**
2. MCP Filesystem workaround may no longer be necessary for 2.1.20+
3. Investigation should shift to:
   - Documenting version boundaries
   - Understanding what changed (for posterity)
   - Verifying the fix is robust across use cases

**Documentation Updates Needed:**
1. Update README.md with version-specific guidance
2. Update WORKAROUND.md noting version where fix occurred
3. Add version boundary to GitHub Issue #17407
4. Update PRD.md with resolution status

---

## Detailed Trial Analysis

### Version 2.1.20 Trials (All Success)

#### Trial 20260127-095002
- **Outcome**: SUCCESS
- **Reset Count**: 1
- **Reset Pattern**: SINGLE_LATE (84.8% of session)
- **Reset From**: 159,633 tokens → 17,942 tokens
- **Files Read**: 9 (all successful, all inline)
- **Tool Results**: None persisted
- **Agent Quote**: "No, I did not experience this issue during my execution."

**Analysis**: Textbook clean execution. Single late reset occurred after all file reading completed. Agent received all content inline.

#### Trial 20260127-100209
- **Outcome**: SUCCESS
- **Reset Count**: 1
- **Reset Pattern**: SINGLE_LATE (85.1% of session)
- **Reset From**: 172,990 tokens → 17,943 tokens
- **Peak Consumption**: 173K tokens (86.5% of 200K window)
- **Files Read**: 9 (all successful, all inline)
- **Tool Results**: None persisted
- **Agent Quote**: "No, I did not experience this issue in this session."

**Analysis**: Reached highest peak of all 2.1.20 trials (173K), demonstrating that even under maximum context pressure tested, phantom reads did not occur.

#### Trial 20260127-100701
- **Outcome**: SUCCESS
- **Reset Count**: 1
- **Reset Pattern**: SINGLE_LATE (85.1% of session)
- **Reset From**: 172,999 tokens → 17,948 tokens
- **Peak Consumption**: 173K tokens (86.5% of 200K window)
- **Files Read**: 9 (all successful, all inline)
- **Tool Results**: None persisted
- **Agent Quote**: "No, I did not experience that issue in this session."

**Analysis**: Nearly identical to trial 100209, confirming consistency of 2.1.20 behavior under high context pressure.

#### Trial 20260127-100944
- **Outcome**: SUCCESS
- **Reset Count**: 1
- **Reset Pattern**: SINGLE_LATE (85.3% of session)
- **Reset From**: 173,000 tokens → 17,941 tokens
- **Peak Consumption**: 173K tokens (86.5% of 200K window)
- **Files Read**: 9 (all successful, all inline)
- **Tool Results**: None persisted
- **Agent Quote**: "No, I did not experience that issue in this session."

**Analysis**: Reached absolute peak of tested range. Still no phantom reads.

#### Trial 20260127-101305
- **Outcome**: SUCCESS
- **Reset Count**: 1
- **Reset Pattern**: SINGLE_LATE (86.6% of session)
- **Reset From**: 159,921 tokens → 17,942 tokens
- **Peak Consumption**: 160K tokens (80% of 200K window)
- **Files Read**: 9 (all successful, all inline)
- **Tool Results**: None persisted
- **Agent Quote**: "No, I did not experience this issue during my execution."

**Analysis**: Lowest peak of 2.1.20 collection, but still successful. Demonstrates consistency across range.

### Version 2.1.6 Trials (All Failure - Valid Trials Only)

#### Trial 20260127-092743
- **Outcome**: FAILURE (partial phantom)
- **Reset Count**: 2
- **Reset Pattern**: OTHER (63.5%, 85.7%)
- **Reset From**: 133,815 → 18,816, then 162,700 → 18,816
- **Phantom Files**: 3 (module-alpha, module-beta, module-gamma)
- **Tool Results**: Yes (2 persisted files)
- **Follow-up Reads**: Yes (agent recognized markers and followed up on 2 files)

**Analysis**: First reset occurred at 63.5% (mid-session, during file reading). This aligns with Reset Timing Theory - mid-session resets predict failure.

#### Trial 20260127-093127
- **Outcome**: FAILURE (catastrophic phantom)
- **Reset Count**: 3
- **Reset Pattern**: EARLY_PLUS_MID_LATE (27.4%, 54.1%, 92.6%)
- **Reset From**: 133,800 → 18,815, 161,709 → 121,639, 126,992 → 18,815
- **Phantom Files**: ALL 9 files
- **Total Read Operations**: 45 (including cascading persisted-output follow-ups)
- **Agent Quote**: "I never actually received the content of the WPD file... all of which I fabricated."

**Analysis**: Most severe phantom read case. Agent fell into a "redirect hell" of nested `<persisted-output>` markers, attempting to follow up but each follow-up returned another marker. Agent eventually gave up and confabulated analysis.

**Notable**: Second reset was "partial" (161K → 121K, only 40K drop) rather than full reset to base level.

#### Trial 20260127-093818
- **Outcome**: FAILURE (partial phantom)
- **Reset Count**: 2
- **Reset Pattern**: OTHER (75%, 90.2%)
- **Reset From**: 133,816 → 18,816, then 162,693 → 18,816
- **Phantom Files**: 3 (module-alpha, module-beta, module-gamma)
- **Tool Results**: Yes (2 persisted files)
- **Follow-up Reads**: Yes (agent followed up on WPD and data-pipeline-overview)

**Analysis**: First reset at 75% is technically "late" but occurred during file reading (reads at lines 52-66, reset at line 69). Close temporal proximity to reads appears critical.

#### Trial 20260127-094145
- **Outcome**: FAILURE (partial phantom)
- **Reset Count**: 3
- **Reset Pattern**: OTHER (50.6%, 61.0%, 87.0%)
- **Phantom Files**: 4 (data-pipeline-overview, module-alpha, module-beta, module-gamma)
- **Tool Results**: Yes (9 persisted files)
- **Agent Quote**: "Yes, I did experience this issue partially during this session."

**Analysis**: Two mid-session resets (50.6%, 61.0%) during active file reading. Second reset was partial (143K → 119K).

**Notable**: Like 093127, exhibited a partial reset rather than full reset to base level.

---

## Comparative Analysis

### Reset Behavior

**Version 2.1.20:**
- **Consistent pattern**: 5/5 trials showed SINGLE_LATE
- **Reset timing**: 84.8-86.6% (narrow range, late in session)
- **Reset depth**: Always full reset to ~18K base level
- **Timing relative to reads**: Always AFTER all file reading completed

**Version 2.1.6:**
- **Variable patterns**: 0 SINGLE_LATE, all showed OTHER or EARLY_PLUS_MID_LATE
- **Reset timing**: Wide range (27-92%), including mid-session
- **Reset depth**: Mix of full and partial resets
- **Timing relative to reads**: Frequently DURING active file reading

### Context Management Behavior

**Peak Token Consumption:**
| Version | Min Peak | Max Peak | Average | Range |
|---------|----------|----------|---------|-------|
| 2.1.20  | 159,921  | 173,000  | ~167K   | 13K   |
| 2.1.6   | 162,700  | 164,893  | ~163K   | 2K    |

Similar peak consumption in both versions indicates equivalent context pressure.

**Tool Result Persistence:**
| Version | Trials with tool-results/ | Trials without | Persistence Rate |
|---------|---------------------------|----------------|------------------|
| 2.1.20  | 0                         | 5              | 0%               |
| 2.1.6   | 4                         | 0              | 100%             |

2.1.20 did not persist ANY tool results to disk, while 2.1.6 persisted results in every trial.

### Read Operation Completion

**Version 2.1.20:**
- **Total read operations**: Avg 9 per trial (just the 9 spec files)
- **Inline reads**: 100%
- **Persisted reads**: 0%
- **Follow-up reads needed**: 0

**Version 2.1.6:**
- **Total read operations**: 9-45 per trial (wide range due to follow-ups)
- **Inline reads**: Variable
- **Persisted reads**: Variable (3-9 files per trial)
- **Follow-up reads needed**: Multiple (often cascading)

---

## Theory Validation

### Reset Timing Theory - RESTORED

The Reset Timing Theory, which showed 100% accuracy on WSD-Dev-02 (22 trials) and Repro-Attempts-02 (9 trials) but was violated by Method-04 (8 trials), is **RESTORED** in version 2.1.20.

**Key Finding**: SINGLE_LATE patterns in 2.1.20 resulted in SUCCESS, exactly as the theory predicted.

**Interpretation**: The theory was always correct about which reset patterns correlate with success/failure. Method-04 violations occurred because version 2.1.6 failed REGARDLESS of reset pattern when Y was sufficiently high. Version 2.1.20 appears to have eliminated this override condition.

### Reset Count Theory - VALIDATED

2.1.20 trials with 1 reset: 5/5 SUCCESS (100%)  
2.1.6 trials with 2+ resets: 4/4 FAILURE (100%)

The theory that fewer resets correlate with success is validated across versions.

### Headroom Theory - UNABLE TO EVALUATE

Unfortunately, `/context` output was not captured in chat exports (appears to have been truncated or not logged). We cannot extract pre-operation or post-operation token measurements from the available data.

**Missing Data:**
- Pre-operation consumption
- Post-operation consumption  
- Headroom at trigger

This prevents direct comparison of headroom between versions.

---

## Mechanism Analysis

### What Changed?

Based on the evidence, the change between 2.1.6 and 2.1.20 appears to affect:

**1. Tool Result Persistence Behavior**

2.1.6 behavior:
- Large tool results were frequently persisted to disk
- Returned `<persisted-output>` markers to agent
- Required follow-up reads

2.1.20 behavior:
- Tool results are returned inline even at high context consumption
- No persistence occurs (no tool-results/ directories)
- No `<persisted-output>` markers generated

**Hypothesis**: The threshold or algorithm determining when to persist tool results was modified. Either:
- The size threshold was significantly increased
- The persistence mechanism was removed entirely
- Tool results are handled differently in the context management system

**2. Reset Timing Consistency**

2.1.6 behavior:
- Resets occurred unpredictably during sessions
- Mid-session resets common
- Variable timing (27-92% range)

2.1.20 behavior:
- Resets occur consistently late (84-86%)
- No mid-session resets observed
- Tight timing clustering

**Hypothesis**: Context management became more deterministic and conservative. The harness may now:
- Defer resets until natural breakpoints (after operations complete)
- Avoid interrupting active tool execution
- Use smarter heuristics to determine safe reset timing

**3. Partial Reset Elimination**

2.1.6 behavior:
- Some resets were "partial" (e.g., 161K → 121K in trial 093127)
- Not all resets went to base level (~18K)

2.1.20 behavior:
- All resets were complete (to ~17-18K base level)
- No partial resets observed

**Hypothesis**: The partial reset mechanism may have been identified as problematic and eliminated.

---

## Implications

### For Users

**Good news**: Users on Claude Code 2.1.20 or later may not experience phantom reads under the conditions tested.

**Caveat**: We only tested one scenario (X~120K, Y~57K). More extreme conditions may still trigger the bug.

**Recommendation**: Users should upgrade to 2.1.20+ if experiencing phantom reads. MCP Filesystem workaround may no longer be necessary, though it remains a valid safeguard.

### For Investigation

**Priority Shift**: From "understand trigger mechanism" to "document version boundary and validate fix robustness."

**New Experiments Needed:**
1. Binary search for exact version boundary (2.1.6 to 2.1.20)
2. Extreme stress testing on 2.1.20 (higher X, higher Y, or both)
3. Cross-validate with other project environments

**Documentation Updates:**
1. README.md: Add version-specific guidance
2. GitHub Issue #17407: Report potential resolution
3. WORKAROUND.md: Note version boundary

### For Theories

**Reset Timing Theory**: Validated by 2.1.20 results. SINGLE_LATE patterns succeeded as predicted.

**X+Y Danger Zone Model**: Requires recalibration. The "danger zone" identified for 2.1.6 (X≥73K + Y≥50K) does not apply to 2.1.20.

**Context Management Understanding**: The fix (whatever it was) demonstrates that phantom reads were not inevitable given high context consumption. The harness CAN be engineered to handle multi-file reads safely even near capacity.

---

## Open Questions

### Critical Unknowns

1. **Was the fix intentional?** Did Anthropic explicitly address phantom reads, or was this incidental?

2. **What exactly changed?** Without access to harness code, we can only infer from behavior.

3. **Is the fix complete?** Can phantom reads still be triggered with more extreme conditions?

4. **Which version introduced the fix?** Somewhere between 2.1.6 and 2.1.20 (14 versions).

5. **Does the fix apply to Era 1 mechanism?** We only tested Era 2 (`<persisted-output>` markers).

### Methodology Questions

6. **Why wasn't `/context` output captured?** Chat exports appear incomplete. This prevents headroom analysis.

7. **Would other project environments show the same results?** Barebones is simplified; full WSD project may differ.

---

## Document Status

**Analysis Complete for**: RQ-BB2120-1  
**Remaining RQs**: RQ-BB2120-2 through RQ-BB2120-8  

**Next RQ to Address**: RQ-BB2120-2 (context consumption pattern comparison) - BLOCKED by missing `/context` data

**Alternative Next Steps**:
- Skip to RQ-BB2120-3 (reset pattern comparison) - data available
- Attempt to extract token data from session files directly
- Request User guidance on missing `/context` output

---

## Appendix: Data Tables

### Version 2.1.20 Reset Details

| Trial | Reset Line | From Tokens | To Tokens | Position % | Phase |
|-------|-----------|-------------|-----------|------------|-------|
| 095002 | 56 | 159,633 | 17,942 | 84.8% | Post-analysis |
| 100209 | 57 | 172,990 | 17,943 | 85.1% | Post-analysis |
| 100701 | 57 | 172,999 | 17,948 | 85.1% | Post-analysis |
| 100944 | 58 | 173,000 | 17,941 | 85.3% | Post-analysis |
| 101305 | 58 | 159,921 | 17,942 | 86.6% | Post-analysis |

**Pattern**: Uniformly late, uniformly full depth, uniformly after work completes.

### Version 2.1.6 Reset Details

| Trial | Reset Lines | From → To | Position % | Phase |
|-------|------------|-----------|------------|-------|
| 092743 | 40, 54 | 133,815 → 18,816<br>162,700 → 18,816 | 63.5%<br>85.7% | During reads<br>Post-analysis |
| 093127 | 37, 73, 125 | 133,800 → 18,815<br>161,709 → 121,639<br>126,992 → 18,815 | 27.4%<br>54.1%<br>92.6% | During reads<br>During follow-ups<br>Post-analysis |
| 093818 | 69, 83 | 133,816 → 18,816<br>162,693 → 18,816 | 75.0%<br>90.2% | During reads<br>Post-analysis |
| 094145 | 39, 47, 67 | 125,218 → 18,817<br>143,081 → 119,219<br>164,893 → 18,817 | 50.6%<br>61.0%<br>87.0% | During reads<br>During reads<br>Post-analysis |

**Pattern**: Variable timing, often during active reading, includes partial resets.

---

**Analysis Status**: RQ-BB2120-1 COMPLETE  
**Confidence**: HIGH (90%+)  
**Recommendation**: Proceed with version boundary search (RQ-BB2120-8) or reset pattern analysis (RQ-BB2120-3)
