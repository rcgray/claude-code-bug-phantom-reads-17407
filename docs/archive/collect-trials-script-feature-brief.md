# Feature Brief: Collect Trials Script

**Date**: 2026-01-15
**Prepared by**: User Agent (Workscope-20260115-185216)
**For**: Feature-Writer Agent

---

## Executive Summary

A Python script (`scripts/collect_trials.py`) that automates the collection of phantom read trial artifacts from chat exports and Claude Code session records, organizing them into a structured destination directory keyed by Workscope ID.

---

## Problem Statement

Running phantom read reproduction trials requires tedious manual file management:

1. Create a destination directory for trial data
2. Run the trial and `/export` the conversation
3. Search `~/.claude/projects/{project}/` for session files containing the trial's identifiers
4. Determine if the session uses flat structure (older builds) or hierarchical structure (newer builds)
5. Copy all relevant files (.jsonl, subagents/, tool-results/) to the destination

This manual process is error-prone, time-consuming, and discourages batch trial execution. Investigators need to run many trials to validate theories like the Headroom Theory, and the collection overhead is a significant friction point.

---

## Solution Overview

A CLI script that:
1. Scans an exports directory for `.txt` chat exports
2. Extracts Workscope IDs from export file contents
3. Locates corresponding session files in Claude Code's project storage
4. Copies all trial artifacts to a structured destination directory
5. Cleans up processed exports to enable idempotent batch processing

**Key Design Decision**: Workscope ID (YYYYMMDD-HHMMSS format) is the primary identifier, NOT Session UUID. This provides:
- Human-readable identifiers for conversation and notes
- No need for users to run `/status` and copy UUIDs
- Consistency with Work Journal naming conventions
- Session UUID is an internal implementation detail only

---

## Relationship to Existing Systems

### Supersedes
- `docs/features/session-analysis-scripts/Session-Analysis-Scripts-Overview.md` - This feature replaces the `collect_trials.py` portion of that spec. The `analyze_trials.py` portion will become a separate feature later.

### References
- `scripts/archive_claude_sessions.py` - Contains `encode_project_path()` function for deriving project subdirectory names. This pattern should be reused.
- `docs/core/Experiment-Methodology-02.md` - Documents the trial workflow this script supports
- `.claude/commands/wsd/init.md` - Generates Workscope IDs during `/wsd:init`

### Session Storage Structures
The script must handle two session file organizations:

**Flat Structure (older builds like 2.0.58-2.0.60):**
```
~/.claude/projects/{project}/
├── {SESSION_UUID}.jsonl
├── agent-{xxx}.jsonl
├── agent-{yyy}.jsonl
└── ...
```

**Hierarchical Structure (newer builds like 2.1.3+):**
```
~/.claude/projects/{project}/
├── {SESSION_UUID}.jsonl
└── {SESSION_UUID}/
    ├── subagents/
    │   └── agent-{xxx}.jsonl
    └── tool-results/
        └── toolu_{xxx}.txt
```

---

## Deliverables

### 1. New File: `scripts/collect_trials.py`

A Python script with the following CLI interface:

```
uv run scripts/collect_trials.py -e <exports-dir> -d <destination-dir>
```

**Arguments:**
- `-e, --exports`: Path to directory containing chat export `.txt` files (REQUIRED)
- `-d, --destination`: Path to destination directory for collected trials (REQUIRED)

**Behavior:**

1. **Validate inputs**
   - Exports directory must exist
   - Destination directory must exist (script does not create it)

2. **Scan exports**
   - Find all `*.txt` files in exports directory
   - For each, extract Workscope ID using regex pattern `Workscope ID: (\d{8}-\d{6})`
   - Skip files without valid Workscope ID (warn user)
   - Build list of (workscope_id, export_path) tuples

3. **Derive project session directory**
   - From `cwd`, compute Claude Code's project subdirectory name
   - Path: `~/.claude/projects/{encoded_cwd}/`
   - Encoding: replace all `/` with `-` (e.g., `/Users/gray/Projects/foo` → `-Users-gray-Projects-foo`)

