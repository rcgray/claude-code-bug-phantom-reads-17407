# Update File Summary Specification

**Version:** 1.0.0
**Date:** 2026-01-21
**Status:** Draft

## Overview

The Update File Summary tool is a Python CLI script (`src/update_file_summary.py`) that aggregates unique project file paths from all `trial_data.json` files within a trial collection and produces or updates a `file_token_counts.json` file at the collection root. This enables investigators to analyze correlations between file sizes (measured in tokens) and phantom read occurrence across trials.

This specification defines the complete behavior of the file summary tool, including collection scanning, path extraction, merge logic for preserving existing token counts, and summary reporting. The tool operates on the principle that file paths serve as correlation identifiers rather than filesystem references, and it maintains idempotency across repeated executions.

For the broader investigation context this tool supports, see `docs/core/PRD.md`. For the trial data schema that provides input to this tool, see the `trial_data.json` schema documentation.

## Purpose

The Update File Summary tool serves four critical functions:

1. **Path Aggregation**: Collects all unique project file paths from `file_reads.unique_file_list` arrays across all `trial_data.json` files within a collection, providing a unified view of files accessed during phantom read trials.

2. **Token Count Scaffolding**: Initializes new file entries with zero token counts, creating placeholders that investigators populate manually using external token counting tools (Anthropic API).

3. **Incremental Updates**: Merges new file paths with existing `file_token_counts.json` data, preserving manually-entered token counts while adding newly discovered files as the collection grows.

4. **Orphan Detection**: Identifies files present in the existing summary but not found in any trial's `unique_file_list`, flagging potential data integrity issues without removing the entries.

This specification establishes the authoritative definition of the file summary generation algorithm, the `file_token_counts.json` output schema, merge behavior, and summary reporting format.

## CLI Interface

### Command Signature

```
./src/update_file_summary.py <collection-path> [--help]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `collection-path` | Yes | Path to trial collection directory containing trial folders with `trial_data.json` files |
| `--help` | No | Display usage information and exit |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (file summary created or updated) |
| 1 | Error (invalid path, malformed JSON, or processing failure) |

## Data Structures

### Output Schema: file_token_counts.json

The tool produces a JSON file with the following structure:

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

### Field Definitions

#### schema_version

**Type:** String
**Purpose:** Identifies the output schema version for future compatibility
**Required:** Yes
**Value:** `"1.0"` (current version)

#### description

**Type:** String
**Purpose:** Human-readable description of the file's purpose
**Required:** Yes
**Value:** `"Token counts for unique project files read across trials"`

#### generated_at

**Type:** String (ISO 8601 datetime)
**Purpose:** Timestamp of last generation or update
**Required:** Yes
**Format:** `YYYY-MM-DDTHH:MM:SS`

#### collection

**Type:** String
**Purpose:** Name of the collection directory (derived from path)
**Required:** Yes
**Example:** `"wsd-dev-02"`

#### total_files

**Type:** Integer
**Purpose:** Count of unique files in the `files` object
**Required:** Yes

#### files

**Type:** Object (string keys, integer values)
**Purpose:** Maps absolute file paths to token counts
**Required:** Yes
**Key format:** Absolute file path as stored in `trial_data.json`
**Value format:** Integer token count (0 for unprocessed files)

## Processing Algorithm

### Overview

The processing follows a four-stage pipeline: collection scanning, path aggregation, merge with existing data, and output generation with summary reporting.

### Helper Function Signatures

The main algorithm relies on these helper functions:

```python
def find_trial_directories(collection_path: Path) -> list[Path]:
    """Return list of immediate subdirectories of collection_path."""

def load_json(path: Path) -> dict:
    """Read and parse JSON file, raising ValueError on parse error."""

def load_existing_data(path: Path) -> dict | None:
    """Load existing file_token_counts.json, or return None if not exists."""

def write_output(path: Path, files: dict[str, int], collection_name: str) -> None:
    """Write file_token_counts.json with schema-compliant structure."""

def report_summary(total: int, new: int, orphans: list[str], skipped: list[str]) -> None:
    """Print formatted summary report to stdout."""
```

### Algorithm Specification

```python
def update_file_summary(collection_path: Path) -> None:
    """
    Update or create file_token_counts.json for a trial collection.

    Args:
        collection_path: Path to collection directory containing trial folders

    Raises:
        FileNotFoundError: If collection_path does not exist
        ValueError: If collection_path is not a directory
    """

    # Stage 1: Scan collection for trial directories
    trial_dirs = find_trial_directories(collection_path)

    # Stage 2: Aggregate unique file paths
    all_paths = set()
    skipped_trials = []
    for trial_dir in trial_dirs:
        trial_data_path = trial_dir / "trial_data.json"
        if not trial_data_path.exists():
            skipped_trials.append(trial_dir.name)
            continue

        trial_data = load_json(trial_data_path)
        unique_files = trial_data.get("file_reads", {}).get("unique_file_list", [])

        for path in unique_files:
            all_paths.add(path)

    # Stage 3: Merge with existing file_token_counts.json
    output_path = collection_path / "file_token_counts.json"
    existing_data = load_existing_data(output_path)
    merged_files, new_count, orphans = merge_file_data(existing_data, all_paths)

    # Stage 4: Write output and report summary
    write_output(output_path, merged_files, collection_path.name)
    report_summary(len(merged_files), new_count, orphans, skipped_trials)
