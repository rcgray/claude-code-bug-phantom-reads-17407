# Research Questions Catalog

This document catalogs all research questions (RQs) identified during the Phantom Reads investigation. Questions are numbered for reference and organized by category. Each question includes its current status, relevant evidence, and links to experiments designed to answer it.

**Purpose**: Provide a central reference for tracking what we know, what we suspect, and what remains uncertain about Claude Code's file read behavior.

**Naming Convention**: Questions are numbered `RQ-#` sequentially within categories.

---

## Category A: Core Mechanism

Questions about the fundamental mechanism that causes phantom reads.

### RQ-A1: What internally triggers a context reset?

**Status**: OPEN

**Background**: Context resets are observed via drops in `cache_read_input_tokens` between assistant messages. We observe resets at widely varying cumulative token counts (82K-383K), ruling out a simple fixed threshold.

**Sub-questions**:
- Is the trigger threshold-based?
- Is it rate-based (tokens per turn)?
- Is it time-based?
- Is it some combination of factors?

**Evidence**:
- Resets occur at 82K-383K cumulative tokens (5x variation)
- No fixed threshold identified despite 31+ trials
- Dynamic Context Pressure hypothesis suggests rate matters

**Related Experiments**: None directly; would require harness instrumentation

---

### RQ-A2: What determines which specific reads become phantom reads?

**Status**: PARTIALLY ANSWERED

**Background**: Within a session experiencing phantom reads, some reads succeed while others fail. What determines which reads are affected?

**Current Understanding**:
- Position in read sequence appears relevant
- File size at reset point does NOT predict outcome
- Reads issued during or immediately after a context reset are vulnerable

**Evidence**:
- Analysis shows resets occur after both small (<1K) and large (>10K) files
- Earlier reads in a batch operation are more likely to be cleared

**Related Experiments**: 04J (examine persisted files)

---

### RQ-A3: Why does the session `.jsonl` file record actual content while the agent receives phantom read markers?

**Status**: HYPOTHESIS FORMED

**Background**: Session files contain complete file content in `tool_result` entries, but agents report seeing `[Old tool result content cleared]` or `<persisted-output>` markers.

**Hypothesis**: The session file logs tool execution results, but a separate context management system transforms content before it reaches the model. This transformation happens AFTER session logging but BEFORE model context injection.

**Evidence**:
- Phantom read markers appear NOWHERE in session files except in conversation text where agents discuss them
- 2.0.58-bad session shows full content logged but agent confirms seeing cleared markers

**Related Experiments**: 04J (examine persisted output files)

---

### RQ-A4: What changed between versions 2.0.59 and 2.0.60?

**Status**: OPEN

**Background**: Era 1 (≤2.0.59) uses `[Old tool result content cleared]` mechanism; Era 2 (≥2.0.60) uses `<persisted-output>` mechanism. This suggests a fundamental change in how large results are handled.

**Evidence**:
- Both eras exhibit phantom reads, just with different markers
- The persisted-output mechanism writes to disk and expects follow-up reads
- The older mechanism appears to clear content from context directly

**Related Experiments**: Cross-version testing (not yet designed)

---

### RQ-A5: Why does the phantom read mechanism only affect agent-initiated reads and not hoisted content?

**Status**: NEW - OPEN

**Background**: Experiments 04D and 04L demonstrated that hoisted content (`@`-notation) never triggers phantom reads, even under extreme context pressure (~172K tokens). Agent-initiated reads via the Read tool are vulnerable.

**Evidence**:
- 04D Hard+maxload: Context filled to capacity, but NO phantom reads on hoisted content
- 04L: 150K hoisted tokens + 6K agent-read = SUCCESS
- Method-04: 73K hoisted + 57K agent-read = FAILURE

**Hypotheses**:
- Hoisting injects content before the agent runs, making it "baked in" to the initial context
- Hoisting uses a different code path that bypasses context management
- Agent-initiated reads go through a layer that applies context pressure rules

