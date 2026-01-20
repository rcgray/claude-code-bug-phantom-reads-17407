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

You are tasked with extracting structured data from a Phantom Reads trial folder and generating a `trial_data.json` file. This command is **idempotent** - it can be run multiple times safely.

### Step 1: Validate Trial Folder

Navigate to the provided path: `$ARGUMENTS`

Verify the folder contains:
1. **Chat export**: `{folder-name}.txt` (e.g., `20260119-131802.txt`)
2. **Session file**: `*.jsonl` (exactly one file with UUID name)

Extract:
- `workscope_id` from folder name
- `session_uuid` from the `.jsonl` filename (without extension)
- `collection_dir` from parent directory (e.g., `dev/misc/wsd-dev-02`)

Check for optional subdirectory `{uuid}/` containing `subagents/` or `tool-results/`.

**Check for token counts file:**
Look for `file_token_counts.json` in the `collection_dir`. If found, load it as `token_counts_data` for use in token analysis. If not found, token analysis will be skipped.

If required files are missing, report the error and stop.

### Step 2: Check for Existing trial_data.json

Check if `trial_data.json` already exists in the trial folder.

- If **exists**: Read it and store as `existing_data` for comparison
- If **not exists**: Note that this will be a fresh creation

### Step 3: Parse Session File

Read the session `.jsonl` file line by line. For each line:

**Track token progression:**
- Look for `assistant` messages with `message.usage.cache_read_input_tokens`
- Record each non-zero value with its line number

**Detect context resets:**
- A reset occurs when `cache_read_input_tokens` drops by more than 10,000 tokens from the previous value
- Record: line number, from_tokens, to_tokens

**Extract file reads:**
- Look for `tool_use` blocks where `name` is "Read"
- Extract: `file_path` from `input`, `id` (tool_use_id), line number
- Track batch grouping: reads in the same assistant message are one batch

**Extract user inputs:**
- Look for `human` messages
- Record content preview (first 50 chars)
- Detect methodology phases:
  - Contains "/wsd:init" → phase "init"
  - Contains "/refine-plan" → phase "trigger"
  - Contains "phantom read" or "persisted-output" → phase "inquiry"

### Step 4: Parse Chat Export

Read the chat export `.txt` file to extract:

**Context snapshots:**
- Look for lines matching pattern: `tokens (XX%)`
- Extract token count and percentage

**Self-reported outcome:**
- Search for agent's response to phantom read inquiry
- Look for indicators:
  - "no phantom reads" / "received inline" / "successfully read" → SUCCESS
  - "phantom read" / "persisted-output" / "did not follow up" → FAILURE
- Extract any mentioned affected file paths

### Step 5: Compute Derived Metrics

**Reset analysis:**
```
total_resets = count of reset events
reset_positions_percent = [(reset.sequence / total_events) * 100 for each reset]
```

**Pattern classification** (apply this logic):
- If no resets → "NO_RESETS"
- If 1 reset < 50% → "SINGLE_EARLY"
- If 1 reset >= 50% → "SINGLE_LATE"
- If all resets > 80% → "LATE_CLUSTERED"
- If first reset < 50% AND no resets between 50-90% AND last reset > 90% → "EARLY_PLUS_LATE"
- If first reset < 50% AND has resets between 50-90% → "EARLY_PLUS_MID_LATE"
- Otherwise → "OTHER"

**Context metrics:**
- Find token count BEFORE "trigger" phase → `pre_operation_tokens`
- Find token count AFTER "trigger" phase completes → `post_operation_tokens`
- `headroom = 200000 - pre_operation_tokens`

**File read stats:**
- `total_operations` = count of all Read tool_use blocks
- `unique_files` = deduplicated file paths

### Step 5b: Compute Token Analysis (if token_counts_data available)

If `file_token_counts.json` was loaded, perform token-based analysis:

**Normalize file paths:**
For each file in `file_reads`, extract the relative path by:
1. Finding the project root pattern (e.g., `/Users/.../Projects/claude-bug/`)
2. Extracting everything after the project root
3. Matching against keys in `token_counts_data.project_files`