```

### Stage Details

#### Stage 1: Collection Scanning

The script scans the collection directory for trial subdirectories. A trial directory is any immediate subdirectory of the collection path.

**Scanning Rules:**
- Scan only immediate subdirectories (non-recursive at top level)
- Each subdirectory is considered a potential trial directory
- Presence of `trial_data.json` determines if trial is processable

#### Stage 2: Path Aggregation

For each trial directory containing `trial_data.json`, extract all file paths from `file_reads.unique_file_list`.

**Aggregation Behavior:**
- All paths from `unique_file_list` are included without filtering
- Paths are stored exactly as found in `trial_data.json` (no normalization)
- Duplicate paths across trials are deduplicated via set operations

**Missing trial_data.json Handling:**
- Log warning to stderr: `Warning: Skipping trial (no trial_data.json): {trial_name}`
- Continue processing remaining trials
- Track skipped trials for summary report

#### Stage 3: Merge Logic

When `file_token_counts.json` already exists, merge new paths with existing data.

**Merge Rules:**

1. **Existing entries with non-zero values**: Preserve the token count value
2. **Existing entries with zero values**: Keep as zero (may be updated later)
3. **New paths not in existing file**: Add with token count of 0
4. **Orphaned entries** (in existing file but not in any trial): Keep in output, report in summary

```python
def merge_file_data(
    existing_data: dict | None,
    current_paths: set[str]
) -> tuple[dict[str, int], int, list[str]]:
    """
    Merge current paths with existing file token counts.

    Args:
        existing_data: Existing file_token_counts.json data, or None if new
        current_paths: Set of file paths from current scan

    Returns:
        Tuple of:
            - Merged files dict (path -> token count)
            - Count of new files added
            - List of orphaned file paths
    """
    if existing_data is None:
        # All paths are new
        return {path: 0 for path in sorted(current_paths)}, len(current_paths), []

    existing_files = existing_data.get("files", {})
    merged = {}
    new_count = 0
    orphans = []

    # Process current paths
    for path in current_paths:
        if path in existing_files:
            merged[path] = existing_files[path]  # Preserve existing value
        else:
            merged[path] = 0  # New entry
            new_count += 1

    # Detect orphans
    for path in existing_files:
        if path not in current_paths:
            orphans.append(path)
            merged[path] = existing_files[path]  # Keep orphan with its value

    return dict(sorted(merged.items())), new_count, orphans
```

#### Stage 4: Output Generation and Reporting

Write the merged data to `file_token_counts.json` and print a summary report.

**Output Formatting:**
- JSON with 2-space indentation for human readability
- Files sorted alphabetically by path
- Trailing newline for POSIX compliance

**Summary Report Format:**
```
================================================================================
File Summary Updated: wsd-dev-02
================================================================================
Total files:     42
New files added: 7
Orphaned files:  2
Skipped trials:  1

Orphaned files (in summary but not in any trial):
  - /Users/gray/Projects/old-file.md
  - /Users/gray/Projects/removed-file.py

Skipped trials (no trial_data.json):
  - 20260115-171302