**Related Experiments**: 04D (completed), 04I (Partial MCP Hybrid)

---

## Category B: Threshold Behavior

Questions about the thresholds and limits that govern phantom read occurrence.

### RQ-B1: Is there an absolute Y threshold independent of X?

**Status**: ~~STRONG HYPOTHESIS~~ → **ANSWERED: NO**

**Background**: Y (operation context) was hypothesized to have a ceiling (~40-57K tokens) beyond which phantom reads occur regardless of X (pre-operation context).

**Answer**: The Y threshold is NOT independent of X. Experiment-04A demonstrated that Y=57K succeeds when X≈0.

**Evidence**:
- Method-04 (X=73K+, Y=57K): 100% FAILURE
- **Experiment-04A (X≈0, Y=57K): 100% SUCCESS (6/6 trials)**
- The same Y value produces opposite outcomes depending on X

**Conclusion**: There is no absolute Y ceiling. X and Y interact to determine phantom read risk.

**Related Experiments**: 04A (completed), 04D (completed)

---

### RQ-B2: Where exactly is the Y threshold?

**Status**: REFRAMED

**Background**: Originally asked where the absolute Y threshold lies (42K-57K range).

**Reframing**: Given RQ-B1's answer (no absolute Y threshold), this question is now conditional: *At what X values does a given Y become dangerous?*

**Current Data Points**:
- X≈0, Y=57K → SUCCESS (04A)
- X=73K, Y=57K → FAILURE (Method-04)
- X=125K, Y=6K → SUCCESS (04D)
- X=150K, Y=6K → SUCCESS (04L)

**Remaining Question**: What is the X threshold above which Y=57K becomes dangerous? Somewhere between 0 and 73K.

**Related Experiments**: 04B (8-File Threshold) - may need redesign given new understanding

---

### RQ-B3: Is the trigger file count or total token count?

**Status**: OPEN

**Background**: Method-03 used 7 files (42K tokens); Method-04 used 9 files (57K tokens). We don't know if the trigger is the NUMBER of files or the TOTAL tokens.

**Test Approach**: Use fewer, larger files (e.g., 4 mega-spec files totaling 57K tokens)
- If SUCCESS: File count is the trigger
- If FAILURE: Token count (or both) is the trigger

**Related Experiments**: 04F (File Count vs Tokens)

---

### RQ-B4: Does X contribute to phantom read risk at all?

**Status**: ~~WEAKENED~~ → **ANSWERED: YES**

**Background**: Originally weakened by Method-04 showing identical failure rates across Easy (X=73K) and Hard (X=120K) scenarios.

**Answer**: X is a CRITICAL factor. Experiment-04A proved this definitively.

**Evidence**:
- **04A: X≈0 + Y=57K → SUCCESS** (6/6 trials)
- Method-04: X=73K+ + Y=57K → FAILURE (8/8 trials)
- The ONLY difference was X; Y was identical

**Conclusion**: X significantly affects phantom read risk. Low X can make high Y safe; moderate-to-high X makes high Y dangerous.

**Related Experiments**: 04A (completed), 04D (completed)

---

### RQ-B5: Does T (context window size) actually matter?

**Status**: ~~OPEN~~ → **ANSWERED: YES**

**Background**: We assumed T≈200K based on the standard context window. But phantom reads occur well below this limit. Is T relevant at all?

**Answer**: T DOES matter. The 1M model avoids phantom reads that the 200K model experiences.

**Evidence**:
- **04K: 1M model, same protocol as Method-04 → 100% SUCCESS (6/6 trials)**
- Method-04: 200K model → 100% FAILURE (8/8 trials)
- 04K trial 20260125-211544 reached 202K tokens and still SUCCEEDED
- Same reset patterns (SINGLE_LATE) produced opposite outcomes depending on model

**Conclusion**: The 200K model has limitations that the 1M model doesn't share. Context window size directly affects phantom read susceptibility.

