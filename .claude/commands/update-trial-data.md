---
description: Process trial folder into json report
argument-hint: <path-to-trial-folder>
---

# Update Trial Data

Extract structured data from a Phantom Reads trial folder and generate/update `trial_data.json`.

## Usage

```
/update-trial-data <trial-folder-path>
```

## Arguments

- `$ARGUMENTS` - Path to the trial folder (e.g., `dev/misc/wsd-dev-02/20260119-131802`)

---

## Instructions

Run the extraction script located at `dev/karpathy/extract_trial_data.py` with the provided trial folder path.

### Step 1: Validate Input

Verify that `$ARGUMENTS` is provided and the path exists. If not, report an error and stop.

### Step 2: Run Extraction Script

Execute the helper script:

```bash
uv run python dev/karpathy/extract_trial_data.py "$ARGUMENTS"
```

The script will:
1. Validate the trial folder structure (chat export, session file)
2. Parse the session `.jsonl` file for token progression, resets, and file reads
3. Parse the chat export for context snapshots and self-reported outcome
4. Compute derived metrics (pattern classification, token analysis)
5. Compare with existing `trial_data.json` if present
6. Write the updated `trial_data.json`
7. Output a formatted summary

### Step 3: Report Results

The script outputs its own summary. If the script exits with an error, report the error to the user.

---

## Output Schema Reference

The script generates `trial_data.json` with schema version 1.2:

```json
{
  "schema_version": "1.2",
  "generated_at": "<ISO timestamp>",
  "metadata": {
    "workscope_id": "<folder name>",
    "session_uuid": "<from jsonl filename>",
    "chat_export_file": "<filename>",
    "session_file": "<filename>",
    "has_subagents": "<boolean>",
    "has_tool_results": "<boolean>"
  },
  "outcome": {
    "self_reported": "<SUCCESS|FAILURE|UNKNOWN>",
    "affected_files": ["<paths if FAILURE>"],
    "notes": "<string>"
  },
  "context_metrics": {
    "pre_operation_tokens": "<number>",
    "pre_operation_percent": "<number>",
    "post_operation_tokens": "<number>",
    "post_operation_percent": "<number>",
    "headroom_at_trigger": "<number>",
    "context_window_size": 200000
  },
  "reset_analysis": {
    "total_resets": "<number>",
    "reset_positions_percent": ["<percentages>"],
    "pattern_classification": "<pattern name>",
    "resets": ["<reset details>"]
  },
  "file_reads": {
    "total_operations": "<number>",
    "successful_operations": "<number>",
    "failed_operations": "<number>",
    "unique_files": "<number>",
    "reads": ["<read details with success/error>"],
    "unique_file_list": ["<deduplicated paths>"],
    "failed_reads": ["<failed read details>"]
  },
  "timeline": ["<timeline events>"],
  "token_progression": ["<token snapshots>"],
  "token_analysis": {
    "available": "<boolean>",
    "token_counts_file": "<path or null>",
    "statistics": "<token stats>",
    "reads_with_tokens": ["<annotated reads>"],
    "resets_with_context": ["<annotated resets>"]
  }
}
```

---

## Error Handling

The script handles these conditions internally:
- **Missing chat export**: Continues with partial extraction
- **Missing session file**: Reports error, cannot proceed
- **Malformed JSON lines**: Skips and counts errors
- **Cannot determine outcome**: Sets to "UNKNOWN"

---

## Helper Script Location

The extraction logic is implemented in: `dev/karpathy/extract_trial_data.py`

This script is maintained separately to ensure consistent, validated extraction behavior. Do not regenerate or modify this script during command execution.
