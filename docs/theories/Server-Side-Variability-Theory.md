# Server-Side Variability Theory

This document presents a theory that phantom read behavior is primarily governed by **server-side variability** — changes to Anthropic's API infrastructure, model routing, and context management parameters — rather than by client build versions. The theory emerged from the Build Scan Discrepancy Investigation and fundamentally reframes how we interpret experimental results.

**Status**: Strongly supported by evidence
**Evidence Base**: 55+ trials across 8 collections spanning builds 2.1.6–2.1.22, collected Jan 27–29 2026
**Relationship to Other Theories**: Adds an external variability dimension to the X+Y model in `Consolidated-Theory.md`; does not replace existing theories but explains why their predictions fail across time windows

---

## Executive Summary

The Build Scan Discrepancy Investigation revealed that the same Claude Code build (2.1.22) produced 100% phantom read failure on Jan 28 and 100% success on Jan 29, with zero changes to the test environment. This cannot be explained by any client-side factor. The investigation traced the root cause to a binary harness-level decision — whether to persist tool results to disk — that is controlled by factors external to the session and invisible in session data.

Further analysis revealed two distinct server-side changes between Jan 28 and Jan 29:

1. **Persistence mechanism change**: The harness persistence trigger was modified, substantially reducing the rate at which tool results are persisted to disk (the root cause of phantom reads).
2. **Model behavioral change**: The model began preferring sub-agent delegation for file reads, a strategy that independently avoids the persistence trigger by keeping main-session token accumulation low.

Together, these changes constitute a **server-side mitigation** of the phantom reads issue. Whether this mitigation is intentional (a targeted fix), incidental (a side effect of other infrastructure changes), or permanent (vs. transient) remains unknown.

---

## The Core Claim

**Phantom read occurrence is primarily determined by server-side state — not by client build version.**

Build versions determine the client harness code, but the critical variables that govern phantom read behavior are controlled upstream:

| Variable | Client or Server? | Evidence |
| -------- | ----------------- | -------- |
| Persistence trigger (whether tool results are persisted to disk) | **Server** | Same build (2.1.22) showed 100% persistence on Jan 28, 0% on Jan 29 |
| Model behavior (delegation vs. direct reads) | **Server** | Delegation appeared simultaneously across builds 2.1.20 and 2.1.22 on Jan 29; confirmed on 2.1.6 on Jan 30 |
| Context management parameters | **Server** | Reset thresholds are consistent within time windows but vary between them |
| Effective threshold T | **Server** | The X+Y model's threshold appears externally configurable |

The client build determines *how* the harness interacts with the server (e.g., Era 1 vs. Era 2 markers), but the server determines *whether* the conditions for phantom reads are created.

---

## Evidence

### Evidence 1: The Build 2.1.22 Reversal

The most direct evidence for server-side control. Build 2.1.22 was tested in two collections:

| Collection | Date | Trials | Outcome | Persistence | Delegation |
| ---------- | ---- | ------ | ------- | ----------- | ---------- |
| barebones-2122 | Jan 28 | 6 | 6/6 FAILURE (100%) | 6/6 true (100%) | 0/6 (0%) |
| schema-13-2122 | Jan 29 | 6 | 6/6 SUCCESS (0%) | 0/6 false (0%) | 5/6 (83%) |

The test environment was identical (same files, same protocol, same machine, same repository state). Baselines matched within tokens (15,617 in both collections). The only variable was the date. A client build cannot change its behavior retroactively.

### Evidence 2: The Persistence Decision Is External to the Session

The JSONL deep dive (Build Scan Discrepancy Analysis, Step 1.4) compared a SUCCESS trial and a FAILURE trial with near-identical peak tokens (~160K). Key findings:

- Both session JSONL files contained identical full-content tool results (byte-for-byte match across all 9 files)
- No `<persisted-output>` markers appeared in either JSONL
- Token usage tracked within ~200 tokens throughout both sessions
- The ONLY artifact distinguishing the two was the presence/absence of a `tool-results/` directory — an external file system artifact

The persistence decision happens in a layer between the JSONL logger and the API call to the model. It is invisible in session data, meaning it cannot be predicted or detected from within the session.

### Evidence 3: Persistence Is Not Deterministic Within a Time Window

The schema-13-2120 collection (Jan 29, build 2.1.20) showed mixed persistence within a ~20-minute window:

| Trial | Time | Persistence | Direct Reads | Outcome |
| ----- | ---- | ----------- | ------------ | ------- |
| 202633 | 20:26 | **false** | 9 | SUCCESS |
| 202641 | 20:26 | **true** | 15 | FAILURE |
| 203737 | 20:37 | **true** | 11 | FAILURE |
| 203749 | 20:37 | **true** | 14 | SUCCESS (recovery) |
| 204311 | 20:43 | **true** | 12 | FAILURE |

