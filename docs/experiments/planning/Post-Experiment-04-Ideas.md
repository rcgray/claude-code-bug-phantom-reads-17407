# Post-Experiment-04 Ideas

This document captures experiment ideas generated after analyzing the results of Experiment-Methodology-04's first trial run (`dev/misc/repro-attempts-04-firstrun/`). The unexpected universal failure across both Easy and Hard scenarios prompted a reassessment of our theoretical framework and identification of experiments that could refine our understanding.

**Naming Convention**: Experiments are named `Experiment-04[A-K]` to indicate they were conceived during the Methodology-04 generation of investigation.

## Background: How We Got Here

### The X + Y Model

Prior to Experiment-Methodology-04, our consolidated theory proposed that phantom reads occur when context consumption exceeds a threshold:

- **X** = Pre-operation context consumption (baseline + preloaded content via hoisting)
- **Y** = Operation context requirement (files read during the triggering action)
- **T** = Context window threshold (~200K tokens)

**Hypothesis**: Phantom reads occur when X + Y > T

### Experiment-Methodology-03 Results

Method-03 tested three scenarios with different X values (via preloaded content) but identical Y values:

| Scenario | X (Pre-op) | Y (Operation) | X + Y | Outcome |
| -------- | ---------- | ------------- | ----- | ------- |
| Easy     | 73K (37%)  | ~42K          | ~115K | SUCCESS |
| Medium   | 92K (46%)  | ~42K          | ~134K | SUCCESS |
| Hard     | 120K (60%) | ~42K          | ~162K | SUCCESS |

**Result**: 100% success across all scenarios. The X + Y model appeared validated—all totals remained under the ~200K threshold.

### Experiment-Methodology-04 Changes

To increase the likelihood of phantom reads in the Hard scenario, we added two additional specification files to increase Y:

- Added `module-epsilon.md` (7,666 tokens)
- Added `module-phi.md` (7,639 tokens)

This increased Y from ~42K tokens (7 files) to ~57K tokens (9 files).

### Experiment-Methodology-04 Results (First Run)

| Scenario | X (Pre-op) | Y (Operation) | X + Y | Outcome     |
| -------- | ---------- | ------------- | ----- | ----------- |
| Easy     | 73K (37%)  | ~57K          | ~130K | **FAILURE** |
| Hard     | 120K (60%) | ~57K          | ~177K | **FAILURE** |

**Result**: 100% failure across ALL scenarios (8/8 trials). Even Easy, with X + Y = 130K (well under the 200K threshold), failed consistently.

### The Critical Observation

The ONLY change between Method-03 (100% success) and Method-04 (100% failure) was the Y value:

| Variable | Method-03     | Method-04        |
| -------- | ------------- | ---------------- |
| Easy X   | 73K           | 73K (unchanged)  |
| Hard X   | 120K          | 120K (unchanged) |
| Y        | 42K (7 files) | 57K (9 files)    |
| T        | 200K          | 200K (unchanged) |

This suggests that **Y alone may have a threshold**, independent of X and T. The X + Y model may be incomplete or incorrect.

### Reset Pattern Anomaly

All Method-04 trials showed SINGLE_LATE reset patterns (resets occurring at 64-83% through the session). According to our previously validated Reset Timing Theory (31/31 trials, 100% accuracy), SINGLE_LATE patterns should predict SUCCESS. Yet all 8 trials FAILED.

This represents the first systematic violation of the Reset Timing Theory, suggesting the theory may be version-specific, context-dependent, or superseded by Y-size effects.

---

## Theoretical Questions

Based on these observations, we identified key questions requiring experimental investigation:

1. **Is there an absolute Y threshold?** Does Y have a ceiling (~40-50K tokens) beyond which phantom reads occur regardless of X?

2. **Does X matter at all?** If Y has an absolute threshold, is X relevant only insofar as it contributes to reset timing?

3. **Is T actually relevant?** Does the context window size affect phantom read occurrence, or is there an internal threshold independent of T?

4. **Does file count or token count matter?** Is the trigger the NUMBER of files read, or the TOTAL tokens read?

5. **Can hoisted content cause phantom reads?** Is there something special about agent-initiated reads vs `@`-hoisted content?