================================================================================
```

## Error Handling

### Error Categories

#### 1. Path Validation Errors

**Error:** Collection path does not exist or is not a directory

**Example Messages:**
```
Error: Collection path does not exist: /path/to/collection
Error: Collection path is not a directory: /path/to/file.txt
```

**Recovery:** Provide a valid path to an existing directory

#### 2. JSON Parsing Errors

**Error:** trial_data.json or existing file_token_counts.json contains invalid JSON

**Example Messages:**
```
Error: Failed to parse trial_data.json in trial 20260115-171302: Expecting ',' delimiter
Error: Failed to parse existing file_token_counts.json: Invalid control character
```

**Recovery:** Fix malformed JSON files. For trial_data.json, regenerate using `/update-trial-data`. For file_token_counts.json, delete and regenerate.

#### 3. Schema Validation Errors

**Error:** trial_data.json lacks expected structure

**Example Messages:**
```
Error: trial_data.json in 20260115-171302 missing 'file_reads' key
Warning: trial_data.json in 20260115-171302 has no unique_file_list (treating as empty)
```

**Recovery:** Ensure trial_data.json conforms to schema 1.2. Regenerate using `/update-trial-data` if necessary.

#### 4. File Write Errors

**Error:** Cannot write to output file

**Example Messages:**
```
Error: Cannot write file_token_counts.json: Permission denied
Error: Cannot write file_token_counts.json: Disk full
```

**Recovery:** Check write permissions on collection directory and available disk space

### Idempotency Guarantees

The tool provides safe re-execution through these mechanisms:

1. **Merge preserves values**: Existing non-zero token counts are never overwritten
2. **Orphans are retained**: Files removed from trials remain in summary for investigation
3. **Deterministic output**: Same input produces identical output (sorted keys, consistent formatting)
4. **Atomic write**: Output file is written completely or not at all

## Design Philosophy

### Paths as Identifiers

File paths in this tool serve as correlation identifiers, not filesystem references:

- **No file access**: The tool never reads or validates the files at the stored paths
- **Exact preservation**: Paths are stored exactly as they appear in trial_data.json
- **No normalization**: No resolution of symlinks, relative paths, or case normalization

This design allows analysis of historical trial data even when the original project files have changed or been deleted.

### Zero as Placeholder

New entries are initialized with token count of 0 rather than null or a separate flag:

- **Consistent type**: All values are integers, simplifying analysis code
- **Clear semantics**: 0 means "not yet counted", non-zero means "counted"
- **Manual population**: Investigators use external tools to populate counts

### Orphan Retention

Files in the existing summary but not in any current trial are retained with a warning:

- **Data preservation**: Never deletes data that may represent manual work
- **Investigation aid**: Orphans may indicate trials that were removed or data issues
- **Explicit handling**: Summary report clearly identifies orphaned entries

## Testing Scenarios

### Basic Processing Tests

1. **Empty Collection**: Given a collection with no trial directories, script creates file_token_counts.json with zero files and reports appropriately
2. **Single Trial**: Given one trial with valid trial_data.json, script extracts unique files and creates output with all entries set to 0
3. **Multiple Trials**: Given multiple trials, script aggregates unique paths across all trials and deduplicates correctly

### Merge Behavior Tests

1. **Preserve Non-Zero Values**: Given existing file_token_counts.json with populated token counts, running script preserves those values
2. **Add New Files**: Given new trial with files not in existing summary, script adds new entries with count 0
3. **Detect Orphans**: Given existing summary with files not in any current trial, script reports orphans but retains them
4. **Fresh Creation**: Given collection with no existing file_token_counts.json, script creates new file with all zeros

### Edge Case Tests

1. **Missing trial_data.json**: Given trial directory without trial_data.json, script warns and continues with other trials
2. **Empty unique_file_list**: Given trial_data.json with empty file list, script processes without error
3. **Missing unique_file_list Key**: Given trial_data.json without `unique_file_list` key, script warns and treats as empty list
4. **Malformed JSON**: Given invalid JSON in trial_data.json, script reports error with trial name and continues
5. **Duplicate Paths Across Trials**: Given same file path in multiple trials, script includes path only once

### Integration Tests

1. **Full Workflow**: Create collection with multiple trials, run script, verify output structure and content
2. **Incremental Update**: Create initial summary, add new trial, run script, verify new files added and existing preserved
3. **Idempotent Re-run**: Run script twice on same collection, verify output is identical

## Best Practices

### For Investigators

1. **Run After Trial Preprocessing**: Execute this tool after running `/update-trial-data` on all trials to ensure trial_data.json files are current

2. **Populate Token Counts Systematically**: After running the tool, use the Anthropic API token counter to populate non-zero values for correlation analysis

3. **Check Orphan Reports**: When orphans are reported, investigate whether they indicate:
   - Trials that were deleted but should be preserved
   - Data corruption in trial_data.json files
   - Expected cleanup of old trial data

4. **Version Your Summaries**: Consider copying file_token_counts.json before major updates to preserve historical snapshots

### For Implementers

1. **Follow Existing Patterns**: Match the code style of `src/cc_version.py` and `src/collect_trials.py` for consistency with the project

2. **Use Dependency Injection**: Support testability by allowing injection of file I/O functions where practical

3. **Fail Fast on Critical Errors**: Exit immediately for path validation failures; continue processing for individual trial errors

4. **Log Informatively**: Provide clear progress indication and detailed error messages that include trial names and file paths

## Related Specifications

- **`docs/core/PRD.md`**: The root document describing the phantom reads investigation and the role of correlation analysis
- **`src/collect_trials.py`**: The trial collection script that creates the trial directory structure this tool operates on; serves as a code pattern exemplar
- **`src/cc_version.py`**: Provides patterns for CLI structure, argument parsing, and error handling used by this tool

---

*This specification defines the authoritative rules for the Update File Summary tool including CLI interface, processing algorithm, merge behavior, and output format. All implementations must conform to these specifications.*

## In-Flight Failures (IFF)

None. This is a new feature with no prior implementation phases.

## Feature Implementation Plan (FIP)

### Phase 1: Core Script Structure

- [ ] **1.1** - Create `src/update_file_summary.py` with CLI foundation
  - [ ] **1.1.1** - Add shebang line (`#!/usr/bin/env python`) and module docstring following `cc_version.py` pattern
  - [ ] **1.1.2** - Implement argument parser with positional `collection-path` argument and `--help`
  - [ ] **1.1.3** - Add collection path validation (exists, is directory)
  - [ ] **1.1.4** - Implement exit codes (0 for success, 1 for error)
  - [ ] **1.1.5** - Create `main()` function with standard entry point pattern