Among direct-read trials on the same build within the same window: 80% persistence (4/5). This rules out a simple binary state ("persistence on" vs. "persistence off") and suggests either a probabilistic mechanism or a session-initialization-dependent factor.

### Evidence 4: Multiple Distinct Server States Observed

Across all data, distinct server-side regimes are evident:

| Date | Persistence Rate (Direct-Read) | Delegation Rate | Interpretation |
| ---- | ------------------------------ | --------------- | -------------- |
| Jan 27 | 0% (0/5) | 0% (0/5) | No persistence, no delegation — phantom reads impossible |
| Jan 28 | 100% (23/23) | 0% (0/23) | Full persistence, no delegation — phantom reads near-certain |
| Jan 29 (early) | ~67% (4/6 across 2.1.20, 2.1.22) | 60% (9/15) | Reduced persistence + delegation — phantom reads rare |
| Jan 29 (late) | 100% (3/3 on 2.1.6) | 50% (3/6) | Persistence remains strong for direct reads; delegation provides avoidance |

These states cannot be explained by build versions (the same builds appear across multiple states, and build 2.1.6 matches newer builds on the same day). They are consistent with server-side configuration changes occurring between test windows, with stochastic variation within windows.

### Evidence 5: Sub-Agent Delegation Appeared Simultaneously Across Builds

The Task/Explore delegation pattern was absent in all prior collections (Jan 27–28, builds 2.1.20–2.1.22, 28+ trials). It appeared on Jan 29 simultaneously on builds 2.1.20 (4/9 trials, 44%), 2.1.22 (5/6 trials, 83%), and 2.1.6 (3/6 trials, 50%). Build 2.1.6 data was collected via formal trial analysis (collection `schema-13-216`, 6 trials), providing quantitative confirmation of the User's Jan 30 observation.

The Task tool for sub-agent spawning has been available in Claude Code since well before 2.1.6. The capability was always present — what changed was the model's *tendency* to use it. Since model behavior is influenced by model weights and system prompts (both served from the API), this change is server-side. Build 2.1.6 is the strongest evidence: its client harness predates all other tested builds, yet it delegates at the same rate as newer builds tested the same day.

### Evidence 6: Rapid Build Release Cadence Suggests Active Tuning

Four builds were released between Jan 28 and Jan 29 (2.1.23 through 2.1.26). This rapid cadence, unusual in normal development, suggests Anthropic is actively iterating on the harness. The fact that 2.1.22 showed clean success (especially the full-protocol trial 211109) while 2.1.20 still showed 80% persistence among direct-reads hints that newer builds may incorporate harness-side mitigations tuned to work with the server-side behavioral changes.

---

## Relationship to the X+Y Model

The Consolidated Theory's X+Y model states: **Phantom reads occur when X + Y > T**, where X is pre-operation context, Y is operation tokens, and T is the effective threshold.

The Server-Side Variability Theory adds a critical dimension: **T is not fixed.** The effective threshold varies based on server-side configuration, potentially including:

- Whether the persistence mechanism is enabled at all
- At what context level persistence triggers
- Whether model behavioral strategies (delegation) are encouraged via system prompt tuning

The revised model becomes:

```
Phantom reads occur when:
  X + Y > T_effective(server_state)
  AND persistence is enabled for this session
  AND the agent does not recover from <persisted-output> markers
```

Where `T_effective` and the persistence enablement are external variables that the experiment cannot control or predict. This explains why the same X and Y values produce different outcomes on different days — the server state changed.

---

## Implications

### For the Investigation

1. **Build-specific failure rates are temporal, not permanent.** The Build Scan's Jan 28 data reflects Jan 28's server state. Those rates may not reproduce on any subsequent day.

2. **The "dead zone" (builds 2.1.7–2.1.14) may have been a server-state artifact.** Context overloads on those builds during the Jan 28 scan may not reproduce under current server conditions.

3. **Future experiments must control for time.** Comparing trials across days introduces server-state confounds. Within-day comparisons are more reliable, though even these show variability (see Evidence 3).

4. **The `has_tool_results` discriminator remains valid** as a per-session indicator. It perfectly predicts outcome within a session. What it cannot predict is whether a *future* session will have persistence enabled — that depends on server state at session time.

### For Users

1. **No build is inherently "safe" or "unsafe."** A build that fails today may succeed tomorrow, and vice versa.

2. **The MCP Filesystem workaround remains the only reliable mitigation.** It bypasses the persistence mechanism entirely, regardless of server state. See `WORKAROUND.md`.

3. **Sub-agent delegation is an emerging natural mitigation** but is not user-controllable. The model may or may not choose to delegate file reads to sub-agents.

### For Reproduction

