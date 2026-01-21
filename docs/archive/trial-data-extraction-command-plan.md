# Trial Data Extraction Command Plan

**Purpose**: Define a reusable slash command (`/update-trial-data`) that generates a structured `trial_data.json` file from a Phantom Reads trial folder.

**Implementation Status**: Command created at `.claude/commands/update-trial-data.md`

**Status**: Draft specification for review

---

## Overview

### Problem Statement

Each trial in our Phantom Reads investigation produces multiple artifacts (chat export, session file, subdirectories). Analyzing these manually is time-consuming and error-prone. We need a standardized pre-processing step that extracts structured data from trial artifacts into a consistent JSON format.

### Goal

Create a slash command that, when pointed at a trial folder, produces a `trial_data.json` file containing:
1. **Metadata**: Trial identification and basic stats
2. **Timeline**: Chronological sequence of all significant events
3. **File reads**: Complete list with order, batching, and paths
4. **Context tracking**: Token consumption progression and reset events
5. **Methodology markers**: User progress through the experiment protocol

---

## Trial Folder Structure

A User Agent executing this command must understand the expected trial folder layout:

```
{workscope-id}/                          # e.g., 20260119-131802/
├── {workscope-id}.txt                   # Chat export (human-readable transcript)
├── {uuid}.jsonl                         # Main session file (line-delimited JSON)
└── {uuid}/                              # Session subdirectory (may not exist)
    ├── subagents/                       # Sub-agent session files
    │   └── agent-{shortId}.jsonl
    └── tool-results/                    # Persisted tool outputs
        └── toolu_{toolUseId}.txt
```

### Key Files

| File | Purpose | Data Available |
|------|---------|----------------|
| `{workscope-id}.txt` | Chat export | User commands, `/context` outputs, self-reported outcome |
| `{uuid}.jsonl` | Session log | All tool calls, token consumption, message sequence |
| `{uuid}/subagents/*.jsonl` | Sub-agent logs | Sub-agent tool calls (if Task tool used) |
| `{uuid}/tool-results/*.txt` | Persisted outputs | Content of large tool results |

---

## Session File Structure

The `.jsonl` file contains one JSON object per line. Key message types:

### Assistant Messages (contain tool calls and usage data)

```json
{
  "type": "assistant",
  "message": {
    "content": [
      {
        "type": "tool_use",
        "id": "toolu_01ABC...",
        "name": "Read",
        "input": {"file_path": "/path/to/file.md"}
      }
    ],
    "usage": {
      "cache_read_input_tokens": 85234,
      "cache_creation_input_tokens": 1200,
      "input_tokens": 150,
      "output_tokens": 2340
    }
  }
}
```

### User Messages (contain tool results)

```json
{
  "type": "user",
  "message": {
    "content": [
      {
        "type": "tool_result",
        "tool_use_id": "toolu_01ABC...",
        "content": "     1→# File content here..."
      }
    ]
  }
}
```

### Human Messages (user input)

```json
{
  "type": "human",
  "message": {
    "content": "/refine-plan docs/tickets/open/example.md"
  }
}
```

---

## Extraction Algorithm

### Step 1: Locate and Validate Files

```
INPUT: trial_folder_path

1. Verify folder exists
2. Find chat export: {folder_name}.txt
3. Find session file: *.jsonl (should be exactly one)
4. Extract workscope_id from folder name
5. Extract session_uuid from jsonl filename
6. Check for session subdirectory: {uuid}/
```

### Step 2: Parse Session File

Process each line of the `.jsonl` file sequentially, maintaining:
- `line_number`: Current position in file
- `event_sequence`: Running count of significant events
- `current_batch`: Tool calls in current assistant message
- `prev_cache_read`: Previous token count for reset detection

```
FOR each line in session_file:
    msg = parse_json(line)

    IF msg.type == "assistant":
        # Extract usage data
        usage = msg.message.usage
        cache_read = usage.cache_read_input_tokens

        # Check for reset (>10K drop)
        IF prev_cache_read > 0 AND cache_read < prev_cache_read - 10000:
            ADD reset_event to timeline

        prev_cache_read = cache_read

        # Extract tool calls
        batch = []
        FOR each block in msg.message.content:
            IF block.type == "tool_use":
                ADD to batch
                IF block.name == "Read":
                    ADD to file_reads

        IF batch is not empty:
            ADD tool_batch_event to timeline

    ELIF msg.type == "human":
        ADD user_input_event to timeline

        # Check for methodology markers
        IF content contains "/wsd:init":
            MARK methodology_phase = "init"
        ELIF content contains "/refine-plan":
            MARK methodology_phase = "trigger"
        ELIF content contains phantom read prompt:
            MARK methodology_phase = "inquiry"
```

