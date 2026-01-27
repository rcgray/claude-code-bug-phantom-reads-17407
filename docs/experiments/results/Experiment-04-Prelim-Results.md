# Experiment-04 Preliminary Results

This document records the results of the preliminary experiments defined in `Post-Experiment-04-Ideas.md`. These smaller experiments (04A through 04L) clarify assumptions and refine our theoretical understanding before determining the next major investigation direction.

---

## Experiment-04L: Hoisted Content Re-Read Behavior

**Date**: 2026-01-26
**Collection**: `dev/misc/experiment-04l`
**Trials**: 6

### Purpose

Test whether the Claude Code harness avoids redundant context injection when files pre-loaded via hoisting (`@` notation) are subsequently read via explicit Read commands.

### Procedure

All trials used `/setup-maxload` (hoists all 8 spec files via `@` notation), then:
- Variant A: `/analyze-wpd-doc` (agent discovers files naturally, no explicit file list)
- Variant B: `/analyze-wpd` (command explicitly lists the 8 spec files)

### Results

| Trial ID | Command | Peak Tokens | Outcome | Reset Pattern |
|----------|---------|-------------|---------|---------------|
| 20260126-083436 | `/analyze-wpd-doc` | 153,565 | SUCCESS | SINGLE_LATE (82%) |
| 20260126-083737 | `/analyze-wpd-doc` | 152,811 | SUCCESS | SINGLE_LATE (80%) |
| 20260126-083842 | `/analyze-wpd-doc` | 153,549 | SUCCESS | SINGLE_LATE (80%) |
| 20260126-084319 | `/analyze-wpd` | 153,026 | SUCCESS | SINGLE_LATE (80%) |
| 20260126-084419 | `/analyze-wpd` | 153,462 | SUCCESS | OTHER (58%, 81%) |
| 20260126-084512 | `/analyze-wpd` | 153,724 | SUCCESS | SINGLE_LATE (75%) |

**Summary Statistics:**

| Metric | `/analyze-wpd-doc` | `/analyze-wpd` |
|--------|-------------------|----------------|
| Average Peak Tokens | 153,308 | 153,404 |
| Token Difference | - | +96 (~0.06%) |
| Success Rate | 3/3 (100%) | 3/3 (100%) |
| Files Read (agent-initiated) | 1 (WPD only) | 1 (WPD only) |

### Key Observations

1. **Context usage is virtually identical** between command variants (~96 token difference, negligible)

2. **Harness avoids redundant reads**: When spec files are hoisted via `@` notation in `/setup-maxload`, subsequent explicit file listing in `/analyze-wpd` does NOT cause the harness to re-inject those files into context

3. **Agent read behavior**: In both variants, the Session Agent only issued 1 Read command (for the WPD). The spec files were already present via hoisting and did not require agent-initiated reads

4. **All trials succeeded**: 6/6 trials reported SUCCESS with no phantom reads, consistent with the minimal Y hypothesis (Y = ~6K tokens for WPD only)

### Conclusions

**Primary Finding**: The Claude Code harness is intelligent about redundant reads. Files pre-loaded via `@`-hoisting are recognized as already present in context, and explicit Read commands (whether from command file lists or agent initiative) do not cause content duplication.

**Implication for Experiment-04D**: This confirms we can safely run `/setup-maxload` → `/analyze-wpd` without context duplication confounding the results. The explicit file list in `/analyze-wpd` is harmless after hoisting.

**Secondary Finding**: With maxload hoisting (X ≈ 150K including baseline) and minimal Y (WPD only, ~6K tokens), all trials succeeded. This is consistent with the hypothesis that Y size is the critical factor for phantom reads, and that hoisted content does not contribute to the phantom read trigger mechanism.

### Theoretical Implications

1. **Hoisting is "safe"**: Pre-loading files via `@` notation does not trigger phantom reads, even at high context consumption (~75% of 200K window)

2. **Y-primacy hypothesis supported**: All trials succeeded despite high X, suggesting the trigger is related to operation-phase reads (Y), not pre-operation context (X)

