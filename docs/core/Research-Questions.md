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
- **Per-file mapping of 2.1.6-bad session** (documented in `docs/experiments/results/Example-Session-Analysis.md`, Question 4): All 11 reads in session lines 20-50 were persisted to `tool-results/`; all 7 reads in lines 64-87 returned inline. This temporal boundary provides the strongest direct evidence that persistence targets earlier reads in a session

**Related Experiments**: 04J (examine persisted files)

---

### RQ-A3: Why does the session `.jsonl` file record actual content while the agent receives phantom read markers?

**Status**: HYPOTHESIS FORMED

**Background**: Session files contain complete file content in `tool_result` entries, but agents report seeing `[Old tool result content cleared]` or `<persisted-output>` markers.

**Hypothesis**: The session file logs tool execution results, but a separate context management system transforms content before it reaches the model. This transformation happens AFTER session logging but BEFORE model context injection.

**Evidence**:
- Phantom read markers appear NOWHERE in session files except in conversation text where agents discuss them
- 2.0.58-bad session shows full content logged but agent confirms seeing cleared markers
- Persisted and inline reads are **structurally identical** in the `.jsonl` — both have `toolUseResult.type: "text"` with `toolUseResult.file` metadata and actual content in `message.content[].content`. No field or format distinguishes them (see `docs/experiments/results/Example-Session-Analysis.md`, Question 4)
- The `tool-results/` directory (present in hybrid and hierarchical session structures) contains the persisted output files, confirming content IS written to disk, but the `.jsonl` records the content as if it were delivered inline

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

**Status**: ~~NEW - OPEN~~ → MECHANISM IDENTIFIED

**Background**: Experiments 04D and 04L demonstrated that hoisted content (`@`-notation) never triggers phantom reads, even under extreme context pressure (~172K tokens). Agent-initiated reads via the Read tool are vulnerable.

**Evidence**:
- 04D Hard+maxload: Context filled to capacity, but NO phantom reads on hoisted content
- 04L: 150K hoisted tokens + 6K agent-read = SUCCESS
- Method-04: 73K hoisted + 57K agent-read = FAILURE

**Key Evidence (2026-01-27)**: An agent's self-reflection during Barebones trials revealed that hoisted files appear as full content in `<system-reminder>` blocks:

> "The four files loaded via the /setup-hard skill's @ references appeared as full content in `<system-reminder>` blocks, so those were actually available to me."

**Answer**: The difference is the **injection mechanism**:
- **Hoisted content**: Injected as `<system-reminder>` blocks (part of system message structure)
- **Agent-initiated reads**: Returned as tool results (subject to context management)

Context management can clear/persist tool results but cannot modify system message content. This explains why hoisting is immune regardless of context pressure.

**Related Experiments**: 04D (completed), 04I (Partial MCP Hybrid)
**See Also**: RQ-C3 for more details on this mechanism

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

| Condition          | X    | Y   | X+Y  | Outcome                      |
| ------------------ | ---- | --- | ---- | ---------------------------- |
| High X only        | 150K | 6K  | 156K | **SUCCESS** (04L)            |
| High Y only        | ≈0   | 57K | ~57K | **SUCCESS** (04A)            |
| Both moderate-high | 73K+ | 57K | 130K | **FAILURE** (Method-04 Easy) |
| High X, moderate Y | 120K | 42K | 162K | **SUCCESS** (Method-03 Hard) |
| Neither high       | Low  | Low | Low  | **SUCCESS** (various)        |

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

**Status**: PARTIALLY ANSWERED → MECHANISM IDENTIFIED

**Background**: Hoisted content is immune to phantom reads; agent-initiated reads are vulnerable.

**Current Understanding**:
- Hoisting happens before the agent runs, so content is "baked in" to initial context
- This content is not subject to the same context pressure management
- Agent-initiated reads go through a layer that CAN trigger phantom reads under pressure

**Key Evidence (2026-01-27)**: An agent's self-reflection during Barebones trials revealed:

> "The four files loaded via the /setup-hard skill's @ references (operations-manual-standard.md, operations-manual-exceptions.md, architecture-deep-dive.md, troubleshooting-compendium.md) appeared as full content in `<system-reminder>` blocks, so those were actually available to me."

**Mechanism**: Hoisted files are injected into the context as `<system-reminder>` blocks containing the full file content. This means:
1. The content becomes part of the **system message structure**, not a tool result
2. Tool results can be cleared/persisted by context management; system messages cannot
3. The hoisted content is present before any agent turn begins, making it immune to mid-session context pressure

**Remaining Question**: Is the `<system-reminder>` injection mechanism used for ALL hoisted content (including direct user `@` references), or only for `@` references within slash commands?

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

**Background**: Recovery from phantom reads has been observed in multiple contexts where agents followed up on persisted output markers.

**Evidence**:
- **2.1.6-bad example session** (Jan 12-13, documented in `docs/experiments/results/Example-Session-Analysis.md`): Line 87 of the session shows the agent successfully reading a persisted `.txt` file from the `tool-results/` directory — the earliest documented instance of agent recovery from a `<persisted-output>` marker
- **Trial 20260121-202919** (repro-attempts-02): A failure was recovered when the agent recognized `<persisted-output>` markers and re-read files
- **Build-Scan Discrepancy Analysis** (Jan 29-30): ~10% of direct-read sessions with persistence showed successful agent recovery