### Step 3: Parse Chat Export

Extract supplementary data not available in session file:

```
FOR each line in chat_export:
    # Find /context outputs
    IF line matches "·.*tokens \(\d+%\)":
        EXTRACT token_count, percentage
        ADD context_snapshot to timeline

    # Find self-reported outcome
    IF line contains "phantom read" AND is agent response:
        DETERMINE outcome (SUCCESS/FAILURE)
        EXTRACT affected_files if mentioned
```

### Step 4: Compute Derived Metrics

```
# Reset analysis
reset_count = count(reset_events)
reset_positions = [event.sequence / total_events for event in reset_events]
reset_pattern = classify_pattern(reset_positions)

# File read analysis
total_reads = count(file_reads)
unique_files = deduplicate(file_reads)
read_batches = group_by_batch(file_reads)

# Context analysis
pre_op_consumption = get_consumption_before("trigger")
post_op_consumption = get_consumption_after("trigger")
headroom = 200000 - pre_op_consumption
```

### Step 5: Generate Output

Assemble all data into the output structure and write to `trial_data.json`.

---

## Output Schema: `trial_data.json`

```json
{
  "schema_version": "1.0",
  "generated_at": "2026-01-19T16:35:30Z",

  "metadata": {
    "workscope_id": "20260119-131802",
    "session_uuid": "637ef6e7-e740-4503-8ff8-5780d7c0918f",
    "chat_export_file": "20260119-131802.txt",
    "session_file": "637ef6e7-e740-4503-8ff8-5780d7c0918f.jsonl",
    "has_subagents": false,
    "has_tool_results": false
  },

  "outcome": {
    "self_reported": "SUCCESS",
    "affected_files": [],
    "notes": ""
  },

  "context_metrics": {
    "pre_operation_tokens": 85000,
    "pre_operation_percent": 43,
    "post_operation_tokens": 150000,
    "post_operation_percent": 75,
    "headroom_at_trigger": 115000,
    "context_window_size": 200000
  },

  "reset_analysis": {
    "total_resets": 2,
    "reset_positions_percent": [42, 97],
    "pattern_classification": "EARLY_PLUS_LATE",
    "resets": [
      {
        "sequence_position": 14,
        "total_events": 33,
        "position_percent": 42,
        "from_tokens": 82000,
        "to_tokens": 21000,
        "session_line": 39
      },
      {
        "sequence_position": 32,
        "total_events": 33,
        "position_percent": 97,
        "from_tokens": 144000,
        "to_tokens": 21000,
        "session_line": 76
      }
    ]
  },

  "file_reads": {
    "total_operations": 9,
    "unique_files": 7,
    "reads": [
      {
        "sequence": 1,
        "batch_id": 1,
        "file_path": "/path/to/file1.md",
        "session_line": 14,
        "tool_use_id": "toolu_01ABC..."
      },
      {
        "sequence": 2,
        "batch_id": 1,
        "file_path": "/path/to/file2.md",
        "session_line": 14,
        "tool_use_id": "toolu_01DEF..."
      }
    ],
    "unique_file_list": [
      "/path/to/file1.md",
      "/path/to/file2.md"
    ]
  },

  "timeline": [
    {
      "sequence": 1,
      "type": "user_input",
      "session_line": 1,
      "content_preview": "/wsd:init --custom",
      "methodology_phase": "init"
    },
    {
      "sequence": 2,
      "type": "tool_batch",
      "session_line": 14,
      "tools": [
        {"name": "Read", "target": "/path/to/file1.md"},
        {"name": "Read", "target": "/path/to/file2.md"}
      ],
      "cache_read_tokens": 77000
    },
    {
      "sequence": 3,
      "type": "context_reset",
      "session_line": 39,
      "from_tokens": 82000,
      "to_tokens": 21000,
      "drop_tokens": 61000
    },
    {
      "sequence": 4,
      "type": "user_input",
      "session_line": 45,
      "content_preview": "/refine-plan docs/tickets/...",
      "methodology_phase": "trigger"
    }
  ],

  "token_progression": [
    {"sequence": 1, "cache_read_tokens": 33000, "session_line": 5},
    {"sequence": 2, "cache_read_tokens": 77000, "session_line": 14},
    {"sequence": 3, "cache_read_tokens": 82000, "session_line": 38},
    {"sequence": 4, "cache_read_tokens": 21000, "session_line": 39}
  ]
}
```

