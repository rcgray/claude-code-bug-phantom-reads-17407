# Trial Data Failed Read Investigation Findings

This document presents the findings from investigating the data quality issue in the `/update-trial-data` command, where Read tool invocations are recorded regardless of success or failure.

## Summary

The investigation confirmed that the `/update-trial-data` command records all Read tool invocations as "reads" without checking whether the read actually succeeded. This leads to inflated file counts and inaccurate analysis data.

## Linkage Mechanism

The session `.jsonl` file format links `tool_use` entries to their `tool_result` counterparts through matching IDs:

**tool_use entry** (in assistant message):
```json
{
  "type": "tool_use",
  "id": "toolu_01YNkHtqaotDbozDfmi7gCao",
  "name": "Read",
  "input": {"file_path": "/path/to/file.md"}
}
```

**tool_result entry** (in subsequent user message):
```json
{
  "type": "tool_result",
  "tool_use_id": "toolu_01YNkHtqaotDbozDfmi7gCao",
  "content": "<content or error message>"
}
```

The `id` field in `tool_use` matches the `tool_use_id` field in `tool_result`. This one-to-one correspondence allows matching each Read invocation to its result.

## Error Patterns

Analysis of 91 session files identified the following error patterns in Read tool results:

### Pattern 1: File Does Not Exist
```
<tool_use_error>File does not exist.</tool_use_error>
```
- **Occurrences**: 10 across 9 sessions
- **Cause**: Agent attempted to read a file that has been renamed, moved, or never existed

### Pattern 2: General Tool Use Error Format
All Read tool errors are wrapped in `<tool_use_error>` tags:
```
<tool_use_error>[error message]</tool_use_error>
```

## Success Pattern

Successful Read operations return file content with line number prefixes:
```
     1→# File Heading
     2→
     3→Content starts here...
```

The presence of the `→` character with line numbers at the start of content indicates a successful read.

## Detection Algorithm

To distinguish successful from failed reads:

```python
def is_successful_read(tool_result_content: str) -> bool:
    """
    Determine if a Read tool_result indicates success or failure.

    Returns True if the read succeeded, False if it failed.
    """
    content = str(tool_result_content).strip()

    # Check for error marker
    if "<tool_use_error>" in content:
        return False

    # Additional validation: successful reads start with line-numbered content
    # Format: "     1→" (spaces + line number + arrow)
    if content.startswith("     1") and "→" in content[:10]:
        return True

    # If neither error nor expected success format, treat as success
    # (defensive - some edge cases may have different formats)
    return True
```

## Affected Data

The `repro-attempts/medium-1` trial demonstrates the issue:

| File | tool_use Line | tool_result Status | Currently Recorded |
|------|---------------|--------------------|--------------------|
| PRD.md | 16 | SUCCESS | ✓ Read |
| Experiment-Methodology.md | 17 | **FAILURE** (does not exist) | ✓ Read (incorrect) |
| Action-Plan.md | 18 | SUCCESS | ✓ Read |

The non-existent file `Experiment-Methodology.md` appears in the `file_reads` list despite returning an error.

## Impact Assessment

**Current state** (without fix):
- `file_reads.total_operations`: Counts all Read invocations
- `file_reads.unique_files`: Includes non-existent files
- Token analysis: May include 0-token entries for failed reads

**With fix**:
- Each read entry gains a `success` boolean field
- Aggregate statistics count only successful reads
- Failed reads remain visible for diagnostic purposes

## Recommendations for Implementation (Phase 2)

1. **Collect tool_results during parsing**: Build a map of `tool_use_id` → `tool_result` while scanning the session file

2. **Match reads to results**: For each Read `tool_use`, look up the corresponding `tool_result`

3. **Detect failure**: Check for `<tool_use_error>` in the result content

4. **Update schema**: Add `success: boolean` field to each read entry:
   ```json
   {
     "sequence": 2,
     "batch_id": 2,
     "file_path": "/path/to/file.md",
     "session_line": 17,
     "tool_use_id": "toolu_01YNk...",
     "success": false,
     "error": "File does not exist."
   }
   ```

5. **Update aggregates**: Ensure `total_operations` and `unique_files` only count successful reads, or add separate `successful_reads` / `failed_reads` counters

## Files Examined

- `.claude/commands/update-trial-data.md` - Command implementation
- `dev/misc/repro-attempts/medium-1/c35c12b8-cefb-4d16-ad19-d62ced4823e4.jsonl` - Session with known failed read
- `dev/misc/repro-attempts/medium-1/trial_data.json` - Current (incorrect) output
- `dev/misc/wsd-dev-02/*/` - Additional session files for pattern validation
- 91 total session files scanned for error patterns

## Conclusion

The investigation confirmed the suspected issue and identified the specific mechanisms needed to fix it. The `tool_use` to `tool_result` linkage is well-defined and consistent across all examined sessions. The error pattern (`<tool_use_error>` wrapper) is unambiguous and easy to detect programmatically.

The implementation phase (Phase 2) has clear requirements and should be straightforward to execute.
