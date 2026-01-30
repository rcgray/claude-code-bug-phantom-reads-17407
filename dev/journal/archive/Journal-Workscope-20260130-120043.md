# Work Journal - 2026-01-30 12:00
## Workscope ID: Workscope-20260130-120043

## Custom Workscope

**Assignment**: Cross-reference global docs against methodology detail docs to identify discrepancies, missing information, or inaccuracies. The detail docs (Experiment-Methodology-01 through 04) are the Source of Truth.

**Global Docs Under Review:**
- `docs/core/PRD.md`
- `docs/core/Timeline.md`
- `docs/core/Investigation-Journal.md`
- `docs/core/Research-Questions.md`
- `README.md`

**Detail Docs (Source of Truth):**
- `docs/experiments/methodologies/Experiment-Methodology-01.md`
- `docs/experiments/methodologies/Experiment-Methodology-02.md`
- `docs/experiments/methodologies/Experiment-Methodology-03.md`
- `docs/experiments/methodologies/Experiment-Methodology-04.md`

## Work Log

### Step 1: Read all documents
- Read all 5 global docs and all 4 methodology detail docs
- Investigation-Journal.md is ~109KB; read through methodology-relevant sections via chunked reads and grep searches

### Step 2: Cross-reference analysis

#### Finding 1: PRD methodology section outdated (FIXED)
**Document**: `docs/core/PRD.md`, "Experiment Methodology" section
**Issue**: The "Current Methodology" section only linked to Methodology-01 and Methodology-02. Methodology-03 and Methodology-04 were completely missing. The "Methodology Evolution" subsection only described two phases, omitting the Methodology-03 → Methodology-04 transition.
**Fix**: Expanded the section to list all four methodology versions with correct descriptions. Added Phase 3 (Methodology 03, superseded) and Phase 4 (Methodology 04, current) to the Methodology Evolution subsection.

#### Finding 2: README "How to Reproduce" section inaccurate (FIXED)
**Document**: `README.md`, "How to Reproduce" section
**Issue**: The bullet points describing key reproduction factors said "Multiple file reads during onboarding (inflates baseline context)" which describes the WSD-Dev-02 observation, NOT Methodology-04's actual mechanism. Methodology-04 uses hoisted file preloading via `/setup-*` commands with `@` notation, not onboarding reads.
**Fix**: Replaced the second and third bullet points to accurately describe hoisted file preloading via `/setup-*` commands and the `/analyze-wpd` command's 9-file, ~57K token operation.

#### Finding 3: Methodology-02 Post-Op token values imprecise (FIXED)
**Document**: `docs/experiments/methodologies/Experiment-Methodology-02.md`, Results section
**Issue**: The easy-1 and medium-1 trials listed approximate Post-Op values ("~100K" and "~130K") when more precise data exists in the Investigation Journal (94K/47% and 123K/62% respectively). Hard-1 already had the precise value (149K/75%).
**Fix**: Updated easy-1 Post-Op from "~100K" to "94K (47%)" and medium-1 Post-Op from "~130K" to "123K (62%)".

#### Finding 4: PRD trial count outdated (FIXED)
**Document**: `docs/core/PRD.md`, Trigger Conditions section
**Issue**: Said "Based on 22 controlled trials" but the Reset Timing Theory was actually validated on 31 trials (22 WSD-Dev-02 + 9 repro-attempts-02). Also, "Current understanding (22-trial analysis)" was outdated.
**Fix**: Updated to "31 controlled trials (22 WSD-Dev-02 + 9 repro-attempts-02)" and "(31-trial analysis)". Also added reference to `Repro-Attempts-02-Analysis-1.md` in the analysis docs list.

#### Finding 5: Timeline methodology entries - ACCURATE (no changes needed)
**Document**: `docs/core/Timeline.md`
All methodology-related entries (Jan 19, Jan 22, Jan 22-23, Jan 23) accurately reflect the methodology documents. The Timeline correctly dates the Methodology-03 design, the first trial collection, the discovery of hoisting limits and `/context` limitations, and the restructuring to Methodology-04.

#### Finding 6: Investigation-Journal methodology entries - ACCURATE (no changes needed)
**Document**: `docs/core/Investigation-Journal.md`
All methodology-related entries match the detail docs. The Jan 15, Jan 19, Jan 22, Jan 22-23, and Jan 23+ entries accurately describe:
- The trial protocol evolution
- The Methodology-03 design rationale
- The discovery of the ~25K hoisting limit
- The `/context` command limitation
- The restructuring to Methodology-04 with separated setup/analysis commands
- Calibration measurements matching Methodology-04

#### Finding 7: Research-Questions methodology references - ACCURATE (no changes needed)
**Document**: `docs/core/Research-Questions.md`
Methodology references in RQ-B8, RQ-D3, RQ-F4 and others correctly use "Method-03" and "Method-04" as shorthand for file composition eras (Y=42K vs Y=57K). RQ-F4's token overhead data uses measured API values that differ from Methodology-04's estimated token counts, but this is a precision difference, not an error.

### Observations for the User

1. **Methodology-04 token counts are estimates**: The file token counts in Methodology-04 (lines 291-296) use "~" prefix and are approximate. RQ-F4 has more precise measured values from the Anthropic API. Consider updating Methodology-04 with measured values if precision matters.

2. **Methodology-03 never produced valid data**: All 9 Methodology-03 trials succeeded trivially due to the hoisting failure. The doc preserves the designed protocol but notes it was "superseded" - this is appropriate.

3. **The "Method-03/04" shorthand**: Throughout the project, "Method-03" and "Method-04" are used to refer to both the methodology versions AND the Y-size eras (7 files/42K vs 9 files/57K). This dual meaning is consistently used but could confuse new readers. Not something to fix now but worth noting.

## Summary of Edits Made

| File | Edit | Type |
|------|------|------|
| `docs/core/PRD.md` | Expanded methodology section to include all 4 versions | Content addition |
| `docs/core/PRD.md` | Updated trial count from 22 to 31 | Accuracy correction |
| `docs/core/PRD.md` | Added Repro-Attempts-02-Analysis reference | Missing reference |
| `README.md` | Fixed "How to Reproduce" bullets to describe actual Method-04 mechanism | Accuracy correction |
| `docs/experiments/methodologies/Experiment-Methodology-02.md` | Fixed Post-Op token values for easy-1 and medium-1 | Precision improvement |

