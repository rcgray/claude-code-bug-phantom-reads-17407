# Barebones-2120 Experiment Planning

**Experiment ID**: Barebones-2120
**Collection**: `dev/misc/repro-attempts-04-2120/`
**Date Conducted**: 2026-01-27
**Claude Code Version**: 2.1.20
**Status**: Trials complete, analysis pending

---

## Executive Summary

This experiment tests whether the Phantom Reads bug manifests in Claude Code version 2.1.20, representing a 14-version jump from our locked testing version (2.1.6). Using the same barebones environment and protocol as Barebones-216, this experiment isolates the version variable.

**High-Level Results**: 0 failures, 5 successes (0% failure rate)

This dramatic reversal from the 100% failure rate observed in 2.1.6 (among valid trials) suggests Anthropic may have changed something significant in the harness between versions 2.1.6 and 2.1.20. Whether this represents a deliberate fix, an incidental optimization, or a threshold shift requires careful analysis.

---

## Background and Rationale

### Version History Context

The Phantom Reads investigation began when the bug was first observed in Claude Code version 2.1.3 in January 2026. During initial exploration:

- The bug was traced back to the 2.0.59 timeframe (Era 1 → Era 2 transition)
- Two distinct phantom read mechanisms were identified:
  - **Era 1** (≤2.0.59): `[Old tool result content cleared]` markers
  - **Era 2** (≥2.0.60): `<persisted-output>` markers
- Testing confirmed the bug persisted through version 2.1.6
- The investigation locked to version 2.1.6 to ensure reproducibility

Since locking to 2.1.6, Claude Code has continued development through version 2.1.20. To remain relevant and ensure our findings apply to current users, we must verify whether the bug persists in newer versions.

### Why This Matters

1. **Relevance**: If phantom reads are fixed in 2.1.20, users on current versions may not experience the bug
2. **Investigation direction**: A fix would shift focus to documenting version boundaries rather than trigger mechanisms
3. **Workaround necessity**: The MCP Filesystem workaround may no longer be needed for current versions
4. **Reproduction case**: Our scenarios may need version constraints in documentation

### Experimental Design

This experiment uses the IDENTICAL setup to Barebones-216:
- Same barebones repository (no WSD framework, minimal files)
- Same protocol (Experiment-Methodology-04 with `/setup-hard`)
- Same file set (12 spec files + WPD)
- ONLY difference: Claude Code version (2.1.20 vs 2.1.6)

This isolation ensures any outcome differences are attributable to the version change, not environmental factors.

---

## Experimental Setup

### Environment Configuration

The barebones repository from Barebones-216 was reused without modification:

```
barebones-phantom-reads/
├── .claude/
│   └── commands/
│       ├── analyze-wpd.md
│       ├── setup-easy.md
│       ├── setup-hard.md
│       ├── setup-medium.md
│       └── setup-none.md
├── CLAUDE.md
├── docs/
│   ├── specs/
│   │   ├── architecture-deep-dive.md
│   │   ├── compliance-requirements.md
│   │   ├── data-pipeline-overview.md
│   │   ├── integration-layer.md
│   │   ├── module-alpha.md
│   │   ├── module-beta.md
│   │   ├── module-epsilon.md
│   │   ├── module-gamma.md
│   │   ├── module-phi.md
│   │   ├── operations-manual-exceptions.md
│   │   ├── operations-manual-standard.md
│   │   └── troubleshooting-compendium.md
│   └── wpds/
│       └── pipeline-refactor.md
└── src/
    └── collect_trials.py

7 directories, 20 files
```

### Version Upgrade Process

1. Used `cc_version.py --install 2.1.20` to upgrade from 2.1.6
2. Verified installation via `cc_version.py --status`
3. Confirmed version in Claude Code startup banner
4. Ran trials back-to-back with Barebones-216 using scripted protocol

### Protocol

Identical to Barebones-216 (Experiment-Methodology-04 7-step protocol):