- [ ] **1.2** - Create `tests/test_update_file_summary.py` with Phase 1 tests
  - [ ] **1.2.1** - Create test file with module docstring and imports
  - [ ] **1.2.2** - Implement argument parsing tests (valid path, invalid path, help flag)
  - [ ] **1.2.3** - Implement path validation tests (not exists, not directory, valid directory)

### Phase 2: Collection Scanning and Path Extraction

- [ ] **2.1** - Implement collection scanning functionality
  - [ ] **2.1.1** - Implement `find_trial_directories()` to enumerate immediate subdirectories
  - [ ] **2.1.2** - Implement `load_trial_data()` to read and parse trial_data.json
  - [ ] **2.1.3** - Implement extraction of `file_reads.unique_file_list` from trial data
  - [ ] **2.1.4** - Add warning output for trials missing trial_data.json

- [ ] **2.2** - Implement Phase 2 tests
  - [ ] **2.2.1** - Create `tmp_collection_dir` fixture with mock trial structure
  - [ ] **2.2.2** - Create `sample_trial_data` fixture for generating trial_data.json content
  - [ ] **2.2.3** - Implement tests for `find_trial_directories()` (empty, single, multiple trials)
  - [ ] **2.2.4** - Implement tests for missing trial_data.json handling (warning, continues)
  - [ ] **2.2.5** - Implement test for missing `unique_file_list` key (treated as empty list)

### Phase 3: Merge Logic and Output Generation

- [ ] **3.1** - Implement merge functionality
  - [ ] **3.1.1** - Implement `load_existing_summary()` to read existing file_token_counts.json
  - [ ] **3.1.2** - Implement `merge_file_data()` with value preservation and orphan detection
  - [ ] **3.1.3** - Implement new file initialization (all new entries get value 0)

- [ ] **3.2** - Implement output generation
  - [ ] **3.2.1** - Implement `write_summary()` with schema-compliant JSON structure
  - [ ] **3.2.2** - Add 2-space indentation and sorted keys for output formatting
  - [ ] **3.2.3** - Generate `generated_at` timestamp and `collection` name fields
  - [ ] **3.2.4** - Calculate and include `total_files` count

- [ ] **3.3** - Implement Phase 3 tests
  - [ ] **3.3.1** - Implement merge tests (preserve values, add new, detect orphans)
  - [ ] **3.3.2** - Implement output format tests (schema compliance, sorting, indentation)
  - [ ] **3.3.3** - Implement fresh creation test (no existing file)

### Phase 4: Summary Reporting

- [ ] **4.1** - Implement summary report
  - [ ] **4.1.1** - Implement `print_summary()` with formatted output
  - [ ] **4.1.2** - Report total files, new files added, orphaned files count
  - [ ] **4.1.3** - List orphaned file paths when present
  - [ ] **4.1.4** - List skipped trials when present

- [ ] **4.2** - Implement Phase 4 tests
  - [ ] **4.2.1** - Implement summary output tests (all counts, orphan listing, skipped trials)
  - [ ] **4.2.2** - Implement clean output test (no orphans, no skipped trials)

### Phase 5: Integration and Polish

- [ ] **5.1** - Implement integration tests
  - [ ] **5.1.1** - Implement full workflow test (create collection, run script, verify output)
  - [ ] **5.1.2** - Implement incremental update test (add trial, re-run, verify merge)
  - [ ] **5.1.3** - Implement idempotency test (run twice, verify identical output)

- [ ] **5.2** - Error handling refinement
  - [ ] **5.2.1** - Add comprehensive error messages with context (trial names, file paths)
  - [ ] **5.2.2** - Implement graceful handling of malformed trial_data.json (warn and continue)

- [ ] **5.3** - Final verification
  - [ ] **5.3.1** - Run full test suite and verify all tests pass
  - [ ] **5.3.2** - Run `./wsd.py health` and verify no issues
  - [ ] **5.3.3** - Test against actual collection (dev/misc/wsd-dev-02) and verify output
