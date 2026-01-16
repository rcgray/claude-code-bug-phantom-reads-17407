# Headroom Theory

This document describes the **Headroom Theory** - a refinement of our understanding of phantom read triggers based on analysis of WSD Development project trials conducted on 2026-01-15. The theory explains why some sessions experience phantom reads while others with similar workloads do not.

**Status**: Active investigation
**Related**: [Context-Reset-Analysis.md](Context-Reset-Analysis.md), [Investigation-Journal.md](Investigation-Journal.md)

---

## Executive Summary

Analysis of WSD Development project trials with embedded `/context` calls revealed that **starting context consumption** before a multi-file read operation is a critical predictor of phantom read occurrence - more predictive than total content size or final token consumption.

| Trial | Pre-Operation | Post-Operation | Delta | Phantom Reads? |
|-------|---------------|----------------|-------|----------------|
| WSD Dev Good | **85K (42%)** | 159K (79%) | +74K | No |
| WSD Dev Bad | **126K (63%)** | 142K (71%) | +16K | **Yes** |

The bad session consumed **fewer total tokens** but experienced phantom reads because it **started higher** and had less "headroom" for the incoming content.

---

## Background

### Discovery Context

On 2026-01-15, we conducted reproduction trials using the Reproduction Specs Collection (a set of dummy specification documents designed to trigger phantom reads). All three trials (easy, medium, hard) succeeded without phantom reads, even though the "hard" case was designed to reliably fail.

Analysis of these failed reproduction attempts, combined with new WSD Development project trials using embedded `/context` calls, revealed that our original hypothesis about a fixed ~140K token threshold was incomplete.

### The Original Hypothesis

The Context Reset Analysis (`Context-Reset-Analysis.md`) established:
- Phantom reads correlate with **context reset frequency**
- Sessions with phantom reads have approximately 2x the resets of successful sessions
- Resets appear to occur around ~140K tokens before dropping to ~20K base level

### What Was Missing

The original hypothesis focused on absolute token counts and reset frequency, but didn't fully explain **why** some sessions had more resets than others with similar content consumption.

---

## The Headroom Theory

### Core Concept

**Headroom** is the available buffer space in the context window before a multi-file read operation begins.

```
Headroom = Context Window Size - Current Token Consumption
```

For a 200K context window:
- Starting at 85K = 115K headroom
- Starting at 126K = 74K headroom

### The Theory

**Lower starting headroom leads to earlier and more frequent context resets, which increases phantom read probability.**

When an agent initiates a multi-file read operation (like `/refine-plan` which reads numerous spec files):

1. **High headroom (>100K)**: Files can be read sequentially without triggering resets. Content accumulates safely.

2. **Low headroom (<80K)**: The first few large files push the context toward the reset threshold. A reset occurs, potentially clearing recently-read content before the model processes it. The cycle repeats with each subsequent file.

### Supporting Evidence

**Token Progression Patterns** (from Context-Reset-Analysis.md):

2.1.6-good progression:
```
32K → 77K → 81K → [RESET to 20K] → 84K → 105K → 137K → 143K → [RESET to 20K]
```

2.1.6-bad progression:
```
32K → 77K → 98K → [RESET to 20K] → 108K → 129K → [RESET to 20K] → 133K → [RESET to 20K] → 132K → 142K → [RESET to 20K]
```

The bad session shows **more frequent resets at lower peak values**. The Headroom Theory explains this: the bad session was operating under greater context pressure (started higher), so it hit the reset threshold sooner and more often.

---

## Relationship to Reset Theory

### Complementary, Not Contradictory

The Headroom Theory **supports and refines** the Reset Theory:

| Theory | Explains |
|--------|----------|
| **Reset Theory** | The MECHANISM - context resets clear content before the model processes it |
| **Headroom Theory** | The TRIGGER - low starting headroom causes earlier/more frequent resets |

They work together:
1. Low headroom → More resets (Headroom Theory)
2. More resets → More phantom reads (Reset Theory)

### Updated Causal Chain

```
High pre-operation consumption
        ↓
Low headroom available
        ↓
Multi-file read begins
        ↓
Context fills quickly
        ↓
Reset threshold reached sooner
        ↓
Context reset occurs
        ↓
Recently-read content cleared
        ↓
Model receives placeholder instead of content
        ↓
PHANTOM READ
        ↓
(Cycle repeats for subsequent files)
```

---

