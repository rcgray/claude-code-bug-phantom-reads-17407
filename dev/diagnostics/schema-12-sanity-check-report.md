# Schema 1.2 Sanity Check Report

**Date:** 2026-01-21
**Trial Analyzed:** `dev/misc/wsd-dev-02/20260120-085642`
**Reviewer:** User Agent 20260121-101637

---

## Executive Summary

The schema 1.1 → 1.2 upgrade introduces **CRITICAL REGRESSIONS** in the `extract_trial_data.py` implementation that break key functionality beyond the intended scope of adding success/failure tracking for Read operations.

**Recommendation:** ❌ **DO NOT DEPLOY** - Roll back changes and fix critical issues before re-attempting upgrade.

---

## Critical Issues Identified

### 1. ❌ CRITICAL: context_metrics Are All Null

**Schema 1.1 (Correct):**
```json
"context_metrics": {
  "pre_operation_tokens": 88000,
  "pre_operation_percent": 44,
  "post_operation_tokens": 155000,
  "post_operation_percent": 78,
  "headroom_at_trigger": 112000
}
```

**Schema 1.2 (Broken):**
```json
"context_metrics": {
  "pre_operation_tokens": null,
  "pre_operation_percent": null,
  "post_operation_tokens": null,
  "post_operation_percent": null,
  "headroom_at_trigger": null
}
```

**Root Cause:** The new `compute_metrics()` function attempts to extract context snapshots from the chat export using a regex pattern, but the pattern doesn't match the actual format in the chat export.

**Evidence from Chat Export:**
```
claude-opus-4-5-20251101 · 88k/200k tokens (44%)
```

**Pattern in Code:**
```python
snapshot_pattern = r"(\d+)K?\s+tokens?\s+\((\d+)%\)"
```

**Problem:** The pattern looks for `tokens (XX%)` but the actual format is `88k/200k tokens (44%)` with the total context window included. The old code used pattern `r'(\d+)k/\d+k tokens \((\d+)%\)'` which would have matched.

**Impact:** This breaks ALL token-based analysis, reset timing calculations, and headroom metrics. This is a REGRESSION unrelated to the success/failure tracking feature.

---

### 2. ❌ CRITICAL: affected_files List Is Completely Wrong

**Schema 1.1 (Correct - 6 files):**
```json
"affected_files": [
  "docs/features/manifest-driven-pipeline/Manifest-Driven-Pipeline-Overview.md",
  "docs/features/pre-staging-script/Pre-Staging-Script-Overview.md",
  "docs/core/WSD-Runtime-Metadata-Schema.md",
  "docs/features/stage-release-script/Stage-Release-Script-Overview.md",
  "dev/scripts/stage_release.py",
  "dev/scripts/build_package.py"
]
```

**Schema 1.2 (Broken - 16 files):**
```json
"affected_files": [
  "docs/read-only/Checkboxlist-System.md",
  "docs/read-only/Agent-Rules.md",
  "docs/core/Design-Decisions.md",
  "docs/read-only/standards/TypeScript-Standards.md",
  "docs/features/manifest-driven-pipeline/Manifest-Driven-Pipeline-Overview.md",
  "docs/features/install-and-update/Installation-System.md",
  "docs/features/content-hashing/Content-Hashing-Overview.md",
  "docs/read-only/Documentation-System.md",
  "docs/core/PRD.md",
  "docs/read-only/standards/Python-Standards.md",
  "docs/read-only/Workscope-System.md",
  "docs/read-only/Agent-System.md",
  "docs/core/WSD-Runtime-Metadata-Schema.md",
  "docs/features/stage-release-script/Stage-Release-Script-Overview.md",
  "docs/read-only/standards/Coding-Standards.md",
  "docs/features/pre-staging-script/Pre-Staging-Script-Overview.md"
]
```

**Evidence from Chat Export:**
The actual self-reported phantom reads in the chat export clearly state:

> Affected Read calls that returned <persisted-output> without me following up:
> 1. docs/features/manifest-driven-pipeline/Manifest-Driven-Pipeline-Overview.md
> 2. docs/features/pre-staging-script/Pre-Staging-Script-Overview.md
> 3. docs/core/WSD-Runtime-Metadata-Schema.md
> 4. docs/features/stage-release-script/Stage-Release-Script-Overview.md
> 5. dev/scripts/stage_release.py
> 6. dev/scripts/build_package.py

