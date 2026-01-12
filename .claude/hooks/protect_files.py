#!/usr/bin/env python
"""Claude Code pre-tool-use hook for protecting sensitive files from access."""

import json
import sys
from fnmatch import fnmatch
from pathlib import Path
from typing import Any


# Debug flag - set to False to disable debug logging
DEBUG_ENABLED = False


def load_settings() -> list[Any]:
    """Load Claude settings and extract deny patterns.

    Returns:
        List of deny patterns from settings.json.
    """
    # First try project-local settings, then fall back to global settings
    project_settings_path = Path.cwd() / ".claude" / "settings.local.json"
    global_settings_path = Path.home() / ".claude" / "settings.json"

    for settings_path in [project_settings_path, global_settings_path]:
        try:
            with settings_path.open() as f:
                settings = json.load(f)
                deny_patterns: list[Any] = settings.get("permissions", {}).get("deny", [])
                return deny_patterns
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            continue

    return []


def extract_path_pattern(deny_rule: str) -> str | None:
    """Extract file path pattern from deny rule.

    Args:
        deny_rule: Deny rule string like 'Read(./path/pattern)'.

    Returns:
        Extracted file path pattern, or None if not a Read rule.
    """
    if deny_rule.startswith("Read(") and deny_rule.endswith(")"):
        return deny_rule[5:-1]  # Remove 'Read(' and ')'
    return None


def matches_pattern(file_path: str | Path, pattern: str) -> bool:
    """Check if file path matches a deny pattern.

    Args:
        file_path: File path to check (string or Path object).
        pattern: Deny pattern to match against.

    Returns:
        True if file path matches the pattern.
    """
    file_path = str(file_path)

    # Convert relative patterns to work with absolute paths
    if pattern.startswith("./"):
        # For patterns like './local/**', check if any part of the path matches
        pattern = pattern[2:]  # Remove './'
        # Check if the pattern matches any suffix of the path
        path_parts = file_path.split("/")
        for i in range(len(path_parts)):
            partial_path = "/".join(path_parts[i:])
            if fnmatch(partial_path, pattern):
                return True
    # Direct pattern matching
    elif fnmatch(file_path, pattern):
        return True

    return False


def main() -> None:
    """Process hook input and check for sensitive file access."""
    # Note - replace the path below with one relevant to your project
    debug_file = None
    # debug_file = Path("/Users/gray/Projects/.../docs/temp.txt")

    try:
        # Read the JSON data passed from Claude Code via stdin
        data = json.load(sys.stdin)
        tool_input = data.get("tool_input", {})
        file_path_str = tool_input.get("file_path")

        # Debug: Log what we're processing
        if DEBUG_ENABLED:
            with debug_file.open("a") as f:
                f.write("=== Hook triggered ===\n")
                f.write(f"Full tool input: {tool_input}\n")
                f.write(f"File path: {file_path_str}\n")

        if not file_path_str:
            # If no file path is involved, the hook doesn't need to act.
            sys.exit(0)

        file_path = Path(file_path_str)

        # Load deny patterns from settings
        deny_rules = load_settings()

        # Debug: Log deny rules
        if DEBUG_ENABLED:
            with debug_file.open("a") as f:
                f.write(f"Deny rules found: {deny_rules}\n")

        # Check if the file path matches any deny pattern
        for rule in deny_rules:
            pattern = extract_path_pattern(rule)

            # Debug: Log pattern matching
            if DEBUG_ENABLED:
                with debug_file.open("a") as f:
                    f.write(f"Rule: {rule} -> Pattern: {pattern}\n")
                    if pattern:
                        matches = matches_pattern(file_path, pattern)
                        f.write(f"  Matches {file_path}: {matches}\n")

            if pattern and matches_pattern(file_path, pattern):
                # Construct a clear, educational error message for the LLM
                error_message = (
                    f"SECURITY_POLICY_VIOLATION: Access to '{file_path}' is blocked by "
                    f"deny rule: {rule}\n"
                    f"Reason: This file matches a pattern in your Claude settings.json "
                    f"deny list.\n"
                    "Action: Files in denied paths contain sensitive information and "
                    "should not be accessed by the AI."
                )

                # Print the error message to stderr
                print(error_message, file=sys.stderr)

                # Exit with code 2 to block the tool and feed stderr back to Claude
                sys.exit(2)

    except (json.JSONDecodeError, KeyError) as e:
        # Handle potential errors in the input data
        print(f"Error processing hook input: {e}", file=sys.stderr)
        # Debug: Log the error
        if DEBUG_ENABLED:
            with debug_file.open("a") as f:
                f.write(f"Error: {e}\n")
        # Exit with a non-blocking error code
        sys.exit(1)

    # If no sensitive file was detected, exit with 0 to allow the action
    if DEBUG_ENABLED:
        with debug_file.open("a") as f:
            f.write("No match found, allowing access\n\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