4. **For each Workscope ID, collect trial:**

   a. **Create trial directory**: `{destination}/{WORKSCOPE_ID}/`
      - If directory already exists, skip this trial (idempotency)

   b. **Copy chat export**:
      - Copy export file to `{trial_dir}/{WORKSCOPE_ID}.txt`

   c. **Find main session file**:
      - Search all `.jsonl` files in project session directory for Workscope ID
      - Extract Session UUID from the matching file's filename
      - Error if Workscope ID not found in any session file

   d. **Copy session files** (preserving original names):
      - Copy `{SESSION_UUID}.jsonl` to trial directory
      - Handle flat vs hierarchical structure:
        - **Flat**: Find all `agent-*.jsonl` files that reference this Session UUID (grep for sessionId field)
        - **Hierarchical**: Copy `{SESSION_UUID}/` directory if it exists (contains subagents/ and tool-results/)

   e. **Delete source export**: Remove the `.txt` file from exports directory
      - Only after successful copy of all files
      - Prevents re-processing in future runs

5. **Report summary**
   - Count of trials collected
   - Count of exports skipped (no Workscope ID)
   - Any errors encountered

**Output Directory Structure:**
```
{destination}/
├── 20260115-171302/
│   ├── 20260115-171302.txt          # Chat export (renamed)
│   ├── 27eaff45-a330-4a88-9213-3725c9f420d0.jsonl  # Main session
│   └── 27eaff45-a330-4a88-9213-3725c9f420d0/       # If hierarchical
│       ├── subagents/
│       │   └── agent-aca2626.jsonl
│       └── tool-results/
│           └── toolu_xxx.txt
├── 20260115-171955/
│   ├── 20260115-171955.txt
│   ├── 504216d1-8285-4ec4-92be-0db8dc92a18a.jsonl
│   └── ...
```

### 2. Updates to Documentation

**Files to update** (2):
- `docs/core/Experiment-Methodology-02.md` - Add section on using collect_trials.py for artifact collection
- `docs/features/session-analysis-scripts/Session-Analysis-Scripts-Overview.md` - Add deprecation notice pointing to this new feature

---

## Design Constraints

1. **Workscope ID is the key** - Session UUID is only used internally to locate associated files. Users never need to know or manage Session UUIDs.

2. **Destination must pre-exist** - The script does not create the destination directory. This prevents accidental creation of mistyped paths.

3. **Idempotent by design** - Running the script multiple times is safe:
   - Existing trial directories are skipped
   - Source exports are deleted after successful collection

4. **Run from project root** - The script derives the session records location from `cwd`, so it must be run from the project where trials were conducted.

5. **Preserve original session filenames** - Session `.jsonl` files keep their UUID-based names. This allows users to see both Workscope ID (directory) and Session UUID (filename) at a glance.

6. **No version tracking** - Users who want version-specific organization can specify version-named destination directories.

---

## Out of Scope

- **Session analysis** - Detecting phantom reads in session files is a separate `analyze_trials.py` feature (future work)
- **Real-time monitoring** - Script runs after trials complete, not during
- **Cross-project collection** - Script only collects from current project's session directory
- **Export creation** - Users must manually `/export` their sessions
- **Destination directory creation** - User must create destination before running script

---

## Success Criteria

1. Script successfully collects trial artifacts from exports directory
2. Output structure matches specification (Workscope ID directories, preserved session filenames)
3. Idempotency works - re-running script doesn't duplicate or error
4. Both flat and hierarchical session structures are handled correctly
5. Source exports are cleaned up after successful collection
6. Clear error messages for missing Workscope IDs, missing session files, etc.

---

## Implementation Notes

### Existing Code Patterns

Reuse `encode_project_path()` pattern from `scripts/archive_claude_sessions.py`:
```python
def encode_project_path(project_path: Path) -> str:
    return str(project_path).replace("/", "-")
```

### Workscope ID Regex
```python
WORKSCOPE_ID_PATTERN = re.compile(r'Workscope ID: (\d{8}-\d{6})')
```

### Session UUID Extraction
The main session `.jsonl` file is named `{SESSION_UUID}.jsonl`. Extract UUID from filename after locating the file containing the Workscope ID.

### Flat vs Hierarchical Detection
- Check if `{SESSION_UUID}/` directory exists alongside `{SESSION_UUID}.jsonl`
- If yes: hierarchical (copy the directory)
- If no: flat (search for `agent-*.jsonl` files containing matching sessionId)

### Agent File Matching (Flat Structure)
In flat structure, agent files are at the same level as the main session. Match by searching for the Session UUID in each `agent-*.jsonl` file:
```python
# Each agent file contains sessionId in its JSON lines
{"sessionId": "27eaff45-a330-4a88-9213-3725c9f420d0", ...}
```

---

## Questions for Feature-Writer

None - this brief captures all design decisions from the conversation.