6. **Can batching or pacing mitigate phantom reads?** Would splitting Y into smaller operations avoid the threshold?

---

## Experiment Ideas

### Experiment-04A: Minimal X ("Easy-0")

**Concept**: Test Y=57K with X≈0 by using a setup command that pre-loads no files.

**Procedure**:
1. Start fresh session
2. Run `/setup-none` (generates Workscope ID but pre-loads no files)
3. Run `/context` (baseline)
4. Run `/analyze-wpd docs/wpds/pipeline-refactor.md` directly
5. Run `/context` (post-operation)
6. Prompt for phantom read self-report
7. Export session

**What It Tests**: Whether the Y threshold is absolute and independent of X.

**Expected Outcomes**:
- If FAILURE: Confirms Y has an absolute threshold (~40-50K) regardless of X
- If SUCCESS: Suggests X does matter, and Method-04 failures were due to X + Y interaction

**Priority**: **VERY HIGH** - This is the most direct test of the "Y-only" hypothesis.

**Preparation**: ~~None required. Simply omit the `/setup-easy` step in the existing Methodology-04 flow.~~

**CORRECTION (2026-01-26)**: Requires creation of `/setup-none` command. The `/setup-*` commands do more than pre-load files—they also generate the Workscope ID required for the trial. A `/setup-none` variant is needed that generates the Workscope ID but pre-loads no files, achieving X≈0 while maintaining the trial infrastructure.

---

### Experiment-04B: Find Exact Y Threshold (8 Files)

**Concept**: Test Y≈50K by adding only ONE of the new files (epsilon OR phi, not both).

**Procedure**:
1. Create a variant `/analyze-wpd-8files` command that reads 8 files (original 7 + epsilon)
2. Run standard Method-04 protocol with Easy and Hard scenarios
3. Compare outcomes to 7-file (Method-03) and 9-file (Method-04) results

**What It Tests**: The precise location of the Y threshold.

**Expected Outcomes**:
- If SUCCESS at Y=50K: Threshold is between 50K and 57K
- If FAILURE at Y=50K: Threshold is between 42K and 50K

**Priority**: **HIGH** - Narrows down the threshold boundary.

**Preparation**: ~~Modify `/analyze-wpd` command to list 8 files instead of 9 (remove `module-phi.md` from the list). Because `module-epsilon.md` and `module-phi.md` were not fully cross-integrated into the other spec files during Phase 10 implementation, they can be excluded simply by removing them from the command's file list—the Session Agent will not discover them via cross-references in other files.~~

**CORRECTION (2026-01-26)**: The original preparation assessment was incorrect. Testing with `/analyze-wpd-doc` (command without explicit file list) revealed that the Session Agent consistently discovers and reads `module-epsilon.md` and `module-phi.md` through cross-references in other spec files. The agent takes initiative to seek out relevant files regardless of command instructions.

**Revised Preparation**: Requires invasive surgical edits throughout the spec scenario:
1. Remove all cross-references to `module-phi.md` from other spec files
2. Ensure no spec file mentions or links to phi in a way that would prompt the agent to read it
3. Verify the scenario still functions coherently with phi removed

This is **Significant Preparation**, not minimal as originally assessed.

---

### Experiment-04C: Reduce Y to 7 Files (Method-03 Replication)

**Concept**: Revert to Method-03's 7-file Y and confirm success returns.

**Procedure**:
1. Modify `/analyze-wpd` to exclude epsilon and phi
2. Run standard protocol with Easy and Hard scenarios
3. Verify 100% success returns

**What It Tests**: Confirms that Y reduction restores success (sanity check).

**Expected Outcomes**:
- If SUCCESS: Confirms Y is the differentiating factor
- If FAILURE: Suggests environmental or version changes since Method-03

**Priority**: **LOW** - We already have Method-03 data. Only valuable as a sanity check if other experiments produce surprising results.

**Preparation**: ~~Similar to Experiment-04B—modify `/analyze-wpd` to list only the original 7 files (exclude both `module-epsilon.md` and `module-phi.md`). Same ease of modification applies since these files lack cross-references from other specs.~~