**Questions**:
- Can this be systematized as a mitigation strategy?
- Does recovery work consistently?
- What prevents agents from recognizing markers in the first place?
- Why do some agents follow up on markers while most ignore them?

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

| Setup Command   | Preload Tokens | Observed Message Context | Unaccounted | Overhead % |
| --------------- | -------------- | ------------------------ | ----------- | ---------- |
| `/setup-easy`   | 35K            | 49.6K                    | 14.6K       | 41.8%      |
| `/setup-medium` | 50K            | 68.9K                    | 18.9K       | 38.1%      |
| `/setup-hard`   | 68K            | 96.9K                    | 28.9K       | 42.4%      |

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

### RQ-F5: Is the transient "0% remaining" UI warning a visible indicator of context resets?

**Status**: NEW - OPEN (OBSERVATIONAL)

**Background**: During trial execution, the User has observed that the Claude Code status bar occasionally flashes "0% remaining" during the operation command (`/analyze-wpd`) when phantom reads are expected to occur. The warning appears briefly and then disappears, and is NOT present when the Session Agent finishes the task.

**Hypothesis**: The transient "0% remaining" warning may be a visible signal that a context reset is occurring or about to occur. If validated, this could provide a real-time indicator for identifying reset events during trials.

**Challenges**:
- UI elements are not logged in session files
- Observation is anecdotal and not systematically recorded
- Would require video recording or manual notation during trials

**Potential Value**:
- Could provide real-time feedback during trials
- May help correlate reset timing with specific operations
- Could inform development of better trial protocols

**Proposed Investigation**:
1. Record UI state during several trials (video or manual notes)
2. Note when "0% remaining" appears and correlate with operation phase
3. Compare trials where warning was observed vs not observed
4. Correlate with phantom read outcomes

**Related Experiments**: None planned; would require methodology enhancement to capture UI state

---

## Category G: Cross-Version and Cross-Model Behavior

Questions about how behavior varies across Claude Code versions and model variants.

### RQ-G1: Are our findings version-specific?

**Status**: OPEN — EXTENSIVE NEW EVIDENCE FROM BUILD SCAN

**Background**: Most trials use version 2.1.6. We don't know if findings (especially the danger zone hypothesis) apply to other versions.

**Concern**: If findings are version-specific, our reproduction scenarios won't work across versions.

**Evidence (2026-01-27)**:
- **Barebones-2120**: Same protocol that produces 100% failure on v2.1.6 (4/4 valid trials) initially appeared to produce **0% failure on v2.1.20** (5/5 SUCCESS)

**Evidence (2026-01-28 — Build Scan)**: Comprehensive testing of every build from 2.1.6 through 2.1.22 reveals three distinct behavioral eras:

| Build Range   | Behavior                                      | Interpretation                                    |
| ------------- | --------------------------------------------- | ------------------------------------------------- |
| 2.1.6         | 100% phantom read failure                     | Our tuned scenario triggers reliably              |
| 2.1.7–2.1.14  | Context overflow (cannot execute)             | Context management too aggressive — kills session |
| 2.1.15–2.1.19 | Phantom read failures                         | Returns to 2.1.6-like behavior                    |
| 2.1.20        | Mixed (failures + successes + context limits) | Transitional build                                |
| 2.1.21–2.1.22 | Phantom read failures; no context limits      | Context limits eliminated, phantom reads persist  |

**Key finding**: The Barebones-2120 result (0% failure) was a **small-sample artifact**. The larger 11-trial study on v2.1.20 shows 6 failures, 1 success, and 4 context limits. Phantom reads ARE still present on 2.1.20.

**Revised Understanding**: Our findings are NOT as version-specific as initially feared. The phantom read mechanism persists across ALL tested builds (2.1.6 through 2.1.22). What varies is the context management behavior:
- 2.1.7–2.1.14: Overly aggressive (session dies)
- 2.1.15+: Returns to phantom-read-producing behavior
- 2.1.21+: Context limits eliminated, clean phantom read signal

**Related Experiments**: Barebones-216, Barebones-2120, Build Scan (completed 2026-01-28)

---

### RQ-G2: Can we detect both Era 1 and Era 2 phantom reads programmatically?

**Status**: OPEN

**Background**: Era 1 uses `[Old tool result content cleared]`; Era 2 uses `<persisted-output>`. Analysis scripts may need to detect both.

**Current State**: Analysis focuses on Era 2. Era 1 detection not implemented.

**Related Experiments**: None planned; implementation concern

---

### RQ-G3: Is there a "safe" Claude Code version?

**Status**: PARTIALLY REOPENED

**Background**: Original investigation incorrectly concluded pre-2.0.59 versions were safe.

**Previous Conclusion**: ALL tested versions (2.0.54 through 2.1.6) can exhibit phantom reads. The mechanism differs by era, but no safe version exists.

**New Evidence (2026-01-27)**: CC v2.1.20 shows **0% failure rate** on our reliable repro case (Barebones-2120: 5/5 SUCCESS + additional unrecorded successes). This does NOT mean 2.1.20 is "safe" — our specific scenario may simply no longer trigger the bug. We cannot rule out that phantom reads still occur under different conditions.

**Revised Conclusion**: No version prior to 2.1.20 is safe. Version 2.1.20 may be safe for our specific repro case but requires broader testing before declaring it generally safe.