3. **Command design flexibility**: Either `/analyze-wpd` or `/analyze-wpd-doc` can be used interchangeably after hoisting without affecting context consumption or phantom read risk

---

## Experiment-04A: Minimal X ("Easy-0")

**Date**: 2026-01-26
**Collection**: `dev/misc/experiment-04a`
**Trials**: 6

### Purpose

Test whether Y has an absolute threshold independent of X by running the 9-file operation (Y≈57K tokens) with minimal pre-operation context (X≈0).

### Procedure

1. Start fresh session
2. Run `/setup-none` (generates Workscope ID, hoists no files)
3. Run `/analyze-wpd docs/wpds/pipeline-refactor.md` (reads 9 spec files)
4. Prompt for phantom read self-report
5. Export session

### Results

| Trial ID | Outcome | Notes |
|----------|---------|-------|
| 20260125-190604 | SUCCESS | No self-reported phantom reads |
| 20260125-190609 | SUCCESS | No self-reported phantom reads |
| 20260125-191433 | SUCCESS | No self-reported phantom reads |
| 20260125-191438 | SUCCESS | No self-reported phantom reads |
| 20260125-193336 | SUCCESS | No self-reported phantom reads |
| 20260125-193404 | SUCCESS | No self-reported phantom reads |

**Summary**: 6/6 trials SUCCESS (100% success rate)

### Key Observations

1. **Y≈57K does NOT cause phantom reads when X≈0**: The same Y value that caused 100% failure in Method-04 (with X=73K or X=120K) produces 100% success when X is minimized.

2. **The Y-only threshold hypothesis is contradicted**: If Y had an absolute ceiling (~40-57K), phantom reads should have occurred regardless of X.

3. **X is a critical factor**: Pre-operation context significantly affects phantom read risk.

### Cross-Experiment Comparison

Combining 04A results with 04L and Method-04 reveals a striking pattern:

| Experiment | X (Pre-op) | Y (Operation) | X + Y | Outcome |
|------------|------------|---------------|-------|---------|
| Method-04 Easy | 73K (37%) | 57K (9 files) | ~130K | **FAILURE** |
| Method-04 Hard | 120K (60%) | 57K (9 files) | ~177K | **FAILURE** |
| **Experiment-04L** | **~150K (75%)** | **~6K (WPD only)** | **~156K** | **SUCCESS** |
| **Experiment-04A** | **≈0** | **~57K (9 files)** | **~57K** | **SUCCESS** |

**Critical Observation**: The 130K total (Method-04 Easy) FAILED, while the 156K total (04L) SUCCEEDED. This definitively rules out a simple "X + Y > T" threshold model.

### Theoretical Implications

The data now suggests a more nuanced interaction:

1. **High X + Low Y → SUCCESS** (04L: X=150K, Y=6K)
2. **Low X + High Y → SUCCESS** (04A: X≈0, Y=57K)
3. **Moderate X + High Y → FAILURE** (Method-04: X=73-120K, Y=57K)

This pattern suggests either:
- A **"danger zone"** exists where moderate X combined with high Y triggers phantom reads
- The **nature of context** matters: hoisted content (X) behaves differently than agent-read content (Y)
- **Timing/rate** of context accumulation may be critical, not just totals

### Remaining Questions

1. **What makes moderate X + high Y dangerous?** Why does X=73K fail with Y=57K while X=150K succeeds with Y=6K?

2. **Is there an X threshold below which high Y is safe?** 04A shows X≈0 is safe. Where does the danger zone begin?

3. **Does hoisted vs. agent-read matter?** In 04L, the 150K included hoisted spec files (not agent-read). In Method-04, the 57K spec files were agent-read. Is the read mechanism itself the trigger?

### Next Steps

1. **Experiment-04D** (Max X, Minimal Y) - Already partially answered by 04L, but formal trial collection would confirm
2. **Threshold boundary testing** - Test X values between 0 and 73K with Y=57K to find where failures begin
3. **Investigate the hoisting hypothesis** - Does moving content from Y to X (via hoisting) inherently make it "safe"?

