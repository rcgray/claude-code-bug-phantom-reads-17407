# Work Journal - 2026-01-29 23:56
## Workscope ID: Workscope-20260129-235637

## Initialization

- Read `docs/core/PRD.md` - Understood the Phantom Reads Investigation project
- Completed `/wsd:boot` - Read all six WSD platform system documents
- Generated Workscope ID: 20260129-235637
- Created Work Journal at `dev/journal/archive/Journal-Workscope-20260129-235637.md`
- Mode: `--custom` (awaiting User-provided workscope)

## Custom Workscope

**Assignment**: Analyze the `schema-13-2122` collection for Step 2.2 of the Build Scan Discrepancy Investigation. Then create theory documentation and update investigation plan/analysis documents based on findings.

**Context Documents Read**:
- `docs/experiments/planning/Build-Scan-Discrepancy-Investigation.md` - Investigation plan
- `docs/experiments/results/Build-Scan-Discrepancy-Analysis.md` - Results document (in progress)
- `docs/experiments/guides/Trial-Analysis-Guide.md` - Trial analysis procedures
- `docs/theories/Consolidated-Theory.md` - Existing X+Y model
- `docs/theories/Reset-Timing-Theory.md` - Existing reset timing theory (partial)

## Execution Log

### Task 1: Step 2.2 Analysis (schema-13-2122)

Read all 6 trial_data.json files from `dev/misc/schema-13-2122/`. Findings:
- ALL 6 trials: SUCCESS, has_tool_results=false (0% persistence)
- 5/6 used sub-agent delegation (has_subagents=true)
- 1/6 (trial 211109) read all 9 files directly — no persistence, 198K total_input, SUCCESS
- Cross-referenced with prior barebones-2122 (Jan 28): 6/6 FAILURE, 100% persistence
- COMPLETE REVERSAL: 100% failure → 100% success in ~24 hours

Wrote comprehensive Step 2.2 section to Analysis document including trial data table, comparison table, 6 observations, and interpretation.

### Discussion with User

User identified this as evidence of server-side variability dominating over client build versions. User confirmed 2.1.6 now shows Task tool delegation (Jan 30). User characterized the finding as a mitigation, not a fix. Rapid build releases (up to 2.1.26) suggest active tuning by Anthropic.

I provided nuanced analysis:
- Two separate transitions (Jan 27→28, Jan 28→29) need explaining
- Persistence not eliminated (still 80% on 2.1.20 direct reads, Jan 29)
- Delegation is a model behavior, not a harness behavior (server-influenced via model weights/system prompt)
- Caution against premature "fix" declaration (Jan 27 improvement also reverted)
- Mitigation characterization is more accurate than "fix"

User agreed with analysis and directed three documentation tasks.

### Task 2: Create Server-Side Variability Theory Document

Created `docs/theories/Server-Side-Variability-Theory.md` covering:
- Core claim: phantom reads governed by server-side state, not client builds
- Six pieces of evidence (2.1.22 reversal, external persistence decision, stochastic behavior, three server states, simultaneous delegation appearance, rapid build releases)
- Relationship to X+Y model (T_effective is externally variable)
- Implications for investigation, users, and reproduction
- Nature of the mitigation (not a fix; reduced persistence + delegation)
- Open questions (per-build configuration, model vs. prompt change, permanence)
- Theory status summary table

### Task 3: Update Investigation Plan

Updated `docs/experiments/planning/Build-Scan-Discrepancy-Investigation.md`:
- Replaced Step 2.3 (Cross-Machine Replication → Server-Side Behavior Verification on 2.1.6)
- Expanded Phase 3 with Step 3.3 (Closure Assessment)
- Updated Success Criteria with answers from completed steps
- Updated Priority and Sequencing diagram with completion status
- Updated Document History

### Task 4: Update Analysis Document

Updated `docs/experiments/results/Build-Scan-Discrepancy-Analysis.md`:
- Replaced Step 2.3 (Cross-Machine → 2.1.6 Verification with placeholder for future data)
- Wrote Phase 2 Synthesis (partial, Steps 2.1-2.2) with server-side variability finding
- Completed Step 3.1 (X+Y model revision with server-side variability)
- Answered RQ-BSD-1 (persistence is server-controlled, fully answered)
- Answered RQ-BSD-2 (discrepancy explained by server-side changes)
- Answered RQ-BSD-4 (persistence threshold is server-state-specific, not build-specific)
- Updated Document History

## Files Created

- `docs/theories/Server-Side-Variability-Theory.md` (NEW)

## Files Modified

- `docs/experiments/results/Build-Scan-Discrepancy-Analysis.md` (Step 2.2 written, Step 2.3 replaced, Phase 2 Synthesis written, Step 3.1 completed, RQ-BSD-1/2/4 answered, Document History updated)
- `docs/experiments/planning/Build-Scan-Discrepancy-Investigation.md` (Step 2.3 replaced, Phase 3 expanded, Success Criteria updated, Sequencing updated, Document History updated)

## Key Findings

1. **Build 2.1.22 reversed**: 100% failure (Jan 28) → 100% success (Jan 29). Zero persistence in any trial. Critical trial 211109 reached 198K total_input with no persistence.
2. **Server-side variability confirmed**: Three distinct server states observed across Jan 27-29. Same builds produce different outcomes on different days.
3. **Two independent mitigations identified**: (a) reduced persistence triggering, (b) model preference for sub-agent delegation
4. **Mitigation, not fix**: Persistence still observed in 80% of 2.1.20 direct-read trials on Jan 29. Root cause (persisted content replaced by markers) not addressed.
5. **Investigation redirected**: Step 2.3 now tests 2.1.6 for server-side behavior; Phase 3 includes closure assessment.

## Status

All assigned tasks complete. Awaiting User direction for next steps (Step 2.3 experiment execution, or further discussion).
