# Work Journal - 2026-01-26 13:40
## Workscope ID: Workscope-20260126-133959

## Initialization

- **Session Type**: Custom workscope (`--custom` flag)
- **Project**: Phantom Reads Investigation (Claude Code Issue #17407)
- **Status**: Awaiting custom workscope from User

## Project-Bootstrapper Onboarding

### Mandatory Files to Read (Phase 1 - Core System):
1. `docs/read-only/Agent-Rules.md` - Strict behavioral rules
2. `docs/read-only/Agent-System.md` - User Agent and Special Agent collaboration
3. `docs/read-only/Checkboxlist-System.md` - Task tracking with checkbox states
4. `docs/read-only/Workscope-System.md` - Work assignment and tracking
5. `docs/read-only/Documentation-System.md` - Document organization

### Coding Standards (Phase 2 - If workscope involves code):
6. `docs/read-only/standards/Coding-Standards.md` - General coding principles
7. `docs/read-only/standards/Python-Standards.md` - Python-specific requirements

### Critical Rules Highlighted:
- **Rule 5.1**: NO backward compatibility - app has not shipped
- **Rule 3.4**: NO meta-process references in product artifacts
- **Rule 3.11**: Write-protected directories → copy to workbench
- **Rule 3.5**: Specifications MUST match implementation
- **Rule 3.12**: Verify proof of work from Special Agents
- **Rules 3.15 & 3.16**: Escalate ALL issues to User

### Onboarding Status: COMPLETE
All core system files were read during `/wsd:boot` execution.

---

## Custom Workscope: Investigation Priority Analysis

**Task**: Analyze completed Experiment-04* results and determine next steps for the investigation.

### Context Documents Reviewed:
- `docs/core/Investigation-Journal.md` (1,445 lines)
- `docs/core/Research-Questions.md` (743 lines)
- `docs/core/Post-Experiment-04-Ideas.md` (569 lines)

---

## Discussion Summary

### Initial Analysis (Corrected by User)

My initial analysis proposed three new experiments:
1. **04M**: X Boundary Exploration (varying X between 0-73K)
2. **04N**: 1M Model Stress Test
3. **04O**: Hoisting Code Path Investigation

The User provided valuable corrections:

**On 04M**: This is essentially what already exists with `/setup-easy`, `/setup-medium`, `/setup-hard`. The key insight I missed: varying X alone (Easy vs Hard) **did not change outcomes** when Y was high (9 files). What changed outcomes was the Y value (7 files vs 9 files). My proposal was regressive—hunting for a "magic X value" rather than understanding the X+Y interaction.

**On 04N**: The 1M model experiment was a **one-time diagnostic** to validate T as a relevant variable, NOT a direction to pursue. The investigation must remain focused on the 200K model.

**On 04O**: I couldn't differentiate it from existing experiments 04A or 04D. Proposal withdrawn as poorly conceived.

### Key Realization: The Current Mystery

The investigation's current state:
- **Method-04 with Y=42K (7 files)**: ALL scenarios succeed (regardless of X)
- **Method-04 with Y=57K (9 files)**: ALL scenarios fail (regardless of X)

This contradicts simple X+Y > T because:
- Method-04 Easy (X+Y = 130K): **FAILURE**
- Method-03 Hard (X+Y = 162K): **SUCCESS**

The higher total succeeds; the lower total fails! The interaction is more complex than additive.

### Documentation Updates Completed

1. **RQ-B8 Reframed**: Changed from "finding magic X and Y thresholds" to "understanding the X+Y interaction surface with respect to T". Added research caution against hunting for magic numbers.

2. **1M Model Scope Notes Added**:
   - RQ-G4: Added scope note that 04K was diagnostic only
   - RQ-G5: Added scope note that 1M is not a direction to pursue
   - Confirmed Mitigations section: Reordered and noted 1M is out of scope
   - Post-Experiment-04-Ideas.md: Added scope limitation to 04K definition
   - Execution plan: Marked Phase 3 as complete with diagnostic-only note

### Remaining Valuable Experiments

**04F (File Count vs Tokens)** remains valuable because:
- Method-03 → Method-04 changed BOTH file count (7→9) AND token count (42K→57K)
- 04F would isolate which variable matters by using fewer, larger files
- Still requires significant preparation (mega-spec consolidation)

### Project Goal Clarification (from User)

The goal is **Aim #3 from PRD.md**: Provide reproducible cases for GitHub users:
- **Easy**: 0% failure rate (no phantom reads)
- **Medium**: 50% failure rate
- **Hard**: 100% failure rate

We're not academically mapping the X+Y surface—we're trying to find working repro scenarios.

---

## Files Modified

1. `docs/core/Research-Questions.md`:
   - RQ-B8: Reframed to emphasize X+Y interaction surface, not magic thresholds
   - RQ-G4: Added scope note (1M diagnostic only)
   - RQ-G5: Added scope note (1M out of scope)
   - Confirmed Mitigations: Reordered, noted 1M out of scope

2. `docs/core/Post-Experiment-04-Ideas.md`:
   - Experiment-04K: Added scope limitation note
   - Phase 3: Marked complete with diagnostic-only note
   - Document history: Updated

---

## Follow-up Discussion: Token Accounting and Experiment-04M

### Token Accounting Clarification

User clarified the confusion about X values and token accounting:

| Term | Definition |
|------|------------|
| **Baseline** | ~23K tokens (harness system prompt, tools) - present in ALL sessions |
| **Preload** | File tokens hoisted via `@` notation |
| **Overhead** | ~38-42% additional observed beyond file content |
| **X (total)** | Baseline + Preload + Overhead = observed value from `/context` |

**Setup Command Breakdown**:
- `/setup-none`: X ≈ 23K (0 preload + 23K baseline)
- `/setup-easy`: X ≈ 73K (35K preload + 23K baseline + 15K overhead)
- `/setup-medium`: X ≈ 92K (50K preload + 23K baseline + 19K overhead)
- `/setup-hard`: X ≈ 120K (68K preload + 23K baseline + 29K overhead)

### Experiment-04M Properly Scoped

My earlier proposal for `/setup-30k` and `/setup-50k` was confusing because I was referencing **total observed X** values, while the user was thinking about **preload file tokens**. We clarified:

- The gap to explore is between `/setup-none` (X≈23K) and `/setup-easy` (X≈73K)
- Available single-file preload options range from 14.7K to 19.3K file tokens
- Each produces roughly X≈44K to X≈50K observed

**Experiment-04M** was properly designed and added to Post-Experiment-04-Ideas.md.

### Other Key Insights

1. **04A disproves file-count limit**: 04A used 9 files and succeeded (because X≈23K was low). If 9 files was inherently dangerous, 04A would have failed.

2. **04A disproves epsilon/phi specific content issue**: 04A used epsilon/phi and succeeded. The content isn't the issue.

3. **Git branch approach for 04B/04C/04F**: Instead of surgical edits, we can branch the repo and restore pre-epsilon/phi state. This enables running all three experiments more easily.

### Agreed Next Steps

1. **04M**: Create `/setup-mid` and test X≈50K with Y=57K
2. **04C/04F via git branch**: Restore pre-epsilon/phi state and run both experiments
3. **04G**: Test sequential vs parallel reads (lower priority)

---

## Final Files Modified (Complete List)

1. **`docs/core/Research-Questions.md`**:
   - RQ-B8: Complete reframe (magic thresholds → interaction surface)
   - RQ-G4: Added scope note (1M diagnostic only)
   - RQ-G5: Added scope note (1M out of scope)
   - Confirmed Mitigations: Reordered, noted 1M out of scope

2. **`docs/core/Post-Experiment-04-Ideas.md`**:
   - Added Experiment-04M definition
   - Experiment-04K: Added scope limitation
   - Priority Summary: Complete overhaul (completed experiments, new tiers)
   - Execution Plan: Complete overhaul (phases 1-3 complete, new current phase)
   - Preparation tables: Added 04M
   - Document history: Updated

3. **`docs/core/Investigation-Journal.md`**:
   - Added 2026-01-26 entry: Token Accounting Clarification and Experiment Status Update

---

## Session Status: COMPLETE

Workscope accomplished:
- ✅ Analyzed completed Experiment-04* results
- ✅ Identified documentation gaps and corrected them
- ✅ Added scope limitations for 1M model experiments
- ✅ Reframed RQ-B8 to prevent "magic number hunting"
- ✅ Clarified token accounting terminology
- ✅ Designed Experiment-04M
- ✅ Established next steps: 04M and 04B/04C/04F via git branch