**Evidence**: 2.0.58-bad session demonstrates Era 1 phantom reads; Barebones-2120 shows 0% failure on v2.1.20

---

### RQ-G6: What changed between CC v2.1.6 and v2.1.20?

**Status**: PARTIALLY ANSWERED (Build Scan 2026-01-28)

**Background**: Barebones-216 (v2.1.6) shows 100% failure rate among valid trials (4/4); Barebones-2120 (v2.1.20) initially appeared to show 0% failure rate (5/5). Same protocol, same repository, same files — only the Claude Code version differs.

**Possible Explanations** (original):
1. ~~**Bug Fix**: Anthropic fixed the phantom reads issue entirely~~ — **RULED OUT** (2.1.22 shows 100% failure)
2. **Threshold Shift**: Read overhead reduced via optimization, shifting our scenario below the danger zone — possible but less likely given 2.1.22 failure
3. **Mechanism Change**: Deferred read handling changed again (potential "Era 3") — possible
4. ~~**Optimization Side-Effect**: Unrelated optimization incidentally prevents our trigger conditions~~ — **RULED OUT** (phantom reads persist on later builds)

**Build Scan Evidence (2026-01-28)**: The comprehensive build scan revealed the transition is NOT a simple boundary but a complex evolution:

- **2.1.7–2.1.12**: Context management became MORE aggressive (context overflow, session dies)
- **2.1.13**: Does not exist (version skipped)
- **2.1.14**: Still context overflow, but beginning to recover
- **2.1.15**: First post-2.1.6 build where Method-04 executes — phantom reads present
- **2.1.20**: Revised — NOT 0% failure. 11-trial study shows 6 failures, 1 success, 4 context limits
- **2.1.21+**: Context limit errors eliminated; phantom reads persist
- **2.1.22**: 100% failure (6/6), same as 2.1.6

**Revised Understanding**: There was no single "fix" or "shift." Instead, context management went through three phases:
1. **2.1.6**: Phantom reads via deferred content clearing
2. **2.1.7–2.1.14**: Overly aggressive context management (refuses to proceed)
3. **2.1.15+**: Returns to phantom-read-producing behavior; context limits gradually eliminated by 2.1.21

The Barebones-2120 "0% failure" was a small-sample artifact, not evidence of a fix.

**Remaining Question**: What specifically changed in 2.1.7 to make context management so aggressive, and what changed in 2.1.15 to relax it?

**Related Experiments**: Build Scan (completed 2026-01-28), Barebones-216 analysis, Barebones-2120 analysis

---

### RQ-G7: Can we re-establish a failure repro case on CC v2.1.20?

**Status**: ANSWERED: YES (Build Scan 2026-01-28)

**Background**: Our carefully tuned Method-04 + `/setup-hard` protocol initially appeared to no longer trigger phantom reads on v2.1.20 (5/5 success in Barebones-2120 study).

**Answer**: The premise was based on a small-sample artifact. The larger 11-trial study on v2.1.20 (conducted 2026-01-28) revealed:
- 5 phantom read failures
- 1 success
- 5 context limit errors

Phantom reads **DO occur on v2.1.20** with the existing protocol — no payload increase was needed. The original 5-trial study was simply lucky.

**Additional Finding**: Build 2.1.22 provides an even more reliable failure case (6/6, 100% failure, no context limits), making it the preferred target build for future experiments.

**Note (2026-01-29)**: The single "success" in `dev/misc/barebones-2121` was subsequently identified as a protocol violation (invalid trial), not a genuine success. This reinforces the conclusion that phantom reads are consistent on 2.1.21+.

**Related Experiments**: Build Scan (completed 2026-01-28)

---

### RQ-G10: Why did the Barebones-2120 and build-scan 2.1.20 results differ when run within the same ~4-hour window?

**Status**: ANSWERED (Build-Scan Discrepancy Investigation, 2026-01-30)

**Discovery Date**: 2026-01-29

**Background**: The original Barebones-2120 study (`dev/misc/repro-attempts-04-2120`) produced 5/5 SUCCESS on v2.1.20. The build-scan trials (`dev/misc/barebones-2120-2`), run approximately 1 hour later with the same protocol, same repository, and same CC build, produced 6 failures, 1 success, and 4 context limit errors.

**Answer**: The discrepancy is fully explained by **server-side variability in the persistence mechanism**. On Jan 27, the server did not enable persistence for any session on build 2.1.20 — all 5 trials read files inline and succeeded (`has_tool_results: false` in all 5). On Jan 28, the server enabled persistence for all sessions across all builds — 100% of direct-read trials had `has_tool_results: true` and phantom reads occurred. The test environment, protocol, and build were identical; the server-side persistence decision was the sole variable.

**Evidence**:
- Build 2.1.22 reversal: 100% failure (Jan 28) → 100% success (Jan 29) with zero environment changes — proves the variable is temporal/server-side
- Build 2.1.6 tested Jan 29: behaviorally indistinguishable from builds 2.1.20 and 2.1.22 on the same day — proves build version is irrelevant
- Within-window stochastic behavior: Jan 29 schema-13-2120 showed 80% persistence among direct-read trials in a 20-minute window — confirms probabilistic per-session mechanism
- The `has_tool_results` field is a near-perfect per-session discriminator: `false` = 100% success (14/14), `true` = 85% failure (17/20 non-overload)

