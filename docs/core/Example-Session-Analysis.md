# Example Session Analysis

This document tracks our investigation into Claude Code session file structure and phantom read detection patterns. The analysis uses sample sessions collected from various builds, stored in `dev/misc/session-examples/`.

**Purpose**: Inform the design of the Session Analysis Scripts feature by examining real session data.

**Sample Data**:
- Era 1 (old mechanism): `2.0.58-good/`, `2.0.58-bad/`
- Era 2 (new mechanism): `2.1.6-good/`, `2.1.6-bad/`

---

## Question 1: How to Associate .jsonl Session Files Together

**Question**: How can we effectively associate multiple `.jsonl` session files that belong to the same session?

### Findings

#### Session ID Mechanism

Each session has a unique **Session ID** in UUID format (e.g., `0357781f-d024-4cef-8496-56501c76afb3`). This ID appears in two places:

1. **Main session filename**: The main session file is named `{sessionId}.jsonl`
2. **Message `sessionId` field**: Every message in all associated files contains a `sessionId` field

**Example (2.1.6-good main session)**:
```
Filename: 0357781f-d024-4cef-8496-56501c76afb3.jsonl
Line 2: {"type": "user", "sessionId": "0357781f-d024-4cef-8496-56501c76afb3", "version": "2.1.6", ...}
```

#### Directory Structure Changes

The session file organization differs between eras:

**Era 1 (2.0.58 and earlier)**:
```
{project-sessions-dir}/
├── {sessionId}.jsonl           # Main session
├── agent-{shortId}.jsonl       # Sub-agent 1
├── agent-{shortId}.jsonl       # Sub-agent 2
└── agent-{shortId}.jsonl       # Sub-agent 3
```

All files are flat in the same directory. Agent files reference the parent session via the `sessionId` field in their messages.

**Era 2 (2.1.6 and later)**:
```
{project-sessions-dir}/
├── {sessionId}.jsonl           # Main session
└── {sessionId}/                # Session subdirectory
    ├── subagents/
    │   └── agent-{shortId}.jsonl
    └── tool-results/
        └── toolu_{toolUseId}.txt
```

The session now has its own subdirectory containing subagents and persisted tool results.

#### Linking Mechanism

**To find all files for a session**:

1. **Identify the main session file**: Any `.jsonl` file with a UUID-format filename
2. **Check for matching subdirectory**: Look for a directory named `{sessionId}/`
3. **Choose association strategy based on directory existence** (not version number):
   - **If subdirectory exists**: Use hierarchical structure (organized for us)
   - **If no subdirectory**: Use flat structure (scan sibling agent files)

#### Algorithm for Session Association

```python
def find_session_files(main_session_path: Path) -> dict:
    """
    Find all files associated with a session.
    
    The algorithm checks for directory existence to determine structure,
    independent of Claude Code version number.
    
    Returns:
        {
            'main': Path to main session file,
            'agents': List of agent file paths,
            'tool_results': List of tool result file paths (hierarchical only)
        }
    """
    session_id = extract_session_id(main_session_path)
    session_dir = main_session_path.parent
    
    result = {
        'main': main_session_path,
        'agents': [],
        'tool_results': []
    }
    
    # Check for hierarchical subdirectory structure
    session_subdir = session_dir / session_id
    if session_subdir.exists():
        # Hierarchical: Look in organized subdirectory
        subagents_dir = session_subdir / 'subagents'
        if subagents_dir.exists():
            result['agents'] = list(subagents_dir.glob('agent-*.jsonl'))
        
        tool_results_dir = session_subdir / 'tool-results'
        if tool_results_dir.exists():
            result['tool_results'] = list(tool_results_dir.glob('toolu_*.txt'))
    else:
        # Flat: Scan all agent-*.jsonl files in same directory
        for agent_file in session_dir.glob('agent-*.jsonl'):
            if extract_session_id(agent_file) == session_id:
                result['agents'].append(agent_file)
    
    return result
```

### Verification