**Related Experiments**: 04K (completed)

---

### RQ-B6: What is the hoisting token limit?

**Status**: CONFIRMED (~25K)

**Background**: Files hoisted via `@` notation that exceed ~25K tokens are silently ignored.

**Evidence**:
- Original `operations-manual.md` (~45K tokens) was completely skipped
- Splitting into two files (~20K each) succeeded
- Limit appears to be approximately 25K tokens per file

**Remaining Questions**:
- Is the limit exactly 25K or approximate?
- Does it vary by model or context?
- Is it per-file or cumulative?

**Related Experiments**: None planned; limit is established

---

### RQ-B7: What is the effective working threshold of the 200K model?

**Status**: NEW - OPEN

**Background**: The 200K model fails at token counts well below its nominal 200K capacity. What is the actual safe operating range?

**Evidence**:
- Method-04 Easy (X+Y ≈ 130K): FAILURE despite being 65% of nominal capacity
- 04L (peak 153K): SUCCESS with minimal Y
- 04K 1M model (peak 202K): SUCCESS

**Hypothesis**: The 200K model's effective threshold is significantly lower than 200K, possibly around 100-130K depending on X/Y composition.

**Related Experiments**: Future threshold boundary testing needed

---

### RQ-B8: How do X and Y interact to create phantom read conditions?

**Status**: OPEN - INTERACTION EFFECT CONFIRMED, MECHANISM UNCLEAR

**Background**: The pattern of successes and failures demonstrates that X and Y interact in a way that cannot be reduced to simple independent thresholds or a simple X+Y > T formula.

**Evidence Summary**:

| Condition | X | Y | X+Y | Outcome |
|-----------|---|---|-----|---------|
| High X only | 150K | 6K | 156K | **SUCCESS** (04L) |
| High Y only | ≈0 | 57K | ~57K | **SUCCESS** (04A) |
| Both moderate-high | 73K+ | 57K | 130K | **FAILURE** (Method-04 Easy) |
| High X, moderate Y | 120K | 42K | 162K | **SUCCESS** (Method-03 Hard) |
| Neither high | Low | Low | Low | **SUCCESS** (various) |

**Critical Observation**: Simple X+Y > T is **contradicted** by the evidence. Method-04 Easy fails at X+Y=130K while Method-03 Hard succeeds at X+Y=162K. The higher total succeeds; the lower total fails. This proves the interaction is more complex than additive.

**Current Understanding**: Phantom reads require BOTH X and Y to exceed some level simultaneously, but these are not independent "magic thresholds" to discover. The interaction appears to be:
- When Y is low (~42K, 7 files): Any X value tested succeeds
- When Y is high (~57K, 9 files): Low X (≈0) succeeds, moderate+ X (73K+) fails
- When X is high but Y is minimal: Succeeds regardless

**⚠️ Research Caution**: Do NOT frame future experiments as "finding the exact X threshold" or "finding the exact Y threshold" in isolation. The evidence shows these dimensions interact—varying X alone while holding Y constant (as in Easy vs Medium vs Hard scenarios) does not predict outcomes when Y is sufficiently high. The goal is to understand the X+Y interaction surface with respect to T, not to identify magic numbers.

**Open Sub-Questions**:
- Why does Y=57K fail with X=73K but succeed with X≈0?
- Is the Y threshold related to file count, token count, or both? (See 04F)
- What is the mechanism causing this interaction effect?

**Related Experiments**: 04F (file count vs tokens) may help isolate variables

---

## Category C: Hoisting Behavior

Questions about how `@`-hoisted content differs from agent-initiated reads.

### RQ-C1: Can hoisted content cause phantom reads?

**Status**: ~~HYPOTHESIS: NO~~ → **ANSWERED: NO**

**Background**: Hoisted files appear to use a different code path than agent-initiated reads.

**Answer**: Hoisting does NOT cause phantom reads, even under extreme context pressure.