**Root Cause:** The new `parse_chat_export()` function appears to be extracting affected files incorrectly, possibly picking up file references from OTHER parts of the chat (like onboarding file lists) rather than from the actual phantom read self-report.

**Impact:** This breaks the entire purpose of the outcome analysis. The affected_files list now includes files that were successfully read (docs/read-only/Agent-Rules.md, etc.) and misses the actual failed reads. This is a REGRESSION unrelated to the success/failure tracking feature.

---

### 3. ❌ CRITICAL: outcome.notes Is Empty

**Schema 1.1 (Correct):**
```json
"notes": "Session agent confirmed phantom reads. Early Read calls returned <persisted-output> redirects that were not followed up. Later reads and Grep calls returned inline content."
```

**Schema 1.2 (Broken):**
```json
"notes": ""
```

**Root Cause:** The new `parse_chat_export()` function doesn't extract the explanatory notes from the self-report.

**Impact:** Loss of important context about the failure mode. This is a REGRESSION.

---

### 4. ❌ MAJOR: token_analysis.reads_with_tokens cumulative_estimate Is Wrong

**Schema 1.1 (Correct):**
```json
"reads_with_tokens": [
  {
    "sequence": 1,
    "file_path": "dev/journal/archive/Journal-Workscope-20260120-093143.md",
    "token_count": 1048,
    "cumulative_estimate": 89048,  // ← Starts at pre_op_tokens (88000) + 1048
    "session_line": 14
  },
  ...
]
```

**Schema 1.2 (Broken):**
```json
"reads_with_tokens": [
  {
    "sequence": 1,
    "file_path": "dev/journal/archive/Journal-Workscope-20260120-093143.md",
    "token_count": 1048,
    "cumulative_estimate": 1048,  // ← Starts at 0 + 1048 (WRONG)
    "session_line": 14
  },
  ...
]
```