1. **Reproduction scenarios must account for server-state variability.** A scenario designed to trigger phantom reads may succeed on days when the server disables persistence.

2. **Large sample sizes are essential.** Given the stochastic nature of persistence enablement, single trials or small batches cannot reliably characterize behavior.

3. **The most reliable reproduction requires persistence to be enabled.** Since we cannot control this, reproduction experiments should be designed to detect persistence (via `tool-results/` directory presence) and classify trials accordingly.

---

## The Nature of the Mitigation

The observed improvement between Jan 28 and Jan 29 is best characterized as a **mitigation, not a fix**:

- **Mitigation via reduced persistence**: The server appears to trigger persistence less frequently, reducing the probability of phantom reads. But persistence was still observed in 80% of direct-read trials on build 2.1.20 (Jan 29). The mechanism is not eliminated.

- **Mitigation via behavioral change**: The model's new preference for sub-agent delegation avoids the persistence trigger entirely. But this is a model behavioral tendency, not a guarantee — 1/6 trials on build 2.1.22 and 5/9 on build 2.1.20 did not delegate.

- **Non-deterministic process**: Because both the persistence decision and the delegation decision involve stochastic elements (server-side configuration + model discretion), a 100% fix may be unachievable through these mechanisms alone. The root cause — that persisted tool results are replaced by markers the model fails to follow up on — has not been addressed. The mitigation reduces exposure to the root cause rather than eliminating it.

- **Permanence unknown**: We have one day (Jan 29) of improved behavior. The Jan 27 data also showed improvement that reverted on Jan 28. Whether the Jan 29 state persists requires ongoing observation.

---

## Open Questions

### OQ-SSV-1: Is the persistence mechanism configurable per-build or globally?

The 80% persistence rate on 2.1.20 vs. 0% on 2.1.22 (Jan 29) suggests possible per-build configuration. Alternatively, the single direct-read trial on 2.1.22 may have been a stochastic non-persistence event. More data is needed.

### OQ-SSV-2: Is the delegation preference a model update or a system prompt change?

If it's a model weights update, it would be permanent (until the next model update). If it's a system prompt change, it could be modified at any time. The fact that 2.1.6 shows delegation (despite having a years-old client system prompt) suggests the change is in the server-side model or system prompt, not in the client-side prompt.

### OQ-SSV-3: Will the mitigation hold?

Only time-series data can answer this. Running periodic trials on a fixed build and tracking persistence rate and delegation rate over days/weeks would reveal whether the server state is stable.

### OQ-SSV-4: Does 2.1.6 (Era 2 boundary build) show reduced persistence under current server conditions?

**ANSWERED** (Step 2.3, collection `schema-13-216`, 6 trials on Jan 29):

Build 2.1.6 shows persistence in 100% of direct-read trials (3/3) and delegation in 50% of trials (3/6). The direct-read persistence rate is consistent with the ~80% rate observed on 2.1.20 earlier the same day. Persistence is NOT reduced on 2.1.6 — it is active at the same rate as on newer builds. The mitigation on 2.1.6 comes from delegation (avoiding the persistence trigger) and occasional recovery (1 trial), not from reduced persistence.

This definitively extends the server-side variability finding to the oldest tested build. Build 2.1.6 is behaviorally indistinguishable from builds 2.1.20 and 2.1.22 on the same day: same delegation rates, same persistence rates, same reset bands, same failure mechanism.

---

## Theory Status Summary

| Component | Status | Confidence |
| --------- | ------ | ---------- |
| Persistence is server-controlled | **Strongly supported** | High — same build reversal (2.1.22: 100% fail → 100% success); 2.1.6 matches newer builds |
| Model delegation is server-influenced | **Strongly supported** | High — simultaneous appearance across builds 2.1.6, 2.1.20, 2.1.22 at 44–83% rates; 2.1.6 formal trial data (3/6) |
| T_effective varies over time | **Supported** | Medium-High — four distinct server-state snapshots observed across 3 days, 3 builds |
| Current state is a mitigation, not a fix | **Strongly supported** | High — persistence 80–100% of direct reads on Jan 29; only delegation avoids the trigger |
| Mitigation permanence | **Unknown** | Low — only 1 day of improved behavior; prior "improvement" reverted |

---

*This document was created 2026-01-30 based on the Build Scan Discrepancy Investigation (Phases 1–2 complete). Updated 2026-01-30 with Step 2.3 findings (build 2.1.6, 6 trials): delegation confirmed at 50%, persistence at 100% of direct reads, OQ-SSV-4 answered, confidence levels upgraded. For detailed evidence, see `docs/experiments/results/Build-Scan-Discrepancy-Analysis.md`. For the investigation plan, see `docs/experiments/planning/Build-Scan-Discrepancy-Investigation.md`.*