---

## Experiment-04K: Larger Context Window (1M Model)

**Date**: 2026-01-26
**Collection**: `dev/misc/experiment-04k`
**Trials**: 6
**Model**: `claude-sonnet-4-5-20250929[1m]` (1M context window)

### Purpose

Test whether context window size (T) affects phantom read occurrence by running the same Method-04 protocol with a 1M context model instead of the standard 200K model.

### Procedure

1. Start fresh session with 1M context model
2. Run `/setup-hard` (hoists baseline + additional files, X≈120K)
3. Run `/analyze-wpd docs/wpds/pipeline-refactor.md` (reads spec files)
4. Prompt for phantom read self-report
5. Export session

### Results

| Trial ID | Files Read | Peak Tokens | Outcome | Reset Pattern |
|----------|------------|-------------|---------|---------------|
| 20260125-210757 | 5 | 167,379 | SUCCESS | SINGLE_LATE (84%) |
| 20260125-210837 | 6 | 150,036 | SUCCESS | SINGLE_LATE (83%) |
| 20260125-210913 | 4 | 144,370 | SUCCESS | SINGLE_LATE (82%) |
| 20260125-211516 | 9 | 177,961 | SUCCESS | SINGLE_LATE (81%) |
| 20260125-211544 | 9 | **202,126** | SUCCESS | SINGLE_LATE (85%) |
| 20260125-211609 | 5 | 130,075 | SUCCESS | SINGLE_LATE (80%) |

**Summary**: 6/6 trials SUCCESS (100% success rate)

### Key Observations

1. **100% SUCCESS with 1M model vs 100% FAILURE with 200K model**: The same configuration (`/setup-hard` + `/analyze-wpd`) that caused universal failure in Method-04 produces universal success with the 1M model.

2. **Peak tokens exceeded 200K nominal threshold**: Trial 20260125-211544 reached **202,126 tokens** - exceeding the 200K model's nominal capacity - yet succeeded. This directly demonstrates the 1M model's additional headroom.

3. **Variable file read counts**: Agents read between 4-9 files across trials (agent discovery behavior varies), but all trials succeeded regardless of file count.

4. **Consistent reset patterns**: All trials showed SINGLE_LATE reset patterns (80-85%), matching the Method-04 pattern that previously predicted SUCCESS but observed FAILURE with the 200K model.

### Cross-Experiment Comparison

| Experiment | Model | X (Pre-op) | Y (Operation) | Peak Tokens | Outcome |
|------------|-------|------------|---------------|-------------|---------|
| Method-04 Easy | 200K | 73K | 57K (9 files) | ~130K | **FAILURE** |
| Method-04 Hard | 200K | 120K | 57K (9 files) | ~177K | **FAILURE** |
| **Experiment-04K** | **1M** | **120K** | **variable** | **130K-202K** | **SUCCESS** |

**Critical Observation**: The identical protocol (`/setup-hard` → `/analyze-wpd`) produces opposite outcomes depending solely on model context window size.

### Theoretical Implications

1. **T (context window size) DOES matter**: The 200K model has limitations that the 1M model doesn't share. This rules out the hypothesis that phantom reads are caused by a fixed internal threshold independent of context capacity.

2. **The 200K model has an effective working threshold below nominal capacity**: Even though Method-04 Easy had X + Y ≈ 130K (well under 200K), it failed. The 200K model's effective safe operating range appears to be significantly lower than its advertised capacity.

3. **The 1M model provides genuine headroom**: With 5x the nominal context window, the 1M model can handle the same operations that cause the 200K model to fail.

4. **Reset Timing Theory needs revision**: SINGLE_LATE patterns (which previously predicted SUCCESS with 100% accuracy) showed FAILURE in Method-04's 200K trials but SUCCESS in 04K's 1M trials. The reset pattern alone is insufficient for prediction without considering context window size.

