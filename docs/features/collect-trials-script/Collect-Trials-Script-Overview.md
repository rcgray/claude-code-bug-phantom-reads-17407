# Collect Trials Script Specification

**Version:** 1.2.0
**Date:** 2026-01-18
**Status:** Draft

## Overview

The Collect Trials Script is a Python CLI tool (`src/collect_trials.py`) that automates the collection and organization of phantom read trial artifacts from Claude Code sessions. It replaces the tedious manual process of gathering chat exports and session `.jsonl` files after running reproduction trials, enabling investigators to focus on analysis rather than file management.

This specification defines the complete behavior of the trial collection script, including the export scanning algorithm, session file discovery mechanism, and output directory structure. The script operates on the principle that Workscope ID serves as the primary trial identifier, with Session UUID being an internal implementation detail used only for locating associated files.

For the broader investigation context this tool supports, see `docs/core/PRD.md`. For the experimental methodology that generates trials to be collected, see `docs/core/Experiment-Methodology-02.md`.

## Purpose

The Collect Trials Script serves four critical functions:

1. **Automated Artifact Collection**: Eliminates manual file copying by automatically locating and gathering all files associated with a trial (chat exports, session `.jsonl` files, subagent logs, and tool results), reducing per-trial overhead from minutes to seconds.

2. **Workscope-Keyed Organization**: Structures collected artifacts into directories named by Workscope ID (`YYYYMMDD-HHMMSS`), providing human-readable identifiers that align with Work Journal naming conventions and investigation notes.

3. **Session Structure Abstraction**: Handles all Claude Code session storage structures (flat, hybrid, and hierarchical) transparently, so investigators need not know which build produced a session.

4. **Idempotent Batch Processing**: Enables safe re-execution by skipping already-collected trials and removing processed exports, supporting workflows where investigators run multiple trials before collecting.

This specification establishes the authoritative definition of the trial collection algorithm, export scanning behavior, session file matching logic, and output directory structure.

## CLI Interface

### Command Signature

```
./src/collect_trials.py -e <exports-dir> -d <destination-dir> [-v]
```

### Arguments

| Argument              | Short | Long            | Required | Description                                           |
| --------------------- | ----- | --------------- | -------- | ----------------------------------------------------- |
| Exports Directory     | `-e`  | `--exports`     | Yes      | Path to directory containing chat export `.txt` files |
| Destination Directory | `-d`  | `--destination` | Yes      | Path to destination directory for collected trials    |
| Verbose Output        | `-v`  | `--verbose`     | No       | Print detailed progress messages during collection    |

### Execution Context

The script MUST be run from the project root directory where trials were conducted. The current working directory determines which Claude Code project session directory to search for session files.

### Exit Codes

| Code | Meaning                                                                   |
| ---- | ------------------------------------------------------------------------- |
| 0    | Success (all trials collected, or no exports to process)                  |
| 1    | Error (missing required arguments, invalid paths, or collection failures) |

## Data Structures

### CollectionResult

The `CollectionResult` dataclass tracks the outcome of a single trial collection attempt.

**Fields:**
- `workscope_id` (str): The Workscope ID of the trial (YYYYMMDD-HHMMSS format)
- `status` (str): Collection outcome - "collected", "skipped", or "failed"
- `files_copied` (list[str]): List of file paths that were successfully copied
- `error` (str | None): Error message if collection failed, None otherwise

**Status Values:**
- **"collected"**: Trial was successfully collected, all files copied, source export deleted
- **"skipped"**: Trial directory already exists (idempotency), no files copied
- **"failed"**: Collection failed due to missing session files or copy errors

## Collection Algorithm

### Overview

The collection process follows a five-stage pipeline: input validation, export scanning, session directory derivation, per-trial collection, and summary reporting.

### Algorithm Specification

```python
def collect_trials(exports_dir: Path, destination_dir: Path) -> CollectionResult:
    """
    Collect trial artifacts from exports directory to destination.

    Args:
        exports_dir: Directory containing chat export .txt files
        destination_dir: Directory where trial artifacts will be organized

    Returns:
        CollectionResult with counts of collected, skipped, and failed trials
    """

    # Stage 1: Validate inputs
    validate_directory_exists(exports_dir, "exports")
    validate_directory_exists(destination_dir, "destination")

    # Stage 2: Scan exports and extract Workscope IDs
    exports = scan_exports(exports_dir)  # List of (workscope_id, export_path)

    # Stage 3: Derive project session directory
    session_dir = derive_session_directory(Path.cwd())

    # Stage 4: Collect each trial
    results = CollectionResult()
    for workscope_id, export_path in exports:
        result = collect_single_trial(
            workscope_id, export_path, session_dir, destination_dir
        )
        results.record(result)

    # Stage 5: Report summary
    report_summary(results)

    return results
```