**CORRECTION (2026-01-26)**: The original preparation assessment was incorrect. See Experiment-04B correction—the Session Agent discovers and reads epsilon and phi through cross-references regardless of command instructions.

**Revised Preparation**: Requires invasive surgical edits throughout the spec scenario:
1. Remove all cross-references to both `module-epsilon.md` and `module-phi.md` from other spec files
2. Ensure no spec file mentions or links to epsilon or phi in a way that would prompt the agent to read them
3. Verify the scenario still functions coherently with both files removed

This is **Significant Preparation**, not minimal as originally assessed. Even more invasive than 04B since both files must be surgically removed from the cross-reference network.

---

### Experiment-04D: Maximum X, Minimal Y

**Concept**: Hoist ALL spec files during setup, leaving only the WPD for the operation phase.

**Procedure**:
1. Create `/setup-maxload` that hoists all 8 spec files (~52K tokens) via `@` notation
2. Use `/analyze-wpd-doc` (already created) which reads only `pipeline-refactor.md` (Y≈6K tokens) without listing additional spec files
3. Run the protocol: `/setup-maxload` → `/analyze-wpd-doc`
4. Compare outcomes with both Easy (lower X) and Hard (higher X) base scenarios

**What It Tests**: Whether hoisted content can cause phantom reads, and whether minimal Y succeeds even with extreme X.

**Expected Outcomes**:
- If SUCCESS with Easy+maxload: Confirms hoisted content is "safe" below context limit
- If SUCCESS with Hard+maxload: Confirms hoisting is safe even near context limit
- If FAILURE with Hard+maxload: Suggests hoisting CAN contribute when X approaches T
- If FAILURE with Easy+maxload: Suggests hoisted content can trigger phantom reads regardless of total

**Priority**: **HIGH** - Tests both the hoisting safety hypothesis and the Y-primacy hypothesis.

**Preparation**: Create `/setup-maxload` command that hoists all 8 spec files. The `/analyze-wpd-doc` command already exists and provides minimal Y (WPD only, no spec file list).

**Note**: This experiment may also cover Experiment-04H (Intentional Early Reset) if the maxload setup pushes context high enough to trigger a reset before the operation phase.

---

### Experiment-04E: Batch Y via Multiple Operations

**Concept**: Split the 9-file Y into multiple smaller operations with pauses between.

**Procedure**:
1. Create a modified workflow:
   - First operation: Read WPD + 3 spec files
   - User runs `/context`
   - Second operation: Read 3 more spec files
   - User runs `/context`
   - Third operation: Read final 3 spec files
2. Test with Easy scenario (lower X)

**What It Tests**: Whether the trigger is single-operation size vs cumulative total.

**Expected Outcomes**:
- If SUCCESS: Suggests batching can mitigate phantom reads; the trigger is per-operation
- If FAILURE: Suggests cumulative total or rate matters more than per-operation size

**Priority**: **MEDIUM** - Valuable for mitigation strategies, but may be confounded by the pause/interaction pattern.

**Note**: This effectively transfers files from Y→X between batches, which may complicate interpretation.

**Preparation**: Requires creating multiple commands for each batch. However, this experiment may be redundant with Experiment-04D—if D succeeds by moving all spec files to hoisting (X) and leaving minimal Y, it demonstrates that batching via hoisting works. The remaining question would be whether agent-initiated batching (multiple separate read operations) has the same effect, which is difficult to control.

**Status**: **UNCERTAIN** - May be covered by Experiment-04D results. Defer unless D produces surprising results.

---

### Experiment-04F: File Count vs Token Count

**Concept**: Test whether the trigger is file count or total tokens by using fewer, larger files.

**Procedure**:
1. Create consolidated spec files:
   - `mega-spec-1.md`: Concatenate alpha + beta + gamma (~20K tokens)
   - `mega-spec-2.md`: Concatenate epsilon + phi + integration + compliance (~25K tokens)
   - `data-pipeline-overview.md`: Keep as-is (~7K tokens)
2. Modify `/analyze-wpd` to read 4 files (WPD + 3 mega-specs) totaling ~57K tokens
3. Run standard protocol

