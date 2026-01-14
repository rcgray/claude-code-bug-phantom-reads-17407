# PostToolUse Hook Mitigation Strategy

This document describes the proposed hook-based mitigation for phantom reads and tracks the investigation findings.

## Objective

Implement a PostToolUse hook that detects when a Read tool returns a `<persisted-output>` marker instead of actual file content, and provides feedback to force the agent to issue a follow-up read.

## Investigation Findings

### Question 1: PostToolUse JSON Structure

**Status**: RESOLVED

PostToolUse hooks receive JSON via stdin with the following structure:

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../session.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "PostToolUse",
  "tool_name": "Read",
  "tool_input": {
    "file_path": "/path/to/file.txt"
  },
  "tool_response": {
    // Tool-specific response object
  }
}
```

**Key field**: `tool_response` contains the result of the tool execution. For Read tools, this would contain the file content or the `<persisted-output>` marker.

**Sources**:
- [Claude Code Hooks Reference](https://code.claude.com/docs/en/hooks)
- [GitButler Claude Code Hooks Guide](https://blog.gitbutler.com/automate-your-ai-workflows-with-claude-code-hooks/)

### Question 2: Exit Code Behavior for PostToolUse

**Status**: RESOLVED

Exit codes work differently for PostToolUse than PreToolUse:

| Exit Code | Behavior |
|-----------|----------|
| 0 | Success - stdout parsed as JSON for structured control |
| 2 | Blocking error - stderr shown to Claude as feedback |
| Other | Non-blocking - stderr shown in verbose mode only |

**Critical difference from PreToolUse**: Since PostToolUse fires AFTER the tool has already executed, exit code 2 does NOT prevent the action—it provides feedback to Claude about the result.

**JSON Output Format** (exit code 0):
```json
{
  "decision": "block",
  "reason": "Explanation shown to Claude"
}
```

The `"decision": "block"` with a reason automatically prompts Claude with the feedback, allowing the agent to take corrective action.

**Sources**:
- [Gend.co Claude Code Hooks Guide](https://www.gend.co/blog/configure-claude-code-hooks-automation)
- [disler/claude-code-hooks-mastery](https://github.com/disler/claude-code-hooks-mastery)

### Question 3: Can We Modify Tool Response Content?

**Status**: RESOLVED - NOT POSSIBLE

**Critical Finding**: PostToolUse hooks **cannot modify tool output**. This was requested in GitHub issues [#4544](https://github.com/anthropics/claude-code/issues/4544) and [#4635](https://github.com/anthropics/claude-code/issues/4635), but was **closed as "not planned"**.

This means our preferred approach (intercepting `<persisted-output>`, reading the file via Python, and injecting the actual content) is **not possible** with current Claude Code architecture.

**What we CAN do**:
- Detect phantom reads by checking `tool_response` for `<persisted-output>` markers
- Use `decision: "block"` with a reason to alert Claude
- Provide the persisted file path in the reason so Claude knows where to read

**What we CANNOT do**:
- Replace the `<persisted-output>` marker with actual file content
- Modify `tool_response` before Claude sees it
- Perform a "transparent" read that sidesteps the bug

**Sources**:
- [Feature Request #4544](https://github.com/anthropics/claude-code/issues/4544) - Closed as duplicate
- [Feature Request #4635](https://github.com/anthropics/claude-code/issues/4635) - Closed as "not planned"

### Known Issues

**PostToolUse Hooks May Not Execute**: GitHub issue [#6403](https://github.com/anthropics/claude-code/issues/6403) reports that PostToolUse hooks were not executing in some versions (v1.0.89+), despite correct configuration. This may have been fixed in later versions but needs verification.

**Source**: [Issue #6403](https://github.com/anthropics/claude-code/issues/6403)

## Implementation Plan

Given the constraints discovered, here is our revised implementation approach:

### Approach: Detection + Feedback

Since we cannot modify tool responses, we will:

1. **Detect** phantom reads by scanning `tool_response` for `<persisted-output>` patterns
2. **Alert** Claude via `decision: "block"` with a detailed reason
3. **Guide** Claude to issue a follow-up Read to the persisted path

### Hook Script: `.claude/hooks/detect_phantom_read.py`

```python
#!/usr/bin/env python
"""PostToolUse hook to detect phantom reads and alert Claude."""