**Original Hypotheses (resolved)**:
1. ✅ **Server-side changes**: CONFIRMED — the primary explanation. Server-side persistence control varies over time.
2. ✅ **Small-sample artifact**: PARTIALLY CONFIRMED — the 5/5 success was consistent with a low persistence probability on Jan 27, not proof of a fix.
3. ❌ **Test environment drift**: RULED OUT — environmental fingerprints were identical (baselines within ~80 tokens).
4. ❌ **Session state effects**: RULED OUT — mixed persistence within same time window rules out cumulative state.

**Investigation Plan**: Documented in `docs/experiments/planning/Build-Scan-Discrepancy-Investigation.md`

**Analysis**: `docs/experiments/results/Build-Scan-Discrepancy-Analysis.md` (completed — full root cause chain mapped)

**Related Experiments**: Build Scan (completed 2026-01-28), Barebones-2120 (completed 2026-01-27), Schema-13 experiments (completed 2026-01-29–30)

---

### RQ-G8: Why do builds 2.1.7 through 2.1.14 cause context overflow instead of phantom reads?

**Status**: NEW — OPEN

**Discovery Date**: 2026-01-28 (Build Scan)

**Background**: Builds 2.1.7 through 2.1.12 consistently hit context overflow during `/analyze-wpd`, killing the session before the trigger operation completes. Build 2.1.14 shows the same behavior. Build 2.1.6 produces phantom reads; build 2.1.15 returns to phantom-read behavior.

**Significance**: This "dead zone" suggests that context management went through a phase of being overly aggressive — instead of silently clearing/persisting content (producing phantom reads), the system refused to proceed at all. This is arguably the *correct* behavior (fail loudly), and it was later relaxed back to the phantom-read-producing behavior.

**Questions**:
- What change in 2.1.7 made context management more aggressive?
- What change in 2.1.15 relaxed it back?
- Is the dead zone behavior related to the same underlying mechanism as phantom reads?
- Did Anthropic intentionally change context management behavior, or was this a side effect?

**Related Experiments**: Build Scan (completed 2026-01-28)

---

### RQ-G9: What eliminated context limit errors between builds 2.1.20 and 2.1.21?

**Status**: NEW — OPEN

**Discovery Date**: 2026-01-28 (Build Scan)

**Background**: Build 2.1.20 shows 5/11 trials hitting context limits. Builds 2.1.21 and 2.1.22 show 0/18 context limits across all trials. Something changed between 2.1.20 and 2.1.21 that eliminated context overflow errors entirely.

**Significance**: The context limit errors disappeared, but phantom reads persisted (and increased — 2.1.22 shows 100% failure). This suggests the "fix" addressed the overflow behavior without addressing the underlying phantom read mechanism. The system learned to handle context pressure without crashing, but still silently defers/clears reads.

**Related Experiments**: Build Scan (completed 2026-01-28)

---

### RQ-G11: Are Task sub-agent reads structurally immune to phantom reads?

**Status**: NEW — OPEN (HYPOTHESIS: YES)

**Discovery Date**: 2026-01-29 (evening)

**Background**: During schema-13 experiments, Session Agents that delegated Read operations to Task sub-agents consistently succeeded, even on builds (like 2.1.22) that showed 100% failure for direct-read trials. Each sub-agent operates in a fresh, small context window.

**Hypothesis**: Task sub-agent reads are structurally immune to phantom reads because:
1. Each sub-agent starts with a fresh context (~23K baseline)
2. A sub-agent reading 1–4 files stays well below the danger zone thresholds
3. The main session only receives the sub-agent's summary, not the full file content
4. This is functionally equivalent to the MCP workaround — reads happen outside the main session's context management

**Evidence**:
- schema-13-2120: 4/4 delegation trials SUCCESS vs. 3/5 direct-read trials FAILURE
- schema-13-2122: 5/5 delegation trials SUCCESS; build previously showed 6/6 FAILURE (direct-read, Jan 28)
- Delegation trials in Build-Scan Discrepancy Analysis show consistent success across builds

**Questions**:
- What determines whether a Session Agent delegates vs. reads directly?
- Is delegation behavior controllable (e.g., via prompt design)?
- Does the main session still receive full file content from sub-agents, or only summaries?
- Could delegation be used as a deliberate mitigation strategy?

**Related Experiments**: None yet; would require controlled comparison of delegation vs. direct-read
**Related DB**: DB-I14

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

**Status**: ~~OPEN~~ → **ANSWERED: YES**

**Background**: When phantom reads occur via `<persisted-output>` markers, we assume content is written to disk but the agent doesn't follow up. We hadn't verified this.

**Answer**: YES. Content is written to disk in the `tool-results/` directory.

**Evidence** (from `docs/experiments/results/Example-Session-Analysis.md`, Questions 3-4):
- The 2.1.6-bad session's `tool-results/` directory contains files named by tool_use_id (e.g., `toolu_0162qTLwBAPom8tHQpddvAev.txt`, 26KB — the actual content of `stage_release.py`)
- All 11 persisted reads in the session have corresponding `.txt` files in `tool-results/`
- The 2.1.6-good session has **no `tool-results/` directory** at all — only `subagents/`
- Presence or absence of the `tool-results/` directory is a reliable indicator of whether persistence occurred during the session

**Related Experiments**: 04J (Examine Persisted Files) — partially addressed by the Example-Session-Analysis findings

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

## Category I: Discovered Behaviors