1. Start fresh Claude Code session
2. Run `/context` (baseline measurement)
3. Run `/setup-hard` (preload ~120K tokens)
4. Run `/context` (post-setup measurement)
5. Run `/analyze-wpd docs/wpds/pipeline-refactor.md` (trigger operation)
6. Run `/context` (post-analysis measurement)
7. Self-report prompt (query Session Agent report of phantom read occurrence)
8. Export chat and collect trial artifacts

### Variables

| Variable            | Value        | Notes                             |
| ------------------- | ------------ | --------------------------------- |
| X (pre-op context)  | ~120K tokens | Via `/setup-hard` hoisting        |
| Y (operation files) | ~57K tokens  | 9 spec files read during analysis |
| T (context window)  | 200K tokens  | Standard model                    |
| Claude Code version | **2.1.20**   | Upgraded from 2.1.6               |

---

## Results Summary

| Trial ID        | Outcome | Notes                     |
| --------------- | ------- | ------------------------- |
| 20260127-095002 | SUCCESS | No phantom reads reported |
| 20260127-100209 | SUCCESS | No phantom reads reported |
| 20260127-100701 | SUCCESS | No phantom reads reported |
| 20260127-100944 | SUCCESS | No phantom reads reported |
| 20260127-101305 | SUCCESS | No phantom reads reported |

**Failure Rate**: 0% (0/5)
**Success Rate**: 100% (5/5)

**Additional Validation**: The User ran additional informal trials beyond these 5 to confirm the pattern. All showed unanimous success.

### Comparison to Barebones-216

| Metric       | Barebones-216 (v2.1.6)     | Barebones-2120 (v2.1.20) |
| ------------ | -------------------------- | ------------------------ |
| Failure Rate | 100% (4/4 valid trials)    | **0% (0/5)**             |
| Success Rate | 0% (0/4 valid trials)      | **100% (5/5)**           |
| Protocol     | Identical                  | Identical                |
| Environment  | Identical                  | Identical                |
| Version      | 2.1.6                      | 2.1.20                   |

**Note on Barebones-216**: One trial (092331) was excluded as a protocol violation—the agent failed to read 3 of 8 specified files. Among valid trials that followed the protocol, Barebones-216 showed 100% failure rate.

The dramatic reversal (100% → 0% failure) with only the version changing strongly suggests a harness-level change between versions.

---

## Research Questions

### RQ-BB2120-1: Did Anthropic fix or mitigate the Phantom Reads bug?

**Status**: OPEN - Requires analysis

**Possible interpretations**:

1. **Deliberate fix**: Anthropic identified and fixed the phantom reads mechanism
2. **Incidental fix**: A related change (optimization, refactoring) inadvertently resolved the issue
3. **Threshold shift**: Context management thresholds changed, making our scenario no longer trigger the bug
4. **Mechanism change**: The bug still exists but manifests differently (new markers, different conditions)

**Analysis approach**:
1. Compare context consumption patterns between 2.1.6 and 2.1.20 trials
2. Look for evidence of changed overhead or thresholds
3. Examine whether agents receive actual content or new marker types
4. Review Claude Code release notes for relevant changes

### RQ-BB2120-2: How do context consumption patterns compare to 2.1.6?

**Status**: OPEN - Requires analysis

**Hypothesis**: If phantom reads were fixed via optimization, we might see:
- Lower overhead (the ~40% unaccounted overhead reduced)
- Different baseline context
- Changed relationship between hoisted content and total context

**Analysis approach**:
1. Extract X values from all 5 trials
2. Compare to Barebones-216 X values
3. Calculate overhead percentages
4. Look for systematic differences

**Key comparison points**:
| Metric         | Expected if threshold shift | Expected if true fix |
| -------------- | --------------------------- | -------------------- |
| Baseline       | Lower                       | Similar              |
| X after setup  | Lower                       | Similar              |
| X + Y total    | Lower                       | Similar              |
| Reset patterns | Different                   | Similar              |

### RQ-BB2120-3: Do reset patterns differ between versions?

**Status**: OPEN - Requires analysis

**Background**: The Reset Timing Theory established that mid-session resets (50-90%) correlate with phantom reads. If 2.1.20 eliminated phantom reads, reset behavior may have changed.

