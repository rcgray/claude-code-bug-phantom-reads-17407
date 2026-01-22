# Feature Brief: Update File Summary

**Date**: 2026-01-21
**Prepared by**: User Agent (Workscope-20260121-171438)
**For**: Feature-Writer Agent

---

## Executive Summary

A Python CLI tool that aggregates unique project file paths from all `trial_data.json` files within a trial collection and produces/updates a `file_token_counts.json` file at the collection root, enabling correlation analysis between file sizes and phantom read occurrence.

---

## Problem Statement

The Phantom Reads investigation involves analyzing trial data to find correlations between file characteristics and phantom read occurrence. Each trial's `trial_data.json` contains a `file_reads.unique_file_list` array of project file paths that were read during that session. To analyze patterns across trials, we need a unified view of all unique files read across a collection, along with their token counts.

Currently, `file_token_counts.json` files are manually created. This is error-prone, tedious, and doesn't scale as collections grow with additional trials.

---

## Solution Overview

Create `src/update_file_summary.py` — a pure Python CLI tool that:
1. Scans a collection directory for trial folders containing `trial_data.json`
2. Extracts and aggregates all unique project file paths (filtering out tool result paths)
3. Merges with any existing `file_token_counts.json`, preserving existing token count values
4. Writes the updated file with new entries initialized to `0`
5. Reports additions, orphans, and skipped trials

The tool is idempotent — running it multiple times produces consistent results, and it safely handles collections that grow over time with new trials.

---

## Relationship to Existing Systems

**Input Dependencies:**
- `trial_data.json` files (schema 1.2) created by `/update-trial-data` command via `dev/karpathy/extract_trial_data.py`
- Specifically reads `file_reads.unique_file_list` array from each trial

**Output:**
- `file_token_counts.json` at collection root (e.g., `dev/misc/wsd-dev-02/file_token_counts.json`)
- Used by analysis tools to correlate file sizes with phantom read outcomes

**Similar Existing Tools (patterns to follow):**
- `src/cc_version.py` — CLI structure, argument parsing, error handling patterns
- `src/collect_trials.py` — Collection scanning, directory enumeration, summary reporting patterns

**NOT a Karpathy Script:**
- Unlike `/update-trial-data`, this tool requires no NLP/semantic analysis
- Implemented as a pure Python script in `src/`, not as a `.claude/commands/` karpathy script

---

## Deliverables

### 1. New File: `src/update_file_summary.py`

Python CLI script with:
- Simple CLI: `./src/update_file_summary.py <collection-path> [--help]`
- Collection scanning to find all trial folders with `trial_data.json`
- Path filtering to exclude tool result paths (containing `/.claude/projects/`)
- Merge logic preserving existing token count values
- Orphan detection (files in existing JSON but not in any trial)
- Summary reporting with counts for new files, orphans, and skipped trials
- Proper error handling and exit codes

### 2. New File: `tests/test_update_file_summary.py`

Comprehensive pytest test suite covering:
- Argument parsing and help output
- Collection scanning with various directory structures
- Path filtering (project files vs tool results)
- JSON merge logic (preserving values, adding new entries)
- Orphan detection
- Empty collection handling
- Missing trial_data.json warnings
- Summary output formatting
- Error conditions (invalid paths, malformed JSON)

### 3. Update: `docs/core/PRD.md`

Add brief mention of the new tool in the Architecture Overview section under "Session Analysis Tools" or create a new subsection for collection-level tools.

---

## Design Constraints

1. **Paths are identifiers, not lookups** — The file paths stored are for matching/correlation purposes only. The tool does not verify file existence or access files.

2. **Use paths as-is from trial_data.json** — The `unique_file_list` contains absolute paths. Store them exactly as found without normalization.

3. **Filter out tool results** — Paths containing `/.claude/projects/` are tool result references and should be excluded from the output.

4. **New entries get value 0** — The User will manually populate token counts using external tools (Anthropic API token counter).

5. **Preserve existing values** — When merging with existing `file_token_counts.json`, never overwrite non-zero token counts.

6. **Report but keep orphans** — Files in existing JSON but not in any trial should be flagged but not removed.

7. **Warn on missing trial_data.json** — Trials without preprocessing should trigger a warning but not halt execution.

8. **Pretty-print JSON output** — Use 2-space indentation for human readability.

9. **Follow existing code patterns** — Match style of `src/cc_version.py` and `src/collect_trials.py` for consistency.

---

## Out of Scope

- **Token counting** — The tool only creates placeholders; actual token counting is done manually via external tools
- **Tool result files** — Excluded from this version; may be added in a future iteration
- **Path normalization** — No conversion between absolute/relative paths
- **Cross-collection aggregation** — Tool operates on a single collection at a time
- **Migration from old format** — User will delete existing `file_token_counts.json` and regenerate

---

## Success Criteria

1. Running `./src/update_file_summary.py dev/misc/wsd-dev-02` produces a valid `file_token_counts.json`
2. All unique project file paths from all `trial_data.json` files are included
3. Tool result paths (containing `/.claude/projects/`) are filtered out
4. Running the command twice produces identical output (idempotent)
5. Adding a new trial and re-running adds only the new files
6. All tests pass with `./wsd.py test`
7. Code passes all health checks with `./wsd.py health`

---

## Implementation Notes

**Audit Findings:**
- 2 existing `file_token_counts.json` files found (wsd-dev-02, repro-attempts)
- 25 `trial_data.json` files across collections
- 2 existing Python scripts in `src/` to use as patterns
- 2 existing test files in `tests/` to use as patterns

**Output Schema (simplified from discussion):**
```json
{
  "schema_version": "1.0",
  "description": "Token counts for unique project files read across trials",
  "generated_at": "2026-01-21T17:30:00",
  "collection": "wsd-dev-02",
  "total_files": 42,
  "files": {
    "/Users/gray/Projects/claude-bug/docs/core/Action-Plan.md": 0,
    "/Users/gray/Projects/claude-bug/source/wsd.py": 50155
  }
}
```

**CLI Usage:**
```
./src/update_file_summary.py <collection-path>
./src/update_file_summary.py --help
```

**Exit Codes:**
- 0: Success
- 1: Error (invalid path, malformed JSON, etc.)

---

## Questions for Feature-Writer

None — this brief captures all design decisions from the discovery conversation.
