#!/usr/bin/env python
"""
Parse session JSONL file to extract trial data metrics.

This script extracts token progression, context resets, file reads,
and user inputs from a Claude Code session JSONL file.
"""

import json
import sys
from pathlib import Path


def parse_session(session_path: Path) -> dict:
    """
    Parse a session JSONL file and extract trial metrics.

    Args:
        session_path: Path to the session JSONL file.

    Returns:
        Dictionary containing parsed session data.
    """
    token_progression = []
    resets = []
    file_reads = []
    user_inputs = []
    timeline = []

    prev_cache_tokens = 0
    sequence = 0
    batch_id = 0
    read_sequence = 0
    current_batch_reads = []
    errors = 0

    with session_path.open() as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                errors += 1
                continue

            msg_type = data.get("type")

            # Track assistant messages with usage data
            if msg_type == "assistant":
                message = data.get("message", {})
                usage = message.get("usage", {})
                cache_tokens = usage.get("cache_read_input_tokens", 0)

                if cache_tokens > 0:
                    sequence += 1
                    token_progression.append({
                        "sequence": sequence,
                        "cache_read_tokens": cache_tokens,
                        "session_line": line_num
                    })

                    # Detect context resets (drop > 10,000 tokens)
                    if prev_cache_tokens > 0 and (prev_cache_tokens - cache_tokens) > 10000:
                        resets.append({
                            "sequence_position": sequence,
                            "from_tokens": prev_cache_tokens,
                            "to_tokens": cache_tokens,
                            "session_line": line_num
                        })
                        timeline.append({
                            "sequence": sequence,
                            "type": "context_reset",
                            "session_line": line_num,
                            "from_tokens": prev_cache_tokens,
                            "to_tokens": cache_tokens
                        })

                    prev_cache_tokens = cache_tokens

                # Track file reads from tool_use blocks
                content = message.get("content", [])
                batch_reads = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        if block.get("name") == "Read":
                            read_sequence += 1
                            input_data = block.get("input", {})
                            file_path = input_data.get("file_path", "")
                            tool_use_id = block.get("id", "")

                            read_entry = {
                                "sequence": read_sequence,
                                "batch_id": batch_id,
                                "file_path": file_path,
                                "session_line": line_num,
                                "tool_use_id": tool_use_id
                            }
                            file_reads.append(read_entry)
                            batch_reads.append(read_entry)

                if batch_reads:
                    timeline.append({
                        "sequence": sequence,
                        "type": "tool_batch",
                        "session_line": line_num,
                        "tool": "Read",
                        "count": len(batch_reads),
                        "files": [r["file_path"] for r in batch_reads]
                    })
                    batch_id += 1

            # Track user inputs
            elif msg_type == "human":
                message = data.get("message", {})
                content = message.get("content", "")
                if isinstance(content, list):
                    # Extract text from content blocks
                    text_parts = []
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            text_parts.append(block.get("text", ""))
                    content = " ".join(text_parts)

                preview = content[:100] if content else ""

                # Detect methodology phases
                phase = None
                content_lower = content.lower() if content else ""
                if "/wsd:init" in content_lower:
                    phase = "init"
                elif "/refine-plan" in content_lower:
                    phase = "trigger"
                elif "phantom read" in content_lower or "persisted-output" in content_lower:
                    phase = "inquiry"

                sequence += 1
                user_input = {
                    "sequence": sequence,
                    "session_line": line_num,
                    "preview": preview,
                    "phase": phase
                }
                user_inputs.append(user_input)

                timeline.append({
                    "sequence": sequence,
                    "type": "user_input",
                    "session_line": line_num,
                    "preview": preview[:50],
                    "phase": phase
                })

    # Compute unique files
    unique_files = list(set(r["file_path"] for r in file_reads if r["file_path"]))

    return {
        "token_progression": token_progression,
        "resets": resets,
        "file_reads": file_reads,
        "user_inputs": user_inputs,
        "timeline": timeline,
        "unique_file_list": sorted(unique_files),
        "total_operations": len(file_reads),
        "unique_file_count": len(unique_files),
        "errors": errors,
        "total_lines": line_num
    }


def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python parse_session.py <session.jsonl>")
        sys.exit(1)

    session_path = Path(sys.argv[1])
    if not session_path.exists():
        print(f"Error: File not found: {session_path}")
        sys.exit(1)

    result = parse_session(session_path)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
