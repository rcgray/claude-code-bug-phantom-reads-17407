#!/usr/bin/env python
"""
PreToolUse hook to intercept Read commands and deliver file content reliably.

This hook completely bypasses the phantom reads bug by:
1. Intercepting all Read tool calls
2. Reading the file via Python (which is reliable)
3. Delivering content via the permissionDecisionReason field

The hook returns permissionDecision: "deny" but this is NOT an error - it's a
mechanism to deliver content to Claude. Agents must be instructed to recognize
"FILE_READ_OVERRIDE" denials as successful reads.

Also incorporates file protection logic from protect_files.py.

See docs/core/Possible-Workarounds.md for full documentation.
"""

import json
import sys
from fnmatch import fnmatch
from pathlib import Path
from typing import Any


# Maximum characters to include in response (to avoid overwhelming context)
MAX_CONTENT_LENGTH = 100000


def load_deny_patterns() -> list[str]:
    """Load deny patterns from Claude settings.

    Returns:
        List of Read deny patterns from settings.
    """
    project_settings_path = Path.cwd() / ".claude" / "settings.local.json"
    global_settings_path = Path.home() / ".claude" / "settings.json"

    for settings_path in [project_settings_path, global_settings_path]:
        try:
            with settings_path.open() as f:
                settings = json.load(f)
                deny_rules: list[Any] = settings.get("permissions", {}).get("deny", [])
                # Extract Read patterns
                patterns = []
                for rule in deny_rules:
                    if rule.startswith("Read(") and rule.endswith(")"):
                        patterns.append(rule[5:-1])
                return patterns
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            continue

    return []


def matches_deny_pattern(file_path: str, patterns: list[str]) -> bool:
    """Check if file path matches any deny pattern.

    Args:
        file_path: File path to check.
        patterns: List of deny patterns.

    Returns:
        True if file matches a deny pattern.
    """
    for pattern in patterns:
        # Handle relative patterns (./path/**)
        if pattern.startswith("./"):
            pattern_suffix = pattern[2:]
            path_parts = file_path.split("/")
            for i in range(len(path_parts)):
                partial_path = "/".join(path_parts[i:])
                if fnmatch(partial_path, pattern_suffix):
                    return True
        elif fnmatch(file_path, pattern):
            return True

    return False


def read_file_content(file_path: str, offset: int = 0, limit: int | None = None) -> tuple[str, int, int]:
    """Read file content with optional offset and limit.

    Args:
        file_path: Path to file.
        offset: Line number to start from (0-indexed).
        limit: Maximum number of lines to return.

    Returns:
        Tuple of (content, lines_returned, total_lines).
    """
    path = Path(file_path)
    content = path.read_text()
    all_lines = content.splitlines()
    total_lines = len(all_lines)

    # Apply offset
    if offset > 0:
        lines = all_lines[offset:]
    else:
        lines = all_lines

    # Apply limit
    if limit is not None and limit > 0:
        lines = lines[:limit]

    lines_returned = len(lines)

    # Add line numbers (matching Read tool format)
    numbered_lines = []
    for i, line in enumerate(lines):
        line_num = offset + i + 1  # 1-indexed
        numbered_lines.append(f"{line_num:6d}\t{line}")

    result = "\n".join(numbered_lines)

    # Truncate if too long
    if len(result) > MAX_CONTENT_LENGTH:
        result = result[:MAX_CONTENT_LENGTH] + "\n\n[Content truncated due to length]"

    return result, lines_returned, total_lines


def main() -> None:
    """Process PreToolUse hook input and deliver file content reliably."""
    try:
        data = json.load(sys.stdin)
        tool_name = data.get("tool_name", "")
        tool_input = data.get("tool_input", {})

        # Only process Read tool
        if tool_name != "Read":
            sys.exit(0)

        file_path = tool_input.get("file_path")
        if not file_path:
            sys.exit(0)

        # Check deny patterns first (security)
        deny_patterns = load_deny_patterns()
        if matches_deny_pattern(file_path, deny_patterns):
            # Actual security denial - not a read override
            output = {
                "hookSpecificOutput": {
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        f"SECURITY_POLICY_VIOLATION: Access to '{file_path}' is blocked.\n"
                        f"This file matches a deny pattern in Claude settings."
                    )
                }
            }
            print(json.dumps(output))
            sys.exit(0)

        # Get offset and limit parameters
        offset = tool_input.get("offset", 0) or 0
        limit = tool_input.get("limit")

        # Read the file ourselves (reliable - no phantom read possible)
        try:
            content, lines_returned, total_lines = read_file_content(file_path, offset, limit)

            # Construct the override response
            output = {
                "hookSpecificOutput": {
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        f"FILE_READ_OVERRIDE\n"
                        f"==================\n"
                        f"Read intercepted and performed reliably via Python.\n"
                        f"This is NOT an error - extract content below.\n\n"
                        f"File: {file_path}\n"
                        f"Lines: {lines_returned} of {total_lines}"
                        + (f" (offset: {offset})" if offset > 0 else "")
                        + (f" (limit: {limit})" if limit else "")
                        + f"\n\n"
                        f"---BEGIN FILE CONTENT---\n"
                        f"{content}\n"
                        f"---END FILE CONTENT---"
                    )
                }
            }
            print(json.dumps(output))
            sys.exit(0)

        except FileNotFoundError:
            output = {
                "hookSpecificOutput": {
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        f"FILE_READ_OVERRIDE_ERROR\n"
                        f"File not found: {file_path}"
                    )
                }
            }
            print(json.dumps(output))
            sys.exit(0)

        except PermissionError:
            output = {
                "hookSpecificOutput": {
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        f"FILE_READ_OVERRIDE_ERROR\n"
                        f"Permission denied: {file_path}"
                    )
                }
            }
            print(json.dumps(output))
            sys.exit(0)

        except Exception as e:
            # For other errors, let native Read try
            # (might handle binary files, etc. differently)
            sys.exit(0)

    except json.JSONDecodeError:
        # Can't parse input - let native Read proceed
        sys.exit(0)
    except Exception:
        # Unexpected error - let native Read proceed
        sys.exit(0)


if __name__ == "__main__":
    main()