### Stage Details

#### Stage 1: Input Validation

Both directories MUST exist before script execution. The script does not create directories to prevent accidental creation of mistyped paths.

**Validation Rules:**
- Exports directory MUST exist and be readable
- Destination directory MUST exist and be writable
- Script does NOT create either directory

#### Stage 2: Export Scanning

The script scans the exports directory for `.txt` files and extracts Workscope IDs from their contents.

**Workscope ID Pattern:**
```python
WORKSCOPE_ID_PATTERN = re.compile(r'Workscope ID:?\s*(?:Workscope-)?(\d{8}-\d{6})')
```

This pattern handles both formats found in chat exports:
- `Workscope ID: 20260115-171302` (inline mentions)
- `Workscope ID: Workscope-20260115-171302` (Work Journal headers)

**Scanning Behavior:**
1. Find all `*.txt` files in exports directory (non-recursive)
2. For each file, search contents for Workscope ID pattern
3. Files without valid Workscope ID are skipped with a warning
4. Build list of `(workscope_id, export_path)` tuples for collection

#### Stage 3: Session Directory Derivation

Claude Code stores session files in `~/.claude/projects/{encoded_cwd}/`. The encoding replaces all `/` characters with `-`.

**Encoding Function:**
```python
def encode_project_path(project_path: Path) -> str:
    """Convert project path to Claude Code's directory naming convention.

    Example: /Users/gray/Projects/foo -> -Users-gray-Projects-foo
    """
    return str(project_path).replace("/", "-")
```

**Session Directory Path:**
```
~/.claude/projects/{encode_project_path(cwd)}/
```

#### Stage 4: Per-Trial Collection

For each Workscope ID, the script performs these steps:

**4a. Create Trial Directory**
- Path: `{destination}/{WORKSCOPE_ID}/`
- If directory already exists, skip this trial (idempotency)

**4b. Copy Chat Export**
- Copy export file to `{trial_dir}/{WORKSCOPE_ID}.txt`
- Renames export to match Workscope ID for consistency

**4c. Find Main Session File**
- Search all `.jsonl` files in session directory for Workscope ID string
- Extract Session UUID from the matching file's filename
- Error if Workscope ID not found in any session file

**4d. Copy Session Files**
- Copy `{SESSION_UUID}.jsonl` to trial directory (preserving UUID filename)
- Use the unified collection algorithm (see Session Storage Structures below)

**4e. Delete Source Export**
- Remove the `.txt` file from exports directory
- ONLY after successful copy of all files
- Enables idempotent re-execution

#### Stage 5: Summary Reporting

Output a summary including:
- Count of trials successfully collected
- Count of exports skipped (no Workscope ID or already collected)
- Any errors encountered with details

## Session Storage Structures

Claude Code has evolved its session file organization across versions. Three distinct structures have been observed, but the collection algorithm handles all of them with a unified approach.

**Note**: Session file structure (how files are organized on disk) is **independent of Era** (the phantom read error mechanism). Era determines what markers to look for when detecting phantom reads; structure determines how to collect associated files.

### Structure Types

#### Flat Structure

Agent files at root level, no session subdirectory exists. Observed in 2.0.58, 2.0.59 samples.

```
~/.claude/projects/{project}/
    {SESSION_UUID}.jsonl          # Main session file
    agent-{xxx}.jsonl             # Subagent files (same level)
    agent-{yyy}.jsonl
```

#### Hybrid Structure

Agent files at root level, but session subdirectory exists containing only `tool-results/`. Observed in some 2.0.60 samples; may exist in other versions.

```
~/.claude/projects/{project}/
    {SESSION_UUID}.jsonl          # Main session file
    agent-{xxx}.jsonl             # Subagent files (still at root)
    agent-{yyy}.jsonl
    {SESSION_UUID}/               # Session subdirectory
        tool-results/             # Only tool-results, no subagents/
            toolu_{xxx}.txt
```

