#!/usr/bin/env python
"""
Extract tool_result success/failure information from a session JSONL file.
"""

import json
import sys
from pathlib import Path

def extract_tool_results(session_file: Path) -> dict[str, dict]:
    """Extract tool_result content by tool_use_id."""
    tool_results = {}

    with session_file.open() as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line)

                # Look for user messages with tool_result in message.content
                if data.get("type") == "user" and "message" in data:
                    message = data["message"]
                    if message.get("role") == "user" and "content" in message:
                        content_list = message["content"]
                        if not isinstance(content_list, list):
                            continue
                        for item in content_list:
                            if not isinstance(item, dict):
                                continue
                            if item.get("type") == "tool_result":
                                tool_use_id = item.get("tool_use_id")
                                content = item.get("content", "")

                                # Determine success/failure
                                if "<tool_use_error>" in content:
                                    # Failed read
                                    # Extract error message
                                    start = content.find("<tool_use_error>") + len("<tool_use_error>")
                                    end = content.find("</tool_use_error>")
                                    error_msg = content[start:end] if start > 0 and end > 0 else "Unknown error"

                                    tool_results[tool_use_id] = {
                                        "success": False,
                                        "error": error_msg,
                                        "line": line_num
                                    }
                                else:
                                    # Successful read (starts with line numbers or no error marker)
                                    tool_results[tool_use_id] = {
                                        "success": True,
                                        "line": line_num
                                    }

            except json.JSONDecodeError:
                continue

    return tool_results

if __name__ == "__main__":
    session_file = Path(sys.argv[1])
    results = extract_tool_results(session_file)

    # Output as JSON
    print(json.dumps(results, indent=2))
