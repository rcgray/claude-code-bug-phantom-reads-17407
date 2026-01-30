# Work Journal - 2026-01-29 15:39
## Workscope ID: Workscope-20260129-153940

## Custom Workscope

Assigned via `--custom` flag. Task: `/refine-plan docs/tickets/open/upgrade-trial-data-schema-1-3.md`

## Investigation Log

### Files Read
- `docs/tickets/open/upgrade-trial-data-schema-1-3.md` — Target WPD
- `dev/karpathy/extract_trial_data.py` — Primary implementation file
- `.claude/commands/update-trial-data.md` — Karpathy command definition
- `docs/experiments/results/Build-Scan-Discrepancy-Analysis.md` — Step 1.4 findings that motivated changes
- `dev/misc/barebones-2121/20260128-150640/trial_data.json` — FAILURE verification trial
- `dev/misc/repro-attempts-04-2120/20260127-095002/trial_data.json` — SUCCESS verification trial
- `docs/experiments/guides/Trial-Analysis-Guide.md` — Analysis guide (updated in plan)
- JSONL raw session file (head) — Verified usage object structure
- `tool-results/` directory listing — Verified persistence mapping

### Findings Presented to User (10 items)

1. `content_gap` formula mismatch with Step 1.4 description
2. Persistence mapping includes non-Read tools (Bash date command)
3. Tool-results filename parsing assumption undocumented
4. JSONL field names differ from schema output names
5. Phase 2 doesn't handle zero-reset edge case
6. Phase 3 needs empty structure for no-persistence trials
7. Phase 6 verification assertion imprecise for SUCCESS trials
8. Trial Analysis Guide update missing from implementation plan
9. `peak_cache_read` is redundant/convenience alias
10. No batch re-processing task for existing trials

### User Decisions

All 10 findings accepted. Specific decisions:
1. Renamed `content_gap` → `compaction_loss` with accurate description
2. Added `persisted_non_reads` field for complete accounting
3. Added filename format note
4. Added JSONL Field Name Mapping table
5. Added zero-reset no-op note in Phase 2
6. Added empty persistence_mapping structure definition
7. Tightened verification language (field name updated per #1)
8. Added Phase 6 (4 tasks) for Trial Analysis Guide updates
9. Kept with convenience alias note
10. Clarified as by-design in Backward Compatibility section

### Changes Applied to WPD

Updated `docs/tickets/open/upgrade-trial-data-schema-1-3.md` with all agreed changes:
- Problem Description: Fixed content_gap description to accurately describe compaction_loss
- Added new "JSONL Field Name Mapping" section under Investigation & Analysis
- Updated "Proposed Solution" to include Trial Analysis Guide
- Updated schema examples throughout (content_gap → compaction_loss, added persisted_non_reads)
- Added empty persistence_mapping structure for no-persistence case
- Added tool-results filename format note
- Added peak_cache_read convenience alias note
- Updated Backward Compatibility with batch re-processing clarification
- Updated Expected Benefits (content_gap → compaction_loss)
- Updated Related Files (Trial Analysis Guide now required, not optional)
- Updated Implementation Plan: refined task descriptions in Phases 1-5, added Phase 6 (Trial Analysis Guide), renumbered old Phase 6 → Phase 7 with tightened verification criteria