import json
import re
import sys

def main() -> None:
    """Check Read tool responses for phantom read indicators."""
    try:
        data = json.load(sys.stdin)
        tool_response = data.get("tool_response", {})

        # tool_response might be a string or object depending on the tool
        response_str = str(tool_response)

        # Check for Era 2 phantom read indicator
        if "<persisted-output>" in response_str and "Use Read to view" in response_str:
            # Extract the persisted file path
            match = re.search(r'Tool result saved to: ([^\n]+)', response_str)
            persisted_path = match.group(1) if match else "unknown path"

            # Return blocking feedback
            output = {
                "decision": "block",
                "reason": (
                    f"PHANTOM READ DETECTED: You received a <persisted-output> marker, "
                    f"not actual file content.\n\n"
                    f"The content was persisted to: {persisted_path}\n\n"
                    f"You MUST issue a follow-up Read to this path before proceeding. "
                    f"Do not attempt to analyze or act on this file—you have not read it."
                )
            }
            print(json.dumps(output))
            sys.exit(0)

        # No phantom read detected
        sys.exit(0)

    except Exception as e:
        # Non-blocking error
        print(f"Hook error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### Configuration: `.claude/settings.local.json`

Add PostToolUse hook entry:

```json
{
  "hooks": {
    "PreToolUse": [
      // ... existing protect_files.py hook ...
    ],
    "PostToolUse": [
      {
        "matcher": "Read",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/detect_phantom_read.py"
          }
        ]
      }
    ]
  }
}
```

## Open Questions (Remaining)

1. **Does `tool_response` contain the raw file content or a structured object?** We need to test what format the Read tool returns.

2. **Will the hook actually execute?** Given reported issues with PostToolUse hooks not firing, we need to verify execution in current Claude Code version (2.1.6).

3. **Will Claude actually follow the guidance?** Even with blocking feedback, Claude may ignore the instruction (as seen with CLAUDE.md warnings). However, hooks are harder to ignore than passive documentation.

4. **Can we detect Era 1 phantom reads?** The `[Old tool result content cleared]` pattern may appear differently in `tool_response`. Needs investigation with older session data.

## Alternative Approaches (If Hook Fails)

If PostToolUse detection proves unreliable:

### Alternative 1: PreToolUse Interception

Use PreToolUse to intercept Read calls and replace them with a custom implementation:
- Block the native Read tool
- Execute a Python-based file read
- Return content via the `reason` field or a custom mechanism

**Limitation**: May not integrate cleanly with Claude's expectations.

### Alternative 2: Proof-of-Work Verification

Require agents to prove file reads by quoting content:
- Embed verification requirements in commands
- Agents must quote first heading + line count
- Failure to verify triggers re-read

**Limitation**: Still relies on agent cooperation.

### Alternative 3: MCP Server Replacement

Replace the Read tool entirely with an MCP server that:
- Handles reads reliably
- Never returns `<persisted-output>` markers
- Forces synchronous content retrieval

**Limitation**: Significant implementation effort; may not address root cause.

## Next Steps

1. Implement the detection hook script
2. Update `.claude/settings.local.json` with PostToolUse configuration
3. Test hook execution with a controlled phantom read scenario
4. Document results and iterate

## References

- [Claude Code Hooks Documentation](https://code.claude.com/docs/en/hooks)
- [GitHub Issue #17407 - Phantom Reads](https://github.com/anthropics/claude-code/issues/17407)
- [GitHub Issue #4635 - PostToolUse Output Modification](https://github.com/anthropics/claude-code/issues/4635) (closed, not planned)
- [GitHub Issue #6403 - PostToolUse Not Executing](https://github.com/anthropics/claude-code/issues/6403)