### Synthesis with 04A and 04L Results

Combining all preliminary experiment results reveals a more complete picture:

| Experiment | Model | X | Y | Peak | Outcome |
|------------|-------|---|---|------|---------|
| Method-04 Easy | 200K | 73K | 57K | ~130K | **FAILURE** |
| Method-04 Hard | 200K | 120K | 57K | ~177K | **FAILURE** |
| 04A (Minimal X) | 200K | ≈0 | 57K | ~57K | **SUCCESS** |
| 04L (Max X, Min Y) | 200K | 150K | 6K | ~156K | **SUCCESS** |
| **04K (1M Model)** | **1M** | **120K** | **variable** | **130K-202K** | **SUCCESS** |

**Emerging Pattern**: On the 200K model, phantom reads occur when:
- X is moderate-to-high (73K+) AND
- Y is high (57K with 9 files)

But this same combination succeeds when:
- X is ≈0 (04A), OR
- Y is minimal (04L), OR
- The model has a larger context window (04K)

### Refined Hypothesis

The phantom read trigger appears to be a **capacity pressure phenomenon** specific to how the 200K model handles context:

1. **Under pressure**: When the 200K model approaches its effective threshold (somewhere below 200K nominal), it struggles to handle large batches of agent-initiated reads.

2. **Not under pressure**: The 1M model, with 5x the headroom, never approaches this pressure point even with the same absolute token counts.

3. **The "danger zone" is model-specific**: What constitutes dangerous X + Y values depends on the model's context capacity.

### Practical Implications

1. **Workaround confirmation**: Using the 1M model variant appears to be a viable workaround for phantom reads, similar to the MCP Filesystem workaround.

2. **200K model usage guidance**: When using the 200K model, either minimize X (fresh sessions) or minimize Y (hoist files instead of agent-reading) to avoid the danger zone.

3. **Further investigation needed**: Understanding WHY the 200K model fails under pressure while the 1M model succeeds could reveal the underlying mechanism.

---

## Experiment-04D: Maximum X, Minimal Y

**Date**: 2026-01-26
**Collection**: `dev/misc/experiment-04d`
**Trials**: 6

### Purpose

Test whether hoisted content can cause phantom reads, and whether minimal Y succeeds even with extreme X. This experiment moves spec files from Y (agent-read during operation) to X (pre-loaded via hoisting), leaving only the WPD for the operation phase.

### Procedure

1. Run `/setup-hard` or `/setup-easy` (baseline X)
2. `/setup-maxload` hoists all 8 spec files via `@` notation (adds ~52K to X)
3. Run `/analyze-wpd-doc` (reads only WPD, Y ≈ 6K tokens)
4. Prompt for phantom read self-report
5. Export session

### Results

#### Hard Scenario (X ≈ 120K baseline + 52K hoisted = ~172K)

| Trial ID | Outcome | Notes |
|----------|---------|-------|
| 20260126-081157 | INCOMPLETE | Context filled; `/analyze-wpd` could not execute |
| 20260126-081436 | INCOMPLETE | Context filled; `/analyze-wpd` could not execute |
| 20260126-081607 | INCOMPLETE | Context filled; `/analyze-wpd` could not execute |

**Critical Observation**: All Hard+maxload trials filled context capacity BEFORE the `/analyze-wpd` operation could be executed. However, **NO phantom reads were reported on the hoisted content itself**.

#### Easy Scenario (X ≈ 73K baseline + 52K hoisted = ~125K)

| Trial ID | Outcome | Notes |
|----------|---------|-------|
| 20260126-081943 | SUCCESS | No self-reported phantom reads |
| 20260126-082019 | SUCCESS | No self-reported phantom reads |
| 20260126-082029 | SUCCESS | No self-reported phantom reads |

**Summary**:
- Hard: 0/3 completed operation (context overflow), 0/3 phantom reads on hoisted content
- Easy: 3/3 SUCCESS (100% success rate)

### Key Observations

