# Upgrade trial_data.json to Schema 1.3 — Enhanced Usage and Persistence Data

**Date Reported:** 2026-01-29
**Status**: Open
**Prerequisites**: None. This ticket can be executed independently.

## Problem Description

During Step 1.4 of the Build Scan Discrepancy Investigation, custom Python scripts were required to extract critical data that the existing `trial_data.json` (Schema 1.2) does not capture. Three categories of data were missing:

1. **Post-reset cache creation values**: The `cache_creation_input_tokens` field from assistant messages is not recorded in `token_progression`. This prevented calculating per-reset compaction losses — the difference between pre-reset `cache_read` and the sum of post-reset `cache_read` + `cache_creation`, revealing how many tokens were discarded during context reconstruction. For the FAILURE verification trial, this compaction loss was ~4K tokens; the cross-trial `cache_creation` difference of ~42K tokens (Step 1.4's headline finding) requires comparing two trials and cannot be derived from a single trial's data alone.

2. **Persistence mapping**: The `has_tool_results` boolean tells us persistence occurred, but not *which* tool results were persisted. Determining this required manually enumerating `tool-results/` files and matching their `toolu_*` IDs to `file_reads` entries. This mapping revealed that persistence is chronological (not size-based) — a finding impossible from the current schema.

3. **Total input accounting**: The current `peak_tokens` metric only captures `cache_read_input_tokens`, but `total_input` (cache_read + cache_creation + input_tokens) gives a more complete picture of context pressure. Both trials showed ~194K `total_input` at peak despite only ~160K `cache_read`, meaning sessions were much closer to the 200K limit than the current metric suggests.

These gaps forced analysts to write custom JSONL parsers for every investigation, defeating the purpose of the pre-processing pipeline.

## Investigation & Analysis

The extraction script (`dev/karpathy/extract_trial_data.py`) already parses assistant messages from the session JSONL but only extracts `cache_read_input_tokens` from the `usage` object. The `cache_creation_input_tokens`, `input_tokens`, and `output_tokens` fields are present in every assistant message but currently ignored.

The script also already detects whether `tool-results/` exists (`has_tool_results` boolean) but does not enumerate its contents or correlate them with `file_reads` entries.

All proposed changes are additions to the existing extraction logic. No new scripts are needed. The karpathy command (`.claude/commands/update-trial-data.md`) needs only its schema reference section updated.

**Key constraint**: The NLP outcome determination (Step 3 of the command) is unaffected by these changes. The extraction script outputs `PENDING_NLP` for outcome fields regardless of schema version.

### JSONL Field Name Mapping

The JSONL `usage` object uses specific field names that differ from the Schema 1.3 output field names. Implementers must map correctly:

| JSONL Field (source)          | Schema 1.3 Field (output) | Notes                           |
| ----------------------------- | ------------------------- | ------------------------------- |
| `cache_read_input_tokens`     | `cache_read_tokens`       | Already extracted in Schema 1.2 |
| `cache_creation_input_tokens` | `cache_creation_tokens`   | **New in 1.3**                  |
| `input_tokens`                | `input_tokens`            | **New in 1.3** (same name)      |
| `output_tokens`               | `output_tokens`           | **New in 1.3** (same name)      |

The JSONL `usage` object also contains a `cache_creation` sub-object with ephemeral breakdown (`ephemeral_5m_input_tokens`, `ephemeral_1h_input_tokens`) and a `service_tier` field. These are not extracted in Schema 1.3.

Example JSONL `usage` object:
```json
"usage": {
  "input_tokens": 2,
  "cache_creation_input_tokens": 98607,
  "cache_read_input_tokens": 15616,
  "cache_creation": {"ephemeral_5m_input_tokens": 0, "ephemeral_1h_input_tokens": 98607},
  "output_tokens": 1,
  "service_tier": "standard"
}
```

## Proposed Solution

Modify `dev/karpathy/extract_trial_data.py` to:
1. Extract full usage data from assistant messages (not just `cache_read_input_tokens`)
2. Enumerate `tool-results/` files and map them to `file_reads` entries
3. Compute derived metrics from the enhanced data
4. Bump schema version to `"1.3"`

Update `.claude/commands/update-trial-data.md` to reflect the new schema in its output reference section.

Update `docs/experiments/guides/Trial-Analysis-Guide.md` to document the new Schema 1.3 fields and their analytical applications.

### Schema Changes (All Additive)

**Enhanced `token_progression` entries:**
```json
{
  "sequence": 1,
  "cache_read_tokens": 159633,
  "cache_creation_tokens": 34889,
  "input_tokens": 0,
  "output_tokens": 1,
  "total_input": 194522,
  "session_line": 48
}
```

The `total_input` field is computed as: `cache_read_tokens + cache_creation_tokens + input_tokens`.

**Enhanced `reset_analysis.resets` entries** (3 new fields per reset):
```json
{
  "from_tokens": 159840,
  "to_tokens": 18148,
  "cache_creation_at_reset": 137557,
  "total_input_at_reset": 155715,
  "compaction_loss": 4135,
  "session_line": 58,
  "sequence_position": 58,
  "total_events": 68,
  "position_percent": 85.29
}
```

The `compaction_loss` field measures tokens discarded during context reconstruction for a single reset: `compaction_loss = from_tokens - (to_tokens + cache_creation_at_reset)`. A positive value indicates tokens were lost (content replaced by compact markers or dropped entirely). A negative value indicates the post-reset context was expanded beyond the pre-reset `cache_read` level (typical of SUCCESS trials where no content was persisted). This is a per-reset, single-trial metric — it does NOT represent the cross-trial "42K content gap" from Step 1.4, which requires comparing `cache_creation` values between a SUCCESS and FAILURE trial.

**New `persistence_mapping` section:**

When `has_tool_results` is true (persistence occurred):
```json
"persistence_mapping": {
  "persisted_tool_ids": ["toolu_01JqXD...", "toolu_01M6U9..."],
  "persisted_count": 6,
  "non_persisted_count": 4,
  "persisted_reads": [
    {"sequence": 1, "file_path": "pipeline-refactor.md", "tool_use_id": "toolu_01JqXD..."}
  ],
  "non_persisted_reads": [
    {"sequence": 6, "file_path": "integration-layer.md", "tool_use_id": "toolu_01SVVv..."}
  ],
  "persisted_non_reads": ["toolu_01PAx2..."]
}
```

When `has_tool_results` is false (no persistence) or no session subdirectory exists:
```json
"persistence_mapping": {
  "persisted_tool_ids": [],
  "persisted_count": 0,
  "non_persisted_count": 9,
  "persisted_reads": [],
  "non_persisted_reads": [
    {"sequence": 1, "file_path": "pipeline-refactor.md", "tool_use_id": "toolu_01TSEW..."}
  ],
  "persisted_non_reads": []
}
```

In the no-persistence case, all file reads appear in `non_persisted_reads` because no tool results were persisted to disk. Note that `non_persisted_count` reflects the total number of file reads, since the persistence mapping is scoped to the intersection of tool-results files and file_reads.

The `persisted_non_reads` field captures tool IDs found in the `tool-results/` directory that do NOT correspond to any `file_reads` entry (e.g., Bash command results like the `date` command). This ensures full accounting: `persisted_count = len(persisted_reads) + len(persisted_non_reads)`.

**Tool-results filename format**: Files in the `tool-results/` directory follow the naming pattern `{tool_use_id}.txt` (e.g., `toolu_01JqXDYnd3tmfuMbccjoUaFG.txt`). Extract the tool_use_id by stripping the `.txt` extension from the filename.

**New fields in `context_metrics`:**
```json
"initial_cache_read": 15616,
"total_input_at_peak": 194729,
"peak_cache_read": 159840
```

Note: `peak_cache_read` is a convenience alias — its value equals `max(cache_read_tokens)` across all `token_progression` entries. It is provided as a top-level metric for quick access without requiring iteration over the progression array.

### Backward Compatibility

All changes are additive — no existing fields are removed or renamed. Existing Schema 1.2 `trial_data.json` files remain valid. Re-running `/update-trial-data` on existing trials upgrades them to Schema 1.3 with the new fields populated. Batch re-processing of all existing trials is not required — the `/update-trial-data` command is idempotent and can be re-run manually on individual trials as analysis needs arise.

## Expected Benefits

1. **Eliminates custom JSONL scripts**: Future analysis can work entirely from `trial_data.json` without touching raw session files
2. **Compaction loss detection**: The `compaction_loss` field on resets immediately reveals whether tokens were discarded during context reconstruction
3. **Persistence analysis**: The `persistence_mapping` section enables chronological vs. size-based analysis without manual tool-results enumeration
4. **Accurate context pressure**: `total_input_at_peak` shows the true proximity to the 200K context limit

## Risk Assessment

**Low risk.** All changes are additive to existing extraction logic. The script already parses the relevant JSONL structures — it just needs to extract additional fields from them. No changes to the NLP outcome determination workflow. No changes to file I/O patterns or error handling.

**Testing approach**: Re-run the updated script on a known trial (e.g., `barebones-2121/20260128-150640`) and verify the new fields match the values discovered during the Step 1.4 manual analysis.

## Related Files

**Primary Implementation:**
- `dev/karpathy/extract_trial_data.py` — Extraction script (main changes)
- `.claude/commands/update-trial-data.md` — Karpathy command (schema reference update)

**Verification Data:**
- `dev/misc/barebones-2121/20260128-150640/trial_data.json` — FAILURE trial with known persistence mapping
- `dev/misc/repro-attempts-04-2120/20260127-095002/trial_data.json` — SUCCESS trial for comparison

**Documentation:**
- `docs/experiments/guides/Trial-Analysis-Guide.md` — Must be updated with new Schema 1.3 fields and their analytical applications
- `docs/experiments/results/Build-Scan-Discrepancy-Analysis.md` — Step 1.4 findings that motivated these changes

## Developer Notes

The 5th recommendation from Step 1.4 — `analysis_output_length` (measuring the char length of the agent's main analysis response as a confabulation signal) — was intentionally deferred. It requires protocol-specific logic to identify "the analysis" assistant message, making it fragile across different experiment methodologies. If needed later, it should be added as a protocol-specific annotation in the NLP step, not the extraction script.

## In-Flight Failures (IFF)

<!-- This section is required and should be left blank -->

## Implementation Plan

### Phase 1: Enhance Usage Data Extraction
- [x] **1.1** - Modify the assistant message parsing loop to extract `cache_creation_input_tokens`, `input_tokens`, and `output_tokens` from the JSONL `usage` object alongside the existing `cache_read_input_tokens` (see JSONL Field Name Mapping table above for source → output field names)
- [x] **1.2** - Add `cache_creation_tokens`, `input_tokens`, `output_tokens`, and `total_input` fields to each `token_progression` entry, where `total_input = cache_read_tokens + cache_creation_tokens + input_tokens`
- [x] **1.3** - Store the full usage data per assistant message in a lookup structure keyed by `session_line` so it can be referenced for reset enrichment in Phase 2

### Phase 2: Enrich Reset Entries
- [x] **2.1** - For each detected reset, look up the assistant message's full usage data at `session_line` and add `cache_creation_at_reset` and `total_input_at_reset` to the reset entry. If no resets exist, this phase is a no-op (the `resets` array remains empty with no new fields needed)
- [x] **2.2** - Compute `compaction_loss = from_tokens - (to_tokens + cache_creation_at_reset)` and add it to the reset entry. Positive values indicate tokens lost during reconstruction; negative values indicate post-reset expansion (typical in SUCCESS trials)

### Phase 3: Add Persistence Mapping
- [x] **3.1** - When `tool-results/` directory exists, enumerate its files and extract tool IDs by stripping the `.txt` extension from each filename (expected format: `{tool_use_id}.txt`, e.g., `toolu_01JqXDYnd3tmfuMbccjoUaFG.txt`)
- [x] **3.2** - Cross-reference persisted tool IDs against the `file_reads` entries (matching on `tool_use_id`) to build three lists: `persisted_reads` (persisted tool IDs that match a file_read), `non_persisted_reads` (file_reads whose tool_use_id is NOT in the persisted set), and `persisted_non_reads` (persisted tool IDs that do NOT match any file_read, e.g., Bash command results)
- [x] **3.3** - Assemble the `persistence_mapping` section with `persisted_tool_ids`, `persisted_count`, `non_persisted_count`, `persisted_reads`, `non_persisted_reads`, and `persisted_non_reads`. Ensure accounting identity: `persisted_count = len(persisted_reads) + len(persisted_non_reads)`
- [x] **3.4** - When `has_tool_results` is false or no session subdirectory exists, populate `persistence_mapping` with the empty structure: `persisted_tool_ids: []`, `persisted_count: 0`, `persisted_non_reads: []`, `persisted_reads: []`, and `non_persisted_reads` populated with ALL file_read entries (since none were persisted)

### Phase 4: Add Derived Top-Level Metrics
- [x] **4.1** - Compute `initial_cache_read` from the first `token_progression` entry's `cache_read_tokens`
- [x] **4.2** - Compute `total_input_at_peak` as `max(total_input)` across all `token_progression` entries, and `peak_cache_read` as `max(cache_read_tokens)` (convenience alias for quick access)
- [x] **4.3** - Add `initial_cache_read`, `total_input_at_peak`, and `peak_cache_read` to the `context_metrics` section of the output

### Phase 5: Update Schema and Command Documentation
- [x] **5.1** - Update `schema_version` from `"1.2"` to `"1.3"` in the output assembly
- [x] **5.2** - Update the `## Output Schema Reference` section in `.claude/commands/update-trial-data.md` to document all new fields, including the JSONL field name mapping, `compaction_loss` formula and interpretation, `persistence_mapping` structure (both with and without persistence), and the `peak_cache_read` convenience alias note
- [x] **5.3** - Verify the script handles re-processing: run on an existing Schema 1.2 trial and confirm clean upgrade to 1.3

### Phase 6: Update Analysis Guide
- [x] **6.1** - Update `docs/experiments/guides/Trial-Analysis-Guide.md` Section 3.4 ("Key Data Points in Session Files") to document the newly extracted usage fields (`cache_creation_tokens`, `input_tokens`, `output_tokens`, `total_input`) alongside the existing `cache_read_input_tokens`
- [x] **6.2** - Add a new appendix (or extend existing appendices) documenting the `persistence_mapping` section: what each field means, how to interpret `persisted_reads` vs `non_persisted_reads` vs `persisted_non_reads`, and how `persisted_count` relates to `has_tool_results`
- [x] **6.3** - Add documentation for the `compaction_loss` field: its formula, interpretation of positive vs negative values, and clarification that it is a per-reset single-trial metric distinct from the cross-trial "42K content gap" described in Step 1.4
- [x] **6.4** - Update the Quick Reference table (Part 7) to include the new key metrics (`total_input_at_peak`, `compaction_loss`, `persisted_count`) with their sources and purposes

### Phase 7: Verification
- [x] **7.1** - Run the updated script on `dev/misc/barebones-2121/20260128-150640` (FAILURE, `has_tool_results: true`) and verify: `compaction_loss` > 0 on the reset entry, `persisted_count` = 6 (5 reads + 1 non-read), `persisted_reads` contains 5 entries matching the Read tool_use_ids from Step 1.4, `persisted_non_reads` contains 1 entry (the Bash `date` command tool_use_id)
- [x] **7.2** - Run the updated script on `dev/misc/repro-attempts-04-2120/20260127-095002` (SUCCESS, `has_tool_results: false`) and verify: `compaction_loss` is negative on the reset entry (indicating post-reset context expansion beyond pre-reset `cache_read`, typical when no content was persisted), `persistence_mapping` shows `persisted_count: 0` and all 9 file reads in `non_persisted_reads`
- [x] **7.3** - Run the updated script on at least one trial from `dev/misc/barebones-2120-2/` to verify consistency across collections