**What It Tests**: Whether the phantom read trigger is file count or token count.

**Expected Outcomes**:
- If SUCCESS with 4 files (57K tokens): File count is the trigger, not token count
- If FAILURE with 4 files: Token count (or both) is the trigger

**Priority**: **HIGH** - Directly tests a fundamental question about the trigger mechanism.

**Preparation**: Requires significant file surgery:
1. Create consolidated "mega-spec" files by concatenating existing specs
2. Update all internal references within the consolidated files to avoid pointing to the original separate files
3. Modify `/analyze-wpd` to reference only the mega-specs

This is the most labor-intensive preparation among all experiments.

---

### Experiment-04G: Sequential vs Parallel Reads

**Concept**: Test whether read pattern (parallel batch vs sequential) affects outcomes.

**Procedure**:
1. Create `/analyze-wpd-parallel` that requests all file reads in a single tool-use response
2. Create `/analyze-wpd-sequential` that explicitly reads one file, processes, then reads the next
3. Compare outcomes on same scenario

**What It Tests**: Whether the harness handles parallel batched reads differently than sequential accumulation.

**Expected Outcomes**:
- If different outcomes: Read pattern affects phantom read risk
- If same outcomes: Pattern doesn't matter; it's purely about total volume

**Priority**: **MEDIUM** - Useful for understanding harness behavior, but may be difficult to control agent behavior precisely.

**Preparation**: Create `/analyze-wpd-sequential` command that instructs the Session Agent to read files one at a time with explicit pauses or user confirmation between reads. The current default behavior appears to be parallel reads (multiple Read tool calls in a single response) that resolve to sequential reporting.

**Note**: Controlling agent read behavior is inherently difficult. The command can request sequential reads, but agents may not comply consistently.

---

### Experiment-04H: Intentional Early Reset

**Concept**: Force an early context reset, then perform the operation in the "clean" post-reset window.

**Procedure**:
1. Create a setup phase that pushes context to ~130K (via large hoisted content or conversation padding)
2. Trigger a natural reset (continue conversation until reset occurs)
3. Immediately run `/analyze-wpd` in the fresh post-reset context
4. Compare outcomes

**What It Tests**: Whether a fresh context post-reset can handle Y=57K that would otherwise fail.

**Expected Outcomes**:
- If SUCCESS: Early reset creates a protected window; timing is critical
- If FAILURE: Y threshold is absolute regardless of reset state

**Priority**: **MEDIUM** - Tests the "clean gap" hypothesis from earlier theories.

**Preparation**: Requires research to understand how to reliably force a context reset. We don't fully understand the reset trigger mechanism. Options include:
- Push context very high via hoisted content and hope a reset occurs
- Engage in extended conversation to accumulate context
- Use `/compact` command explicitly (but this is user-initiated, not natural)

**Status**: **UNCERTAIN** - May be covered by Experiment-04D. If `/setup-maxload` pushes context high enough to trigger a reset, and then the minimal Y operation succeeds in the post-reset window, that would effectively answer this experiment's question.

---

### Experiment-04I: Partial MCP Hybrid

**Concept**: Use MCP filesystem for some reads and native Read for others within the same operation.

**Procedure**:
1. Modify `/analyze-wpd` to use MCP for half the spec files and native Read for the other half
2. Track which files experience phantom reads
3. Compare MCP-read files vs native-read files

**What It Tests**: Whether MCP reads are immune to phantom reads within an operation that triggers them.

**Expected Outcomes**:
- If MCP files succeed, native files fail: Confirms MCP bypasses the issue at the read level
- If all fail or all succeed: Suggests the trigger is operation-level, not read-level

**Priority**: **MEDIUM** - Useful for understanding the mechanism, but primarily confirms the workaround rather than advancing theory.

**Preparation**: Create `/analyze-wpd-mcp` command that instructs the Session Agent to use MCP filesystem tools for some reads and native Read for others. Additionally, consider using harness permission settings to block native Read access to certain files, forcing MCP usage.

**Note**: Controlling which tool an agent uses is inherently difficult. Blocking certain files from native Read access may be more reliable than instruction-based approaches.

---

### Experiment-04J: Examine Persisted-Output Files