**2.0.58-good sample**:
- Main session: `c489af7a-584d-4276-a76c-ddb29f988ace.jsonl`
- Agent files: `agent-07bd3f25.jsonl`, `agent-17c7da61.jsonl`, `agent-af401ba5.jsonl`
- All agent files contain `sessionId: c489af7a-584d-4276-a76c-ddb29f988ace` ✓

**2.1.6-good sample**:
- Main session: `0357781f-d024-4cef-8496-56501c76afb3.jsonl`
- Subdirectory: `0357781f-d024-4cef-8496-56501c76afb3/`
- Agent file: `subagents/agent-aee03d2.jsonl` (contains matching sessionId) ✓

### Design Implications for Session Analysis Scripts

1. **Session discovery**: Find main sessions by identifying `.jsonl` files with UUID-format filenames
2. **Structure detection**: Check for subdirectory existence, not version number
3. **Associated files**: Use directory structure if available, fall back to flat scanning
4. **Tool results**: Only present in hierarchical structure; contain actual persisted content

---

## Question 2: How to Pair Session Files with Chat Export

**Question**: How can we effectively pair a set of `.jsonl` session files with their chat export file (if it exists)?

### Findings

#### The Challenge

Chat exports (`.txt` files from `/export` command) do NOT contain the raw Session ID (UUID). The Session ID only exists in:
- Session filenames
- The `sessionId` field within `.jsonl` messages

This means we cannot directly match exports to sessions by Session ID.

#### Solution: Workscope ID

Both session files and exports contain a **Workscope ID** (format: `YYYYMMDD-HHMMSS`) that is generated during the session via the `date` command as part of `/wsd:init`. This ID appears in both locations and serves as the linking key.

**In session file (2.1.6-good)**:
```
$ grep -o "20260113-095602" 0357781f-d024-4cef-8496-56501c76afb3.jsonl
20260113-095602   # appears multiple times
```

**In export file (2.1.6-good.txt)**:
```
⏺ Workscope ID: 20260113-095602
⏺ Bash(bash scripts/init_work_journal.sh "20260113-095602")
```

**Verified in both directory structure types**:
- 2.0.58-good (flat): Workscope ID `20260113-020300` appears in both session and export
- 2.1.6-good (hierarchical): Workscope ID `20260113-095602` appears in both session and export

#### Why This Works

Since `/wsd:init --custom` is already part of the reproduction steps for each trial, every trial session automatically contains a Workscope ID. This provides a natural linking mechanism without requiring any additional commands or markers.

#### Matching Algorithm

```python
def extract_workscope_id(file_path: Path) -> Optional[str]:
    """
    Extract Workscope ID from a file.
    
    Pattern: "Workscope ID: YYYYMMDD-HHMMSS"
    
    Returns:
        Workscope ID string (YYYYMMDD-HHMMSS) if found, None otherwise
    """
    pattern = r'Workscope ID: (\d{8}-\d{6})'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    match = re.search(pattern, content)
    if match:
        return match.group(1)
    
    return None


def match_session_to_export(session_path: Path, exports_dir: Path) -> Optional[Path]:
    """
    Find the export file that matches a session file.
    
    Returns:
        Path to matching export, or None if no match found
    """
    workscope_id = extract_workscope_id(session_path)
    if not workscope_id:
        return None
    
    for export_file in exports_dir.glob('*.txt'):
        export_id = extract_workscope_id(export_file)
        if export_id == workscope_id:
            return export_file
    
    return None
```

### Design Implications for Session Analysis Scripts

1. **Trial identification**: Use `Workscope ID: YYYYMMDD-HHMMSS` pattern
2. **Export matching**: Scan exports for matching Workscope ID, not filename
3. **Optional exports**: Exports are optional; sessions without matching exports are still valid trials
4. **First match wins**: Use first occurrence of pattern in file

---

## Question 3: Session Without `<persisted-output>` Phantom Reads (Era 2)

**Question**: What does a session look like when NO phantom reads occur in a 2.0.60+ build?

### Findings

**Sample examined**: `2.1.6-good/`

#### Successful Read Structure