This section catalogs confirmed facts about Claude Code behavior discovered during experimentation. These are NOT questions but established knowledge that affects methodology or would be valuable for future investigators.

### DB-I1: PreToolUse hooks are unreliable for file read interception

**Status**: CONFIRMED

**Discovery Date**: 2026-01-13

**Description**: Claude Code hooks (PreToolUse) do not fire consistently. Even when observed firing in the terminal, agent behavior may not be affected. Hooks cannot be relied upon for critical operations like phantom read mitigation.

**Evidence**: Attempted to use PreToolUse hook with "deny" response to inject file contents via error mechanism. Despite hooks visibly firing, agents still experienced `<persisted-output>` responses.

**Implication**: Hook-based workarounds are not viable for phantom read mitigation.

---

### DB-I2: Project-level `permissions.deny` has limited scope

**Status**: CONFIRMED

**Discovery Date**: 2026-01-13

**Description**: When using `permissions.deny: ["Read"]` in `.claude/settings.local.json` (project config), the denial only affects the main Claude Code session agent. It does NOT restrict:
- Slash commands and skills (custom commands may still use native Read tool)
- Sub-agents spawned via the Task tool

**Evidence**: Observed during MCP Filesystem workaround implementation and testing.

**Implication**: For complete phantom read protection, global configuration (`~/.claude/settings.json`) may be needed, but this requires configuring MCP server paths for each project.

---

### DB-I3: Claude Code configuration file paths

**Status**: CONFIRMED

**Discovery Date**: 2026-01-13

**Description**: Claude Code uses two distinct configuration file locations:
- **Global config**: `~/.claude/settings.json` - affects all projects
- **Project config**: `.claude/settings.local.json` - affects only the current project

Note: `.claude/settings.json` (without `.local`) is NOT a valid project config path.

**Evidence**: Discovered when documenting the MCP Filesystem workaround; initial documentation incorrectly referenced `.claude/settings.json`.

**Implication**: When documenting workarounds or configurations, specify the correct path based on intended scope.

---

### DB-I4: Chat exports must be saved OUTSIDE the project directory

**Status**: CONFIRMED

**Discovery Date**: 2026-01-14

**Description**: When running `/export` to save chat transcripts, the export file must be saved OUTSIDE the project directory. If saved within the project, the session ID appears in the chat export file, and when Claude Code runs in that same project later, the new session's `.jsonl` files will contain grep-able references to the old session ID (because the export file is within the project scope).

**Evidence**: User ran trials sequentially and noticed session UUIDs from earlier trials appearing in later session files via grep. Investigation revealed this was due to `/export` files being saved within the project directory, not actual session contamination.

**Implication**: Always export chat transcripts to a directory OUTSIDE the project (e.g., `../cc-exports/`) to avoid polluting session file analysis. This is now documented in Experiment-Methodology-02.

---

### DB-I5: `/context` command cannot be called by agents programmatically

**Status**: CONFIRMED

**Discovery Date**: 2026-01-22-23

**Description**: The `/context` command (Claude Code built-in for displaying token consumption) only works when explicitly typed by the user. Agents cannot invoke it programmatically from within custom commands, slash commands, or any automated script context.

**Evidence**: Discovered during Experiment-Methodology-03 development when attempting to integrate `/context` calls into scenario commands (`/analyze-light`, `/analyze-standard`, `/analyze-thorough`). The commands failed to produce context measurements, leading to investigation that confirmed agents cannot invoke this built-in command.

**Implication**: Trial protocols must include explicit user `/context` calls at key measurement points (baseline, post-preload, post-operation). Context consumption cannot be automatically logged within commands, requiring the methodology restructuring that led to Experiment-Methodology-04's separated setup and analysis commands.

---

### DB-I6: Session Agents discover and read cross-referenced files independently

**Status**: CONFIRMED

**Discovery Date**: 2026-01-25

**Description**: Session Agents will independently discover and read files that are cross-referenced in other loaded specifications, even when those files are deliberately omitted from command file lists. This prevents simple "file list reduction" approaches to controlling Y (operation context).

**Evidence**: Discovered during Experiment-04B/04C planning when attempting to reduce spec count from 9 to 8 files by removing `module-epsilon.md` and `module-phi.md` from the `/analyze-wpd` command. Despite omission from the command's explicit file list, agents consistently found and read these files via cross-references in `data-pipeline-overview.md`, `integration-layer.md`, and the `pipeline-refactor.md` WPD.

**Implication**: To test different Y values via file count reduction, invasive surgical edits must be made to remove cross-references throughout the spec scenario, not just the command file list. Experiments 04B and 04C require more preparation work than initially anticipated.

---

### DB-I7: Transient "0% remaining" UI warning may signal context resets

**Status**: OBSERVED (NOT YET CONFIRMED)

**Discovery Date**: 2026-01-27

**Description**: During trial execution, the Claude Code status bar occasionally displays "0% remaining" briefly during operation commands (`/analyze-wpd`) and then disappears. The warning is NOT present when the Session Agent finishes the task. This has been observed anecdotally during trials where phantom reads are expected to occur.

**Evidence**: User observation during many runs throughout project, but noted it specifically in the Barebones-216 trial runs. Not systematically recorded.

**Hypothesis**: This transient warning may be a visible indicator that a context reset is in progress or about to occur. The warning appearing and then disappearing could represent the harness:
1. Detecting context pressure approaching threshold
2. Initiating a reset
3. Clearing the warning once reset completes and context drops