**Concept**: Examine the actual persisted-output files written by the harness to understand the mechanism.

**Procedure**:
1. After a phantom read trial, examine the `tool-results/` directory
2. Verify that file content was actually written to the persisted-output files
3. Check file sizes, timestamps, and content integrity
4. Compare successful vs failed trials

**What It Tests**: Whether the persisted-output mechanism is working correctly (content is saved) and the failure is in the follow-up read.

**Expected Outcomes**:
- If content present: Confirms the write succeeds but agent doesn't follow up
- If content missing/truncated: Suggests a deeper harness issue

**Priority**: **LOW** - More diagnostic than experimental. Useful for understanding but doesn't change theory.

**Preparation**: None required. Can be performed using existing trial data from `dev/misc/repro-attempts-04-firstrun/` and other collections. Simply examine the `tool-results/` directories within each trial.

**Note**: This diagnostic work has not been formally documented, though the Investigation Journal (2026-01-13 entry) notes that `tool-results/` directories exist in trial data. Examining these files would confirm whether the persisted-output mechanism successfully writes content (indicating the failure is in agent follow-up) or fails to write (indicating a deeper harness issue).

---

### Experiment-04K: Larger Context Window (1M Model)

**Concept**: Run the same experiments with a 1M context model to test T's relevance.

**Procedure**:
1. Switch to `claude-sonnet-4-5-20250929[1m]` (1M context)
2. Run Method-04 protocol (Easy and Hard scenarios)
3. Compare outcomes to 200K model results

**What It Tests**: Whether the context window size (T) affects phantom read occurrence.

**Expected Outcomes**:
- If same failures at Y=57K: T is irrelevant; internal threshold governs
- If success: T matters; the 200K model has a lower effective threshold

**Priority**: **MEDIUM** - High conceptual value but introduces confounds:
- Different model may have different behavior
- Harness may have model-specific optimizations
- Results may not be directly comparable

**Caution**: Interpret results carefully due to potential confounding factors.

**Preparation**: None required. Simply switch the model configuration and repeat the Methodology-04 protocol.

**⚠️ SCOPE LIMITATION**: This experiment is a **one-time diagnostic** to validate whether T is a relevant variable in the X+Y model. The 1M model is **NOT a direction to pursue** for this investigation. Regardless of 04K's outcome, this project must remain focused on the **200K model**, which represents the default user experience. Do not propose further 1M model experiments or frame the 1M model as a recommended workaround for reproduction scenarios.

---

### Experiment-04L: Hoisted Content Re-Read Behavior

**Concept**: Verify that files pre-loaded via hoisting are not re-injected into context when the Session Agent subsequently issues Read commands for those same files.

**Procedure**:
1. Run trials with `/setup-maxload` (hoists all 8 spec files) followed by `/analyze-wpd` (explicitly lists the 8 files)
2. Run trials with `/setup-maxload` followed by `/analyze-wpd-doc` (does NOT list files, agent discovers them)
3. Compare context usage between both command variants
4. Measure whether explicit file listing causes context duplication

**What It Tests**: Whether the Claude Code harness is intelligent enough to recognize that a file already exists in context and avoid re-injecting it when a Read is issued.

**Expected Outcomes**:
- If similar context usage: Confirms harness avoids redundant reads; `/analyze-wpd` is safe to use after hoisting
- If higher context with `/analyze-wpd`: Suggests explicit file listing causes re-reads; `/analyze-wpd-doc` is required after hoisting

**Priority**: **HIGH** - Foundational for Experiment-04D. Must confirm this behavior before running 04D with confidence that explicit file listing doesn't cause context duplication.

**Preparation**: The `/analyze-wpd-doc` command already exists. No additional preparation required.

**Note**: This behavior has been observed anecdotally during normal agent interactions, but this experiment provides formal confirmation. Results directly inform the design of Experiment-04D, where we need to know whether using `/analyze-wpd` (with explicit file list) after `/setup-maxload` (which hoists those same files) would cause redundant context consumption.

---

### Experiment-04M: X Boundary Exploration (Intermediate Preload Values)