**Evidence**:
- **04D Hard+maxload: Context filled to capacity (~172K), but NO phantom reads on hoisted content**
- 04L: 150K hoisted tokens successfully received
- All 04D Easy+maxload trials (X≈125K hoisted) succeeded with 100% rate

**Conclusion**: Hoisting is definitively "safe" - it does not trigger the phantom read mechanism regardless of how much content is hoisted (within the 25K per-file limit).

**Related Experiments**: 04D (completed), 04L (completed)

---

### RQ-C2: Does the harness avoid redundant reads for already-hoisted files?

**Status**: ~~OPEN~~ → **ANSWERED: YES**

**Background**: If a file is hoisted via `@` and then the agent issues a Read for the same file, does the harness re-inject the content?

**Answer**: YES, the harness is intelligent about redundant reads.

**Evidence**:
- **04L: `/analyze-wpd-doc` vs `/analyze-wpd` after hoisting showed only ~96 token difference (0.06%)**
- Agent only issued 1 Read command (for WPD) in both variants
- Hoisted spec files were recognized as already present

**Conclusion**: Explicit file listing in commands after hoisting does NOT cause context duplication. The harness recognizes content is already present.

**Related Experiments**: 04L (completed)

---

### RQ-C3: Why are hoisted files treated differently than agent-initiated reads?

**Status**: PARTIALLY ANSWERED

**Background**: Hoisted content is immune to phantom reads; agent-initiated reads are vulnerable.

**Current Understanding**:
- Hoisting happens before the agent runs, so content is "baked in" to initial context
- This content is not subject to the same context pressure management
- Agent-initiated reads go through a layer that CAN trigger phantom reads under pressure

**Remaining Question**: What specifically in the harness architecture causes this difference?

**Related Experiments**: 04D (completed), 04I (Partial MCP Hybrid)

---

### RQ-C4: Does moving content from Y to X (via hoisting) make it inherently safe?

**Status**: NEW - ANSWERED: YES

**Background**: Can we avoid phantom reads by hoisting files that would otherwise be agent-read?

**Answer**: YES. Moving content from Y (agent-read) to X (hoisted) eliminates phantom read risk for that content.

**Evidence**:
- **Method-04: Spec files as Y (agent-read) → FAILURE**
- **04D/04L: Same spec files as X (hoisted) → SUCCESS**
- The files are identical; only the loading mechanism differs

**Practical Implication**: Hoisting is a reliable mitigation strategy. Pre-load files via `@`-notation to avoid phantom reads.

**Related Experiments**: 04D (completed), 04L (completed)

---

## Category D: Reset Timing

Questions about the relationship between context resets and phantom reads.

### RQ-D1: Is reset timing causal or merely correlational?

**Status**: ~~UNCERTAIN~~ → **REFINED: CORRELATIONAL, MODEL-DEPENDENT**

**Background**: The Reset Timing Theory achieved 31/31 (100%) prediction accuracy on early trials.

**Refined Understanding**: Reset timing patterns alone are INSUFFICIENT for prediction. The model's context window capacity is a critical moderating variable.

**Evidence**:
- Method-04 (200K model): SINGLE_LATE patterns → FAILURE
- **04K (1M model): SINGLE_LATE patterns → SUCCESS**
- Same reset patterns, opposite outcomes based on model

**Conclusion**: Reset timing correlates with phantom reads but is not the causal mechanism. The underlying cause appears to be context pressure, which manifests differently depending on model capacity.

**Related Experiments**: 04K (completed)

---

### RQ-D2: Can intentional early resets create protected processing windows?

**Status**: OPEN

**Background**: The "Clean Gap" pattern observed in successful sessions suggests a post-reset window where operations can proceed safely.

**Hypothesis**: If we force an early reset (by pushing context high), the subsequent "clean" context could handle operations that would otherwise fail.

