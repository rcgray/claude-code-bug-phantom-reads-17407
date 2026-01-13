# Possible Workarounds for Phantom Reads

This document tracks potential mitigation strategies for the Phantom Reads bug, their implementation status, and effectiveness.

## Summary Table

| Approach | Status | Effectiveness | Notes |
|----------|--------|---------------|-------|
| Warning in onboarding | Tested | Not effective | Agent ignores warnings |
| PostToolUse detection hook | Tested | Not effective | Agent ignores feedback |
| Proof-of-Work verification | Not tested | Unknown | Requires agent cooperation |
| PreToolUse Read override | **In Testing** | Unknown | Most promising technical solution |
| MCP server replacement | Not tested | Unknown | Highest effort, most reliable |

---

## 1. Warning in Onboarding

**Status**: Tested, not effective

**Description**: Add explicit warnings about phantom reads in documentation that agents read during initialization:
- CLAUDE.md warning section
- WSD System docs (`docs/read-only/Agent-Rules.md`, etc.)
- `/wsd:init` command instructions

**Implementation**: Added "CRITICAL: Phantom Reads Warning" to CLAUDE.md explaining:
- The bug exists and what it looks like
- What to look for (`<persisted-output>` markers)
- Self-check instructions
- Mitigation advice (prefer Grep)

**Results**: Agent admitted seeing and understanding the warning but "completely failed to apply" it. The agent proceeded to confabulate analysis of files it never read, using Grep fragments to build false confidence.

**Conclusion**: Documentation-based warnings are ineffective because the agent operates on "autopilot" and doesn't consciously apply guidance at the moment of failure.

---

## 2. PostToolUse Detection Hook

**Status**: Tested, not effective

**Description**: Use a PostToolUse hook to detect when Read tool returns `<persisted-output>` markers and provide blocking feedback to Claude.

**Implementation**:
- Created `.claude/hooks/detect_phantom_read.py`
- Hook detects `<persisted-output>` in `tool_response`
- Returns `decision: "block"` with detailed reason explaining the phantom read
- Provides the persisted path for follow-up

**Results**: The hook fires (events visible in output), but the agent still ignores the feedback and proceeds without follow-up reads. Same failure mode as documentation warnings.