**Limitation**: This is a UI element that is NOT captured in session logs or chat exports. It can only be observed in real-time during trials.

**Implication**: If validated, this observation could:
- Provide real-time feedback during trial execution
- Help identify the exact moment resets occur relative to specific operations
- Inform enhanced trial protocols that capture UI state (via video or manual notes)

**Related RQ**: RQ-F5 (proposed investigation of this phenomenon)

---

### DB-I8: Hoisted files are injected as `<system-reminder>` blocks

**Status**: CONFIRMED

**Discovery Date**: 2026-01-27

**Description**: Files loaded via `@` notation in slash commands are injected into the agent's context as `<system-reminder>` blocks containing the full file content. This is distinct from agent-initiated Read tool calls, which return content as tool results.

**Evidence**: Agent self-reflection during Barebones-216 trial:

> "The four files loaded via the /setup-hard skill's @ references (operations-manual-standard.md, operations-manual-exceptions.md, architecture-deep-dive.md, troubleshooting-compendium.md) appeared as full content in `<system-reminder>` blocks, so those were actually available to me."

**Significance**: This explains why hoisted content is immune to phantom reads:
1. `<system-reminder>` blocks are part of the system message structure
2. System messages are not subject to the same context management as tool results
3. Tool results can be cleared (`[Old tool result content cleared]`) or persisted (`<persisted-output>`), but system messages cannot

**Implication**: The hoisting immunity is architectural—it's not about timing or code paths, but about the fundamental difference between system message content and tool result content in the Claude API/harness.

**Related RQs**: RQ-A5, RQ-C3

---

### DB-I9: Builds 2.1.7 through 2.1.14 cannot execute Experiment-Methodology-04

**Status**: CONFIRMED

**Discovery Date**: 2026-01-28

**Description**: Claude Code builds 2.1.7 through 2.1.12 (and 2.1.14) consistently hit a context overflow error during the `/analyze-wpd` command when using Experiment-Methodology-04 with `/setup-hard`. The session dies with a "0% memory" / "context full" message before the trigger operation completes. This means our primary experiment methodology cannot execute on these builds.

**Evidence**: Comprehensive build scan testing every build from 2.1.6 through 2.1.22. All trials on builds 2.1.7–2.1.12 and 2.1.14 resulted in context overflow. Build 2.1.6 and 2.1.15+ execute normally.

**Implication**: Any cross-version analysis must account for this "dead zone." These builds cannot be used for phantom read experiments with our current methodology. The dead zone also suggests that context management behavior changed significantly between 2.1.6 and 2.1.15, with an intermediate period of overly aggressive management.

**Related RQs**: RQ-G1, RQ-G6, RQ-G8

---

### DB-I10: `/context` command behavior varies significantly across builds

**Status**: CONFIRMED

**Discovery Date**: 2026-01-28

**Description**: The `/context` command (Claude Code built-in for displaying token consumption) exhibits different behaviors across builds:

| Build Range   | Behavior                                                                                                       |
| ------------- | -------------------------------------------------------------------------------------------------------------- |
| ≤2.1.8        | Prints to session chat normally                                                                                |
| 2.1.9         | Changed to an interstitial dialog; does not persist in chat log; described as "very buggy" with display issues |
| 2.1.10–2.1.13 | Unclear (builds in dead zone; limited testing)                                                                 |
| 2.1.14        | Restored to original behavior (prints to session chat)                                                         |
| 2.1.15–2.1.19 | **Double-print bug**: context output is printed twice to the session chat                                      |
| 2.1.20+       | Double-print bug fixed; normal behavior restored                                                               |

**Evidence**: Observed during comprehensive build scan (2026-01-28) across all tested builds.

**Implication**: Our experiment methodology relies on `/context` output captured in chat exports to measure token consumption. The interstitial behavior in 2.1.9 would make measurements impossible (data not captured in exports). The double-print bug in 2.1.15–2.1.19 is a nuisance but doesn't prevent data capture. Any future cross-version analysis must account for these variations.

**Related RQs**: RQ-G1, DB-I5

---

### DB-I11: Claude Code version 2.1.13 does not exist

**Status**: CONFIRMED

**Discovery Date**: 2026-01-28

**Description**: There is no Claude Code build numbered 2.1.13. The version numbering skips from 2.1.12 directly to 2.1.14.

**Evidence**: Attempted installation during comprehensive build scan. Version 2.1.13 is not available in the npm registry.

**Implication**: Minor — this is a version numbering gap with no impact on the investigation beyond noting the gap when documenting version ranges.

---

### DB-I12: Build 2.1.15 introduced npm-to-native installer transition warning

**Status**: CONFIRMED

**Discovery Date**: 2026-01-28

**Description**: Starting with build 2.1.15, Claude Code began issuing a warning during startup when installed via npm: "Claude Code has switched from npm to native installer. Run `claude install` or see https://docs.anthropic.com/en/docs/claude-code/getting-started for more options."

**Evidence**: Observed during build scan when installing via `cc_version.py --install 2.1.15` and later builds. The warning appears but does not prevent operation.

**Implication**: Our `cc_version.py` script installs via npm, which is now the legacy installation mechanism. The warning does not affect CC operation or our experiments, but future versions may eventually drop npm support entirely.

