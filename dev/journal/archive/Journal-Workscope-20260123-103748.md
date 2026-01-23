# Work Journal - 2026-01-23 10:37
## Workscope ID: Workscope-20260123-103748

## Initialization Phase

**Status**: Initialized with `--custom` flag - awaiting custom workscope from User.

## Project-Bootstrapper Onboarding

Consulted Project-Bootstrapper agent for onboarding. Key takeaways:

### Critical Rules to Follow

1. **Rule 5.1**: Backward compatibility is FORBIDDEN (project has not shipped)
2. **Rule 3.4**: No meta-process references in product artifacts (no phase numbers, task IDs in code)
3. **Rule 3.11**: If blocked from writing to read-only directory, copy file to `docs/workbench/` with exact same filename
4. **Rule 4.4**: NEVER use `cat >>`, `echo >>`, or `<< EOF` to write files
5. **Rule 4.2**: Read files COMPLETELY unless otherwise directed
6. **Rule 2.2**: Only read-only git commands allowed

### Files to Read for Onboarding

**TIER 1: CRITICAL (Already read during /wsd:boot)**
1. `docs/read-only/Agent-Rules.md` - Fundamental laws all agents must follow
2. `docs/read-only/Agent-System.md` - User Agent and Special Agent collaboration
3. `docs/read-only/Checkboxlist-System.md` - Task organization and tracking
4. `docs/read-only/Workscope-System.md` - Work assignment definitions

**TIER 2: ESSENTIAL CONTEXT (Already read during /wsd:boot)**
5. `docs/read-only/Documentation-System.md` - Document organization
6. `docs/core/Design-Decisions.md` - Project-specific design philosophies

**TIER 3: TASK-SPECIFIC (To read based on assigned workscope)**
- Coding standards in `docs/read-only/standards/` as relevant to tasks

### QA Agents with Veto Power
- Documentation-Steward: Verifies spec compliance
- Rule-Enforcer: Checks rule compliance
- Test-Guardian: Verifies test coverage
- Health-Inspector: Runs health checks

### Understanding `[%]` Tasks
- Treat EXACTLY as `[ ]` - full implementation responsibility
- Find delta between current state and specification, then implement it

---

## Custom Workscope: Theory Review

Read `docs/core/Investigation-Journal.md` (~1199 lines) to understand current investigation state.

### Current Theories Summary

**STRONGLY CONFIRMED:**
- **Reset Timing Theory**: Mid-session resets (50-90% of session) predict phantom reads with 100% accuracy (31/31 trials)

**STRENGTHENED:**
- **Reset Count Theory**: 2 resets = safe (100%), 4+ resets = failure (100% in current data)

**SUPPORTED:**
- **Headroom Theory**: Low starting headroom correlates with phantom reads but is not sufficient alone
- **Mid-Session Accumulation**: 2+ mid-session resets = likely failure, 3+ = guaranteed failure
- **Sustained Processing Gap**: Successful sessions show ~25-30% uninterrupted window between early and late resets

**HYPOTHESIS (Needs Validation):**
- **Dynamic Context Pressure**: Rate of token accumulation (not just total) may trigger resets

**NEW - CONFIRMED:**
- **Hoisting Limit**: ~25k tokens per hoisted file; files exceeding this are silently ignored

### Key Mechanism Understanding

The Read tool records actual content to session `.jsonl` files, but a separate context management system decides what actually reaches the model. The session file logs tool execution, NOT model context. Phantom read markers (`<persisted-output>` or `[Old tool result content cleared]`) appear nowhere in session files—only in agent self-reports.

### Two Eras of Phantom Reads

| Era | Versions | Error Mechanism |
|-----|----------|-----------------|
| 1 | ≤2.0.59 | `[Old tool result content cleared]` |
| 2 | ≥2.0.60 | `<persisted-output>` markers |

### Critical Pattern: "Clean Gap"

Successful sessions exhibit:
1. Early reset at <50% (during setup)
2. Uninterrupted processing window of 35-40%
3. Late reset at >90% (after work completes)

Failures occur when this gap is fragmented by mid-session resets.

---

## Consolidated Theory Document

Created `docs/core/Consolidated-Theory.md` integrating:
1. Previous theories from Investigation Journal
2. User's new findings from Experiment-Methodology-04 tinkering
3. The X + Y threshold overflow model

### Key New Insights from User's Manual Testing

**All Methodology-04 scenarios succeed** because X + Y fits within context window:
- Easy: 73K + 40K = 113K < threshold
- Medium: 92K + 40K = 132K < threshold
- Hard: 120K + 40K = 160K < threshold

**Phantom reads only manifested when files were added** (module-epsilon, module-phi) to push Y higher.

### The X + Y Model (NEW PRIMARY THEORY)

- **X** = Pre-operation context consumption
- **Y** = Operation context requirement (files read during trigger)
- **T** = Context window threshold (appears to be sub-200K)

**Phantom reads require X + Y > T**

Within-threshold operations are safe regardless of utilization percentage.

### Reframed Understanding of Previous Theories

| Theory | Original | Reframed |
|--------|----------|----------|
| Headroom | Universal threshold (<80K remaining = danger) | Relative to Y; headroom must accommodate operation |
| Reset Timing | Mid-session resets cause phantom reads | Artifact of when deferred reads occur in flow |
| Reset Count | More resets = more failures | Downstream indicator; more resets = more opportunities |
| Clean Gap | Required for success | Allows operation to complete before reset |

### Open Investigations Flagged

1. **Token accounting discrepancy**: ~25K tokens unaccounted (thinking? overhead?)
2. **Context reporting accuracy**: Harness reports "0% remaining" at 90% consumption
3. **Hoisting vs agent-initiated reads**: Different code paths?
4. **Reset trigger conditions**: Still unknown what causes a reset

### Conditions Required for Phantom Reads (All Must Be True)

1. Threshold Overflow: X + Y > T
2. Deferred Reads: Multiple files read simultaneously
3. Agent-Initiated: Reads triggered by agent, not hoisting
4. Reset During Processing: Context reset while reads are deferred

---

## Documentation Updates

### Investigation-Journal.md
Added new entry "2026-01-23: Consolidated Theory and X + Y Model" documenting:
- The critical discovery from Methodology-04 trials
- The X + Y model as primary framework
- Reframing of previous theories
- Four conditions required for phantom reads
- Open investigations and next steps

### README.md
Updated to reflect consolidated theory:
- Replaced "31-Trial Analysis" section with "The X + Y Model" section
- Added "Four Conditions Required" table
- Added "How Previous Theories Fit Together" explanation
- Updated theories summary table with new statuses
- Revised "How to Reproduce" section with X + Y framing
- Updated references to include Consolidated-Theory.md

---