**Concept**: Find where in the X range between `/setup-none` (X≈23K) and `/setup-easy` (X≈73K) the transition from success to failure occurs when Y=57K.

**Background**: We know:
- `/setup-none` + Y=57K → SUCCESS (04A): X ≈ 23K (0 preload + 23K baseline)
- `/setup-easy` + Y=57K → FAILURE (Method-04): X ≈ 73K (35K preload + 23K baseline + 15K overhead)

The transition point lies somewhere in the 23K-73K X range. Understanding where this boundary is helps quantify the X+Y interaction and potentially enables calibration of a reliable "Medium" reproduction scenario (target 50% failure rate).

**Token Accounting Reference** (see also Investigation-Journal.md):
- **Baseline**: ~23K tokens (harness system prompt, tools, etc.) - present in ALL sessions
- **Preload**: File tokens hoisted via `@` notation
- **Overhead**: ~38-42% additional tokens observed beyond file content (reading overhead, message formatting)
- **X (total)**: Baseline + Preload + Overhead

**Available Single-File Preload Options**:

| File | File Tokens | Expected X (total observed) |
|------|-------------|----------------------------|
| `architecture-deep-dive.md` | 14.7K | ~44K |
| `operations-manual-exceptions.md` | 15.6K | ~45K |
| `troubleshooting-compendium.md` | 18.5K | ~49K |
| `operations-manual-standard.md` | 19.3K | ~50K |

**Procedure**:
1. Create `/setup-mid` command that preloads ONE file (recommend `operations-manual-standard.md` for X≈50K, roughly midpoint of the gap)
2. Run 4-6 trials: `/setup-mid` → `/context` → `/analyze-wpd` → `/context` → self-report → `/export`
3. Record outcomes and compare to 04A (X≈23K, SUCCESS) and Method-04 Easy (X≈73K, FAILURE)
4. If results are mixed (some success, some failure), this X value may be near the boundary
5. If all succeed, try a higher preload; if all fail, try a lower preload

**What It Tests**: Where in the X range does Y=57K become dangerous?

**Expected Outcomes**:
- If X≈50K + Y=57K → **ALL SUCCESS**: Boundary is between 50K and 73K; consider testing X≈60K
- If X≈50K + Y=57K → **ALL FAILURE**: Boundary is between 23K and 50K; consider testing X≈35K
- If X≈50K + Y=57K → **MIXED**: X≈50K may be near the boundary; useful for "Medium" scenario calibration

**Priority**: **HIGH** - Directly addresses the X+Y interaction and enables scenario calibration.

**Preparation**: Minimal - create `/setup-mid` command that hoists a single file. Can iterate with different files to test different X values.

**Recommended First Test**: Use `operations-manual-standard.md` (19.3K file tokens → X≈50K) as it's roughly the midpoint between setup-none and setup-easy.

**Follow-up Variants** (if needed):
- `/setup-low`: Use `architecture-deep-dive.md` (14.7K) for X≈44K
- `/setup-high`: Combine two smaller files for X≈60K (e.g., architecture + troubleshooting)

---

## Preparation Requirements and Ease of Running

Based on the preparation requirements identified above, experiments are grouped by ease of execution:

### Immediate (No Preparation Required)

| Experiment | Description              | Notes                             |
| ---------- | ------------------------ | --------------------------------- |
| **04J**    | Examine Persisted Files  | Uses existing trial data          |
| **04K**    | 1M Context Model         | Swap model, run same protocol     |
| **04L**    | Hoisted Re-Read Behavior | `/analyze-wpd-doc` already exists |

**Note (2026-01-26)**: 04A moved to "Minimal Preparation" below—requires creation of `/setup-none` command.

### Minimal Preparation (Command Changes Only)

| Experiment | Description          | Preparation                                                |
| ---------- | -------------------- | ---------------------------------------------------------- |
| **04A**    | Minimal X            | Create `/setup-none` (Workscope ID only, no file hoisting) |
| **04D**    | Max X, Minimal Y     | Create `/setup-maxload`; `/analyze-wpd-doc` already exists |
| **04M**    | Intermediate X       | Create `/setup-mid` (single-file preload for X≈50K)        |

