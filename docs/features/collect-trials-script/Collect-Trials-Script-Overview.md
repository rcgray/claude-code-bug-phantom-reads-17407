# Collect Trials Script Specification

**Version:** 1.1.0
**Date:** 2026-01-15
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
./src/collect_trials.py -e <exports-dir> -d <destination-dir>
```

### Arguments

| Argument              | Short | Long            | Required | Description                                           |
| --------------------- | ----- | --------------- | -------- | ----------------------------------------------------- |
| Exports Directory     | `-e`  | `--exports`     | Yes      | Path to directory containing chat export `.txt` files |
| Destination Directory | `-d`  | `--destination` | Yes      | Path to destination directory for collected trials    |

### Execution Context

The script MUST be run from the project root directory where trials were conducted. The current working directory determines which Claude Code project session directory to search for session files.

### Exit Codes

| Code | Meaning                                                                   |
| ---- | ------------------------------------------------------------------------- |
| 0    | Success (all trials collected, or no exports to process)                  |
| 1    | Error (missing required arguments, invalid paths, or collection failures) |

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

## Feature Implementation Plan (FIP)

### Phase 1: Core Script Structure

- [ ] **1.1** - Create `src/collect_trials.py` with argument parsing
  - [ ] **1.1.1** - Add shebang line (`#!/usr/bin/env python`)
  - [ ] **1.1.2** - Implement argument parser with `-e/--exports` and `-d/--destination` required arguments
  - [ ] **1.1.3** - Add directory existence validation for both arguments
  - [ ] **1.1.4** - Implement exit codes (0 for success, 1 for error)
- [ ] **1.2** - Implement `encode_project_path()` function
  - [ ] **1.2.1** - Copy pattern from `archive_claude_sessions.py` for consistency
  - [ ] **1.2.2** - Add function to derive session directory from cwd

### Phase 2: Export Scanning

- [ ] **2.1** - Implement export scanning functionality
  - [ ] **2.1.1** - Implement glob for `*.txt` files in exports directory
  - [ ] **2.1.2** - Implement Workscope ID regex extraction (pattern: `r'Workscope ID:?\s*(?:Workscope-)?(\d{8}-\d{6})'`)
  - [ ] **2.1.3** - Add warning output for exports without valid Workscope ID
  - [ ] **2.1.4** - Build and return list of `(workscope_id, export_path)` tuples

### Phase 3: Session File Discovery

- [ ] **3.1** - Implement session file search
  - [ ] **3.1.1** - Search all `.jsonl` files for Workscope ID string
  - [ ] **3.1.2** - Extract Session UUID from matching filename
  - [ ] **3.1.3** - Handle case where no session file contains Workscope ID

### Phase 4: Trial Collection

- [ ] **4.1** - Implement single trial collection using unified algorithm
  - [ ] **4.1.1** - Create trial directory `{destination}/{WORKSCOPE_ID}/`
  - [ ] **4.1.2** - Skip if trial directory already exists (idempotency)
  - [ ] **4.1.3** - Copy chat export as `{WORKSCOPE_ID}.txt`
  - [ ] **4.1.4** - Copy main session `.jsonl` file (preserve UUID filename)
  - [ ] **4.1.5** - Copy session subdirectory if it exists (handles tool-results/ and subagents/)
  - [ ] **4.1.6** - Search and copy root-level `agent-*.jsonl` files matching session UUID
  - [ ] **4.1.7** - Delete source export only after successful copy
- [ ] **4.2** - Implement batch collection loop
  - [ ] **4.2.1** - Iterate over all scanned exports
  - [ ] **4.2.2** - Track collected, skipped, and failed counts
  - [ ] **4.2.3** - Continue processing on individual trial errors

### Phase 5: Output and Reporting

- [ ] **5.1** - Implement progress output
  - [ ] **5.1.1** - Print each trial being collected with workscope ID
  - [ ] **5.1.2** - Print files being copied
  - [ ] **5.1.3** - Print warnings for skipped exports
- [ ] **5.2** - Implement summary report
  - [ ] **5.2.1** - Report count of trials collected
  - [ ] **5.2.2** - Report count of exports skipped (no Workscope ID)
  - [ ] **5.2.3** - Report count of trials skipped (already exist)
  - [ ] **5.2.4** - Report any errors with details

### Phase 6: Documentation Updates

- [ ] **6.1** - Update `docs/core/Experiment-Methodology-02.md`
  - [ ] **6.1.1** - Add section on using `collect_trials.py` for artifact collection
  - [ ] **6.1.2** - Document recommended workflow with exports and collection