#### Hierarchical Structure

No agent files at root level. Session subdirectory contains both `subagents/` and `tool-results/`. Observed in 2.1.3, 2.1.6 samples; may exist in other versions.

```
~/.claude/projects/{project}/
    {SESSION_UUID}.jsonl          # Main session file
    {SESSION_UUID}/               # Session subdirectory
        subagents/
            agent-{xxx}.jsonl
        tool-results/
            toolu_{xxx}.txt
```

### Unified Collection Algorithm

Rather than detecting structure type and branching, the script uses a unified algorithm that handles all cases:

```python
def copy_session_files(session_uuid: str, session_dir: Path, trial_dir: Path):
    """Copy all session files using unified algorithm.

    This algorithm correctly handles flat, hybrid, and hierarchical structures
    without needing to detect which type we're dealing with.
    """
    # 1. Copy main session .jsonl (always exists)
    main_session = session_dir / f"{session_uuid}.jsonl"
    shutil.copy2(main_session, trial_dir / main_session.name)

    # 2. If session subdirectory exists, copy it entirely
    #    (handles tool-results/ and/or subagents/)
    subdir = session_dir / session_uuid
    if subdir.is_dir():
        shutil.copytree(subdir, trial_dir / session_uuid)

    # 3. ALWAYS search for root-level agent files
    #    (they exist in flat and hybrid, not in hierarchical - but searching is harmless)
    for agent_file in session_dir.glob("agent-*.jsonl"):
        if file_contains_session_id(agent_file, session_uuid):
            shutil.copy2(agent_file, trial_dir / agent_file.name)
```

**Why This Works:**
- Step 2 copies any subdirectory content (empty operation if no subdirectory)
- Step 3 finds root-level agents (empty operation if none exist)
- The algorithm is correct regardless of structure type
- No structure detection logic needed

### Agent File Matching

In flat and hybrid structures, agent files at the root level reference their parent session via a `sessionId` field in their JSON lines:
```json
{"sessionId": "27eaff45-a330-4a88-9213-3725c9f420d0", ...}
```

To identify associated agent files, read the first line of each `agent-*.jsonl` file, parse the JSON, and check if the `sessionId` field matches the target Session UUID.

## Output Directory Structure

The script organizes collected artifacts into a consistent structure regardless of the source session format.

```
{destination}/
    {WORKSCOPE_ID}/                              # e.g., 20260115-171302/
        {WORKSCOPE_ID}.txt                       # Chat export (renamed)
        {SESSION_UUID}.jsonl                     # Main session (UUID preserved)
        {SESSION_UUID}/                          # If source had subdirectory
            subagents/                           # If present in source
                agent-{xxx}.jsonl
            tool-results/                        # If present in source
                toolu_{xxx}.txt
        agent-{xxx}.jsonl                        # If flat/hybrid source
        agent-{yyy}.jsonl
```

**Key Design Decisions:**
- **Directory named by Workscope ID**: Human-readable, matches investigation notes
- **Session file preserves UUID name**: Allows seeing both identifiers at a glance
- **Chat export renamed to Workscope ID**: Consistent naming within trial directory
- **Source structure preserved**: Matches original layout for compatibility

## Error Handling

### Error Categories

#### 1. Input Validation Errors

**Error:** Required argument missing or invalid

**Example Messages:**
```
Error: --exports argument is required
Error: Exports directory does not exist: /path/to/exports
Error: Destination directory does not exist: /path/to/dest
```

**Recovery:** Provide valid paths to existing directories

#### 2. Export Parsing Errors

**Error:** Export file cannot be read or lacks Workscope ID

**Example Messages:**
```
Warning: Skipping export (no Workscope ID found): trial-export.txt
Warning: Cannot read export file: corrupted-file.txt
```

**Recovery:** These are warnings, not fatal errors. The script continues processing other exports. Check export file contents if Workscope ID should be present.

#### 3. Session File Not Found

**Error:** No session file contains the Workscope ID

**Example Message:**
```
Error: No session file found containing Workscope ID 20260115-171302
  Searched: /Users/gray/.claude/projects/-Users-gray-Projects-foo/
  This may indicate the trial was run in a different project directory.
```

**Recovery:**
- Verify the script is run from the correct project directory
- Check if session files have been purged by Claude Code
- Consider using `archive_claude_sessions.py` before trials to preserve sessions