A successful Read tool result has this JSON structure:

```json
{
  "type": "user",
  "message": {
    "content": [{
      "type": "tool_result",
      "tool_use_id": "toolu_01QintgrhnXTAtR3HW6TZjSK",
      "content": "     1→# Work Journal - 2026-01-13 09:56\n     2→## Workscope ID..."
    }]
  },
  "toolUseResult": {
    "type": "text",
    "file": {
      "filePath": "/path/to/file.md",
      "content": "# Work Journal...",
      "numLines": 4,
      "startLine": 1,
      "totalLines": 4
    }
  }
}
```

**Key fields**:
- `message.content[].content`: File content WITH line number prefixes (`1→`, `2→`, etc.) - this is what gets sent to the model
- `toolUseResult.type`: `"text"` for successful reads
- `toolUseResult.file.content`: Raw file content WITHOUT line number prefixes
- `toolUseResult.file.filePath`, `numLines`, etc.: Metadata about the read

#### String Search Caveat

Raw grep for `<persisted-output>` found 3 hits in the good session, but ALL were in **conversation text** where the user was discussing/quoting the bug from other sessions - NOT in actual tool_result entries.

**Lesson**: Detection must check within tool_result content specifically, not just grep the entire file.

#### Directory Structure Indicator

The good session has **no `tool-results/` subdirectory** - only `subagents/`:
```
2.1.6-good/0357781f-d024-4cef-8496-56501c76afb3/
└── subagents/
    └── agent-aee03d2.jsonl
```

The presence of a `tool-results/` directory indicates persistence occurred during the session.

#### Verification Across Session and Subagent

Both main session and subagent files were scanned - no `<persisted-output>` markers found in any tool_result entries.

### Design Implications

1. Cannot simply grep for `<persisted-output>` string - must parse JSON and check within tool_result entries
2. The `tool-results/` directory existence could be a quick pre-filter for sessions where persistence occurred
3. Absence of `tool-results/` directory strongly suggests no phantom reads occurred

---

## Question 4: Session WITH `<persisted-output>` Phantom Reads (Era 2)

**Question**: What does a session look like when a `<persisted-output>` phantom read DOES occur in a 2.0.60+ build?

### Findings

**Sample examined**: `2.1.6-bad/`

#### Critical Discovery: Session File Does NOT Capture Phantom Read Markers

**The most significant finding**: The session `.jsonl` file records **actual file content** in tool_result entries, even when the agent claims to have experienced phantom reads.

**Evidence**:
1. Agent self-report (from chat export and session file):
   > "dev/scripts/stage_release.py → persisted-output, **never followed up**"

2. But the session file (line 52) shows actual content:
   ```json
   {
     "tool_use_id": "toolu_0162qTLwBAPom8tHQpddvAev",
     "type": "tool_result", 
     "content": "     1→\"\"\"Stage Release Script for WSD Development..."
   }
   ```

3. The `tool-results/` directory DOES contain a file for this tool_use_id:
   ```
   tool-results/toolu_0162qTLwBAPom8tHQpddvAev.txt  (26KB - stage_release.py content)
   ```

#### Mapping of Read Operations to Persistence

Analysis of all Read operations in the bad session:

| Line | Tool Use ID | File | Persisted? |
|------|-------------|------|------------|
| 20 | toolu_0175... | Journal-Workscope-20260113-100413.md | YES |
| 27 | toolu_01SiA... | Coding-Standards.md | YES |
| 27 | toolu_01DxD... | Python-Standards.md | YES |
| 27 | toolu_01Cn2... | Python-Test-Environment-Isolation-Standards.md | YES |
| 27 | toolu_01UJC... | Specification-Maintenance-Standards.md | YES |
| 27 | toolu_01FDk... | Process-Integrity-Standards.md | YES |
| 44 | toolu_018rC... | Manifest-Driven-Pipeline-Overview.md | YES |
| 47 | toolu_01MBd... | Pre-Staging-Script-Overview.md | YES |
| 48 | toolu_01UYf... | WSD-Runtime-Metadata-Schema.md | YES |
| 49 | toolu_0162q... | stage_release.py | YES |
| 50 | toolu_01FKd... | build_package.py | YES |
| 64 | toolu_01ExS... | Installation-System.md | NO (inline) |
| 65 | toolu_01Mvq... | Update-System.md | NO (inline) |
| 69 | toolu_016Au... | Stage-Release-Script-Overview.md | NO (inline) |
| 72 | toolu_018Hq... | wsd_utils.py | NO (inline) |
| 77 | toolu_014wx... | wsd.py | NO (inline) |
| 82 | toolu_01Cgz... | Journal-Workscope-20260113-100413.md | NO (inline) |
| 87 | toolu_01TAv... | toolu_018rC...txt (follow-up read!) | NO (inline) |

