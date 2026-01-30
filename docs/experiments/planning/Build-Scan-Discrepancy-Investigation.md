# Build Scan Discrepancy Investigation

**Date Created**: 2026-01-29
**Triggered By**: Experiment-04-BuildScan results contradicting Barebones-2120 study
**Priority**: BLOCKING — halts other phantom read investigations until resolved

---

## The Problem

On 2026-01-27, the Barebones-2120 experiment (`dev/misc/repro-attempts-04-2120/`) ran 5 trials on Claude Code build 2.1.20 and observed **0% failure rate** (5/5 SUCCESS). This led to the provisional conclusion that Anthropic had fixed phantom reads.

On 2026-01-28, the Experiment-04 Build Scan ran 11 additional trials on the **same build** (2.1.20) in collection `dev/misc/barebones-2120-2/` and observed **6 failures, 1 success, 4 context overloads** — an 86% failure rate among valid trials.

These experiments used the same protocol (Experiment-Methodology-04), the same test repository (`barebones-phantom-reads`), and were conducted within an estimated 4-hour window. Something changed between the two test sessions, and understanding what changed is essential before trusting any of the build scan data or drawing further conclusions about phantom read behavior.

---

## Preliminary Findings

An initial comparison of pre-processed `trial_data.json` files across `repro-attempts-04-2120` (SUCCESS, Jan 27) and `barebones-2121` (2 FAILURE / 1 SUCCESS, Jan 28) reveals the following.

### Finding 1: The Test Environment Did Not Change

Structural fingerprints are nearly identical across both collections:

| Metric            | repro-04-2120 (Jan 27)                                                         | barebones-2121 (Jan 28) |
| ----------------- | ------------------------------------------------------------------------------ | ----------------------- |
| File paths        | `/Users/gray/Projects/barebones-phantom-reads/docs/specs/*`                    | Same                    |
| Files targeted    | 9 spec files + WPD                                                             | Same 9 files            |
| Protocol sequence | `/context` → `/setup-hard` → `/context` → `/analyze-wpd` → inquiry → `/export` | Same                    |
| Post-setup tokens | 114,017–114,018                                                                | 114,223–114,226         |
| Baseline tokens   | 15,490 (trials 2–5)                                                            | 15,616                  |

The ~200-token difference in post-setup is negligible and consistent with minor version differences in system prompt or tool definitions between builds 2.1.20 and 2.1.21. This rules out environmental drift (modified files, changed commands, repository alterations) as the cause of the discrepancy.

### Finding 2: `has_tool_results` Is the Discriminator

The critical difference between SUCCESS and FAILURE trials is whether the Claude Code harness persisted tool results to disk:

| Collection     | Trial  | Outcome | Files Read | Peak Tokens | has_tool_results |
| -------------- | ------ | ------- | ---------- | ----------- | ---------------- |
| repro-04-2120  | 095002 | SUCCESS | 9          | 159,633     | **false**        |
| repro-04-2120  | 100209 | SUCCESS | 9          | 172,990     | **false**        |
| repro-04-2120  | 100944 | SUCCESS | 9          | 173,000     | **false**        |
| barebones-2121 | 150640 | FAILURE | 9          | 159,840     | **true**         |
| barebones-2121 | 150657 | SUCCESS | **6**      | **131,802** | **false**        |
| barebones-2121 | 150706 | FAILURE | 9          | 159,856     | **true**         |

The same 9 files, similar peak token counts (~160K), but the harness made different persistence decisions. When it persisted (`has_tool_results: true`), phantom reads occurred. When it did not (`has_tool_results: false`), reads succeeded.

### Finding 3: The 2121 "Success" Was a Protocol Violation

Trial 150657 (the lone success in `barebones-2121`) only read **6 files** instead of 9. It skipped `module-alpha.md`, `module-beta.md`, and `module-gamma.md` — the agent chose not to read them. This reduced peak tokens to 131K (vs ~160K for proper trials) and persistence was never triggered. **This trial is INVALID** as a data point for comparing success vs. failure — it avoided the conditions that trigger the bug, rather than surviving them.

---

## Research Questions

### RQ-BSD-1: Why did the harness persist tool results in some sessions and not others?

The same files at similar token counts (~160K peak) produced `has_tool_results: false` on Jan 27 and `has_tool_results: true` on Jan 28. The persistence decision is the proximate cause of the discrepancy. What drives this decision?

