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

Run the extraction script located at `dev/karpathy/extract_trial_data.py` with the provided trial folder path, then perform semantic analysis of the chat export to determine the trial outcome.

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
3. Parse the chat export for context snapshots
4. Compute derived metrics (pattern classification, token analysis)
5. Compare with existing `trial_data.json` if present
6. Write the updated `trial_data.json` with placeholder values for outcome fields
7. Output a formatted summary

The script outputs `"PENDING_NLP"` for the `outcome.self_reported` and `outcome.notes` fields. You must determine these values in the next step.

### Step 3: Determine Outcome via Semantic Analysis

The extraction script cannot reliably determine whether the Session Agent experienced phantom reads because this requires understanding natural language context. You must analyze the chat export to determine the actual outcome.

#### 3.1: Read the Chat Export

Open the chat export file. The filename is stored in the `trial_data.json` file you just created at `metadata.chat_export_file`. The file is located in the trial folder.

#### 3.2: Locate the Session Agent's Self-Report

Search for the section where the Session Agent responds to questions about whether they experienced phantom reads. Look for responses to prompts like:
- "Did you experience phantom reads?"
- "Did you receive any `<persisted-output>` messages?"
- Questions about whether file contents were received inline

#### 3.3: Determine the Outcome

Analyze the Session Agent's response semantically to determine the outcome:

- **SUCCESS**: The Session Agent explicitly states they did NOT experience phantom reads, received file contents inline, or otherwise confirms normal operation. Examples:
  - "No, I did not experience the phantom read issue"
  - "All my Read tool calls returned the actual file contents"
  - "I did not receive any `<persisted-output>` redirections"

- **FAILURE**: The Session Agent explicitly states they DID experience phantom reads, received `<persisted-output>` messages without following up, or confirms the issue occurred. Examples:
  - "Yes, I experienced phantom reads on these files..."
  - "Several files returned `<persisted-output>` markers"
  - "I did not receive the actual content for..."

- **UNKNOWN**: The chat export does not contain a clear self-report, the response is ambiguous, or the session ended before the inquiry was made.

**Important**: Do not rely on keyword matching. Understand the semantic meaning of the response. The presence of words like "phantom read" or "persisted-output" in a denial statement (e.g., "I did NOT experience phantom reads") indicates SUCCESS, not FAILURE.

#### 3.4: Extract Summary Notes

Write a concise summary note (1-2 sentences) describing the Session Agent's experience. Include:
- The Session Agent's explicit statement if available (quote key phrases)
- Which files were affected if FAILURE
- Any relevant context about the session

Examples:
- `"Agent explicitly stated: 'No, I did not experience the phantom read issue during this session.'"`
- `"Agent reported phantom reads on 5 files in docs/read-only/standards/. Received <persisted-output> for all."`
- `"Session ended before phantom read inquiry. No self-report available."`

#### 3.5: Update trial_data.json

Read the `trial_data.json` file from the trial folder and update:
- `outcome.self_reported`: Set to `"SUCCESS"`, `"FAILURE"`, or `"UNKNOWN"`
- `outcome.notes`: Set to your summary note string
- `outcome.affected_files`: If FAILURE, list the file paths that experienced phantom reads. If SUCCESS or UNKNOWN, leave as empty array `[]`.

Write the updated JSON back to `trial_data.json`.

### Step 4: Report Results

Report to the user:
1. The script's extraction summary (from Step 2)
2. Your outcome determination with reasoning
3. The summary note you recorded
4. Confirmation that `trial_data.json` has been updated

If any step fails, report the error to the user.

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

If the chat export is missing or incomplete, set outcome to `"UNKNOWN"` with an appropriate note explaining why the outcome could not be determined.

---

## Helper Script Location

The extraction logic is implemented in: `dev/karpathy/extract_trial_data.py`

This script is maintained separately to ensure consistent, validated extraction behavior. Do not regenerate or modify this script during command execution.
