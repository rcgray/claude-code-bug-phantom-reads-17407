# Experiment-04 Build Scan: Builds 2.1.6 through 2.1.22

**Experiment ID**: Experiment-04-BuildScan
**Date Conducted**: 2026-01-28
**Protocol**: Experiment-Methodology-04 (`/setup-hard` + `/analyze-wpd`)
**Environment**: Barebones repository (minimal reproduction environment)
**Builds Tested**: 2.1.6, 2.1.7, 2.1.8, 2.1.9, 2.1.10, 2.1.11, 2.1.12, 2.1.14, 2.1.15, 2.1.16, 2.1.17, 2.1.18, 2.1.19, 2.1.20, 2.1.21, 2.1.22
**Note**: Build 2.1.13 does not exist (skipped in release sequence)

---

## Executive Summary

This experiment applied the standard Experiment-Methodology-04 protocol across every Claude Code build from 2.1.6 (the project's original target) through 2.1.22 (the current build at time of testing). The goal was threefold: (1) identify precisely where phantom reads were "fixed" or changed, (2) gather additional data for post-2.1.6 builds, and (3) understand the journey Claude Code has taken across these releases.

**Key Findings**:

1. **A "dead zone" from builds 2.1.7 through 2.1.14** rendered our experiment protocol inoperable due to context overload ("context full" during `/analyze-wpd`). Phantom reads were confirmed both before (2.1.6) and after (2.1.15+) this dead zone.

2. **Build 2.1.15 restores experiment viability** after the dead zone. The protocol runs again and phantom reads are detected, returning to the familiar failure pattern.

3. **Builds 2.1.15 through 2.1.19 consistently reproduce phantom reads**, appearing to behave similarly to 2.1.6.

4. **Build 2.1.20 shows mixed results**: failures, successes, AND context overloads — contradicting the earlier Barebones-2120 study (which showed 0% failure in 5/5 trials).

5. **Build 2.1.21 shows phantom reads with an occasional success** (2 failures, 1 success). No context overloads observed.

6. **Build 2.1.22 shows 100% failure** (6 failures, 0 successes). No context overloads observed.

7. **No context overloads were observed in 2.1.21 or later** across 18 total runs, suggesting the overload issue was limited to 2.1.20 or earlier.

---

## Motivation

### Why a Build Scan?

The Barebones-2120 study (5/5 success in build 2.1.20) raised the possibility that Anthropic had fixed phantom reads somewhere between 2.1.6 and 2.1.20. This scan was conducted to:

1. **Explore RQ-BB2120-8**: If Anthropic fixed phantom reads, determine precisely where the change occurred. Understanding this would help inform RQ-BB2120-6 (attempts to trigger phantom reads despite the apparent fix).

2. **Gather additional data**: Collect more samples across builds to better understand the nature of phantom reads and whether failures were truly eliminated or merely reduced in frequency.

3. **Understand the journey**: Document how Claude Code's behavior evolved across the 2.1.6 to 2.1.22 range, since the investigation had been locked to 2.1.6 for most of its history.

---

## Build Timeline

The following table documents the observed behavior of every build tested. This timeline captures not only phantom read outcomes but also behavioral observations about Claude Code's evolution across releases.

### Phase 1: Builds 2.1.6 – 2.1.12 (Jan 13 – Jan 17)

| Build      | Release Date | Experiment Outcome          | Notable Observations                                                                                                                                                                 |
| ---------- | ------------ | --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **2.1.6**  | Jan 13       | **FAILURE** (phantom reads) | Baseline build. Consistent with all prior Barebones-216 results. Last build before the dead zone (2.1.7–2.1.14).                                                                     |
| **2.1.7**  | Jan 14       | **CONTEXT OVERLOAD**        | Experiment cannot execute. Session hits 0% memory and dies during `/analyze-wpd`.                                                                                                    |
| **2.1.8**  | —            | **CONTEXT OVERLOAD**        | Same as 2.1.7.                                                                                                                                                                       |
| **2.1.9**  | Jan 16       | **CONTEXT OVERLOAD**        | Same as 2.1.7. Additionally, `/context` command removed from chat log — now displays as an interstitial dialog that doesn't write to the session. Very buggy, causes display issues. |
| **2.1.10** | Jan 16       | **CONTEXT OVERLOAD**        | Same as 2.1.7.                                                                                                                                                                       |
| **2.1.11** | Jan 17       | **CONTEXT OVERLOAD**        | Same as 2.1.7.                                                                                                                                                                       |
| **2.1.12** | Jan 17       | **CONTEXT OVERLOAD**        | Same as 2.1.7.                                                                                                                                                                       |

**Build 2.1.13 does not exist** (skipped in the release sequence).

### Phase 2: Builds 2.1.14 – 2.1.19 (Jan 20 – Jan 23)

| Build      | Release Date | Experiment Outcome          | Notable Observations                                                                                                                                                                                              |
| ---------- | ------------ | --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **2.1.14** | Jan 20       | **CONTEXT OVERLOAD**        | Restores old `/context` functionality — properly prints to session chat again. However, experiment still cannot complete. Changelog notes: "Fixed context window blocking regression."                            |
| **2.1.15** | Jan 21       | **FAILURE** (phantom reads) | **First build since 2.1.6 where experiment runs successfully!** New npm deprecation warning: "Claude Code has switched from npm to native installer." New bug: `/context` output printed *twice* to session chat. |
| **2.1.16** | Jan 22       | **FAILURE** (phantom reads) | Double `/context` bug persists.                                                                                                                                                                                   |
| **2.1.17** | Jan 22       | **FAILURE** (phantom reads) | Double `/context` bug persists.                                                                                                                                                                                   |
| **2.1.18** | Jan 23       | **FAILURE** (phantom reads) | Double `/context` bug persists.                                                                                                                                                                                   |
| **2.1.19** | Jan 23       | **FAILURE** (phantom reads) | Double `/context` bug persists. Last build with the double-print issue.                                                                                                                                           |

### Phase 3: Builds 2.1.20 – 2.1.22 (Jan 27 – Jan 28)

| Build      | Release Date | Experiment Outcome                                   | Notable Observations                                                                                          |
| ---------- | ------------ | ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| **2.1.20** | Jan 27       | **MIXED** (failures + successes + context overloads) | `/context` double-print bug fixed. Mixed results contradict earlier Barebones-2120 study (0% failure in 5/5). |
| **2.1.21** | Jan 28       | **2 FAILURE, 1 SUCCESS**                             | Phantom reads observed. One success. No context overloads.                                                    |
| **2.1.22** | Jan 28       | **6 FAILURE, 0 SUCCESS**                             | 100% failure rate. No context overloads.                                                                      |

---

## Detailed Results by Build

### Build 2.1.6 (Baseline)

**Collection**: `dev/misc/repro-attempts-04-barebones/`
**Trials**: 5 (4 valid failures, 1 invalid protocol violation)
**Valid Failure Rate**: 100% (4/4)

This is the well-characterized baseline from the Barebones-216 study. All valid trials produced phantom reads with `has_tool_results: true` and `<persisted-output>` markers. See `Barebones-216-Analysis.md` for full analysis.

### Builds 2.1.7 – 2.1.14: The "Dead Zone"

**Collections**: `dev/misc/barebones-219/` (build 2.1.9, 3 trials), `dev/misc/barebones-2114/` (build 2.1.14, 3 trials)
**Outcome**: All trials hit context overload — sessions died before the experiment protocol could complete.

Starting with build 2.1.7, the Experiment-Methodology-04 protocol became inoperable. Sessions would fill to 0% remaining memory and terminate with a "context full" message during the `/analyze-wpd` command. This persisted through build 2.1.14.

**Build 2.1.9 Trials** (`dev/misc/barebones-219/`):

| Trial ID        | Outcome               |
| --------------- | --------------------- |
| 20260128-094434 | Context limit reached |
| 20260128-094447 | Context limit reached |
| 20260128-095954 | Context limit reached |

**Build 2.1.14 Trials** (`dev/misc/barebones-2114/`):

| Trial ID        | Outcome               |
| --------------- | --------------------- |
| 20260128-124952 | Context limit reached |
| 20260128-125336 | Context limit reached |
| 20260128-125621 | Context limit reached |

**Interpretation**: The changelog for build 2.1.7 mentions "Fixed orphaned tool_results, context blocking limit" and 2.1.9 mentions "Context window blocking limit calculation corrected." The Barebones-2120 analysis (RQ-BB2120-7) identified build 2.1.14's fix — "Fixed a regression where the context window blocking limit was calculated too aggressively, blocking users at ~65% context usage instead of the intended ~98%" — as the most likely cause of these overloads. However, the experiment did not recover until 2.1.15, suggesting the 2.1.14 fix was necessary but not sufficient, or that the fix needed one additional release to stabilize.

### Build 2.1.15: Experiment Restored

**Collection**: `dev/misc/barebones-2115/` (3 trials)
**Outcome**: Phantom reads detected (FAILURE)

| Trial ID        | Outcome |
| --------------- | ------- |
| 20260128-130258 | FAILURE |
| 20260128-130530 | FAILURE |
| 20260128-131052 | FAILURE |

This is the first build since 2.1.6 (8 builds and 8 days later) where the experiment protocol runs to completion. Phantom reads were observed, confirming that the "dead zone" was not a phantom-read fix but rather a separate context management regression.

**Notable Changes**:
- npm deprecation warning appears: "Claude Code has switched from npm to native installer. Run `claude install` or see https://docs.anthropic.com/en/docs/claude-code/getting-started for more options." This is likely caused by our `cc_version.py` script installing via npm.
- `/context` output now prints twice to the session chat (new bug introduced in 2.1.15).

### Builds 2.1.16 – 2.1.19: Consistent Failures

**Outcome**: All runs showed phantom reads (FAILURE)

These builds behave similarly to 2.1.6 and 2.1.15, with the experiment protocol running successfully and phantom reads consistently occurring. The double `/context` print bug persists through 2.1.19 (fixed in 2.1.20).

### Build 2.1.20: The Contradiction

**Collection**: `dev/misc/barebones-2120-2/` (11 trials)
**Prior Study**: `dev/misc/repro-attempts-04-2120/` (5 trials, all SUCCESS)
**Outcome**: Mixed — 6 failures, 1 success, 4 context overloads

| Trial ID        | Outcome               |
| --------------- | --------------------- |
| 20260128-134716 | Context limit reached |
| 20260128-134724 | FAILURE               |
| 20260128-140143 | SUCCESS               |
| 20260128-140149 | FAILURE               |
| 20260128-140157 | FAILURE               |
| 20260128-142506 | Context limit reached |
| 20260128-142515 | Context limit reached |
| 20260128-142526 | FAILURE               |
| 20260128-143045 | Context limit reached |
| 20260128-143056 | FAILURE               |
| 20260128-143105 | FAILURE               |

This is the most interesting and confusing result. The earlier Barebones-2120 study showed 0% failure (5/5 success), leading to the conclusion that phantom reads were "fixed" in 2.1.20. The build scan study, conducted only hours later on the same build, showed 6 failures, 1 success, and 4 context overloads across 11 trials.

**Possible Explanations**:
- **Server-side changes**: Anthropic may have made server-side model or infrastructure changes between the two test sessions that affected context behavior without a client version bump.
- **Environmental variance**: Session-to-session variance may be wider than 5 trials captured.
- **Transient fix**: The "fix" observed in the first 5 trials may have been a transient server-side state.

**Implication**: The Barebones-2120 analysis conclusions (RQ-BB2120-1 through RQ-BB2120-7) may need to be revisited. The dramatic 0/5 → 6/7 valid failures shift within the same build version undermines the "definitive fix" interpretation and suggests server-side factors play a role.

### Build 2.1.21: Failures with One Success

**Collection**: `dev/misc/barebones-2121/` (3 trials, pre-processed)
**Failure Rate**: 67% (2/3)

| Trial ID        | Outcome | Affected Files          | has_tool_results |
| --------------- | ------- | ----------------------- | ---------------- |
| 20260128-150640 | FAILURE | 5 files (WPD + 4 specs) | true             |
| 20260128-150657 | SUCCESS | None                    | false            |
| 20260128-150706 | FAILURE | 5 files (WPD + 4 specs) | true             |

The success in trial 150657 is notable because it shows `has_tool_results: false` (no persistence triggered) while the failures show `has_tool_results: true` — the same pattern that distinguished successes from failures in all prior analysis. No context overloads were observed.

### Build 2.1.22: Unanimous Failure

**Collection**: `dev/misc/barebones-2122/` (6 trials, pre-processed)
**Failure Rate**: 100% (6/6)

| Trial ID        | Outcome | Affected Files | has_tool_results |
| --------------- | ------- | -------------- | ---------------- |
| 20260128-152044 | FAILURE | 4 files        | true             |
| 20260128-152056 | FAILURE | 4 files        | true             |
| 20260128-152157 | FAILURE | 5 files        | true             |
| 20260128-152658 | FAILURE | 5 files        | true             |
| 20260128-152707 | FAILURE | 5 files        | true             |
| 20260128-152715 | FAILURE | 4 files        | true             |

All 6 trials failed with `has_tool_results: true`, confirming the `<persisted-output>` persistence mechanism is active and phantom reads are occurring. No context overloads, no successes.

---

## Aggregate Results

### Failure Rates by Build

| Build             | Trials | Failures | Successes   | Context Overloads | Failure Rate (valid) |
| ----------------- | ------ | -------- | ----------- | ----------------- | -------------------- |
| **2.1.6**         | 5      | 4        | 1 (invalid) | 0                 | **100%** (4/4 valid) |
| **2.1.7–2.1.12**  | —      | —        | —           | All               | N/A (dead zone)      |
| **2.1.14**        | 3      | —        | —           | All               | N/A (dead zone)      |
| **2.1.15**        | 3      | 3        | 0           | 0                 | **100%**             |
| **2.1.16–2.1.19** | runs   | failures | 0           | 0                 | **~100%**            |
| **2.1.20**        | 11     | 6        | 1           | 4                 | **86%** (6/7 valid)  |
| **2.1.21**        | 3      | 2        | 1           | 0                 | **67%**              |
| **2.1.22**        | 6      | 6        | 0           | 0                 | **100%**             |

### Build Classification Summary

| Category                         | Builds                               | Behavior                                |
| -------------------------------- | ------------------------------------ | --------------------------------------- |
| **Phantom Reads (confirmed)**    | 2.1.6, 2.1.15–2.1.19, 2.1.21, 2.1.22 | Experiment runs; phantom reads detected |
| **Dead Zone (context overload)** | 2.1.7–2.1.12, 2.1.14                 | Experiment cannot execute; context full |
| **Mixed / Inconclusive**         | 2.1.20                               | Failures, successes, and overloads      |

---

## `/context` Command Evolution

The `/context` command behavior changed across builds, affecting experiment data collection:

| Build Range              | `/context` Behavior                                                                                     |
| ------------------------ | ------------------------------------------------------------------------------------------------------- |
| 2.1.6 – 2.1.8            | Normal: prints to session chat once                                                                     |
| 2.1.9 – 2.1.12 (approx.) | **Broken**: displays as interstitial dialog, does not write to session chat. Buggy with display issues. |
| 2.1.14                   | **Restored**: prints to session chat again                                                              |
| 2.1.15 – 2.1.19          | **Double-print bug**: output appears twice in session chat                                              |
| 2.1.20+                  | **Normal**: prints once, double-print bug fixed                                                         |

---

## `cc_version.py` Compatibility

Starting with build 2.1.15, a new warning appears when launching Claude Code after installation via the `cc_version.py` script (which uses npm):

> "Claude Code has switched from npm to native installer. Run `claude install` or see https://docs.anthropic.com/en/docs/claude-code/getting-started for more options."

This warning appears to be cosmetic and does not affect Claude Code operation or experiment results as of 2.1.22. However, it signals that Anthropic is transitioning away from npm-based installation, which may eventually break the `cc_version.py` script.

---

## Impact on Prior Analysis

### Barebones-2120 Study Validity

The Barebones-2120 study (`docs/experiments/results/Barebones-2120-Analysis.md`) concluded that phantom reads were "fixed or fundamentally mitigated" in build 2.1.20, based on 5/5 success. The build scan reveals that the same build (2.1.20), tested roughly one day later, shows a mix of failures, successes, and context overloads.

**Possible explanations for this discrepancy**:

1. **Server-side model/infrastructure changes**: Anthropic may have pushed server-side changes (model updates, routing changes, infrastructure modifications) that affected behavior without requiring a client version bump. This would mean client version alone does not fully determine behavior.

2. **Small sample size**: 5 trials may have been insufficient to capture the true failure rate if it was, for example, 20-30%.

3. **Time-of-day effects**: API behavior may vary based on load, routing, or other time-dependent factors.

**Affected conclusions**:
- RQ-BB2120-1 ("Did Anthropic fix phantom reads?"): Answer changes from "strong evidence of fix" to "inconclusive — behavior is not stable even within a single build"
- RQ-BB2120-4 ("Has the phantom read mechanism changed?"): The conclusion that `<persisted-output>` was eliminated is undermined by the reappearance of failures
- The "causal chain" explaining the fix through context management improvements may still be directionally correct but clearly does not tell the complete story

### Implications for the Investigation

1. **Client version is necessary but not sufficient** for predicting phantom read behavior. Server-side factors appear to play a role.

2. **Build 2.1.22 is a viable target for continued investigation**, since it shows 100% failure rate (6/6) and does not suffer from context overloads.

3. **The "dead zone" (2.1.7–2.1.14) represents a separate regression** in context management, not a phantom-read fix. Phantom reads returned immediately when the experiment became viable again in 2.1.15.

4. **The investigation should consider moving its target build to 2.1.22** to stay current and avoid the growing age of 2.1.6 (released Jan 13, over two weeks old).

---

## Conclusions

### What We Learned

1. **Phantom reads are NOT fixed.** Despite the Barebones-2120 study's promising results, builds 2.1.21 and 2.1.22 clearly exhibit phantom reads with the same `<persisted-output>` mechanism (Era 2) observed in 2.1.6.

2. **There was a "dead zone" from 2.1.7 to 2.1.14** where a context management regression made our experiment inoperable. This was a separate issue from phantom reads.

3. **Build behavior is not fully determined by client version.** The same build (2.1.20) showed dramatically different results when tested on different days, suggesting server-side factors influence phantom read occurrence.

4. **Build 2.1.22 is the strongest current candidate** for continued investigation: 100% failure rate, no context overloads, and the most recent stable build at time of testing.

5. **The `/context` command has been unstable** across builds, with broken display in 2.1.9–2.1.12 and a double-print bug in 2.1.15–2.1.19. Researchers should verify `/context` behavior on any new build before relying on its measurements.

### Recommended Next Steps

1. **Adopt build 2.1.22 as the new project target**, replacing 2.1.6. It is current, shows reliable failure, and avoids context overloads.

2. **Analyze `barebones-2122` and `barebones-2121` collections** in depth. The 2.1.22 collection (6 failures) should be compared against Barebones-216 to see if the failure profile has changed. The 2.1.21 collection contains a success worth examining against its failures.

3. **Revisit the Barebones-2120 analysis** with appropriate caveats. The "fix" conclusion needs to be walked back to "inconclusive — may reflect transient server-side state."

4. **Investigate server-side variability** as a factor in phantom read occurrence. The 2.1.20 discrepancy is the strongest evidence yet that client version alone does not determine behavior.

---

## Collections Reference

| Collection                  | Build  | Trials | Pre-Processed | Location                                |
| --------------------------- | ------ | ------ | ------------- | --------------------------------------- |
| repro-attempts-04-barebones | 2.1.6  | 5      | Yes           | `dev/misc/repro-attempts-04-barebones/` |
| barebones-219               | 2.1.9  | 3      | No            | `dev/misc/barebones-219/`               |
| barebones-2114              | 2.1.14 | 3      | No            | `dev/misc/barebones-2114/`              |
| barebones-2115              | 2.1.15 | 3      | No            | `dev/misc/barebones-2115/`              |
| repro-attempts-04-2120      | 2.1.20 | 5      | Yes           | `dev/misc/repro-attempts-04-2120/`      |
| barebones-2120-2            | 2.1.20 | 11     | No            | `dev/misc/barebones-2120-2/`            |
| barebones-2121              | 2.1.21 | 3      | Yes           | `dev/misc/barebones-2121/`              |
| barebones-2122              | 2.1.22 | 6      | Yes           | `dev/misc/barebones-2122/`              |

---

## Document History

- **2026-01-29**: Initial creation documenting build scan results across 2.1.6–2.1.22