**Sub-questions:**
- Is persistence purely threshold-based (e.g., result exceeds N tokens)?
- Does the threshold vary between builds?
- Does the threshold vary over time within the same build (server-side configuration)?
- Could caching behavior differ between the first session on a build and subsequent sessions?

### RQ-BSD-2: Is the discrepancy explained by server-side changes?

The ~4-hour gap between the two test sessions is short, but Anthropic could plausibly push server-side changes (model routing, context management parameters, infrastructure updates) without a client version bump. However, this raises a follow-up question: **why would Anthropic deploy a change that makes phantom reads succeed, then revert it?** Possible explanations include:

- **A/B testing**: Anthropic may be testing different context management strategies on subsets of API traffic
- **Infrastructure rotation**: Different API backends may have different behavior
- **Rollback**: A change deployed during the first test window may have been rolled back
- **Time-of-day effects**: API behavior may differ based on server load
- **No intentional change at all**: The difference may be in how the client harness interacts with the server, not the server itself

### RQ-BSD-3: Can we reproduce the original 2120 success pattern?

If we re-run the exact same protocol on build 2.1.20 today, do we get the same results as either session? This would tell us whether the original success was a transient state or a reproducible condition.

### RQ-BSD-4: Is the persistence threshold build-specific?

The 2120 original SUCCESS trials hit 159-173K peak tokens without persistence. The 2121 FAILURE trials hit 159K with persistence. Is there a build-level difference in where the persistence threshold sits?

### RQ-BSD-5: Do the raw JSONL files reveal any structural differences?

The `trial_data.json` pre-processing captures high-level metrics but may miss low-level differences in the session files. The raw JSONL data could reveal differences in:
- Tool result formats or sizes
- System message content
- Harness behavior markers
- API response metadata
- Token accounting details

---

## Investigation Plan

### Phase 1: Analyze Existing Data (No New Experiments)

Use the data already collected to extract maximum insight before running any new trials.

#### Step 1.1: Pre-Process `barebones-2120-2`

The `barebones-2120-2` collection (11 trials, build 2.1.20) has no `trial_data.json` files. Pre-processing these trials enables direct structural comparison with `repro-attempts-04-2120` (same build, different outcomes).

**Action**: Run `/update-trial-data` on all 11 trials in `dev/misc/barebones-2120-2/`.

**What we learn**: Whether the 2120-2 failures and successes have the same structural fingerprint as the original 2120 successes.

#### Step 1.2: Compare 2120 Success vs 2120-2 Success

After pre-processing, compare the single SUCCESS trial in `barebones-2120-2` against the 5 SUCCESS trials in `repro-attempts-04-2120`.

**Key comparisons**:
- `has_tool_results` (should be `false` in both if the pattern holds)
- Peak token counts
- Files read (was it a full 9-file run or a protocol violation like 2121?)
- Post-setup token baseline
- Reset patterns

**What we learn**: Whether the 2120-2 success is a genuine apples-to-apples match or another protocol violation.

#### Step 1.3: Compare 2120-2 Failures Against 2121/2122 Failures

Compare the failure trials across collections to verify they share the same failure profile (`has_tool_results: true`, same affected files, same persistence mechanism).

**What we learn**: Whether the failure mechanism is consistent across builds and sessions, or if there are structural variations in how failures manifest.

#### Step 1.4: Examine Raw JSONL Differences (RQ-BSD-5)

Select one SUCCESS trial from `repro-attempts-04-2120` and one FAILURE trial from `barebones-2121` with similar peak tokens (~160K). Compare their raw JSONL session files line by line, focusing on:
- The API request/response around file reads
- Any differences in tool result handling
- System messages or harness behavior markers
- Token count metadata in API responses

**What we learn**: Whether there are low-level structural differences that `trial_data.json` doesn't capture.

### Phase 2: Targeted Experiments

Based on Phase 1 findings, run focused experiments to test specific hypotheses.

#### Step 2.1: Replication Attempt on Build 2.1.20 (RQ-BSD-3)
Collection: `schema-13-2120`

Re-run the exact Experiment-Methodology-04 protocol on build 2.1.20 (3-5 trials).

**What we learn**:
- If all SUCCESS: Suggests the original pattern may still be reproducible (server-side state varies over time)
- If all FAILURE: Suggests the original success was a transient anomaly
- If MIXED: Suggests stochastic server-side behavior