**Test Approach**: Push context to ~130K via hoisting/conversation, trigger reset, then run operation immediately after

**Related Experiments**: 04H (Intentional Early Reset), possibly covered by 04D results

---

### RQ-D3: Why did Reset Timing Theory predictions fail in Experiment-04?

**Status**: ~~OPEN~~ → **PARTIALLY ANSWERED**

**Background**: Previously 100% accurate theory (31 trials) showed systematic violations (8 trials) when Y increased from 42K to 57K.

**Partial Answer**: The theory was validated on conditions where the 200K model wasn't under extreme pressure. When Y pushed the model into the "danger zone," reset timing became irrelevant.

**Evidence**:
- **04K: 1M model with high Y still shows SINGLE_LATE → SUCCESS**
- The theory's violations correlate with model capacity, not Y per se

**Remaining Question**: Is the theory valid for ALL conditions on the 1M model, or does the danger zone shift with larger context windows?

**Related Experiments**: 04K (completed), further 1M model testing

---

## Category E: Read Patterns and Mitigation

Questions about how different read patterns affect phantom read risk.

### RQ-E1: Why does `grep` appear more reliable than `Read`?

**Status**: OPEN

**Background**: Agents report that grep results are received reliably even when Read results are phantom reads.

**Hypotheses**:
- Grep results are smaller (summary vs full content)
- Grep uses a different code path
- Grep results are not subject to the same context management

**Evidence**: Agent reports from 2026-01-12-13 investigation

**Related Experiments**: None planned

---

### RQ-E2: Does read pattern (sequential vs parallel) affect outcomes?

**Status**: OPEN

**Background**: Current agent behavior appears to issue parallel reads (multiple Read tool calls in single response). Would explicit sequential reads (one at a time with pauses) change outcomes?

**Test Approach**: Create command that forces sequential reads with user confirmation between each

**Challenges**: Controlling agent behavior is inherently difficult

**Related Experiments**: 04G (Sequential vs Parallel Reads)

---

### RQ-E3: Can batching Y into smaller operations mitigate phantom reads?

**Status**: PARTIALLY ANSWERED

**Background**: If Y has a per-operation threshold, splitting reads into smaller batches with processing pauses might avoid triggering phantom reads.

**Partial Answer**: Transferring files from Y to X (via hoisting) definitively works. Batching within agent-read Y is less clear.

**Evidence**: 04D/04L demonstrate that moving files to X (hoisted) eliminates risk. Whether batching agent reads achieves the same effect is untested.

**Related Experiments**: 04E (Batch Y), largely covered by 04D results

---

### RQ-E4: Is MCP immunity at the read level or operation level?

**Status**: OPEN

**Background**: MCP Filesystem achieves 100% success rate. But we don't know if MCP reads are immune within an operation that also uses native reads.

**Test Approach**: Use MCP for half the files, native Read for the other half, within the same operation

**Related Experiments**: 04I (Partial MCP Hybrid)

---

### RQ-E5: Can agent awareness enable reliable recovery from phantom reads?

**Status**: OBSERVED BUT NOT SYSTEMATIZED

**Background**: In repro-attempts-02, a failure was recovered when the agent recognized `<persisted-output>` markers and re-read files.

**Evidence**: Trial 20260121-202919 showed successful recovery

**Questions**:
- Can this be systematized as a mitigation strategy?
- Does recovery work consistently?
- What prevents agents from recognizing markers in the first place?

**Related Experiments**: None planned; would require behavior-level investigation

---

### RQ-E6: Is hoisting a reliable mitigation strategy for production use?

**Status**: NEW - STRONG HYPOTHESIS: YES

**Background**: Experiments demonstrate hoisting eliminates phantom read risk.

**Evidence**:
- 04D: 100% success with hoisted specs
- 04L: 100% success with hoisted specs
- No phantom reads observed on hoisted content in any experiment