---

### DB-I13: Barebones-2121 "success" was a protocol violation (invalid trial)

**Status**: CONFIRMED

**Discovery Date**: 2026-01-29

**Description**: The single "success" trial in `dev/misc/barebones-2121` (build 2.1.21) was identified as an invalid trial due to a protocol violation — the Session Agent did not follow the experiment protocol correctly. This follows the same pattern as Barebones-216 trial 092331, where an agent skipped required files, reducing Y below the danger threshold and producing a false "success."

**Evidence**: Review of the build scan data during the Jan 29 documentation session identified the protocol violation.

**Implication**: The 2.1.21 collection should be treated as 2/2 failures (100% failure rate among valid trials), not 2/3 failures with 1 success. This eliminates a potential red herring where the 2.1.21 success might have suggested some protective behavior that was lost in 2.1.22. It also reinforces the importance of rigorous protocol validation for all trials — "success" trials must be verified as protocol-compliant before being accepted as valid data points.

**Related RQs**: RQ-G7, RQ-G1

---

### DB-I14: Session Agents sometimes delegate Read operations to Task sub-agents

**Status**: CONFIRMED

**Discovery Date**: 2026-01-29 (evening)

**Description**: During Method-04 trials on CC v2.1.20 and v2.1.22, Session Agents were observed delegating file Read operations to Task sub-agents instead of reading files directly in the main session context. When delegation occurs, each sub-agent operates in its own fresh context window, reading only a subset of the required files. This structurally avoids the context pressure conditions that trigger phantom reads.

**Evidence**: Observed across two collections:
- `schema-13-2120` (v2.1.20): 4/9 trials used delegation — all 4 succeeded. Of 5 direct-read trials: 3 failures, 1 success, 1 recovery.
- `schema-13-2122` (v2.1.22): 5/6 trials used delegation — all 5 succeeded. The 1 direct-read trial also succeeded.
- Build 2.1.22 had shown 100% failure (6/6) on Jan 28 (`barebones-2122`). The Jan 29 reversal to 100% success is explained by **both** the shift to delegation behavior **and** server-side persistence changes. Trial 211109 — a direct-read trial (no delegation) — succeeded at 198K total input tokens with zero persistence, proving the server-side persistence mechanism itself had changed (see `docs/theories/Server-Side-Variability-Theory.md`).

**Significance**: This is a major confounding variable in trial outcomes. Aggregate success/failure rates that mix direct-read and delegation trials are misleading. The delegation pattern explains apparent contradictions in cross-day results (e.g., 2.1.22 going from 100% failure to 100% success) without requiring server-side variability as an explanation.

**Implication**: Future trial analysis must classify trials as "direct-read" vs. "delegation" before drawing conclusions about phantom read rates. Methodology may need to be updated to either control for this variable or to deliberately test whether delegation is a reliable mitigation.

**Related RQs**: RQ-G11, RQ-G10, RQ-E4

---

### DB-I15: Phantom reads are NOT WSD-specific — confirmed via barebones environment

**Status**: CONFIRMED

**Discovery Date**: 2026-01-27

**Description**: The Barebones-216 experiment tested whether phantom reads occur in a minimal environment stripped of all non-essential project infrastructure. A repository containing only 20 files across 7 directories (no WSD framework, no hooks, no investigation documentation, no MCP configuration) reproduced phantom reads at 100% (4/4 valid trials) — identical to the full investigation repository's rate (8/8 with Method-04).

**Evidence**:

| Environment | Framework | Failure Rate |
| --- | --- | --- |
| Full investigation repo (Method-04) | Full WSD + hooks | 100% (8/8) |
| **Barebones repo (Barebones-216)** | **None** | **100% (4/4)** |
| WSD Development project | Full WSD | 77% (17/22) |

One additional trial (092331) was initially recorded as a "success" but was reclassified as INVALID due to a protocol violation — the agent skipped 3 of 8 required files, reducing Y below the danger threshold.

**Significance**: This definitively rules out the WSD framework, the `protect_files.py` hook system, investigation documentation, and project complexity as contributing factors. The bug exists at the Claude Code harness level and affects any user who triggers multi-file read operations under context pressure.

**Related RQs**: RQ-A5, RQ-C3
**Analysis**: `docs/experiments/results/Barebones-216-Analysis.md`

---

## Summary Statistics

| Category                | Total  | Open   | Answered | Hypothesis | Confirmed |
| ----------------------- | ------ | ------ | -------- | ---------- | --------- |
| A: Core Mechanism       | 5      | 2      | 1        | 2          | -         |
| B: Threshold Behavior   | 8      | 3      | 4        | 1          | -         |
| C: Hoisting Behavior    | 4      | 0      | 3        | 1          | -         |
| D: Reset Timing         | 3      | 1      | 0        | 2          | -         |
| E: Read Patterns        | 6      | 3      | 0        | 3          | -         |
| F: Measurement          | 5      | 4      | 1        | 0          | -         |
| G: Cross-Version/Model  | 11     | 6      | 3        | 1          | -         |
| H: Persisted Output     | 3      | 2      | 1        | 0          | -         |
| I: Discovered Behaviors | 15     | -      | -        | -          | 14        |
| **TOTAL**               | **60** | **21** | **13**   | **10**     | **14**    |

---

## Experiment Coverage