**Pattern observed**: Early reads (lines 20-50) were PERSISTED, later reads (lines 64+) were INLINE. Line 87 shows the agent reading a persisted `.txt` file directly - a successful follow-up read.

#### Structural Comparison: Persisted vs Inline

Both PERSISTED and INLINE reads have identical structure in the session file:
- Both have `toolUseResult.type: "text"`
- Both have `toolUseResult.file` with filePath, content, numLines, etc.
- Both have actual file content in `message.content[].content`

**No structural difference was found** between reads that were persisted vs inline.

#### The Discrepancy

The session `.jsonl` appears to log tool execution results BEFORE they are processed for the model's context window. The actual `<persisted-output>` marker that the model sees is NOT recorded in the session file.

This means: **The session .jsonl is NOT a reliable source for detecting phantom reads.**

### Design Implications

1. **Session file is unreliable** for phantom read detection - it logs tool execution, not model context
2. **Presence of `tool-results/` directory** indicates persistence occurred but doesn't prove phantom reads
3. **Agent self-report** provides evidence but may be unreliable (see Question 6 findings)
4. **Alternative detection strategies needed** - cannot rely solely on session file parsing

---

## Question 5: Session Without `[Old tool result content cleared]` Phantom Reads (Era 1)

**Question**: What does a session look like when NO phantom reads occur in a 2.0.59 or earlier build?

### Findings

**Sample examined**: `2.0.58-good/`

#### Directory Structure

Era 1 sessions have a flat structure with no `tool-results/` directory:
```
2.0.58-good/
├── c489af7a-584d-4276-a76c-ddb29f988ace.jsonl  # Main session (554KB)
├── agent-07bd3f25.jsonl  (1.5KB)
├── agent-17c7da61.jsonl  (855B)
└── agent-af401ba5.jsonl  (333KB)
```

#### Tool Result Structure

**Identical to Era 2** - tool_result entries contain actual file content with line number prefixes:

```
Line 16: tool_result - Has line numbers, Content length: 446
Line 38: tool_result - Has line numbers, Content length: 24168
Line 43: tool_result - Has line numbers, Content length: 18385
Line 44: tool_result - Has line numbers, Content length: 44800
...
```

All tool_result entries show substantial content with line number prefixes (`1→`, `2→`, etc.), indicating successful Read operations were recorded.

#### No Phantom Read Markers

Grep search for `[Old tool result content cleared]` returned **zero results** in the good session files (main session and all agent files).

#### Verification Via Chat Export

The chat export (`2.0.58-good.txt`) confirms the agent did NOT experience phantom reads - when asked about the `<persisted-output>` issue, the agent stated:
> "If you're trying to reproduce the `<persisted-output>` issue, this session did NOT exhibit that behavior. I received file contents directly, not `<persisted-output>` messages."

### Design Implications

1. **Era 1 good sessions are structurally identical to bad sessions** - the session file format does not differ
2. **No `[Old tool result content cleared]` markers appear** in good sessions
3. **The key difference is behavioral** - the agent's actual competence with file contents, not the session file structure

---

## Question 6: Session WITH `[Old tool result content cleared]` Phantom Reads (Era 1)

**Question**: What does a session look like when a phantom read DOES occur in a 2.0.59 or earlier build?

### Findings