**Technical Limitation**: PostToolUse hooks **cannot modify tool output**—they can only detect and provide feedback. This was confirmed by researching GitHub issues [#4544](https://github.com/anthropics/claude-code/issues/4544) and [#4635](https://github.com/anthropics/claude-code/issues/4635), both closed as "not planned."

**Conclusion**: Detection alone is insufficient. Even when explicitly told a read failed, the agent doesn't change behavior.

---

## 3. Proof-of-Work Verification

**Status**: Not tested

**Description**: Require agents to prove they actually read files by reporting verifiable content from each file.

**Implementation Options**:

**Option A: First-line verification**
```
After reading each file, you MUST report the first non-empty line.
Example: "docs/core/PRD.md: '# Project: Claude Code Phantom Reads Reproduction'"
If you cannot report this, you experienced a phantom read.
```

**Option B: Content hash verification**
```
After reading each file, calculate and report: filename + line count + first heading.
Example: "Agent-System.md | 616 lines | # Agent System Overview"
```

**Pros**:
- Forces active verification rather than passive "I read it"
- Detectable failure when agent can't produce proof

**Cons**:
- Still relies on agent cooperation
- Agent might confabulate "proof" from context clues
- Adds overhead to every file read

**Open Questions**:
- Will agents actually perform the check?
- Can agents confabulate plausible-looking proof?

---

## 4. PreToolUse Read Override

**Status**: In Testing (implemented 2026-01-13)

**Description**: Use PreToolUse to intercept ALL Read calls, perform the read via Python (which is reliable), and deliver content to Claude.

### Technical Background

PreToolUse hooks have these capabilities:
- `permissionDecision: "deny"` - blocks tool execution
- `permissionDecisionReason` - shown TO CLAUDE (not user) when denying
- Exit code 2 - stderr sent to Claude as feedback
- `updatedInput` - modify tool parameters (v2.0.10+)

**Key insight**: When we DENY a Read with `permissionDecisionReason`, that reason is sent to Claude. We can put the file content there.

### Proposed Implementation

```python
#!/usr/bin/env python
"""PreToolUse hook to reliably read files and deliver content."""

import json
import sys
from pathlib import Path

def main():
    data = json.load(sys.stdin)
    tool_name = data.get("tool_name")
    tool_input = data.get("tool_input", {})

    if tool_name != "Read":
        sys.exit(0)  # Allow non-Read tools

    file_path = tool_input.get("file_path")
    if not file_path:
        sys.exit(0)

    try:
        # Read file ourselves (reliable, no phantom read possible)
        content = Path(file_path).read_text()
        line_count = len(content.splitlines())

        # Deliver content via deny reason
        output = {
            "hookSpecificOutput": {
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"FILE_READ_OVERRIDE: Read intercepted and performed reliably.\n"
                    f"File: {file_path}\n"
                    f"Lines: {line_count}\n"
                    f"Content follows:\n"
                    f"---BEGIN FILE---\n"
                    f"{content}\n"
                    f"---END FILE---"
                )
            }
        }
        print(json.dumps(output))
        sys.exit(0)

    except Exception as e:
        # If we can't read, let native Read try
        sys.exit(0)

if __name__ == "__main__":
    main()
```

### Required CLAUDE.md Instructions

For this to work, agents must understand the pattern:

```markdown
## File Read Override

This project uses a PreToolUse hook that intercepts Read commands and performs
reads reliably. When you see a "denied" Read with reason starting with
"FILE_READ_OVERRIDE:", the file WAS successfully read. Extract the content
from between ---BEGIN FILE--- and ---END FILE--- markers.

This is NOT an error. The hook prevents phantom reads by performing the read
via Python instead of the native Read tool.
```

### Actual Implementation (2026-01-13)

**Files created/modified:**
- `.claude/hooks/reliable_read.py` - The PreToolUse hook
- `.claude/settings.local.json` - Updated to use reliable_read.py
- `CLAUDE.md` - Added FILE_READ_OVERRIDE instructions

**Hook behavior:**
1. Intercepts ALL Read tool calls
2. Checks deny patterns first (security - preserves protect_files.py behavior)
3. Reads file via Python `Path.read_text()` (reliable)
4. Handles offset/limit parameters
5. Returns content with line numbers matching native Read format
6. Truncates at 100,000 characters to avoid context overflow

**Output format:**
```
FILE_READ_OVERRIDE
==================
Read intercepted and performed reliably via Python.
This is NOT an error - extract content below.

File: /path/to/file.md
Lines: 150 of 150

---BEGIN FILE CONTENT---
     1	# File Content
     2	...
---END FILE CONTENT---
```

### Pros
- Completely bypasses the phantom read bug
- Claude receives actual file content (in deny reason)
- No reliance on agent following up
- Preserves offset/limit functionality
- Includes security deny pattern checking

### Cons
- Hacky - abuses "deny" mechanism to deliver content
- Requires CLAUDE.md instructions for agents to understand
- May confuse agents who interpret "denied" as failure
- All Reads become "denied" in logs/UI
- Unknown file size limits on `permissionDecisionReason`

### Open Questions
- Will Claude actually extract content from deny reasons?
- Will the pattern be recognized reliably?
- Are there file size limits on `permissionDecisionReason`?
- How does this interact with binary files?

---

## 5. MCP Server Replacement

**Status**: Not tested

**Description**: Replace the native Read tool entirely with a custom MCP server that provides a reliable file reading tool.

### Proposed Implementation

Create an MCP server that provides:
- `reliable_read` tool - reads files synchronously, never returns persisted-output
- Possibly `reliable_grep` - if Grep also has issues
- Session-wide file content cache

### Architecture

```
┌─────────────┐     ┌─────────────────┐     ┌──────────────┐
│ Claude Code │────▶│ MCP Server      │────▶│ File System  │
│   Agent     │◀────│ (reliable_read) │◀────│              │
└─────────────┘     └─────────────────┘     └──────────────┘
```

### Implementation Sketch

```python
from mcp.server import Server

app = Server("reliable-filesystem")

@app.tool()
async def reliable_read(file_path: str, offset: int = 0, limit: int = None) -> str:
    """Read file content reliably. Never returns persisted-output markers."""
    content = Path(file_path).read_text()
    lines = content.splitlines()

    if offset:
        lines = lines[offset:]
    if limit:
        lines = lines[:limit]

    return "\n".join(lines)
```

### Pros
- Most reliable solution - completely bypasses bug
- Clean architecture - no hacks
- Could add additional features (caching, validation)

### Cons
- Highest implementation effort
- Requires MCP server setup and configuration
- Agents must be instructed to use `reliable_read` instead of `Read`
- May not integrate seamlessly with existing tooling

---

## Answering the Hook Question

**Question**: Is there another hook type that would allow us to fully insert ourselves into the file read process and return custom data as the tool result?

**Answer**: No. Based on research:

1. **PostToolUse** - Can detect issues and provide feedback, but **cannot modify `tool_response`**. Feature requests for this ([#4544](https://github.com/anthropics/claude-code/issues/4544), [#4635](https://github.com/anthropics/claude-code/issues/4635)) were closed as "not planned."

2. **PreToolUse** - Can block/allow tools and modify inputs (`updatedInput`), but **cannot provide custom output**. The `permissionDecisionReason` is shown to Claude when denying, which is our best option for content delivery (Approach #4).

3. **Other hooks** (Stop, Notification, etc.) - Not relevant to tool execution.

**The closest we can get**: PreToolUse deny + content in `permissionDecisionReason`. This is a hack that abuses the deny mechanism, but it's the only way to deliver custom content to Claude via hooks.

---

## Recommendation

**Try PreToolUse override next** (Approach #4). It's the most promising because:
1. It doesn't rely on agent cooperation after the fact
2. It completely bypasses the phantom read bug
3. Content is delivered directly (albeit via deny reason)

If that fails due to agents not understanding the pattern, fall back to **MCP server** (Approach #5) which is cleaner but requires more effort.

---

## References

- [Claude Code Hooks Documentation](https://code.claude.com/docs/en/hooks)
- [GitHub Issue #4544](https://github.com/anthropics/claude-code/issues/4544) - PostToolUse output modification (closed)
- [GitHub Issue #4635](https://github.com/anthropics/claude-code/issues/4635) - Rewriting tool_response (closed)
- [Steve Kinney - Hook Control Flow](https://stevekinney.com/courses/ai-development/claude-code-hook-control-flow)