**Practical Considerations**:
- Requires knowing files in advance (can't hoist dynamically discovered files)
- Subject to 25K per-file limit
- Works well for known specification/documentation sets

**Conclusion**: For workflows with predictable file sets, hoisting is a viable production mitigation alongside the MCP Filesystem workaround.

**Related Experiments**: 04D (completed), 04L (completed)

---

## Category F: Measurement and Accounting

Questions about how context is measured and reported.

### RQ-F1: Why is there a ~25K token accounting discrepancy?

**Status**: OPEN

**Background**: Files contribute measurable tokens but harness reports higher totals. Example: Files sum to 131K tokens but harness reports 156K total (~25K discrepancy).

**Hypotheses**:
- Thinking tokens (chain-of-thought overhead)
- System prompt overhead
- Message formatting overhead
- Tool call/result formatting

**Related Experiments**: None planned; would require detailed accounting

---

### RQ-F2: Why does the harness report "0% remaining" at 90% consumption?

**Status**: OPEN

**Background**: Harness reports "10% remaining" at 76% consumed and "0% remaining" at 90% consumed. This suggests either:
- The effective threshold is lower than 200K
- The harness reserves buffer space
- The reporting algorithm is different than we assume

**Related Experiments**: None planned; would require harness documentation

---

### RQ-F3: Can we detect phantom reads programmatically from session files?

**Status**: PARTIALLY ANSWERED: NO (Direct), YES (Proxy)

**Background**: Phantom read markers don't appear in session files. However, context reset patterns correlate with phantom reads.

**Current Approach**:
- Use context reset counting as risk proxy
- Rely on agent self-report for confirmation
- Correlate output quality (fabricated details) as secondary indicator

**Related Experiments**: Ongoing analysis methodology refinement

---

### RQ-F4: Why is there a ~40% token overhead when reading files?

**Status**: OPEN (LOW PRIORITY)

**Background**: When preloading files via hoisting, the harness consistently reports ~40% more tokens consumed than the actual file content tokens. This overhead scales proportionally with preload size.

**Evidence** (from Experiment-Methodology-04 measurements, pre-`/analyze-wpd`):

| Setup Command | Preload Tokens | Observed Message Context | Unaccounted | Overhead % |
|---------------|----------------|--------------------------|-------------|------------|
| `/setup-easy` | 35K | 49.6K | 14.6K | 41.8% |
| `/setup-medium` | 50K | 68.9K | 18.9K | 38.1% |
| `/setup-hard` | 68K | 96.9K | 28.9K | 42.4% |

Total context follows the same pattern (adding ~23K baseline):
- Easy: 73K observed = 23K baseline + 35K preload + 15K unaccounted
- Medium: 92K observed = 23K baseline + 50K preload + 19K unaccounted
- Hard: 120K observed = 23K baseline + 68K preload + 29K unaccounted

**Hypotheses**:
- Message/tool result formatting overhead (XML tags, metadata)
- Read tool invocation overhead per file
- Tokenization differences between raw file content and injected context
- Caching or deduplication metadata

**Relationship to RQ-F1**: RQ-F1 notes a ~25K fixed discrepancy; this question addresses a proportional ~40% overhead that scales with content size. These may be related or independent phenomena.

**Priority**: Low - we can work around this by using empirical measurements rather than file token counts. Understanding the mechanism is not blocking.

**Related Experiments**: None planned; observational finding

---

## Category G: Cross-Version and Cross-Model Behavior

Questions about how behavior varies across Claude Code versions and model variants.

### RQ-G1: Are our findings version-specific?

**Status**: OPEN

**Background**: Most trials use version 2.1.6. We don't know if findings (especially the danger zone hypothesis) apply to other versions.

**Concern**: If findings are version-specific, our reproduction scenarios won't work across versions.

**Related Experiments**: Cross-version testing (not yet designed)

---

### RQ-G2: Can we detect both Era 1 and Era 2 phantom reads programmatically?

**Status**: OPEN

**Background**: Era 1 uses `[Old tool result content cleared]`; Era 2 uses `<persisted-output>`. Analysis scripts may need to detect both.

**Current State**: Analysis focuses on Era 2. Era 1 detection not implemented.

**Related Experiments**: None planned; implementation concern

---

### RQ-G3: Is there a "safe" Claude Code version?

**Status**: ANSWERED: NO

**Background**: Original investigation incorrectly concluded pre-2.0.59 versions were safe.

**Conclusion**: ALL tested versions (2.0.54 through 2.1.6) can exhibit phantom reads. The mechanism differs by era, but no safe version exists.

**Evidence**: 2.0.58-bad session demonstrates Era 1 phantom reads

---

### RQ-G4: Why does the 1M model avoid phantom reads that affect the 200K model?

**Status**: NEW - OPEN (LOW PRIORITY - see scope note)

**Background**: Experiment-04K showed 100% success with the 1M model using the same protocol that caused 100% failure on the 200K model.

**Evidence**:
- 04K: 6/6 SUCCESS, peak tokens up to 202K
- Method-04: 8/8 FAILURE at similar token counts on 200K model
- Same reset patterns (SINGLE_LATE) in both

**Hypotheses**:
- 5x headroom prevents the model from entering the "danger zone"
- The 1M model may have different context management behavior
- The threshold for aggressive context management scales with model capacity

**⚠️ Scope Note**: Experiment-04K was conducted **solely to validate that T (context window size) is a relevant variable** in our X+Y model. The 1M model is **NOT a direction to pursue** for this investigation. This project must remain focused on the 200K model, which is the default configuration users encounter. Further investigation into the 1M model's behavior is out of scope.

**Related Experiments**: 04K (completed) - no further 1M investigation planned

---

### RQ-G5: Is the 1M model a viable workaround for phantom reads?

**Status**: ANSWERED: YES (but out of scope - see note)

**Background**: Experiment-04K demonstrated complete immunity to phantom reads with the 1M model.

**Evidence**:
- 6/6 trials SUCCESS
- Peak tokens exceeded 200K nominal (202K) and still succeeded
- Same protocol that fails on 200K model

**Practical Considerations**:
- May have cost implications (larger context = more tokens billed)
- Availability may vary
- Confirms MCP isn't the ONLY workaround

**Conclusion**: Using the 1M context model appears to be a viable alternative workaround alongside MCP Filesystem.

**⚠️ Scope Note**: While the 1M model is technically a viable workaround, **this investigation will not pursue it further**. Experiment-04K was conducted as a one-time diagnostic to confirm that T (context window size) is a relevant variable. The project's reproduction scenarios and analysis must focus on the **200K model**, which represents the default user experience. The MCP Filesystem workaround remains the recommended mitigation for users needing to avoid phantom reads.

**Related Experiments**: 04K (completed) - no further 1M investigation planned

---

## Category H: Persisted Output Mechanism

Questions specific to the Era 2 `<persisted-output>` behavior.

### RQ-H1: Is content actually written to persisted-output files?

**Status**: OPEN

**Background**: When phantom reads occur via `<persisted-output>` markers, we assume content is written to disk but the agent doesn't follow up. We haven't verified this.

**Test Approach**: Examine `tool-results/` directories in trial data

**Related Experiments**: 04J (Examine Persisted Files)

---

### RQ-H2: Why doesn't the agent follow up on `<persisted-output>` markers?

**Status**: OPEN

**Background**: The marker explicitly says "Use Read to view" but agents don't issue follow-up reads.

**Hypotheses**:
- Agent doesn't "see" the marker (it's in tool result, not conversation)
- Agent sees it but doesn't understand instruction
- Agent proceeds too quickly before processing the marker
- Context management clears the marker before agent processes it