---

## Pattern Classification Logic

The command should classify reset patterns according to the Reset Timing Theory:

```python
def classify_reset_pattern(reset_positions_percent):
    """
    Classify reset pattern based on position percentages.

    Returns one of:
    - "EARLY_PLUS_LATE": Low risk pattern
    - "EARLY_PLUS_MID_LATE": High risk pattern
    - "LATE_CLUSTERED": High risk pattern
    - "SINGLE_EARLY": Unknown risk
    - "SINGLE_LATE": Unknown risk
    - "NO_RESETS": Unknown risk
    """
    if len(reset_positions_percent) == 0:
        return "NO_RESETS"

    if len(reset_positions_percent) == 1:
        if reset_positions_percent[0] < 50:
            return "SINGLE_EARLY"
        else:
            return "SINGLE_LATE"

    first = reset_positions_percent[0]
    last = reset_positions_percent[-1]
    mid_resets = [p for p in reset_positions_percent if 50 <= p <= 90]

    # Check for late clustered (all resets > 80% and close together)
    if all(p > 80 for p in reset_positions_percent):
        return "LATE_CLUSTERED"

    # Check for early + late only (no mid-session resets)
    if first < 50 and last > 90 and len(mid_resets) == 0:
        return "EARLY_PLUS_LATE"

    # Otherwise, it has mid-session resets
    if first < 50:
        return "EARLY_PLUS_MID_LATE"

    return "OTHER"
```

---

## Command Specification

### Usage

```
/extract-trial-data <trial-folder-path>
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `trial-folder-path` | Yes | Path to the trial folder (e.g., `dev/misc/wsd-dev-02/20260119-131802`) |

### Output

- Creates `trial_data.json` in the trial folder
- Reports summary to user

### Example Invocation

```
/extract-trial-data dev/misc/wsd-dev-02/20260119-131802
```

### Expected Output

```
Trial data extracted successfully.

Summary:
  Workscope ID: 20260119-131802
  Session UUID: 637ef6e7-e740-4503-8ff8-5780d7c0918f
  Outcome: SUCCESS (self-reported)

  Context Metrics:
    Pre-operation: 85K tokens (43%)
    Post-operation: 150K tokens (75%)
    Headroom at trigger: 115K tokens

  Reset Analysis:
    Total resets: 2
    Pattern: EARLY_PLUS_LATE (low risk)
    Positions: 42%, 97%

  File Reads:
    Total operations: 9
    Unique files: 7

Output written to: dev/misc/wsd-dev-02/20260119-131802/trial_data.json
```

---

## Implementation Notes

### Error Handling

The command should handle:
1. **Missing files**: Chat export or session file not found
2. **Malformed JSON**: Lines in session file that don't parse
3. **Missing data**: Usage data not present in some messages
4. **Multiple session files**: More than one `.jsonl` in folder (error)

### Edge Cases

1. **Subagents**: If `{uuid}/subagents/` exists, note in metadata but don't process (future enhancement)
2. **Persisted outputs**: File reads to `tool-results/` paths should be flagged as "persisted_followup"
3. **Partial trials**: If methodology phases are incomplete, note what's missing

### Performance

- Session files can be large (100K+ lines)
- Process line-by-line, don't load entire file into memory
- Timeline can be capped at significant events only (skip consecutive unchanged token readings)

---

## Future Enhancements

Once the per-trial command is solid:

1. **Collection-level command**: `/analyze-trial-collection <collection-path>` that:
   - Runs extraction on all trials
   - Generates deduplicated file list
   - Produces comparative summary

2. **Token count integration**: Add `token_count` field to file reads once Anthropic API counts are available

3. **Visualization**: Generate timeline diagrams or charts from the JSON data

---

## Acceptance Criteria

The command is complete when:

- [ ] Successfully extracts data from all 7 `wsd-dev-02` trials
- [ ] Generated JSON validates against the schema
- [ ] Reset pattern classification matches manual analysis
- [ ] Timeline includes all significant events in correct order
- [ ] File reads capture all Read operations with batch information
- [ ] Error handling covers missing/malformed data gracefully
- [ ] Output summary is clear and actionable

---

*Draft created: 2026-01-19*
*For review before implementation*