**Possible findings**:
1. **Fewer resets overall**: Harness manages context more efficiently
2. **Different timing**: Resets occur at safer times (early/late only)
3. **No resets**: Context never reaches reset threshold
4. **Same patterns, different outcomes**: Resets occur but don't cause phantom reads

**Analysis approach**:
1. Extract reset counts and positions from `trial_data.json`
2. Classify patterns (EARLY_PLUS_LATE, SINGLE_LATE, etc.)
3. Compare to Barebones-216 patterns
4. Correlate with success outcomes

### RQ-BB2120-4: Has the phantom read mechanism changed (Era 3)?

**Status**: OPEN - Requires analysis

**Background**: The transition from Era 1 (`[Old tool result content cleared]`) to Era 2 (`<persisted-output>`) occurred around version 2.0.60. It's possible another mechanism change occurred.

**What to look for**:
- New marker types in tool results
- Different deferred read handling
- Changed persisted-output file locations
- New self-report patterns from agents

**Analysis approach**:
1. Review chat exports for any unusual patterns
2. Check if agents mention any new markers
3. Examine tool-results directories in session data
4. Compare to Era 2 patterns in Barebones-216

### RQ-BB2120-5: Did agents receive actual file content?

**Status**: OPEN - Requires analysis

**The key verification**: In 2.1.6 failures, agents received `<persisted-output>` markers instead of file content. In 2.1.20 successes, we need to verify agents received ACTUAL content.

**Evidence to look for**:
1. Agents quoting specific content from spec files
2. Accurate analysis referencing real file details
3. Correct line numbers and section references
4. No self-reported phantom reads

**Analysis approach**:
1. Review chat exports for content accuracy
2. Compare quoted content to actual spec files
3. Check self-report questions for "no phantom reads" confirmation
4. Look for any partial phantom reads (some files affected)

### RQ-BB2120-6: Can we re-establish a failure case in 2.1.20?

**Status**: OPEN - Future experiment required

**Rationale**: If 2.1.20 merely shifted thresholds (rather than fixing the bug), we should be able to trigger phantom reads by increasing context pressure.

**Proposed approaches**:
1. **Increase X**: Use a new `/setup-extreme` with more hoisted content
2. **Increase Y**: Add more spec files to the analysis operation
3. **Both**: Push X+Y higher until phantom reads occur or context saturates

**Success criteria**: If we can trigger phantom reads in 2.1.20 with higher thresholds, it confirms a threshold shift rather than a fix. If we cannot trigger them even at context saturation, it suggests a more fundamental fix.

### RQ-BB2120-7: What changed between 2.1.6 and 2.1.20?

**Status**: OPEN - Research required

**Approach**:
1. Review Claude Code changelog/release notes for versions 2.1.7 through 2.1.20
2. Look for mentions of:
   - Context management
   - Tool result handling
   - Read operation optimizations
   - Memory or caching changes
3. Identify candidate changes that could affect phantom reads

**If no relevant changes documented**: The fix may have been incidental or internal without public documentation.

### RQ-BB2120-8: At which version did the behavior change?

**Status**: OPEN - Binary search experiment required

**Rationale**: Knowing the exact version boundary helps:
- Identify the specific change that affected phantom reads
- Document precise version requirements for reproduction
- Understand the scope of the fix

**Proposed approach**: Binary search between 2.1.6 and 2.1.20:
1. Test 2.1.13 (midpoint)
2. If fails: test 2.1.17 (upper midpoint)
3. If succeeds: test 2.1.10 (lower midpoint)
4. Continue until boundary identified

**Estimated trials**: 4-5 versions × 3 trials each = 12-15 trials

---

## Analysis Methodology

### Phase 1: Pre-Processing (COMPLETED)

The `/update-trial-data` command has been run on all trials, generating `trial_data.json` files.

### Phase 2: Quantitative Comparison

Create side-by-side comparison table:

| Metric              | Barebones-216 (2.1.6) | Barebones-2120 (2.1.20) | Delta |
| ------------------- | --------------------- | ----------------------- | ----- |
| Baseline context    | TBD                   | TBD                     | TBD   |
| Post-setup X        | TBD                   | TBD                     | TBD   |
| Post-analysis total | TBD                   | TBD                     | TBD   |
| Reset count (avg)   | TBD                   | TBD                     | TBD   |
| Reset count (range) | TBD                   | TBD                     | TBD   |
| Failure rate        | 100% (4/4 valid)      | 0%                      | -100% |

**Statistical significance**: With 4 valid trials in 2.1.6 and 5 trials in 2.1.20, the difference (4/4 vs 0/5) has p < 0.01 by Fisher's exact test, representing a highly significant result.

### Phase 3: Pattern Analysis

For each trial:
1. Classify reset pattern
2. Calculate reset positions as % of session
3. Identify any mid-session resets
4. Note any anomalies

**Expected pattern comparison**:
| Pattern         | 2.1.6 Trials | 2.1.20 Trials |
| --------------- | ------------ | ------------- |
| EARLY_PLUS_LATE | TBD          | TBD           |
| SINGLE_LATE     | TBD          | TBD           |
| MID_SESSION     | TBD          | TBD           |
| NONE            | TBD          | TBD           |

### Phase 4: Qualitative Analysis

**Chat export review**:
1. Verify agents received actual file content (accurate quotes, correct details)
2. Check for any new marker types or unusual patterns
3. Confirm self-report indicates no phantom reads
4. Note any behavioral differences from 2.1.6 trials

### Phase 5: Threshold Analysis

If context patterns differ between versions:
1. Calculate the "effective overhead" difference
2. Estimate how much our scenario would need to increase to trigger phantom reads in 2.1.20
3. Design follow-up experiment to test this estimate

### Phase 6: Synthesis

1. Determine most likely explanation (fix vs threshold shift vs mechanism change)
2. Update Research-Questions.md with findings
3. Update Investigation-Journal.md
4. Recommend next steps

---

## Implications and Next Steps

### If analysis confirms threshold shift:

1. **Re-calibrate scenarios**: Design new `/setup-extreme` or add spec files to push thresholds higher
2. **Document version dependency**: Note that reproduction requires specific versions or higher thresholds
3. **Continue investigation**: The bug exists but our trigger is outdated

### If analysis suggests deliberate fix:

1. **Verify with Anthropic**: Check if fix was intentional or if they acknowledge the issue
2. **Document version boundary**: Identify exactly which version introduced the fix
3. **Update documentation**: Note that workarounds may not be needed for versions ≥X
4. **Shift investigation focus**: Document the fix rather than continuing trigger research

### If mechanism changed (Era 3):

1. **Identify new markers**: Document the new phantom read indicators
2. **Update self-report prompts**: Adjust questions to detect new mechanism
3. **Re-run trials**: Test if new mechanism can be triggered
4. **Update theories**: Revise theoretical framework for new behavior

---

## Expected Deliverables

1. **Analysis document**: `docs/experiments/results/Barebones-2120-Analysis.md`
2. **Comparative analysis**: Side-by-side with Barebones-216 findings
3. **Investigation Journal update**: New entry documenting version behavior change
4. **Research Questions update**: Status changes and new questions
5. **Recommended next experiment**: Based on findings (threshold push, version search, etc.)

---

## Dependencies and Prerequisites

**Required files for analysis**:
- `dev/misc/repro-attempts-04-2120/*/trial_data.json` (5 files)
- `dev/misc/repro-attempts-04-2120/*/chat-export.md` (5 files)
- `dev/misc/repro-attempts-04-barebones/*/trial_data.json` (for comparison)
- `dev/misc/repro-attempts-04-barebones/*/chat-export.md` (for comparison)

**Required context**:
- `docs/experiments/methodologies/Experiment-Methodology-04.md`
- `docs/experiments/guides/Trial-Analysis-Guide.md`
- `docs/theories/Consolidated-Theory.md`
- `docs/core/Research-Questions.md`
- `docs/experiments/planning/Barebones-216.md` (companion analysis)

---

## Document History

- **2026-01-27**: Initial creation
- **2026-01-27**: Updated Barebones-216 comparison to reflect corrected 100% (4/4 valid trials) failure rate; one trial was excluded as a protocol violation