#### 4. File Copy Errors

**Error:** Cannot copy files to destination

**Example Messages:**
```
Error: Failed to copy session file: Permission denied
Error: Destination disk full
```

**Recovery:** Check destination permissions and available disk space

### Idempotency Guarantees

The script provides safe re-execution through these mechanisms:

1. **Existing trial directories are skipped**: If `{destination}/{WORKSCOPE_ID}/` exists, the trial is skipped without error
2. **Export deletion is atomic**: Source export is only deleted after all files are successfully copied
3. **Partial collection is detectable**: If a trial directory exists but is incomplete (due to previous failure), manual intervention is required

## Design Philosophy

### Workscope ID as Primary Identifier

The Workscope ID (`YYYYMMDD-HHMMSS`) serves as the user-facing trial identifier rather than Session UUID for several reasons:

- **Human-readable**: Timestamps are immediately meaningful in investigation notes
- **Consistent with workflows**: Aligns with Work Journal and workscope file naming
- **No extra steps**: Users don't need to run `/status` and copy UUIDs
- **Session UUID preserved**: The UUID remains visible in filenames for technical reference

### Pre-existing Directories Required

The script requires both exports and destination directories to exist rather than creating them automatically:

- **Prevents typos**: Mistyped paths fail fast rather than creating unexpected directories
- **Explicit setup**: Forces investigators to consciously organize their trial storage
- **Clear responsibility**: Directory creation is a one-time setup task, not script responsibility

### Source Export Deletion

Processed exports are deleted to enable clean batch workflows:

- **Idempotent batches**: Run trials, export, run script multiple times safely
- **Clear separation**: Exports directory contains only unprocessed files
- **Explicit deletion**: Only occurs after successful collection, never on error

## Testing Architecture

This section defines the testing strategy, dependency injection requirements, and test organization for the collect_trials.py script.

### Testing Approach: Phase-Aligned Testing

Tests are written alongside implementation in each phase, following a test plan created upfront. This approach:

- Keeps test context fresh (same agent writes code and tests)
- Ensures each phase ends with passing tests (QA-friendly)
- Avoids IFF documentation overhead
- Builds coverage incrementally

Each implementation phase includes corresponding test tasks. Integration tests are consolidated in a dedicated final phase.

### Dependency Injection Requirements

To enable isolated unit testing without accessing real file systems or directories, the implementation must support dependency injection for external dependencies.

#### Required Injection Points

| Parameter | Type | Default | Purpose |
|-----------|------|---------|---------|
| `cwd_path` | `Path \| None` | `Path.cwd()` | Current working directory for session path derivation |
| `home_path` | `Path \| None` | `Path.home()` | Home directory for `~/.claude/projects/` path |
| `copy_file` | `Callable \| None` | `shutil.copy2` | File copy function |
| `copy_tree` | `Callable \| None` | `shutil.copytree` | Directory copy function |
| `remove_file` | `Callable \| None` | `Path.unlink` | File deletion function |

#### Function Signatures with DI

```python
def derive_session_directory(
    cwd_path: Path | None = None,
    home_path: Path | None = None,
) -> Path:
    """Derive Claude Code session directory from current working directory."""

def copy_session_files(
    session_uuid: str,
    session_dir: Path,
    trial_dir: Path,
    copy_file: Callable[[Path, Path], None] | None = None,
    copy_tree: Callable[[Path, Path], None] | None = None,
    verbose: bool = False,
) -> list[str]:
    """Copy all session files using unified algorithm.
    
    Returns:
        List of file paths that were copied.
    """

def collect_single_trial(
    workscope_id: str,
    export_path: Path,
    session_dir: Path,
    destination_dir: Path,
    copy_file: Callable[[Path, Path], None] | None = None,
    copy_tree: Callable[[Path, Path], None] | None = None,
    remove_file: Callable[[Path], None] | None = None,
    verbose: bool = False,
) -> CollectionResult:
    """Collect a single trial's artifacts.

    Returns:
        CollectionResult containing status ('collected', 'skipped', or 'failed'),
        list of files copied, and error message if failed.
    """

def collect_trials(
    exports_dir: Path,
    destination_dir: Path,
    cwd_path: Path | None = None,
    home_path: Path | None = None,
) -> CollectionResult:
    """Main entry point for trial collection."""
```

### Test Fixtures

The test suite requires these pytest fixtures:

```python
@pytest.fixture
def tmp_exports_dir(tmp_path: Path) -> Path:
    """Provide a temporary exports directory for testing.

    Args:
        tmp_path: Pytest fixture providing temporary directory for test files.

    Returns:
        Path to temporary exports directory (created but empty).
    """

@pytest.fixture
def tmp_destination_dir(tmp_path: Path) -> Path:
    """Provide a temporary destination directory for collected trials.

    Args:
        tmp_path: Pytest fixture providing temporary directory for test files.

    Returns:
        Path to temporary destination directory (created but empty).
    """

@pytest.fixture
def tmp_session_dir(tmp_path: Path) -> Path:
    """Provide a temporary session directory mimicking ~/.claude/projects/.

    Args:
        tmp_path: Pytest fixture providing temporary directory for test files.

    Returns:
        Path to temporary session directory structure.
    """

@pytest.fixture
def flat_session_structure(tmp_session_dir: Path) -> dict[str, Path]:
    """Create flat session structure files and return paths.

    Creates:
        - {SESSION_UUID}.jsonl with Workscope ID
        - agent-{xxx}.jsonl files with sessionId field

    Args:
        tmp_session_dir: Pytest fixture providing temporary session directory.

    Returns:
        Dictionary mapping file types to their paths.
    """

@pytest.fixture
def hybrid_session_structure(tmp_session_dir: Path) -> dict[str, Path]:
    """Create hybrid session structure files and return paths.

    Creates:
        - {SESSION_UUID}.jsonl with Workscope ID
        - {SESSION_UUID}/ directory with tool-results/
        - agent-{xxx}.jsonl files at root level

    Args:
        tmp_session_dir: Pytest fixture providing temporary session directory.

    Returns:
        Dictionary mapping file types to their paths.
    """

@pytest.fixture
def hierarchical_session_structure(tmp_session_dir: Path) -> dict[str, Path]:
    """Create hierarchical session structure files and return paths.

    Creates:
        - {SESSION_UUID}.jsonl with Workscope ID
        - {SESSION_UUID}/ directory with subagents/ and tool-results/

    Args:
        tmp_session_dir: Pytest fixture providing temporary session directory.

    Returns:
        Dictionary mapping file types to their paths.
    """

@pytest.fixture
def sample_export_content() -> Callable[[str], str]:
    """Provide factory for sample chat export content with Workscope ID.

    Returns:
        Function that takes workscope_id and returns export file content.
    """

@pytest.fixture
def sample_session_content() -> Callable[[str], str]:
    """Provide factory for sample session .jsonl content with Workscope ID.

    Returns:
        Function that takes workscope_id and returns session file content.
    """
```

### Test Categories

Tests are organized into these categories, implemented across phases:

| Category | Phase | Test Count | Focus |
|----------|-------|------------|-------|
| Input Validation | 1 | 5 | Argument parsing, directory existence |
| Path Encoding | 1 | 3 | `encode_project_path()`, session directory derivation |
| Export Scanning | 2 | 8 | Workscope ID regex, both formats, edge cases |
| Session Discovery | 3 | 4 | Grep for Workscope ID, UUID extraction |
| File Copying | 4 | 6 | Unified algorithm, all three structures |
| Trial Collection | 4 | 6 | Directory creation, file naming, orchestration |
| Idempotency | 4 | 3 | Skip existing, re-run safety, export cleanup |
| Reporting | 5 | 4 | Counts and error messages |
| Integration | 6 | 4 | Full workflows, mixed structures |

**Total: ~43 test cases**

## Testing Scenarios

### Basic Collection Tests

1. **Single Trial Collection**: Given one export with valid Workscope ID and matching session file, script creates trial directory with all expected files
2. **Multiple Trial Collection**: Given three exports with distinct Workscope IDs, script creates three trial directories
3. **Empty Exports Directory**: Given no `.txt` files, script exits cleanly with zero collected count

### Edge Case Tests

1. **Duplicate Workscope ID**: Given two exports with same Workscope ID, second is skipped (trial directory exists)
2. **No Workscope ID in Export**: Given export lacking Workscope ID pattern, script warns and skips
3. **Pre-existing Trial Directory**: Given destination already contains trial directory, script skips without error
4. **Session File Missing**: Given valid export but no matching session file, script reports error and continues

### Structure Handling Tests