~~**Note on 04B/04C**: These are simple because `module-epsilon.md` and `module-phi.md` were not fully cross-integrated into other specs during Phase 10 implementation. They can be excluded by editing the command's file list without triggering the Session Agent to discover them via cross-references.~~

**CORRECTION (2026-01-26)**: 04B and 04C have been moved to "Significant Preparation" below. Testing revealed that the Session Agent discovers and reads epsilon/phi through cross-references regardless of whether they are listed in the command.

### Moderate Preparation

| Experiment | Description            | Preparation                                    |
| ---------- | ---------------------- | ---------------------------------------------- |
| **04I**    | Partial MCP Hybrid     | Create command + configure harness permissions |
| **04G**    | Sequential vs Parallel | Create command to force sequential reads       |

### Significant Preparation

| Experiment | Description          | Preparation                                                        |
| ---------- | -------------------- | ------------------------------------------------------------------ |
| **04F**    | File Count vs Tokens | Create mega-spec files + update all internal references            |
| **04B**    | 8-File Threshold     | Remove all cross-references to phi from other spec files           |
| **04C**    | 7-File Confirmation  | Remove all cross-references to epsilon + phi from other spec files |

**Note on 04B/04C (added 2026-01-26)**: Originally assessed as "Minimal Preparation," but testing revealed the Session Agent discovers omitted files through cross-references regardless of command instructions. Requires surgical removal of cross-references throughout the spec scenario.

### Uncertain / May Be Redundant

| Experiment | Description             | Notes                                                            |
| ---------- | ----------------------- | ---------------------------------------------------------------- |
| **04E**    | Batch Y                 | May be covered by 04D results                                    |
| **04H**    | Intentional Early Reset | May be covered by 04D results; requires reset mechanism research |

---

## Priority Summary

### Completed Experiments

| ID  | Experiment          | Result | Key Finding |
| --- | ------------------- | ------ | ----------- |
| 04A | Minimal X (Easy-0)  | ✅ 6/6 SUCCESS | Y=57K succeeds when X≈23K; Y threshold is NOT absolute |
| 04D | Max X, Minimal Y    | ✅ SUCCESS | Hoisting is safe; minimal Y succeeds even at high X |
| 04K | 1M Context Model    | ✅ 6/6 SUCCESS | T matters; 1M model avoids phantom reads *(diagnostic only, out of scope)* |
| 04L | Hoisted Re-Read     | ✅ SUCCESS | Harness avoids redundant reads for hoisted files |

### Tier 1 - Critical Experiments (Run Next)

| ID  | Experiment              | Key Question                          | ROI       | Ease      |
| --- | ----------------------- | ------------------------------------- | --------- | --------- |
| 04M | Intermediate X          | Where in 23K-73K does Y=57K fail?     | Very High | Minimal   |
| 04C | 7-File Sanity Check     | Confirm Method-03 behavior still holds | High     | Git branch |
| 04F | File Count vs Tokens    | Is trigger file count or token count? | High      | Git branch |

**04M**: Create `/setup-mid` to test X≈50K with Y=57K. Maps the X boundary for the danger zone.

**04C/04F via Git Branch**: Instead of surgical edits, branch the repo and restore pre-epsilon/phi state. Run 04C first (sanity check), then 04F (mega-spec consolidation).

### Tier 2 - Important Experiments

| ID  | Experiment             | Key Question                | ROI    | Ease      |
| --- | ---------------------- | --------------------------- | ------ | --------- |
| 04G | Sequential vs Parallel | Does read pattern matter?   | Medium | Moderate  |
| 04B | 8-File Y Threshold     | Where is Y boundary?        | Medium | Git branch |

**04G**: Tests the Dynamic Context Pressure hypothesis (accumulation rate).

**04B**: If 04C/04F are informative, 04B may help narrow the Y threshold further.

### Tier 3 - Lower Priority

| ID  | Experiment              | Key Question                | ROI | Notes |
| --- | ----------------------- | --------------------------- | --- | ----- |
| 04I | Partial MCP Hybrid      | Is MCP immunity read-level? | Low | Mechanism investigation |
| 04J | Examine Persisted Files | Diagnostic only             | Low | Uses existing trial data |
| 04E | Batch Y                 | Covered by 04D results      | Low | Likely redundant |
| 04H | Intentional Early Reset | Covered by 04D results      | Low | Likely redundant |