## Evidence

### WSD Development Project Trials (2026-01-15)

Two trials conducted on the WSD Development project with identical `/refine-plan` operations but different onboarding paths:

**Good Trial** (no phantom reads):
- Pre-/refine-plan: 85K tokens (42%)
- Post-/refine-plan: 159K tokens (79%)
- Files read: All returned inline content
- Agent self-report: "All my Read tool calls returned actual file content inline"

**Bad Trial** (phantom reads confirmed):
- Pre-/refine-plan: 126K tokens (63%)
- Post-/refine-plan: 142K tokens (71%)
- Files affected: Target WPD, Pre-Staging-Script-Overview.md, WSD-Runtime-Metadata-Schema.md, Installation-System.md, multiple others
- Agent self-report: "My entire 10-point assessment was fabricated. I never actually read the target document."

### Why Did the Bad Trial Start Higher?

The bad trial agent read more files during onboarding:
- `Python-Test-Environment-Isolation-Standards.md` (1,238 lines)
- `TypeScript-Test-Environment-Isolation-Standards.md` (1,251 lines)
- Additional standards files

This pushed context consumption to 126K before `/refine-plan` even started.

### Reproduction Attempt Analysis

Our reproduction attempts failed because the clone repository's onboarding process consumes fewer tokens:

| Project | Post-Init Consumption | Headroom | Result |
|---------|----------------------|----------|--------|
| Clone (hard trial) | 95K | 105K | Success (no phantom reads) |
| Clone (medium trial) | 80K | 120K | Success |
| Clone (easy trial) | 74K | 126K | Success |
| WSD Dev (good trial) | 85K | 115K | Success |
| WSD Dev (bad trial) | 126K | 74K | **PHANTOM READS** |

The clone trials all had >100K headroom, avoiding the danger zone.

---

## Implications

### For Reproduction Environment

To reliably trigger phantom reads, we must:

1. **Increase baseline consumption** before `/refine-plan` (not just spec content size)
2. **Target ~120-130K pre-operation** to reduce headroom to <80K
3. **Add substantial onboarding content** (e.g., large standards files)

### For Detection Strategy

The `/context` command provides visibility into headroom status. A session at 63%+ consumption before a multi-file operation is at elevated phantom read risk.

Potential risk classification (revised):
- **Low risk**: <50% consumption (>100K headroom)
- **Medium risk**: 50-60% consumption (80-100K headroom)
- **High risk**: >60% consumption (<80K headroom)

### For Mitigation Strategy

If headroom is the key factor:

1. **Monitor context before operations**: Check `/context` before initiating multi-file reads
2. **Defer large operations**: If context is high, complete current work first
3. **Staged onboarding**: Read critical files early when headroom is abundant
4. **Session breaks**: For complex operations, consider starting fresh sessions

---

## Open Questions

### 1. Is There a Fixed Threshold?

Is the danger zone truly at ~120-130K starting consumption, or does it depend on the size of the incoming content?

**Method**: Conduct trials with varying starting consumption levels and measure phantom read occurrence rates.

### 2. Does Reset Timing Matter?

If a reset occurs AFTER a file is fully processed, is the content "safe"? Or can resets retroactively cause phantom reads?

**Method**: Map precise timestamps of Read operations and resets in `.jsonl` files.

### 3. Is Content Size or Operation Count More Important?

Does reading 10 small files create more risk than reading 2 large files with the same total tokens?

**Method**: Conduct trials with varied file count/size distributions.

### 4. Are Some File Types More Vulnerable?

Do certain file characteristics (size, content type, read method) make files more likely to be phantom-read?

**Method**: Analyze phantom read occurrence by file characteristics across sessions.

---

## Terminology

- **Headroom**: Available buffer space in context window (Context Size - Current Consumption)
- **Pre-operation consumption**: Token count before initiating a multi-file operation
- **Reset threshold**: The approximate token level (~140K) that triggers context clearing
- **Danger zone**: The consumption range (>60%, <80K headroom) where phantom reads become likely

---

## References

- [Context-Reset-Analysis.md](Context-Reset-Analysis.md) - The Reset Theory and context reset mechanics
- [Investigation-Journal.md](Investigation-Journal.md) - Chronological discovery log
- [PRD.md](PRD.md) - Project overview and phantom reads background
- Sample data: `dev/misc/wsd-dev-repeat/`

---

*Created: 2026-01-15*