1. **Flat Structure Collection**: Given flat session files (no subdirectory), script correctly identifies and copies root-level agent files
2. **Hybrid Structure Collection**: Given hybrid session (subdirectory with tool-results/ but agents at root), script copies both subdirectory and root agent files
3. **Hierarchical Structure Collection**: Given hierarchical session (all content in subdirectory), script copies entire subdirectory tree
4. **Mixed Version Collection**: Given exports from different structure types, script handles each appropriately

### Idempotency Tests

1. **Re-run After Success**: Running script twice with same inputs results in "0 collected, N skipped" on second run
2. **Re-run After Partial**: If collection fails mid-batch, re-run collects remaining trials
3. **Export Cleanup Verification**: After successful collection, source export files no longer exist

## Best Practices

### For Investigators

1. **Archive Sessions First**: Run `./src/archive_claude_sessions.py` before trials to prevent session file loss from Claude Code purges

2. **Batch Your Trials**: Run multiple trials, using `/export` after each, then collect all at once:
   ```bash
   # After running trials and exporting each...
   ./src/collect_trials.py -e ~/trial-exports -d ~/trial-data/v2.1.3
   ```

3. **Version-Based Destinations**: Organize trials by Claude Code version for easier analysis:
   ```
   ~/trial-data/
       v2.0.58/
       v2.0.60/
       v2.1.3/
   ```

4. **Verify Before Deleting**: The script deletes processed exports; if you want to preserve originals, copy exports directory first

### For Implementers

1. **Reuse encode_project_path**: Import from `archive_claude_sessions.py` or copy the function to maintain consistency with Claude Code's path encoding

2. **Fail Fast on Validation**: Check directory existence before any file operations; clear error messages save debugging time

3. **Log Verbosely**: Print each file being copied and each export being processed; investigators need visibility into what the script is doing

4. **Preserve Original Names**: Keep Session UUID in filenames; investigators may need to correlate with other Claude Code tools

## Related Specifications

- **Experiment-Methodology-02.md**: Documents the trial workflow this script supports, including reproduction environment setup and trial execution procedures.
- **PRD.md**: The root document describing the phantom reads investigation this tool serves.

---

*This specification defines the authoritative rules for the Collect Trials Script including CLI interface, collection algorithm, session structure handling, and output organization. All implementations must conform to these specifications.*

## In-Flight Failures (IFF)

*No in-flight failures currently documented.*

## Feature Implementation Plan (FIP)

### Phase 1: Core Script Structure

- [x] **1.1** - Create `src/collect_trials.py` with argument parsing
  - [x] **1.1.1** - Add shebang line (`#!/usr/bin/env python`) and module docstring
  - [x] **1.1.2** - Implement argument parser with `-e/--exports` and `-d/--destination` required arguments
  - [x] **1.1.3** - Add directory existence validation for both arguments
  - [x] **1.1.4** - Implement exit codes (0 for success, 1 for error)
- [x] **1.2** - Implement path encoding functions
  - [x] **1.2.1** - Implement `encode_project_path()` function
  - [x] **1.2.2** - Implement `derive_session_directory()` with DI support for `cwd_path` and `home_path`
- [x] **1.3** - Create `tests/test_collect_trials.py` with Phase 1 tests
  - [x] **1.3.1** - Create test file with module docstring and imports
  - [x] **1.3.2** - Implement `TestArgumentParsing` class (5 tests: missing args, invalid paths, valid args)
  - [x] **1.3.3** - Implement `TestEncodeProjectPath` class (3 tests: basic encoding, edge cases)
  - [x] **1.3.4** - Implement `TestDeriveSessionDirectory` class (2 tests: with DI, path construction)

### Phase 2: Export Scanning

- [x] **2.1** - Implement export scanning functionality
  - [x] **2.1.1** - Implement glob for `*.txt` files in exports directory
  - [x] **2.1.2** - Implement Workscope ID regex extraction (pattern: `r'Workscope ID:?\s*(?:Workscope-)?(\d{8}-\d{6})'`)
  - [x] **2.1.3** - Add warning output for exports without valid Workscope ID
  - [x] **2.1.4** - Build and return list of `(workscope_id, export_path)` tuples
- [x] **2.2** - Implement Phase 2 tests
  - [x] **2.2.1** - Create `tmp_exports_dir` and `sample_export_content` fixtures
  - [x] **2.2.2** - Implement `TestExportScanning` class (8 tests: valid ID, both formats, no ID, multiple exports, empty dir, unreadable file, multiple IDs in one file, non-txt files ignored)

