#!/usr/bin/env python
"""
PostToolUse hook to detect phantom reads in Claude Code.

This hook fires after Read tool execution and checks if the response contains
a <persisted-output> marker instead of actual file content. When detected,
it provides blocking feedback to alert Claude to issue a follow-up read.

See docs/core/PostToolUse-Hook.md for full documentation.
"""

import json
import re
import sys
from typing import Any


def extract_persisted_path(response_str: str) -> str:
    """Extract the persisted file path from a <persisted-output> marker.

    Args:
        response_str: The tool response string containing the marker.

    Returns:
        The extracted file path, or "unknown path" if not found.
    """
    match = re.search(r'Tool result saved to: ([^\n<]+)', response_str)
    if match:
        return match.group(1).strip()
    return "unknown path"


def check_for_phantom_read(tool_response: Any) -> tuple[bool, str]:
    """Check if a tool response indicates a phantom read.

    Args:
        tool_response: The tool_response field from PostToolUse JSON input.

    Returns:
        Tuple of (is_phantom_read, persisted_path).
    """
    # tool_response might be a string, dict, or other structure
    response_str = str(tool_response)

    # Check for Era 2 phantom read indicator
    if "<persisted-output>" in response_str and "Use Read to view" in response_str:
        persisted_path = extract_persisted_path(response_str)
        return True, persisted_path

    return False, ""


def main() -> None:
    """Process PostToolUse hook input and detect phantom reads."""
    try:
        # Read JSON input from stdin
        data = json.load(sys.stdin)

        tool_name = data.get("tool_name", "")
        tool_response = data.get("tool_response", {})
        tool_input = data.get("tool_input", {})

        # Only process Read tool responses
        if tool_name != "Read":
            sys.exit(0)

        # Check for phantom read
        is_phantom, persisted_path = check_for_phantom_read(tool_response)

        if is_phantom:
            # Get the original file that was requested
            original_file = tool_input.get("file_path", "unknown file")

            # Construct blocking feedback
            output = {
                "decision": "block",
                "reason": (
                    "PHANTOM READ DETECTED\n"
                    "=====================\n\n"
                    f"Your Read of '{original_file}' returned a <persisted-output> "
                    "marker, NOT actual file content.\n\n"
                    f"The content was persisted to:\n{persisted_path}\n\n"
                    "ACTION REQUIRED: You MUST issue a follow-up Read to the "
                    "persisted path above before proceeding.\n\n"
                    "WARNING: Do not attempt to analyze, summarize, or act on this "
                    "file—you have NOT read it. Any beliefs you have about its "
                    "contents are confabulated."
                )
            }
            print(json.dumps(output))
            sys.exit(0)

        # No phantom read detected - allow normal processing
        sys.exit(0)

    except json.JSONDecodeError as e:
        # Log error but don't block
        print(f"Hook JSON decode error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        # Log unexpected errors but don't block
        print(f"Hook unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