These experiments are only valuable in specific circumstances or may be redundant with other experiments.

**Note (2026-01-26)**: 04C ease updated from "Minimal" to "Significant" due to required surgical removal of cross-references (see experiment definition).

---

## Recommended Execution Plan

### Completed Phases

**Phase 1: Y Threshold Independence** - ✅ COMPLETE
- 04A (Minimal X): Confirmed Y=57K succeeds when X≈23K
- **Finding**: Y threshold is NOT absolute; it depends on X

**Phase 2: Hoisting Behavior** - ✅ COMPLETE
- 04L (Hoisted Re-Read): Confirmed harness avoids redundant reads
- 04D (Max X, Minimal Y): Confirmed hoisting is safe; minimal Y succeeds at any X

**Phase 3: Context Window Relevance** - ✅ COMPLETE (Diagnostic Only)
- 04K (1M Model): Confirmed T matters; 1M model avoids phantom reads
- **⚠️ Note**: This was diagnostic only. The 1M model is NOT a direction to pursue.

### Current Phase: Map X+Y Interaction Surface

**Step 1: Experiment-04M (X Boundary Exploration)**

1. Create `/setup-mid` command that preloads `operations-manual-standard.md` (19.3K → X≈50K)
2. Run 4-6 trials with Y=57K (9 files)
3. Based on results:
   - If all SUCCESS: Boundary is between 50K and 73K; consider `/setup-high` (X≈60K)
   - If all FAILURE: Boundary is between 23K and 50K; consider `/setup-low` (X≈44K)
   - If MIXED: X≈50K is near the boundary; useful for "Medium" scenario calibration

**Step 2: Experiments 04C/04F via Git Branch**

1. Branch the repository
2. Restore `docs/specs/` and `/analyze-wpd` to pre-epsilon/phi state (7 files, ~42K Y)
3. Run **04C** (sanity check): Confirm Y=42K still succeeds at all X levels
4. Run **04F** (file count vs tokens): Create mega-specs (~57K in 4 files) and test
   - If SUCCESS: File count matters (fewer files is safer)
   - If FAILURE: Token count matters (or both)

**Step 3: Experiment-04G (Sequential vs Parallel)** - If time permits

Test the Dynamic Context Pressure hypothesis by forcing sequential reads with pauses.

---

## Success Criteria

After completing these experiments, we should be able to answer:

1. ~~**What is the Y threshold?**~~ → Reframed: How do X and Y interact?
2. ~~**Does X matter?**~~ → **ANSWERED**: Yes, critically. Low X makes high Y safe.
3. ~~**Does T matter?**~~ → **ANSWERED**: Yes. 1M model avoids phantom reads.
4. **What triggers the threshold?** (File count, token count, or both?) - 04F addresses this
5. **Can we reliably produce 0%, 50%, 100% failure rates?** - 04M helps calibrate scenarios

This understanding will enable us to create reliable reproduction scenarios and potentially identify mitigation strategies.

---

*Document created: 2026-01-24*
*Updated: 2026-01-24 (added preparation requirements and ease of running assessment)*
*Updated: 2026-01-26 (added Experiment-04L: Hoisted Content Re-Read Behavior)*
*Updated: 2026-01-26 (corrected 04B/04C preparation: Session Agent discovers omitted files via cross-references)*
*Updated: 2026-01-26 (corrected 04A preparation: requires `/setup-none` command for Workscope ID generation)*
*Updated: 2026-01-26 (added scope limitation note to 04K: 1M model is diagnostic only, not a direction to pursue)*
*Updated: 2026-01-26 (added Experiment-04M: X Boundary Exploration with intermediate preload values)*
*Updated: 2026-01-26 (overhauled Priority Summary and Execution Plan to reflect completed experiments and new priorities)*
*Updated: 2026-01-26 (added git-branch approach for 04B/04C/04F as alternative to surgical edits)*
*Based on analysis of: `dev/misc/repro-attempts-04-firstrun/` (8 trials)*