**Sample examined**: `2.0.58-bad/`

#### Agent Self-Report

From the chat export and session file, the agent explicitly states:
> "The results came back as `[Old tool result content cleared]` in the conversation history shown to me. I can see this pattern throughout my tool results."

The agent lists affected files:
- `docs/features/manifest-driven-pipeline/Manifest-Driven-Pipeline-Overview.md`
- `docs/features/pre-staging-script/Pre-Staging-Script-Overview.md`
- `docs/features/stage-release-script/Stage-Release-Script-Overview.md`
- `docs/core/WSD-Runtime-Metadata-Schema.md`
- `docs/features/install-and-update/Installation-System.md`
- `docs/features/install-and-update/Update-System.md`

#### Critical Discovery: Same Discrepancy as Era 2

Searching the session `.jsonl` file for `[Old tool result content cleared]`:
- Only 1 occurrence found - in the agent's self-report message
- **NO occurrences in actual tool_result entries**

All tool_result entries in the Era 1 bad session show **actual file content**, just like Era 2:
```
Line 38: Normal content (has line numbers), content length: 24168
Line 45: Normal content (has line numbers), content length: 18385
Line 46: Normal content (has line numbers), content length: 44800
...
```

#### Confirmed Pattern

**The same discrepancy exists in both eras**: The session `.jsonl` records actual content, but the agent reports seeing phantom read markers (`[Old tool result content cleared]` in Era 1, `<persisted-output>` in Era 2).

### Design Implications

The Era 1 findings confirm that the session file discrepancy is NOT related to the `tool-results/` directory mechanism introduced in Era 2. The content clearing/persisting happens at a layer between:
1. Tool execution (recorded in session file with actual content)
2. Model context (where the phantom read marker appears)

---

## Critical Finding: Context Reset Correlation

### Discovery

While examining the `cache_read_input_tokens` field in assistant messages, a **quantifiable indicator** of context management was found that correlates with phantom read occurrence.

### The `cache_read_input_tokens` Field

Assistant messages in the session file contain a `usage` object with cache-related fields:
- `cache_read_input_tokens`: Tokens read from the prompt cache
- `cache_creation_input_tokens`: Tokens added to the cache this turn
- `input_tokens`: Non-cached input tokens

### Context Reset Pattern

A **context reset** occurs when `cache_read_input_tokens` drops significantly (>10,000 tokens) between consecutive assistant messages. This indicates the system cleared older context to make room.

**Comparison between good and bad sessions:**

| Session | Context Resets | Phantom Reads? | Reset Points |
|---------|---------------|----------------|--------------|
| 2.0.58-good | 1 | No | Line 36 (82K → 20K) |
| 2.0.58-bad | 3 | Yes | Line 36 (83K → 20K), Line 57 (116K → 20K), Line 69 (146K → 20K) |

**Key observation**: All resets drop to approximately the same "base" level (~20K tokens), which likely represents the persistent system prompt and command definitions.

### Why More Resets = More Risk

Each context reset clears older tool results to make room for new context. When a reset occurs:
1. The session file has ALREADY recorded the actual content
2. But the model's context window is cleared of that content
3. The model sees a placeholder marker (`[Old tool result content cleared]` or `<persisted-output>`) instead

More resets = more opportunities for critical file content to be cleared before the model has fully processed it.

### Detection Algorithm

```python
def count_context_resets(session_path: Path, threshold: int = 10000) -> list[tuple[int, int, int]]:
    """
    Count context resets in a session file.
    
    A reset is detected when cache_read_input_tokens drops by more than
    the threshold between consecutive assistant messages.
    
    Returns:
        List of (line_number, before_value, after_value) tuples
    """
    resets = []
    prev_cache_read = 0
    
    with open(session_path, 'r') as f:
        for i, line in enumerate(f, 1):
            try:
                msg = json.loads(line)
                if msg.get('type') == 'assistant':
                    usage = msg.get('message', {}).get('usage', {})
                    cache_read = usage.get('cache_read_input_tokens', 0)
                    if cache_read > 0:
                        if prev_cache_read > 0 and cache_read < prev_cache_read - threshold:
                            resets.append((i, prev_cache_read, cache_read))
                        prev_cache_read = cache_read
            except json.JSONDecodeError:
                continue
    
    return resets
```