### Phase 3: Session File Discovery

- [x] **3.1** - Implement session file search
  - [x] **3.1.1** - Search all `.jsonl` files for Workscope ID string
  - [x] **3.1.2** - Extract Session UUID from matching filename
  - [x] **3.1.3** - Handle case where no session file contains Workscope ID
- [x] **3.2** - Implement Phase 3 tests
  - [x] **3.2.1** - Create `tmp_session_dir` and `sample_session_content` fixtures
  - [x] **3.2.2** - Implement `TestSessionFileDiscovery` class (4 tests: found, not found, multiple files, UUID extraction)

### Phase 4: Trial Collection

- [x] **4.1** - Implement single trial collection using unified algorithm
  - [x] **4.1.1** - Create trial directory `{destination}/{WORKSCOPE_ID}/`
  - [x] **4.1.2** - Skip if trial directory already exists (idempotency)
  - [x] **4.1.3** - Copy chat export as `{WORKSCOPE_ID}.txt`
  - [x] **4.1.4** - Copy main session `.jsonl` file (preserve UUID filename)
  - [x] **4.1.5** - Implement `copy_session_files()` with DI support for copy functions
  - [x] **4.1.6** - Copy session subdirectory if it exists (handles tool-results/ and subagents/)
  - [x] **4.1.7** - Search and copy root-level `agent-*.jsonl` files matching session UUID
  - [x] **4.1.8** - Delete source export only after successful copy
- [x] **4.2** - Implement batch collection loop
  - [x] **4.2.1** - Iterate over all scanned exports
  - [x] **4.2.2** - Track collected, skipped, and failed counts
  - [x] **4.2.3** - Continue processing on individual trial errors
- [x] **4.3** - Implement Phase 4 tests
  - [x] **4.3.1** - Create `flat_session_structure`, `hybrid_session_structure`, `hierarchical_session_structure` fixtures
  - [x] **4.3.2** - Implement `TestCopySessionFiles` class (6 tests: flat, hybrid, hierarchical, agent matching, no subdirectory, no root agents)
  - [x] **4.3.3** - Implement `TestCollectSingleTrial` class (6 tests: success, directory creation, file naming, export deletion, skip existing)
  - [x] **4.3.4** - Implement `TestIdempotency` class (3 tests: re-run skips, export cleanup, partial recovery)

### Phase 5: Output and Reporting

- [x] **5.1** - Implement progress output
  - [x] **5.1.1** - Print each trial being collected with workscope ID
  - [x] **5.1.2** - Print files being copied
  - [x] **5.1.3** - Print warnings for skipped exports
- [x] **5.2** - Implement summary report
  - [x] **5.2.1** - Report count of trials collected
  - [x] **5.2.2** - Report count of exports skipped (no Workscope ID)
  - [x] **5.2.3** - Report count of trials skipped (already exist)
  - [x] **5.2.4** - Report any errors with details
- [x] **5.3** - Implement Phase 5 tests
  - [x] **5.3.1** - Implement `TestProgressOutput` class (3 tests: collection messages, copy messages, warnings)
  - [x] **5.3.2** - Implement `TestSummaryReport` class (4 tests: collected count, skipped count, error details, zero case)

### Phase 6: Integration Tests

- [x] **6.1** - Implement comprehensive integration tests
  - [x] **6.1.1** - Implement `TestIntegrationSingleTrial` (end-to-end single trial collection)
  - [x] **6.1.2** - Implement `TestIntegrationMultipleTrials` (batch collection with mixed outcomes)
  - [x] **6.1.3** - Implement `TestIntegrationMixedStructures` (flat + hybrid + hierarchical in same batch)
  - [x] **6.1.4** - Implement `TestIntegrationErrorRecovery` (partial failures, continuation)
- [x] **6.2** - Final test coverage verification
  - [x] **6.2.1** - Run full test suite and verify all tests pass
  - [x] **6.2.2** - Verify test coverage meets project standards

### Phase 7: Documentation Updates

- [x] **7.1** - Update `docs/core/Experiment-Methodology-02.md`
  - [x] **7.1.1** - Add section on using `collect_trials.py` for artifact collection
  - [x] **7.1.2** - Document recommended workflow with exports and collection