**Related Experiments**: Behavioral investigation needed

---

### RQ-H3: What determines when persisted-output is used vs inline content?

**Status**: PARTIALLY UNDERSTOOD

**Background**: Some reads return inline content; others trigger persisted-output.

**Current Understanding**: Size threshold triggers persisted-output, but exact threshold unknown.

**Evidence**: Large files trigger persisted-output; small files return inline

**Related Experiments**: None planned

---

## Summary Statistics

| Category | Total | Open | Answered | Hypothesis |
|----------|-------|------|----------|------------|
| A: Core Mechanism | 5 | 3 | 0 | 2 |
| B: Threshold Behavior | 8 | 3 | 4 | 1 |
| C: Hoisting Behavior | 4 | 0 | 3 | 1 |
| D: Reset Timing | 3 | 1 | 0 | 2 |
| E: Read Patterns | 6 | 3 | 0 | 3 |
| F: Measurement | 4 | 3 | 1 | 0 |
| G: Cross-Version/Model | 5 | 3 | 1 | 1 |
| H: Persisted Output | 3 | 3 | 0 | 0 |
| **TOTAL** | **38** | **19** | **9** | **10** |

---

## Experiment Coverage

| Experiment | Status | Primary RQs Addressed |
|------------|--------|----------------------|
| **04A** | ✅ COMPLETED | RQ-B1 ✓, RQ-B4 ✓, RQ-D3 |
| 04B | Not run | RQ-B2, RQ-B3 |
| 04C | Not run | RQ-B2 (sanity check) |
| **04D** | ✅ COMPLETED | RQ-B1 ✓, RQ-C1 ✓, RQ-C4 ✓, RQ-D2 |
| 04E | Not run | RQ-E3 |
| 04F | Not run | RQ-B3 |
| 04G | Not run | RQ-E2 |
| 04H | Not run | RQ-D2 |
| 04I | Not run | RQ-E4 |
| 04J | Not run | RQ-A2, RQ-A3, RQ-H1 |
| **04K** | ✅ COMPLETED | RQ-B5 ✓, RQ-D1, RQ-G4, RQ-G5 |
| **04L** | ✅ COMPLETED | RQ-C2 ✓ |