### Implications for Detection Strategy

1. **Context resets are quantifiable** - we can detect them in session files
2. **Reset count correlates with phantom reads** - sessions with more resets are at higher risk
3. **Not a "smoking gun"** - resets indicate risk, not certainty of phantom reads
4. **Potential for risk scoring** - could classify sessions as "low risk" (0-1 resets) vs "high risk" (2+ resets)

---

## Critical Finding: Session File Does Not Capture Model Context

### Summary

Across BOTH Era 1 and Era 2 "bad" sessions:
- The session `.jsonl` file records **actual file content** in all tool_result entries
- But agents **claim** they saw phantom read markers (`[Old tool result content cleared]` or `<persisted-output>`)
- The phantom read markers appear NOWHERE in the session files except in conversation text where agents discuss experiencing them

### Hypothesis

The session `.jsonl` appears to be a log of tool execution results, NOT a representation of what the model actually receives in its context window. The content clearing/persistence happens AFTER the session file is written but BEFORE the content is sent to the model.

### Implications for Detection Strategy

1. **Session `.jsonl` parsing alone CANNOT detect phantom reads** - the markers aren't recorded there
2. **Proxy indicators** may be needed:
   - Context reset count (see above)
   - Presence of `tool-results/` directory (Era 2 only)
   - Agent self-report patterns in conversation
   - Discrepancies between claimed file reads and actual agent knowledge
3. **Chat export analysis** may provide better evidence since it shows the agent's actual responses and reasoning
4. **Further investigation needed** to determine if any other data source captures the actual model context

---

## Summary

| Question | Status | Key Finding |
|----------|--------|-------------|
| Q1: Session file association | ✅ Complete | Use sessionId field; check for subdirectory structure |
| Q2: Export pairing | ✅ Complete | Use Workscope ID pattern (`YYYYMMDD-HHMMSS`) |
| Q3: Good session (Era 2) | ✅ Complete | No `tool-results/` dir; actual content in tool_results |
| Q4: Bad session (Era 2) | ✅ Complete | Session file has content but agent saw `<persisted-output>` |
| Q5: Good session (Era 1) | ✅ Complete | Structurally identical to bad; 1 context reset vs 3 in bad |
| Q6: Bad session (Era 1) | ✅ Complete | Same discrepancy - session has content but agent saw `[Old tool result content cleared]` |

**Critical Discoveries**:
1. The session `.jsonl` file does NOT accurately represent what the model sees in its context window
2. Phantom read markers are NOT recorded in the session file
3. Context resets (drops in `cache_read_input_tokens`) correlate with phantom read occurrence
4. More context resets = higher risk of phantom reads

---

## Alternative Detection Strategies

Given that direct detection from session files is not possible, these alternative approaches warrant investigation:

### 1. Context Reset Risk Scoring

Classify sessions by context reset count:
- **Low risk**: 0-1 resets
- **High risk**: 2+ resets

This provides a quantifiable proxy, though not definitive detection.

### 2. Agent Self-Report Validation Study

A feasibility study could correlate:
- Agent's yes/no self-report on phantom reads
- Actual quality of their `/refine-plan` output (checking for hallucinated details, bad line numbers, etc.)

If high correlation exists with sufficient statistical power, self-report could serve as a reliable proxy.

### 3. Output Quality Analysis

Programmatically check agent outputs for:
- References to line numbers that don't exist
- Quotes of text not present in referenced files
- Structural claims that don't match file structure

This would require baseline "ground truth" files for comparison.

### 4. Alternative Read Mechanisms

The MCP Filesystem workaround has shown 100% success rate. Sessions using MCP reads vs native Read tool could be compared to validate the issue is specific to the native Read mechanism.

---

*This document is part of the Phantom Reads Investigation project. Last updated: 2026-01-13*