**Preparation**: None — use existing protocol and `cc_version.py` to install 2.1.20.

#### Step 2.2: Replication on Build 2.1.22 as Control
Collection: `schema-13-2122`

Run 3 trials on build 2.1.22 to confirm it still shows 100% failure (as observed in the build scan). This serves as a control — if 2.1.22 also suddenly shows successes, we know something systemic changed.

**What we learn**: Whether the current API state produces consistent results on a build with previously 100% failure.

#### Step 2.3: Cross-Machine Replication (Low Priority)

Run the protocol on a different machine (different IP, different user account) to test whether the discrepancy is tied to the specific test machine or user identity.

**What we learn**: Whether API behavior is user-specific, IP-specific, or universal.

**Priority**: LOW — only pursue if Phase 1 and Steps 2.1-2.2 fail to explain the discrepancy. The preliminary analysis strongly suggests this is not an environment issue, and the 4-hour window between tests makes machine-specific factors unlikely.

### Phase 3: Theoretical Integration

#### Step 3.1: Revise or Confirm the X+Y Model

The Consolidated Theory's X+Y model assumes that for a given X and Y, the outcome is deterministic (either X+Y > T triggers phantom reads or it doesn't). The 2120 discrepancy suggests the model may need a stochastic component — something like:

- **X + Y > T_effective**, where T_effective varies due to server-side configuration
- Or: persistence is triggered probabilistically based on factors beyond just X+Y

Document how the discrepancy affects the X+Y model and whether the model needs revision.

#### Step 3.2: Assess Impact on Build Scan Conclusions

Based on the investigation findings, determine which Build Scan conclusions remain valid:
- Is the "dead zone" (2.1.7-2.1.14) interpretation still sound?
- Is build 2.1.22 reliably the best reproduction target?
- Should any trials be re-run on specific builds?

---

## Experiment Variants NOT Recommended at This Stage

The following investigation approaches from the Post-Experiment-04 Ideas are **on hold** pending resolution of this discrepancy:

- **04M (Intermediate X)**: Mapping the X boundary is meaningless if the threshold itself is unstable
- **04F (File Count vs Tokens)**: Same reasoning — the threshold needs to be stable to measure
- **04C (7-File Sanity Check)**: Same reasoning

These experiments all assume a deterministic or near-deterministic relationship between inputs and outcomes. If server-side variability introduces randomness, these experiments would need significantly more trials per data point to be meaningful.

The Easy/Medium/Hard scenario variants are similarly deferred. Calibrating reproduction scenarios requires understanding the stability of the underlying system first.

---

## Success Criteria

This investigation succeeds when we can answer:

1. **Is the 2120 discrepancy explained by identifiable structural differences in session data?** (Phase 1)
2. **Is the original 2120 success reproducible today?** (Phase 2, Step 2.1)
3. **Is our current test methodology stable enough to draw conclusions?** (Phase 2, Step 2.2)
4. **Does the X+Y model need a stochastic component?** (Phase 3)

If the answer to #3 is "no" (results are too variable to draw conclusions), we have a fundamental methodological problem that must be solved before any further investigation is meaningful.

---

## Priority and Sequencing

```
Phase 1 (Data Analysis - No new experiments needed)
├── Step 1.1: Pre-process barebones-2120-2                    [FIRST]
├── Step 1.2: Compare 2120 success vs 2120-2 success          [After 1.1]
├── Step 1.3: Compare failure profiles across collections     [After 1.1]
└── Step 1.4: Raw JSONL deep dive                             [After 1.2/1.3]

Phase 2 (Targeted Experiments - Based on Phase 1 findings)
├── Step 2.1: Re-run 2.1.20 today (3-5 trials)               [After Phase 1]
├── Step 2.2: Re-run 2.1.22 as control (3 trials)            [Parallel with 2.1]
└── Step 2.3: Cross-machine test (only if needed)             [After 2.1/2.2]

Phase 3 (Theoretical Integration)
├── Step 3.1: Revise X+Y model if needed                      [After Phase 2]
└── Step 3.2: Assess Build Scan validity                      [After Phase 2]
```

Phase 1 can begin immediately with no additional experiments. Phase 2 requires terminal access to the barebones test machine. Phase 3 is analytical work that follows from the earlier phases.

---

## Document History

- **2026-01-29**: Initial creation based on Build Scan discrepancy analysis
