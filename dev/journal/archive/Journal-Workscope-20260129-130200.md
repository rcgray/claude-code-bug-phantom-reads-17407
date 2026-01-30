# Work Journal - 2026-01-29 13:02
## Workscope ID: Workscope-20260129-130200

## Initialization

- Read `wsd-init-project-introduction` section and followed directions (read `docs/core/PRD.md`)
- Executed `/wsd:boot` - read all six WSD platform documents:
  - Agent-System.md
  - Agent-Rules.md
  - Design-Decisions.md
  - Documentation-System.md
  - Checkboxlist-System.md
  - Workscope-System.md
- Generated Workscope ID: `20260129-130200`
- Created Work Journal at `dev/journal/archive/Journal-Workscope-20260129-130200.md`
- `--custom` flag detected: Skipping Task-Master assignment, awaiting custom workscope from User

## Custom Workscope

User assigned: Build Scan Discrepancy Investigation - Phase 1 analysis across multiple collections.

**Planning document**: `docs/experiments/planning/Build-Scan-Discrepancy-Investigation.md`
**Results document**: `docs/experiments/results/Build-Scan-Discrepancy-Analysis.md`
**Analysis guide**: `docs/experiments/guides/Trial-Analysis-Guide.md`

## Step 1.1: Pre-Process `barebones-2120-2` — COMPLETE

Pre-processing already completed by User. All 11 trials have `trial_data.json` files. Extracted key metrics from all 11 trials and 5 comparison trials from original 2120 collection. Key finding: `has_tool_results` perfectly discriminates outcomes (10/10 true→FAILURE/UNKNOWN, 1/1 false→SUCCESS but protocol violation). Reset thresholds differ dramatically: original 2120 at 160-173K vs 2120-2 at 123-132K.

## Step 1.2: Compare 2120 Success vs 2120-2 Success — COMPLETE

The lone SUCCESS in 2120-2 (trial 140143) is another protocol violation — read only 6 of 9 files, skipping the same three modules as the 2121 protocol violation. Zero valid SUCCESS trials exist in the 2120-2 collection.

## Step 1.3: Compare Failure Profiles Across Collections — COMPLETE

Compared 18 FAILURE trials across 4 collections (2120-2, 2121, 2122, repro-04-barebones).

Key findings:
1. **`has_tool_results: true` is universal**: 18/18 failures (100%). Combined with 6/6 successes having `false`, the discriminator is 24/24 (100%).
2. **Affected files are position-dependent**: `module-alpha.md` in 100% of failures, but the full set varies based on agent read order. Not intrinsic to specific files.
3. **Two distinct reset profiles**: Profile A (mid-session double reset at ~123-132K) in 2120-2 and some 2122; Profile B (late single reset at ~160K) in 2121 and some 2122. Both produce phantom reads because persistence is the root cause, not resets.
4. **2122 is the key insight**: Contains BOTH profiles within one build, proving reset profile isn't build-dependent.
5. **Synthesis**: One root cause (persistence enabled), variable presentation (reset timing, affected files, agent recovery behavior).