| Experiment | Status      | Primary RQs Addressed            |
| ---------- | ----------- | -------------------------------- |
| **04A**    | ✅ COMPLETED | RQ-B1 ✓, RQ-B4 ✓, RQ-D3          |
| 04B        | Not run     | RQ-B2, RQ-B3                     |
| 04C        | Not run     | RQ-B2 (sanity check)             |
| **04D**    | ✅ COMPLETED | RQ-B1 ✓, RQ-C1 ✓, RQ-C4 ✓, RQ-D2 |
| 04E        | Not run     | RQ-E3                            |
| 04F        | Not run     | RQ-B3                            |
| 04G        | Not run     | RQ-E2                            |
| 04H        | Not run     | RQ-D2                            |
| 04I        | Not run     | RQ-E4                            |
| 04J        | Not run     | RQ-A2, RQ-A3, RQ-H1              |
| **04K**    | ✅ COMPLETED | RQ-B5 ✓, RQ-D1, RQ-G4, RQ-G5     |
| **04L**    | ✅ COMPLETED | RQ-C2 ✓                          |

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
- **2026-01-26**: Added Category I: Discovered Behaviors from prompt log analysis (`Prompts-2026-01-13_140924.txt`)
  - Added DB-I1 (PreToolUse hook unreliability)
  - Added DB-I2 (permissions.deny scope limitation)
  - Added DB-I3 (configuration file paths)
  - Updated summary statistics to include new category
- **2026-01-26**: Added DB-I4 (chat export location best practice) from prompt log analysis (`Prompts-2026-01-14_120425.txt`)
- **2026-01-26**: Added DB-I5 (`/context` command limitation) from prompt log analysis (`Prompts-2026-01-23_100643.txt`)
- **2026-01-26**: Added DB-I6 (agent cross-reference file discovery) from prompt log analysis (`Prompts-2026-01-25_185205.txt`)
- **2026-01-27**: Added RQ-F5 (transient UI warning as reset indicator) and DB-I7 (observational data about "0% remaining" warning) from Barebones experiment observations
- **2026-01-27**: Added DB-I8 (hoisted files as system-reminder blocks) from agent self-reflection; updated RQ-A5 and RQ-C3 status to MECHANISM IDENTIFIED
- **2026-01-30**: Added Build Scan findings from prompt log analysis (`dev/todo/Prompts-2026-01-28_094131.txt`)
  - Updated RQ-G1 with extensive build scan evidence (three behavioral eras across 2.1.6–2.1.22)
  - Updated RQ-G6 status to PARTIALLY ANSWERED (ruled out bug fix and optimization side-effect explanations)
  - Updated RQ-G7 status to ANSWERED: YES (v2.1.20 failures confirmed in larger study)
  - Added RQ-G8 (dead zone: why builds 2.1.7–2.1.14 cause context overflow)
  - Added RQ-G9 (context limit elimination between 2.1.20 and 2.1.21)
  - Added DB-I9 (builds 2.1.7–2.1.14 cannot execute Method-04)
  - Added DB-I10 (`/context` command behavior varies by build)
  - Added DB-I11 (version 2.1.13 does not exist)
  - Added DB-I12 (npm-to-native installer warning from 2.1.15)
  - Updated summary statistics
- **2026-01-30**: Added Jan 29 findings from prompt log analysis (`dev/todo/Prompts-2026-01-29_082142.txt`)
  - Added RQ-G10 (Build-Scan Discrepancy: why did Barebones-2120 and build-scan 2.1.20 differ?)
  - Added note to RQ-G7 about barebones-2121 success being a protocol violation
  - Added DB-I13 (barebones-2121 success was a protocol violation)
  - Updated summary statistics
- **2026-01-30**: Added Jan 29 evening findings from prompt log analysis (`dev/todo/Prompts-2026-01-29_201458.txt`)
  - Added RQ-G11 (Task sub-agent reads structural immunity to phantom reads)
  - Added DB-I14 (Session Agents delegate Read operations to Task sub-agents)
  - Updated summary statistics
- **2026-01-30**: Processed prompt log `dev/todo/Prompts-2026-01-29_213439.txt` — no new RQs or DBs identified; all discoveries from this log (Server-Side Variability Theory, schema-13-216, Build-Scan Discrepancy closure, investigation redirect to documentation/reporting) were already captured in prior processing sessions
- **2026-01-30**: Added DB-I15 (phantom reads are NOT WSD-specific) from Barebones-216 Analysis cross-reference review
  - Updated summary statistics (14 → 15 Discovered Behaviors, 59 → 60 total)
- **2026-01-30**: Cross-reference review against `docs/experiments/results/Build-Scan-Discrepancy-Analysis.md`
  - Updated RQ-G10 status from OPEN to ANSWERED — Build-Scan Discrepancy investigation fully resolved this question via Server-Side Variability Theory
  - Corrected DB-I14 last bullet: the 2.1.22 reversal is explained by both delegation AND server-side persistence changes (not delegation alone); trial 211109 (direct-read, zero persistence, 198K tokens) was the key evidence
  - Updated summary statistics (G: 6 open/3 answered; Total: 21 open/13 answered)
- **Source Documents**:
  - `docs/core/Investigation-Journal.md`
  - `docs/experiments/planning/Post-Experiment-04-Ideas.md`
  - `docs/experiments/results/Experiment-04-Prelim-Results.md`
  - `docs/theories/Consolidated-Theory.md`