---

## Key Findings Summary (from Completed Experiments)

### The "Danger Zone" Model (Emerging)

Based on experiments 04A, 04D, 04K, and 04L, phantom reads on the 200K model appear to require:

```
DANGER ZONE (200K model):
  X ≥ ~73K tokens (pre-operation context)
  AND
  Y ≥ ~50K tokens (agent-initiated reads)

SAFE CONDITIONS:
  - X ≈ 0 (any Y up to 57K tested) → SUCCESS
  - Y minimal (~6K) (any X up to 150K tested) → SUCCESS
  - 1M model (any tested X/Y combination) → SUCCESS
```

### Confirmed Mitigations

1. **Hoisting** (RQ-C1, RQ-C4): Move files from Y to X via `@`-notation
2. **MCP Filesystem**: Bypass native Read entirely (previously established)
3. **1M Model** (RQ-G5): Use larger context window model *(Note: Confirmed to work but out of scope for this investigation; included for completeness only)*

---

## Document History

- **2026-01-26**: Initial creation from Investigation Journal and Post-Experiment-04-Ideas analysis
- **2026-01-26**: Major update incorporating results from Experiments 04A, 04D, 04K, 04L
  - Updated 7 existing RQs with new status/evidence
  - Added 7 new RQs (RQ-A5, RQ-B7, RQ-B8, RQ-C4, RQ-E6, RQ-G4, RQ-G5)
  - Added Key Findings Summary section
  - Updated statistics and experiment coverage
- **2026-01-26**: Added RQ-F4 (token overhead on file reads) based on Experiment-Methodology-04 observations
- **Source Documents**:
  - `docs/core/Investigation-Journal.md`
  - `docs/experiments/planning/Post-Experiment-04-Ideas.md`
  - `docs/experiments/results/Experiment-04-Prelim-Results.md`
  - `docs/theories/Consolidated-Theory.md`