**Root Cause:** The `/update-trial-data` command instructions state: "Calculate cumulative estimate: start with `pre_operation_tokens`, add each file's tokens in sequence". However, since `pre_operation_tokens` is null (due to Issue #1), the cumulative calculation starts at 0 instead of 88000.

**Impact:** All cumulative token estimates are understated by ~88K tokens. This makes reset context analysis meaningless because it no longer shows actual context consumption at reset points.

**Evidence:**
- Schema 1.1 reset 1: cumulative_tokens_before = 156856 (157K tokens before reset)
- Schema 1.2 reset 1: cumulative_tokens_before = 68856 (only 69K - missing the 88K baseline)

This is a **cascading failure** from Issue #1.

---

### 5. ✅ EXPECTED: Timeline event_count Changed (48 → 104)

**Schema 1.1:**
- total_events: 48
- reset_positions_percent: [54.2, 81.3, 97.9]

**Schema 1.2:**
- total_events: 104
- reset_positions_percent: [60.6, 80.8, 100.0]

**Root Cause:** The new implementation now includes `user_input` events in the timeline, which weren't tracked before.

**Impact:** This changes the denominator for reset position calculations, making comparisons to historical data difficult. However, this is **EXPECTED and CORRECT** - the new approach gives a more accurate picture of session progression.

**Note:** The reset position percentages are still similar (within ~6 percentage points), suggesting the core reset detection is working correctly.

---

### 6. ✅ CORRECT: tool_use_id Fixed for Sequence 4

**Schema 1.1 (Duplicate IDs - Bug):**
- Sequence 4 (line 43): `toolu_014gP4J8gYS4JSAC7vvjqnW5`
- Sequence 12 (line 65): `toolu_014gP4J8gYS4JSAC7vvjqnW5` ← SAME ID (impossible)

**Schema 1.2 (Fixed):**
- Sequence 4 (line 43): `toolu_011xbvfKFQHdLoydaB5ZN4Y2` ← Correct ID
- Sequence 12 (line 65): `toolu_014gP4J8gYS4JSAC7vvjqnW5`

**Impact:** The new implementation correctly extracts unique tool_use_ids from the session file. This is a BUG FIX.

---

### 7. ✅ CORRECT: Success Tracking Added

**Schema 1.2 adds:**
```json
"file_reads": {
  "total_operations": 15,
  "successful_operations": 15,
  "failed_operations": 0,
  "failed_reads": [],
  "reads": [
    {
      "sequence": 1,
      ...
      "success": true  // ← NEW FIELD
    }
  ]
}
```

**Impact:** This is the **intended feature** of the schema upgrade. The new schema correctly tracks that all 15 Read operations in this trial succeeded (returned file content, not errors).

**Validation:** Checked the session file - no `<tool_use_error>` tags were found in any Read tool results, confirming all 15 reads succeeded.

---

### 8. ⚠️ MINOR: Batch ID Indexing Changed (1-based → 0-based)

**Schema 1.1:**
- batch_id ranges from 1 to 15

**Schema 1.2:**
- batch_id ranges from 0 to 14

**Impact:** This is cosmetic but creates inconsistency with historical data. Not a functional problem, but makes comparisons harder.

---

## Testing Against Intended Scope

The original ticket (`docs/tickets/closed/investigate-trial-data-failed-read-recording.md`) specified:

**Intended Changes:**
1. ✅ Add `success` boolean field to each read entry
2. ✅ Add `error` field when success is false
3. ✅ Add `successful_operations` and `failed_operations` counters
4. ✅ Add `failed_reads` section for diagnostic visibility
5. ✅ Update unique_files to only count successful reads

**All intended changes were correctly implemented.**

**Unintended Regressions:**
1. ❌ context_metrics parsing broke
2. ❌ affected_files extraction broke
3. ❌ outcome.notes extraction broke
4. ❌ cumulative_estimate calculations broke (cascading failure)

---

## Root Cause Analysis

The Python implementation (`dev/diagnostics/extract_trial_data.py`) was **completely rewritten** rather than **incrementally updated**. The rewrite introduced new bugs in areas unrelated to the success/failure tracking feature.

**Evidence:**
```bash
git diff --stat dev/diagnostics/extract_trial_data.py
# 1035 lines changed (insertions + deletions)
```

This is not a "fix" - it's a ground-up rewrite that broke working functionality.

---

## Recommendations

### Immediate Actions

1. **❌ REJECT the current schema 1.2 implementation** - Do not deploy to production or use for analysis

2. **Roll back to schema 1.1** for all existing trials until fixes are complete

3. **Create a proper fix** that:
   - Adds success/failure tracking (the intended feature) ✅
   - DOES NOT break context_metrics extraction
   - DOES NOT break affected_files extraction
   - DOES NOT break outcome.notes extraction
   - DOES NOT break cumulative_estimate calculations

### Implementation Approach

**DO NOT rewrite the entire script.** Instead:

1. Start with the working schema 1.1 implementation
2. Add ONLY the success/failure tracking logic:
   - Build tool_results_map while parsing
   - Check for `<tool_use_error>` tags
   - Add `success` and `error` fields to read entries
   - Add `successful_operations`, `failed_operations`, `failed_reads` sections
3. Update schema_version to 1.2
4. Test on known-good trial (one with failed reads, one without)
5. Verify NO REGRESSIONS in unrelated fields

### Testing Checklist

Before deploying schema 1.2:

- [ ] context_metrics are populated correctly
- [ ] affected_files match the self-reported list (6 files for this trial)
- [ ] outcome.notes contain the self-reported explanation
- [ ] cumulative_estimate starts at pre_operation_tokens, not 0
- [ ] success tracking correctly identifies failed vs successful reads
- [ ] failed_reads section contains only actual failures
- [ ] unique_files counts only successful reads

---

## Trial-Specific Verification

For trial `20260120-085642` specifically:

**Expected Values (from session data):**
- pre_operation_tokens: 88000 (from context snapshot: "88k/200k tokens (44%)")
- affected_files: 6 files (from self-report)
- outcome: FAILURE (phantom reads confirmed)
- All 15 Read operations succeeded (no `<tool_use_error>` tags found)

**Schema 1.1 Got Right:**
- context_metrics ✅
- affected_files ✅
- outcome.notes ✅
- cumulative_estimate ✅

**Schema 1.2 Got Wrong:**
- context_metrics ❌ (all null)
- affected_files ❌ (wrong list - 16 instead of 6)
- outcome.notes ❌ (empty)
- cumulative_estimate ❌ (starts at 0 not 88K)

---

## Conclusion

While the intended feature (success/failure tracking) was correctly implemented, the schema 1.2 upgrade introduced **4 critical regressions** that break core functionality. The large diff volume (1035 lines changed) suggests this was a rewrite rather than a targeted fix.

**The current schema 1.2 implementation should NOT be used for analysis** until the regressions are fixed. A proper incremental fix starting from the working schema 1.1 code is recommended.