**Build reads_with_tokens:**
For each read operation, in sequence order:
1. Look up token count from `token_counts_data` (use 0 if not found, -1 for ephemeral files)
2. Calculate cumulative estimate: start with `pre_operation_tokens`, add each file's tokens in sequence
3. Note: cumulative is an ESTIMATE - actual context includes more than just file content

```
reads_with_tokens = [
  {
    "sequence": <read sequence number>,
    "file_path": "<relative path>",
    "token_count": <from token_counts_data or 0>,
    "cumulative_estimate": <running total>,
    "session_line": <line number>
  }
]
```

**Build resets_with_context:**
For each reset event:
1. Find the last read operation BEFORE this reset (by session_line)
2. Record cumulative token estimate at that point
3. Record the file that was last read

```
resets_with_context = [
  {
    "reset_sequence": <reset sequence number>,
    "session_line": <line number>,
    "cumulative_tokens_before": <estimate at reset point>,
    "last_file_read": "<relative path or null>",
    "last_file_tokens": <token count or null>
  }
]
```

**Compute token statistics:**
- `total_tokens_read`: Sum of all known file token counts (exclude -1 values)
- `largest_file_tokens`: Maximum single file token count
- `largest_file_path`: Path of the largest file
- `unknown_token_files`: Count of files with 0 or -1 token count

### Step 6: Assemble Output Structure

Create a JSON object with this structure:

```json
{
  "schema_version": "1.1",
  "generated_at": "<current ISO timestamp>",
  "metadata": {
    "workscope_id": "<from folder name>",
    "session_uuid": "<from jsonl filename>",
    "chat_export_file": "<filename>",
    "session_file": "<filename>",
    "has_subagents": <boolean>,
    "has_tool_results": <boolean>
  },
  "outcome": {
    "self_reported": "<SUCCESS|FAILURE|UNKNOWN>",
    "affected_files": [<list of paths if FAILURE>],
    "notes": "<any relevant notes>"
  },
  "context_metrics": {
    "pre_operation_tokens": <number>,
    "pre_operation_percent": <number>,
    "post_operation_tokens": <number>,
    "post_operation_percent": <number>,
    "headroom_at_trigger": <number>,
    "context_window_size": 200000
  },
  "reset_analysis": {
    "total_resets": <number>,
    "reset_positions_percent": [<list of percentages>],
    "pattern_classification": "<pattern name>",
    "resets": [
      {
        "sequence_position": <number>,
        "total_events": <number>,
        "position_percent": <number>,
        "from_tokens": <number>,
        "to_tokens": <number>,
        "session_line": <number>
      }
    ]
  },
  "file_reads": {
    "total_operations": <number>,
    "unique_files": <number>,
    "reads": [
      {
        "sequence": <number>,
        "batch_id": <number>,
        "file_path": "<path>",
        "session_line": <number>,
        "tool_use_id": "<id>"
      }
    ],
    "unique_file_list": [<deduplicated paths>]
  },
  "timeline": [
    {
      "sequence": <number>,
      "type": "<user_input|tool_batch|context_reset>",
      "session_line": <number>,
      "<type-specific fields>"
    }
  ],
  "token_progression": [
    {
      "sequence": <number>,
      "cache_read_tokens": <number>,
      "session_line": <number>
    }
  ],
  "token_analysis": {
    "available": <boolean - true if token_counts_data was loaded>,
    "token_counts_file": "<path to file_token_counts.json or null>",
    "statistics": {
      "total_tokens_read": <sum of known file tokens>,
      "largest_file_tokens": <max single file>,
      "largest_file_path": "<path>",
      "unknown_token_files": <count of files with 0 or -1>
    },
    "reads_with_tokens": [
      {
        "sequence": <number>,
        "file_path": "<relative path>",
        "token_count": <number>,
        "cumulative_estimate": <number>,
        "session_line": <number>
      }
    ],
    "resets_with_context": [
      {
        "reset_sequence": <number>,
        "session_line": <number>,
        "cumulative_tokens_before": <number>,
        "last_file_read": "<path or null>",
        "last_file_tokens": <number or null>
      }
    ]
  }
}
```

### Step 7: Compare and Report Changes

If `existing_data` exists, compare each section:

For each top-level key, report:
- **NEW**: Key doesn't exist in current file
- **UPDATED**: Key exists but value differs
- **UNCHANGED**: Key exists and value matches