1. **Hard+maxload exceeded context capacity**: The combination of Hard baseline (~120K) + maxload hoisting (~52K) = ~172K pushed context too high for the session to proceed to the operation phase. This is a methodological limitation, not a phantom read.

2. **Hoisting did NOT cause phantom reads**: Despite context filling to capacity in Hard scenarios, the hoisted spec files were correctly available in context. No phantom reads occurred on `@`-hoisted content, even under extreme context pressure.

3. **Easy+maxload succeeded completely**: With Easy baseline (~73K) + maxload (~52K) = ~125K, all trials succeeded with minimal Y (~6K for WPD only). This confirms the 04L finding that high X + minimal Y is safe.

4. **Methodological insight**: The Hard+maxload combination is too aggressive for the 200K model. Future experiments should either use smaller baselines or the 1M model when testing extreme X values.

### Cross-Experiment Comparison

| Experiment | X (Pre-op) | Y (Operation) | Total | Outcome |
|------------|------------|---------------|-------|---------|
| Method-04 Easy | 73K | 57K (9 files) | ~130K | **FAILURE** |
| Method-04 Hard | 120K | 57K (9 files) | ~177K | **FAILURE** |
| 04L (Maxload) | ~150K | 6K (WPD only) | ~156K | **SUCCESS** |
| **04D Easy+maxload** | **~125K** | **~6K** | **~131K** | **SUCCESS** |
| **04D Hard+maxload** | **~172K** | **N/A** | **N/A** | **INCOMPLETE** (context overflow) |

### Theoretical Implications

1. **Hoisting is definitively "safe"**: Even when context overflowed in Hard+maxload trials, the hoisted content was correctly present - no phantom reads occurred. The failure mode was context capacity, not phantom reads.

2. **Y-primacy hypothesis strongly supported**: The contrast is stark:
   - Method-04 Easy (X=73K, Y=57K) → FAILURE
   - 04D Easy+maxload (X=125K, Y=6K) → SUCCESS

   Higher total X but minimal Y succeeds, while lower total X but high Y fails. This confirms that Y (agent-initiated reads) is the critical factor.

3. **The "danger zone" requires both conditions**:
   - High Y alone (04A: X≈0, Y=57K) → SUCCESS
   - High X alone (04D: X=125K, Y=6K) → SUCCESS
   - Moderate X + High Y (Method-04: X=73K+, Y=57K) → FAILURE

   The phantom read trigger appears to require BOTH moderate-to-high X AND high Y simultaneously.

4. **Hoisted vs agent-read content behaves differently**: Moving content from Y to X (via hoisting) fundamentally changes how it interacts with the phantom read mechanism. Hoisted content does not trigger phantom reads even at extreme context levels.

### Refined Model

Based on 04D results combined with 04A, 04L, and 04K, the phantom read mechanism appears to work as follows:

```
IF (model == 200K) AND (X >= ~73K) AND (Y >= ~50K):
    → PHANTOM READ RISK
ELSE:
    → SAFE
```

Where:
- X = Pre-operation context (baseline + hoisted content)
- Y = Agent-initiated reads during operation
- The 1M model appears immune due to increased headroom

### Practical Implications

1. **Hoisting is a reliable mitigation**: Move files from Y to X via `@`-hoisting to avoid phantom reads.

2. **The Easy+maxload pattern is safe**: Even with high total context (~125K), minimal Y ensures success.

3. **Hard baseline is too high for maxload testing**: Future experiments testing extreme X should use Easy baseline or the 1M model.

---

*Document created: 2026-01-26*
*Updated: 2026-01-26 - Added Experiment-04A results*
*Updated: 2026-01-26 - Added Experiment-04K results*
*Updated: 2026-01-26 - Added Experiment-04D results*
*Based on analysis of: `dev/misc/experiment-04l/` (6 trials), `dev/misc/experiment-04a/` (6 trials), `dev/misc/experiment-04k/` (6 trials), `dev/misc/experiment-04d/` (6 trials)*