Format the change report:
```
Changes to trial_data.json:
  - schema_version: UPDATED (1.0 → 1.1)
  - metadata: UNCHANGED
  - outcome: UPDATED (self_reported: UNKNOWN → SUCCESS)
  - context_metrics: NEW
  - reset_analysis: UPDATED (total_resets: 1 → 2)
  - file_reads: UNCHANGED
  - timeline: UPDATED (added 5 events)
  - token_progression: UPDATED (added 12 data points)
  - token_analysis: NEW (9 reads with tokens, 2 resets with context)
```

If no existing file:
```
Creating new trial_data.json with all sections.
```

### Step 8: Write Output

Write the assembled JSON to `{trial-folder}/trial_data.json` with proper formatting (2-space indentation).

### Step 9: Report Summary

Output a summary:

```
Trial Data Extraction Complete
==============================
Trial: {workscope_id}
Session: {session_uuid}

Outcome: {self_reported}

Context Metrics:
  Pre-operation:  {pre_op}K tokens ({pre_op_pct}%)
  Post-operation: {post_op}K tokens ({post_op_pct}%)
  Headroom:       {headroom}K tokens

Reset Analysis:
  Total resets: {count}
  Pattern: {pattern_classification}
  Positions: {positions as percentages}

File Reads:
  Total operations: {total}
  Unique files: {unique}

Token Analysis: {AVAILABLE | NOT AVAILABLE}
  Total tokens read: {total_tokens_read}
  Largest file: {largest_file_path} ({largest_file_tokens} tokens)
  Unknown files: {unknown_token_files}

Timeline Events: {count}

Output: {path}/trial_data.json
Status: {CREATED | UPDATED}
```

If token analysis is not available (no `file_token_counts.json`), show:
```
Token Analysis: NOT AVAILABLE
  (No file_token_counts.json found in collection directory)
```

---

## Error Handling

- **Missing chat export**: Report error, continue with partial extraction
- **Missing session file**: Report error, cannot proceed
- **Malformed JSON lines**: Skip and count errors, report at end
- **Missing usage data**: Record null for that data point
- **Cannot determine outcome**: Set to "UNKNOWN"

---

## Example

```
> /update-trial-data dev/misc/wsd-dev-02/20260119-131802

Validating trial folder...
  Chat export: 20260119-131802.txt ✓
  Session file: 637ef6e7-e740-4503-8ff8-5780d7c0918f.jsonl ✓
  Subdirectory: Not present
  Token counts: file_token_counts.json ✓

Checking for existing trial_data.json... Found (schema 1.0)

Parsing session file (602KB)...
  Processed 1,247 lines
  Found 33 assistant messages with usage data
  Found 9 Read operations in 4 batches
  Detected 2 context resets

Parsing chat export...
  Found 2 /context snapshots
  Outcome: SUCCESS (self-reported)

Computing metrics...
  Pre-operation: 85K (43%)
  Post-operation: 150K (75%)
  Pattern: EARLY_PLUS_LATE

Computing token analysis...
  Matched 7/7 files to token counts
  Calculated cumulative estimates for 9 reads
  Annotated 2 resets with context

Changes to trial_data.json:
  - schema_version: UPDATED (1.0 → 1.1)
  - token_analysis: NEW (9 reads with tokens, 2 resets with context)

Trial Data Extraction Complete
==============================
Trial: 20260119-131802
Session: 637ef6e7-e740-4503-8ff8-5780d7c0918f

Outcome: SUCCESS

Context Metrics:
  Pre-operation:  85K tokens (43%)
  Post-operation: 150K tokens (75%)
  Headroom:       115K tokens

Reset Analysis:
  Total resets: 2
  Pattern: EARLY_PLUS_LATE
  Positions: 42%, 97%

File Reads:
  Total operations: 9
  Unique files: 7

Token Analysis: AVAILABLE
  Total tokens read: 54,996
  Largest file: docs/features/install-and-update/Update-System.md (14,137 tokens)
  Unknown files: 0

Timeline Events: 33

Output: dev/misc/wsd-dev-02/20260119-131802/trial_data.json
Status: UPDATED
```
